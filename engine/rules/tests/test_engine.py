import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from epc_rules import RuleSet, match_when, compare  # noqa: E402

STD_A = {
    "schema_version": "1.1",
    "standard": {"id": "TEST-1", "country": "ZZ", "body": "T", "edition": "1", "domain": "electrical"},
    "source_status": "verified", "validated_by": "t", "validated_on": "2026-01-01",
    "tables": [{"id": "t1", "clause": "1.1", "columns": ["size", "ampacity"], "rows": [[1.5, 15], [2.5, 21]]}],
    "rules": [
        {"id": "tray.reserve", "clause": "1.2", "topic": "trays", "type": "mandatory", "summary": {"es": "Reserva minima"},
         "applies_to": {"installation_types": ["dwellings"]}, "params": {"reserve_min_pct": 20},
         "check": {"field": "reserve_pct", "op": ">=", "value": 20}},
        {"id": "bath.zone1", "clause": "1.3", "topic": "bathrooms.zone1", "type": "mandatory", "summary": {"es": "Altura"},
         "applies_to": {"when": {"room": "bathroom", "area_m2": {"lt": 10}}}, "check": {"field": "height_cm", "op": "<=", "value": 225}},
        {"id": "no.diag", "clause": "1.4", "topic": "conduits", "type": "prohibited", "summary": {"es": "Sin diagonal"},
         "check": {"field": "diagonal", "op": "==", "value": True}},
    ],
}
STD_B_DRAFT = {
    "schema_version": "1.1",
    "standard": {"id": "TEST-2", "country": "ZZ", "body": "T", "edition": "1", "domain": "electrical"},
    "source_status": "draft",
    "rules": [{"id": "d.rule", "clause": "2.1", "topic": "x", "type": "recommended", "summary": {"es": "d"}}],
}


def make_root(tmp):
    """A jurisdiction ZZ whose electrical norms live in the norm engine `zznorm`."""
    (Path(tmp) / "jurisdictions" / "ZZ").mkdir(parents=True)
    (Path(tmp) / "jurisdictions" / "ZZ" / "jurisdiction.json").write_text(json.dumps({"id": "ZZ", "packs": {"electrical": "zznorm"}}), encoding="utf-8")
    d = Path(tmp) / "zznorm" / "src" / "epc_zznorm" / "standards"
    (d / "TEST-1").mkdir(parents=True)
    (d / "TEST-2").mkdir(parents=True)
    (d / "TEST-1" / "rules.json").write_text(json.dumps(STD_A), encoding="utf-8")
    (d / "TEST-2" / "rules.json").write_text(json.dumps(STD_B_DRAFT), encoding="utf-8")
    return Path(tmp)


class TestConditions(unittest.TestCase):
    def test_match_when(self):
        self.assertTrue(match_when({"a": 1, "b": ["x", "y"], "c": {"lt": 5}}, {"a": 1, "b": "y", "c": 4}))
        self.assertFalse(match_when({"a": 1}, {"a": 2}))
        self.assertFalse(match_when({"a": 1}, {}))          # missing field never matches

    def test_compare_type_error_is_false(self):
        self.assertFalse(compare("a", "<", 3))


class TestRuleSet(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = make_root(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_env_gating(self):
        dev = RuleSet.load("ZZ", root=self.root, env="dev")
        prod = RuleSet.load("ZZ", root=self.root, env="production")
        self.assertEqual({r["id"] for r in dev.rules}, {"tray.reserve", "bath.zone1", "no.diag", "d.rule"})
        self.assertEqual({r["id"] for r in prod.rules}, {"tray.reserve", "bath.zone1", "no.diag"})

    def test_query(self):
        rs = RuleSet.load("ZZ", root=self.root, env="dev")
        self.assertEqual([r["id"] for r in rs.query(topic="bathrooms")], ["bath.zone1"])
        self.assertEqual([r["id"] for r in rs.query(installation_type="dwellings", standard="TEST-1")][0], "tray.reserve")
        self.assertEqual(rs.param("tray.reserve", "reserve_min_pct"), 20)

    def test_table_lookup(self):
        rs = RuleSet.load("ZZ", root=self.root, env="dev")
        self.assertEqual(rs.lookup("t1", size=2.5), [{"size": 2.5, "ampacity": 21}])

    def test_check_pass_fail_skip(self):
        rs = RuleSet.load("ZZ", root=self.root, env="production")
        rep = rs.check({"reserve_pct": 15, "room": "bathroom", "area_m2": 5, "height_cm": 200, "diagonal": False}, installation_type="dwellings")
        by = {f.rule_id: f for f in rep.findings}
        self.assertFalse(by["tray.reserve"].passed)
        self.assertTrue(by["bath.zone1"].passed)
        self.assertTrue(by["no.diag"].passed)               # prohibited and not present -> ok
        rep2 = rs.check({"room": "kitchen"})
        self.assertNotIn("bath.zone1", {f.rule_id for f in rep2.findings})   # 'when' not satisfied
        rep3 = rs.check({}, installation_type="dwellings")
        self.assertTrue(all(f.passed is None for f in rep3.findings))        # missing fields are reported, not guessed
        self.assertEqual(rep.summary()["failed"], 1)

    def test_overrides(self):
        extra = dict(STD_B_DRAFT, source_status="verified")
        extra["rules"] = [{"id": "tray.reserve.v2", "overrides": "tray.reserve", "clause": "9", "topic": "trays", "type": "mandatory",
                           "summary": {"es": "x"}, "check": {"field": "reserve_pct", "op": ">=", "value": 25}}]
        p = self.root / "zznorm" / "src" / "epc_zznorm" / "standards" / "TEST-2" / "rules.json"
        p.write_text(json.dumps(extra), encoding="utf-8")
        rs = RuleSet.load("ZZ", root=self.root, env="production")
        self.assertIsNone(rs.get("tray.reserve"))
        self.assertEqual(rs.get("tray.reserve.v2")["check"]["value"], 25)


class TestLegacyDrafts(unittest.TestCase):
    """Runs against the imported AEA drafts when dev-knowledge is present."""
    DK = Path(__file__).resolve().parents[3] / "local" / "dev-knowledge"

    @unittest.skipUnless((DK / "standards/AR/AEA-90364-7-771/draft/rules.json").exists(), "drafts not available")
    def test_aea_drafts_load_and_check(self):
        rs = RuleSet.load("AR", "electrical", env="dev", include_drafts_from=self.DK)
        self.assertGreaterEqual(len(rs.rules), 177)
        rep = rs.check({"reserva_pct": 10, "altura_cm": 250}, installation_type="dwellings")
        self.assertTrue(any(f.rule_id == "bandejas.reserva_20pct" and f.passed is False for f in rep.findings))
        prod = RuleSet.load("AR", "electrical", env="production", include_drafts_from=self.DK)
        self.assertEqual(len(prod.rules), 0)               # nothing verified yet -> production sees no AEA rules


if __name__ == "__main__":
    unittest.main()
