"""The phases of a project: where it starts, where it ends (not every project goes through detail engineering or as-built) and the phases the options offer."""
import json
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from epc.core.config import settings
from epc.main import create_app

BODY = {"client_name": "Acme SA", "client_code": "ACME", "project_code": "P-1", "project_name": "Planta", "jurisdiction": "AR", "methodology": "pm2", "disciplines": ["electrical"]}


class TestProjectPhases(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._old = (settings.projects_dir, settings.role, settings.data_dir)
        settings.projects_dir, settings.role, settings.data_dir = self.root, "admin", self.root / "_data"
        self.c = TestClient(create_app())

    def tearDown(self):
        settings.projects_dir, settings.role, settings.data_dir = self._old
        self.tmp.cleanup()

    def meta(self):
        return json.loads((self.root / "ACME" / "P-1" / ".epc" / "project.json").read_text(encoding="utf-8"))

    def test_the_options_offer_the_five_phases_in_the_order_they_are_worked(self):
        self.assertEqual(self.c.get("/api/projects/options").json()["phases"], ["IC", "IB", "ID", "IE", "ASB"])

    def test_a_project_ends_at_as_built_unless_it_says_otherwise_and_keeps_the_phase_it_chose(self):
        self.assertEqual(self.c.post("/api/projects", json=BODY).status_code, 201)
        self.assertEqual((self.meta()["phase"], self.meta()["end_phase"]), ("IC", "ASB"))

    def test_a_project_may_stop_at_basic_engineering(self):
        self.assertEqual(self.c.post("/api/projects", json={**BODY, "phase": "IB", "end_phase": "ID"}).status_code, 201)
        self.assertEqual((self.meta()["phase"], self.meta()["end_phase"]), ("IB", "ID"))

    def test_the_end_cannot_come_before_the_start_nor_be_unknown(self):
        r = self.c.post("/api/projects", json={**BODY, "phase": "ID", "end_phase": "IB"})
        self.assertEqual(r.status_code, 422)
        self.assertIn("end_phase", r.json()["detail"]["errors"])
        r = self.c.post("/api/projects", json={**BODY, "end_phase": "XX"})
        self.assertEqual(r.status_code, 422)
        self.assertIn("end_phase", r.json()["detail"]["errors"])
        self.assertFalse((self.root / "ACME" / "P-1").exists())                  # nothing was created


if __name__ == "__main__":
    unittest.main()
