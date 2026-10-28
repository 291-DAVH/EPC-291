import json
import unittest
from importlib import resources

from epc_lighting import norm_data
from epc_lighting.model import LightingError


class NormDataTest(unittest.TestCase):
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
