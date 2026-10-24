#!/usr/bin/env python3
"""EPC build tool (stdlib only).

  python tools/build/epc_build.py registry            validate plugins + skills, write claude/plugins/registry.json
  python tools/build/epc_build.py package <id|all>    build dist/<id>-<version>.plugin (official layout, zipped)
  python tools/build/epc_build.py marketplace         build dist/marketplace/ (plugins in the official layout + marketplace.json)
  python tools/build/epc_build.py lock <project_dir>  write <project>/.epc/plugins.lock from the registry

Sources live in claude/: plugins/<id>/ (our plugin.json: packaging only), skills/<id>/, agents/<name>.md, marketplace/.
The code lives in engine/<area>/src/<package>; a plugin lists the areas it wraps in `engine`.
A built plugin follows Claude Code's layout: .claude-plugin/plugin.json, skills/, agents/, plus lib/ with the engine packages it needs.

Rules enforced by `registry`:
  - every plugin.json has id, version (semver), kind and skills;
  - every skill a plugin lists exists in claude/skills/ (or inside the plugin: plugin copy governs);
  - every agent a plugin lists exists in claude/agents/;
  - every engine area a plugin lists exists in engine/<area>/src;
  - every `requires` entry resolves to a plugin whose version satisfies the range;
  - a skill has exactly one owner plugin.
"""
import argparse
import hashlib
import json
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CLAUDE = REPO / "claude"
HUB, SKILLS, AGENTS, MARKET = CLAUDE / "plugins", CLAUDE / "skills", CLAUDE / "agents", CLAUDE / "marketplace"
ENGINE = REPO / "engine"
DIST = REPO / "dist"
SKIP_DIRS = {"__pycache__", ".git", "tests", "dist", "node_modules"}
SKIP_SUFFIX = {".pyc", ".pdf"}
INSTALL_REPO = "291-DAVH/EPC-291"                   # GitHub repository that will host the marketplace
SKIP_FILES = {"plugin.json", "registry.json"}      # our manifest is replaced by .claude-plugin/plugin.json


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
    for f in sorted(p for p in d.rglob("*") if p.is_file() and not (set(p.parts) & {"__pycache__", ".git", "build", "dist"}) and p.suffix != ".pyc"
                    and not any(x.endswith(".egg-info") for x in p.parts)):          # only sources: generated folders differ per machine and would change the hash
        h.update(str(f.relative_to(d)).replace("\\", "/").encode())
        h.update(f.read_bytes())
    return h.hexdigest()[:16]


def plugin_hash(m):
    """Hash of the plugin folder plus the engine sources it wraps (what a lock must pin)."""
    h = hashlib.sha256(tree_hash(m["_dir"]).encode())
    for a in m.get("engine", []):
        if (ENGINE / a / "src").is_dir():
            h.update(tree_hash(ENGINE / a / "src").encode())
    for rel in m.get("engine_data", []):                # a corrected norm value changes the plugin's hash: projects locked to the old one are warned
        if (ENGINE / rel).is_file():
            h.update(rel.encode() + (ENGINE / rel).read_bytes())
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
        for a in m.get("engine", []):
            if not (ENGINE / a / "src").is_dir():
                errors.append(f"{pid}: engine area '{a}' not found in engine/")
        for rel in m.get("engine_data", []):
            if not (ENGINE / rel).is_file():
                errors.append(f"{pid}: engine data '{rel}' not found in engine/")
        for ag in m.get("agents", []):
            if not (AGENTS / f"{ag}.md").exists():
                errors.append(f"{pid}: agent '{ag}' not found in claude/agents")
        for dep, rng in m.get("requires", {}).items():
            if dep not in plugins:
                errors.append(f"{pid}: requires unknown plugin '{dep}'")
            elif not satisfies(plugins[dep]["version"], rng):
                errors.append(f"{pid}: requires {dep} {rng} but the repository has {plugins[dep]['version']}")
    return errors, owners


def cmd_registry(check=False):
    plugins = load_plugins()
    errors, owners = validate(plugins)
    reg = {"schema_version": "1.0", "plugins": {}, "skills": {k: {"owner": v} for k, v in sorted(owners.items())}}
    for pid, m in plugins.items():
        reg["plugins"][pid] = {"version": m["version"], "kind": m["kind"], "status": m.get("status", "active"),
                               "requires": m.get("requires", {}), "skills": [s["id"] for s in m.get("skills", [])],
                               "engine": m.get("engine", []), "hash": plugin_hash(m)}
    text = json.dumps(reg, indent=2, ensure_ascii=False) + "\n"
    target = HUB / "registry.json"
    if check:                                           # the gate and the hook verify; they never rewrite the versioned file
        if target.read_bytes().decode("utf-8").replace("\r\n", "\n") != text:
            errors.append("registry.json is out of date: run `python tools/build/epc_build.py registry` and commit it")
    else:
        target.write_text(text, encoding="utf-8", newline="\n")
    for e in errors:
        print("ERROR:", e)
    print(f"registry.json: {len(plugins)} plugins, {len(owners)} owned skills, {len(errors)} error(s)")
    return 1 if errors else 0


def assemble(m, dest: Path):
    """Write one plugin in Claude Code's official layout into `dest` (must not exist)."""
    dest.mkdir(parents=True)
    manifest = {"name": m["id"], "version": m["version"], "description": m.get("description", ""),
                "author": {"name": "EPC-291"}, "keywords": [m["kind"]] + m.get("discipline", [])}
    deps = sorted(m.get("requires", {}))
    if deps:
        manifest["dependencies"] = deps
    (dest / ".claude-plugin").mkdir()
    (dest / ".claude-plugin" / "plugin.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    for f in sorted(m["_dir"].rglob("*")):
        rel = f.relative_to(m["_dir"])
        if f.is_dir() or (set(rel.parts) & SKIP_DIRS) or f.suffix in SKIP_SUFFIX or (len(rel.parts) == 1 and f.name in SKIP_FILES):
            continue
        (dest / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dest / rel)
    readme = dest / "README.md"
    body = readme.read_text(encoding="utf-8") if readme.exists() else f"# {m['id']}\n\n{m.get('description', '')}\n"
    install = f"\n\n## Install\n\n```\n/plugin install {m['id']} --marketplace {INSTALL_REPO}\n```\n"
    readme.write_text(body.rstrip() + install, encoding="utf-8", newline="\n")
    for s in m.get("skills", []):
        inside = m["_dir"] / "skills" / s["id"]
        src = inside if inside.exists() else SKILLS / s["id"]          # plugin copy governs
        for f in sorted(src.rglob("*")):
            if f.is_file() and "__pycache__" not in f.parts:
                t = dest / "skills" / s["id"] / f.relative_to(src)
                t.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, t)
    for a in m.get("engine", []):                       # engine packages travel with the plugin under lib/
        for f in sorted((ENGINE / a / "src").rglob("*")):
            rel = f.relative_to(ENGINE / a / "src")
            if f.is_file() and not (set(rel.parts) & {"__pycache__"}) and f.suffix not in {".pyc", ".pdf"} and ".egg-info" not in str(rel):
                (dest / "lib" / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dest / "lib" / rel)
    for rel in m.get("engine_data", []):                # data the engine reads (e.g. the design-criteria catalog): generated from its single source in engine/
        (dest / "lib" / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ENGINE / rel, dest / "lib" / rel)
    for ag in m.get("agents", []):
        (dest / "agents").mkdir(exist_ok=True)
        shutil.copy2(AGENTS / f"{ag}.md", dest / "agents" / f"{ag}.md")


def _plugins_or_fail():
    plugins = load_plugins()
    errors, _ = validate(plugins)
    if errors:
        print("Refusing to build, fix first:", *errors, sep="\n  ")
        return None
    return plugins


def cmd_package(target):
    plugins = _plugins_or_fail()
    if plugins is None:
        return 1
    ids = list(plugins) if target == "all" else [target]
    DIST.mkdir(exist_ok=True)
    for pid in ids:
        m = plugins[pid]
        out = DIST / f"{pid}-{m['version']}.plugin"
        with tempfile.TemporaryDirectory() as t:
            stage = Path(t) / pid
            assemble(m, stage)
            with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
                for f in sorted(stage.rglob("*")):
                    if f.is_file():
                        z.write(f, str(f.relative_to(stage)).replace("\\", "/"))
        print(f"built {out.relative_to(REPO)} ({out.stat().st_size // 1024} KB)")
    return 0


def cmd_marketplace():
    plugins = _plugins_or_fail()
    if plugins is None:
        return 1
    root = DIST / "marketplace"
    if root.exists():
        shutil.rmtree(root)                              # build output only
    meta = json.loads((MARKET / "marketplace.template.json").read_text(encoding="utf-8"))
    entries = []
    for pid, m in plugins.items():
        if m.get("status") == "pending":
            continue
        assemble(m, root / "plugins" / pid)
        entries.append({"name": pid, "source": f"./plugins/{pid}", "description": m.get("description", "")[:300], "version": m["version"]})
    meta["plugins"] = entries
    (root / ".claude-plugin").mkdir(parents=True, exist_ok=True)
    (root / ".claude-plugin" / "marketplace.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"marketplace: {len(entries)} plugins in {root.relative_to(REPO)} (pending plugins skipped)")
    return 0


def cmd_lock(project):
    reg = json.loads((HUB / "registry.json").read_text(encoding="utf-8"))
    p = Path(project) / ".epc"
    p.mkdir(parents=True, exist_ok=True)
    lock = {"schema_version": "1.0", "plugins": {k: {"version": v["version"], "hash": v["hash"]} for k, v in reg["plugins"].items() if v["status"] != "pending"}}
    (p / "plugins.lock").write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {p / 'plugins.lock'}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("registry").add_argument("--check", action="store_true", help="fail if registry.json differs from what the sources produce")
    sp = sub.add_parser("package")
    sp.add_argument("target")
    sub.add_parser("marketplace")
    sl = sub.add_parser("lock")
    sl.add_argument("project")
    a = ap.parse_args()
    sys.exit({"registry": lambda: cmd_registry(a.check), "package": lambda: cmd_package(a.target), "marketplace": cmd_marketplace, "lock": lambda: cmd_lock(a.project)}[a.cmd]())
