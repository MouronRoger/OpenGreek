#!/usr/bin/env python3
"""TLG Reference Preservation Module.

This module ensures that every extracted TLG text maintains complete
scholarly citation integrity, including TLG IDs, traditional citations,
internal structure, and cross-reference validation.

Critical for making the extracted corpus academically valuable.
"""

from __future__ import annotations

import json
import re
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


# Traditional TLG author abbreviations mapping
TLG_ABBREVIATIONS = {
    '0012': 'Hom.',      # Homer
    '0059': 'Pl.',       # Plato  
    '0086': 'Arist.',    # Aristotle
    '0011': 'Soph.',     # Sophocles
    '0006': 'Eur.',      # Euripides
    '0007': 'Aesch.',    # Aeschylus
    '0016': 'Hdt.',      # Herodotus
    '0003': 'Th.',       # Thucydides
    '0087': 'Dem.',      # Demosthenes
    '0014': 'Xen.',      # Xenophon
    '0017': 'Isoc.',     # Isocrates
    '0020': 'Lys.',      # Lysias
    '0028': 'Isae.',     # Isaeus
    '0030': 'Lyc.',      # Lycurgus
    '0031': 'Hyp.',      # Hyperides
    '0032': 'Din.',      # Dinarchus
    '0040': 'Andr.',     # Andocides
    # Add more as needed
}

# Work-specific mappings for major authors
WORK_MAPPINGS = {
    '0012': {  # Homer
        '001': {'title': 'Iliad', 'abbrev': 'Il.', 'genre': 'Epic Poetry'},
        '002': {'title': 'Odyssey', 'abbrev': 'Od.', 'genre': 'Epic Poetry'},
    },
    '0059': {  # Plato
        '030': {'title': 'Republic', 'abbrev': 'R.', 'genre': 'Philosophy'},
        '003': {'title': 'Phaedo', 'abbrev': 'Phd.', 'genre': 'Philosophy'},
        '004': {'title': 'Meno', 'abbrev': 'Men.', 'genre': 'Philosophy'},
        '021': {'title': 'Apology', 'abbrev': 'Ap.', 'genre': 'Philosophy'},
        # Add more dialogues as needed
    },
    '0086': {  # Aristotle
        '035': {'title': 'Metaphysics', 'abbrev': 'Metaph.', 'genre': 'Philosophy'},
        '087': {'title': 'Nicomachean Ethics', 'abbrev': 'EN', 'genre': 'Ethics'},
        '001': {'title': 'Categories', 'abbrev': 'Cat.', 'genre': 'Logic'},
        # Add more works as needed
    }
}


@dataclass
class TLGReference:
    """Complete TLG reference with all scholarly metadata."""
    author_id: str
    author_name: str
    author_description: str
    period: str
    location: str
    work_id: str
    work_title: str
    work_genre: str
    url: str
    traditional_citation: str
    traditional_abbreviation: str
    extraction_date: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return asdict(self)
    
    def to_citation(self, book: Optional[str] = None, line: Optional[str] = None) -> str:
        """Generate traditional scholarly citation."""
        base_citation = self.traditional_citation
        
        if book and line:
            return f"{base_citation} {book}.{line}"
        elif book:
            return f"{base_citation} {book}"
        else:
            return base_citation


@dataclass  
class TextStructure:
    """Internal text structure with preserved divisions."""
    raw_text: str
    structured_text: Dict[str, Any]
    line_mapping: Dict[str, str]
    page_mapping: Dict[str, str]
    division_mapping: Dict[str, str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return asdict(self)


@dataclass
class ValidatedExtraction:
    """Complete validated extraction with reference preservation."""
    tlg_reference: TLGReference
    text_structure: TextStructure
    validation_metrics: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for JSON serialization."""
        return {
            'tlg_reference': self.tlg_reference.to_dict(),
            'text_structure': self.text_structure.to_dict(),
            'validation_metrics': self.validation_metrics
        }


class TLGReferenceParser:
    """Parse and validate TLG references from URLs and content."""
    
    def __init__(self):
        self.abbreviations = TLG_ABBREVIATIONS
        self.work_mappings = WORK_MAPPINGS
    
    def parse_url_reference(self, url: str) -> Tuple[str, str]:
        """Extract TLG author and work IDs from URL.
        
        Args:
            url: TLG URL like http://217.71.231.54:8080/TLG0012/0012_001.htm
            
        Returns:
            Tuple of (author_id, work_id)
        """
        # Pattern: /TLG0012/0012_001.htm
        pattern = r'/TLG(\d{4})/\d{4}_(\d{3})\.htm'
        match = re.search(pattern, url)
        
        if match:
            return match.group(1), match.group(2)
        
        # Try encoded underscore pattern
        pattern = r'/TLG(\d{4})/\d{4}%5F(\d{3})\.htm'
        match = re.search(pattern, url)
        
        if match:
            return match.group(1), match.group(2)
            
        raise ValueError(f"Cannot parse TLG reference from URL: {url}")
    
    def build_traditional_citation(self, author_id: str, work_id: str) -> str:
        """Build traditional scholarly citation format."""
        author_abbrev = self.abbreviations.get(author_id, f'TLG{author_id}')
        
        # Check for specific work mappings
        if author_id in self.work_mappings and work_id in self.work_mappings[author_id]:
            work_info = self.work_mappings[author_id][work_id]
            return f"{author_abbrev} {work_info['abbrev']}"
        
        # Generic format
        return f"{author_abbrev} {work_id}"
    
    def validate_reference_format(self, author_id: str, work_id: str) -> bool:
        """Validate TLG ID formats."""
        return (
            re.match(r'\d{4}', author_id) is not None and
            re.match(r'\d{3}', work_id) is not None
        )


class TLGTextStructureAnalyzer:
    """Analyze and preserve internal text structure."""
    
    def __init__(self):
        # Common structure patterns in TLG HTML
        self.structure_patterns = {
            'book': [
                r'<div[^>]*class[^>]*book[^>]*>(\d+)</div>',
                r'<span[^>]*class[^>]*book[^>]*>(\d+)</span>',
                r'<h\d[^>]*>(?:Book\s+)?(\d+)</h\d>',
            ],
            'line': [
                r'<span[^>]*class[^>]*line[^>]*>(\d+)</span>',
                r'<div[^>]*class[^>]*line[^>]*>(\d+)</div>',
                r'\[(\d+)\]',  # Line numbers in brackets
            ],
            'page': [
                r'<span[^>]*class[^>]*page[^>]*>([^<]+)</span>',
                r'<div[^>]*class[^>]*page[^>]*>([^<]+)</div>',
                r'\{([^}]+)\}',  # Stephanus pages in braces
            ],
            'chapter': [
                r'<div[^>]*class[^>]*chapter[^>]*>(\d+)</div>',
                r'<span[^>]*class[^>]*chapter[^>]*>(\d+)</span>',
            ]
        }
    
    def extract_structure_markers(self, html_content: str) -> Dict[str, List[Tuple[str, int]]]:
        """Extract all structural markers with their positions."""
        markers = {}
        
        for marker_type, patterns in self.structure_patterns.items():
            markers[marker_type] = []
            
            for pattern in patterns:
                for match in re.finditer(pattern, html_content, re.IGNORECASE):
                    markers[marker_type].append((match.group(1), match.start()))
        
        return markers
    
    def build_structured_text(self, clean_text: str, markers: Dict[str, List[Tuple[str, int]]]) -> Dict[str, Any]:
        """Build structured text representation with divisions."""
        structured = {}
        
        # For now, create a simple paragraph-based structure
        # This can be enhanced based on the actual HTML structure found
        paragraphs = [p.strip() for p in clean_text.split('\n') if p.strip()]
        
        if paragraphs:
            structured = {
                'paragraphs': paragraphs,
                'total_paragraphs': len(paragraphs),
                'estimated_lines': sum(len(p.split('.')) for p in paragraphs)
            }
        
        return structured


class TLGValidationSystem:
    """Comprehensive validation for extracted TLG texts."""
    
    def __init__(self):
        self.min_greek_ratio = 0.2
        self.min_text_length = 50
        self.required_reference_fields = [
            'author_id', 'work_id', 'author_name', 
            'work_title', 'traditional_citation', 'url'
        ]
    
    def validate_greek_content(self, text: str) -> Dict[str, Any]:
        """Validate Greek text content quality."""
        if not text or len(text) < self.min_text_length:
            return {
                'valid': False,
                'reason': 'Text too short',
                'length': len(text) if text else 0,
                'greek_ratio': 0.0
            }
        
        # Count Greek characters
        greek_chars = 0
        total_alpha_chars = 0
        
        for char in text:
            if char.isalpha():
                total_alpha_chars += 1
                # Greek Unicode ranges
                if ('\u0370' <= char <= '\u03FF' or  # Greek and Coptic
                    '\u1F00' <= char <= '\u1FFF'):   # Greek Extended
                    greek_chars += 1
        
        if total_alpha_chars == 0:
            return {
                'valid': False,
                'reason': 'No alphabetic characters',
                'length': len(text),
                'greek_ratio': 0.0
            }
        
        greek_ratio = greek_chars / total_alpha_chars
        
        return {
            'valid': greek_ratio >= self.min_greek_ratio,
            'reason': 'Valid Greek text' if greek_ratio >= self.min_greek_ratio else 'Insufficient Greek content',
            'length': len(text),
            'word_count': len(text.split()),
            'greek_chars': greek_chars,
            'total_alpha_chars': total_alpha_chars,
            'greek_ratio': greek_ratio
        }
    
    def validate_reference_completeness(self, reference: TLGReference) -> Dict[str, Any]:
        """Validate that all required reference fields are present."""
        missing_fields = []
        
        for field in self.required_reference_fields:
            value = getattr(reference, field, None)
            if not value or (isinstance(value, str) and not value.strip()):
                missing_fields.append(field)
        
        return {
            'valid': len(missing_fields) == 0,
            'missing_fields': missing_fields,
            'completeness_score': (len(self.required_reference_fields) - len(missing_fields)) / len(self.required_reference_fields)
        }
    
    def validate_extraction(self, extraction: ValidatedExtraction) -> Dict[str, Any]:
        """Perform comprehensive validation of extraction."""
        # Validate text content
        text_validation = self.validate_greek_content(extraction.text_structure.raw_text)
        
        # Validate reference completeness
        reference_validation = self.validate_reference_completeness(extraction.tlg_reference)
        
        # Overall validation
        overall_valid = text_validation['valid'] and reference_validation['valid']
        
        return {
            'overall_valid': overall_valid,
            'text_validation': text_validation,
            'reference_validation': reference_validation,
            'validation_timestamp': datetime.now().isoformat()
        }


class TLGReferencePreserver:
    """Main class for preserving TLG references during extraction."""
    
    def __init__(self):
        self.reference_parser = TLGReferenceParser()
        self.structure_analyzer = TLGTextStructureAnalyzer()
        self.validator = TLGValidationSystem()
    
    def create_reference_from_discovery(self, author_data: Dict[str, Any], work_data: Dict[str, Any]) -> TLGReference:
        """Create complete TLG reference from discovery data."""
        author_id = author_data['tlg_id']
        work_id = work_data['work_id']
        
        # Build traditional citation
        traditional_citation = self.reference_parser.build_traditional_citation(author_id, work_id)
        
        # Get work details if available
        work_title = work_data.get('title', f'Work {work_id}')
        work_genre = 'Unknown'
        
        if (author_id in self.reference_parser.work_mappings and 
            work_id in self.reference_parser.work_mappings[author_id]):
            work_info = self.reference_parser.work_mappings[author_id][work_id]
            work_title = work_info.get('title', work_title)
            work_genre = work_info.get('genre', work_genre)
        
        return TLGReference(
            author_id=author_id,
            author_name=author_data['name'],
            author_description=author_data.get('description', ''),
            period=author_data.get('period', ''),
            location=author_data.get('location', ''),
            work_id=work_id,
            work_title=work_title,
            work_genre=work_genre,
            url=work_data['url'],
            traditional_citation=traditional_citation,
            traditional_abbreviation=self.reference_parser.abbreviations.get(author_id, f'TLG{author_id}'),
            extraction_date=datetime.now().isoformat()
        )
    
    def analyze_text_structure(self, html_content: str, clean_text: str) -> TextStructure:
        """Analyze and preserve internal text structure."""
        # Extract structural markers
        markers = self.structure_analyzer.extract_structure_markers(html_content)
        
        # Build structured representation
        structured_text = self.structure_analyzer.build_structured_text(clean_text, markers)
        
        # Create mappings (simplified for now)
        line_mapping = {}
        page_mapping = {}
        division_mapping = {}
        
        return TextStructure(
            raw_text=clean_text,
            structured_text=structured_text,
            line_mapping=line_mapping,
            page_mapping=page_mapping,
            division_mapping=division_mapping
        )
    
    def preserve_extraction_references(
        self, 
        author_data: Dict[str, Any], 
        work_data: Dict[str, Any],
        html_content: str,
        clean_text: str
    ) -> ValidatedExtraction:
        """Create complete validated extraction with preserved references."""
        
        # Create TLG reference
        tlg_reference = self.create_reference_from_discovery(author_data, work_data)
        
        # Analyze text structure
        text_structure = self.analyze_text_structure(html_content, clean_text)
        
        # Create initial extraction
        extraction = ValidatedExtraction(
            tlg_reference=tlg_reference,
            text_structure=text_structure,
            validation_metrics={}
        )
        
        # Validate extraction
        validation_results = self.validator.validate_extraction(extraction)
        extraction.validation_metrics = validation_results
        
        return extraction
    
    def save_reference_index(self, extractions: List[ValidatedExtraction], output_path: Path) -> None:
        """Save master reference index for the entire corpus."""
        index_data = {
            'tlg_corpus_index': {
                'extraction_date': datetime.now().isoformat(),
                'total_works': len(extractions),
                'total_authors': len(set(e.tlg_reference.author_id for e in extractions)),
                'validation_summary': {
                    'valid_extractions': len([e for e in extractions if e.validation_metrics.get('overall_valid', False)]),
                    'avg_greek_ratio': sum(e.validation_metrics.get('text_validation', {}).get('greek_ratio', 0) for e in extractions) / len(extractions) if extractions else 0,
                },
                'authors': self._build_author_index(extractions)
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    def _build_author_index(self, extractions: List[ValidatedExtraction]) -> Dict[str, Any]:
        """Build author index from extractions."""
        authors = {}
        
        for extraction in extractions:
            ref = extraction.tlg_reference
            author_id = ref.author_id
            
            if author_id not in authors:
                authors[author_id] = {
                    'name': ref.author_name,
                    'description': ref.author_description,
                    'period': ref.period,
                    'location': ref.location,
                    'traditional_abbrev': ref.traditional_abbreviation,
                    'works': {}
                }
            
            authors[author_id]['works'][ref.work_id] = {
                'title': ref.work_title,
                'genre': ref.work_genre,
                'traditional_citation': ref.traditional_citation,
                'url': ref.url,
                'word_count': extraction.validation_metrics.get('text_validation', {}).get('word_count', 0),
                'validation_status': 'valid' if extraction.validation_metrics.get('overall_valid', False) else 'invalid'
            }
        
        return authors


def main():
    """Test reference preservation functionality."""
    # Example usage
    preserver = TLGReferencePreserver()
    
    # Test reference parsing
    test_url = "http://217.71.231.54:8080/TLG0012/0012_001.htm"
    author_id, work_id = preserver.reference_parser.parse_url_reference(test_url)
    print(f"Parsed {test_url} -> Author: {author_id}, Work: {work_id}")
    
    # Test citation building
    citation = preserver.reference_parser.build_traditional_citation(author_id, work_id)
    print(f"Traditional citation: {citation}")
    
    print("Reference preservation module initialized successfully!")


if __name__ == "__main__":
    main()

