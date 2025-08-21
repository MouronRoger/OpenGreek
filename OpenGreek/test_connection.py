#!/usr/bin/env python3
"""Test TLG site connection and basic structure.

Quick test script to verify the TLG site is accessible and 
validate our understanding of the HTML structure.
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import yaml
from pathlib import Path

# Load config
CONFIG_FILE = Path(__file__).parent / "config.yaml"
with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    CONFIG = yaml.safe_load(f)

BASE_URL = CONFIG["source"]["base_url"]
INDEX_URL = f"{BASE_URL}{CONFIG['source']['index_url']}"

async def test_connection():
    """Test basic connection to TLG site."""
    print(f"Testing connection to: {INDEX_URL}")
    
    headers = {'User-Agent': CONFIG["source"]["user_agent"]}
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
        try:
            async with session.get(INDEX_URL) as response:
                print(f"Status: {response.status}")
                print(f"Content-Type: {response.headers.get('content-type', 'Unknown')}")
                
                if response.status == 200:
                    content = await response.text()
                    print(f"Content length: {len(content)} characters")
                    
                    # Parse and analyze structure
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Look for tables (likely structure)
                    tables = soup.find_all('table')
                    print(f"Found {len(tables)} tables")
                    
                    # Look for TLG references
                    tlg_links = soup.find_all('a', href=True)
                    tlg_count = 0
                    sample_links = []
                    
                    for link in tlg_links:
                        href = link.get('href', '')
                        text = link.get_text()
                        if 'TLG' in text or 'TLG' in href:
                            tlg_count += 1
                            if len(sample_links) < 5:
                                sample_links.append((text.strip(), href))
                    
                    print(f"Found {tlg_count} TLG-related links")
                    print("Sample TLG links:")
                    for text, href in sample_links:
                        print(f"  {text} -> {href}")
                    
                    # Look for table rows with author data
                    rows = soup.find_all('tr')
                    author_rows = 0
                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) >= 3:
                            first_cell_text = cells[0].get_text().strip()
                            if 'TLG' in first_cell_text:
                                author_rows += 1
                    
                    print(f"Found {author_rows} potential author rows")
                    
                    # Test a specific author page
                    await test_author_page(session, "0012")  # Homer
                    
                else:
                    print(f"Failed to fetch index: HTTP {response.status}")
                    
        except Exception as e:
            print(f"Error: {e}")

async def test_author_page(session, tlg_id):
    """Test accessing a specific author's works."""
    print(f"\nTesting author TLG{tlg_id} (Homer)...")
    
    # Try different URL formats
    test_urls = [
        f"{BASE_URL}/TLG{tlg_id}/{tlg_id}_001.htm",
        f"{BASE_URL}/TLG{tlg_id}/{tlg_id}%5F001.htm"
    ]
    
    for url in test_urls:
        try:
            async with session.get(url) as response:
                print(f"  {url} -> HTTP {response.status}")
                if response.status == 200:
                    content = await response.text()
                    print(f"    Content length: {len(content)} characters")
                    
                    # Quick Greek text check
                    greek_chars = sum(1 for c in content if '\u0370' <= c <= '\u03FF' or '\u1F00' <= c <= '\u1FFF')
                    if greek_chars > 100:
                        print(f"    Contains substantial Greek text ({greek_chars} Greek characters)")
                    else:
                        print(f"    Limited Greek content ({greek_chars} Greek characters)")
                    break
        except Exception as e:
            print(f"    Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
