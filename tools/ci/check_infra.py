"""Static checks of infra/ and .github/ (Docker is not required): YAML parses, COPY sources exist,
compose references exist, the secrets file is never committed, images exclude local/.

  python tools/ci/check_infra.py
"""
import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
errors: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def dockerfile_copies(path: Path):
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*COPY\s+(?:--from=\S+\s+)?(.+)", line)
        if m and "--from=" not in line:
            parts = m.group(1).split()
            yield from parts[:-1]


def main() -> int:
    for f in (REPO / "infra" / "compose" / "compose.yml", REPO / ".github" / "workflows" / "ci.yml"):
        try:
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                err(f"{f.name}: not a mapping")
        except Exception as e:                      # noqa: BLE001
            err(f"{f.name}: invalid YAML: {e}")
            data = {}
        if f.name == "compose.yml":
            for name, svc in (data.get("services") or {}).items():
                build = svc.get("build")
                if build:
                    ctx = (f.parent / build["context"]).resolve()
                    if ctx != REPO:
                        err(f"compose {name}: build context must be the repository root")
                    if not (ctx / build["dockerfile"]).exists():
                        err(f"compose {name}: missing {build['dockerfile']}")
                for dep in (svc.get("depends_on") or {}):
                    if dep not in data["services"]:
                        err(f"compose {name}: depends_on unknown service {dep}")
        if f.name == "ci.yml":
            for job, spec in (data.get("jobs") or {}).items():
                for need in ([spec.get("needs")] if isinstance(spec.get("needs"), str) else spec.get("needs") or []):
                    if need not in data["jobs"]:
                        err(f"ci job {job}: needs unknown job {need}")

    for df in (REPO / "infra" / "docker").glob("*.Dockerfile"):
        for src in dockerfile_copies(df):
            if not any(REPO.glob(src.rstrip("/"))):
                err(f"{df.name}: COPY source {src} does not exist")

    ignore = (REPO / ".dockerignore").read_text(encoding="utf-8").split()
    if "local" not in ignore:
        err(".dockerignore must exclude local/ (private material)")
    if not (REPO / "infra" / "compose" / ".env.example").exists():
        err("infra/compose/.env.example missing")
    if (REPO / ".gitignore").read_text(encoding="utf-8").find(".env") < 0:
        err(".gitignore must ignore .env files")
    for e in errors:
        print("FAIL", e)
    print("infra:", "OK" if not errors else f"{len(errors)} problem(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
