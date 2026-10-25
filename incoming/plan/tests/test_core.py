"""Runs on its own: python -m unittest discover -s tests -t .   (needs only the folder, no backend, no network)"""
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from epc_plan import core, jobs   # noqa: E402


def load(name):
    return json.loads((ROOT / "fixtures" / name).read_text(encoding="utf-8"))


class TestCore(unittest.TestCase):
    def test_the_sample_gives_the_expected_result(self):
        self.assertEqual(core.process(load("input.json")), load("expected_output.json"))

    def test_it_is_deterministic(self):
        self.assertEqual(core.process(load("input.json")), core.process(load("input.json")))

    def test_the_output_has_the_fields_of_its_schema(self):
        schema = json.loads((ROOT / "schema" / "output.schema.json").read_text(encoding="utf-8"))
        out = core.process(load("input.json"))
        for k in schema["required"]:
            self.assertIn(k, out)

    def test_nothing_imports_the_backend(self):
        for f in (ROOT / "src").rglob("*.py"):
            text = f.read_text(encoding="utf-8")
            self.assertNotRegex(text, r"^\s*(from|import)\s+epc\b", f.name)


class TestJobs(unittest.TestCase):
    def test_a_job_reports_its_status_and_ends(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            jobs.start(load("input.json"), out).join(10)
            st = json.loads((out / "status.json").read_text(encoding="utf-8"))
            self.assertEqual((st["state"], st["progress"]), ("done", 1.0))
            self.assertTrue((out / "result.json").exists())


if __name__ == "__main__":
    unittest.main()
