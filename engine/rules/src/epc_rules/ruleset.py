"""Rule engine: load rules.json files for a jurisdiction and query/check them.

Sources, in order:
  1. engine/<norm engine>/src/epc_<norm engine>/standards/<STANDARD-ID>/rules.json   (promoted, product). The norm engines of a domain are the ones the jurisdiction
     names in `engine/jurisdictions/<CC>/jurisdiction.json` (`packs`: {"electrical": "aea90364"}, or a list when more than one norm applies).
  2. optional extra roots (e.g. dev-knowledge/standards/<CC>/<ID>/draft/rules.json) when
     `include_drafts_from` is given. Drafts are for development only.

env="production" keeps only standards with source_status == "verified".
"""
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .conditions import MISSING, compare, match_when

def _engine_root() -> Path:
    """Folder that contains `jurisdictions/`: EPC_ENGINE_ROOT, else the `engine/` folder of the repository."""
    env = os.environ.get("EPC_ENGINE_ROOT")
    if env:
        return Path(env)
    for p in Path(__file__).resolve().parents:
        if (p / "jurisdictions").is_dir() and p.name == "engine":
            return p
    return Path.cwd()


ENGINE_ROOT = _engine_root()


@dataclass
class Finding:
    rule_id: str
    standard: str
    clause: str
    type: str
    passed: Optional[bool]          # None = not evaluated
    message: str
    field: str = ""
    expected: Any = None
    actual: Any = None
    source_status: str = "draft"
    derived_check: bool = False
    reason: str = ""                # why it was not evaluated


@dataclass
class Report:
    findings: List[Finding] = field(default_factory=list)

    @property
    def failed(self):
        return [f for f in self.findings if f.passed is False]

    @property
    def passed(self):
        return [f for f in self.findings if f.passed is True]

    @property
    def not_evaluated(self):
        return [f for f in self.findings if f.passed is None]

    def summary(self):
        return {"passed": len(self.passed), "failed": len(self.failed), "not_evaluated": len(self.not_evaluated)}


class RuleSet:
    def __init__(self, files: List[dict], env: str = "dev"):
        self.env = env
        self.standards: Dict[str, dict] = {}
        self.rules: List[dict] = []
        self.tables: Dict[str, dict] = {}
        self._by_id: Dict[str, dict] = {}
        for doc in files:
            std = doc["standard"]
            sid = std["id"]
            status = doc.get("source_status", "draft")
            if env == "production" and status != "verified":
                continue
            self.standards[sid] = {**std, "source_status": status, "validated_by": doc.get("validated_by")}
            for t in doc.get("tables", []):
                self.tables[f"{sid}:{t['id']}"] = {**t, "standard": sid}
            for r in doc.get("rules", []):
                r = {**r, "_standard": sid, "_status": status}
                self.rules.append(r)
        self._resolve_overrides()
        self._by_id = {r["id"]: r for r in self.rules}

    # ---- loading ----
    @staticmethod
    def _standard_dirs(root: Path, jurisdiction: str, domain: Optional[str]) -> List[Path]:
        """The `standards/` folders of the norm engines the jurisdiction uses for the domain (all its domains when none is asked)."""
        jf = root / "jurisdictions" / jurisdiction / "jurisdiction.json"
        packs = json.loads(jf.read_text(encoding="utf-8")).get("packs", {}) if jf.is_file() else {}
        out: List[Path] = []
        for dom, value in sorted(packs.items()):
            for pack in ([value] if isinstance(value, str) else list(value or [])):
                if pack and (not domain or dom == domain):
                    out.append(root / pack / "src" / f"epc_{pack}" / "standards")
        return out

    @classmethod
    def load(cls, jurisdiction: str = "AR", domain: Optional[str] = None, env: Optional[str] = None,
             root: Optional[Path] = None, include_drafts_from: Optional[Path] = None) -> "RuleSet":
        env = env or os.environ.get("EPC_ENV", "dev")
        root = Path(root) if root else ENGINE_ROOT
        files = []
        for standards in cls._standard_dirs(root, jurisdiction, domain):
            for f in sorted(standards.glob("*/rules.json")):
                doc = json.loads(f.read_text(encoding="utf-8"))
                if not domain or doc["standard"].get("domain") == domain:
                    files.append(doc)
        if include_drafts_from:
            seen = {d["standard"]["id"] for d in files}
            for f in sorted(Path(include_drafts_from).glob(f"standards/{jurisdiction}/*/draft/rules.json")):
                doc = json.loads(f.read_text(encoding="utf-8"))
                if doc["standard"]["id"] not in seen and (not domain or doc["standard"].get("domain") == domain):
                    files.append(doc)
        return cls(files, env=env)

    def _resolve_overrides(self):
        replaced = {r["overrides"] for r in self.rules if r.get("overrides")}
        if replaced:
            self.rules = [r for r in self.rules if r["id"] not in replaced]

    # ---- queries ----
    def get(self, rule_id: str) -> Optional[dict]:
        return self._by_id.get(rule_id)

    def query(self, topic: Optional[str] = None, standard: Optional[str] = None, clause_prefix: Optional[str] = None,
              installation_type: Optional[str] = None, type: Optional[str] = None, part: Optional[str] = None) -> List[dict]:
        out = []
        for r in self.rules:
            if topic and not (r["topic"] == topic or r["topic"].startswith(topic + ".")):
                continue
            if standard and r["_standard"] != standard:
                continue
            if clause_prefix and not r["clause"].startswith(clause_prefix):
                continue
            if type and r["type"] != type:
                continue
            if part and r.get("part") != part:
                continue
            types = r.get("applies_to", {}).get("installation_types")
            if installation_type and types and installation_type not in types:
                continue
            out.append(r)
        return out

    def param(self, rule_id: str, key: str, default: Any = None) -> Any:
        r = self._by_id.get(rule_id)
        return r.get("params", {}).get(key, default) if r else default

    def table(self, table_id: str, standard: Optional[str] = None) -> Optional[dict]:
        if standard:
            return self.tables.get(f"{standard}:{table_id}")
        for k, t in self.tables.items():
            if k.endswith(":" + table_id):
                return t
        return None

    def lookup(self, table_id: str, standard: Optional[str] = None, **where) -> List[dict]:
        t = self.table(table_id, standard)
        if not t:
            return []
        cols = t["columns"]
        rows = [dict(zip(cols, row)) for row in t["rows"]]
        return [r for r in rows if all(r.get(k) == v for k, v in where.items())]

    # ---- checking ----
    def check(self, ctx: Dict[str, Any], installation_type: Optional[str] = None, topic: Optional[str] = None,
              standard: Optional[str] = None) -> Report:
        """Evaluate every applicable rule that has a `check`. Missing fields are reported, not guessed."""
        ctx = dict(ctx)
        if installation_type:
            ctx.setdefault("installation_type", installation_type)
        rep = Report()
        for r in self.query(topic=topic, standard=standard, installation_type=installation_type):
            chk = r.get("check")
            if not chk:
                continue
            when = r.get("applies_to", {}).get("when")
            if when and not match_when(when, ctx):
                continue
            base = dict(rule_id=r["id"], standard=r["_standard"], clause=r["clause"], type=r["type"],
                        field=chk["field"], expected=chk["value"], source_status=r["_status"],
                        derived_check=bool(chk.get("derived")), message=_summary(r))
            actual = ctx.get(chk["field"], MISSING)
            if actual is MISSING:
                rep.findings.append(Finding(passed=None, reason=f"context has no '{chk['field']}'", **base))
                continue
            ok = compare(actual, chk["op"], chk["value"])
            if r["type"] == "prohibited":
                ok = not ok
            rep.findings.append(Finding(passed=ok, actual=actual, **base))
        return rep


def _summary(rule: dict, locale: str = "es") -> str:
    s = rule.get("summary", {})
    return s.get(locale) or s.get("en") or next(iter(s.values()), rule.get("title", ""))
