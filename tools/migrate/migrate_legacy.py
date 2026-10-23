#!/usr/bin/env python3
"""One-off migration: legacy folders -> epc-workspace/{platform,dev-knowledge,projects}.

Phase 1 (this script, `python migrate_legacy.py copy`):
  - MOVES the unique master PDFs to dev-knowledge/ (never versioned).
  - COPIES plugins, skills, workflow rules, agents, templates into platform/ and projects/.
  - Originals are not deleted. `python migrate_legacy.py archive` (phase 2) relocates the
    legacy folders into epc-workspace/_legacy/ once the new tree has been verified.
Every action is logged to platform/docs/MIGRATION_LOG.md.
"""
import json
import re
import shutil
import sys
from pathlib import Path

P = Path(r"E:\plugins\prueba")
W = P / "epc-workspace"
PF, DK, PR, LG = W / "platform", W / "dev-knowledge", W / "projects", W / "_legacy"
T = P / "00-Template-Claude" / ".claude"
LOG = []

IGNORE = shutil.ignore_patterns("__pycache__", ".git", "*.pdf", "*.plugin", ".gitkeep", "*.pyc", "Thumbs.db")
TRAINING = ("knowledge", "learning", "memory", "cache", "outputs")


def log(kind, src, dst=""):
    LOG.append(f"| {kind} | `{str(src).replace(str(P), '')}` | `{str(dst).replace(str(W), '')}` |")


def cp(src, dst, ignore=IGNORE):
    src, dst = Path(src), Path(dst)
    if not src.exists():
        log("MISSING", src)
        return
    if src.is_dir():
        shutil.copytree(src, dst, ignore=ignore, dirs_exist_ok=True)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    log("copy", src, dst)


def mv(src, dst):
    src, dst = Path(src), Path(dst)
    if not src.exists():
        log("MISSING", src)
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    log("MOVE", src, dst)


def cpglob(srcdir, patterns, dst):
    for pat in patterns:
        for f in Path(srcdir).glob(pat):
            if f.is_file():
                cp(f, Path(dst) / f.name)


def std_json(dirpath, sid, country, body, domain, files, lic="copyrighted-internal-study-only"):
    meta = {"id": sid, "country": country, "body": body, "title": "", "edition": "", "language": "es",
            "domain": domain, "license": lic, "status": "draft",
            "source_files": [f"source/{f}" for f in files], "notes": "Imported by migrate_legacy.py; fill title/edition."}
    (dirpath).mkdir(parents=True, exist_ok=True)
    (dirpath / "standard.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def phase_pdfs():
    # AEA standards (master copies)
    src = P / "elec-calc-generator" / "assets"
    for f in sorted(src.glob("*.pdf")):
        sid = f.stem.replace("_", "-")
        d = DK / "standards" / "AR" / sid
        mv(f, d / "source" / f.name)
        std_json(d, sid, "AR", "AEA", "electrical", [f.name])
    # library/calculations/assets: only the non-AEA unique files
    lib = P / "elec-calc-generator" / "library" / "calculations" / "assets"
    for f in sorted(lib.glob("CIMET_*.pdf")):
        mv(f, DK / "third-party-reports" / "CIMET-OPTEL" / f.name)
    for f in sorted(lib.glob("NFPA_*.pdf")):
        sid = f.stem.replace("_", "-")
        d = DK / "standards" / "US" / sid
        mv(f, d / "source" / f.name)
        std_json(d, sid, "US", "NFPA", "electrical", [f.name])
    # PM2 guides
    for f in sorted((T / "library" / "plugins" / "management" / "assets").glob("*.pdf")):
        mv(f, DK / "standards" / "INTL" / "PM2" / "source" / f.name)
    std_json(DK / "standards" / "INTL" / "PM2", "PM2", "INTL", "EC", "management", [], lic="CC-BY-4.0 (kept out of git by project rule)")
    # Ford specs
    for f in sorted((T / "skills" / "generar-pliego" / "knowledge" / "pdf").glob("*.pdf")):
        mv(f, DK / "reference-specs" / "FORD" / f.name)
    # SLD training drawings
    for f in sorted((P / "sld-generator" / "assets").glob("*.pdf")):
        mv(f, DK / "training-material" / "drawings" / f.name)
    # IEC 60617
    f = P / "291_E_IEC60617_Symbols_Generator" / "assets" / "IEC_60617_Simbologia.pdf"
    mv(f, DK / "standards" / "INTL" / "IEC-60617" / "source" / f.name)
    std_json(DK / "standards" / "INTL" / "IEC-60617", "IEC-60617", "INTL", "IEC", "electrical", [f.name])


def phase_plugins():
    H = PF / "hub"
    # aea-calc
    s = P / "elec-calc-generator"
    pl = s / "plugin" / "elec-calc-generator"
    cp(pl / "scripts", H / "aea-calc" / "scripts")
    cp(pl / "docs", H / "aea-calc" / "docs")
    cp(s / "src", H / "aea-calc" / "examples")
    cp(s / "assets" / "logo.png", H / "aea-calc" / "assets" / "logo.png")
    for n in ("CHANGELOG.md", "CONTRIBUTING.md", "LICENSE"):
        cp(s / n, H / "aea-calc" / n)
    # iec-symbols
    s = P / "291_E_IEC60617_Symbols_Generator"
    cp(s / "src", H / "iec-symbols" / "symbols")
    cp(s / "tools", H / "iec-symbols" / "tools")
    cp(s / "assets", H / "iec-symbols" / "assets")
    cp(s / "feedback", H / "iec-symbols" / "feedback")
    for n in ("CHANGELOG.md", "CONTRIBUTING.md", "LICENSE"):
        cp(s / n, H / "iec-symbols" / n)
    # iram-titleblock
    s = P / "291_G_IRAM_Custom_TitleBlocks_Generator"
    pl = s / "plugin" / "iram-titleblock-plugin"
    cp(pl / "scripts", H / "iram-titleblock" / "scripts")
    cp(pl / "templates", H / "iram-titleblock" / "templates")
    cp(s / "assets", H / "iram-titleblock" / "assets")
    cp(s / "test", H / "iram-titleblock" / "tests" / "fixtures")
    for n in ("CHANGELOG.md", "CONTRIBUTING.md", "LICENSE"):
        cp(s / n, H / "iram-titleblock" / n)
    cp(T / "library" / "plugins" / "laminas-iram" / "lamina_iram.py", H / "iram-titleblock" / "scripts" / "lamina_iram.py")
    cp(T / "library" / "plugins" / "laminas-iram" / "templates", H / "iram-titleblock" / "templates" / "iram-sheet")
    # sld
    s = P / "sld-generator"
    cp(s / "src", H / "sld" / "scripts")
    cp(s / "test", H / "sld" / "tests" / "fixtures" / "a1")
    cp(s / "test_a3", H / "sld" / "tests" / "fixtures" / "a3")
    # examples: inputs and title-block assets move out of scripts/
    ex = H / "sld" / "examples"
    for n in ("input_for_sld_V1.xlsx",):
        mv(H / "sld" / "scripts" / n, ex / n)
    for n in ("input-titleblocks.xlsx", "client-logo-FORD.svg", "provider-logo-EnergySapiens.svg"):
        mv(H / "sld" / "scripts" / n, ex / "titleblock" / n)
    # mld
    s = P / "mld-generator"
    cp(s / "plugin" / "mld-generator" / "templates", H / "mld" / "templates")
    cp(s / "assets", H / "mld" / "data")
    cp(T / "library" / "core" / "sld_to_mld_input_template.xlsx", H / "mld" / "templates" / "sld_to_mld_input_template.xlsx")
    # pm2-docs
    c = T / "library" / "plugins" / "calculations"
    cpglob(c, ["ccpm*", "*canvas*", "charter_exporter*", "test_ccpm*", "test_charter*", "test_canvas*", "example_ccpm*"], H / "pm2-docs" / "scripts")
    # doc-quality
    cpglob(c, ["document_verifier*", "specification_verifier*", "input_converter*", "test_document_verifier*",
               "test_specification_verifier*", "test_input_converter*"], H / "doc-quality" / "scripts")
    # equipment-catalog
    cp(T / "library" / "plugins" / "equipment", H / "equipment-catalog" / "data")
    # spec-writer / procurement have no code of their own yet
    for n in ("spec-writer", "procurement"):
        (H / n).mkdir(parents=True, exist_ok=True)


SKILLS = [
    # (source dir, new id, owner plugin, legacy id)
    (P / "elec-calc-generator/plugin/elec-calc-generator/skills/feeder-sizing", "size-feeder", "aea-calc", "feeder-sizing"),
    (P / "elec-calc-generator/plugin/elec-calc-generator/skills/electrical-dimensioning", "dimension-installation", "aea-calc", "electrical-dimensioning"),
    (P / "elec-calc-generator/plugin/elec-calc-generator/skills/calculation-memo", "write-calculation-memo", "aea-calc", "calculation-memo"),
    (P / "elec-calc-generator/plugin/elec-calc-generator/skills/memo-summary", "write-memo-summary", "aea-calc", "memo-summary"),
    (P / "sld-generator/plugin/sld-generator/skills/sld-generator", "generate-sld", "sld", "sld-generator"),
    (P / "mld-generator/plugin/mld-generator/skills/convert-sld-to-mld", "convert-sld-to-mld", "mld", "convert-sld-to-mld"),
    (P / "291_G_IRAM_Custom_TitleBlocks_Generator/plugin/iram-titleblock-plugin/skills/iram-titleblock-custom-generator", "generate-titleblock-sheet", "iram-titleblock", "iram-titleblock-custom-generator"),
    (T / "skills/generate-laminas-iram", "generate-iram-sheet", "iram-titleblock", "generate-laminas-iram"),
    (T / "skills/generate-electrical-symbol", "generate-electrical-symbol", "iec-symbols", "generate-electrical-symbol"),
    (T / "skills/create-pm2-document", "create-management-document", "pm2-docs", "create-pm2-document"),
    (T / "skills/generar-pliego", "generate-specification", "spec-writer", "generar-pliego"),
    (T / "skills/get-cotizacion", "request-quotation", "procurement", "get-cotizacion"),
]
SUPERSEDED = ["create-electrical-line-diagram", "electrical-dimensioning (template copy)", "memoria-calculos", "sintesis-memoria"]


def phase_skills():
    registry = {}
    for src, sid, owner, legacy in SKILLS:
        dst = PF / "skills" / sid
        # skill body: everything except training data
        dst.mkdir(parents=True, exist_ok=True)
        for item in src.iterdir():
            if item.name in TRAINING or item.name == ".gitkeep":
                continue
            if item.is_dir():
                if any(item.rglob("*")) and not all(x.name == ".gitkeep" for x in item.rglob("*") if x.is_file()):
                    cp(item, dst / item.name)
            else:
                cp(item, dst / item.name)
        # rename inside SKILL.md / skill.json
        md = dst / "SKILL.md"
        if md.exists():
            t = md.read_text(encoding="utf-8")
            t2 = re.sub(r'(?m)^name:\s*"?[^"\n]+"?\s*$', f'name: "{sid}"', t, count=1)
            md.write_text(t2, encoding="utf-8")
        sj = dst / "skill.json"
        if sj.exists():
            j = json.loads(sj.read_text(encoding="utf-8"))
            j["name"] = sid
            sj.write_text(json.dumps(j, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        # training data -> dev-knowledge
        for tr in TRAINING:
            d = src / tr
            if d.exists() and any(f for f in d.rglob("*") if f.is_file() and f.name != ".gitkeep"):
                cp(d, DK / "skill-knowledge" / sid / tr)
        registry[sid] = {"owner": owner, "legacy_id": legacy, "status": "active"}
    for s in SUPERSEDED:
        registry[s] = {"owner": None, "status": "superseded", "note": "kept only in _legacy"}
    (PF / "skills" / "_registry.json").write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    log("write", "skills registry", PF / "skills" / "_registry.json")


def phase_template():
    # workflow engine seed + rules
    wf = PF / "core" / "workflow"
    for n in ("framework.md", "m1-glossary-and-phases.md", "m2-startup-questionnaire.md", "m3-interview-copy-baseline.md",
              "m5-packages-development.md", "m6-states-quality.md", "m7-examples.md", "m9-engineering-checklist.md"):
        cp(T / "rules" / n, wf / "rules" / n)
    cp(T / "hooks", wf / "scripts")
    cp(T / "commands", wf / "commands")
    # pm2 methodology
    pm = PF / "methodologies" / "pm2"
    for n in ("m8-management-documents.md", "m10-programme-management.md", "management-templates.md"):
        cp(T / "rules" / n, pm / "rules" / n)
    mg = T / "library" / "plugins" / "management"
    for f in mg.glob("*.md"):
        cp(f, pm / "templates" / f.name)
    cp(mg / "plugin.json", pm / "legacy-plugin.json")
    # agents, docs, tools
    cp(T / "agents", PF / "agents")
    cp(T / "docs", PF / "docs" / "framework-legacy")
    cp(T / "schemas", PF / "docs" / "framework-legacy" / "schemas")
    for n in ("README.md", "CHANGELOG.md", "CLAUDE.md"):
        cp(P / "00-Template-Claude" / n, PF / "docs" / "framework-legacy" / f"template-{n}")
    for n in ("skill_learn.py", "preview.py", "reconstruir_indices.py"):
        cp(T / "library" / "core" / n, PF / "tools" / "dev" / n)
    # standards index (legacy notes)
    st = T / "library" / "plugins" / "standards"
    cp(st / "standards-index.md", PF / "jurisdictions" / "AR" / "_legacy" / "standards-index.md")
    cp(st / "template-extract.md", PF / "jurisdictions" / "AR" / "_legacy" / "template-extract.md")
    # project template
    ws = PR / "_template" / "workspace"
    pd = T / "library" / "project-data"
    for f in pd.glob("*.md"):
        cp(f, ws / "00-setup" / f.name)
    cp(pd / "management", ws / "05-management")
    root = P / "00-Template-Claude"
    cp(root / "01-input" / "02-requirements" / "input_for_sld.xlsx", ws / "01-input" / "requirements" / "input_for_sld.xlsx")
    cp(root / "03-review" / "review-sheets" / "review-sheet.md", ws / "03-review" / "review-sheet.md")
    cp(root / "04-audit" / "project-audit.md", ws / "04-audit" / "project-audit.md")
    for n in ("audit-register.md", "project-status.md", "README.md"):
        cp(root / "90-management" / n, ws / "05-management" / n)
    cp(root / "90-management" / "reports", ws / "05-management" / "reports")
    cp(root / "pyproject.toml", PF / "docs" / "framework-legacy" / "template-pyproject.toml")
    # backups -> dev-knowledge notes
    cp(root / ".project" / "SEAL.json", DK / "notes" / "template-backup" / "SEAL.json")
    for f in (root / ".project").glob("*.tgz"):
        mv(f, DK / "notes" / "template-backup" / f.name)
    # logos used as branding samples
    flag = P / "image-a-flag-svg"
    if flag.exists():
        cp(flag, DK / "training-material" / "branding")


def write_log():
    d = PF / "docs" / "MIGRATION_LOG.md"
    d.write_text("# Migration log\n\n| action | source | destination |\n|---|---|---|\n" + "\n".join(LOG) + "\n", encoding="utf-8")


def phase_archive():
    LG.mkdir(exist_ok=True)
    for n in ("00-Template-Claude", "291_E_IEC60617_Symbols_Generator", "291_G_IRAM_Custom_TitleBlocks_Generator",
              "elec-calc-generator", "mld-generator", "sld-generator", "image-a-flag-svg"):
        mv(P / n, LG / n)
    f = P / "PLAN_FRAMEWORK_EPC.md"
    if f.exists():
        mv(f, PF / "docs" / "plan" / "PLAN_FRAMEWORK_EPC.md")
    d = PF / "docs" / "MIGRATION_LOG.md"
    old = d.read_text(encoding="utf-8") if d.exists() else ""
    d.write_text(old + "\n## Archive phase\n\n| action | source | destination |\n|---|---|---|\n" + "\n".join(LOG) + "\n", encoding="utf-8")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "copy":
        phase_pdfs()
        phase_plugins()
        phase_skills()
        phase_template()
        write_log()
        print(f"copy phase done: {len(LOG)} actions")
    elif mode == "archive":
        phase_archive()
        print(f"archive phase done: {len(LOG)} actions")
    else:
        print("usage: migrate_legacy.py copy|archive")
