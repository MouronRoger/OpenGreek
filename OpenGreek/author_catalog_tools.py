from __future__ import annotations

"""Utility script for working with TLG/legacy author catalogues.

This script provides two independent CLI sub-commands:

1. ``normalise`` – Create a *title-cased* copy of ``tlg_author_index.json`` so
   that the ``name`` field no longer appears in full upper-case.
2. ``coverage``  – Produce a CSV that lists every author/work combination in
   *either* catalogue, annotated with a column indicating which catalogue(s)
   contain the work:

   =======  =============================================================
   label    Meaning
   -------  -------------------------------------------------------------
   bot      Work exists in both catalogues (TLG integrated **and** legacy)
   tlg      Work exists only in the TLG integrated catalogue
   leg      Work exists only in the legacy catalogue
   =======  =============================================================

Both commands leave the original JSON files untouched – all new artefacts are
written to paths supplied via the CLI.  This helps guarantee that the process
is *safe* and fully reversible (just delete the generated files if you no
longer need them).

Usage examples
--------------
::

    # Normalise author names to title-case
    python author_catalog_tools.py normalise \
        --input ./data/tlg/catalogues/tlg_author_index.json \
        --output ./data/tlg/catalogues/tlg_author_index_titlecase.json

    # Create coverage report
    python author_catalog_tools.py coverage \
        --legacy ./data/tlg/catalogues/legacy_catalog.json \
        --tlg ./data/tlg/catalogues/tlg_integrated_catalog.json \
        --output ./author_work_coverage.csv \
        --language grc
"""

from pathlib import Path
import argparse
import csv
import json
from typing import Any, Dict, Mapping, MutableMapping, Sequence, Set

JSONDict = Dict[str, Any]


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

def _title_case(name: str) -> str:
    """Return ``name`` in title case, preserving multiple words.

    The default :py:meth:`str.title` works reasonably well for the catalogue
    because names are stored in ASCII/Latin transliteration, e.g. ``HESIODUS``.
    For Greek characters you may want to use a dedicated library such as
    ``str.title()`` from *python-unicodedata2*, but that is beyond the current
    scope and not required for the English transliterations present in the
    JSON files.
    """

    return name.title()


def normalise_author_index(input_path: Path, output_path: Path) -> None:
    """Create a new author-index JSON file with title-cased names."""

    data: JSONDict = json.loads(input_path.read_text(encoding="utf-8"))
    for entry in data.values():  # mutate in-place
        if "name" in entry:
            entry["name"] = _title_case(str(entry["name"]))

    output_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"Normalised author index written to {output_path}")


# ---------------------------------------------------------------------------
# Coverage helpers
# ---------------------------------------------------------------------------

def _collect_works(
    catalogue: Mapping[str, JSONDict], *, languages: Set[str] | None = None
) -> Dict[tuple[str, str], JSONDict]:
    """Return mapping of (author_id, work_id) → metadata for selected *languages*.

    If *languages* is *None*, no language filtering is applied.  Otherwise a
    work is included **only if** its ``language`` metadata matches a value in
    *languages* (case-insensitive).
    """

    norm_langs = {lang.lower() for lang in languages} if languages else None

    works: Dict[tuple[str, str], JSONDict] = {}
    for author_id, author_meta in catalogue.items():
        for work_id, work_meta in author_meta.get("works", {}).items():
            work_lang = str(work_meta.get("language", "")).lower()
            if norm_langs is not None and work_lang not in norm_langs:
                continue

            key = (author_id, work_id)
            # Shallow-copy so we can attach author data without mutating source
            combined: JSONDict = {
                "author_id": author_id,
                "work_id": work_id,
                "author_name": author_meta.get("name", ""),
                "work_title": work_meta.get("title", ""),
            }
            works[key] = combined
    return works


def generate_coverage_csv(
    legacy_catalog_path: Path,
    tlg_catalog_path: Path,
    output_csv_path: Path,
    *,
    languages: Sequence[str] | None = None,
) -> None:
    """Generate a CSV summarising work coverage across catalogues.

    Only works whose ``language`` field matches **any** of *languages* (case-
    insensitive) are considered.  If *languages* is *None* or empty, works of
    **all** languages are compared.
    """

    legacy_catalog: JSONDict = json.loads(
        legacy_catalog_path.read_text(encoding="utf-8")
    )
    tlg_catalog: JSONDict = json.loads(tlg_catalog_path.read_text(encoding="utf-8"))

    lang_set = {lang.lower() for lang in languages} if languages else None

    legacy_works = _collect_works(legacy_catalog, languages=lang_set)
    tlg_works = _collect_works(tlg_catalog, languages=lang_set)

    all_keys = set(legacy_works) | set(tlg_works)

    with output_csv_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["author_id", "work_id", "author_name", "work_title", "coverage"])

        for key in sorted(all_keys):
            in_legacy = key in legacy_works
            in_tlg = key in tlg_works

            if in_legacy and in_tlg:
                label = "bot"
                # Prefer the TLG entry's metadata where overlaps exist
                row_meta = {**legacy_works[key], **tlg_works[key]}
            elif in_tlg:
                label = "tlg"
                row_meta = tlg_works[key]
            else:
                label = "leg"
                row_meta = legacy_works[key]

            writer.writerow(
                [
                    row_meta["author_id"],
                    row_meta["work_id"],
                    row_meta["author_name"],
                    row_meta["work_title"],
                    label,
                ]
            )

    print(f"Coverage CSV written to {output_csv_path}")


# ---------------------------------------------------------------------------
# CLI plumbing
# ---------------------------------------------------------------------------

def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:  # noqa: D401
    """Return parsed CLI arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    # normalise sub-command
    norm_parser = subparsers.add_parser(
        "normalise", help="Normalise author names to title case"
    )
    norm_parser.add_argument("--input", type=Path, required=True, help="Input tlg_author_index.json path")
    norm_parser.add_argument("--output", type=Path, required=True, help="Output JSON path")

    # coverage sub-command
    cov_parser = subparsers.add_parser(
        "coverage", help="Generate coverage CSV for works across catalogues"
    )
    cov_parser.add_argument("--legacy", type=Path, required=True, help="Legacy catalogue JSON path")
    cov_parser.add_argument("--tlg", type=Path, required=True, help="TLG integrated catalogue JSON path")
    cov_parser.add_argument("--output", type=Path, required=True, help="Output CSV path")
    cov_parser.add_argument(
        "--language",
        "--languages",
        nargs="+",
        default=["grc"],
        help="One or more language codes to include (default: grc)",
    )

    # copy sub-command
    copy_parser = subparsers.add_parser(
        "copy", help="Copy legacy-only XML texts to destination directory"
    )
    copy_parser.add_argument("--csv", type=Path, required=True, help="Coverage CSV path")
    copy_parser.add_argument(
        "--legacy-base",
        type=Path,
        required=True,
        help="Base directory of legacy eulogos2 data (authors/works)",
    )
    copy_parser.add_argument(
        "--dest-base",
        type=Path,
        required=True,
        help="Destination directory to copy XML texts into",
    )

    return parser.parse_args(argv)


def main() -> None:  # noqa: D401
    """Entry-point executed by ``python author_catalog_tools.py …``."""

    args = _parse_args()

    if args.command == "normalise":
        normalise_author_index(args.input, args.output)
    elif args.command == "coverage":
        generate_coverage_csv(
            args.legacy, args.tlg, args.output, languages=args.language
        )
    elif args.command == "copy":
        copy_legacy_texts(
            csv_path=args.csv,
            legacy_base=args.legacy_base,
            dest_base=args.dest_base,
        )
    else:  # pragma: no cover – argparse enforces valid command
        raise RuntimeError(f"Unknown command: {args.command}")


# ---------------------------------------------------------------------------
# Copy legacy XML texts helper
# ---------------------------------------------------------------------------

import shutil


def _copy_xml_files(src_dir: Path, dest_dir: Path) -> None:
    """Copy all ``.xml`` files recursively from *src_dir* into *dest_dir*."""

    if not src_dir.exists():
        return

    for path in src_dir.rglob("*.xml"):
        rel_path = path.relative_to(src_dir)
        target_path = dest_dir / rel_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target_path)


def copy_legacy_texts(*, csv_path: Path, legacy_base: Path, dest_base: Path) -> None:
    """Copy XML texts for works marked as *legacy-only* in *csv_path*.

    Parameters
    ----------
    csv_path
        CSV produced by :pymeth:`generate_coverage_csv` with at least the
        columns ``author_id``, ``work_id`` and ``coverage``.
    legacy_base
        Path to the *eulogos2* ``data`` directory containing author/work
        sub-directories.
    dest_base
        Destination directory where XML files will be copied.  The structure
        ``author_id/work_id/…`` is preserved.
    """

    dest_base.mkdir(parents=True, exist_ok=True)

    with csv_path.open(newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row.get("coverage") != "leg":
                continue

            author_id = row["author_id"].strip()
            work_id = row["work_id"].strip()

            src_dir = legacy_base / author_id / work_id
            dest_dir = dest_base / author_id / work_id

            _copy_xml_files(src_dir, dest_dir)

    print(f"Legacy XML files copied into {dest_base}")


if __name__ == "__main__":
    main()
