# Cursor AI: TLG Emergency Extraction Setup Prompt

I'd like you to take a look at this folder and help me set up the data extraction aspect of this project, underlining the supreme importance of preserving references and tagging.

## Project Context

I've discovered that the University of Saint Petersburg has accidentally made the complete **Thesaurus Linguae Graecae (TLG) corpus** publicly accessible at `http://217.71.231.54:8080/`. This represents the most comprehensive collection of ancient Greek literature ever assembled - over 10,000 works from 3,000+ authors spanning Homer to the Byzantine period.

**This is a time-critical opportunity** - the university appears unaware of the public accessibility, and this access could be restricted at any moment. I need to extract the complete corpus quickly but systematically while preserving complete scholarly citation integrity.

## Critical Success Requirements

### 1. **Reference Preservation is PARAMOUNT**
Without proper TLG references, this extraction becomes academically worthless. Every extracted text MUST retain:

- **TLG Author ID** (e.g., `0012` for Homer)
- **TLG Work ID** (e.g., `001` for Iliad) 
- **Author metadata** (name, period, description)
- **Work metadata** (title, genre, traditional citation)
- **Internal structure** (books, lines, Stephanus pages, Bekker numbers)
- **Source URL** for verification/re-extraction

**Example Complete Reference:**
```
TLG 0012 001 1.1 = Homer, Iliad, Book 1, Line 1
Traditional Citation: Hom. Il. 1.1
Source: http://217.71.231.54:8080/TLG0012/0012_001.htm
```

### 2. **Systematic Extraction Architecture**
The site follows a predictable structure:
- **Index URL**: `http://217.71.231.54:8080/indices/indexA.htm`
- **Author Pattern**: `/TLG[AUTHOR_ID]/` (e.g., `/TLG0012/`)
- **Work Pattern**: `/TLG[AUTHOR_ID]/[AUTHOR_ID]_[WORK_ID].htm` (e.g., `/TLG0012/0012_001.htm`)

### 3. **Performance Requirements**
- **Target**: Complete corpus extraction in ~10 hours (single-threaded conservative approach)
- **Method**: Single extraction stream with systematic pacing
- **Rate Limiting**: 3-4 second delays between requests (respectful but steady)
- **Checkpointing**: Save progress every 50 works (resume capability)
- **Error Handling**: Robust retries with exponential backoff

## Technical Implementation Requirements

### Phase 1: Site Structure Analysis & Index Discovery
```python
# Required capabilities:
# 1. Parse alphabetic index to extract all TLG author entries
# 2. Build complete author inventory with metadata
# 3. Generate all possible work URLs for systematic crawling
# 4. Validate URL existence before full extraction
```

### Phase 2: Parallel Text Extraction with Reference Preservation
```python
# Required extraction data structure:
{
  "tlg_reference": {
    "author_id": "0012",
    "author_name": "HOMER", 
    "author_description": "Epic Poet",
    "period": "8th cent. BC",
    "work_id": "001",
    "work_title": "Iliad",
    "traditional_citation": "Hom. Il.",
    "genre": "Epic Poetry",
    "url": "http://217.71.231.54:8080/TLG0012/0012_001.htm"
  },
  "text_content": {
    "full_text": "μῆνιν ἄειδε θεὰ Πηληϊάδεω Ἀχιλῆος...",
    "structured_text": {
      "book_1": {
        "line_1": "μῆνιν ἄειδε θεὰ Πηληϊάδεω Ἀχιλῆος",
        "line_2": "οὐλομένην, ἣ μυρί᾽ Ἀχαιοῖς ἄλγε᾽ ἔθηκε"
      }
    }
  },
  "validation": {
    "greek_ratio": 0.95,
    "extraction_status": "success",
    "reference_completeness": true
  }
}
```

### Phase 3: Quality Assurance & Output Organization
```python
# Required outputs:
# 1. Individual work files with complete TLG metadata headers
# 2. Master reference index (JSON) for the entire corpus
# 3. Multiple organizational schemes (by author, period, genre)
# 4. Validation reports ensuring reference completeness
# 5. Citation mapping files for traditional scholarly abbreviations
```

## Existing Project Assets

You'll find I already have a `scaffold-source-texts` project with proven extraction patterns from the Daphnet Presocratics database. Key existing components:

- **Extraction architecture** in `/scripts/` with rate limiting and error handling
- **Greek text validation** using Unicode ranges and character ratios
- **Checkpoint/resume systems** for handling interruptions
- **Multiple output formats** (JSON, TXT, structured data)

**Leverage these patterns** but adapt for TLG's systematic structure and prioritize reference preservation.

## Implementation Specifications

### Directory Structure to Create
```
tlg_emergency_extraction/
├── scripts/
│   ├── discover_tlg_index.py     # Parse alphabetic index
│   ├── discover_tlg_works.py     # Find all works per author
│   ├── extract_tlg_parallel.py   # Main parallel extractor
│   ├── validate_references.py    # Quality assurance
│   └── organize_corpus.py        # Final organization
├── data/
│   ├── catalogues/               # Author/work inventories
│   ├── raw_extraction/           # Direct extraction results
│   ├── organized_corpus/         # Final structured output
│   ├── checkpoints/             # Resume points
│   └── validation_reports/       # Quality assurance
├── config/
│   └── tlg_config.yaml          # Extraction parameters
└── logs/                        # Extraction monitoring
```

### Configuration Requirements
```yaml
# tlg_config.yaml essentials:
extraction:
  base_url: "http://217.71.231.54:8080"
  parallel_streams: 1    # Single-threaded for simplicity and safety
  rate_limit: 3.5        # ~3.5 seconds between requests
  timeout: 30
  max_retries: 3
  checkpoint_frequency: 50

validation:
  min_greek_ratio: 0.2
  required_reference_fields:
    - tlg_author_id
    - tlg_work_id  
    - author_name
    - work_title
    - source_url

priority_authors:  # Extract these first
  - "0012"  # Homer
  - "0059"  # Plato
  - "0086"  # Aristotle
  - "0011"  # Sophocles
  - "0006"  # Euripides
```

### Key Technical Challenges to Address

1. **HTML Parsing Strategy**: TLG pages may use different selectors than Daphnet
2. **Reference Extraction**: Parse author/work metadata from HTML structure
3. **Internal Structure**: Preserve book/line divisions, traditional page references
4. **Traditional Citations**: Build mapping from TLG IDs to scholarly abbreviations
5. **Sequential Coordination**: Systematic single-stream extraction with reliable checkpointing
6. **Error Recovery**: Handle server timeouts, connection issues, malformed pages

### Validation Requirements

Every extracted work must pass:
- **Reference Completeness**: All required metadata fields present
- **Greek Text Quality**: Minimum character ratio validation
- **Traditional Citation**: Buildable scholarly reference format
- **Structural Integrity**: Internal divisions properly preserved
- **URL Mapping**: Source link maintained for verification

## Expected Deliverables

1. **Complete TLG Corpus** (~10,000 works) with full reference preservation
2. **Master Reference Index** enabling traditional scholarly citations
3. **Quality Validation Reports** confirming extraction completeness
4. **Multiple Output Formats** for different research applications
5. **Resume Capability** for handling any interruptions

## Execution Timeline

- **Hours 1-2**: Site analysis and test extraction setup
- **Hours 3-4**: Index discovery and work enumeration  
- **Hours 5-7**: Priority authors extraction (Homer, Plato, Aristotle)
- **Hours 8-10**: Systematic completion of remaining corpus
- **Hour 10+**: Quality validation and final organization

## Critical Success Metrics

- **Coverage**: 95%+ of accessible TLG works extracted
- **Reference Quality**: 100% of works have complete TLG metadata
- **Text Quality**: 95%+ of works pass Greek validation  
- **Citation Integrity**: Traditional scholarly references buildable for all works
- **Performance**: Complete extraction within 10-hour window

## Legal/Ethical Framework

- **Content**: Ancient Greek texts (public domain, pre-1500 AD)
- **Access**: Currently publicly accessible
- **Purpose**: Preservation and democratization of cultural heritage
- **Attribution**: Proper citation of TLG project and Saint Petersburg University
- **Method**: Respectful crawling with appropriate delays

---

**Please help me implement this emergency extraction system with absolute priority on preserving the scholarly reference integrity that makes this corpus academically valuable. The window of opportunity may be brief, but the impact of success would be permanent public access to the complete ancient Greek literary tradition.**