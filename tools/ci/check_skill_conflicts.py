#!/usr/bin/env python3
"""Detect skills defined twice (central skills/ and inside a plugin) and warn.

Rule: when the same skill exists in claude/skills/ and in a plugin
(plugins/<plugin>/skills/<id>/), the PLUGIN copy governs. That is a warning in
development and a blocking error for production builds, so every duplicate
gets resolved before release.

Also reports: skills inside two different plugins, skills not listed by any
plugin (orphans), and plugin.json entries whose skill cannot be found.

Usage:
  python tools/ci/check_skill_conflicts.py [--root CLAUDE_DIR] [--env dev|production] [--json]
Exit code: 0 clean (or only warnings in dev), 1 blocking problems.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

IGNORED = {"__pycache__", ".git", ".gitkeep"}


def tree_hash(folder: Path) -> str:
    h = hashlib.sha256()
    for f in sorted(p for p in folder.rglob("*") if p.is_file() and not (set(p.parts) & IGNORED)):
        h.update(str(f.relative_to(folder)).replace("\\", "/").encode())
        h.update(f.read_bytes())
    return h.hexdigest()


def skill_dirs(base: Path):
    if not base.is_dir():
        return {}
    return {d.name: d for d in sorted(base.iterdir()) if d.is_dir() and (d / "SKILL.md").exists()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[2] / "claude"), help="folder holding skills/ and plugins/")
    ap.add_argument("--env", choices=["dev", "production"], default="dev")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    root = Path(a.root)
    central = skill_dirs(root / "skills")
    plugins = {}
    for pdir in sorted((root / "plugins").glob("*/")):
        if not pdir.is_dir():
            continue
        manifest = {}
        mf = pdir / "plugin.json"
        if mf.exists():
            manifest = json.loads(mf.read_text(encoding="utf-8"))
        plugins[pdir.name] = {"dir": pdir, "skills": skill_dirs(pdir / "skills"), "manifest": manifest}

    findings = []

    def add(level, code, msg, **extra):
        findings.append({"level": level, "code": code, "message": msg, **extra})

    severity_dup = "ERROR" if a.env == "production" else "WARNING"

    # 1) central vs plugin duplicates -> plugin governs
    for sid, cdir in central.items():
        for pname, p in plugins.items():
            if sid in p["skills"]:
                same = tree_hash(cdir) == tree_hash(p["skills"][sid])
                add(severity_dup, "DUPLICATE_SKILL",
                    f"Skill '{sid}' exists in skills/ and in plugin '{pname}'. "
                    f"The plugin copy GOVERNS. Content is {'identical' if same else 'DIFFERENT'}. "
                    f"Resolve before production: keep one location.",
                    skill=sid, plugin=pname, identical=same, governs=f"plugins/{pname}/skills/{sid}")

    # 2) same skill in two plugins
    seen = {}
    for pname, p in plugins.items():
        for sid in p["skills"]:
            seen.setdefault(sid, []).append(pname)
    for sid, owners in seen.items():
        if len(owners) > 1:
            add("ERROR", "MULTIPLE_OWNERS", f"Skill '{sid}' is inside several plugins: {', '.join(owners)}. A skill has one owner.",
                skill=sid, plugins=owners)

    # 3) orphans and missing references
    listed = set()
    for pname, p in plugins.items():
        for s in p["manifest"].get("skills", []):
            listed.add(s["id"])
            if s["id"] not in central and s["id"] not in p["skills"]:
                add("ERROR", "MISSING_SKILL", f"Plugin '{pname}' lists skill '{s['id']}' but it was not found.",
                    skill=s["id"], plugin=pname)
    for sid in central:
        if sid not in listed and not any(sid in p["skills"] for p in plugins.values()):
            add("WARNING", "ORPHAN_SKILL", f"Skill '{sid}' is not listed by any plugin: inactive.", skill=sid)

    if a.json:
        print(json.dumps(findings, indent=2, ensure_ascii=False))
    else:
        if not findings:
            print("OK: no skill conflicts.")
        for f in findings:
            print(f"[{f['level']}] {f['code']}: {f['message']}")
        errs = sum(1 for f in findings if f["level"] == "ERROR")
        warns = sum(1 for f in findings if f["level"] == "WARNING")
        print(f"\nenv={a.env}: {errs} error(s), {warns} warning(s)")
    return 1 if any(f["level"] == "ERROR" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
