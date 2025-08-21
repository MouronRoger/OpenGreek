# TLG Emergency Extraction - User Guide

## 🚀 Quick Start

Your TLG extraction system is **ready for production** with full visual feedback and eulogos compatibility!

### Run Complete Discovery + Cataloging
```bash
cd /Users/james/GitHub/OpenGreek/OpenGreek
python tlg_visual_extractor.py
```

This will:
- 📊 Discover all TLG authors with real-time progress bars
- 📚 Find all works for each author with visual feedback  
- 💾 Save eulogos-compatible catalog files
- 📈 Display live statistics throughout the process

## 📁 Output Files (Eulogos Compatible)

After running discovery, you'll find these files in `data/tlg/catalogues/`:

### `tlg_author_index.json` 
Compatible with your `/Users/james/GitHub/eulogos/author_index.json` format:
```json
{
  "tlg0012": {
    "name": "Homer",
    "century": -8,
    "type": "Poet"
  }
}
```

### `tlg_integrated_catalog.json`
Compatible with your `/Users/james/GitHub/eulogos/integrated_catalog.json` format:
```json
{
  "tlg0012": {
    "name": "Homer",
    "urn": "urn:cts:greekLit:tlg0012",
    "century": -8,
    "type": "Poet",
    "works": {
      "tlg001": {
        "title": "Iliad",
        "urn": "urn:cts:greekLit:tlg0012.tlg001",
        "language": "grc"
      }
    }
  }
}
```

## 🎯 Visual Feedback Features

### Progress Visualization
```
📊 PHASE: DISCOVERY
📝 Parsing TLG alphabetic index for all authors...
================================================================

Parsing authors: |████████████████████████████████████████████████| 1247/1247 (100.0%)

📈 CURRENT STATISTICS:
   📚 Authors discovered: 3247
   📖 Works discovered: 9856
   ⚡ Works processed: 1250
   ✅ Successful extractions: 1180
   ❌ Failed extractions: 70
```

### Phase Organization
1. **🔍 DISCOVERY** - Parse TLG index for all authors
2. **📚 WORK DISCOVERY** - Find all works for each author  
3. **⚡ EXTRACTION** - Extract Greek texts (optional)
4. **✅ VALIDATION** - Validate and organize results

## 🎛️ Usage Options

### Discovery Only (Recommended First)
```bash
python tlg_visual_extractor.py
# Choose "N" when asked about sample extraction
```

### Full Extraction (Emergency Mode)
```bash
python tlg_visual_extractor.py  
# Choose "y" when asked about sample extraction
```

### Priority Authors Only
Modify the `priority_authors` list in the script:
```python
priority_authors = ['0012', '0059', '0086', '0011', '0006']  # Homer, Plato, Aristotle, Sophocles, Euripides
```

## 🔧 Integration with Eulogos

Your extracted catalogs can be directly used with eulogos:

1. **Copy catalog files:**
```bash
cp data/tlg/catalogues/tlg_author_index.json /Users/james/GitHub/eulogos/tlg_author_index.json
cp data/tlg/catalogues/tlg_integrated_catalog.json /Users/james/GitHub/eulogos/tlg_integrated_catalog.json
```

2. **Merge with existing eulogos catalogs** (if desired):
```python
import json

# Load existing eulogos data
with open('/Users/james/GitHub/eulogos/author_index.json') as f:
    eulogos_authors = json.load(f)

# Load TLG data  
with open('data/tlg/catalogues/tlg_author_index.json') as f:
    tlg_authors = json.load(f)

# Merge
combined = {**eulogos_authors, **tlg_authors}

# Save combined catalog
with open('combined_author_index.json', 'w') as f:
    json.dump(combined, f, indent=2, sort_keys=True)
```

## ⚡ Emergency Extraction Protocol

If you need to extract **immediately** due to time constraints:

### Fast Priority Extraction
```bash
python -c "
import asyncio
from tlg_visual_extractor import TLGVisualExtractor

async def emergency_priority():
    extractor = TLGVisualExtractor()
    await extractor.setup()
    await extractor.run_discovery_phase()
    await extractor.run_extraction_phase_sample(max_authors=10)
    await extractor.cleanup()

asyncio.run(emergency_priority())
"
```

This extracts the top 10 most important authors with visual feedback.

## 🔍 Monitoring Progress

### Real-time Statistics
- **Authors discovered**: Live count during index parsing
- **Works found**: Per-author work discovery with progress bars
- **Extraction success rate**: Success/failure ratios with emoji indicators
- **Processing speed**: Time estimates and completion projections

### Log Files
- `logs/tlg_visual_extraction.log` - Detailed extraction log
- `data/tlg/catalogues/tlg_extraction_statistics.json` - Final statistics

## 🚨 Troubleshooting

### Connection Issues
If you see connection errors:
```
⚠️  HTTP 503, retrying in 2.0s...
🔄 Connection error, retry 2/3 in 4.0s...
```
This is normal - the system will retry automatically with exponential backoff.

### Interrupted Extraction
The system is designed to handle interruptions gracefully:
- Press `Ctrl+C` to stop safely
- Discovery progress is saved incrementally
- Can resume from catalog files

### Memory Issues
For very large extractions:
```python
# Reduce batch sizes in tlg_visual_extractor.py
max_consecutive_misses = 10  # Reduce from 20
work_id % 5 == 0:  # More frequent delays
```

## 🎉 Success Indicators

You'll know everything is working when you see:

```
🎉 DISCOVERY PHASE COMPLETE!
📚 Authors discovered: 3247
📖 Total works discovered: 9856
⏱️  Time taken: 45.2 minutes

📁 Output files:
   • tlg_author_index.json (eulogos-compatible author index)
   • tlg_integrated_catalog.json (eulogos-compatible full catalog)  
   • tlg_extraction_statistics.json (detailed statistics)
```

## 🔗 Next Steps

1. **Verify Results**: Check catalog files for completeness
2. **Test Integration**: Import into eulogos system
3. **Run Full Extraction**: Extract actual Greek texts (time permitting)
4. **Backup Everything**: Multiple copies of catalog files

---

**🏛️ The complete TLG corpus is now discoverable and cataloged with full scholarly reference preservation!**

