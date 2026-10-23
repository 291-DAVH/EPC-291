#!/usr/bin/env python3
"""One-off importer: legacy aea-calc rules (scripts/rules/*.json, Spanish) -> draft rules.json per standard.

  python -m epc_standards.import_legacy_rules [--rules-dir DIR] [--dev-knowledge DIR]

For each standard it writes (in dev-knowledge, never versioned):
  standards/AR/<ID>/draft/rules.json        product-shaped rules (schema 1.1), source_status = draft
  standards/AR/<ID>/analysis/evidence.json  the verbatim quotes, kept private
Ids and parameter names keep their legacy Spanish text (flag i18n_pending) until the English pass.
A `check` is derived mechanically only when a rule has exactly one numeric *_min/*_max parameter.
"""
import argparse
import collections
import re
import sys
from pathlib import Path

from .common import DEV_KNOWLEDGE, ENGINE, read_json, write_json

STD = {  # legacy "norma" -> (standard id, part)
    "AEA 90364-7-771": ("AEA-90364-7-771", None), "AEA 90364-7-770": ("AEA-90364-7-770", None),
    "AEA 90364-7-701": ("AEA-90364-7-701", None), "AEA 90364-7-722": ("AEA-90364-7-722", None),
    "AEA 90364-5-51": ("AEA-90364-5", "5-51"), "AEA 90364-5-52": ("AEA-90364-5", "5-52"), "AEA 90364-5-54": ("AEA-90364-5", "5-54"),
    "AEA 90364-4-41": ("AEA-90364-4", "4-41"), "AEA 90364-4-43": ("AEA-90364-4", "4-43"),
}
TYPE = {"obligatorio": "mandatory", "recomendado": "recommended", "prohibido": "prohibited"}
INSTALLATION = {"viviendas": "dwellings", "oficinas": "offices", "locales": "commercial_premises", "industrias": "industrial",
                "vehículos eléctricos": "ev_charging", "depósitos y elaboración de sustancias no inflamables": "non_flammable_storage",
                "establecimientos educativos": "educational", "alumbrado exterior": "outdoor_lighting", "garajes": "garages"}
CONF = {"text": "medium", "visual": "medium", "ocr": "low"}
MINMAX = re.compile(r"^(.+?)_(min|max)(?:_([a-z0-9]+))?$")


def convert_table(rid, clause, tabla):
    if isinstance(tabla, list) and tabla and isinstance(tabla[0], dict):
        cols = list(tabla[0].keys())
        return {"id": rid, "clause": clause, "columns": cols, "rows": [[row.get(c) for c in cols] for row in tabla]}
    if isinstance(tabla, dict) and "filas" in tabla:
        cols = tabla.get("columnas", [])
        t = {"id": rid, "clause": clause, "columns": cols, "rows": [list(row) + [None] * (len(cols) - len(row)) for row in tabla["filas"]]}
        if tabla.get("notas"):
            t["notes"] = tabla["notas"]
        return t
    return None


def derive_check(rtype, params):
    if rtype == "prohibited":
        return None
    hits = [(k, MINMAX.match(k)) for k, v in params.items() if MINMAX.match(k) and isinstance(v, (int, float)) and not isinstance(v, bool)]
    if len(hits) != 1:
        return None
    k, m = hits[0]
    base, kind, unit = m.groups()
    return {"field": base + (f"_{unit}" if unit else ""), "op": ">=" if kind == "min" else "<=", "value": params[k], "derived": True}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules-dir", default=str(ENGINE / "calc" / "src" / "epc_calc" / "rules"))
    ap.add_argument("--dev-knowledge", default=str(DEV_KNOWLEDGE))
    ap.add_argument("--force", action="store_true", help="overwrite existing drafts (they may contain human edits)")
    a = ap.parse_args()
    fixes = read_json(Path(__file__).resolve().parent / "data" / "summary_fixes.json")["es"]
    legacy = []
    for f in sorted(Path(a.rules_dir).glob("*.json")):
        if f.name.startswith("_"):
            continue
        legacy.extend(read_json(f)["reglas"])
    docs = {}
    editions = collections.defaultdict(collections.Counter)
    for r in legacy:
        f = r["fuente"]
        sid, part = STD[f["norma"]]
        d = docs.setdefault(sid, {"rules": [], "tables": [], "evidence": {}})
        editions[sid][f.get("edicion", "")] += 1
        rtype = TYPE[r["tipo"]]
        ver = f.get("verificacion") or "text"
        rule = {"id": r["id"], "legacy_id": r["id"], "clause": f["clausula"], "topic": r["grupo"], "title": r["tema"],
                "summary": {"es": fixes.get(r["id"], r["regla"])[:240]}, "type": rtype,
                "applies_to": {"installation_types": sorted({INSTALLATION[x] for x in r.get("aplica_a", [])})},
                "params": r.get("parametros", {}), "verification": ver, "confidence": CONF[ver],
                "evidence_ref": r["id"], "i18n_pending": True}
        if part:
            rule["part"] = part
        page = {}
        if f.get("pagina_impresa") is not None:
            page["printed"] = f["pagina_impresa"]
        if f.get("pagina_pdf") is not None:
            page["pdf"] = f["pagina_pdf"]
        if page:
            rule["page"] = page
        chk = derive_check(rtype, rule["params"])
        if chk:
            rule["check"] = chk
        if "tabla" in r:
            t = convert_table(r["id"], f["clausula"], r["tabla"])
            if t:
                d["tables"].append(t)
                rule["table_ref"] = t["id"]
        d["rules"].append(rule)
        d["evidence"][r["id"]] = {"quote": f.get("cita", ""), "norm": f["norma"], "edition": f.get("edicion"), "clause": f["clausula"],
                                  "page_printed": f.get("pagina_impresa"), "page_pdf": f.get("pagina_pdf"), "verification": ver, "legacy_state": r.get("estado")}
    for sid, d in sorted(docs.items()):
        edition = editions[sid].most_common(1)[0][0]
        doc = {"schema_version": "1.1",
               "standard": {"id": sid, "country": "AR", "body": "AEA", "edition": edition, "domain": "electrical"},
               "source_status": "draft", "tables": d["tables"], "rules": d["rules"]}
        base = Path(a.dev_knowledge) / "standards" / "AR" / sid
        if (base / "draft" / "rules.json").exists() and not a.force:
            print(f"{sid}: draft exists, skipped (use --force to overwrite)")
            continue
        write_json(base / "draft" / "rules.json", doc)
        write_json(base / "analysis" / "evidence.json", d["evidence"])
        nchk = sum(1 for r in d["rules"] if "check" in r)
        print(f"{sid:18s} {len(d['rules']):4d} rules  {len(d['tables']):2d} tables  {nchk:3d} derived checks  -> {base / 'draft' / 'rules.json'}")
    print(f"total {sum(len(d['rules']) for d in docs.values())} rules from {len(legacy)} legacy rules")
    return 0


if __name__ == "__main__":
    sys.exit(main())
