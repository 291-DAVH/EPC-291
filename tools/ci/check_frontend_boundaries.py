"""Frontend boundaries: apps depend only on @epc/ui; ui depends on no app; features do not reach into each other.

  python tools/ci/check_frontend_boundaries.py
"""
import re
import sys
from pathlib import Path

FE = Path(__file__).resolve().parents[2] / "frontend"
IMPORT = re.compile(r"""(?:from|import)\s+["']([^"']+)["']""")


def imports(f: Path):
    return IMPORT.findall(f.read_text(encoding="utf-8"))


def main() -> int:
    errors = []
    for app in ("web", "console"):
        other = "console" if app == "web" else "web"
        for f in (FE / app / "src").rglob("*.ts*"):
            rel = f.relative_to(FE / app / "src")
            for imp in imports(f):
                if imp.startswith("@epc/") and not imp.startswith("@epc/ui"):
                    errors.append(f"{app}/{rel}: imports {imp} (apps may import only @epc/ui)")
                if imp.startswith("."):
                    target = (f.parent / imp).resolve()
                    try:
                        t = target.relative_to((FE / app / "src").resolve())
                    except ValueError:
                        errors.append(f"{app}/{rel}: relative import {imp} leaves the app")
                        continue
                    if len(rel.parts) >= 2 and rel.parts[0] == "features" and len(t.parts) >= 2 and t.parts[0] == "features" and t.parts[1] != rel.parts[1]:
                        errors.append(f"{app}/{rel}: reaches into another feature ({imp})")
    for f in (FE / "packages" / "ui" / "src").rglob("*.ts*"):
        for imp in imports(f):
            if imp.startswith("@epc/") and imp != "@epc/ui" or imp.startswith(("../../web", "../../console")):
                errors.append(f"ui/{f.name}: imports {imp} (ui must not depend on apps)")
    for e in errors:
        print("FAIL", e)
    print("frontend boundaries:", "OK" if not errors else f"{len(errors)} violation(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
