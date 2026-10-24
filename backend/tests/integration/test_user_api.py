"""End-user surface (/api/app/*): portfolio, deliverables, inputs, role guard."""
import io
import json
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from epc.core.config import settings
from epc.main import create_app


class TestUserApi(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._old = (settings.projects_dir, settings.role)
        settings.projects_dir, settings.role = self.root, "user"
        self.c = TestClient(create_app())
        r = self.c.post("/api/projects", json={"client_name": "Acme SA", "client_code": "ACME", "project_code": "P-1", "project_name": "Planta",
                                                "jurisdiction": "AR", "methodology": "pm2", "disciplines": ["electrical"]})
        self.assertEqual(r.status_code, 201, r.text)
        self.pid = "ACME/P-1"

    def tearDown(self):
        settings.projects_dir, settings.role = self._old
        self.tmp.cleanup()

    def test_internals_are_hidden_from_users(self):
        for path in ["/api/plugins", "/api/skills", "/api/rules", "/api/overview", "/api/projects/ACME/P-1/tree",
                     "/api/rules/standards", "/api/policy"]:
            self.assertEqual(self.c.get(path).status_code, 403, path)
        self.assertEqual(self.c.post("/api/rules/check", json={}).status_code, 403)
        settings.role = "admin"
        self.assertEqual(self.c.get("/api/plugins").status_code, 200)

    def test_public_surface(self):
        self.assertEqual(self.c.get("/api/health").status_code, 200)
        self.assertEqual(self.c.get("/api/me").json()["role"], "user")
        self.assertEqual(self.c.get("/api/projects/options").status_code, 200)

    def test_admin_console_endpoints(self):
        settings.role = "admin"
        self.assertEqual(len(self.c.get("/api/plugins").json()), len(self.c.get("/api/overview").json() and self.c.get("/api/plugins").json()))
        ov = self.c.get("/api/overview").json()
        self.assertEqual(ov["projects"], 1)
        self.assertGreaterEqual(ov["plugins"], 10)
        self.assertEqual(self.c.get("/api/plugins/sld").json()["id"], "sld")
        self.assertEqual(self.c.get("/api/plugins/nope").status_code, 404)
        self.assertTrue(self.c.get("/api/skills").json())
        self.assertIn("formats", self.c.get("/api/policy").json())
        tree = self.c.get(f"/api/projects/{self.pid}/tree?area=workspace&depth=1").json()
        self.assertTrue(any(n["name"] == "00-setup" for n in tree["tree"]))
        self.assertEqual(self.c.get(f"/api/projects/{self.pid}/tree?area=bogus").status_code, 404)
        self.assertEqual(self.c.get("/api/rules/standards").status_code, 200)
        self.assertEqual(self.c.get("/api/rules/no-such-rule").status_code, 404)

    def test_portfolio_and_project(self):
        p = self.c.get("/api/app/portfolio").json()
        self.assertEqual(p["kpis"]["total"], 1)
        self.assertEqual(p["projects"][0]["name"], "Planta")
        self.assertEqual(p["projects"][0]["progress"], 0)
        self.assertEqual(self.c.get(f"/api/app/projects/{self.pid}").json()["client"], "Acme SA")
        self.assertEqual(self.c.get("/api/app/projects/_template/x").status_code, 404)
        self.assertEqual(self.c.get("/api/app/projects/ACME/..%2F..").status_code, 404)

    def test_input_upload_and_listing(self):
        r = self.c.post(f"/api/app/projects/{self.pid}/inputs", data={"kind": "voice_of_customer", "title": "Corte de luz", "text": "No podemos parar la línea."},
                        files=[("files", ("acta.pdf", io.BytesIO(b"%PDF-1.4 x"), "application/pdf"))])
        self.assertEqual(r.status_code, 201, r.text)
        self.assertEqual((r.json()["id"], r.json()["status"]), ("INT-0001", "received"))
        r2 = self.c.post(f"/api/app/projects/{self.pid}/inputs", data={"kind": "user_story", "title": "Otra", "text": "x"})
        self.assertEqual(r2.json()["id"], "INT-0002")
        self.assertTrue((self.root / "ACME" / "P-1" / "workspace" / "01-input" / "intake" / "files" / "INT-0001" / "acta.pdf").exists())
        self.assertEqual(len(self.c.get(f"/api/app/projects/{self.pid}/inputs").json()), 2)
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

    def test_requirements_show_source_titles(self):
        d = self.root / "ACME" / "P-1" / "workspace"
        self.c.post(f"/api/app/projects/{self.pid}/inputs", data={"kind": "user_story", "title": "Ruido", "text": "x"})
        (d / "00-setup" / "requirements.json").write_text(json.dumps([{"id": "REQ-001", "statement": "s", "type": "funcional", "priority": "alta",
                                                                      "discipline": "general", "acceptance": [], "open_questions": [],
                                                                      "source_intake": ["INT-0001"], "status": "definido"}]), encoding="utf-8")
        reqs = self.c.get(f"/api/app/projects/{self.pid}/requirements").json()
        self.assertEqual(reqs[0]["source_titles"], ["Ruido"])
        self.assertEqual(self.c.get(f"/api/app/projects/{self.pid}").json()["requirements_count"], 1)

    def test_open_questions_can_be_answered_with_author_and_time(self):
        d = self.root / "ACME" / "P-1" / "workspace"
        (d / "00-setup" / "requirements.json").write_text(json.dumps([{"id": "REQ-001", "statement": "s", "type": "funcional", "priority": "alta", "discipline": "general",
                                                                      "acceptance": [], "open_questions": ["¿Peso máximo?", "¿Fecha?"], "source_intake": [], "status": "abierto"}]), encoding="utf-8")
        base = f"/api/app/projects/{self.pid}/requirements/REQ-001/answer"
        self.assertEqual(self.c.post(base, json={"question": "¿Peso máximo?", "answer": "  "}).status_code, 422)
        self.assertEqual(self.c.post(base, json={"question": "otra", "answer": "x"}).status_code, 404)
        self.assertEqual(self.c.post(base.replace("REQ-001", "REQ-999"), json={"question": "¿Fecha?", "answer": "x"}).status_code, 404)
        r = self.c.post(base, json={"question": "¿Peso máximo?", "answer": "5 t"})
        self.assertEqual(r.status_code, 200, r.text)
        req = r.json()
        self.assertEqual((req["open_questions"], req["status"]), (["¿Fecha?"], "abierto"))
        a = req["answered_questions"][0]
        self.assertEqual((a["question"], a["answer"]), ("¿Peso máximo?", "5 t"))
        self.assertTrue(a["at"] and "T" in a["at"] and "by" in a)
        self.assertEqual(self.c.post(base, json={"question": "¿Peso máximo?", "answer": "again"}).status_code, 404)      # already answered
        self.assertEqual(self.c.post(base, json={"question": "¿Fecha?", "answer": "Marzo"}).json()["status"], "definido")  # none left
        self.assertEqual(self.c.get(f"/api/app/projects/{self.pid}/requirements").json()[0]["answered_questions"][1]["answer"], "Marzo")

    def test_downloads_only_inside_deliverables(self):
        d = self.root / "ACME" / "P-1"
        (d / "deliverables" / "ifa").mkdir(parents=True, exist_ok=True)
        (d / "deliverables" / "ifa" / "a.pdf").write_bytes(b"%PDF-1.4 ok")
        (d / "workspace" / "05-management" / "deliverables.json").write_text(json.dumps([
            {"id": "ENT-001", "code": "A-1", "name": "A", "format": "pdf", "status": "delivered", "file": "ifa/a.pdf", "due": "2026-01-01"},
            {"id": "ENT-002", "code": "A-2", "name": "B", "format": "pdf", "status": "delivered", "file": "../workspace/00-setup/goals.md"},
            {"id": "ENT-003", "code": "A-3", "name": "C", "format": "xlsx", "status": "planned", "due": "2000-01-01"}]), encoding="utf-8")
        (d / "workspace" / "05-management" / "reports" / "index.json").write_text(json.dumps([
            {"id": "INF-001", "title": "R", "type": "avance", "date": "2026-10-01", "file": "ifa/a.pdf", "summary": "s"},
            {"id": "INF-002", "title": "R2", "type": "avance", "date": "2026-10-02", "file": "../../../etc/passwd", "summary": "s"}]), encoding="utf-8")
        base = f"/api/app/projects/{self.pid}/deliverables"
        lst = {x["id"]: x for x in self.c.get(base).json()}
        self.assertTrue(lst["ENT-001"]["downloadable"])
        self.assertFalse(lst["ENT-002"]["downloadable"])
        self.assertTrue(lst["ENT-003"]["overdue"])
        self.assertEqual(self.c.get(base + "/ENT-001/download").content, b"%PDF-1.4 ok")
        self.assertEqual(self.c.get(base + "/ENT-002/download").status_code, 404)       # traversal blocked
        reps = {x["id"]: x for x in self.c.get(f"/api/app/projects/{self.pid}/reports").json()}
        self.assertTrue(reps["INF-001"]["downloadable"])
        self.assertFalse(reps["INF-002"]["downloadable"])
        self.assertEqual(self.c.get(f"/api/app/projects/{self.pid}/reports/INF-002/download").status_code, 404)
        k = self.c.get("/api/app/portfolio").json()["kpis"]
        self.assertEqual((k["deliverables_total"], k["deliverables_delivered"]), (3, 2))
        self.assertGreaterEqual(k["deliverables_due_soon"], 1)


if __name__ == "__main__":
    unittest.main()
