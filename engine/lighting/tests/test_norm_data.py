import json
import unittest
from importlib import resources

from epc_lighting import norm_data
from epc_lighting.model import LightingError


class NormDataTest(unittest.TestCase):
    def setUp(self):
        """The shipped rules as if none had been reviewed yet, so that approving one in the repository does not break these tests."""
        from unittest import mock
        real = json.loads((norm_data.RULES_DIR / "D351-79.rules.json").read_text("utf-8"))["rules"]
        pending = tuple({**r, "review": "pending"} for r in real)
        reader = lambda norm_id: pending                                              # noqa: E731
        reader.cache_clear = lambda: None
        patcher = mock.patch.object(norm_data, "_rules", reader)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_pending_rules_hidden_by_default(self):
        self.assertEqual(norm_data.rules("D351-79"), [])

    def test_pending_rules_available_on_request(self):
        found = norm_data.rules("D351-79", include_pending=True)
        self.assertGreater(len(found), 10)
        self.assertTrue(all(r["review"] == "pending" for r in found))

    def test_rule_lookup(self):
        item = norm_data.rule("D351-79", "D351-AIV-T2-oficina-general", True)
        self.assertEqual(item["value"], 500)
        with self.assertRaises(LightingError):
            norm_data.rule("D351-79", "D351-AIV-T2-oficina-general")

    def test_unknown_norm(self):
        with self.assertRaises(LightingError):
            norm_data.standard("NOPE")

    def test_standard_points_to_rules_file(self):
        std = norm_data.standard("D351-79")
        path = resources.files("epc_lighting").joinpath(std["rules_file"])
        self.assertEqual(json.loads(path.read_text("utf-8"))["norm"], "D351-79")
        self.assertFalse(std["source"]["kept_in_repo"])

    def test_rule_ids_unique_and_cited(self):
        found = norm_data.rules("D351-79", True)
        ids = [r["id"] for r in found]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(r["clause"] and r["summary"] for r in found))
        self.assertTrue(all(len(r["summary"]) <= 240 for r in found))


if __name__ == "__main__":
    unittest.main()


class TestTargetFromARule(unittest.TestCase):
    """A room takes its target from an approved rule of a norm; the test gives the engine rules in the states it has to tell apart (the shipped ones are still pending a human review)."""
    RULES = (
        {"id": "T-OFFICE", "clause": "Annex, table 2, offices", "summary": "General office work.", "value": 500, "unit": "lx", "review": "approved", "norm": "D351-79"},
        {"id": "T-PENDING", "clause": "Annex", "summary": "Not reviewed yet.", "value": 300, "unit": "lx", "review": "pending", "norm": "D351-79"},
        {"id": "T-RATIO", "clause": "Annex", "summary": "A ratio, not a level.", "value": 0.5, "unit": "ratio", "review": "approved", "norm": "D351-79"},
        {"id": "T-EMPTY", "clause": "Annex", "summary": "No value loaded.", "value": None, "unit": "lx", "review": "approved", "norm": "D351-79"},
    )

    def setUp(self):
        from unittest import mock
        patcher = mock.patch.object(norm_data, "_rules", lambda norm_id: self.RULES)
        patcher.start()
        self.addCleanup(patcher.stop)

    def room(self, **kw):
        import helpers
        item = {k: v for k, v in helpers.room_dict().items() if k != "target_lux"}
        return helpers.document([{**item, **kw}])

    def test_an_approved_rule_gives_the_target_and_says_where_it_comes_from(self):
        from epc_lighting import run
        room = run(self.room(target_rule="T-OFFICE")).as_dict()["rooms"][0]
        self.assertEqual(room["target"]["value"], 500)
        self.assertEqual(room["target"]["confidence"], 1.0)
        self.assertIn("rule T-OFFICE of D351-79", room["target"]["reason"])
        self.assertEqual((room["target"]["norm"], room["target"]["clause"]), ("D351-79", "Annex, table 2, offices"))

    def test_a_target_given_in_the_document_wins_over_the_rule_and_the_rule_over_the_activity(self):
        from epc_lighting import run
        given = run(self.room(target_rule="T-OFFICE", target_lux=320)).as_dict()["rooms"][0]["target"]
        self.assertEqual(given["value"], 320)
        both = run(self.room(target_rule="T-OFFICE", activity="education.classroom")).as_dict()["rooms"][0]["target"]
        self.assertEqual((both["value"], both["activity"], both["norm_rule"]), (500, "education.classroom", "T-OFFICE"))      # the activity still gives the glare limit

    def test_a_rule_that_is_not_approved_or_not_a_level_or_not_there_is_refused_with_what_to_do(self):
        from epc_lighting import run
        for rule, words in (("T-PENDING", "not approved"), ("T-RATIO", "not an illuminance level"), ("T-EMPTY", "not an illuminance level"), ("NOPE", "not in any norm")):
            with self.assertRaises(LightingError) as raised:
                run(self.room(target_rule=rule))
            self.assertIn(words, str(raised.exception))

    def test_an_exterior_area_can_take_it_too_and_the_document_still_needs_one_way_to_say_the_target(self):
        from epc_lighting import run
        import helpers
        area = run(helpers.document(areas=[{"id": "A1", "area_m2": 100, "target_rule": "T-OFFICE", "luminaire": "F1"}])).as_dict()["areas"][0]
        self.assertEqual(area["target"]["value"], 500)
        with self.assertRaises(LightingError) as missing:
            run(self.room())
        self.assertIn("'target_rule'", str(missing.exception))

    def test_the_norms_of_the_engine_are_listed(self):
        self.assertEqual(norm_data.norms(), ["D351-79"])


class TestCache(unittest.TestCase):
    def test_the_rule_files_can_be_read_again_after_a_correction(self):
        norm_data.rules("D351-79", True)
        norm_data.clear_cache()
        self.assertGreater(len(norm_data.rules("D351-79", True)), 10)
