#!/usr/bin/env python3
"""Code metrics for the refactoring: size, complexity, tests and coverage, written as JSON so that "before" and "after" can be compared.

  python tools/ci/collect_metrics.py --out docs/refactor/baseline.json
Coverage comes from docs/refactor/coverage_baseline.json or from the .cov data of the last gate run (check_coverage.py).
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "ci"))
import check_complexity as CC          # noqa: E402

LONG_FILE = 300


def files(patterns):
    out = subprocess.run(["git", "ls-files", *patterns], cwd=REPO, capture_output=True, text=True, check=True).stdout.splitlines()
    return [f for f in out if not any(x in "/" + f for x in ("/node_modules/", "incoming/", "local/", "/migrations/"))]


def lines(rel):
    return len((REPO / rel).read_text(encoding="utf-8", errors="replace").splitlines())


def longest_functions(n=15):
    from radon.complexity import cc_visit
    rows = []
    for rel in CC.sources():
        try:
            blocks = cc_visit((REPO / rel).read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for b in blocks:
            if b.__class__.__name__ != "Class":
                rows.append((b.endline - b.lineno + 1, f"{rel}::{b.name}"))
    return [{"function": k, "lines": v} for v, k in sorted(rows, reverse=True)[:n]]


def count_tests():
    py = sum(len(re.findall(r"^\s+(?:async )?def test_", (REPO / f).read_text(encoding="utf-8", errors="replace"), re.M)) for f in files(["*.py"]) if "/tests/" in "/" + f or "/test_" in "/" + f)
    ts = sum(len(re.findall(r"^\s*(?:it|test)\(", (REPO / f).read_text(encoding="utf-8", errors="replace"), re.M)) for f in files(["*.test.ts", "*.test.tsx"]))
    return {"python": py, "frontend": ts}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="docs/refactor/baseline.json")
    a = ap.parse_args(argv)
    prod_py = [f for f in CC.sources()]
    prod_ts = [f for f in files(["*.ts", "*.tsx"]) if ".test." not in f and not f.endswith(".d.ts")]
    sizes = {f: lines(f) for f in prod_py + prod_ts}
    cc = CC.measure()
    cov_file = REPO / "docs" / "refactor" / "coverage_baseline.json"
    data = {
        "production_lines": {"python": sum(sizes[f] for f in prod_py), "typescript": sum(sizes[f] for f in prod_ts)},
        "files": {"python": len(prod_py), "typescript": len(prod_ts)},
        "files_over_300_lines": sorted(({"file": f, "lines": n} for f, n in sizes.items() if n > LONG_FILE), key=lambda r: -r["lines"]),
        "longest_functions": longest_functions(),
        "complexity": {"functions": len(cc), "above_10": sum(1 for v in cc.values() if v > 10), "above_20": sum(1 for v in cc.values() if v > 20),
                       "max": max(cc.values()), "mean": round(sum(cc.values()) / len(cc), 2)},
        "tests": count_tests(),
        "coverage_percent": {k: v["percent"] for k, v in json.loads(cov_file.read_text(encoding="utf-8")).items()} if cov_file.is_file() else {},
    }
    out = REPO / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: data[k] for k in ("production_lines", "files", "complexity", "tests", "coverage_percent")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
