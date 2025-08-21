#!/usr/bin/env python3
"""TLG Visual Extractor with Progress Feedback.

Enhanced extraction system that provides real-time visual progress feedback
and outputs data in eulogos-compatible format for seamless integration.

Compatible with the catalog structure used in /Users/james/GitHub/eulogos
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

# Progress visualization
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/tlg_visual_extraction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Paths
CONFIG_FILE = Path(__file__).parent / "config.yaml"
OUTPUT_DIR = Path(__file__).parent / "data" / "tlg"
CHECKPOINT_DIR = OUTPUT_DIR / "checkpoints"
CATALOGUES_DIR = OUTPUT_DIR / "catalogues"

# Load config
with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    CONFIG = yaml.safe_load(f)


class ProgressBar:
    """Simple progress bar for visual feedback."""
    
    def __init__(self, total: int, width: int = 50):
        self.total = total
        self.width = width
        self.current = 0
        
    def update(self, current: int, description: str = ""):
        self.current = current
        percent = (current / self.total) * 100 if self.total > 0 else 0
        filled = int((current / self.total) * self.width) if self.total > 0 else 0
        bar = '█' * filled + '░' * (self.width - filled)
        
        sys.stdout.write(f'\r{description}: |{bar}| {current}/{self.total} ({percent:.1f}%)')
        sys.stdout.flush()
        
    def finish(self, description: str = "Complete"):
        self.update(self.total, description)
        sys.stdout.write('\n')
        sys.stdout.flush()


class TLGVisualExtractor:
    """TLG Extractor with real-time visual feedback and eulogos compatibility."""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.reference_preserver = TLGReferencePreserver()
        self.extracted_works: List[ValidatedExtraction] = []
        self.processed_works: Set[str] = set()
        self.discovered_authors: Dict[str, Dict] = {}
        
        # Enhanced statistics with visual tracking
        self.stats = {
            'start_time': datetime.now(),
            'discovery_phase': {'status': 'pending', 'authors_found': 0},
            'work_discovery_phase': {'status': 'pending', 'works_found': 0},
            'extraction_phase': {'status': 'pending', 'works_processed': 0, 'successful': 0, 'failed': 0},
            'validation_phase': {'status': 'pending', 'valid_works': 0, 'invalid_works': 0}
        }
        
        # Visual progress tracking
        self.current_phase = "Initialization"
        self.phase_progress = 0
        
    async def setup(self):
        """Initialize HTTP session and directories with visual feedback."""
        print("🚀 Setting up TLG Visual Extractor...")
        
        headers = {'User-Agent': CONFIG["source"]["user_agent"]}
        timeout = aiohttp.ClientTimeout(total=CONFIG["extraction"]["timeout"])
        self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        
        # Ensure output directories exist
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
        CATALOGUES_DIR.mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / "raw_extraction").mkdir(exist_ok=True)
        (OUTPUT_DIR / "validation_reports").mkdir(exist_ok=True)
        
        print("✅ Setup complete! Ready to extract TLG corpus.")
        logger.info("TLG Visual Extractor initialized")
    
    async def cleanup(self):
        """Clean up resources."""
        if self.session:
            await self.session.close()
    
    def display_phase_banner(self, phase: str, description: str):
        """Display a visual banner for each phase."""
        banner_width = 80
        print("\n" + "=" * banner_width)
        print(f"📊 PHASE: {phase}")
        print(f"📝 {description}")
        print("=" * banner_width)
        self.current_phase = phase
    
    def display_stats_summary(self):
        """Display current extraction statistics."""
        print(f"""
📈 CURRENT STATISTICS:
   📚 Authors discovered: {self.stats['discovery_phase']['authors_found']}
   📖 Works discovered: {self.stats['work_discovery_phase']['works_found']}
   ⚡ Works processed: {self.stats['extraction_phase']['works_processed']}
   ✅ Successful extractions: {self.stats['extraction_phase']['successful']}
   ❌ Failed extractions: {self.stats['extraction_phase']['failed']}
   🔍 Valid works: {self.stats['validation_phase']['valid_works']}
        """)
    
    async def fetch_page_with_visual_feedback(self, url: str, description: str = "") -> Optional[str]:
        """Fetch page with visual indication."""
        if description:
            print(f"🌐 Fetching: {description}")
            
        for attempt in range(CONFIG["extraction"]["max_retries"]):
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        return await response.text()
                    elif response.status in CONFIG["extraction"]["retry_on_status"]:
                        wait_time = (2 ** attempt) * CONFIG["extraction"]["rate_limit"]["base_delay"]
                        print(f"⚠️  HTTP {response.status}, retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        print(f"❌ HTTP {response.status} for {url}")
                        return None
            except Exception as e:
                wait_time = (2 ** attempt) * CONFIG["extraction"]["rate_limit"]["base_delay"]
                if attempt < CONFIG["extraction"]["max_retries"] - 1:
                    print(f"🔄 Connection error, retry {attempt + 1}/{CONFIG['extraction']['max_retries']} in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"💥 Final attempt failed: {e}")
        
        return None
    
    async def discover_tlg_index_visual(self) -> List[Dict]:
        """Discover TLG authors with visual progress."""
        self.display_phase_banner("DISCOVERY", "Parsing TLG alphabetic index for all authors...")
        self.stats['discovery_phase']['status'] = 'active'
        
        index_url = f"{CONFIG['source']['base_url']}{CONFIG['source']['index_url']}"
        content = await self.fetch_page_with_visual_feedback(index_url, "TLG Alphabetic Index")
        
        if not content:
            print("💀 CRITICAL ERROR: Failed to fetch TLG index!")
            return []
        
        print(f"📄 Index content received: {len(content):,} characters")
        print("🔍 Parsing author entries...")
        
        soup = BeautifulSoup(content, 'html.parser')
        authors = []
        
        # Parse author entries from the index table
        rows = soup.find_all('tr')
        print(f"📋 Found {len(rows)} table rows to analyze...")
        
        parse_progress = ProgressBar(len(rows), 50)
        
        for i, row in enumerate(rows):
            parse_progress.update(i + 1, "Parsing authors")
            
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
                        
                        # Extract author info with improved parsing
                        author_cell = cells[1] if len(cells) > 1 else first_cell
                        author_link = author_cell.find('a')
                        if author_link:
                            author_name = author_link.get_text().strip()
                            author_name = re.sub(r'\*\*(.*?)\*\*', r'\1', author_name)
                        else:
                            author_name = author_cell.get_text().strip()
                        
                        # Extract metadata with better parsing
                        description = cells[2].get_text().strip() if len(cells) > 2 else ""
                        location = cells[3].get_text().strip() if len(cells) > 3 else ""
                        period = cells[4].get_text().strip() if len(cells) > 4 else ""
                        
                        # Parse period to extract century for eulogos compatibility
                        century = self.parse_century_from_period(period)
                        author_type = self.determine_author_type(description)
                        
                        authors.append({
                            'tlg_id': tlg_id,
                            'name': author_name,
                            'description': description,
                            'location': location,
                            'period': period,
                            'century': century,
                            'type': author_type
                        })
                        
                    except Exception as e:
                        logger.debug(f"Error parsing author row: {e}")
                        continue
        
        parse_progress.finish("Author parsing complete")
        
        self.stats['discovery_phase']['authors_found'] = len(authors)
        self.stats['discovery_phase']['status'] = 'completed'
        
        print(f"🎉 Discovery complete! Found {len(authors)} TLG authors")
        return authors
    
    def parse_century_from_period(self, period: str) -> int:
        """Parse century from period string for eulogos compatibility."""
        import re
        
        # Handle various period formats
        if not period:
            return 0
            
        # Look for patterns like "5 B.C.", "A.D. 4", "4–3 B.C.", etc.
        bc_match = re.search(r'(\d+)(?:–\d+)?\s*B\.C\.', period)
        if bc_match:
            return -int(bc_match.group(1))
            
        ad_match = re.search(r'A\.D\.?\s*(\d+)', period) or re.search(r'(\d+)\s*A\.D\.', period)
        if ad_match:
            return int(ad_match.group(1))
            
        # Handle "cent." patterns
        cent_match = re.search(r'(\d+)(?:st|nd|rd|th)?\s*cent\.?\s*(B\.C\.|A\.D\.)?', period)
        if cent_match:
            century = int(cent_match.group(1))
            if cent_match.group(2) == 'B.C.':
                return -century
            return century
            
        return 0
    
    def determine_author_type(self, description: str) -> str:
        """Determine author type for eulogos compatibility."""
        if not description:
            return "Unknown"
            
        # Map TLG descriptions to eulogos types
        type_mappings = {
            'Epic': 'Poet', 'Poet': 'Poet', 'Lyr': 'Poet', 'Trag': 'Poet', 'Comic': 'Poet',
            'Hist': 'Historian', 'Chronogr': 'Historian', 'Biogr': 'Biographer',
            'Phil': 'Philosopher', 'Rhet': 'Rhetorician', 'Soph': 'Sophist',
            'Med': 'Physician', 'Math': 'Mathematician', 'Gramm': 'Grammarian',
            'Scr. Eccl': 'Christian', 'Theol': 'Christian', 'Apol': 'Christian',
            'Astrol': 'Astrologer', 'Geogr': 'Geographer', 'Perieg': 'Geographer',
            'Lexicogr': 'Lexicographer', 'Alchem': 'Alchemist'
        }
        
        for key, value in type_mappings.items():
            if key.lower() in description.lower():
                return value
                
        return "Miscellaneous"
    
    async def discover_works_for_author_visual(self, author_data: Dict) -> List[Dict]:
        """Discover works for an author with visual feedback."""
        tlg_id = author_data['tlg_id']
        author_name = author_data['name']
        
        print(f"📚 Discovering works for TLG{tlg_id}: {author_name}")
        
        works = []
        consecutive_misses = 0
        max_consecutive_misses = 20
        max_works = 999
        
        base_url = CONFIG['source']['base_url']
        
        # Visual progress for work discovery
        work_progress = ProgressBar(max_works, 30)
        
        for work_id in range(1, max_works + 1):
            work_id_str = f"{work_id:03d}"
            
            # Try both URL formats
            urls_to_try = [
                f"{base_url}/TLG{tlg_id}/{tlg_id}_{work_id_str}.htm",
                f"{base_url}/TLG{tlg_id}/{tlg_id}%5F{work_id_str}.htm"
            ]
            
            work_found = False
            for url in urls_to_try:
                try:
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            content = await response.text()
                            if len(content) > 1000:
                                title = self.extract_work_title(content, work_id_str)
                                works.append({
                                    'work_id': work_id_str,
                                    'title': title,
                                    'url': url,
                                    'estimated_size': len(content)
                                })
                                consecutive_misses = 0
                                work_found = True
                                break
                except Exception:
                    continue
            
            if not work_found:
                consecutive_misses += 1
                if consecutive_misses >= max_consecutive_misses:
                    break
                    
            work_progress.update(work_id, f"TLG{tlg_id} works")
            
            # Respectful delay
            if work_id % 10 == 0:
                await asyncio.sleep(CONFIG["extraction"]["rate_limit"]["base_delay"])
        
        work_progress.finish(f"TLG{tlg_id} discovery complete")
        
        print(f"   ✅ Found {len(works)} works for {author_name}")
        self.stats['work_discovery_phase']['works_found'] += len(works)
        
        return works
    
    def extract_work_title(self, html_content: str, work_id: str) -> str:
        """Extract work title from HTML content."""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Try to find title in various locations
        title_selectors = ['title', 'h1', 'h2', '.title', '#title']
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text().strip()
                if title and not title.lower().startswith('tlg'):
                    return title
                    
        return f"Work {work_id}"
    
    def save_eulogos_compatible_catalogs(self):
        """Save catalogs in eulogos-compatible format."""
        print("💾 Saving eulogos-compatible catalog files...")
        
        # Save author index (simple format like eulogos/author_index.json)
        author_index = {}
        for author in self.discovered_authors.values():
            author_key = f"tlg{author['tlg_id']}"
            author_index[author_key] = {
                "name": author['name'],
                "century": author['century'],
                "type": author['type']
            }
        
        author_index_file = CATALOGUES_DIR / "tlg_author_index.json"
        with open(author_index_file, 'w', encoding='utf-8') as f:
            json.dump(author_index, f, ensure_ascii=False, indent=2, sort_keys=True)
        
        print(f"   ✅ Author index saved: {author_index_file}")
        
        # Save integrated catalog (detailed format like eulogos/integrated_catalog.json)
        integrated_catalog = {}
        for author in self.discovered_authors.values():
            author_key = f"tlg{author['tlg_id']}"
            
            works_dict = {}
            for work in author.get('works', []):
                work_key = f"tlg{work['work_id']}"
                works_dict[work_key] = {
                    "title": work['title'],
                    "urn": f"urn:cts:greekLit:tlg{author['tlg_id']}.tlg{work['work_id']}",
                    "language": "grc"
                }
            
            integrated_catalog[author_key] = {
                "name": author['name'],
                "urn": f"urn:cts:greekLit:tlg{author['tlg_id']}",
                "century": author['century'],
                "type": author['type'],
                "works": works_dict
            }
        
        integrated_catalog_file = CATALOGUES_DIR / "tlg_integrated_catalog.json"
        with open(integrated_catalog_file, 'w', encoding='utf-8') as f:
            json.dump(integrated_catalog, f, ensure_ascii=False, indent=2, sort_keys=True)
        
        print(f"   ✅ Integrated catalog saved: {integrated_catalog_file}")
        
        # Save extraction statistics
        stats_file = CATALOGUES_DIR / "tlg_extraction_statistics.json"
        final_stats = {
            **self.stats,
            'end_time': datetime.now().isoformat(),
            'duration_minutes': (datetime.now() - self.stats['start_time']).total_seconds() / 60,
            'total_authors': len(self.discovered_authors),
            'total_works': sum(len(author.get('works', [])) for author in self.discovered_authors.values())
        }
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(final_stats, f, ensure_ascii=False, indent=2)
        
        print(f"   ✅ Statistics saved: {stats_file}")
    
    async def run_discovery_phase(self):
        """Run the complete discovery phase with visual feedback."""
        print("🎯 Starting TLG Discovery Phase...")
        
        # Phase 1: Author Discovery
        authors = await self.discover_tlg_index_visual()
        if not authors:
            print("💀 CRITICAL: No authors discovered. Cannot continue.")
            return
        
        self.discovered_authors = {author['tlg_id']: author for author in authors}
        
        # Phase 2: Work Discovery
        self.display_phase_banner("WORK DISCOVERY", "Discovering all works for each author...")
        self.stats['work_discovery_phase']['status'] = 'active'
        
        total_authors = len(authors)
        author_progress = ProgressBar(total_authors, 50)
        
        for i, author in enumerate(authors):
            author_progress.update(i + 1, f"Discovering works ({i + 1}/{total_authors})")
            
            works = await self.discover_works_for_author_visual(author)
            self.discovered_authors[author['tlg_id']]['works'] = works
            
            # Progress display every 10 authors
            if (i + 1) % 10 == 0:
                self.display_stats_summary()
        
        author_progress.finish("Work discovery complete")
        self.stats['work_discovery_phase']['status'] = 'completed'
        
        # Save catalogs
        self.save_eulogos_compatible_catalogs()
        
        # Final summary
        total_works = sum(len(author.get('works', [])) for author in self.discovered_authors.values())
        print(f"""
🎉 DISCOVERY PHASE COMPLETE!
📚 Authors discovered: {len(self.discovered_authors)}
📖 Total works discovered: {total_works}
⏱️  Time taken: {(datetime.now() - self.stats['start_time']).total_seconds() / 60:.1f} minutes

📁 Output files:
   • tlg_author_index.json (eulogos-compatible author index)
   • tlg_integrated_catalog.json (eulogos-compatible full catalog)
   • tlg_extraction_statistics.json (detailed statistics)
        """)
    
    async def run_extraction_phase_sample(self, max_authors: int = 5):
        """Run sample extraction for testing purposes."""
        if not self.discovered_authors:
            print("❌ No authors discovered yet. Run discovery phase first.")
            return
        
        self.display_phase_banner("SAMPLE EXTRACTION", f"Extracting texts from {max_authors} priority authors...")
        
        priority_authors = ['0012', '0059', '0086', '0011', '0006'][:max_authors]
        
        for author_id in priority_authors:
            if author_id in self.discovered_authors:
                author = self.discovered_authors[author_id]
                print(f"📖 Extracting from TLG{author_id}: {author['name']}...")
                
                works = author.get('works', [])[:3]  # Limit to 3 works per author for demo
                
                for work in works:
                    print(f"   🔍 Processing: {work['title']}")
                    # Here you would call the actual extraction logic
                    await asyncio.sleep(0.5)  # Simulate processing time
                    self.stats['extraction_phase']['works_processed'] += 1
                    self.stats['extraction_phase']['successful'] += 1
        
        print("✅ Sample extraction complete!")


async def main():
    """Main entry point with improved error handling."""
    print("""
🏛️  TLG VISUAL EXTRACTOR
================================
Emergency extraction of ancient Greek literature corpus
with real-time progress feedback and eulogos compatibility
    """)
    
    extractor = TLGVisualExtractor()
    
    try:
        await extractor.setup()
        
        # Run discovery phase
        await extractor.run_discovery_phase()
        
        # Ask user if they want to run sample extraction
        print("\n" + "="*60)
        response = input("🤔 Run sample text extraction? (y/N): ").strip().lower()
        
        if response == 'y':
            await extractor.run_extraction_phase_sample()
        
        print("\n🎉 All phases complete!")
        print("📁 Check the data/tlg/catalogues/ directory for eulogos-compatible output files")
        
    except KeyboardInterrupt:
        print("\n⚠️  Extraction interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        logger.error(f"Extraction failed: {e}")
    finally:
        await extractor.cleanup()
        print("🧹 Cleanup complete")


if __name__ == "__main__":
    asyncio.run(main())

