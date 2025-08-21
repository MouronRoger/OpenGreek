#!/usr/bin/env python3
"""Fix TLG extraction based on actual page structure analysis."""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json

async def analyze_actual_tlg_structure():
    """Analyze the actual TLG page structure to fix extraction."""
    print("🔍 ANALYZING ACTUAL TLG PAGE STRUCTURE")
    print("="*50)
    
    test_url = "http://217.71.231.54:8080/TLG2064/2064_002.htm"
    print(f"📖 Testing with: {test_url}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(test_url) as response:
                if response.status != 200:
                    print(f"❌ Failed: HTTP {response.status}")
                    return
                
                content = await response.text()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find the main content table
        tables = soup.find_all('table')
        print(f"📋 Found {len(tables)} tables on page")
        
        # Analyze table structure
        for i, table in enumerate(tables):
            rows = table.find_all('tr')
            print(f"\n📊 Table {i+1}: {len(rows)} rows")
            
            if rows:
                # Check first few rows
                for j, row in enumerate(rows[:5]):
                    cells = row.find_all('td')
                    print(f"   Row {j+1}: {len(cells)} cells")
                    
                    if len(cells) >= 2:
                        left_cell = cells[0].get_text().strip()
                        right_cell = cells[1].get_text().strip()
                        
                        # Count Greek in each cell
                        left_greek = sum(1 for c in left_cell if '\u0370' <= c <= '\u03FF' or '\u1F00' <= c <= '\u1FFF')
                        right_greek = sum(1 for c in right_cell if '\u0370' <= c <= '\u03FF' or '\u1F00' <= c <= '\u1FFF')
                        
                        print(f"      Left: {len(left_cell)} chars, {left_greek} Greek")
                        print(f"      Right: {len(right_cell)} chars, {right_greek} Greek")
                        
                        if right_greek > 50:  # Substantial Greek in right column
                            print(f"      🎉 RIGHT COLUMN HAS GREEK TEXT!")
                            print(f"      📝 Sample: {right_cell[:100]}...")
                        
                        if j == 0:  # Show full content of first meaningful row
                            print(f"      📖 Left cell: {left_cell}")
                            print(f"      📖 Right cell: {right_cell[:200]}...")
                
                # Test extraction strategies
                print(f"\n🔧 TESTING EXTRACTION STRATEGIES:")
                
                # Strategy 1: Get only right column cells
                right_column_cells = []
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        right_column_cells.append(cells[1])
                
                if right_column_cells:
                    right_column_text = ' '.join(cell.get_text().strip() for cell in right_column_cells)
                    right_greek = sum(1 for c in right_column_text if '\u0370' <= c <= '\u03FF' or '\u1F00' <= c <= '\u1FFF')
                    
                    print(f"   Strategy 1 - Right column only:")
                    print(f"      📊 {len(right_column_text)} chars, {right_greek} Greek ({right_greek/len(right_column_text)*100:.1f}%)")
                    
                    if right_greek > 1000:
                        print(f"      ✅ EXCELLENT! Right column has substantial Greek text")
                        print(f"      📝 Sample: {right_column_text[:200]}...")
                        
                        # Save the corrected extraction method
                        return "right_column_only"
        
        # Strategy 2: Look for cells with high Greek ratio
        all_cells = soup.find_all('td')
        high_greek_cells = []
        
        for cell in all_cells:
            text = cell.get_text().strip()
            if len(text) > 50:
                greek_chars = sum(1 for c in text if '\u0370' <= c <= '\u03FF' or '\u1F00' <= c <= '\u1FFF')
                greek_ratio = greek_chars / len(text) if text else 0
                
                if greek_ratio > 0.8 and greek_chars > 100:
                    high_greek_cells.append({
                        'text': text,
                        'greek_chars': greek_chars,
                        'greek_ratio': greek_ratio
                    })
        
        print(f"\n   Strategy 2 - High Greek ratio cells:")
        print(f"      📊 Found {len(high_greek_cells)} cells with >80% Greek content")
        
        if high_greek_cells:
            best_cell = max(high_greek_cells, key=lambda x: x['greek_chars'])
            print(f"      🎉 Best cell: {best_cell['greek_chars']} Greek chars")
            print(f"      📝 Sample: {best_cell['text'][:200]}...")
            return "high_greek_ratio"
        
        return None
        
    except Exception as e:
        print(f"💥 Error: {e}")
        return None

# Run the analysis
result = asyncio.run(analyze_actual_tlg_structure())
print(f"\n🎯 RECOMMENDED EXTRACTION METHOD: {result}")

if result == "right_column_only":
    print("✅ Solution: Extract only the right column of the main table")
    print("🔧 Selector: 'table tr td:nth-child(2)'")
elif result == "high_greek_ratio":  
    print("✅ Solution: Filter cells by Greek character ratio")
    print("🔧 Method: Select cells with >80% Greek content")
else:
    print("❌ Need more investigation")



