#!/usr/bin/env python3
"""Quality gate: the test battery that must be green before a branch is merged into dev.

  python tools/ci/run_gate.py [--fast] [--no-web]

Checks (paths are detected, so the same gate works before and after each migration phase):
  registry         plugin registry + skill ownership
  skill-conflicts  duplicate / orphan skills (production rules)
  board            planning/BOARD.md is up to date
  api              API tests (user surface, role guard, uploads, project creation)
  aea-calc         205 calculation tests
  intake           customer-input pipeline tests
  standard-ingest  ingestion and promotion tests
  rules-engine     rules engine tests
  sld-smoke        single-line diagram generated from the example, no warnings
  web              TypeScript type-check (and build unless --fast)
Exit code 0 only when every check passes.
"""
import argparse
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def first(*paths):
    for p in paths:
        if p and Path(p).exists():
            return Path(p)
    return None


PLATFORM = first(REPO / "platform")
PYTHON = first(REPO / "backend" / ".venv" / "Scripts" / "python.exe", PLATFORM / ".venv" / "Scripts" / "python.exe",
               REPO / ".venv" / "Scripts" / "python.exe", PLATFORM / ".venv" / "bin" / "python") or Path(sys.executable)
PLUGINS = first(REPO / "claude" / "plugins", PLATFORM / "hub")
BUILD = first(REPO / "tools" / "build" / "epc_build.py", PLATFORM / "tools" / "build" / "epc_build.py")
CONFLICTS = first(REPO / "tools" / "ci" / "check_skill_conflicts.py", PLATFORM / "tools" / "ci" / "check_skill_conflicts.py")
BOARD = first(REPO / "tools" / "planning" / "board.py")
API_CWD = first(REPO / "backend", PLATFORM)
RULES_CWD = first(REPO / "engine" / "rules", PLATFORM / "core" / "rules")
WEB = first(REPO / "frontend" / "web", PLATFORM / "apps" / "web")
RESULTS = []


def run(name, cmd, cwd, expect_ok=True, must_not_contain=None, env=None):
    t0 = time.time()
    e = dict(os.environ, **(env or {}))
    p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, env=e)
    out = (p.stdout or "") + (p.stderr or "")
    ok = (p.returncode == 0) == expect_ok
    if ok and must_not_contain and must_not_contain in out:
        ok = False
    RESULTS.append((name, ok, round(time.time() - t0, 1), out.strip().splitlines()[-3:] if not ok else []))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true", help="skip the web production build")
    ap.add_argument("--no-web", action="store_true")
    a = ap.parse_args()
    py = str(PYTHON)

    run("registry", [py, str(BUILD), "registry"], REPO)
    run("skill-conflicts", [py, str(CONFLICTS), "--env", "production"], REPO)
    if BOARD:
        run("board", [py, str(BOARD), "--check"], REPO)
    run("api", [py, "-m", "unittest", "apps.api.test_projects", "apps.api.test_app"], API_CWD)
    for name, folder, args in [
        ("aea-calc", "aea-calc/scripts", ["discover", "-s", ".", "-p", "test_*.py"]),
        ("intake", "intake-analysis/scripts", ["test_intake"]),
        ("standard-ingest", "standard-ingest/scripts", ["test_ingest"]),
    ]:
        d = PLUGINS / folder
        if d.exists():
            run(name, [py, "-m", "unittest", *args], d)
    if RULES_CWD:
        run("rules-engine", [py, "-m", "unittest", "discover", "-s", "tests"], RULES_CWD)
    sld = PLUGINS / "sld"
    if (sld / "scripts" / "sld_paginate.py").exists():
        out = tempfile.mkdtemp(prefix="gate_sld_")
        run("sld-smoke", [py, "scripts/sld_paginate.py", "default", "examples/input_for_sld_V1.xlsx", out, "SLD_V1", "default", "default"],
            sld, must_not_contain="AVISO")
    if WEB and not a.no_web and (WEB / "node_modules").exists():
        npx = "npx.cmd" if os.name == "nt" else "npx"
        run("web-types", [npx, "tsc", "--noEmit"], WEB)
        if not a.fast:
            npm = "npm.cmd" if os.name == "nt" else "npm"
            run("web-build", [npm, "run", "build"], WEB)

    width = max(len(r[0]) for r in RESULTS)
    for name, ok, secs, tail in RESULTS:
        print(f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}  {secs:>5}s")
        for line in tail:
            print("      |", line)
    failed = [r[0] for r in RESULTS if not r[1]]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed" + (f"  FAILED: {', '.join(failed)}" if failed else "  GATE GREEN"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
