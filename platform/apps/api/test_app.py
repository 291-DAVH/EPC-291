"""End-user API tests. Run from platform/:  python -m unittest apps.api.test_app"""
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

PLATFORM = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PLATFORM))

from fastapi.testclient import TestClient  # noqa: E402

from apps.api import main  # noqa: E402


class TestUserApi(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._old, self._role = main.PROJECTS, main.ROLE
        main.PROJECTS, main.ROLE = self.root, "user"
        self.c = TestClient(main.app)
        r = self.c.post("/api/projects", json={"client_name": "Acme SA", "client_code": "ACME", "project_code": "P-1", "project_name": "Planta",
                                                "jurisdiction": "AR", "methodology": "pm2", "disciplines": ["electrical"]})
        self.assertEqual(r.status_code, 201, r.text)
        self.pid = "ACME/P-1"

    def tearDown(self):
        main.PROJECTS, main.ROLE = self._old, self._role
        self.tmp.cleanup()

    def test_internals_are_hidden_from_users(self):
        for path in ["/api/plugins", "/api/skills", "/api/rules", "/api/overview", "/api/projects", "/api/projects/ACME/P-1/tree",
                     "/api/rules/standards", "/api/policy"]:
            self.assertEqual(self.c.get(path).status_code, 403, path)
        self.assertEqual(self.c.post("/api/rules/check", json={}).status_code, 403)
        main.ROLE = "admin"
        self.assertEqual(self.c.get("/api/plugins").status_code, 200)

    def test_portfolio_and_project(self):
        p = self.c.get("/api/app/portfolio").json()
        self.assertEqual(p["kpis"]["total"], 1)                       # _template is never listed
        self.assertEqual(p["projects"][0]["name"], "Planta")
        self.assertEqual(p["projects"][0]["progress"], 0)
        self.assertEqual(self.c.get(f"/api/app/projects/{self.pid}").json()["client"], "Acme SA")
        self.assertEqual(self.c.get("/api/app/projects/_template/x").status_code, 404)
        self.assertEqual(self.c.get("/api/app/projects/ACME/..%2F..").status_code, 404)

    def test_input_upload_and_listing(self):
        r = self.c.post(f"/api/app/projects/{self.pid}/inputs", data={"kind": "voice_of_customer", "title": "Corte de luz", "text": "No podemos parar la línea."},
                        files=[("files", ("acta.pdf", io.BytesIO(b"%PDF-1.4 x"), "application/pdf"))])
        self.assertEqual(r.status_code, 201, r.text)
        self.assertEqual(r.json()["id"], "INT-0001")
        self.assertEqual(r.json()["status"], "received")
        r2 = self.c.post(f"/api/app/projects/{self.pid}/inputs", data={"kind": "user_story", "title": "Otra", "text": "x"})
        self.assertEqual(r2.json()["id"], "INT-0002")
        self.assertTrue((self.root / "ACME" / "P-1" / "workspace" / "01-input" / "intake" / "files" / "INT-0001" / "acta.pdf").exists())
        items = self.c.get(f"/api/app/projects/{self.pid}/inputs").json()
        self.assertEqual(len(items), 2)
        self.assertEqual(self.c.get("/api/app/portfolio").json()["projects"][0]["inputs"]["open"], 2)

    def test_input_validation(self):
        base = f"/api/app/projects/{self.pid}/inputs"
        self.assertEqual(self.c.post(base, data={"kind": "bad", "title": "t", "text": "x"}).status_code, 422)
        self.assertEqual(self.c.post(base, data={"kind": "document", "title": " ", "text": "x"}).status_code, 422)
        self.assertEqual(self.c.post(base, data={"kind": "document", "title": "t", "text": ""}).status_code, 422)
        r = self.c.post(base, data={"kind": "document", "title": "t", "text": "x"}, files=[("files", ("evil.exe", io.BytesIO(b"MZ"), "application/octet-stream"))])
        self.assertEqual(r.status_code, 422)
        r = self.c.post(base, data={"kind": "document", "title": "t", "text": "x"}, files=[("files", ("../../x.txt", io.BytesIO(b"hi"), "text/plain"))])
        self.assertEqual(r.status_code, 201)
        saved = self.root / "ACME" / "P-1" / "workspace" / "01-input" / "intake" / "files" / r.json()["id"]
        self.assertEqual([f.name for f in saved.iterdir()], ["x.txt"])      # path components stripped

    def test_download_only_inside_deliverables(self):
        d = self.root / "ACME" / "P-1"
        (d / "deliverables" / "ifa").mkdir(parents=True, exist_ok=True)
        (d / "deliverables" / "ifa" / "a.pdf").write_bytes(b"%PDF-1.4 ok")
        (d / "workspace" / "05-management" / "deliverables.json").write_text(json.dumps([
            {"id": "ENT-001", "code": "A-1", "name": "A", "format": "pdf", "status": "delivered", "file": "ifa/a.pdf", "due": "2026-01-01"},
            {"id": "ENT-002", "code": "A-2", "name": "B", "format": "pdf", "status": "delivered", "file": "../workspace/00-setup/goals.md"},
            {"id": "ENT-003", "code": "A-3", "name": "C", "format": "xlsx", "status": "planned", "due": "2000-01-01"}]), encoding="utf-8")
        base = f"/api/app/projects/{self.pid}/deliverables"
        lst = {x["id"]: x for x in self.c.get(base).json()}
        self.assertTrue(lst["ENT-001"]["downloadable"])
        self.assertFalse(lst["ENT-002"]["downloadable"])
        self.assertTrue(lst["ENT-003"]["overdue"])
        self.assertEqual(self.c.get(base + "/ENT-001/download").content, b"%PDF-1.4 ok")
        self.assertEqual(self.c.get(base + "/ENT-002/download").status_code, 404)   # traversal blocked


if __name__ == "__main__":
    unittest.main()
