#!/usr/bin/env python3
"""Test Greek text extraction with corrected selectors."""

import asyncio
import aiohttp
import yaml
from bs4 import BeautifulSoup
from pathlib import Path

# Load config
CONFIG_FILE = Path(__file__).parent / "config.yaml"
with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    CONFIG = yaml.safe_load(f)

async def test_greek_extraction():
    """Test extraction with corrected selectors."""
    print("🧪 TESTING CORRECTED GREEK TEXT EXTRACTION")
    print("="*60)
    
    # Test with Homer Iliad (we know this has Greek content)
    test_url = "http://217.71.231.54:8080/TLG0012/0012_001.htm"
    print(f"🎯 Testing URL: {test_url}")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(test_url) as response:
            if response.status != 200:
                print(f"❌ Failed to fetch: HTTP {response.status}")
                return
            
            content = await response.text()
            print(f"📄 Page content: {len(content):,} characters")
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Remove unwanted elements
    for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer']):
        element.decompose()
    
    print(f"\n🔍 TESTING SELECTORS:")
    
    # Test new primary selectors
    for selector in CONFIG["extraction"]["selectors"]["primary"]:
        print(f"\n📊 Testing selector: '{selector}'")
        
        elements = soup.select(selector)
        print(f"   📋 Found {len(elements)} elements")
        
        if elements:
            # Get text from all elements
            all_text = ' '.join(elem.get_text(separator=' ', strip=True) for elem in elements)
            
            # Count Greek characters
            greek_chars = sum(1 for c in all_text if '\u0370' <= c <= '\u03FF' or '\u1F00' <= c <= '\u1FFF')
            total_chars = len(all_text)
            greek_ratio = greek_chars / total_chars if total_chars > 0 else 0
            
            print(f"   📝 Total text: {total_chars:,} characters")
            print(f"   🏛️  Greek characters: {greek_chars:,}")
            print(f"   📊 Greek ratio: {greek_ratio:.3f} ({greek_ratio*100:.1f}%)")
            
            if greek_chars > 1000:
                print(f"   🎉 EXCELLENT! This selector finds substantial Greek text!")
                print(f"   📖 Sample text: {all_text[:200]}...")
                
                # Save a test extraction
                test_output = {
                    'test_url': test_url,
                    'selector_used': selector,
                    'text_stats': {
                        'total_chars': total_chars,
                        'greek_chars': greek_chars,
                        'greek_ratio': greek_ratio
                    },
                    'sample_text': all_text[:1000]  # First 1000 chars as sample
                }
                
                with open('test_extraction_sample.json', 'w', encoding='utf-8') as f:
                    import json
                    json.dump(test_output, f, ensure_ascii=False, indent=2)
                
                print(f"   💾 Test sample saved to: test_extraction_sample.json")
                return True
            else:
                print(f"   ❌ Not enough Greek content")
        else:
            print(f"   ❌ No elements found")
    
    return False

success = asyncio.run(test_greek_extraction())
if success:
    print(f"\n✅ EXTRACTION FIX CONFIRMED!")
    print(f"🔧 The corrected selectors can extract actual Greek text!")
    print(f"🚀 Ready to re-run extraction with proper Greek text extraction!")
else:
    print(f"\n❌ Still need to find the right selectors")



