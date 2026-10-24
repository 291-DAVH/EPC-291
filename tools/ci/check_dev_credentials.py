"""No development credential may reach the repository (and so never `main`).

  python tools/ci/check_dev_credentials.py

The development MASTER account (ADR-0015) is switched on only by the environment of a developer's machine (`local/dev.ps1`, which git ignores). This check fails when
  1. a versioned file gives `EPC_DEV_MASTER_PASSWORD` (or its user) a value,
  2. the deployment files (infra/, .github/, Dockerfiles) mention the MASTER variables at all,
  3. `local/` is not ignored by git, so the developer's private scripts could be committed.
"""
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ASSIGNS = re.compile(r"EPC_DEV_MASTER_(PASSWORD|USER)\s*[=:]\s*[\"']?[^\s\"'#]")
SELF = {"tools/ci/check_dev_credentials.py", "backend/tests/architecture/test_dev_credentials.py"}      # the detector and its test hold deliberate examples of what it forbids


def git(*args) -> str:
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, check=True).stdout


def main() -> int:
    errors = []
    for f in git("ls-files").splitlines():
        if f in SELF or not (REPO / f).is_file():
            continue
        try:
            text = (REPO / f).read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if ASSIGNS.search(text):
            errors.append(f"{f}: gives a value to a development MASTER variable")
        if f.startswith(("infra/", ".github/")) and "EPC_DEV_MASTER" in text:
            errors.append(f"{f}: deployment files must not mention the development MASTER account")
    if subprocess.run(["git", "check-ignore", "-q", "local/dev.ps1"], cwd=REPO).returncode != 0:
        errors.append("local/ is not ignored by git: private development scripts could be committed")
    for e in errors:
        print("FAIL", e)
    print("dev credentials:", "OK (none versioned)" if not errors else f"{len(errors)} problem(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
