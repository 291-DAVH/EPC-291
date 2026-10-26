#!/usr/bin/env python3
"""Cyclomatic-complexity ratchet over the production Python code.

  python tools/ci/check_complexity.py            # check against tools/ci/complexity_baseline.json
  python tools/ci/check_complexity.py --update   # rewrite the baseline from the code as it is now
  python tools/ci/check_complexity.py --report   # print the most complex functions

The baseline maps a function's qualified name (module path + name, without line numbers) to its complexity. A function may not become MORE complex than its
baseline, and a function that is not in the baseline (new, or moved to another file) may not exceed MAX_NEW. Moving a function keeps its baseline because the key
is the qualified name inside its file's module name, resolved by name when the file moved: see `_lookup`.
Open-source: radon (MIT).
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BASELINE = REPO / "tools" / "ci" / "complexity_baseline.json"
MAX_NEW = 10
EXCLUDED = ("/tests/", "/test_", "incoming/", "local/", "node_modules/", ".venv/", "/migrations/")


def sources():
    out = subprocess.run(["git", "ls-files", "*.py"], cwd=REPO, capture_output=True, text=True, check=True).stdout.splitlines()
    return [f for f in out if not any(x in "/" + f for x in EXCLUDED)]


def measure():
    """{ "path::Class.method": complexity } for every function and method of the production code."""
    from radon.complexity import cc_visit
    result = {}
    for rel in sources():
        try:
            blocks = cc_visit((REPO / rel).read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for b in blocks:
            if b.__class__.__name__ == "Class":
                continue
            name = f"{b.classname}.{b.name}" if getattr(b, "classname", None) else b.name
            key = f"{rel}::{name}"
            result[key] = max(result.get(key, 0), b.complexity)
    return result


def _name(key: str) -> str:
    return key.split("::", 1)[1]


def _lookup(key: str, baseline: dict, by_name: dict):
    """Baseline complexity for `key`: its own, else that of the same-named function in another file (it moved)."""
    return baseline.get(key, by_name.get(_name(key)))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--update", action="store_true")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args(argv)
    now = measure()
    if a.update:
        BASELINE.write_text(json.dumps(dict(sorted(now.items())), indent=0, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"baseline written: {len(now)} functions, {sum(1 for v in now.values() if v > MAX_NEW)} above {MAX_NEW}")
        return 0
    if a.report:
        for k, v in sorted(now.items(), key=lambda kv: -kv[1])[:40]:
            print(f"{v:4d}  {k}")
        return 0
    baseline = json.loads(BASELINE.read_text(encoding="utf-8")) if BASELINE.is_file() else {}
    by_name = {}
    for k, v in baseline.items():
        by_name[_name(k)] = max(v, by_name.get(_name(k), 0))
    bad = []
    for key, cc in now.items():
        base = _lookup(key, baseline, by_name)
        if base is None and cc > MAX_NEW:
            bad.append(f"{key}: new function with complexity {cc} (max {MAX_NEW})")
        elif base is not None and cc > base:
            bad.append(f"{key}: complexity {cc} above its baseline {base}")
    for line in bad[:30]:
        print("FAIL", line)
    above = sum(1 for v in now.values() if v > MAX_NEW)
    base_above = sum(1 for v in baseline.values() if v > MAX_NEW)
    print(f"{len(now)} functions, {above} above {MAX_NEW} (baseline {base_above})")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
