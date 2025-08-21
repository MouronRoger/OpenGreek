# TLG Corpus Extraction

Comprehensive extraction of the complete Thesaurus Linguae Graecae (TLG) corpus from http://217.71.231.54:8080/. This system discovers and extracts all available ancient Greek texts, creating the most complete digital corpus of Greek literature.

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Discover all TLG authors and works**:
   ```bash
   python discover_tlg.py
   ```

3. **Extract all Greek texts**:
   ```bash
   python extract_tlg.py
   ```

## Two-Stage Process

### Stage 1: Discovery (`discover_tlg.py`)
- Parses the TLG alphabetic index to find all authors
- Discovers all available works for each author
- Creates comprehensive catalogue: `data/tlg/tlg_catalogue.json`
- Estimated: 3,000+ authors, 10,000+ works

### Stage 2: Extraction (`extract_tlg.py`)
- Extracts Greek text from all discovered works
- Validates Greek content (minimum 30% Greek characters)
- Produces multiple output formats

## Output Files

All files are saved to `data/tlg/`:

- **`tlg_corpus.json`** - Complete structured corpus with metadata
- **`tlg_texts.txt`** - Plain text Greek corpus
- **`tlg_stats.json`** - Extraction statistics and metrics
- **`tlg_catalogue.json`** - Author and work inventory

## Configuration

Edit `config.yaml` to customize:

```yaml
extraction:
  rate_limit:
    base_delay: 1.0  # Seconds between requests
  content_validation:
    greek_threshold: 0.3  # Minimum Greek character ratio
    min_text_length: 50   # Minimum text length
```

## Key Features

### Robust Discovery
- Parses TLG alphabetic index systematically
- Tests all possible work URLs for each author
- Handles both encoded and unencoded URL formats
- Comprehensive error handling and retry logic

### Quality Greek Text Extraction
- Multiple HTML selector strategies
- Greek Unicode validation (U+0370-U+03FF, U+1F00-U+1FFF)
- Text normalization to NFC form
- Filters out navigation and metadata

### Respectful Crawling
- Configurable rate limiting (default: 1 second delays)
- Exponential backoff on errors
- Progress checkpointing and resume capability
- Conservative timeout and retry settings

## Expected Results

- **Authors**: 3,000+ (Homer to Byzantine period)
- **Works**: 10,000+ individual texts
- **Corpus Size**: ~500MB of Greek text
- **Coverage**: Complete surviving ancient Greek literature
- **Time Period**: 8th century BC to 15th century AD

## Monitoring Progress

```bash
# Watch discovery progress
tail -f data/tlg/tlg_catalogue.json

# Watch extraction progress
tail -f data/tlg/tlg_stats.json
```

## Architecture

This system is adapted from proven Daphnet extraction patterns:

- **Async HTTP**: Efficient concurrent processing
- **Error Handling**: Robust retry logic with exponential backoff
- **Checkpointing**: Resume capability for long-running extractions
- **Validation**: Greek text quality assurance
- **Multiple Formats**: JSON, plain text, and statistics

## Integration

The extracted corpus is designed for:

- **Digital Humanities Research**: Complete Greek literature analysis
- **Language Learning**: Comprehensive Greek text corpus
- **Computational Linguistics**: Large-scale Greek text processing
- **Web Platform**: Foundation for searchable digital library

## Legal and Ethical Use

- Academic and research use
- Respectful server crawling with delays
- Proper attribution to TLG project
- No commercial redistribution without permission

## Next Steps

This extraction system provides the foundation for:

1. **Public Web Platform**: Searchable digital library
2. **Research APIs**: Programmatic access to Greek corpus
3. **Educational Tools**: Greek language learning resources
4. **Digital Humanities**: Computational analysis platform

The complete TLG corpus represents the most comprehensive collection of ancient Greek literature available for computational research and digital scholarship.
