"""The five PM² reports are what they were when the refactoring started (golden/reporting.json): document model and Markdown, in both languages."""
import json
import unittest

from tests.unit import characterization_reporting as C

GOLDEN = json.loads(C.GOLDEN.read_text(encoding="utf-8")) if C.GOLDEN.is_file() else {}
CURRENT = C.run()


class TestReportingCharacterization(unittest.TestCase):
    def test_every_case_is_in_the_golden_file(self):
        self.assertEqual(sorted(GOLDEN), sorted(CURRENT))

    def test_each_report_is_unchanged(self):
        for key in GOLDEN:
            with self.subTest(case=key):
                self.assertEqual(CURRENT[key], GOLDEN[key])

    def test_the_cases_cover_the_five_builders_in_both_languages(self):
        reports = [k.split("|") for k in GOLDEN if k != "helpers"]
        self.assertEqual({r[2] for r in reports}, {"status", "progress", "risks", "effort", "changes"})
        self.assertEqual({r[0] for r in reports}, {"es", "en"})


if __name__ == "__main__":
    unittest.main()
