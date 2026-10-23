#!/usr/bin/env python3
"""
assemble-spec.py — Assembles a Ford technical spec from checked LEGO blocks.

Usage:
    python3 assemble-spec.py <discipline> [--out FILENAME]

Disciplines:
    electrical          → knowledge/templates/electrical/
    civil               → knowledge/templates/civil/blocks/
    fire-suppression    → knowledge/templates/fire-suppression/blocks/
    fire-detection      → knowledge/templates/fire-detection/blocks/
    hvac                → knowledge/templates/hvac/blocks/
    thermomechanical    → knowledge/templates/thermomechanical/blocks/

Examples:
    python3 assemble-spec.py electrical
    python3 assemble-spec.py electrical --out spec-workshop-a.md
    python3 assemble-spec.py civil --list
"""

import re
import sys
import argparse
from pathlib import Path

BASE = Path(__file__).parent / "knowledge/templates"

DISCIPLINE_MAP = {
    "electrical":       BASE / "electrical",
    "civil":            BASE / "civil/blocks",
    "fire-suppression": BASE / "fire-suppression/blocks",
    "fire-detection":   BASE / "fire-detection/blocks",
    "hvac":             BASE / "hvac/blocks",
    "thermomechanical": BASE / "thermomechanical/blocks",
}

OUT_DIR = Path(__file__).parent / "knowledge/assembled"


def parse_checklist(blocks_dir: Path) -> list[str]:
    """
    Reads 00-project-data.md and returns the list of files marked [x].
    The 00 block is always first.
    """
    index_file = blocks_dir / "00-project-data.md"
    if not index_file.exists():
        raise FileNotFoundError(f"Not found: {index_file}")

    text = index_file.read_text(encoding="utf-8")

    pattern = re.compile(
        r"\|\s*[\w\.]+\s*\|[^|]+\|\s*`([^`]+\.md)`\s*\|[^|]+\|\s*\[x\]\s*\|",
        re.IGNORECASE,
    )
    files = pattern.findall(text)

    ordered = ["00-project-data.md"]
    for f in files:
        if f not in ordered:
            ordered.append(f)
    return ordered


def assemble(blocks_dir: Path, file_list: list[str], out_path: Path):
    parts = []
    missing = []
    for fname in file_list:
        fpath = blocks_dir / fname
        if not fpath.exists():
            missing.append(fname)
            continue
        content = fpath.read_text(encoding="utf-8").strip()
        lines = content.split("\n")
        if lines and lines[0].strip().startswith("<!--"):
            lines = lines[1:]
        parts.append("\n".join(lines).strip())
    if missing:
        print(f"  ⚠ Missing (skipped): {', '.join(missing)}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n\n---\n\n".join(parts), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(
        description="Assembles a Ford technical spec from LEGO blocks."
    )
    parser.add_argument(
        "discipline",
        choices=list(DISCIPLINE_MAP.keys()),
        help="Discipline to assemble",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Output filename (no path). Default: spec-<discipline>.md",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Show selected blocks only, do not write file",
    )
    args = parser.parse_args()

    blocks_dir = DISCIPLINE_MAP[args.discipline]

    print(f"\n{'='*60}")
    print(f"  assemble-spec.py  |  discipline: {args.discipline}")
    print(f"  blocks: {blocks_dir.relative_to(Path(__file__).parent)}")
    print(f"{'='*60}\n")

    print("  Reading checklist from 00-project-data.md ...")
    try:
        file_list = parse_checklist(blocks_dir)
    except FileNotFoundError as e:
        print(f"  ERROR: {e}")
        sys.exit(1)

    print(f"  Selected blocks ({len(file_list)}):")
    for i, f in enumerate(file_list, 1):
        status = "✓" if (blocks_dir / f).exists() else "✗ NOT FOUND"
        print(f"    {i:2}. {f:<55} {status}")

    if args.list:
        print("\n  --list mode: no file written.\n")
        return

    out_name = args.out or f"spec-{args.discipline}.md"
    out_path = OUT_DIR / out_name

    print(f"\n  Assembling → {out_path.relative_to(Path(__file__).parent)}")
    assemble(blocks_dir, file_list, out_path)

    size_kb = out_path.stat().st_size / 1024
    print(f"  ✓ Generated: {out_path.name}  ({size_kb:.1f} KB)")
    print("  Next: replace all {{VARIABLES}} with project-specific values.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
