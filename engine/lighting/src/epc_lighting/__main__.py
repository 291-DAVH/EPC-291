"""python -m epc_lighting INPUT --out DIR [--enforce-spacing] [--spacing-basis height|distribution] [--point-step M] [--no-points]"""
import argparse
import json
import sys
from pathlib import Path

from epc_lighting import LightingError, Options, run


def _parser() -> argparse.ArgumentParser:
    defaults = Options()
    ap = argparse.ArgumentParser(prog="epc_lighting", description="Calculate luminaire count, layout and illuminance from a lighting JSON document.")
    ap.add_argument("input", help="lighting document (JSON)")
    ap.add_argument("--out", default="out", help="output folder (the only place written)")
    ap.add_argument("--enforce-spacing", action="store_true", help="add rows/columns until the maximum spacing is respected")
    ap.add_argument("--spacing-basis", choices=["height", "distribution"], default=defaults.spacing_basis)
    ap.add_argument("--point-step", type=float, default=defaults.point_step_m, help="grid step in metres for point-by-point")
    ap.add_argument("--no-points", action="store_true", help="skip the point-by-point calculation")
    return ap


def main(argv=None) -> int:
    args = _parser().parse_args(argv)
    src = Path(args.input)
    options = Options(
        enforce_spacing=args.enforce_spacing,
        spacing_basis=args.spacing_basis,
        compute_points=not args.no_points,
        point_step_m=args.point_step,
    )
    try:
        result = run(src.read_bytes(), options)
    except OSError as exc:
        print(f"ERROR cannot read {src}: {exc.strerror or exc}", file=sys.stderr)
        return 1
    except LightingError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(result.as_dict(), indent=1, ensure_ascii=False) + "\n"
    (out / f"{src.stem}.lighting.json").write_text(payload, encoding="utf-8")
    counts = result.as_dict()["counts"]
    print(f"OK {counts['rooms']} rooms, {counts['areas']} areas, {counts['luminaires']} luminaires, {counts['warnings']} warnings -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
