"""python -m epc_arch PLAN --out DIR  [--units-per-metre N] [--page N]"""
import argparse
import json
import sys
from pathlib import Path

from epc_arch import ArchError, Options, recognize


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="epc_arch", description="walls, doors and windows from a DXF, a PDF or an image")
    ap.add_argument("plan")
    ap.add_argument("--out", default="out")
    ap.add_argument("--units-per-metre", type=float, default=None)
    ap.add_argument("--page", type=int, default=0)
    a = ap.parse_args(argv)
    src = Path(a.plan)
    try:
        result = recognize(src.read_bytes(), src.name, Options(units_per_metre=a.units_per_metre, page=a.page))
    except ArchError as e:
        print(f"ERROR {e}", file=sys.stderr)
        return 1
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{src.stem}.architecture.json").write_text(json.dumps(result.as_dict(), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / f"{src.stem}.architecture.svg").write_text(result.svg, encoding="utf-8")
    c = result.as_dict()["counts"]
    print(f"OK {c['walls']} walls, {c['doors']} doors, {c['windows']} windows, {c['openings']} openings -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
