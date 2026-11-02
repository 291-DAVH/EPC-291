"""python -m epc_receptacles INPUT --out DIR [--norm 771|770]"""
import argparse
import json
import sys
from pathlib import Path

from epc_receptacles import Options, ReceptaclesError, run
from epc_receptacles.model import NORMS


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="epc_receptacles", description="Calculate the socket outlets of the rooms of a JSON document.")
    ap.add_argument("input", help="receptacles document (JSON)")
    ap.add_argument("--out", default="out", help="output folder (the only place written)")
    ap.add_argument("--norm", choices=NORMS, default=Options().norm, help="section of AEA 90364 whose mounting heights are checked")
    args = ap.parse_args(argv)
    src = Path(args.input)
    try:
        result = run(src.read_bytes(), Options(norm=args.norm))
    except OSError as exc:
        print(f"ERROR cannot read {src}: {exc.strerror or exc}", file=sys.stderr)
        return 1
    except ReceptaclesError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{src.stem}.receptacles.json").write_text(json.dumps(result.as_dict(), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    counts = result.as_dict()["counts"]
    print(f"OK {counts['rooms']} rooms, {counts['outlets']} outlets, {counts['warnings']} warnings -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
