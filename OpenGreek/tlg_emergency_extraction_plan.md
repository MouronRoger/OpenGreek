# Emergency TLG Corpus Extraction Plan
## University of Saint Petersburg - Complete Ancient Greek Literature Corpus

**CRITICAL TIMELINE: 7 Days Maximum**
**OBJECTIVE**: Extract complete TLG corpus before institutional access restrictions

---

## Day 1: Reconnaissance & Setup

### Hour 1-2: Site Analysis
```bash
# Quick site structure assessment
curl -I http://217.71.231.54:8080/indices/indexA.htm
curl -s http://217.71.231.54:8080/robots.txt
curl -s http://217.71.231.54:8080/indices/indexA.htm | grep -o 'TLG[0-9]\+' | sort -u | wc -l

# Test TLG URL patterns
curl -I http://217.71.231.54:8080/TLG0012/0012_001.htm  # Homer Iliad
curl -I http://217.71.231.54:8080/TLG0059/0059_001.htm  # Plato Republic
```

### Hour 3-4: Infrastructure Setup
```bash
mkdir tlg_emergency_extraction
cd tlg_emergency_extraction

# Create directory structure
mkdir -p {data/{raw,processed,checkpoints},logs,scripts,backups}

# Setup parallel extraction environment
pip install aiohttp asyncio beautifulsoup4 aiofiles
```

### Hour 5-8: Test Extraction
- Modify existing `extract_greek_site.py` for TLG structure
- Test with 10 high-priority works
- Measure server response patterns
- Establish baseline extraction rate

---

## Day 2: Index Discovery & Priority Extraction

### Morning: Complete Index Harvesting
```python
# Extract ALL TLG author entries from alphabetic index
# Target: Complete author list with TLG IDs (TLG0001-TLG9999+)
# Output: tlg_authors_complete.json

PRIORITY_AUTHORS = [
    'TLG0012',  # Homer
    'TLG0059',  # Plato  
    'TLG0086',  # Aristotle
    'TLG0011',  # Sophocles
    'TLG0006',  # Euripides
    'TLG0007',  # Aeschylus
    'TLG0016',  # Herodotus
    'TLG0003',  # Thucydides
]
```

### Afternoon: High-Priority Authors
- Extract complete works for top 20 most important authors
- Parallel extraction: 3 streams
- Rate limit: 1 second per request
- **Success Target**: 500+ works by end of day

---

## Day 3: Systematic Work Discovery

### All Day: Work URL Enumeration
```python
# For each discovered TLG author, generate all possible work URLs
# Pattern: /TLG{id}/{id}_{work:03d}.htm
# Range: 001-999 per author
# Method: Parallel HEAD requests to verify existence

async def discover_works(tlg_id):
    for work_num in range(1, 1000):
        url = f"http://217.71.231.54:8080/TLG{tlg_id}/{tlg_id}_{work_num:03d}.htm"
        # HEAD request to check existence
        # Build complete work inventory
```

**Target Output**: `tlg_works_complete.json` with 10,000+ verified work URLs

---

## Day 4-5: Aggressive Parallel Extraction

### Multi-Stream Extraction Strategy
```bash
# Launch 4 parallel extraction processes
python extract_tlg_range.py --start TLG0001 --end TLG2500 --stream 1 &
python extract_tlg_range.py --start TLG2501 --end TLG5000 --stream 2 &
python extract_tlg_range.py --start TLG5001 --end TLG7500 --stream 3 &
python extract_tlg_range.py --start TLG7501 --end TLG9999 --stream 4 &
```

### Extraction Parameters
- **Rate Limit**: 0.7 seconds per request (aggressive but sustainable)
- **Retry Logic**: 3 attempts with exponential backoff
- **Checkpoint Frequency**: Every 50 successful extractions
- **Quality Threshold**: 20% Greek character minimum
- **Timeout**: 30 seconds per request

### Real-Time Monitoring
```bash
# Monitor extraction progress
watch -n 10 'echo "Stream 1: $(wc -l < logs/stream1.log) | Stream 2: $(wc -l < logs/stream2.log)"'

# Monitor server health
watch -n 30 'curl -w "%{time_total}" -o /dev/null -s http://217.71.231.54:8080/TLG0012/0012_001.htm'
```

---

## Day 6: Gap Filling & Validation

### Morning: Completeness Analysis
```python
# Compare extracted works against discovered work inventory
# Identify missing works
# Prioritize high-value missing content

def find_extraction_gaps():
    discovered = load_json('tlg_works_complete.json')
    extracted = load_json('tlg_extracted_works.json')
    
    missing = []
    for work in discovered:
        if work['url'] not in extracted:
            missing.append(work)
    
    return sorted(missing, key=lambda x: x['priority'])
```

### Afternoon: Targeted Re-extraction
- Focus on failed/missing extractions
- Retry with different parameters
- Manual verification of important works

---

## Day 7: Final Validation & Emergency Backup

### Morning: Quality Assurance
```python
# Validate extraction completeness
EXPECTED_MINIMUMS = {
    'total_authors': 3000,
    'total_works': 8000,
    'homer_works': 2,      # Iliad + Odyssey minimum
    'plato_works': 25,     # Major dialogues
    'total_size_mb': 300,  # Estimated corpus size
}

def validate_corpus():
    stats = generate_corpus_stats()
    for metric, minimum in EXPECTED_MINIMUMS.items():
        assert stats[metric] >= minimum, f"Failed {metric}: {stats[metric]} < {minimum}"
```

### Afternoon: Multi-Location Backup
```bash
# Immediate backups to multiple locations
rsync -av --progress data/ /backup/location1/tlg_corpus_$(date +%Y%m%d)/
rsync -av --progress data/ /backup/location2/tlg_corpus_$(date +%Y%m%d)/

# Cloud backup
tar -czf tlg_complete_corpus_$(date +%Y%m%d).tar.gz data/
# Upload to multiple cloud providers

# Generate corpus statistics
python generate_final_stats.py > TLG_EXTRACTION_REPORT.txt
```

---

## Critical Implementation Scripts

### 1. Emergency TLG Extractor (`extract_tlg_emergency.py`)
```python
#!/usr/bin/env python3
import asyncio
import aiohttp
import aiofiles
from pathlib import Path
import json
import time
import logging

class EmergencyTLGExtractor:
    def __init__(self, stream_id: int = 1):
        self.stream_id = stream_id
        self.base_delay = 0.7
        self.session = None
        self.checkpoint_freq = 50
        self.extracted_count = 0
        
    async def extract_work(self, tlg_id: str, work_id: str):
        url = f"http://217.71.231.54:8080/TLG{tlg_id}/{tlg_id}_{work_id}.htm"
        # Implementation details...
        
    async def extract_range(self, start_tlg: str, end_tlg: str):
        # Parallel extraction implementation
        pass
        
    def save_checkpoint(self):
        # Save progress every N extractions
        pass
```

### 2. Work Discovery Script (`discover_tlg_works.py`)
```python
#!/usr/bin/env python3
async def discover_all_works():
    """Generate and verify all possible TLG work URLs"""
    authors = load_tlg_authors()
    
    for author in authors:
        tlg_id = author['tlg_id']
        for work_num in range(1, 1000):
            url = f"http://217.71.231.54:8080/TLG{tlg_id}/{tlg_id}_{work_num:03d}.htm"
            if await url_exists(url):
                yield {
                    'tlg_id': tlg_id,
                    'work_id': f"{work_num:03d}",
                    'url': url,
                    'author': author['name']
                }
```

### 3. Parallel Launcher (`launch_extraction.sh`)
```bash
#!/bin/bash
# Launch multiple extraction streams

echo "Starting emergency TLG extraction..."

python extract_tlg_emergency.py --start TLG0001 --end TLG2500 --stream 1 > logs/stream1.log 2>&1 &
python extract_tlg_emergency.py --start TLG2501 --end TLG5000 --stream 2 > logs/stream2.log 2>&1 &
python extract_tlg_emergency.py --start TLG5001 --end TLG7500 --stream 3 > logs/stream3.log 2>&1 &
python extract_tlg_emergency.py --start TLG7501 --end TLG9999 --stream 4 > logs/stream4.log 2>&1 &

echo "All streams launched. Monitor with: tail -f logs/stream*.log"
```

---

## Risk Mitigation

### Server Overload Prevention
- Monitor response times continuously
- Implement adaptive rate limiting
- Circuit breaker for 429/503 responses
- Fallback to sequential extraction if parallel fails

### Legal/Ethical Safeguards
- Content is ancient texts (public domain)
- Currently publicly accessible
- Academic fair use applies
- Preservation of cultural heritage

### Technical Failure Recovery
- Checkpoint every 50 works
- Multiple backup locations
- Resume capability from any checkpoint
- Redundant logging systems

---

## Success Metrics

### Minimum Viable Extraction
- **Homer**: Complete Iliad & Odyssey ✓
- **Plato**: 25+ major dialogues ✓
- **Aristotle**: Major works (Metaphysics, Ethics, etc.) ✓
- **Drama**: Complete Sophocles, Euripides, Aeschylus ✓
- **Total**: 5,000+ works minimum

### Optimal Complete Extraction
- **Authors**: 3,000+ unique TLG authors
- **Works**: 8,000+ individual texts
- **Coverage**: 95%+ of publicly accessible TLG corpus
- **Quality**: 98%+ Greek text validation rate

---

## Post-Extraction Immediate Actions

### Day 8: Corpus Organization
```bash
# Organize extracted corpus
python organize_corpus.py --input data/raw --output data/organized

# Generate multiple formats
python generate_formats.py --corpus data/organized --formats txt,json,csv
```

### Day 9-10: Public Release Preparation
- Set up permanent hosting infrastructure
- Create basic search interface
- Prepare public announcement
- Ensure redundant backups

### Day 11+: Public Launch
- Launch public corpus website
- Announce to Greek studies communities
- Establish permanent access points
- Begin web platform development

---

## Emergency Contact Protocol

**If extraction is blocked/detected:**
1. Immediately pause all streams
2. Assess what was successfully extracted
3. Pivot to preservation of captured data
4. Implement alternative access strategies

**Communication channels:**
- Monitor extraction logs continuously
- Set up alerts for failure patterns
- Prepare alternative extraction methods

---

**REMEMBER: This is a time-critical operation. The complete TLG corpus being publicly accessible may be temporary. Extract aggressively but respectfully. The goal is to preserve this invaluable cultural heritage for permanent public access.**