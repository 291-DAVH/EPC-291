"""python -m epc_plan --demo --out DIR   |   python -m epc_plan --input FILE.json --out DIR"""
import argparse
import json
import sys
from pathlib import Path

from epc_plan import jobs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="epc_plan")
    ap.add_argument("--input", help="input document (JSON)")
    ap.add_argument("--demo", action="store_true", help="use the sample of fixtures/")
    ap.add_argument("--out", default="out")
    a = ap.parse_args(argv)
    if a.demo:
        src = Path(__file__).resolve().parents[2] / "fixtures" / "input.json"
    elif a.input:
        src = Path(a.input)
    else:
        ap.error("give --demo or --input")
    result = jobs.run(json.loads(src.read_text(encoding="utf-8")), Path(a.out))
    print(f"OK {Path(a.out) / 'result.json'} ({len(result['stretches'])} stretches, {result['schedule']['total_length_m']} m, DXF {result['files']['dxf']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
