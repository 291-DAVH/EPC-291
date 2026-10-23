"""Project creation and options (projects module) through the HTTP API."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

from epc.core.config import settings
from epc.main import create_app


class TestCreateProject(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._old = (settings.projects_dir, settings.role)
        settings.projects_dir, settings.role = self.root, "admin"
        self.c = TestClient(create_app())

    def tearDown(self):
        settings.projects_dir, settings.role = self._old
        self.tmp.cleanup()

    body = {"client_name": "Ford Argentina", "client_code": "FORD", "project_code": "PRJ-001", "project_name": "Planta",
            "jurisdiction": "AR", "methodology": "pm2", "disciplines": ["electrical", "hvac"]}

    def test_options(self):
        o = self.c.get("/api/projects/options").json()
        self.assertEqual(o["jurisdictions"][0]["id"], "AR")
        self.assertIn("electrical", o["jurisdictions"][0]["disciplines"])
        pm = {m["id"]: m for m in o["methodologies"]}
        self.assertTrue(pm["pm2"]["available"])
        self.assertFalse(pm["pmi"]["available"])

    def test_create_copies_template_and_writes_lock(self):
        r = self.c.post("/api/projects", json=self.body)
        self.assertEqual(r.status_code, 201, r.text)
        d = self.root / "FORD" / "PRJ-001"
        meta = json.loads((d / ".epc" / "project.json").read_text(encoding="utf-8"))
        self.assertEqual((meta["client"], meta["client_code"], meta["project_code"]), ("Ford Argentina", "FORD", "PRJ-001"))
        self.assertEqual(meta["locale"], "es-AR")           # default from the jurisdiction
        self.assertEqual(meta["disciplines"], ["electrical", "hvac"])
        lock = json.loads((d / ".epc" / "plugins.lock").read_text(encoding="utf-8"))
        self.assertIn("aea-calc", lock["plugins"])
        self.assertNotIn("mld", lock["plugins"])            # pending plugins are not locked
        self.assertTrue((d / "workspace" / "00-setup" / "goals.md").exists())
        self.assertTrue((d / "deliverables").is_dir())
        self.assertTrue((d / ".epc" / "ledger" / "0001_created.json").exists())
        self.assertEqual(r.json()["id"], "FORD/PRJ-001")
        self.assertGreater(r.json()["plugins_locked"], 0)
        self.assertIn("FORD/PRJ-001", [p["id"] for p in self.c.get("/api/projects").json()])

    def test_duplicate_is_409(self):
        self.assertEqual(self.c.post("/api/projects", json=self.body).status_code, 201)
        self.assertEqual(self.c.post("/api/projects", json=self.body).status_code, 409)

    def test_validation(self):
        for patch, field in [({"client_code": "../evil"}, "client_code"), ({"project_code": "a b"}, "project_code"),
                             ({"client_name": " "}, "client_name"), ({"jurisdiction": "ZZ"}, "jurisdiction"),
                             ({"methodology": "pmi"}, "methodology"), ({"methodology": "xyz"}, "methodology"),
                             ({"disciplines": []}, "disciplines"), ({"disciplines": ["nuclear"]}, "disciplines"),
                             ({"client_code": "_template"}, "client_code")]:
            r = self.c.post("/api/projects", json={**self.body, **patch})
            self.assertEqual(r.status_code, 422, (patch, r.text))
            self.assertIn(field, r.json()["detail"]["errors"])
        self.assertFalse((self.root / "evil").exists())

    def test_nothing_left_behind_on_failure(self):
        with mock.patch("epc.modules.projects.repository._load_build_tool", side_effect=RuntimeError("boom")):
            r = self.c.post("/api/projects", json=self.body)
        self.assertEqual(r.status_code, 500)
        self.assertFalse((self.root / "FORD" / "PRJ-001").exists())


if __name__ == "__main__":
    unittest.main()
