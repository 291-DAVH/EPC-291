"""CLI: python -m epc_rules <list|query|check> [options]   (run from platform/core/rules)

  list  [--jurisdiction AR] [--drafts DEV_KNOWLEDGE_DIR]
  query [--topic bathrooms] [--standard ID] [--clause 771.8] [--installation dwellings] [--drafts DIR]
  check --context '{"reserva_pct": 15}' [--installation dwellings] [--drafts DIR]
"""
import argparse
import json
import sys
from pathlib import Path

from .ruleset import RuleSet, _summary


def main(argv=None):
    ap = argparse.ArgumentParser(prog="epc_rules")
    ap.add_argument("cmd", choices=["list", "query", "check"])
    ap.add_argument("--jurisdiction", default="AR")
    ap.add_argument("--domain")
    ap.add_argument("--env")
    ap.add_argument("--drafts", help="dev-knowledge directory to read draft rules from (development only)")
    ap.add_argument("--topic")
    ap.add_argument("--standard")
    ap.add_argument("--clause")
    ap.add_argument("--installation")
    ap.add_argument("--context", default="{}")
    a = ap.parse_args(argv)
    rs = RuleSet.load(a.jurisdiction, a.domain, a.env, include_drafts_from=Path(a.drafts) if a.drafts else None)
    if a.cmd == "list":
        for sid, s in rs.standards.items():
            n = sum(1 for r in rs.rules if r["_standard"] == sid)
            print(f"{sid:20s} {s['source_status']:18s} {n:4d} rules  {len(s.get('tables', []))}")
        print(f"total: {len(rs.rules)} rules, {len(rs.tables)} tables, env={rs.env}")
    elif a.cmd == "query":
        for r in rs.query(topic=a.topic, standard=a.standard, clause_prefix=a.clause, installation_type=a.installation):
            print(f"{r['id']:55s} {r['type']:11s} cl.{r['clause']:14s} {_summary(r)[:90]}")
    else:
        rep = rs.check(json.loads(a.context), installation_type=a.installation, topic=a.topic, standard=a.standard)
        for f in rep.findings:
            state = {True: "PASS", False: "FAIL", None: "SKIP"}[f.passed]
            extra = f" (expected {f.expected}, got {f.actual})" if f.passed is False else (f" [{f.reason}]" if f.passed is None else "")
            print(f"[{state}] {f.rule_id} cl.{f.clause}{extra}")
        print(rep.summary())
    return 0


if __name__ == "__main__":
    sys.exit(main())
