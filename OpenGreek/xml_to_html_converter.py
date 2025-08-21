#!/usr/bin/env python3
"""
XML to HTML Converter for TLG Corpus

Converts TEI/XML files to HTML format matching the existing TLG HTML structure.
Generates lowercase filenames and preserves all structural markup.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, Optional

from lxml import etree


class XMLToHTMLConverter:
    """Convert TEI/XML files to TLG-style HTML format."""
    
    def __init__(self, author_index_path: Path):
        """Initialize converter with author metadata."""
        with open(author_index_path, encoding="utf-8") as f:
            self.author_index: Dict[str, Any] = json.load(f)
    
    def extract_metadata(self, xml_root: etree._Element) -> Dict[str, str]:
        """Extract metadata from TEI header."""
        ns = {"tei": "http://www.tei-c.org/ns/1.0"}
        
        # Extract basic info from filename or URN
        filename = xml_root.xpath("//tei:idno[@type='filename']/text()", namespaces=ns)
        filename = filename[0] if filename else ""
        
        # Parse TLG ID from filename with flexible patterns
        filename_lower = filename.lower()
        
        # Try standard pattern first: tlg0007.tlg040.edition.xml
        tlg_match = re.match(r"(tlg\d+)\.(tlg\d+)", filename_lower)
        
        # Try alternative patterns
        if not tlg_match:
            # Pattern: tlg0007.084a.edition.xml (letter suffix)
            tlg_match = re.match(r"(tlg\d+)\.(tlg\d+[a-z])", filename_lower)
        
        if not tlg_match:
            # Pattern: tlg0007.tlgX01.edition.xml (X prefix)
            tlg_match = re.match(r"(tlg\d+)\.(tlgx\d+)", filename_lower)
            if tlg_match:
                # Convert tlgX01 to tlg001 format
                work_id = tlg_match.group(2).replace('tlgx', 'tlg')
                tlg_match = (tlg_match.group(1), work_id)
        
        if not tlg_match:
            # Pattern: tlg0007.ogl001.edition.xml (ogl prefix)
            tlg_match = re.match(r"(tlg\d+)\.(ogl\d+)", filename_lower)
            if tlg_match:
                # Convert ogl001 to tlg001 format
                work_id = tlg_match.group(2).replace('ogl', 'tlg')
                tlg_match = (tlg_match.group(1), work_id)
        
        if not tlg_match:
            # Pattern: tlg0007.1st1K001.edition.xml (1st1K prefix)
            tlg_match = re.match(r"(tlg\d+)\.(1st1k\d+)", filename_lower)
            if tlg_match:
                # Convert 1st1K001 to tlg001 format
                work_num = tlg_match.group(2).replace('1st1k', '')
                work_id = f"tlg{work_num.zfill(3)}"
                tlg_match = (tlg_match.group(1), work_id)
        
        if not tlg_match:
            # Skip non-TLG files (heb, stoa, ggm, etc.) - they're not Greek TLG texts
            if not filename_lower.startswith('tlg'):
                raise ValueError(f"Skipping non-TLG file: {filename}")
            else:
                raise ValueError(f"Cannot parse TLG ID from filename: {filename}")
        
        if isinstance(tlg_match, tuple):
            author_id, work_id = tlg_match
        else:
            author_id, work_id = tlg_match.groups()
        
        # Get author info from index
        author_info = self.author_index.get(author_id, {})
        author_name = author_info.get("name", "Unknown Author")
        author_type = author_info.get("type", "")
        century = author_info.get("century", 0)
        
        # Extract work title from TEI
        title_elem = xml_root.xpath("//tei:titleStmt/tei:title[1]/text()", namespaces=ns)
        work_title = title_elem[0] if title_elem else "Unknown Work"
        
        # Extract editor info
        editor_elem = xml_root.xpath("//tei:titleStmt/tei:editor/text()", namespaces=ns)
        editor = editor_elem[0] if editor_elem else ""
        
        # Extract source/edition info
        source_elem = xml_root.xpath("//tei:sourceDesc//tei:biblStruct", namespaces=ns)
        source_info = ""
        if source_elem:
            # Try to build source citation from biblStruct
            editor_name = xml_root.xpath("//tei:sourceDesc//tei:editor//tei:name/text()", namespaces=ns)
            title_text = xml_root.xpath("//tei:sourceDesc//tei:title/text()", namespaces=ns)
            publisher = xml_root.xpath("//tei:sourceDesc//tei:publisher/text()", namespaces=ns)
            pub_place = xml_root.xpath("//tei:sourceDesc//tei:pubPlace/text()", namespaces=ns)
            date = xml_root.xpath("//tei:sourceDesc//tei:date/text()", namespaces=ns)
            
            parts = []
            if editor_name:
                parts.append(f"{editor_name[0]} (ed.)")
            if title_text:
                parts.append(f"<em>{title_text[0]}</em>")
            if publisher:
                parts.append(publisher[0])
            if pub_place:
                parts.append(pub_place[0])
            if date:
                parts.append(date[0])
            
            source_info = ", ".join(parts) if parts else ""
        
        # Format century display
        if century < 0:
            century_display = f"{abs(century)} B.C."
        elif century > 0:
            century_display = f"A.D. {century}"
        else:
            century_display = "Date unknown"
        
        return {
            "author_id": author_id,
            "work_id": work_id,
            "author_name": author_name.upper(),
            "work_title": work_title,
            "author_type": author_type,
            "century_display": century_display,
            "editor": editor,
            "source_info": source_info,
            "filename": filename
        }
    
    def convert_text_structure(self, body_elem: etree._Element) -> str:
        """Convert TEI text structure to HTML table rows."""
        ns = {"tei": "http://www.tei-c.org/ns/1.0"}
        html_rows = []
        
        # Find all text divisions
        divisions = body_elem.xpath(".//tei:div[@type='textpart']", namespaces=ns)
        
        for div in divisions:
            subtype = div.get("subtype", "")
            n = div.get("n", "")
            
            if subtype in ["chapter", "book"]:
                # Chapter/book header
                html_rows.append(f'<tr><td><h3>{n}</h3>.<h2>1</h2><td>')
                
                # Process paragraphs within chapter
                paragraphs = div.xpath(".//tei:p", namespaces=ns)
                for i, p in enumerate(paragraphs, 1):
                    text_content = self.extract_text_content(p)
                    if i > 1:
                        html_rows.append(f'<tr><td><h3>{n}</h3>.<h2>{i}</h2><td>')
                    html_rows.append(text_content)
                    html_rows.append('<td class=K rowspan=1>')
                    
            elif subtype == "section":
                # Section within chapter
                parent_n = div.getparent().get("n", "1") if div.getparent() is not None else "1"
                html_rows.append(f'<tr><td><h3>{parent_n}</h3>.<h2>{n}</h2><td>')
                
                paragraphs = div.xpath(".//tei:p", namespaces=ns)
                for p in paragraphs:
                    text_content = self.extract_text_content(p)
                    html_rows.append(text_content)
                    html_rows.append('<td class=K rowspan=1>')
        
        return "".join(html_rows)
    
    def extract_text_content(self, elem: etree._Element) -> str:
        """Extract and clean text content from XML element."""
        # Get all text, preserving some formatting
        text_parts = []
        
        def process_node(node):
            if node.text:
                text_parts.append(node.text)
            
            for child in node:
                if child.tag.endswith("}lb"):  # Line break
                    text_parts.append(" ")
                elif child.tag.endswith("}pb"):  # Page break - ignore
                    pass
                else:
                    process_node(child)
                
                if child.tail:
                    text_parts.append(child.tail)
        
        process_node(elem)
        
        # Clean up text
        text = "".join(text_parts)
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        text = text.strip()
        
        return text
    
    def generate_html(self, xml_path: Path) -> str:
        """Generate complete HTML from XML file."""
        # Parse XML
        parser = etree.XMLParser(strip_cdata=False)
        tree = etree.parse(str(xml_path), parser)
        root = tree.getroot()
        
        # Extract metadata
        metadata = self.extract_metadata(root)
        
        # Extract text body
        ns = {"tei": "http://www.tei-c.org/ns/1.0"}
        body = root.xpath("//tei:body", namespaces=ns)[0]
        text_content = self.convert_text_structure(body)
        
        # Generate HTML
        html_template = f"""<!doctype html>
<html lang="el">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<link href="../style/base.css" rel="stylesheet" type="text/css" />
<script src="../script/tips.js"></script>
<title>{metadata['author_name']} :: {metadata['work_title']} :: TLG {metadata['author_id'].upper().replace('TLG', '')} {metadata['work_id'].upper().replace('TLG', '')}</title>
</head>
<body>
<table>
<tr><td class="Card" colspan="3">
<p class=CaTi><a class=CanonTLG href="..\\indices\\indexA.htm">TLG</a> <a class=CaIx href="{metadata['author_id'].replace('tlg', '')}.htm">{metadata['author_id'].upper().replace('TLG', '')}</a> {metadata['work_id'].upper().replace('TLG', '')}&nbsp;:: <strong><a class=CaCo href="{metadata['author_id'].replace('tlg', '')}.htm">{metadata['author_name']}</a></strong>&nbsp;:: <strong>{metadata['work_title']}</strong></p>
<p class="AuthorInfo"><a class=CaCo href="{metadata['author_id'].replace('tlg', '')}.htm">{metadata['author_name']}</a> <a class="CanonEpi">{metadata['author_type']}</a><br />(<a class="CanonDat">{metadata['century_display']}</a>)</p><p class="WorkInfo"><strong>{metadata['work_title']}</strong></p><p class="EditionInfo"><a class=CaE>Source: {metadata['source_info']}</a></p><p class="CitationStyle">Citation: Chapter&nbsp;&mdash; section&nbsp;&mdash; (line)</p>
<tr><td class=qS colspan=3> {text_content}
</table>
<script>
var IL = ["Line", "Section", "Chapter"];
document.body.onload=f();
</script>
</body>
</html>
"""
        
        return html_template
    
    def convert_file(self, xml_path: Path, output_dir: Path) -> Path:
        """Convert single XML file to HTML."""
        try:
            html_content = self.generate_html(xml_path)
            
            # Generate output filename (lowercase)
            xml_filename = xml_path.stem  # e.g., tlg0007.tlg040.1st1K-grc1
            parts = xml_filename.split('.')
            if len(parts) >= 2:
                author_id = parts[0].upper().replace('TLG', 'TLG')
                work_id = parts[1].upper().replace('TLG', '')
                
                # Get author name from metadata
                parser = etree.XMLParser(strip_cdata=False)
                tree = etree.parse(str(xml_path), parser)
                root = tree.getroot()
                metadata = self.extract_metadata(root)
                author_name = metadata['author_name'].replace(' ', '_')
                
                output_filename = f"{author_id}_{work_id}_{author_name}_{author_id}_{work_id}.html".lower()
            else:
                output_filename = f"{xml_filename}.html".lower()
            
            output_path = output_dir / output_filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return output_path
            
        except Exception as e:
            print(f"Error converting {xml_path}: {e}")
            raise


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Convert TEI/XML files to TLG-style HTML")
    parser.add_argument("--xml-dir", type=Path, 
                       help="Directory containing XML files")
    parser.add_argument("--output-dir", type=Path, required=True,
                       help="Output directory for HTML files")
    parser.add_argument("--author-index", type=Path, required=True,
                       help="Path to author index JSON file")
    parser.add_argument("--single-file", type=Path,
                       help="Convert single XML file instead of directory")
    
    args = parser.parse_args()
    
    # Initialize converter
    converter = XMLToHTMLConverter(args.author_index)
    
    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    if args.single_file:
        # Convert single file
        output_path = converter.convert_file(args.single_file, args.output_dir)
        print(f"Converted: {args.single_file} -> {output_path}")
    elif args.xml_dir:
        # Convert all XML files in directory
        xml_files = list(args.xml_dir.rglob("*.xml"))
        xml_files = [f for f in xml_files if not f.name.startswith("__")]  # Skip __cts__.xml files
        
        print(f"Found {len(xml_files)} XML files to convert...")
        
        converted = 0
        for xml_file in xml_files:
            try:
                output_path = converter.convert_file(xml_file, args.output_dir)
                converted += 1
                if converted % 10 == 0:
                    print(f"Converted {converted}/{len(xml_files)} files...")
            except Exception as e:
                print(f"Failed to convert {xml_file}: {e}")
                continue
        
        print(f"Conversion complete: {converted}/{len(xml_files)} files converted")
    else:
        parser.error("Either --xml-dir or --single-file must be specified")


if __name__ == "__main__":
    main()
