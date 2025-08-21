#!/usr/bin/env python3
"""Development Progress Tracker for OpenGreek Project.

Automatically generates timestamped development progress entries
in DEVELOPMENT_PROGRESS.md with proper formatting and chronological ordering.

Usage:
    python DEVELOPMENT_PROGRESS.py "Your progress report content here"

The script automatically handles:
- System-generated timestamps (no hallucinated dates)
- Consistent formatting across all entries  
- Proper reverse chronological ordering
- Preservation of document structure
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def add_development_progress_entry(content: str) -> None:
    """Add a new development progress entry to DEVELOPMENT_PROGRESS.md.
    
    Args:
        content: The progress report content (without timestamp or header)
    """
    progress_file = Path(__file__).parent / "DEVELOPMENT_PROGRESS.md"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_only = datetime.now().strftime("%Y-%m-%d")
    
    # Create entry header and content
    entry_header = f"## {date_only}: Development Progress Update"
    entry_content = f"""
{entry_header}
**Timestamp**: {timestamp}

{content.strip()}

---
"""

    # Handle file creation or updating
    if not progress_file.exists():
        # Create new file with initial structure
        initial_content = f"""# OpenGreek Development Progress Log

This document tracks development progress for the OpenGreek TLG extraction project.
Entries are automatically generated using DEVELOPMENT_PROGRESS.py.

**IMPORTANT**: Do not manually edit entries between the delimiter lines.
Use the script: `python DEVELOPMENT_PROGRESS.py "Your report content"`

---
{entry_content}
"""
        progress_file.write_text(initial_content, encoding="utf-8")
        print(f"✅ Created new progress file: {progress_file}")
        
    else:
        # Read existing content
        existing_content = progress_file.read_text(encoding="utf-8")
        
        # Find insertion point (after header section, before first entry)
        lines = existing_content.split("\n")
        insert_index = None
        
        # Look for the first "---" after the header section
        header_section_done = False
        for i, line in enumerate(lines):
            if line.strip() == "---" and header_section_done:
                insert_index = i + 1
                break
            elif "Use the script:" in line:
                header_section_done = True
        
        if insert_index is None:
            # Fallback: add at the end
            insert_index = len(lines)
        
        # Insert new entry at the top of entries (after header)
        new_lines = (
            lines[:insert_index] + 
            entry_content.strip().split("\n") +
            ([""] if insert_index < len(lines) else []) +
            lines[insert_index:]
        )
        
        # Write updated content
        progress_file.write_text("\n".join(new_lines), encoding="utf-8")
        print(f"✅ Added progress entry to: {progress_file}")
    
    print(f"📝 Entry timestamp: {timestamp}")


def main() -> None:
    """Main entry point for development progress tracking."""
    if len(sys.argv) != 2:
        print("Usage: python DEVELOPMENT_PROGRESS.py \"Your report content here\"")
        print("\nExample:")
        print('python DEVELOPMENT_PROGRESS.py "Implemented TLG discovery module with 95% success rate"')
        sys.exit(1)
    
    content = sys.argv[1]
    if not content.strip():
        print("❌ Error: Progress content cannot be empty")
        sys.exit(1)
    
    try:
        add_development_progress_entry(content)
        print("✅ Development progress entry added successfully!")
        
    except Exception as e:
        print(f"❌ Error adding progress entry: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

