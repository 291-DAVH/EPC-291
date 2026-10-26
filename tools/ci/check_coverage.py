#!/usr/bin/env python3
"""Coverage floor over the Python code, measured while the gate runs the suites.

  python tools/ci/check_coverage.py            # combine the data the gate collected and compare each area with tools/ci/coverage_floor.json
  python tools/ci/check_coverage.py --update   # write the floor from the data now collected (floor = measured percentage, rounded down to 0.1, minus TOLERANCE)

The suites run under `coverage run --parallel-mode` with COVERAGE_FILE pointing at `.cov/.coverage`; this script combines the pieces and groups the files by area.
Code that runs in a child process (the engine's generators called by the backend) is not measured: the golden tests of the engine cover it.
Open-source: coverage (Apache-2.0).
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
COV_DIR = REPO / ".cov"
FLOOR = REPO / "tools" / "ci" / "coverage_floor.json"
TOLERANCE = 0.3                      # points: runs are not byte-identical (threads, timing)
AREAS = {                            # area -> path fragment of its production code
    "backend": "/backend/src/epc/",
    "engine-calc": "/engine/calc/src/",
    "engine-rules": "/engine/rules/src/",
    "engine-standards": "/engine/standards/src/",
    "engine-drawing": "/engine/drawing/src/",
    "engine-documents": "/engine/documents/src/",
}


def combine() -> dict:
    env = dict(os.environ, COVERAGE_FILE=str(COV_DIR / ".coverage"))
    py = sys.executable
    pieces = list(COV_DIR.glob(".coverage.*"))
    if not pieces and not (COV_DIR / ".coverage").is_file():
        print("no coverage data collected: run the gate, which runs the suites under coverage")
        return {}
    if pieces:                                                   # the pieces of this run; a repeated call finds them already combined
        subprocess.run([py, "-m", "coverage", "combine", "--append", "--quiet"], cwd=REPO, env=env, check=True)
    out = COV_DIR / "coverage.json"
    subprocess.run([py, "-m", "coverage", "json", "-q", "-o", str(out)], cwd=REPO, env=env, check=True)
    files = json.loads(out.read_text(encoding="utf-8"))["files"]
    totals = {a: [0, 0] for a in AREAS}                      # statements, covered
    for path, info in files.items():
        norm = "/" + path.replace("\\", "/").lstrip("/")
        for area, frag in AREAS.items():
            if frag in norm:
                s = info["summary"]
                totals[area][0] += s["num_statements"]
                totals[area][1] += s["covered_lines"]
    return {a: {"statements": n, "covered": c, "percent": round(100.0 * c / n, 2) if n else 0.0} for a, (n, c) in totals.items()}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--update", action="store_true")
    a = ap.parse_args(argv)
    now = combine()
    if not now:
        return 1
    if a.update:
        floor = {k: round(max(0.0, int(v["percent"] * 10) / 10 - TOLERANCE), 1) for k, v in now.items()}
        FLOOR.write_text(json.dumps(floor, indent=1) + "\n", encoding="utf-8")
        (REPO / "docs" / "refactor").mkdir(parents=True, exist_ok=True)
        (REPO / "docs" / "refactor" / "coverage_baseline.json").write_text(json.dumps(now, indent=1) + "\n", encoding="utf-8")
        print("floor written:", floor)
        return 0
    floor = json.loads(FLOOR.read_text(encoding="utf-8")) if FLOOR.is_file() else {}
    bad = []
    for area, v in now.items():
        want = floor.get(area, 0.0)
        mark = "FAIL" if v["percent"] < want else "ok  "
        print(f"{mark} {area:18s} {v['percent']:6.2f} %  ({v['covered']}/{v['statements']} statements)  floor {want}")
        if v["percent"] < want:
            bad.append(area)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
