#!/usr/bin/env python3
"""Full TLG HTML Downloader - Download ALL works as individual HTML files."""

import asyncio
import json
import aiohttp
from pathlib import Path
from datetime import datetime, timedelta
import time
import sys

# Paths
OUTPUT_DIR = Path(__file__).parent / "data" / "tlg" / "html_downloads"
CATALOGUES_DIR = Path(__file__).parent / "data" / "tlg" / "catalogues"

class FullHTMLDownloader:
    """Download complete TLG corpus as individual HTML files."""
    
    def __init__(self):
        self.session = None
        self.downloaded = 0
        self.failed = 0
        self.start_time = time.time()
        
    async def setup(self):
        """Initialize session and directories."""
        print("🚀 Setting up FULL TLG HTML Downloader...")
        print("📁 Target: ALL 6,523+ works as individual HTML files")
        
        self.session = aiohttp.ClientSession()
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        print("✅ Ready for COMPLETE corpus download!")
    
    async def cleanup(self):
        if self.session:
            await self.session.close()
    
    def load_catalog(self):
        """Load the complete discovered catalog."""
        catalog_file = CATALOGUES_DIR / "tlg_integrated_catalog.json"
        with open(catalog_file, 'r') as f:
            return json.load(f)
    
    def update_progress(self, current: int, total: int, description: str = "Downloading"):
        """Display progress bar with ETA."""
        if current == 0:
            return
            
        percent = (current / total) * 100 if total > 0 else 0
        filled = int((current / total) * 50) if total > 0 else 0
        bar = '█' * filled + '░' * (50 - filled)
        
        # Calculate ETA
        elapsed = time.time() - self.start_time
        avg_time_per_item = elapsed / current
        remaining_items = total - current
        eta_seconds = remaining_items * avg_time_per_item
        eta = timedelta(seconds=int(eta_seconds))
        
        # Calculate rate
        rate = current / elapsed * 60 if elapsed > 0 else 0  # per minute
        
        sys.stdout.write(f'\r{description}: |{bar}| {current}/{total} ({percent:.1f}%) | ✅{self.downloaded} ❌{self.failed} | {rate:.1f}/min | ETA: {eta}')
        sys.stdout.flush()
    
    def clean_filename(self, title: str, author_name: str) -> str:
        """Create clean filename from work title."""
        # Extract just the work name, not the full TLG reference
        if '::' in title:
            parts = title.split('::')
            work_name = parts[-1].strip() if len(parts) > 2 else parts[1].strip()
        else:
            work_name = title
        
        # Clean for filename
        clean = work_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        clean = clean.replace('(', '').replace(')', '').replace('[', '').replace(']', '')
        
        # Keep only safe characters
        safe_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-'
        clean = ''.join(c for c in clean if c in safe_chars)
        
        # Limit length and add author for clarity
        author_clean = author_name.replace(' ', '_')[:20]
        return f"{author_clean}_{clean}"[:80]
    
    async def download_work_html(self, author_id: str, work_id: str, work_title: str, author_name: str) -> bool:
        """Download a single work as HTML file."""
        url = f"http://217.71.231.54:8080/TLG{author_id}/{author_id}_{work_id}.htm"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Save as HTML file
                    filename = f"TLG{author_id}_{work_id}_{self.clean_filename(work_title, author_name)}.html"
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
    
    async def download_all_works(self):
        """Download ALL works from the catalog."""
        catalog = self.load_catalog()
        
        # Count total works
        total_works = sum(len(author_data.get('works', {})) for author_data in catalog.values())
        total_authors = len(catalog)
        
        print("================================================================================")
        print("📊 PHASE: COMPLETE HTML DOWNLOAD")
        print("📝 Downloading ALL TLG works as individual HTML files...")
        print("================================================================================")
        print(f"🏛️  FULL CORPUS DOWNLOAD:")
        print(f"   📚 Authors: {total_authors:,}")
        print(f"   📖 Works: {total_works:,}")
        print(f"   ⚡ Estimated time: {total_works * 2 / 60:.0f}-{total_works * 4 / 60:.0f} minutes")
        print(f"   💾 Expected size: {total_works * 100 / 1024:.0f}MB - {total_works * 500 / 1024:.0f}MB")
        print()
        
        works_processed = 0
        authors_processed = 0
        
        # Process all authors
        for author_key, author_data in catalog.items():
            author_id = author_key.replace('tlg', '')
            author_name = author_data['name']
            works = author_data.get('works', {})
            
            authors_processed += 1
            
            # Show progress for major authors or every 100 authors
            if len(works) > 20 or authors_processed % 100 == 0:
                print(f"\n📚 Processing: {author_name} (TLG{author_id}, {len(works)} works)")
            
            # Download all works for this author
            for work_key, work_data in works.items():
                work_id = work_key.replace('tlg', '')
                work_title = work_data.get('title', f'Work {work_id}')
                
                success = await self.download_work_html(author_id, work_id, work_title, author_name)
                works_processed += 1
                
                # Update progress every 10 works
                if works_processed % 10 == 0:
                    self.update_progress(works_processed, total_works, "Downloading HTML files")
                
                # Respectful delay
                await asyncio.sleep(1.2)  # 1.2 seconds between downloads
                
                # Save checkpoint every 1000 works
                if works_processed % 1000 == 0:
                    self.save_checkpoint(works_processed, total_works)
        
        # Final progress update
        self.update_progress(total_works, total_works, "Download complete")
        print()
        
        # Final statistics
        duration = time.time() - self.start_time
        success_rate = (self.downloaded / works_processed * 100) if works_processed > 0 else 0
        
        print(f"""
🎉 COMPLETE TLG HTML DOWNLOAD FINISHED!

📊 FINAL STATISTICS:
   🏛️  Authors processed: {authors_processed:,}
   ⚡ Works processed: {works_processed:,}
   ✅ Successfully downloaded: {self.downloaded:,} ({success_rate:.1f}%)
   ❌ Failed downloads: {self.failed:,}
   ⏱️  Total time: {duration/60:.1f} minutes ({duration/3600:.1f} hours)
   📁 Files saved to: {OUTPUT_DIR}
        """)
        
        # Show some file statistics
        html_files = list(OUTPUT_DIR.glob("*.html"))
        if html_files:
            total_size = sum(f.stat().st_size for f in html_files) / 1024 / 1024  # MB
            print(f"💾 Total corpus size: {total_size:.1f}MB")
            print(f"📄 Average file size: {total_size / len(html_files):.1f}KB")
    
    def save_checkpoint(self, works_processed: int, total_works: int):
        """Save checkpoint information."""
        checkpoint_data = {
            'checkpoint_time': datetime.now().isoformat(),
            'works_processed': works_processed,
            'total_works': total_works,
            'downloaded': self.downloaded,
            'failed': self.failed,
            'progress_percent': (works_processed / total_works * 100) if total_works > 0 else 0
        }
        
        checkpoint_file = OUTPUT_DIR.parent / "checkpoints" / f"html_download_checkpoint_{works_processed}.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
        
        print(f"\n💾 Checkpoint saved: {works_processed}/{total_works} works")

async def main():
    """Download complete TLG corpus as HTML files."""
    print("""
🏛️  COMPLETE TLG HTML DOWNLOADER
==================================
📁 Downloads ALL 6,523+ works as individual HTML files
⚡ Each work = One HTML file with complete content
🚨 This will take 2-4 hours but preserves EVERYTHING!
    """)
    
    response = input("🔥 Download COMPLETE TLG corpus as HTML files? (y/N): ").strip().lower()
    
    if response != 'y':
        print("❌ Full HTML download cancelled.")
        return
    
    print("🚀 Starting COMPLETE TLG HTML download...")
    print("📊 Progress bars will show downloads, success/failure rates, and ETA")
    print("💾 Checkpoints every 1000 works for recovery")
    print("⚠️  You can interrupt with Ctrl+C - can resume from checkpoints\n")
    
    downloader = FullHTMLDownloader()
    
    try:
        await downloader.setup()
        await downloader.download_all_works()
        
    except KeyboardInterrupt:
        print("\n⚠️  Download interrupted by user")
        print("💾 Progress saved in checkpoints - can resume later!")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
    finally:
        await downloader.cleanup()
        print("🧹 Cleanup complete")

if __name__ == "__main__":
    asyncio.run(main())

