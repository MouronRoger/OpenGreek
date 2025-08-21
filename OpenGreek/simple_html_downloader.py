#!/usr/bin/env python3
"""Simple HTML Downloader - Save each TLG work as individual HTML file."""

import asyncio
import json
import aiohttp
from pathlib import Path
from datetime import datetime
import time

# Paths
OUTPUT_DIR = Path(__file__).parent / "data" / "tlg" / "html_downloads"
CATALOGUES_DIR = Path(__file__).parent / "data" / "tlg" / "catalogues"

class SimpleHTMLDownloader:
    """Download TLG works as raw HTML files - one file per work."""
    
    def __init__(self):
        self.session = None
        self.downloaded = 0
        self.failed = 0
        
    async def setup(self):
        """Initialize session and directories."""
        print("🚀 Setting up Simple HTML Downloader...")
        
        self.session = aiohttp.ClientSession()
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        print("✅ Ready to download HTML files!")
    
    async def cleanup(self):
        if self.session:
            await self.session.close()
    
    def load_catalog(self):
        """Load the discovered catalog."""
        catalog_file = CATALOGUES_DIR / "tlg_integrated_catalog.json"
        with open(catalog_file, 'r') as f:
            return json.load(f)
    
    async def download_work_html(self, author_id: str, work_id: str, work_title: str) -> bool:
        """Download a single work as HTML file."""
        url = f"http://217.71.231.54:8080/TLG{author_id}/{author_id}_{work_id}.htm"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Save as HTML file
                    filename = f"TLG{author_id}_{work_id}_{self.clean_filename(work_title)}.html"
                    filepath = OUTPUT_DIR / filename
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    self.downloaded += 1
                    return True
                else:
                    self.failed += 1
                    return False
                    
        except Exception as e:
            self.failed += 1
            return False
    
    def clean_filename(self, title: str) -> str:
        """Clean work title for filename."""
        # Remove TLG reference and clean up
        clean = title.split('::')[-1].strip() if '::' in title else title
        clean = clean.replace(' ', '_').replace('/', '_').replace('\\', '_')
        # Keep only safe characters
        safe_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-'
        clean = ''.join(c for c in clean if c in safe_chars)
        return clean[:50]  # Limit length
    
    async def download_sample_works(self, max_works: int = 10):
        """Download a sample of works for testing."""
        print(f"📁 Downloading {max_works} sample works as HTML files...")
        
        catalog = self.load_catalog()
        
        # Get priority authors
        priority_authors = ['tlg0012', 'tlg0059', 'tlg0086', 'tlg0011', 'tlg0006']
        
        downloaded = 0
        for author_key in priority_authors:
            if author_key in catalog and downloaded < max_works:
                author_data = catalog[author_key]
                author_id = author_key.replace('tlg', '')
                author_name = author_data['name']
                
                print(f"📚 {author_name} (TLG{author_id})")
                
                works = author_data.get('works', {})
                for work_key, work_data in list(works.items())[:2]:  # Max 2 works per author
                    if downloaded >= max_works:
                        break
                        
                    work_id = work_key.replace('tlg', '')
                    work_title = work_data.get('title', f'Work {work_id}')
                    
                    print(f"   🔍 Downloading: {work_title}")
                    
                    success = await self.download_work_html(author_id, work_id, work_title)
                    if success:
                        print(f"   ✅ Saved: TLG{author_id}_{work_id}_{self.clean_filename(work_title)}.html")
                        downloaded += 1
                    else:
                        print(f"   ❌ Failed to download")
                    
                    await asyncio.sleep(1.5)  # Respectful delay
        
        print(f"\n📊 Download complete!")
        print(f"   ✅ Downloaded: {self.downloaded}")
        print(f"   ❌ Failed: {self.failed}")
        print(f"   📁 Files saved to: {OUTPUT_DIR}")
        
        # List downloaded files
        html_files = list(OUTPUT_DIR.glob("*.html"))
        if html_files:
            print(f"\n📄 Downloaded HTML files:")
            for file in html_files[:10]:
                size_kb = file.stat().st_size / 1024
                print(f"   📄 {file.name} ({size_kb:.1f}KB)")

async def main():
    """Download sample HTML files."""
    downloader = SimpleHTMLDownloader()
    
    try:
        await downloader.setup()
        await downloader.download_sample_works(max_works=10)
    finally:
        await downloader.cleanup()

if __name__ == "__main__":
    asyncio.run(main())


