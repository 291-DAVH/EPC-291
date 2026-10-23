#!/usr/bin/env python3
"""EPC platform build tool (stdlib only).

  python tools/build/epc_build.py registry            validate hub + skills, write hub/registry.json
  python tools/build/epc_build.py package <id|all>    build dist/<id>-<version>.plugin for Claude Code
  python tools/build/epc_build.py lock <project_dir>  write <project>/.epc/plugins.lock from the registry

Rules enforced by `registry`:
  - every plugin.json has id, version (semver), kind and skills;
  - every skill a plugin lists exists in platform/skills/ (or inside the plugin: plugin copy governs);
  - every `requires` entry resolves to a hub plugin whose version satisfies the range;
  - a skill has exactly one owner plugin.
Skill duplicate warnings are produced by tools/ci/check_skill_conflicts.py.
"""
import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HUB, SKILLS, DIST = ROOT / "hub", ROOT / "skills", ROOT / "dist"
SKIP_DIRS = {"__pycache__", ".git", "tests", "dist"}
SKIP_SUFFIX = {".pyc", ".pdf"}


def ver(s):
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)$", s)
    if not m:
        raise ValueError(f"bad semver: {s}")
    return tuple(int(x) for x in m.groups())


def satisfies(v, rng):
    rng = rng.strip()
    if rng in ("", "*"):
        return True
    op, base = (rng[0], rng[1:]) if rng[0] in "^~" else ("=", rng)
    b, x = ver(base), ver(v)
    if op == "=":
        return x == b
    if op == "~":
        return x >= b and x[:2] == b[:2]
    if b[0] > 0:
        return x >= b and x[0] == b[0]
    return x >= b and x[:2] == b[:2]


def load_plugins():
    out = {}
    for d in sorted(p for p in HUB.iterdir() if p.is_dir()):
        mf = d / "plugin.json"
        if mf.exists():
            m = json.loads(mf.read_text(encoding="utf-8"))
            m["_dir"] = d
            out[m["id"]] = m
    return out


def tree_hash(d):
    h = hashlib.sha256()
    for f in sorted(p for p in d.rglob("*") if p.is_file() and not (set(p.parts) & {"__pycache__", ".git"}) and p.suffix != ".pyc"):
        h.update(str(f.relative_to(d)).replace("\\", "/").encode())
        h.update(f.read_bytes())
    return h.hexdigest()[:16]


def validate(plugins):
    errors, owners = [], {}
    for pid, m in plugins.items():
        for k in ("id", "version", "kind", "skills"):
            if k not in m:
                errors.append(f"{pid}: missing '{k}'")
        try:
            ver(m["version"])
        except Exception as e:
            errors.append(f"{pid}: {e}")
        if m["id"] != m["_dir"].name:
            errors.append(f"{pid}: folder name differs from id")
        for s in m.get("skills", []):
            sid = s["id"]
            if not ((SKILLS / sid / "SKILL.md").exists() or (m["_dir"] / "skills" / sid / "SKILL.md").exists()):
                errors.append(f"{pid}: skill '{sid}' not found")
            if s.get("role") == "owner":
                if sid in owners:
                    errors.append(f"skill '{sid}' has two owners: {owners[sid]} and {pid}")
                owners[sid] = pid
        for dep, rng in m.get("requires", {}).items():
            if dep not in plugins:
                errors.append(f"{pid}: requires unknown plugin '{dep}'")
            elif not satisfies(plugins[dep]["version"], rng):
                errors.append(f"{pid}: requires {dep} {rng} but hub has {plugins[dep]['version']}")
    return errors, owners


def cmd_registry():
    plugins = load_plugins()
    errors, owners = validate(plugins)
    reg = {"schema_version": "1.0", "plugins": {}, "skills": {k: {"owner": v} for k, v in sorted(owners.items())}}
    for pid, m in plugins.items():
        reg["plugins"][pid] = {"version": m["version"], "kind": m["kind"], "status": m.get("status", "active"),
                               "requires": m.get("requires", {}), "skills": [s["id"] for s in m.get("skills", [])],
                               "hash": tree_hash(m["_dir"])}
    (HUB / "registry.json").write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for e in errors:
        print("ERROR:", e)
    print(f"registry.json: {len(plugins)} plugins, {len(owners)} owned skills, {len(errors)} error(s)")
    return 1 if errors else 0


def cmd_package(target):
    plugins = load_plugins()
    errors, _ = validate(plugins)
    if errors:
        print("Refusing to package, fix first:", *errors, sep="\n  ")
        return 1
    ids = list(plugins) if target == "all" else [target]
    DIST.mkdir(exist_ok=True)
    for pid in ids:
        m = plugins[pid]
        out = DIST / f"{pid}-{m['version']}.plugin"
        manifest = {"name": pid, "version": m["version"], "description": m.get("description", ""),
                    "author": {"name": "EPC Platform"}, "keywords": [m["kind"]] + m.get("discipline", [])}
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr(".claude-plugin/plugin.json", json.dumps(manifest, indent=2, ensure_ascii=False))
            for f in sorted(m["_dir"].rglob("*")):
                rel = f.relative_to(m["_dir"])
                if f.is_dir() or (set(rel.parts) & SKIP_DIRS) or f.suffix in SKIP_SUFFIX or f.name == "plugin.json" and len(rel.parts) == 1 and False:
                    continue
                z.write(f, str(rel).replace("\\", "/"))
            for s in m.get("skills", []):
                inside = m["_dir"] / "skills" / s["id"]
                src = inside if inside.exists() else SKILLS / s["id"]   # plugin copy governs
                for f in sorted(src.rglob("*")):
                    if f.is_file() and "__pycache__" not in f.parts:
                        z.write(f, "skills/" + s["id"] + "/" + str(f.relative_to(src)).replace("\\", "/"))
        print(f"built {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KB)")
    return 0


def cmd_lock(project):
    reg = json.loads((HUB / "registry.json").read_text(encoding="utf-8"))
    p = Path(project) / ".epc"
    p.mkdir(parents=True, exist_ok=True)
    lock = {"schema_version": "1.0", "plugins": {k: {"version": v["version"], "hash": v["hash"]} for k, v in reg["plugins"].items() if v["status"] != "pending"}}
    (p / "plugins.lock").write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {p / 'plugins.lock'}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("registry")
    sp = sub.add_parser("package"); sp.add_argument("target")
    sl = sub.add_parser("lock"); sl.add_argument("project")
    a = ap.parse_args()
    sys.exit({"registry": cmd_registry, "package": lambda: cmd_package(a.target), "lock": lambda: cmd_lock(a.project)}[a.cmd]())
