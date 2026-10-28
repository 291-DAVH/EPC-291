#!/usr/bin/env python3
"""Promote a validated draft rules.json from dev-knowledge to the product: the norm engine the jurisdiction names for the domain.

  python -m epc_standards.promote_rules <standard_dir | CC/ID | ID> [--mark-verified "Full Name"] [--engine DIR] [--pack NAME]

Gate (all must hold):
  1. draft/rules.json passes validate_rules.py with no ERROR;
  2. source_status == "verified" with validated_by and validated_on (use --mark-verified ONLY when the
     human reviewer has said they validated it: it stamps the draft and the date);
  3. no PDF or verbatim quote travels: evidence.json stays in dev-knowledge.
Result: engine/<pack>/src/epc_<pack>/standards/<ID>/rules.json  + promotion.json next to the draft
        + the standard is listed in jurisdictions/<CC>/jurisdiction.json.
  <pack> is the norm engine `jurisdiction.json` names for the domain (`packs`: {"electrical": "aea90364"}); with more than one, say which with --pack.
"""
import argparse
import datetime
import sys
from pathlib import Path

from .common import ENGINE, pack_standards_dir, read_json, standard_dir, write_json
from .validate_rules import validate


def _destination(engine: Path, std: dict, pack):
    """The jurisdiction file, its content and the `standards/` folder of the norm engine it names for the domain of the standard (or the problem)."""
    jf = engine / "jurisdictions" / std["country"] / "jurisdiction.json"
    j = read_json(jf) if jf.exists() else {"id": std["country"], "status": "active"}
    standards, problem = pack_standards_dir(engine, j, std["domain"], pack)
    return jf, j, standards, problem


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("standard")
    ap.add_argument("--mark-verified", metavar="NAME")
    ap.add_argument("--engine", default=str(ENGINE), help="the engine folder: holds jurisdictions/ and the norm engines")
    ap.add_argument("--pack", help="the norm engine to promote into, when the jurisdiction names more than one for the domain")
    a = ap.parse_args()
    sdir = standard_dir(a.standard)
    draft = sdir / "draft" / "rules.json"
    if not draft.exists():
        print(f"no draft: {draft}")
        return 1
    doc, errs, warns = validate(draft, sdir)
    if errs:
        print("PROMOTION BLOCKED (validation errors):", *errs[:20], sep="\n  ")
        return 1
    if a.mark_verified:                       # stamp only after the draft passed validation
        doc["source_status"] = "verified"
        doc["validated_by"] = a.mark_verified
        doc["validated_on"] = datetime.date.today().isoformat()
        write_json(draft, doc)
        print(f"draft stamped as verified by {a.mark_verified}")
    if doc.get("source_status") != "verified" or not doc.get("validated_by") or not doc.get("validated_on"):
        print(f"PROMOTION BLOCKED: source_status={doc.get('source_status')!r}; the human reviewer must validate the draft first.")
        return 1
    std = doc["standard"]
    jf, j, standards, problem = _destination(Path(a.engine), std, a.pack)
    if problem:
        print(f"PROMOTION BLOCKED: {problem}")
        return 1
    dest = standards / std["id"] / "rules.json"
    write_json(dest, doc)
    listed = j.setdefault("standards", [])
    entry = {"id": std["id"], "domain": std["domain"], "engine": standards.parents[2].name, "rules": f"{standards.parents[2].name}/standards/{std['id']}/rules.json",
             "validated_by": doc["validated_by"], "validated_on": doc["validated_on"]}
    j["standards"] = [e for e in listed if e["id"] != std["id"]] + [entry]
    write_json(jf, j)
    write_json(sdir / "promotion.json", {"promoted_to": str(dest), "date": datetime.datetime.now().isoformat(timespec="seconds"),
                                         "rules": len(doc["rules"]), "warnings": len(warns)})
    print(f"promoted {std['id']}: {len(doc['rules'])} rules -> {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
