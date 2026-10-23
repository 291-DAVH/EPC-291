"""Guards against source files silently excluded by an ignore rule (they pass locally and fail on a clean checkout).

  python tools/ci/check_ignored_sources.py

Lists untracked files that .gitignore hides, except the known generated/private folders. Any other hit means a
source file (or a folder such as backend/src/epc/modules/knowledge) is being ignored by mistake.
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ALLOWED_PARTS = {"node_modules", ".venv", "__pycache__", "dist", ".import_linter_cache", ".pytest_cache", "_out", ".mypy_cache"}
ALLOWED_TOP = {"local", ".claude", "respuestas.md"}
ALLOWED_SUFFIX = (".egg-info", ".pyc", ".bak", ".tmp", ".plugin")


def main() -> int:
    if not (REPO / ".git").exists():
        print("ignored-sources: no git checkout, skipped")
        return 0
    out = subprocess.run(["git", "ls-files", "--others", "--ignored", "--exclude-standard", "--directory"], cwd=REPO, capture_output=True, text=True)
    bad = []
    for line in out.stdout.splitlines():
        p = Path(line.rstrip("/"))
        parts = set(p.parts)
        if parts & ALLOWED_PARTS or p.parts[0] in ALLOWED_TOP or any(s.endswith(ALLOWED_SUFFIX) for s in p.parts):
            continue
        if p.name.startswith(".env"):
            continue
        bad.append(line)
    for b in bad:
        print("FAIL ignored by .gitignore:", b)
    print("ignored-sources:", "OK" if not bad else f"{len(bad)} ignored path(s): fix .gitignore or add them to the allow-list")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
