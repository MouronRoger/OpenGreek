#!/usr/bin/env python3
"""TLG Corrected Extractor - Separates Greek text from metadata.

Uses corrected selectors and filters to extract actual Greek content.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set

import aiohttp
import yaml
from bs4 import BeautifulSoup

import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/tlg_corrected_extraction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Paths
CONFIG_FILE = Path(__file__).parent / "config.yaml"
OUTPUT_DIR = Path(__file__).parent / "data" / "tlg"
CATALOGUES_DIR = OUTPUT_DIR / "catalogues"

# Load config
with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    CONFIG = yaml.safe_load(f)


class GreekTextFilter:
    """Filter to separate Greek content from metadata."""
    
    def __init__(self):
        self.metadata_patterns = [
            r'TLG \d+ \d+ ::', 
            r'Source:', 
            r'Citation:', 
            r'Cf\. et',
            r'Scholia:',
            r'Vitae:',
            r'\([^)]*B\.C\.\)',
            r'\([^)]*A\.D\.\)',
            r'Oxford:', 
            r'Leipzig:', 
            r'Teubner',
            r'Clarendon Press'
        ]
    
    def separate_greek_from_metadata(self, mixed_text: str) -> Dict[str, str]:
        """Separate actual Greek text from catalog metadata."""
        
        # Split into lines for analysis
        lines = mixed_text.split('\n')
        greek_lines = []
        metadata_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if line is primarily metadata
            is_metadata = False
            for pattern in self.metadata_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    is_metadata = True
                    break
            
            # Calculate Greek character ratio for this line
            if line:
                greek_chars = sum(1 for c in line if '\u0370' <= c <= '\u03FF' or '\u1F00' <= c <= '\u1FFF')
                total_chars = len(line)
                greek_ratio = greek_chars / total_chars if total_chars > 0 else 0
                
                # If line has substantial Greek content and isn't metadata, it's probably Greek text
                if greek_ratio > 0.5 and not is_metadata and len(line) > 20:
                    greek_lines.append(line)
                elif is_metadata or greek_ratio < 0.1:
                    metadata_lines.append(line)
                else:
                    # Mixed content - need to analyze more carefully
                    # For now, err on side of including it
                    greek_lines.append(line)
        
        return {
            'greek_text': '\n'.join(greek_lines),
            'metadata': '\n'.join(metadata_lines),
            'mixed_content': mixed_text
        }


class TLGCorrectedExtractor:
    """Corrected TLG extractor that separates Greek text from metadata."""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.text_filter = GreekTextFilter()
        self.extracted_works: List[Dict] = []
        
        # Statistics
        self.stats = {
            'start_time': datetime.now(),
            'works_processed': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'greek_text_found': 0,
            'metadata_only': 0
        }
    
    async def setup(self):
        """Initialize HTTP session."""
        print("🚀 Setting up Corrected TLG Extractor...")
        
        headers = {'User-Agent': CONFIG["source"]["user_agent"]}
        timeout = aiohttp.ClientTimeout(total=CONFIG["extraction"]["timeout"])
        self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / "corrected_extraction").mkdir(exist_ok=True)
        
        print("✅ Setup complete! Ready for corrected extraction.")
    
    async def cleanup(self):
        """Clean up resources."""
        if self.session:
            await self.session.close()
    
    def load_catalog(self) -> Dict:
        """Load the discovered catalog."""
        catalog_file = CATALOGUES_DIR / "tlg_integrated_catalog.json"
        with open(catalog_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    async def fetch_and_extract_work(self, author_id: str, work_id: str, work_title: str) -> Optional[Dict]:
        """Fetch and extract a single work with Greek text separation."""
        url = f"{CONFIG['source']['base_url']}/TLG{author_id}/{author_id}_{work_id}.htm"
        
        # Fetch content
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return None
                
                html_content = await response.text()
                
        except Exception as e:
            logger.debug(f"Error fetching {url}: {e}")
            return None
        
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove unwanted elements
        for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer']):
            element.decompose()
        
        # Extract using corrected selectors
        extracted_text = None
        
        # Try primary selectors (table cells)
        for selector in CONFIG["extraction"]["selectors"]["primary"]:
            elements = soup.select(selector)
            if elements:
                all_text = ' '.join(elem.get_text(separator=' ', strip=True) for elem in elements)
                if len(all_text) > 100:  # Has substantial content
                    extracted_text = all_text
                    break
        
        if not extracted_text:
            return None
        
        # Separate Greek text from metadata
        filtered_content = self.text_filter.separate_greek_from_metadata(extracted_text)
        
        # Calculate metrics
        greek_text = filtered_content['greek_text']
        greek_chars = sum(1 for c in greek_text if '\u0370' <= c <= '\u03FF' or '\u1F00' <= c <= '\u1FFF')
        total_chars = len(greek_text) if greek_text else 0
        greek_ratio = greek_chars / total_chars if total_chars > 0 else 0
        
        return {
            'tlg_reference': {
                'author_id': author_id,
                'work_id': work_id,
                'work_title': work_title,
                'url': url,
                'extraction_date': datetime.now().isoformat()
            },
            'content': {
                'greek_text': greek_text,
                'metadata': filtered_content['metadata'],
                'mixed_content': filtered_content['mixed_content'][:1000]  # First 1000 chars for debugging
            },
            'metrics': {
                'total_chars': total_chars,
                'greek_chars': greek_chars,
                'greek_ratio': greek_ratio,
                'has_substantial_greek': greek_ratio > 0.3 and total_chars > 100
            }
        }
    
    async def test_priority_works(self):
        """Test extraction on a few priority works."""
        print("================================================================================")
        print("📊 PHASE: CORRECTED EXTRACTION TEST")
        print("📝 Testing Greek text separation on priority works...")
        print("================================================================================")
        
        # Test works
        test_works = [
            ('0012', '001', 'Homer Iliad'),
            ('0012', '002', 'Homer Odyssey'), 
            ('0059', '030', 'Plato Republic'),
            ('0086', '035', 'Aristotle Metaphysics'),
            ('0011', '001', 'Sophocles Ajax')
        ]
        
        results = []
        
        for author_id, work_id, title in test_works:
            print(f"🔍 Testing: TLG{author_id}.{work_id} ({title})")
            
            result = await self.fetch_and_extract_work(author_id, work_id, title)
            
            if result:
                metrics = result['metrics']
                greek_ratio = metrics['greek_ratio']
                greek_chars = metrics['greek_chars']
                has_greek = metrics['has_substantial_greek']
                
                status = "✅ GREEK TEXT FOUND" if has_greek else "⚠️  LOW GREEK CONTENT"
                print(f"   {status}: {greek_chars:,} Greek chars ({greek_ratio*100:.1f}% Greek)")
                
                if has_greek:
                    # Show sample of actual Greek text
                    greek_sample = result['content']['greek_text'][:200]
                    print(f"   📖 Sample: {greek_sample}...")
                
                results.append(result)
                self.stats['greek_text_found'] += 1 if has_greek else 0
                self.stats['metadata_only'] += 0 if has_greek else 1
            else:
                print(f"   ❌ FAILED to fetch")
            
            await asyncio.sleep(2)  # Respectful delay
            print()
        
        # Save test results
        test_file = OUTPUT_DIR / "corrected_extraction" / "test_results.json"
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump({
                'test_date': datetime.now().isoformat(),
                'test_results': results,
                'summary': {
                    'works_tested': len(test_works),
                    'works_with_greek': self.stats['greek_text_found'],
                    'metadata_only': self.stats['metadata_only']
                }
            }, f, ensure_ascii=False, indent=2)
        
        print(f"📊 TEST SUMMARY:")
        print(f"   🔍 Works tested: {len(test_works)}")
        print(f"   ✅ Greek text found: {self.stats['greek_text_found']}")
        print(f"   ❌ Metadata only: {self.stats['metadata_only']}")
        print(f"   💾 Results saved: {test_file}")
        
        return self.stats['greek_text_found'] > 0


async def main():
    """Test the corrected extraction system."""
    extractor = TLGCorrectedExtractor()
    
    try:
        await extractor.setup()
        success = await extractor.test_priority_works()
        
        if success:
            print(f"\n🎉 CORRECTED EXTRACTION WORKING!")
            print(f"🔧 Ready to re-run full corpus extraction with actual Greek text!")
        else:
            print(f"\n❌ Still need more investigation")
            
    finally:
        await extractor.cleanup()


if __name__ == "__main__":
    asyncio.run(main())




