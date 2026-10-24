"""PM² management reports (D11 to D15): built from project data in the template's structure, saved as Markdown and PDF, published to the client on demand."""
import datetime as dt
import io
import json
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from epc.core.config import settings
from epc.main import create_app

TODAY = dt.date.today()


def iso(days):
    return (TODAY + dt.timedelta(days=days)).isoformat()


class TestReporting(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._old = (settings.projects_dir, settings.role, settings.data_dir)
        settings.projects_dir, settings.role, settings.data_dir = self.root, "admin", self.root / "_data"
        self.c = TestClient(create_app())
        r = self.c.post("/api/projects", json={"client_name": "Acme SA", "client_code": "ACME", "project_code": "P-1", "project_name": "Planta",
                                                "jurisdiction": "AR", "methodology": "pm2", "disciplines": ["electrical"]})
        self.assertEqual(r.status_code, 201, r.text)
        self.d = self.root / "ACME" / "P-1"
        self.m = self.d / "workspace" / "05-management"
        self.base = "/api/projects/ACME/P-1/reporting"
        (self.m / "project-status.json").write_text(json.dumps({
            "schema_version": "1.0", "state": "active", "progress_pct": 30, "health": "at_risk", "phase": "IB", "manager": "M. Ferreyra", "start": iso(-60), "due": iso(60),
            "milestones": [{"name": "Arranque", "date": iso(-60), "done": True}, {"name": "Ingeniería básica aprobada", "date": iso(-5), "done": False},
                           {"name": "Entrega final", "date": iso(60), "done": False}], "updated": iso(-1)}), encoding="utf-8")
        self.c.put("/api/projects/ACME/P-1/wbs", json={"nodes": [{"id": "1", "name": "Ingeniería", "discipline": "electrical", "owner": "ME"},
                                                                  {"id": "1.1", "name": "Cálculos", "weight": 3, "progress": 100, "discipline": "electrical"},
                                                                  {"id": "1.2", "name": "Planos", "weight": 1, "progress": 0, "discipline": "electrical"}]})
        self.c.put("/api/projects/ACME/P-1/schedule", json={"activities": [{"id": "A1", "name": "Planos del tablero", "start": iso(1), "end": iso(8), "wbs_id": "1.2"}]})
        for title, h, wbs in (("Cálculo de alimentadores", 40, "1.1"), ("Planos unifilar", 20, "1.2")):
            self.c.post("/api/projects/ACME/P-1/backlog", json={"title": title, "estimate_h": h, "wbs_id": wbs})
        (self.m / "deliverables.json").write_text(json.dumps([
            {"id": "ENT-001", "code": "P-1-ELE-001", "name": "Memoria", "format": "pdf", "status": "delivered", "revision": "Rev 00", "delivered_on": iso(-2), "due": iso(-3)},
            {"id": "ENT-002", "code": "P-1-ELE-002", "name": "Unifilar", "format": "dxf", "status": "planned", "revision": "Rev 00", "due": iso(-1)},
            {"id": "ENT-003", "code": "P-1-ELE-003", "name": "Cómputo", "format": "xlsx", "status": "planned", "revision": "Rev 00", "due": iso(3)}]), encoding="utf-8")
        (self.d / "workspace" / "00-setup" / "requirements.json").write_text(json.dumps([
            {"id": "REQ-001", "statement": "s", "type": "funcional", "priority": "alta", "discipline": "general", "acceptance": [], "open_questions": ["¿Peso máximo?"],
             "source_intake": [], "status": "abierto"}]), encoding="utf-8")
        reg = lambda kind, **f: self.assertEqual(self.c.post(f"/api/projects/ACME/P-1/registers/{kind}", json=f).status_code, 201)
        reg("change", title="Agregar tablero TS-03", category="scope", status="approved", owner="ME", decision_ref="DEC-004")
        reg("change", title="Cambiar luminarias", category="design", status="open", owner="ME")
        reg("change", title="Mover sala", category="client", status="rejected", owner="ME", decision_ref="DEC-005", justification="Fuera de alcance")
        reg("risk", title="Demora del cliente en datos", probability=4, impact=5, strategy="reduce", owner="ME")
        reg("risk", title="Cambio de norma", probability=2, impact=3, strategy="accept", owner="ME")
        reg("risk", title="Proveedor", probability=1, impact=2, strategy="accept", owner="ME", status="closed", closing_reason="Entregado")
        reg("issue", title="Falta plano de arquitectura", type="client_info", impact="PQ-03", owner="Cliente", due=iso(5))
        reg("issue", title="Resuelto", type="pending", owner="ME", due=iso(1), status="closed")

    def tearDown(self):
        settings.projects_dir, settings.role, settings.data_dir = self._old
        self.tmp.cleanup()

    def gen(self, kind, **extra):
        r = self.c.post(self.base, json={"type": kind, **extra})
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()

    def md(self, rec):
        return (self.d / rec["md"]).read_text(encoding="utf-8")

    def test_catalog_comes_from_the_methodology(self):
        o = self.c.get(self.base).json()
        self.assertEqual(o["methodology"], "pm2")
        self.assertEqual([(t["id"], t["code"], t["audience"]) for t in o["types"]],
                         [("status", "D11", "client"), ("progress", "D12", "client"), ("risks", "D13", "internal"), ("effort", "D14", "internal"), ("changes", "D15", "internal")])
        self.assertEqual(o["types"][0]["name"], "Informe de estado")
        self.assertEqual(self.c.post(self.base, json={"type": "nope"}).status_code, 422)

    def test_status_report_follows_the_d11_template_with_project_data(self):
        r = self.gen("status")
        self.assertEqual((r["id"], r["code"], r["audience"], r["published"]), ("STATUS-01", "D11", "client", None))
        self.assertTrue(r["md"].startswith("workspace/05-management/progress/STATUS-01_") and r["pdf"].endswith(".pdf"))
        md = self.md(r)
        for s in ("# INFORME DE ESTADO — STATUS-01", "**Proyecto:** Planta", "**Fase actual:** Ingeniería básica", "### Estado general", "### Resumen ejecutivo",
                  "### Indicadores de desempeño", "### Hitos", "### Cambios activos", "### Riesgos activos relevantes", "### Problemas / Incidencias", "### Decisiones requeridas"):
            self.assertIn(s, md)
        self.assertIn("| Cronograma | AMARILLO | → |", md)                   # health at risk and an overdue deliverable
        self.assertIn("| Riesgos | ROJO |", md)                               # RIE-001 level 20
        self.assertIn("| Cambios | AMARILLO |", md)                          # rfc-002 is open
        self.assertIn("Estado general del proyecto: ROJO", md)
        self.assertIn("| Ingeniería básica aprobada |", md)
        self.assertIn("Con retraso", md)                                      # that milestone date has passed
        self.assertIn("RFC-002 | Cambiar luminarias | Abierto", md)
        self.assertIn("RIE-001 | Demora del cliente en datos", md)
        self.assertNotIn("RIE-003", md)                                       # closed
        self.assertIn("INC-001 Falta plano de arquitectura | PQ-03 | Abierto", md)
        self.assertNotIn("INC-002", md)                                       # closed
        self.assertIn("REQ-001: ¿Peso máximo?", md)                           # open questions are the decisions still required from the client
        self.assertIn("Entregables vencidos: 1", md)                          # the unifilar is overdue
        pdf = self.c.get(f"{self.base}/STATUS-01/file").content
        self.assertTrue(pdf.startswith(b"%PDF"))
        import pypdfium2 as pdfium
        text = "".join(p.get_textpage().get_text_range() for p in pdfium.PdfDocument(io.BytesIO(pdf)))
        self.assertIn("INFORME DE ESTADO", text)
        self.assertIn("Cambiar luminarias", text)

    def test_trend_compares_with_the_previous_report(self):
        self.gen("status")
        self.assertEqual(self.c.patch("/api/projects/ACME/P-1/registers/change/RFC-002", json={"status": "approved"}).status_code, 200)   # no open change any more
        r2 = self.gen("status")
        self.assertEqual(r2["id"], "STATUS-02")
        self.assertIn("| Cambios | VERDE | ↑ |", self.md(r2))
        self.assertIn("| Riesgos | ROJO | → |", self.md(r2))

    def test_progress_report_has_the_nine_sections(self):
        md = self.md(self.gen("progress"))
        for n, s in enumerate(["Resumen ejecutivo", "Interesados clave", "Hitos y entregables", "Plan de trabajo por paquete", "Cambios de alcance",
                               "Riesgos principales y acciones", "Problemas principales y acciones", "Otras acciones en curso / planificadas", "Logros del período"], 1):
            self.assertIn(f"### {n}. {s}", md)
        self.assertIn("1.1 Cálculos | -", md)
        self.assertIn("P-1-ELE-001 Memoria", md)
        self.assertIn("Cambios aprobados acumulados: 1", md)
        self.assertIn("Sin interesados registrados", md)                      # the register has no rows yet: it says so instead of inventing people
        self.assertIn("Entregable emitido: P-1-ELE-001 – Memoria", md)        # delivered inside the period

    def test_risk_report(self):
        md = self.md(self.gen("risks"))
        self.assertIn("| General | 1 | 1 | 0 | 2 |", md)                      # active risks by level (the closed one is not counted)
        self.assertIn("| RIE-001 | Demora del cliente en datos | 4 | 5 | 20 | Reducir | ME | Abierto |", md)
        self.assertIn("RIE-002", md)
        self.assertIn("| RIE-003 | Proveedor | Cerrado – Entregado |", md)       # closed today, inside the period
        self.assertIn("### Riesgos nuevos en el período", md)
        self.assertIn("Riesgos altos: n/d | Riesgos altos: 1 | →", md)

    def test_effort_report_never_invents_worked_hours(self):
        md = self.md(self.gen("effort"))
        self.assertIn("| electrical | 60 | 40 | 20 | 67 % |", md)               # 40 h done (node 1.1 at 100 %) of 60 h
        self.assertIn("todavía no se registran", md)
        self.assertIn("No se incluyen tarifas ni costos", md)

    def test_change_report(self):
        md = self.md(self.gen("changes"))
        self.assertIn("| Aprobados | 1 | 1 |", md)
        self.assertIn("| Abiertos | 1 | 1 |", md)
        self.assertIn("| Rechazados | 1 | 1 |", md)
        self.assertIn("| RFC-001 | Agregar tablero TS-03 | Alcance | DEC-004 | ME |", md)
        self.assertIn("| RFC-003 | Mover sala | Rechazado | DEC-005 | Fuera de alcance |", md)

    def test_english_and_period(self):
        r = self.gen("status", lang="en", period_start=iso(-10), period_end=iso(-1))
        self.assertEqual(r["period"], [iso(-10), iso(-1)])
        self.assertIn("# STATUS REPORT — STATUS-01", self.md(r))
        self.assertEqual(self.c.post(self.base, json={"type": "status", "period_start": iso(0), "period_end": iso(-1)}).status_code, 422)
        self.assertEqual(self.c.post(self.base, json={"type": "status", "period_end": "yesterday"}).status_code, 422)
        self.assertEqual(self.gen("status")["period"][0], iso(0))   # a second report the same day starts today (never after its end)

    def test_empty_project_still_produces_honest_reports(self):
        self.c.post("/api/projects", json={"client_name": "Beta", "client_code": "BETA", "project_code": "B-1", "jurisdiction": "AR", "methodology": "pm2", "disciplines": ["electrical"]})
        for kind in ("status", "progress", "risks", "effort", "changes"):
            r = self.c.post("/api/projects/BETA/B-1/reporting", json={"type": kind})
            self.assertEqual(r.status_code, 201, (kind, r.text))

    def test_publish_makes_it_visible_to_the_client_once(self):
        r = self.gen("status")
        self.assertEqual(self.c.get("/api/app/projects/ACME/P-1/reports").json(), [])
        pub = self.c.post(f"{self.base}/STATUS-01/publish")
        self.assertEqual(pub.status_code, 200, pub.text)
        self.assertEqual(pub.json()["published"], "INF-001")
        self.assertEqual(self.c.post(f"{self.base}/STATUS-01/publish").status_code, 409)
        settings.role = "user"
        reps = self.c.get("/api/app/projects/ACME/P-1/reports").json()
        self.assertEqual((reps[0]["id"], reps[0]["type"], reps[0]["downloadable"]), ("INF-001", "estado", True))
        self.assertTrue(self.c.get("/api/app/projects/ACME/P-1/reports/INF-001/download").content.startswith(b"%PDF"))
        self.assertEqual(r["summary"], reps[0]["summary"])

    def test_engineer_only(self):
        self.gen("status")
        settings.role = "auditor"            # reviews only: the engineering is for the engineering team and the organization that owns the project
        for method, path in (("get", ""), ("post", ""), ("get", "/STATUS-01/file"), ("post", "/STATUS-01/publish")):
            self.assertEqual(getattr(self.c, method)(self.base + path).status_code, 403, path)
        settings.role = "admin"
        self.assertEqual(self.c.get(f"{self.base}/STATUS-09/file").status_code, 404)
        self.assertEqual(self.c.get(f"{self.base}/STATUS-01/file?format=docx").status_code, 422)
        self.assertIn("INFORME DE ESTADO", self.c.get(f"{self.base}/STATUS-01/file?format=md").text)


if __name__ == "__main__":
    unittest.main()
