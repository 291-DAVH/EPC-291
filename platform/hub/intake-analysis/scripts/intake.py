#!/usr/bin/env python3
"""Customer-input pipeline: list what is waiting for analysis and store the structured result.

  python intake.py pending [--projects DIR] [--project CLIENT/CODE]
  python intake.py apply  <CLIENT/CODE | project_dir> <analysis.json> [--projects DIR]

`pending` prints JSON: per project, the intake items still `received` or `analyzing` plus the requirements
that already exist (so the analyst can merge instead of duplicating).

`apply` validates an analysis file and writes it:
  {
    "requirements": [
      {"statement": "...", "type": "funcional|no funcional|restricción|documental", "priority": "alta|media|baja",
       "discipline": "electrical|civil|hvac|fire|mechanical|instrumentation|telecom|general",
       "acceptance": ["..."], "open_questions": ["..."], "source_intake": ["INT-0001"],
       "merge_into": "REQ-003"}                      # optional: extend an existing requirement instead of creating one
    ],
    "intake_status": {"INT-0001": "structured", "INT-0002": "analyzing"}
  }
Files written: workspace/00-setup/requirements.json, the intake records' `status`, and the internal
workspace/01-input/intake/analysis_log.json (never shown to end users). Writes are atomic.
"""
import argparse
import datetime
import json
import os
import re
import sys
import tempfile
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[4]
TYPES = {"funcional", "no funcional", "restricción", "documental"}
PRIORITIES = {"alta", "media", "baja"}
DISCIPLINES = {"electrical", "civil", "hvac", "fire", "mechanical", "instrumentation", "telecom", "general"}
INTAKE_STATUS = {"structured", "analyzing"}
MAX_STATEMENT = 300


def read(p, default=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return default


def write_atomic(p, obj):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=p.parent, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, p)


def projects_root(arg):
    return Path(arg or os.environ.get("EPC_PROJECTS") or WORKSPACE / "projects")


def project_dir(root, ref):
    p = Path(ref)
    if p.is_dir() and (p / ".epc" / "project.json").exists():
        return p
    d = root / ref
    if not (d / ".epc" / "project.json").exists():
        raise SystemExit(f"project not found: {ref}")
    return d


def intake_items(pdir):
    return [read(f, {}) for f in sorted((pdir / "workspace" / "01-input" / "intake").glob("INT-*.json"))]


def cmd_pending(a):
    root = projects_root(a.projects)
    dirs = [project_dir(root, a.project)] if a.project else [pj.parent.parent for pj in sorted(root.glob("*/*/.epc/project.json")) if not pj.parent.parent.parent.name.startswith("_")]
    out = []
    for d in dirs:
        waiting = [i for i in intake_items(d) if i.get("status") in ("received", "analyzing")]
        if not waiting:
            continue
        meta = read(d / ".epc" / "project.json", {})
        out.append({"project": f"{d.parent.name}/{d.name}", "client": meta.get("client"), "locale": meta.get("locale"),
                    "disciplines": meta.get("disciplines", []), "pending": waiting,
                    "existing_requirements": read(d / "workspace" / "00-setup" / "requirements.json", [])})
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


def validate(analysis, items, existing):
    errors, ids = [], {i["id"] for i in items}
    req_ids = {r["id"] for r in existing}
    for n, r in enumerate(analysis.get("requirements", []), 1):
        tag = f"requirements[{n}]"
        st = (r.get("statement") or "").strip()
        if not st:
            errors.append(f"{tag}: statement is required")
        elif len(st) > MAX_STATEMENT:
            errors.append(f"{tag}: statement longer than {MAX_STATEMENT} characters; split it into separate requirements")
        if r.get("type") not in TYPES:
            errors.append(f"{tag}: type must be one of {sorted(TYPES)}")
        if r.get("priority") not in PRIORITIES:
            errors.append(f"{tag}: priority must be one of {sorted(PRIORITIES)}")
        if r.get("discipline") not in DISCIPLINES:
            errors.append(f"{tag}: discipline must be one of {sorted(DISCIPLINES)}")
        if not isinstance(r.get("acceptance", []), list) or not all(isinstance(x, str) and x.strip() for x in r.get("acceptance", [])):
            errors.append(f"{tag}: acceptance must be a list of non-empty strings")
        if not r.get("source_intake"):
            errors.append(f"{tag}: source_intake is required (traceability)")
        for s in r.get("source_intake", []):
            if s not in ids:
                errors.append(f"{tag}: unknown intake item {s}")
        if r.get("merge_into") and r["merge_into"] not in req_ids:
            errors.append(f"{tag}: merge_into {r['merge_into']} does not exist")
        if re.search(r"(\$|USD|ARS|u\$s)\s?\d|\d+\s?(pesos|dólares|dolares|USD|ARS)", st, re.I):
            errors.append(f"{tag}: monetary amounts are confidential and must not be stored in a requirement")
    for iid, status in analysis.get("intake_status", {}).items():
        if iid not in ids:
            errors.append(f"intake_status: unknown item {iid}")
        if status not in INTAKE_STATUS:
            errors.append(f"intake_status[{iid}]: must be one of {sorted(INTAKE_STATUS)}")
    return errors


def cmd_apply(a):
    root = projects_root(a.projects)
    d = project_dir(root, a.project)
    analysis = read(a.analysis)
    if analysis is None:
        raise SystemExit(f"cannot read analysis file: {a.analysis}")
    items = intake_items(d)
    rf = d / "workspace" / "00-setup" / "requirements.json"
    existing = read(rf, [])
    errors = validate(analysis, items, existing)
    if errors:
        print("ANALYSIS REJECTED, nothing written:", *errors, sep="\n  ")
        return 1
    nums = [int(m.group(1)) for r in existing if (m := re.match(r"REQ-(\d+)", r["id"]))]
    nxt = max(nums, default=0)
    created, merged = [], []
    for r in analysis.get("requirements", []):
        body = {"statement": r["statement"].strip(), "type": r["type"], "priority": r["priority"], "discipline": r["discipline"],
                "acceptance": r.get("acceptance", []), "open_questions": r.get("open_questions", []), "source_intake": r["source_intake"]}
        if r.get("merge_into"):
            tgt = next(x for x in existing if x["id"] == r["merge_into"])
            tgt["source_intake"] = sorted(set(tgt["source_intake"]) | set(body["source_intake"]))
            tgt["acceptance"] = tgt.get("acceptance", []) + [x for x in body["acceptance"] if x not in tgt.get("acceptance", [])]
            tgt["open_questions"] = tgt.get("open_questions", []) + [x for x in body["open_questions"] if x not in tgt.get("open_questions", [])]
            tgt["status"] = "abierto" if tgt["open_questions"] else "definido"
            merged.append(tgt["id"])
        else:
            nxt += 1
            existing.append({"id": f"REQ-{nxt:03d}", **body, "status": "abierto" if body["open_questions"] else "definido"})
            created.append(f"REQ-{nxt:03d}")
    write_atomic(rf, existing)
    by_id = {i["id"]: i for i in items}
    for iid, status in analysis.get("intake_status", {}).items():
        rec = by_id[iid]
        rec["status"] = status
        write_atomic(d / "workspace" / "01-input" / "intake" / f"{iid}.json", rec)
    log_f = d / "workspace" / "01-input" / "intake" / "analysis_log.json"
    log = read(log_f, [])
    log.append({"at": datetime.datetime.now().isoformat(timespec="seconds"), "created": created, "merged": merged,
                "intake_status": analysis.get("intake_status", {}), "notes": analysis.get("notes", "")})
    write_atomic(log_f, log)
    print(f"applied to {d.parent.name}/{d.name}: created {created or '-'}, merged {merged or '-'}, intake updated {list(analysis.get('intake_status', {})) or '-'}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pending")
    p.add_argument("--projects")
    p.add_argument("--project")
    q = sub.add_parser("apply")
    q.add_argument("project")
    q.add_argument("analysis")
    q.add_argument("--projects")
    a = ap.parse_args(argv)
    return cmd_pending(a) if a.cmd == "pending" else cmd_apply(a)


if __name__ == "__main__":
    sys.exit(main())
