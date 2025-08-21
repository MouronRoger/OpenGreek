#!/usr/bin/env python3
"""Quick analysis of TLG table structure to find where Greek text actually is."""

import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def map_table_structure():
    print("🔍 MAPPING TLG TABLE STRUCTURE")
    print("="*50)
    
    url = "http://217.71.231.54:8080/TLG2064/2064_002.htm"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                content = await response.text()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find main content table
        tables = soup.find_all('table')
        print(f"📋 Found {len(tables)} tables")
        
        # Analyze the main table (likely the largest one)
        main_table = None
        max_content = 0
        
        for table in tables:
            table_text = table.get_text()
            greek_chars = sum(1 for c in table_text if '\u0370' <= c <= '\u03FF' or '\u1F00' <= c <= '\u1FFF')
            if greek_chars > max_content:
                max_content = greek_chars
                main_table = table
        
        if main_table:
            print(f"🎯 Main table has {max_content:,} Greek characters")
            
            # Analyze row structure
            rows = main_table.find_all('tr')
            print(f"📊 Table has {len(rows)} rows")
            
            # Look at first 10 data rows to understand structure
            data_rows = [row for row in rows if row.find_all(['td', 'th']) and len(row.find_all(['td', 'th'])) > 1][:10]
            
            print(f"\n📋 ANALYZING ROW STRUCTURE:")
            for i, row in enumerate(data_rows):
                cells = row.find_all(['td', 'th'])
                print(f"\nRow {i+1}: {len(cells)} cells")
                
                for j, cell in enumerate(cells):
                    cell_text = cell.get_text().strip()
                    greek_chars = sum(1 for c in cell_text if '\u0370' <= c <= '\u03FF' or '\u1F00' <= c <= '\u1FFF')
                    
                    if len(cell_text) > 0:
                        print(f"   Cell {j+1}: {len(cell_text)} chars, {greek_chars} Greek")
                        print(f"      Content: {cell_text[:80]}{'...' if len(cell_text) > 80 else ''}")
                        
                        if greek_chars > 50:
                            print(f"      🎉 HIGH GREEK CONTENT!")
            
            # Test different extraction strategies
            print(f"\n🔧 TESTING EXTRACTION STRATEGIES:")
            
            # Strategy 1: All cells with substantial Greek
            all_cells = main_table.find_all(['td', 'th'])
            greek_cells = []
            
            for cell in all_cells:
                text = cell.get_text().strip()
                if len(text) > 20:
                    greek_chars = sum(1 for c in text if '\u0370' <= c <= '\u03FF' or '\u1F00' <= c <= '\u1FFF')
                    greek_ratio = greek_chars / len(text) if text else 0
                    
                    if greek_ratio > 0.5 and greek_chars > 50:
                        greek_cells.append(text)
            
            print(f"Strategy 1 - High Greek cells: Found {len(greek_cells)} cells")
            if greek_cells:
                combined_greek = '\n'.join(greek_cells)
                total_greek_chars = sum(1 for c in combined_greek if '\u0370' <= c <= '\u03FF' or '\u1F00' <= c <= '\u1FFF')
                print(f"   📊 Combined: {len(combined_greek)} chars, {total_greek_chars} Greek")
                print(f"   📝 Sample: {combined_greek[:200]}...")
            
            return len(greek_cells) > 0
        
        return False
        
    except Exception as e:
        print(f"💥 Error: {e}")
        return False

# Run quick analysis
result = asyncio.run(map_table_structure())
print(f"\n🎯 Greek content found: {'✅ YES' if result else '❌ NO'}")



