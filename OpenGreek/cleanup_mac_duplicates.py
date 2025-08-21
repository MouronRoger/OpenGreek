#!/usr/bin/env python3
"""
Mac Duplicate File Cleanup Script for OpenGreek Project

This script identifies and removes Mac-generated duplicate files in the TLG XML directory.
Mac often creates duplicate files with patterns like:
- "filename.xml" -> "filename 2.xml" 
- "filename.xml" -> "filename-2.xml"

The script compares file sizes and names to ensure safe removal of true duplicates.

Author: OpenGreek Project
Date: 2024
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple, Dict
import argparse
import logging
from collections import defaultdict


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)


def find_potential_duplicates(directory: Path) -> Dict[str, List[Path]]:
    """
    Find potential duplicate files based on Mac naming patterns.
    
    Args:
        directory: Root directory to search
        
    Returns:
        Dictionary mapping base names to lists of potential duplicate files
    """
    logger = logging.getLogger(__name__)
    
    # Find all XML files
    xml_files = list(directory.rglob("*.xml"))
    logger.info(f"Found {len(xml_files)} XML files total")
    
    # Group files by potential base name
    potential_groups: Dict[str, List[Path]] = defaultdict(list)
    
    for file_path in xml_files:
        filename = file_path.name
        
        # Check for Mac duplicate patterns
        if filename.endswith(" 2.xml"):
            # Pattern: "filename 2.xml" -> base: "filename.xml"
            base_name = filename.replace(" 2.xml", ".xml")
            potential_groups[base_name].append(file_path)
        elif filename.endswith("-2.xml"):
            # Pattern: "filename-2.xml" -> base: "filename.xml"  
            base_name = filename.replace("-2.xml", ".xml")
            potential_groups[base_name].append(file_path)
        else:
            # This might be an original file
            potential_groups[filename].append(file_path)
    
    # Filter to only groups with potential duplicates
    duplicate_groups = {
        base_name: files for base_name, files in potential_groups.items()
        if len(files) > 1
    }
    
    logger.info(f"Found {len(duplicate_groups)} potential duplicate groups")
    return duplicate_groups


def analyze_duplicate_group(files: List[Path]) -> Tuple[Path, List[Path]]:
    """
    Analyze a group of potential duplicates to identify original and duplicates.
    
    Args:
        files: List of file paths that might be duplicates
        
    Returns:
        Tuple of (original_file, duplicate_files)
    """
    logger = logging.getLogger(__name__)
    
    # Separate original from duplicates based on filename patterns
    originals = []
    duplicates = []
    
    for file_path in files:
        filename = file_path.name
        if filename.endswith(" 2.xml") or filename.endswith("-2.xml"):
            duplicates.append(file_path)
        else:
            originals.append(file_path)
    
    # If we have exactly one original, use it
    if len(originals) == 1:
        original = originals[0]
    elif len(originals) > 1:
        # Multiple potential originals - choose the one with the simplest name
        original = min(originals, key=lambda p: len(p.name))
        # Add the rest to duplicates
        duplicates.extend([f for f in originals if f != original])
    else:
        # No clear original - choose the one with the simplest name
        original = min(files, key=lambda p: len(p.name))
        duplicates = [f for f in files if f != original]
    
    return original, duplicates


def verify_duplicates(original: Path, duplicates: List[Path]) -> List[Path]:
    """
    Verify that files are actually duplicates by comparing sizes and content.
    
    Args:
        original: The original file
        duplicates: List of potential duplicate files
        
    Returns:
        List of verified duplicate files safe to remove
    """
    logger = logging.getLogger(__name__)
    verified_duplicates = []
    
    if not original.exists():
        logger.warning(f"Original file does not exist: {original}")
        return verified_duplicates
    
    original_size = original.stat().st_size
    
    for duplicate in duplicates:
        if not duplicate.exists():
            logger.warning(f"Duplicate file does not exist: {duplicate}")
            continue
            
        duplicate_size = duplicate.stat().st_size
        
        if original_size == duplicate_size:
            # Sizes match - likely a true duplicate
            logger.debug(f"Size match: {original.name} ({original_size}) == {duplicate.name} ({duplicate_size})")
            verified_duplicates.append(duplicate)
        else:
            logger.warning(f"Size mismatch: {original.name} ({original_size}) != {duplicate.name} ({duplicate_size})")
    
    return verified_duplicates


def remove_duplicates(duplicates: List[Path], dry_run: bool = True) -> int:
    """
    Remove verified duplicate files.
    
    Args:
        duplicates: List of duplicate files to remove
        dry_run: If True, only simulate removal
        
    Returns:
        Number of files removed (or would be removed in dry run)
    """
    logger = logging.getLogger(__name__)
    removed_count = 0
    
    for duplicate in duplicates:
        if dry_run:
            logger.info(f"[DRY RUN] Would remove: {duplicate}")
            removed_count += 1  # Count dry run removals too
        else:
            try:
                duplicate.unlink()
                logger.info(f"Removed: {duplicate}")
                removed_count += 1
            except OSError as e:
                logger.error(f"Failed to remove {duplicate}: {e}")
    
    return removed_count


def main() -> None:
    """Main function to orchestrate the duplicate cleanup process."""
    parser = argparse.ArgumentParser(
        description="Remove Mac-generated duplicate XML files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (safe preview):
  python cleanup_mac_duplicates.py --dry-run
  
  # Actually remove duplicates:
  python cleanup_mac_duplicates.py --execute
  
  # Verbose output:
  python cleanup_mac_duplicates.py --dry-run --verbose
        """
    )
    
    parser.add_argument(
        "--directory", "-d",
        type=Path,
        default=Path("data/tlg/catalogues/legacy_texts_xml"),
        help="Directory to search for duplicates (default: data/tlg/catalogues/legacy_texts_xml)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Preview what would be removed without actually deleting (default)"
    )
    
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually remove the duplicate files (overrides --dry-run)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    logger = setup_logging(args.verbose)
    
    # Determine if this is a dry run
    dry_run = not args.execute
    
    if dry_run:
        logger.info("=== DRY RUN MODE - No files will be deleted ===")
    else:
        logger.info("=== EXECUTE MODE - Files will be permanently deleted ===")
    
    # Validate directory
    if not args.directory.exists():
        logger.error(f"Directory does not exist: {args.directory}")
        sys.exit(1)
    
    if not args.directory.is_dir():
        logger.error(f"Path is not a directory: {args.directory}")
        sys.exit(1)
    
    logger.info(f"Searching for duplicates in: {args.directory.absolute()}")
    
    try:
        # Find potential duplicates
        duplicate_groups = find_potential_duplicates(args.directory)
        
        if not duplicate_groups:
            logger.info("No duplicate files found!")
            return
        
        total_duplicates_found = 0
        total_duplicates_removed = 0
        
        # Process each group
        for base_name, files in duplicate_groups.items():
            logger.debug(f"\nProcessing group: {base_name}")
            logger.debug(f"Files in group: {[f.name for f in files]}")
            
            # Analyze the group
            original, potential_duplicates = analyze_duplicate_group(files)
            
            if not potential_duplicates:
                logger.debug(f"No duplicates found in group {base_name}")
                continue
            
            logger.debug(f"Original: {original.name}")
            logger.debug(f"Potential duplicates: {[f.name for f in potential_duplicates]}")
            
            # Verify duplicates
            verified_duplicates = verify_duplicates(original, potential_duplicates)
            
            if verified_duplicates:
                total_duplicates_found += len(verified_duplicates)
                logger.info(f"\nFound {len(verified_duplicates)} verified duplicates for {original.name}:")
                for dup in verified_duplicates:
                    logger.info(f"  - {dup.name}")
                
                # Remove duplicates
                removed = remove_duplicates(verified_duplicates, dry_run)
                total_duplicates_removed += removed
        
        # Summary
        logger.info(f"\n=== SUMMARY ===")
        logger.info(f"Total duplicate files found: {total_duplicates_found}")
        if dry_run:
            logger.info(f"Files that would be removed: {total_duplicates_removed}")
            logger.info("Run with --execute to actually remove the files")
        else:
            logger.info(f"Files successfully removed: {total_duplicates_removed}")
        
    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
