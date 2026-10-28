"""Where the data of the norm lives: inside the engine package, so it travels with it."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from epc_aea90364 import aea_rules, aea_tables, norm_data   # noqa: E402


class TestNormData(unittest.TestCase):
    def test_the_data_of_the_norm_is_one_folder_inside_the_package(self):
        pkg = Path(norm_data.__file__).resolve().parent
        for f in (norm_data.criteria_file("electrical"), norm_data.REVIEW, norm_data.REVIEW_LOG, Path(aea_tables.RUTA_JSON), Path(aea_rules.CARPETA)):
            self.assertTrue(f.exists(), f)
            self.assertIn(pkg, f.resolve().parents)                       # nothing of the norm lies outside its engine
        self.assertEqual(norm_data.criteria_file("electrical").parent, norm_data.DATA)

    def test_a_discipline_the_norm_has_no_catalog_for_gets_none(self):
        self.assertIsNone(norm_data.criteria_file("hvac"))

    def test_the_catalog_lists_criteria_with_a_default_inside_their_limits(self):
        import json
        cat = json.loads(norm_data.criteria_file("electrical").read_text(encoding="utf-8-sig"))
        self.assertTrue(cat["criteria"])
        for c in cat["criteria"]:
            if c["type"] == "number":
                self.assertTrue(c.get("min", float("-inf")) <= c["default"] <= c.get("max", float("inf")), c["id"])
            else:
                self.assertIn(c["default"], c["options"], c["id"])


if __name__ == "__main__":
    unittest.main()
