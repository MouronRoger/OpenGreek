#!/usr/bin/env python3
"""TLG Integrated Extraction Workflow.

Combines discovery, extraction, and reference preservation into a single
comprehensive workflow that ensures complete scholarly citation integrity.

This is the main extraction script for the TLG emergency extraction project.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

import aiohttp
import yaml
from bs4 import BeautifulSoup

# Import our custom modules
from tlg_reference_preservation import (
    TLGReferencePreserver, 
    ValidatedExtraction, 
    TLGReference
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/tlg_extraction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Paths
CONFIG_FILE = Path(__file__).parent / "config.yaml"
OUTPUT_DIR = Path(__file__).parent / "data" / "tlg"
CHECKPOINT_DIR = OUTPUT_DIR / "checkpoints"

# Load config
with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    CONFIG = yaml.safe_load(f)


class TLGIntegratedExtractor:
    """Integrated TLG extraction with complete reference preservation."""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.reference_preserver = TLGReferencePreserver()
        self.extracted_works: List[ValidatedExtraction] = []
        self.processed_works: Set[str] = set()
        self.discovered_authors: Dict[str, Dict] = {}
        
        # Extraction statistics
        self.stats = {
            'start_time': datetime.now(),
            'total_discovered': 0,
            'total_extracted': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'validation_failures': 0
        }
    
    async def setup(self):
        """Initialize HTTP session and directories."""
        headers = {'User-Agent': CONFIG["source"]["user_agent"]}
        timeout = aiohttp.ClientTimeout(total=CONFIG["extraction"]["timeout"])
        self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        
        # Ensure output directories exist
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / "catalogues").mkdir(exist_ok=True)
        (OUTPUT_DIR / "raw_extraction").mkdir(exist_ok=True)
        (OUTPUT_DIR / "validation_reports").mkdir(exist_ok=True)
        
        logger.info("TLG Integrated Extractor initialized")
    
    async def cleanup(self):
        """Clean up resources."""
        if self.session:
            await self.session.close()
    
    async def fetch_page(self, url: str, max_retries: int = 3) -> Optional[str]:
        """Fetch HTML content with retry logic."""
        for attempt in range(max_retries):
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        return await response.text()
                    elif response.status in CONFIG["extraction"]["retry_on_status"]:
                        wait_time = (2 ** attempt) * CONFIG["extraction"]["rate_limit"]["base_delay"]
                        logger.warning(f"HTTP {response.status} for {url}, retrying in {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.warning(f"HTTP {response.status} for {url}")
                        return None
            except Exception as e:
                wait_time = (2 ** attempt) * CONFIG["extraction"]["rate_limit"]["base_delay"]
                logger.error(f"Error fetching {url} (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(wait_time)
        
        return None
    
    async def discover_tlg_index(self) -> List[Dict]:
        """Discover all TLG authors from the alphabetic index."""
        logger.info("Discovering TLG authors from index...")
        
        index_url = f"{CONFIG['source']['base_url']}{CONFIG['source']['index_url']}"
        content = await self.fetch_page(index_url)
        
        if not content:
            logger.error("Failed to fetch TLG index")
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        authors = []
        
        # Parse author entries from the index table
        for row in soup.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) >= 4:
                first_cell = cells[0]
                tlg_link = first_cell.find('a')
                
                if tlg_link and 'TLG' in tlg_link.get_text():
                    try:
                        # Parse TLG ID
                        tlg_text = tlg_link.get_text().strip()
                        import re
                        tlg_match = re.search(r'TLG\s+(\d+)', tlg_text)
                        if not tlg_match:
                            continue
                        tlg_id = tlg_match.group(1).zfill(4)  # Ensure 4 digits
                        
                        # Extract author info
                        author_cell = cells[1] if len(cells) > 1 else first_cell
                        author_link = author_cell.find('a')
                        if author_link:
                            author_name = author_link.get_text().strip()
                            author_name = re.sub(r'\*\*(.*?)\*\*', r'\1', author_name)
                        else:
                            author_name = author_cell.get_text().strip()
                        
                        # Extract metadata
                        description = cells[2].get_text().strip() if len(cells) > 2 else ""
                        location = cells[3].get_text().strip() if len(cells) > 3 else ""
                        period = cells[4].get_text().strip() if len(cells) > 4 else ""
                        
                        authors.append({
                            'tlg_id': tlg_id,
                            'name': author_name,
                            'description': description,
                            'location': location,
                            'period': period
                        })
                        
                    except Exception as e:
                        logger.debug(f"Error parsing author row: {e}")
                        continue
        
        logger.info(f"Discovered {len(authors)} authors from index")
        self.stats['total_discovered'] = len(authors)
        return authors
    
    async def discover_author_works(self, author_data: Dict) -> List[Dict]:
        """Discover all works for a specific author."""
        tlg_id = author_data['tlg_id']
        works = []
        consecutive_misses = 0
        max_consecutive_misses = 20
        
        base_url = CONFIG['source']['base_url']
        
        for work_id in range(1, 1000):
            work_id_str = f"{work_id:03d}"
            
            # Try both URL formats
            urls_to_try = [
                f"{base_url}/TLG{tlg_id}/{tlg_id}_{work_id_str}.htm",
                f"{base_url}/TLG{tlg_id}/{tlg_id}%5F{work_id_str}.htm"
            ]
            
            work_found = False
            for url in urls_to_try:
                content = await self.fetch_page(url, max_retries=2)
                if content and len(content) > 1000:
                    works.append({
                        'work_id': work_id_str,
                        'url': url,
                        'estimated_size': len(content)
                    })
                    consecutive_misses = 0
                    work_found = True
                    logger.debug(f"Found work TLG{tlg_id}.{work_id_str}")
                    break
            
            if not work_found:
                consecutive_misses += 1
                if consecutive_misses >= max_consecutive_misses:
                    logger.debug(f"Stopping work discovery for TLG{tlg_id} after {consecutive_misses} consecutive misses")
                    break
            
            # Respectful delay
            await asyncio.sleep(CONFIG["extraction"]["rate_limit"]["base_delay"])
        
        logger.info(f"TLG{tlg_id} ({author_data['name']}): discovered {len(works)} works")
        return works
    
    def extract_greek_from_html(self, html_content: str) -> Optional[str]:
        """Extract clean Greek text from HTML."""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove unwanted elements
        for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer']):
            element.decompose()
        
        # Try primary selectors
        for selector in CONFIG["extraction"]["selectors"]["primary"]:
            elements = soup.select(selector)
            if elements:
                text = ' '.join(elem.get_text(separator=' ', strip=True) for elem in elements)
                if self.is_substantial_greek_text(text):
                    return text.strip()
        
        # Try fallback selectors
        for selector in CONFIG["extraction"]["selectors"]["fallback"]:
            elements = soup.select(selector)
            if elements:
                text = ' '.join(elem.get_text(separator=' ', strip=True) for elem in elements)
                if self.is_substantial_greek_text(text):
                    return text.strip()
        
        # Last resort: full text
        full_text = soup.get_text(separator=' ', strip=True)
        if self.is_substantial_greek_text(full_text):
            return full_text.strip()
        
        return None
    
    def is_substantial_greek_text(self, text: str) -> bool:
        """Check if text contains substantial Greek content."""
        if not text or len(text) < CONFIG["extraction"]["content_validation"]["min_text_length"]:
            return False
        
        greek_chars = 0
        total_chars = 0
        
        for char in text:
            if char.isalpha():
                total_chars += 1
                if ('\u0370' <= char <= '\u03FF' or  # Greek and Coptic
                    '\u1F00' <= char <= '\u1FFF'):   # Greek Extended
                    greek_chars += 1
        
        if total_chars == 0:
            return False
        
        greek_ratio = greek_chars / total_chars
        return greek_ratio >= CONFIG["extraction"]["content_validation"]["greek_threshold"]
    
    async def extract_work_with_references(self, author_data: Dict, work_data: Dict) -> Optional[ValidatedExtraction]:
        """Extract a single work with complete reference preservation."""
        work_key = f"{author_data['tlg_id']}_{work_data['work_id']}"
        
        if work_key in self.processed_works:
            return None
        
        url = work_data['url']
        logger.debug(f"Extracting TLG{author_data['tlg_id']}.{work_data['work_id']} from {url}")
        
        # Fetch HTML content
        html_content = await self.fetch_page(url)
        if not html_content:
            self.stats['failed_extractions'] += 1
            return None
        
        # Extract clean Greek text
        clean_text = self.extract_greek_from_html(html_content)
        if not clean_text:
            logger.debug(f"No Greek text found in {url}")
            self.stats['failed_extractions'] += 1
            return None
        
        # Create validated extraction with reference preservation
        try:
            validated_extraction = self.reference_preserver.preserve_extraction_references(
                author_data, work_data, html_content, clean_text
            )
            
            # Check if validation passed
            if validated_extraction.validation_metrics.get('overall_valid', False):
                self.stats['successful_extractions'] += 1
                logger.debug(f"Successfully extracted and validated TLG{author_data['tlg_id']}.{work_data['work_id']}")
            else:
                self.stats['validation_failures'] += 1
                logger.warning(f"Validation failed for TLG{author_data['tlg_id']}.{work_data['work_id']}")
            
            self.processed_works.add(work_key)
            return validated_extraction
            
        except Exception as e:
            logger.error(f"Error processing TLG{author_data['tlg_id']}.{work_data['work_id']}: {e}")
            self.stats['failed_extractions'] += 1
            return None
    
    async def extract_priority_authors(self, priority_authors: List[str] = None) -> None:
        """Extract works from priority authors first."""
        if priority_authors is None:
            priority_authors = ['0012', '0059', '0086', '0011', '0006', '0007']
        
        logger.info(f"Starting priority extraction for {len(priority_authors)} authors")
        
        for author_id in priority_authors:
            if author_id in self.discovered_authors:
                author_data = self.discovered_authors[author_id]
                logger.info(f"Processing priority author TLG{author_id}: {author_data['name']}")
                
                # Discover works for this author
                works = await self.discover_author_works(author_data)
                
                # Extract each work
                for work in works:
                    extraction = await self.extract_work_with_references(author_data, work)
                    if extraction:
                        self.extracted_works.append(extraction)
                    
                    # Progress logging and checkpoints
                    self.stats['total_extracted'] += 1
                    if self.stats['total_extracted'] % 50 == 0:
                        self.save_checkpoint()
                        self.log_progress()
                    
                    # Respectful delay
                    await asyncio.sleep(CONFIG["extraction"]["rate_limit"]["base_delay"])
    
    def save_checkpoint(self) -> None:
        """Save current extraction progress."""
        checkpoint_file = CHECKPOINT_DIR / f"tlg_extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        checkpoint_data = {
            'stats': self.stats,
            'processed_works': list(self.processed_works),
            'extracted_count': len(self.extracted_works),
            'timestamp': datetime.now().isoformat()
        }
        
        # Update stats
        checkpoint_data['stats']['end_time'] = datetime.now().isoformat()
        checkpoint_data['stats']['duration_minutes'] = (datetime.now() - self.stats['start_time']).total_seconds() / 60
        
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Checkpoint saved: {checkpoint_file}")
    
    def log_progress(self) -> None:
        """Log current extraction progress."""
        duration = (datetime.now() - self.stats['start_time']).total_seconds() / 60
        success_rate = (self.stats['successful_extractions'] / self.stats['total_extracted'] * 100 
                       if self.stats['total_extracted'] > 0 else 0)
        
        logger.info(f"Progress: {self.stats['total_extracted']} works processed, "
                   f"{self.stats['successful_extractions']} successful ({success_rate:.1f}%), "
                   f"Duration: {duration:.1f} minutes")
    
    def save_results(self) -> None:
        """Save all extraction results in multiple formats."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save complete JSON corpus
        corpus_file = OUTPUT_DIR / f"tlg_corpus_{timestamp}.json"
        corpus_data = {
            'metadata': {
                'extraction_date': datetime.now().isoformat(),
                'total_works': len(self.extracted_works),
                'successful_works': len([e for e in self.extracted_works if e.validation_metrics.get('overall_valid', False)]),
                'total_authors': len(set(e.tlg_reference.author_id for e in self.extracted_works)),
                'extraction_stats': self.stats
            },
            'works': [extraction.to_dict() for extraction in self.extracted_works]
        }
        
        with open(corpus_file, 'w', encoding='utf-8') as f:
            json.dump(corpus_data, f, ensure_ascii=False, indent=2)
        
        # Save reference index
        reference_index_file = OUTPUT_DIR / f"tlg_reference_index_{timestamp}.json"
        self.reference_preserver.save_reference_index(self.extracted_works, reference_index_file)
        
        # Save validation report
        validation_report_file = OUTPUT_DIR / "validation_reports" / f"validation_report_{timestamp}.json"
        self.save_validation_report(validation_report_file)
        
        logger.info(f"Results saved:")
        logger.info(f"  Corpus: {corpus_file}")
        logger.info(f"  Reference Index: {reference_index_file}")
        logger.info(f"  Validation Report: {validation_report_file}")
    
    def save_validation_report(self, output_file: Path) -> None:
        """Save comprehensive validation report."""
        valid_works = [e for e in self.extracted_works if e.validation_metrics.get('overall_valid', False)]
        
        report = {
            'validation_summary': {
                'total_works': len(self.extracted_works),
                'valid_works': len(valid_works),
                'validation_rate': len(valid_works) / len(self.extracted_works) * 100 if self.extracted_works else 0,
                'avg_greek_ratio': sum(e.validation_metrics.get('text_validation', {}).get('greek_ratio', 0) 
                                     for e in self.extracted_works) / len(self.extracted_works) if self.extracted_works else 0
            },
            'validation_failures': [
                {
                    'tlg_reference': f"TLG{e.tlg_reference.author_id}.{e.tlg_reference.work_id}",
                    'author': e.tlg_reference.author_name,
                    'issues': e.validation_metrics
                }
                for e in self.extracted_works 
                if not e.validation_metrics.get('overall_valid', False)
            ]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    
    async def run_extraction(self, priority_only: bool = False) -> None:
        """Run complete TLG extraction workflow."""
        try:
            await self.setup()
            
            # Discover all authors
            authors = await self.discover_tlg_index()
            self.discovered_authors = {author['tlg_id']: author for author in authors}
            
            if priority_only:
                # Extract only priority authors
                await self.extract_priority_authors()
            else:
                # TODO: Implement full corpus extraction
                logger.info("Full corpus extraction not yet implemented, running priority extraction")
                await self.extract_priority_authors()
            
            # Save results
            self.save_results()
            self.save_checkpoint()
            
            # Final statistics
            duration = (datetime.now() - self.stats['start_time']).total_seconds() / 60
            success_rate = (self.stats['successful_extractions'] / self.stats['total_extracted'] * 100 
                           if self.stats['total_extracted'] > 0 else 0)
            
            logger.info("=" * 60)
            logger.info("TLG EXTRACTION COMPLETE")
            logger.info("=" * 60)
            logger.info(f"Total works extracted: {self.stats['total_extracted']}")
            logger.info(f"Successful extractions: {self.stats['successful_extractions']} ({success_rate:.1f}%)")
            logger.info(f"Validation failures: {self.stats['validation_failures']}")
            logger.info(f"Total duration: {duration:.1f} minutes")
            logger.info("=" * 60)
            
        finally:
            await self.cleanup()


async def main():
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("TLG Integrated Extraction with Reference Preservation")
    logger.info("Emergency extraction of complete ancient Greek corpus")
    logger.info("=" * 60)
    
    extractor = TLGIntegratedExtractor()
    await extractor.run_extraction(priority_only=True)


if __name__ == "__main__":
    asyncio.run(main())

