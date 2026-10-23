#!/usr/bin/env python3
"""Validate a rules.json against schemas/rules.schema.json and the copyright/quality rules.

  python validate_rules.py <rules.json> [--standard-dir DIR] [--json]

Checks
  ERROR  schema violations, duplicate rule ids, unknown table_ref, table rows not matching columns,
         a summary sharing 12+ consecutive words with the extracted source text (verbatim copy),
         invalid check operator.
  WARN   clause number not found anywhere in the extracted text (only when a text layer exists),
         rule without check or params, derived check not yet confirmed, evidence_ref missing in evidence.json.
Exit code 1 when there is any ERROR.
"""
import argparse
import re
import sys
from pathlib import Path

from common import SCHEMAS, SHINGLE, norm_words, read_json, shingles, source_text_words

CLAUSE_TOKEN = re.compile(r"\d{1,3}(?:\.\d+)+")
OPS = {"==", "!=", "<", "<=", ">", ">=", "in", "not_in"}


def validate(path, standard_dir=None):
    errs, warns = [], []
    doc = read_json(path)
    schema = read_json(SCHEMAS / "rules.schema.json")
    try:
        import jsonschema
        for e in sorted(jsonschema.Draft202012Validator(schema).iter_errors(doc), key=lambda e: list(e.path)):
            errs.append(f"schema: {'/'.join(str(p) for p in e.path)}: {e.message[:160]}")
    except ImportError:
        for k in schema["required"]:
            if k not in doc:
                errs.append(f"schema: missing '{k}' (jsonschema not installed: minimal check only)")
    rules = doc.get("rules", [])
    ids, tables = set(), {t["id"]: t for t in doc.get("tables", [])}
    for t in doc.get("tables", []):
        for i, row in enumerate(t.get("rows", [])):
            if len(row) != len(t["columns"]):
                errs.append(f"table {t['id']} row {i}: {len(row)} cells for {len(t['columns'])} columns")
    clauses = None
    shing = None
    evidence = {}
    if standard_dir:
        sdir = Path(standard_dir)
        for pf in sdir.glob("extracted/*/pages/p*.txt"):
            clauses = (clauses or set()) | set(CLAUSE_TOKEN.findall(pf.read_text(encoding="utf-8")))
        words = source_text_words(sdir)
        shing = shingles(words) if words else None
        ev = sdir / "analysis" / "evidence.json"
        evidence = read_json(ev) if ev.exists() else {}
    for r in rules:
        rid = r.get("id", "?")
        if rid in ids:
            errs.append(f"{rid}: duplicate id")
        ids.add(rid)
        chk = r.get("check")
        if chk:
            if chk.get("op") not in OPS:
                errs.append(f"{rid}: bad check op {chk.get('op')!r}")
            if chk.get("derived"):
                warns.append(f"{rid}: derived check (from parameter name) needs human confirmation")
        elif not r.get("params") and not r.get("table_ref"):
            warns.append(f"{rid}: no check, params or table_ref (informative rule only)")
        if r.get("table_ref") and r["table_ref"] not in tables:
            errs.append(f"{rid}: unknown table_ref {r['table_ref']!r}")
        if clauses is not None and r.get("clause") and not r.get("part"):
            tokens = CLAUSE_TOKEN.findall(r["clause"])
            if tokens and not any(t in clauses for t in tokens):
                warns.append(f"{rid}: clause {r['clause']} not found in the extracted text")
        if shing:
            for loc, text in (r.get("summary") or {}).items():
                w = norm_words(text)
                if len(w) >= SHINGLE and shingles(w) & shing:
                    errs.append(f"{rid}: summary[{loc}] copies {SHINGLE}+ consecutive words from the source (verbatim)")
        if r.get("evidence_ref") and evidence and r["evidence_ref"] not in evidence:
            warns.append(f"{rid}: evidence_ref {r['evidence_ref']!r} not in analysis/evidence.json")
    return doc, errs, warns


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rules")
    ap.add_argument("--standard-dir")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    sdir = a.standard_dir or (Path(a.rules).resolve().parent.parent if Path(a.rules).resolve().parent.name == "draft" else None)
    doc, errs, warns = validate(a.rules, sdir)
    if a.json:
        import json
        print(json.dumps({"errors": errs, "warnings": warns}, ensure_ascii=False, indent=2))
    else:
        for e in errs:
            print("ERROR:", e)
        for w in warns[:25]:
            print("WARN: ", w)
        if len(warns) > 25:
            print(f"WARN:  ... {len(warns) - 25} more warnings")
        print(f"{doc['standard']['id']}: {len(doc.get('rules', []))} rules, {len(doc.get('tables', []))} tables, "
              f"{len(errs)} error(s), {len(warns)} warning(s), status={doc.get('source_status')}")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
