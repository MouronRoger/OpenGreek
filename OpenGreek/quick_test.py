#!/usr/bin/env python3
"""Quick test to verify Greek text extraction - completes in under 30 seconds."""

import json
import sys

def main():
    """Fast analysis of extraction results."""
    try:
        print("🔍 QUICK ANALYSIS: What did we actually extract?")
        
        # Check our Homer extraction
        with open('data/tlg/full_corpus/tlg_corpus_results_500.json', 'r') as f:
            data = json.load(f)
        
        # Find Homer work
        homer_work = None
        for work in data['extracted_works'][:20]:  # Only check first 20
            ref = work.get('tlg_reference', {})
            if ref.get('author_id') == '0012':
                homer_work = work
                break
        
        if homer_work:
            text = homer_work['text_structure']['raw_text']
            print(f"\n📖 HOMER EXTRACTION RESULT:")
            print(f"   Length: {len(text)} chars")
            print(f"   First 200 chars: {text[:200]}")
            
            # Count Greek characters
            greek_chars = sum(1 for c in text if '\u0370' <= c <= '\u03FF' or '\u1F00' <= c <= '\u1FFF')
            print(f"   Greek chars: {greek_chars} ({greek_chars/len(text)*100:.1f}%)")
            
            # Check if this looks like actual Iliad
            has_menin = 'μῆνιν' in text.lower()
            has_achilleos = 'ἀχιλῆος' in text.lower()
            
            print(f"\n🎯 ILIAD CONTENT CHECK:")
            print(f"   Contains 'μῆνιν': {has_menin}")
            print(f"   Contains 'ἀχιλῆος': {has_achilleos}")
            
            if has_menin and has_achilleos:
                print("   ✅ This IS actual Iliad content!")
            else:
                print("   ❌ This is NOT actual Iliad content - just metadata")
        else:
            print("❌ No Homer work found in extraction")
        
        print(f"\n🎯 CONCLUSION:")
        if homer_work and greek_chars > 1000:
            print("✅ Greek text extraction IS working!")
        else:
            print("❌ Greek text extraction needs fixing")
            print("💡 Need to fix HTML selectors to get actual text content")
    
    except FileNotFoundError:
        print("❌ Extraction results file not found")
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()



