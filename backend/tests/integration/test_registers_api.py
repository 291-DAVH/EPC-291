"""Project registers of the methodology (PM²): validated records, derived risk level, history of changes, never deleted."""
import json
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from epc.core.config import settings
from epc.main import create_app


class TestRegisters(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._old = (settings.projects_dir, settings.role, settings.user)
        settings.projects_dir, settings.role, settings.user = self.root, "admin", "Ing. Villena"
        self.c = TestClient(create_app())
        r = self.c.post("/api/projects", json={"client_name": "Acme SA", "client_code": "ACME", "project_code": "P-1", "project_name": "Planta",
                                                "jurisdiction": "AR", "methodology": "pm2", "disciplines": ["electrical"]})
        self.assertEqual(r.status_code, 201, r.text)
        self.base = "/api/projects/ACME/P-1/registers"

    def tearDown(self):
        settings.projects_dir, settings.role, settings.user = self._old
        self.tmp.cleanup()

    def test_definitions_come_from_the_methodology(self):
        v = self.c.get(self.base).json()
        self.assertEqual(v["methodology"], "pm2")
        self.assertEqual([(r["id"], r["prefix"], r["name"]) for r in v["registers"]],
                         [("risk", "RIE", "Riesgos"), ("change", "RFC", "Cambios"), ("issue", "INC", "Incidencias"), ("decision", "DEC", "Decisiones"),
                          ("assumption", "SUP", "Supuestos"), ("stakeholder", "STK", "Interesados"), ("observation", "OBS", "Observaciones")])
        risk = v["registers"][0]
        strategy = next(f for f in risk["fields"] if f["id"] == "strategy")
        self.assertEqual([o["label"] for o in strategy["options"]], ["Evitar", "Reducir", "Aceptar", "Transferir"])
        en = self.c.get(self.base + "?lang=en").json()
        self.assertEqual(en["registers"][0]["name"], "Risks")

    def test_risk_level_is_probability_times_impact(self):
        r = self.c.post(self.base + "/risk", json={"title": "Demora del cliente", "probability": 4, "impact": 5, "strategy": "reduce", "owner": "ME"})
        self.assertEqual(r.status_code, 201, r.text)
        rec = r.json()
        self.assertEqual((rec["id"], rec["level"], rec["level_name"], rec["status"], rec["created_by"]), ("RIE-001", 20, "high", "open", "Ing. Villena"))
        self.assertEqual(self.c.post(self.base + "/risk", json={"title": "b", "probability": 1, "impact": 2}).json()["level_name"], "low")
        self.assertEqual(self.c.post(self.base + "/risk", json={"title": "c", "probability": 3, "impact": 4}).json()["id"], "RIE-003")
        up = self.c.patch(self.base + "/risk/RIE-001", json={"impact": 2}).json()
        self.assertEqual((up["level"], up["level_name"]), (8, "medium"))

    def test_validation(self):
        for kind, body, field in (("risk", {"probability": 3, "impact": 3}, "title"), ("risk", {"title": "x", "probability": 9, "impact": 3}, "probability"),
                                  ("risk", {"title": "x", "probability": "alto", "impact": 3}, "probability"), ("risk", {"title": "x", "probability": 3, "impact": 3, "strategy": "ignore"}, "strategy"),
                                  ("risk", {"title": "x", "probability": 3, "impact": 3, "bogus": 1}, "bogus"), ("risk", {"title": "x" * 400, "probability": 3, "impact": 3}, "title"),
                                  ("issue", {"title": "sin responsable ni fecha"}, "owner"), ("issue", {"title": "x", "owner": "ME", "due": "mañana"}, "due"),
                                  ("assumption", {"title": "valor"}, "basis")):
            r = self.c.post(f"{self.base}/{kind}", json=body)
            self.assertEqual(r.status_code, 422, body)
            self.assertIn(field, r.json()["detail"]["errors"])
        self.assertEqual(self.c.post(self.base + "/nope", json={}).status_code, 404)

    def test_history_records_who_changed_what_and_when(self):
        self.c.post(self.base + "/change", json={"title": "Agregar tablero", "category": "scope"})
        up = self.c.patch(self.base + "/change/RFC-001", json={"status": "approved", "decision_ref": "DEC-001"}).json()
        self.assertEqual(up["status"], "approved")
        h = up["history"]
        self.assertEqual([x["action"] for x in h], ["created", "updated"])
        self.assertEqual((h[1]["by"], h[1]["changes"]), ("Ing. Villena", {"status": ["open", "approved"], "decision_ref": ["", "DEC-001"]}))
        self.assertTrue(h[1]["at"] and "T" in h[1]["at"])
        same = self.c.patch(self.base + "/change/RFC-001", json={"status": "approved"}).json()
        self.assertEqual(len(same["history"]), 2)                                    # nothing changed: nothing is recorded
        self.assertEqual(self.c.patch(self.base + "/change/RFC-099", json={"status": "closed"}).status_code, 404)

    def test_closing_stamps_the_date_and_records_are_never_deleted(self):
        self.c.post(self.base + "/issue", json={"title": "Falta plano", "owner": "Cliente", "due": "2026-12-01", "type": "client_info"})
        done = self.c.patch(self.base + "/issue/INC-001", json={"status": "closed", "evidence": "Plano recibido"}).json()
        self.assertTrue(done["closed_on"])
        self.assertEqual(self.c.delete(self.base + "/issue/INC-001").status_code, 405)
        self.assertEqual(len(self.c.get(self.base + "/issue").json()), 1)
        v = {r["id"]: r for r in self.c.get(self.base).json()["registers"]}
        self.assertEqual(v["issue"]["counts"], {"total": 1, "active": 0})

    def test_stored_as_project_data(self):
        self.c.post(self.base + "/decision", json={"title": "Usar cobre XLPE", "decided_by": "Cliente", "decided_on": "2026-10-20"})
        f = self.root / "ACME" / "P-1" / "workspace" / "05-management" / "registers" / "decision.json"
        data = json.loads(f.read_text(encoding="utf-8"))
        self.assertEqual((data["kind"], data["items"][0]["id"], data["items"][0]["status"]), ("decision", "DEC-001", "active"))

    def test_a_methodology_without_registers_is_reported_not_a_failure(self):
        meta = self.root / "ACME" / "P-1" / ".epc" / "project.json"
        meta.write_text(meta.read_text(encoding="utf-8").replace('"methodology": "pm2"', '"methodology": "pmi"'), encoding="utf-8")        # PMI has no pack yet
        v = self.c.get(self.base)
        self.assertEqual((v.status_code, v.json()["available"], v.json()["registers"], v.json()["methodology"]), (200, False, [], "pmi"))
        self.assertEqual(self.c.post(self.base + "/risk", json={"title": "x", "probability": 1, "impact": 1}).status_code, 409)       # writing still says why not
        r = self.c.get("/api/projects/ACME/P-1/reporting")
        self.assertEqual((r.status_code, r.json()["available"], r.json()["types"]), (200, False, []))
        self.assertEqual(self.c.post("/api/projects/ACME/P-1/reporting", json={"type": "status"}).status_code, 409)
        self.assertTrue(self.c.get(self.base).json()["registers"] == [])

    def test_engineer_only(self):
        settings.role = "user"
        for method, path in (("get", ""), ("get", "/risk"), ("post", "/risk"), ("patch", "/risk/RIE-001")):
            self.assertEqual(getattr(self.c, method)(self.base + path).status_code, 403, path)


if __name__ == "__main__":
    unittest.main()
