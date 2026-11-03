"""python -m epc_arch PLAN --out DIR  [--units-per-metre N] [--page N] [--background]

A plan gives `<name>.architecture.json` and `.svg`. A sheet with several plans (one per floor) also gives one pair per plan, `<name>.<floor>.architecture.json` and `.svg` (floor: `L0`, `L1`, `L-1`...,
or `plan1`, `plan2` when the sheet does not name them), all in the same frame, and `<name>.sheet.json` listing them; `<name>.architecture.*` is then the lowest floor."""
import argparse
import json
import sys
from pathlib import Path

from epc_arch import ArchError, Options
from epc_arch.pipeline import Result, recognize_sheet


def _tag(result: Result, position: int) -> str:
    level = result.architecture.level
    return f"L{level.index}" if level and level.index is not None else f"plan{position}"


def _write(out: Path, stem: str, result: Result) -> None:
    (out / f"{stem}.architecture.json").write_text(json.dumps(result.as_dict(), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / f"{stem}.architecture.svg").write_text(result.svg, encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="epc_arch", description="walls, doors and windows from a DXF, a PDF or an image")
    ap.add_argument("plan")
    ap.add_argument("--out", default="out")
    ap.add_argument("--units-per-metre", type=float, default=None)
    ap.add_argument("--page", type=int, default=0)
    ap.add_argument("--background", action="store_true", help="draw the original linework faintly under the plan")
    a = ap.parse_args(argv)
    src = Path(a.plan)
    try:
        sheet = recognize_sheet(src.read_bytes(), src.name, Options(units_per_metre=a.units_per_metre, page=a.page, background=a.background))
    except ArchError as e:
        print(f"ERROR {e}", file=sys.stderr)
        return 1
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    first = sheet.levels[0]
    if len(sheet.levels) > 1:
        first.architecture.warnings.append(f"the file is a sheet with {len(sheet.levels)} plans: this is the lowest; each plan has its own files")
        listing = sheet.as_dict()
        for i, r in enumerate(sheet.levels, 1):
            _write(out, f"{src.stem}.{_tag(r, i)}", r)
            listing["levels"][i - 1]["file"] = f"{src.stem}.{_tag(r, i)}.architecture.json"
        (out / f"{src.stem}.sheet.json").write_text(json.dumps(listing, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    _write(out, src.stem, first)
    c = first.as_dict()["counts"]
    print(f"OK {len(sheet.levels)} plan(s): {c['walls']} walls, {c['doors']} doors, {c['windows']} windows, {c['openings']} openings (the first) -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
