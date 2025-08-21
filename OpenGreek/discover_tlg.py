#!/usr/bin/env python3
"""TLG Index Discovery Script.

This script discovers all available TLG authors and works by parsing the 
alphabetic index at http://217.71.231.54:8080/indices/indexA.htm and then
discovering all works for each author.

Adapted from the proven Daphnet discovery patterns.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin

import aiohttp
import yaml
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
CONFIG_FILE = Path(__file__).parent / "config.yaml"
OUTPUT_DIR = Path(__file__).parent / "data" / "tlg"
CHECKPOINT_DIR = OUTPUT_DIR / "checkpoints"

# Load config
with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    CONFIG = yaml.safe_load(f)

BASE_URL = CONFIG["source"]["base_url"]
INDEX_URL = urljoin(BASE_URL, CONFIG["source"]["index_url"])
REQUEST_DELAY = float(CONFIG["extraction"]["rate_limit"]["base_delay"])

@dataclass
class TLGWork:
    """Represents a discovered TLG work."""
    work_id: str
    title: str
    url: str
    estimated_size: Optional[int] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class TLGAuthor:
    """Represents a discovered TLG author with all their works."""
    tlg_id: str
    name: str
    description: str
    location: str
    period: str
    work_count: int
    works: List[TLGWork]
    discovery_method: str
    
    def to_dict(self) -> Dict:
        return {
            'tlg_id': self.tlg_id,
            'name': self.name,
            'description': self.description,
            'location': self.location,
            'period': self.period,
            'work_count': self.work_count,
            'works': [work.to_dict() for work in self.works],
            'discovery_method': self.discovery_method
        }

class TLGDiscovery:
    """Discover all TLG authors and works from the index."""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.authors: Dict[str, TLGAuthor] = {}
        self.processed_authors: Set[str] = set()
        
    async def setup(self):
        """Initialize HTTP session."""
        headers = {
            'User-Agent': CONFIG["source"]["user_agent"]
        }
        timeout = aiohttp.ClientTimeout(total=CONFIG["extraction"]["timeout"])
        self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        
    async def cleanup(self):
        """Clean up resources."""
        if self.session:
            await self.session.close()
            
    async def fetch_page(self, url: str) -> Optional[str]:
        """Fetch HTML content from a URL with error handling."""
        if not self.session:
            await self.setup()
            
        for attempt in range(CONFIG["extraction"]["max_retries"]):
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        return content
                    elif response.status in CONFIG["extraction"]["retry_on_status"]:
                        wait_time = (2 ** attempt) * REQUEST_DELAY
                        logger.warning(f"HTTP {response.status} for {url}, retrying in {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.warning(f"HTTP {response.status} for {url}")
                        return None
            except Exception as e:
                wait_time = (2 ** attempt) * REQUEST_DELAY
                logger.error(f"Error fetching {url} (attempt {attempt + 1}): {e}")
                if attempt < CONFIG["extraction"]["max_retries"] - 1:
                    await asyncio.sleep(wait_time)
                    
        return None
    
    def parse_index_page(self, html_content: str) -> List[Dict]:
        """Parse the alphabetic index to extract all author entries."""
        soup = BeautifulSoup(html_content, 'html.parser')
        authors = []
        
        # Find the main table with author entries
        # The structure appears to be a table with TLG links and author info
        for row in soup.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) >= 4:  # Ensure we have enough cells
                # Extract TLG ID from the first cell's link
                first_cell = cells[0]
                tlg_link = first_cell.find('a')
                if tlg_link and 'TLG' in tlg_link.get_text():
                    try:
                        # Parse TLG ID (e.g., "TLG 0116" -> "0116")
                        tlg_text = tlg_link.get_text().strip()
                        tlg_match = re.search(r'TLG\s+(\d+)', tlg_text)
                        if not tlg_match:
                            continue
                        tlg_id = tlg_match.group(1)
                        
                        # Extract author info from subsequent cells
                        author_cell = cells[1] if len(cells) > 1 else first_cell
                        author_link = author_cell.find('a')
                        if author_link:
                            author_name = author_link.get_text().strip()
                            # Remove formatting like **AUTHOR**
                            author_name = re.sub(r'\*\*(.*?)\*\*', r'\1', author_name)
                        else:
                            author_name = author_cell.get_text().strip()
                            
                        # Extract description, location, period from remaining cells
                        description = cells[2].get_text().strip() if len(cells) > 2 else ""
                        location = cells[3].get_text().strip() if len(cells) > 3 else ""
                        period = cells[4].get_text().strip() if len(cells) > 4 else ""
                        
                        # Extract work count if available (usually last cell)
                        work_count = 0
                        if len(cells) > 5:
                            work_count_text = cells[-1].get_text().strip()
                            work_count_match = re.search(r'(\d+)', work_count_text)
                            if work_count_match:
                                work_count = int(work_count_match.group(1))
                        
                        authors.append({
                            'tlg_id': tlg_id,
                            'name': author_name,
                            'description': description,
                            'location': location,
                            'period': period,
                            'work_count': work_count,
                            'index_url': urljoin(BASE_URL, tlg_link.get('href', ''))
                        })
                        
                    except Exception as e:
                        logger.debug(f"Error parsing author row: {e}")
                        continue
                        
        logger.info(f"Parsed {len(authors)} authors from index")
        return authors
    
    async def discover_author_works(self, tlg_id: str, max_works: int = 999) -> List[TLGWork]:
        """Discover all works for a specific author by testing work URLs."""
        works = []
        consecutive_misses = 0
        max_consecutive_misses = 20  # Stop after 20 consecutive 404s
        
        for work_id in range(1, max_works + 1):
            # Try both URL formats (encoded and unencoded underscore)
            work_id_str = f"{work_id:03d}"
            urls_to_try = [
                f"{BASE_URL}/TLG{tlg_id}/{tlg_id}_{work_id_str}.htm",
                f"{BASE_URL}/TLG{tlg_id}/{tlg_id}%5F{work_id_str}.htm"
            ]
            
            work_found = False
            for url in urls_to_try:
                content = await self.fetch_page(url)
                if content:
                    # Basic validation - check if it contains substantial content
                    if len(content) > 1000:  # Minimum content threshold
                        works.append(TLGWork(
                            work_id=work_id_str,
                            title=f"Work {work_id_str}",  # Will be refined later
                            url=url,
                            estimated_size=len(content)
                        ))
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
            await asyncio.sleep(REQUEST_DELAY)
            
        logger.info(f"TLG{tlg_id}: discovered {len(works)} works")
        return works
    
    async def discover_all_authors(self) -> Dict[str, TLGAuthor]:
        """Discover all authors and their works from the index."""
        logger.info("Fetching TLG alphabetic index...")
        
        # Fetch and parse the index
        index_content = await self.fetch_page(INDEX_URL)
        if not index_content:
            logger.error("Failed to fetch TLG index")
            return {}
            
        author_entries = self.parse_index_page(index_content)
        logger.info(f"Found {len(author_entries)} authors in index")
        
        # Discover works for each author
        for i, entry in enumerate(author_entries, 1):
            tlg_id = entry['tlg_id']
            
            if tlg_id in self.processed_authors:
                logger.info(f"Author TLG{tlg_id} already processed, skipping")
                continue
                
            logger.info(f"Processing author {i}/{len(author_entries)}: TLG{tlg_id} ({entry['name']})")
            
            try:
                works = await self.discover_author_works(tlg_id)
                
                author = TLGAuthor(
                    tlg_id=tlg_id,
                    name=entry['name'],
                    description=entry['description'],
                    location=entry['location'],
                    period=entry['period'],
                    work_count=len(works),
                    works=works,
                    discovery_method="index_crawl"
                )
                
                self.authors[tlg_id] = author
                self.processed_authors.add(tlg_id)
                
                # Save checkpoint periodically
                if i % 50 == 0:
                    self.save_checkpoint()
                    
            except Exception as e:
                logger.error(f"Error processing author TLG{tlg_id}: {e}")
                continue
                
        logger.info(f"Discovery complete: {len(self.authors)} authors, {sum(len(a.works) for a in self.authors.values())} total works")
        return self.authors
    
    def save_checkpoint(self):
        """Save current progress as checkpoint."""
        CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
        checkpoint_file = CHECKPOINT_DIR / f"tlg_discovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        checkpoint_data = {
            'processed_authors': list(self.processed_authors),
            'authors': {tlg_id: author.to_dict() for tlg_id, author in self.authors.items()},
            'timestamp': datetime.now().isoformat()
        }
        
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Checkpoint saved: {checkpoint_file}")
    
    def save_catalogue(self) -> Path:
        """Save the discovered authors and works to a catalogue file."""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        catalogue_file = OUTPUT_DIR / "tlg_catalogue.json"
        
        # Calculate statistics
        total_works = sum(len(author.works) for author in self.authors.values())
        period_stats = {}
        for author in self.authors.values():
            period = author.period or "Unknown"
            if period not in period_stats:
                period_stats[period] = 0
            period_stats[period] += 1
        
        catalogue = {
            "collection": "tlg",
            "discovery_date": datetime.now().isoformat(),
            "total_authors": len(self.authors),
            "total_works": total_works,
            "discovery_method": "index_crawl",
            "period_statistics": period_stats,
            "authors": [author.to_dict() for author in sorted(
                self.authors.values(),
                key=lambda a: int(a.tlg_id)
            )]
        }
        
        with open(catalogue_file, 'w', encoding='utf-8') as f:
            json.dump(catalogue, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Catalogue saved: {catalogue_file}")
        logger.info(f"Total authors: {len(self.authors)}")
        logger.info(f"Total works: {total_works}")
        
        return catalogue_file
    
    async def run(self) -> Path:
        """Run the complete discovery process."""
        try:
            await self.setup()
            await self.discover_all_authors()
            catalogue_file = self.save_catalogue()
            return catalogue_file
        finally:
            await self.cleanup()

async def main():
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("TLG Corpus Discovery")
    logger.info("Discovers all available authors and works from TLG")
    logger.info("=" * 60)
    
    discovery = TLGDiscovery()
    catalogue_file = await discovery.run()
    
    logger.info("=" * 60)
    logger.info(f"Discovery complete! Catalogue saved to: {catalogue_file}")
    logger.info("Use this catalogue with extract_tlg.py for text extraction")
    logger.info("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
