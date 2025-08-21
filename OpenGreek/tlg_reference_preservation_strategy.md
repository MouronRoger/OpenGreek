# TLG Reference Preservation Strategy
## Maintaining Scholarly Citation Integrity During Extraction

**CRITICAL PRINCIPLE**: Every extracted text must retain complete citation metadata to ensure scholarly usability.

---

## TLG Reference System Structure

### Primary Identifiers
```
Complete TLG Reference Format:
TLG [AUTHOR] [WORK] [BOOK].[CHAPTER].[SECTION].[LINE]

Examples:
- TLG 0012 001 1.1.1    = Homer, Iliad, Book 1, Line 1
- TLG 0059 030 7.514a   = Plato, Republic, Book 7, Stephanus 514a
- TLG 0086 035 1.980a   = Aristotle, Metaphysics, Book 1, Bekker 980a
```

### URL to Reference Mapping
```
URL Pattern: /TLG0012/0012_001.htm
Maps to: TLG 0012 001 (Homer, Iliad)

Critical Data to Extract:
- TLG Author Number: 0012
- Work Number: 001  
- Author Name: HOMER
- Work Title: Iliad
- Internal divisions: Books, chapters, lines
- Traditional reference systems: Stephanus pages, Bekker numbers, etc.
```

---

## Extraction Metadata Schema

### Required Data Structure
```json
{
  "tlg_reference": {
    "author_id": "0012",
    "author_name": "HOMER", 
    "author_description": "Epic Poet",
    "period": "8th cent. BC",
    "work_id": "001",
    "work_title": "Iliad",
    "work_genre": "Epic Poetry",
    "url": "http://217.71.231.54:8080/TLG0012/0012_001.htm",
    "traditional_citation": "Hom. Il.",
    "internal_structure": {
      "divisions": ["book", "line"],
      "book_count": 24,
      "line_count_total": 15693
    }
  },
  "text_content": {
    "full_text": "μῆνιν ἄειδε θεὰ Πηληϊάδεω Ἀχιλῆος...",
    "structured_text": {
      "book_1": {
        "lines": {
          "1": "μῆνιν ἄειδε θεὰ Πηληϊάδεω Ἀχιλῆος",
          "2": "οὐλομένην, ἣ μυρί᾽ Ἀχαιοῖς ἄλγε᾽ ἔθηκε",
          // ... continue
        }
      }
    }
  },
  "extraction_metadata": {
    "extraction_date": "2025-08-21T15:30:00Z",
    "source_url": "http://217.71.231.54:8080/TLG0012/0012_001.htm",
    "validation_status": "passed",
    "greek_ratio": 0.95
  }
}
```

---

## Reference Extraction Implementation

### 1. Author Metadata Extraction
```python
class TLGAuthorParser:
    def extract_author_metadata(self, index_html):
        """Extract complete author information from index"""
        return {
            'tlg_id': self.parse_tlg_id(author_entry),
            'name': self.parse_author_name(author_entry),
            'description': self.parse_description(author_entry),  # "Epic Poet", "Philosopher"
            'period': self.parse_period(author_entry),            # "5th cent. BC"
            'location': self.parse_location(author_entry),        # "Athens"
            'traditional_abbreviation': self.get_abbreviation()   # "Hom.", "Pl.", "Arist."
        }
```

### 2. Work Metadata Extraction  
```python
class TLGWorkParser:
    def extract_work_metadata(self, work_html, tlg_id, work_id):
        """Extract work-specific metadata from HTML page"""
        
        # Parse from HTML title, headers, metadata
        work_title = self.extract_title(work_html)
        genre = self.determine_genre(work_title, tlg_id)
        traditional_citation = self.build_traditional_citation(tlg_id, work_id)
        
        return {
            'tlg_id': tlg_id,
            'work_id': work_id,
            'title': work_title,
            'genre': genre,
            'traditional_citation': traditional_citation,
            'internal_structure': self.analyze_text_structure(work_html)
        }
```

### 3. Internal Reference Preservation
```python
class TLGTextStructureParser:
    def preserve_internal_references(self, html_content):
        """Maintain internal text divisions and line numbers"""
        
        # Look for structural markers in HTML
        structure_patterns = [
            r'<div class="book">(\d+)</div>',      # Book divisions
            r'<span class="line">(\d+)</span>',    # Line numbers  
            r'<span class="page">(\w+)</span>',    # Stephanus/Bekker pages
            r'<div class="chapter">(\d+)</div>',   # Chapter divisions
            r'<span class="section">(\w+)</span>'  # Section markers
        ]
        
        # Build structured text with preserved references
        structured_content = {
            'raw_text': self.extract_clean_text(html_content),
            'line_mapping': self.build_line_mapping(html_content),
            'page_mapping': self.build_page_mapping(html_content),
            'division_mapping': self.build_division_mapping(html_content)
        }
        
        return structured_content
```

---

## Traditional Citation System Integration

### Standard Abbreviations Mapping
```python
TLG_ABBREVIATIONS = {
    '0012': 'Hom.',      # Homer
    '0059': 'Pl.',       # Plato  
    '0086': 'Arist.',    # Aristotle
    '0011': 'Soph.',     # Sophocles
    '0006': 'Eur.',      # Euripides
    '0007': 'Aesch.',    # Aeschylus
    '0016': 'Hdt.',      # Herodotus
    '0003': 'Th.',       # Thucydides
    # ... complete mapping
}

def build_citation(tlg_id, work_id, book=None, line=None):
    """Build traditional scholarly citation"""
    abbrev = TLG_ABBREVIATIONS.get(tlg_id, f'TLG{tlg_id}')
    
    if tlg_id == '0012':  # Homer
        work_abbrev = 'Il.' if work_id == '001' else 'Od.'
        return f'{abbrev} {work_abbrev} {book}.{line}' if book and line else f'{abbrev} {work_abbrev}'
    
    elif tlg_id == '0059':  # Plato - use Stephanus pages
        return f'{abbrev} {get_work_name(work_id)} {stephanus_page}'
    
    # ... continue for other citation systems
```

### Reference System Examples
```python
CITATION_EXAMPLES = {
    'homer_iliad': {
        'tlg_ref': 'TLG 0012 001 1.1',
        'traditional': 'Hom. Il. 1.1',
        'full_citation': 'Homer, Iliad 1.1'
    },
    'plato_republic': {
        'tlg_ref': 'TLG 0059 030 7.514a',
        'traditional': 'Pl. R. 514a', 
        'full_citation': 'Plato, Republic 514a'
    },
    'aristotle_metaphysics': {
        'tlg_ref': 'TLG 0086 035 1.980a',
        'traditional': 'Arist. Metaph. 980a',
        'full_citation': 'Aristotle, Metaphysics 980a'
    }
}
```

---

## Quality Assurance for References

### Validation Checklist
```python
def validate_extraction_references(extracted_work):
    """Ensure all reference data is complete and accurate"""
    
    required_fields = [
        'tlg_reference.author_id',
        'tlg_reference.work_id', 
        'tlg_reference.author_name',
        'tlg_reference.work_title',
        'tlg_reference.traditional_citation',
        'tlg_reference.url'
    ]
    
    for field in required_fields:
        assert get_nested_field(extracted_work, field), f"Missing {field}"
    
    # Validate TLG ID format
    assert re.match(r'\d{4}', extracted_work['tlg_reference']['author_id'])
    assert re.match(r'\d{3}', extracted_work['tlg_reference']['work_id'])
    
    # Validate traditional citation format
    citation = extracted_work['tlg_reference']['traditional_citation']
    assert citation and len(citation) > 2, "Invalid traditional citation"
    
    return True
```

### Cross-Reference Verification
```python
def cross_reference_validation():
    """Verify extracted references against known TLG data"""
    
    # Check against authoritative TLG author lists
    known_tlg_authors = load_authoritative_tlg_list()
    
    for extracted_author in extracted_authors:
        tlg_id = extracted_author['tlg_id']
        
        if tlg_id in known_tlg_authors:
            # Verify name matches
            assert extracted_author['name'] == known_tlg_authors[tlg_id]['name']
            # Verify period matches
            assert extracted_author['period'] == known_tlg_authors[tlg_id]['period']
        else:
            log_warning(f"Unknown TLG ID discovered: {tlg_id}")
```

---

## Output Format with Complete References

### Individual Work File Format
```
# Filename: TLG0012_001_Homer_Iliad.txt

=== TLG REFERENCE METADATA ===
TLG Author: 0012
Author Name: HOMER
Author Description: Epic Poet  
Period: 8th cent. BC
Work ID: 001
Work Title: Iliad
Traditional Citation: Hom. Il.
Genre: Epic Poetry
Source URL: http://217.71.231.54:8080/TLG0012/0012_001.htm
Extraction Date: 2025-08-21T15:30:00Z

=== TEXT CONTENT ===
[Book 1]
[1] μῆνιν ἄειδε θεὰ Πηληϊάδεω Ἀχιλῆος
[2] οὐλομένην, ἣ μυρί᾽ Ἀχαιοῖς ἄλγε᾽ ἔθηκε,
[3] πολλὰς δ᾽ ἰφθίμους ψυχὰς Ἅϊδι προΐαψεν
...

[Book 2]
[1] Νῦν αὖτε θεοὶ θέσαν οὖλον ὄνειρον...
...
```

### Master Reference Index
```json
{
  "tlg_corpus_index": {
    "extraction_date": "2025-08-21T15:30:00Z",
    "total_authors": 3247,
    "total_works": 9856,
    "authors": {
      "0012": {
        "name": "HOMER",
        "description": "Epic Poet",
        "period": "8th cent. BC",
        "traditional_abbrev": "Hom.",
        "works": {
          "001": {
            "title": "Iliad", 
            "traditional_citation": "Hom. Il.",
            "genre": "Epic Poetry",
            "filename": "TLG0012_001_Homer_Iliad.txt",
            "line_count": 15693,
            "book_count": 24
          },
          "002": {
            "title": "Odyssey",
            "traditional_citation": "Hom. Od.", 
            "genre": "Epic Poetry",
            "filename": "TLG0012_002_Homer_Odyssey.txt",
            "line_count": 12110,
            "book_count": 24
          }
        }
      }
    }
  }
}
```

---

## Implementation Priority for Reference Preservation

### Phase 1: Core Reference Extraction
1. **Author metadata** from index page (TLG ID, name, period)
2. **Work metadata** from individual pages (work ID, title)
3. **URL mapping** preservation (source link for every text)

### Phase 2: Traditional Citation Integration
1. **Standard abbreviations** (Hom., Pl., Arist.)
2. **Citation format** construction (Hom. Il. 1.1)
3. **Cross-reference validation** against known systems

### Phase 3: Internal Structure Preservation
1. **Line numbering** for poetry
2. **Page references** (Stephanus, Bekker) for prose
3. **Book/chapter divisions** for long works

### Phase 4: Quality Assurance
1. **Reference completeness** validation
2. **Citation accuracy** verification  
3. **Cross-reference** consistency checks

---

## Critical Success Metrics for References

### Minimum Viable Reference Preservation
- ✅ Every work has TLG author + work ID
- ✅ Every work has author name + work title
- ✅ Every work has source URL preserved
- ✅ Traditional citation format available

### Optimal Reference Preservation  
- ✅ Complete internal structure (books, lines, pages)
- ✅ Traditional reference systems (Stephanus, Bekker)
- ✅ Cross-validated against authoritative TLG data
- ✅ Multiple citation format outputs

**BOTTOM LINE**: Without proper references, the extracted corpus becomes a pile of unusable Greek text. Reference preservation is equally important as text extraction itself.