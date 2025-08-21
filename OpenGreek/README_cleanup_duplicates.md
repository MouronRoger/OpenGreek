# Mac Duplicate File Cleanup Script

This script removes Mac-generated duplicate files from the TLG XML directory structure.

## Problem

Mac OS sometimes creates duplicate files with naming patterns like:
- `filename.xml` → `filename 2.xml` (space before 2)
- `filename.xml` → `filename-2.xml` (dash before 2)

These duplicates clutter the directory and can cause confusion in processing.

## Solution

The `cleanup_mac_duplicates.py` script:

1. **Identifies duplicates** by filename patterns
2. **Verifies duplicates** by comparing file sizes
3. **Safely removes** only true duplicates (same size)
4. **Preserves originals** with the simplest filenames
5. **Provides dry-run mode** for safe preview

## Usage

### Preview what would be removed (safe):
```bash
python cleanup_mac_duplicates.py --dry-run --verbose
```

### Actually remove duplicates:
```bash
python cleanup_mac_duplicates.py --execute
```

### Custom directory:
```bash
python cleanup_mac_duplicates.py --directory /path/to/xml/files --execute
```

## Safety Features

- **Dry-run by default**: Never removes files unless `--execute` is specified
- **Size verification**: Only removes files with identical sizes
- **Detailed logging**: Shows exactly what will be/was removed
- **Error handling**: Continues processing if individual files fail
- **Preserves originals**: Always keeps the file with the simplest name

## Example Output

```
=== DRY RUN MODE - No files will be deleted ===
Found 57 verified duplicates for removal:
  - tlg0006.tlg001.perseus-grc2 2.xml
  - tlg0006.tlg001.perseus-eng2 2.xml
  - __cts__ 2.xml
  ...

Total duplicate files found: 57
Files that would be removed: 57
Run with --execute to actually remove the files
```

## Requirements

- Python 3.6+
- Standard library only (no external dependencies)

## Safety Note

Always run with `--dry-run` first to preview changes before using `--execute`.
