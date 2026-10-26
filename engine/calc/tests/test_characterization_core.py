"""Ampacity over installation methods, the feeder report and the protection checks give what they gave when the refactoring started (golden/core.json)."""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import characterization_core as C   # noqa: E402

GOLDEN = json.loads(C.GOLDEN.read_text(encoding="utf-8")) if C.GOLDEN.is_file() else {}


class TestCoreCharacterization(unittest.TestCase):
    def test_ampacity_by_method_insulation_material_phases_grouping_and_temperature(self):
        self.assertEqual(C.ampacity(), GOLDEN["ampacity"])

    def test_the_feeder_report_documents(self):
        self.assertEqual(C.feeder_reports(), GOLDEN["feeder_reports"])

    def test_the_protection_checks(self):
        self.assertEqual(C.protection(), GOLDEN["protection"])

    def test_the_grid_has_the_shape_it_claims(self):
        self.assertEqual(len(GOLDEN["ampacity"]), 8 * 2 * 2 * 2 * 2 * 2)
        self.assertTrue(any("error" in str(v) for row in GOLDEN["ampacity"].values() for v in row["iz"].values()))     # combinations without a table are part of the behaviour
        self.assertTrue(any("NO CUMPLE" in f for r in GOLDEN["feeder_reports"].values() for f in r.get("files", {}).values()))
        self.assertTrue(any("CUMPLE" in f for r in GOLDEN["feeder_reports"].values() for f in r.get("files", {}).values()))
        self.assertIn("error", GOLDEN["feeder_reports"]["al_xlpe"])                        # the report applies no XLPE -> B2 rule: pinned as a known divergence


if __name__ == "__main__":
    unittest.main()
