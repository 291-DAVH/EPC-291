"""The rules of the lighting norms (Decreto 351/79 for now) are one more unit of the norms review, and an approved one gives the target of a room."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

from epc_aea90364 import norm_data
from epc_lighting import norm_data as lighting_norms
from epc.core.config import settings
from epc.main import create_app
from epc.modules.norms import repository, service
from tests.integration.test_lighting_api import BASE, CLASSROOM, Base, body

UNIT = "lighting-rule:d351-79"
RULE = "D351-AIV-T2-oficina-general"
LATER = "D351-AIV-T2-oficina-hall"


class Reviewed(unittest.TestCase):
    """The norm data copied to a temporary folder, as the review of the other norms does, and the lighting engine reading the copy."""

    def setUp(self):
        import epc_aea90364
        pkg = Path(epc_aea90364.__file__).parent
        self.norms_tmp = tempfile.TemporaryDirectory()
        self.norms_root = Path(self.norms_tmp.name)
        (self.norms_root / "rules").mkdir()
        (self.norms_root / "lighting").mkdir()
        for f in (pkg / "rules").glob("*.json"):
            shutil.copy2(f, self.norms_root / "rules" / f.name)
        shutil.copy2(pkg / "aea_tables.json", self.norms_root / "aea_tables.json")
        shutil.copy2(norm_data.criteria_file("electrical"), self.norms_root / "design-criteria.json")
        shutil.copy2(lighting_norms.RULES_DIR / "D351-79.rules.json", self.norms_root / "lighting" / "D351-79.rules.json")
        repository.override({"rules": self.norms_root / "rules", "tables": self.norms_root / "aea_tables.json", "criteria": self.norms_root / "design-criteria.json", "review": self.norms_root / "review.json",
                             "log": self.norms_root / "review-log.jsonl", "lighting_rules": self.norms_root / "lighting"})
        self.addCleanup(repository.override, None)
        reader = lambda norm_id: tuple(self.file()["rules"])                                         # noqa: E731  the engine reads the copy, uncached
        reader.cache_clear = lambda: None
        patches = [mock.patch.object(lighting_norms, "_rules", reader), mock.patch.object(lighting_norms, "norms", lambda: ["D351-79"])]
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)
        self._reviewer_settings = (settings.role, settings.user)
        settings.role, settings.user = "standards", "Ing. Revisor"
        self.addCleanup(lambda: setattr(settings, "role", self._reviewer_settings[0]) or setattr(settings, "user", self._reviewer_settings[1]))

    def file(self):
        return json.loads((self.norms_root / "lighting" / "D351-79.rules.json").read_text(encoding="utf-8"))

    def flag(self, rule_id=RULE):
        return next(r["review"] for r in self.file()["rules"] if r["id"] == rule_id)


class TestReview(Reviewed):
    def setUp(self):
        super().setUp()
        self.c = TestClient(create_app())
        self.base = f"/api/norms/units/{UNIT}"

    def test_the_reviewer_sees_the_norm_as_a_unit_with_its_rules_pending(self):
        unit = next(u for u in self.c.get("/api/norms/units").json() if u["id"] == UNIT)
        self.assertEqual(unit["kind"], "lighting_rule")
        self.assertEqual((unit["counts"]["total"], unit["counts"]["approved"]), (len(self.file()["rules"]), 0))
        point = self.c.get(f"{self.base}/points/{RULE}").json()
        self.assertEqual((point["status"], point["value"]["value"], point["value"]["unit"]), ("pending", 500, "lx"))
        self.assertNotIn("review", point["value"])                                                    # the flag the engine reads is not part of what is approved
        self.assertEqual(point["editable"], ["summary", "value", "unit", "plane", "clause"])

    def test_approving_a_rule_marks_it_for_the_engine_and_is_logged(self):
        r = self.c.post(f"{self.base}/points/{RULE}/approve", json={"note": "checked against the decree"})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual((r.json()["status"], self.flag(), self.flag(LATER)), ("approved", "approved", "pending"))
        self.assertEqual(lighting_norms.illuminance_rule(RULE)["value"], 500)                           # the engine reads it now
        self.assertEqual(service.lighting_rule(RULE)["status"], "approved")
        self.assertEqual(self.c.get("/api/norms/log").json()[0]["action"], "approved")

    def test_a_correction_with_approval_changes_the_value_and_keeps_it_approved(self):
        r = self.c.put(f"{self.base}/points/{RULE}", json={"patch": {"value": 450, "clause": "Annex IV, table 2"}, "note": "the table says 450", "approve": True})
        self.assertEqual(r.status_code, 200, r.text)
        saved = next(x for x in self.file()["rules"] if x["id"] == RULE)
        self.assertEqual((saved["value"], saved["clause"], saved["review"]), (450, "Annex IV, table 2", "approved"))
        self.assertEqual(lighting_norms.illuminance_rule(RULE)["value"], 450)

    def test_a_correction_without_approval_and_a_rejection_take_the_rule_back_to_pending_for_the_engine(self):
        self.c.post(f"{self.base}/points/{RULE}/approve", json={})
        self.c.put(f"{self.base}/points/{RULE}", json={"patch": {"value": 480}})
        self.assertEqual((self.c.get(f"{self.base}/points/{RULE}").json()["status"], self.flag()), ("pending", "pending"))
        self.c.post(f"{self.base}/points/{RULE}/approve", json={})
        self.assertEqual(self.c.post(f"{self.base}/points/{RULE}/reject", json={"note": ""}).status_code, 422)
        self.assertEqual(self.c.post(f"{self.base}/points/{RULE}/reject", json={"note": "not what the decree says"}).json()["status"], "rejected")
        self.assertEqual(self.flag(), "pending")

    def test_what_cannot_be_a_level_or_is_not_editable_is_refused_with_what_to_correct(self):
        for patch in ({"value": -1}, {"unit": "foot-candles"}, {"summary": ""}, {"id": "other"}, {"review": "approved"}, {"value": "five hundred"}):
            self.assertEqual(self.c.put(f"{self.base}/points/{RULE}", json={"patch": patch}).status_code, 422, patch)
        self.assertEqual(self.c.put(f"{self.base}/points/{RULE}", json={"patch": {"unit": "ratio", "value": 0}}).status_code, 200)       # a ratio is not a level in lux
        self.assertEqual(self.flag(), "pending")

    def test_a_value_changed_after_the_approval_by_other_means_shows_as_stale(self):
        self.c.post(f"{self.base}/points/{RULE}/approve", json={})
        data = self.file()
        next(r for r in data["rules"] if r["id"] == RULE)["value"] = 520                               # for example a merge
        (self.norms_root / "lighting" / "D351-79.rules.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
        self.assertEqual(service.lighting_rule(RULE)["status"], "stale")
        self.assertEqual(self.c.get(f"{self.base}/points/{RULE}").json()["status"], "stale")


class TestApprovedRuleFeedsTheTarget(Reviewed, Base):
    def setUp(self):
        Base.setUp(self)                                                 # the project and its client first, then the norms as the reviewer sees them
        Reviewed.setUp(self)
        settings.role = "admin"                                          # the one working on the project is not the reviewer

    def rule_room(self, rule=RULE, **extra):
        return body(params={"R1": {"luminaire": "led_panel_600", "norm_rule": rule, **extra}})

    def calc(self, **kw):
        return self.c.post(BASE + "/calc", json=self.rule_room(**kw)).json()

    def test_the_panel_is_offered_the_levels_of_the_norm_with_their_status(self):
        rules = {r["id"]: r for r in self.c.get(BASE + "/options").json()["norm_rules"]}
        self.assertEqual((rules[RULE]["value"], rules[RULE]["status"], rules[RULE]["norm"]), (500, "pending", "D351-79"))
        self.assertNotIn("D351-AIV-uniformidad", rules)                                              # a ratio is not a level
        self.assertNotIn("D351-AIV-T2-industria-otros", rules)                                       # nor is a row with no value loaded yet
        service.approve(UNIT, RULE, "ok")
        self.assertEqual({r["id"]: r["status"] for r in self.c.get(BASE + "/options").json()["norm_rules"]}[RULE], "approved")

    def test_a_pending_rule_leaves_the_room_out_and_an_approved_one_gives_its_target_as_such(self):
        out = self.calc()
        self.assertIsNone(out["result"])
        self.assertIn("is pending", out["skipped"][0]["reason"])
        service.approve(UNIT, RULE, "ok")
        out = self.calc()
        target = out["result"]["rooms"][0]["target"]
        self.assertEqual((target["value"], target["confidence"], target["norm"]), (500, 1.0, "D351-79"))
        self.assertIn(RULE, target["reason"])
        self.assertIn("approved in the norms review", target["reason"])

    def test_a_target_given_by_hand_wins_and_a_rule_that_is_not_there_or_not_a_level_is_said(self):
        self.assertEqual(self.calc(target_lux=320)["result"]["rooms"][0]["target"]["value"], 320)
        self.assertIn("is not in any norm", self.calc(rule="NOPE")["skipped"][0]["reason"])
        service.approve(UNIT, "D351-AIV-uniformidad", "ok")
        self.assertIn("not a level in lux", self.calc(rule="D351-AIV-uniformidad")["skipped"][0]["reason"])

    def test_the_study_goes_stale_when_the_rule_it_used_is_corrected_or_withdrawn(self):
        service.approve(UNIT, RULE, "ok")
        params = {"luminaire": "led_panel_600", "norm_rule": RULE}
        layout = "/api/projects/ACME/P-1/layout/L0"
        drawing = {"discipline": "electrica_BT", "scale": {"p1": [0, 0], "p2": [100, 0], "distance_m": 10}, "origin": [0, 0], "nodes": [], "lines": [], "circuits": [], "rooms": [{**CLASSROOM, "lighting": params}]}
        self.assertEqual(self.c.put(layout, json=drawing).status_code, 200)
        self.assertEqual(self.c.put(BASE + "/study/L0", json=body(params={"R1": params})).status_code, 200)
        self.assertFalse(self.c.get(BASE + "/study/L0").json()["stale"])
        service.edit(UNIT, RULE, {"value": 450}, "corrected", approve=True)
        self.assertTrue(self.c.get(BASE + "/study/L0").json()["stale"])


if __name__ == "__main__":
    unittest.main()
