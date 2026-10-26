#!/usr/bin/env python3
"""Quality gate: the test battery that must be green before a branch is merged into dev.

  python tools/ci/run_gate.py [--fast] [--no-web]

Checks
  registry          plugin registry (plugins, skills, agents, engine areas)
  skill-conflicts   duplicate / orphan skills (production rules)
  single-source     no two versioned files hold the same content (one source of truth per datum)
  dev-credentials   no development credential (the MASTER account) is versioned: it can never reach main
  coverage          each area keeps at least its measured coverage (tools/ci/coverage_floor.json); the suites run under `coverage`
  complexity        no function becomes more complex than its baseline; a new function stays at or below 10 (tools/ci/complexity_baseline.json)
  board             planning/BOARD.md is up to date
  api               API tests (user surface, role guard, uploads, project creation)
  engine-calc       LV calculation tests
  engine-rules      rules engine tests
  engine-standards  standards ingestion and promotion tests
  engine-drawing    symbol library tests
  engine-documents  document verifiers, CCPM, exporters (environment-dependent tests are skipped)
  intake            customer-input pipeline tests
  sld-smoke         single-line diagram generated from the example through the engine, no warnings
  frontend-boundaries, web-types, web-build   frontend rules, TypeScript type-check of web+console (and build unless --fast)
  web-tests         Vitest characterization tests of the shared UI and the screens
  marketplace       plugins assembled in Claude Code's layout, validated with `claude plugin validate --strict`
The engine packages are put on PYTHONPATH, so no installation is needed. Exit code 0 only when every check passes.
"""
import argparse
import os
import shutil
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


PYTHON = first(REPO / ".venv" / "Scripts" / "python.exe", REPO / ".venv" / "bin" / "python") or Path(sys.executable)
PLUGINS = REPO / "claude" / "plugins"
ENGINE = REPO / "engine"
AREAS = ("calc", "rules", "standards", "drawing", "documents")
BUILD = first(REPO / "tools" / "build" / "epc_build.py")
CONFLICTS = first(REPO / "tools" / "ci" / "check_skill_conflicts.py")
BOARD = first(REPO / "tools" / "planning" / "board.py")
WEB = first(REPO / "frontend")
RESULTS = []
COV_DIR = REPO / ".cov"
ENGINE_ENV = {"PYTHONPATH": os.pathsep.join([str(ENGINE / a / "src") for a in AREAS if (ENGINE / a / "src").is_dir()] + [os.environ.get("PYTHONPATH", "")])}


def covered(py, source):
    """Prefix that runs a Python module under coverage (data pieces go to .cov/ and are combined by check_coverage.py)."""
    return [py, "-m", "coverage", "run", "--parallel-mode", f"--source={source}", "-m"]


def cov_env(env=None):
    return dict(env or {}, COVERAGE_FILE=str(COV_DIR / ".coverage"))


def keep_failure(name, ok, out):
    """The summary shows three lines of a failed check; its whole output is kept in .cov/ for diagnosis."""
    if not ok:
        COV_DIR.mkdir(exist_ok=True)
        (COV_DIR / f"failed-{name}.txt").write_text(out, encoding="utf-8")


def run(name, cmd, cwd, must_not_contain=None, env=None):
    t0 = time.time()
    p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, env=dict(os.environ, **(env or {})))
    out = (p.stdout or "") + (p.stderr or "")
    ok = p.returncode == 0 and not (must_not_contain and must_not_contain in out)
    RESULTS.append((name, ok, round(time.time() - t0, 1), out.strip().splitlines()[-3:] if not ok else []))
    keep_failure(name, ok, out)
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true", help="skip the web production build")
    ap.add_argument("--no-web", action="store_true")
    a = ap.parse_args()
    py = str(PYTHON)
    shutil.rmtree(COV_DIR, ignore_errors=True)
    COV_DIR.mkdir(exist_ok=True)

    run("registry", [py, str(BUILD), "registry", "--check"], REPO)
    run("skill-conflicts", [py, str(CONFLICTS), "--env", "production"], REPO)
    if BOARD:
        run("board", [py, str(BOARD), "--check"], REPO)
    backend = REPO / "backend"
    benv = dict(ENGINE_ENV, PYTHONPATH=os.pathsep.join([str(backend / "src"), ENGINE_ENV["PYTHONPATH"]]))
    run("ignored-sources", [py, str(REPO / "tools" / "ci" / "check_ignored_sources.py")], REPO)
    run("single-source", [py, str(REPO / "tools" / "ci" / "check_single_source.py")], REPO)
    run("dev-credentials", [py, str(REPO / "tools" / "ci" / "check_dev_credentials.py")], REPO)
    run("complexity", [py, str(REPO / "tools" / "ci" / "check_complexity.py")], REPO)
    run("importlinter-config", [py, str(REPO / "tools" / "ci" / "gen_importlinter.py"), "--check"], REPO)
    run("backend-contracts", [py, "-c", "from importlinter.cli import lint_imports_command as m; m()", "--config", str(backend / ".importlinter")], backend, env=benv)
    run("backend", covered(py, str(backend / "src" / "epc")) + ["unittest", "discover", "-s", "tests", "-t", "."], backend, env=cov_env(benv))
    if (REPO / "database" / "alembic.ini").exists():
        run("database", [py, "-m", "unittest", "discover", "-s", "tests", "-t", "."], REPO / "database")
    run("infra", [py, str(REPO / "tools" / "ci" / "check_infra.py")], REPO)
    for area in AREAS:
        d = ENGINE / area
        if (d / "tests").is_dir():
            run(f"engine-{area}", covered(py, str(d / "src")) + ["unittest", "discover", "-s", "tests"], d, env=cov_env(ENGINE_ENV))
    run("coverage", [py, str(REPO / "tools" / "ci" / "check_coverage.py")], REPO)
    intake = PLUGINS / "intake-analysis" / "scripts"
    if intake.is_dir():
        run("intake", [py, "-m", "unittest", "test_intake"], intake)

    run("impact-map", [py, str(REPO / "tools" / "build" / "impact_map.py"), "--check"], REPO)

    example = ENGINE / "drawing" / "examples" / "sld"
    if example.is_dir():
        out = Path(tempfile.mkdtemp(prefix="gate_sld_"))
        run("sld-smoke", [py, "-m", "epc_drawing.board_design", "--xlsx", str(example / "input_for_sld_V1.xlsx"), "--out", str(out), "--name", "SLD_V1"],
            REPO, must_not_contain="AVISO", env=ENGINE_ENV)

    if WEB and not a.no_web and (WEB / "node_modules").exists():
        npm = "npm.cmd" if os.name == "nt" else "npm"
        run("frontend-boundaries", [py, str(REPO / "tools" / "ci" / "check_frontend_boundaries.py")], REPO)
        run("web-types", [npm, "run", "typecheck"], WEB)
        run("web-tests", [npm, "run", "test"], WEB)
        if not a.fast:
            run("web-build", [npm, "run", "build"], WEB)

    claude = shutil.which("claude")
    if claude and BUILD:
        market = REPO / "dist" / "marketplace"
        if run("marketplace-build", [py, str(BUILD), "marketplace"], REPO) and market.exists():
            targets = [market] + sorted(p for p in (market / "plugins").iterdir() if p.is_dir())
            bad, t0 = [], time.time()
            for tgt in targets:
                p = subprocess.run([claude, "plugin", "validate", "--strict", str(tgt)], capture_output=True, text=True)
                if p.returncode != 0 or "Validation passed" not in (p.stdout or ""):
                    bad.append(tgt.name + ": " + ((p.stdout or "") + (p.stderr or "")).strip().splitlines()[-1][:120])
            RESULTS.append(("claude-validate", not bad, round(time.time() - t0, 1), bad[:3]))
    else:
        print("note: claude CLI not found, skipping official plugin validation")

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
