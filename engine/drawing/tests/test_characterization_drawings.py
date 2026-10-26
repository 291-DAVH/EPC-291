"""The diagrams, tables, calculation files and memo of a board are what they were when the refactoring started (golden/drawings.json): any difference in a
drawing or a document is a change of what is delivered, not a refactoring."""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import characterization as C   # noqa: E402

GOLDEN = json.loads(C.GOLDEN.read_text(encoding="utf-8")) if C.GOLDEN.is_file() else {}


class TestDrawingCharacterization(unittest.TestCase):
    def test_every_case_is_in_the_golden_file(self):
        self.assertEqual(sorted(GOLDEN), sorted(C.CASES))

    def test_each_board_gives_its_drawings_byte_for_byte_after_normalizing_what_changes_every_run(self):
        for name in C.CASES:
            with self.subTest(case=name):
                got, want = C.run(name), GOLDEN[name]
                self.assertEqual((got["ok"], got["circuits"], got["non_compliant"]), (want["ok"], want["circuits"], want["non_compliant"]))
                self.assertEqual(sorted(got["files"]), sorted(want["files"]))
                for f in want["files"]:
                    self.assertEqual(got["files"][f], want["files"][f], f)

    def test_the_cases_exercise_what_they_claim(self):
        big = GOLDEN["big_paginated_sld_mld"]["files"]
        self.assertTrue(any(f.startswith("SLD_T1_H") and f.endswith(".svg") for f in big), "the big board is paginated in sheets")
        self.assertTrue(any(f.startswith("MLD_T1") for f in big))
        self.assertIn("T1_MC.md", big)
        self.assertGreater(GOLDEN["big_paginated_sld_mld"]["files"]["T1_MC.pdf"]["pdf_pages"], 0)


if __name__ == "__main__":
    unittest.main()
