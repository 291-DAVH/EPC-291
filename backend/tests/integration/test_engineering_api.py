"""Engineering tab: SVG previews and text lists, admin/engineer role only."""
import tempfile
import unittest
from pathlib import Path

import openpyxl
from fastapi.testclient import TestClient

from epc.core.config import settings
from epc.main import create_app

SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><script>alert(1)</script><rect width="10" height="10"/></svg>'


class TestEngineering(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._old = (settings.projects_dir, settings.role)
        settings.projects_dir, settings.role = self.root, "admin"
        self.c = TestClient(create_app())
        r = self.c.post("/api/projects", json={"client_name": "Acme SA", "client_code": "ACME", "project_code": "P-1", "project_name": "Planta",
                                                "jurisdiction": "AR", "methodology": "pm2", "disciplines": ["electrical"]})
        self.assertEqual(r.status_code, 201, r.text)
        eng = self.root / "ACME" / "P-1" / "workspace" / "02-engineering" / "electrical" / "PQ-01"
        (eng / "drawings" / "svg").mkdir(parents=True)
        (eng / "calc").mkdir()
        (eng / "docs").mkdir()
        (eng / "drawings" / "svg" / "SLD-tablero-general.svg").write_text(SVG, encoding="utf-8")
        (eng / "drawings" / "svg" / "MLD-tablero-general.svg").write_text(SVG, encoding="utf-8")
        (eng / "drawings" / "svg" / "layout.svg").write_text(SVG, encoding="utf-8")
        (eng / "drawings" / "dxf").mkdir()
        (eng / "drawings" / "dxf" / "x.dxf").write_text("0\nEOF\n", encoding="utf-8")
        (eng / "calc" / "cargas.csv").write_text("circuito;potencia\nC1;1200\nC2;800\n", encoding="utf-8")
        (eng / "docs" / "criterios.md").write_text("# Criterios\n\nCaída máxima 3 %.\n", encoding="utf-8")
        wb = openpyxl.Workbook()
        wb.active.title = "Cables"
        wb.active.append(["id", "sección"])
        wb.active.append(["C1", 2.5])
        wb.save(eng / "calc" / "cables.xlsx")
        self.base = "/api/projects/ACME/P-1/engineering"

    def tearDown(self):
        settings.projects_dir, settings.role = self._old
        self.tmp.cleanup()

    def test_overview_classifies_files(self):
        o = self.c.get(self.base).json()
        kinds = {d["name"]: d["kind"] for d in o["diagrams"]}
        self.assertEqual(kinds, {"SLD-tablero-general": "single_line", "MLD-tablero-general": "multi_line", "layout": "drawing"})
        self.assertEqual({d["name"]: d["kind"] for d in o["documents"]}, {"cargas": "list", "cables": "list", "criterios": "text"})
        self.assertEqual(o["counts"]["by_kind"], {"single_line": 1, "multi_line": 1, "drawing": 1})
        self.assertNotIn("x", [d["name"] for d in o["diagrams"] + o["documents"]])      # DXF is not listed

    def test_svg_is_served_sandboxed(self):
        r = self.c.get(self.base + "/svg", params={"path": "electrical/PQ-01/drawings/svg/SLD-tablero-general.svg"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers["content-type"], "image/svg+xml")
        self.assertIn("sandbox", r.headers["content-security-policy"])
        self.assertEqual(r.headers["x-content-type-options"], "nosniff")

    def test_text_views(self):
        p = "electrical/PQ-01/"
        t = self.c.get(self.base + "/text", params={"path": p + "calc/cargas.csv"}).json()
        self.assertEqual((t["format"], t["rows"][1]), ("table", ["C1", "1200"]))
        m = self.c.get(self.base + "/text", params={"path": p + "docs/criterios.md"}).json()
        self.assertEqual(m["format"], "text")
        self.assertIn("Caída máxima", m["text"])
        x = self.c.get(self.base + "/text", params={"path": p + "calc/cables.xlsx"}).json()
        self.assertEqual((x["format"], x["sheets"]["Cables"][1]), ("sheets", ["C1", "2.5"]))

    def test_paths_are_restricted(self):
        for params in ({"path": "../../../project.json"}, {"path": "electrical/PQ-01/drawings/dxf/x.dxf"}, {"path": "nope.svg"}, {"path": ""}):
            self.assertIn(self.c.get(self.base + "/svg", params=params).status_code, (404, 422), params)
        for params in ({"path": "electrical/PQ-01/drawings/svg/layout.svg"}, {"path": "../../../.epc/project.json"}, {"path": "electrical/PQ-01/calc/missing.csv"}):
            self.assertIn(self.c.get(self.base + "/text", params=params).status_code, (404, 422), params)

    def test_data_files_are_hidden_and_the_calculation_reads_as_a_table(self):
        import json
        calc = self.root / "ACME" / "P-1" / "workspace" / "02-engineering" / "electrical" / "PQ-01" / "calc"
        dump = lambda n, o: (calc / n).write_text(json.dumps(o), encoding="utf-8")
        dump("TG_dimensionado.json", {"C1": {"In": 16, "Ib": 12.0, "icu": 6, "S": 2.5, "dU": 1.2, "disp": "MCB 16 A"}, "C2": {"In": 10, "Ib": 9.0, "icu": 6, "S": 1.5, "dU": 4.1, "disp": "MCB 10 A"}})
        dump("TG_dimensionado_detalle.json", {"C1": {"descripcion": "Luces", "tipo": "iluminacion", "limite_pct": 3, "du_propia_pct": 1.2, "iz_a": 20, "cumple": True},
                                              "C2": {"descripcion": "Tomas", "tipo": "tomacorrientes", "limite_pct": 3, "du_propia_pct": 4.1, "iz_a": 14, "cumple": False}})
        dump("TG_criterios.json", {"limites_pct": {"seccional": 1, "terminal": 3, "motor": 5}, "conductor": {"material": "cu", "aislacion": "pvc"}, "rcd_ma": 30})
        dump("SLD_TG_H1_calculo.json", {"x": 1})
        o = self.c.get(self.base).json()
        names = {d["name"]: d["kind"] for d in o["documents"]}
        self.assertEqual(names["TG"], "calculation")
        self.assertEqual([n for n in names if n.startswith(("TG_", "SLD_TG"))], [])      # internal formats are not listed
        self.assertIn("TG_criterios", [d["name"] for d in self.c.get(self.base, params={"technical": "true"}).json()["documents"]])
        p = "electrical/PQ-01/calc/"
        v = self.c.get(self.base + "/calculation", params={"path": p + "TG_dimensionado.json"}).json()
        self.assertEqual(v["summary"], {"circuits": 2, "compliant": 1, "non_compliant": 1})
        self.assertEqual((v["rows"][0]["description"], v["rows"][1]["cumple"], v["criteria"]["limits_pct"]["terminal"]), ("Luces", False, 3))
        self.assertEqual(self.c.get(self.base + "/text", params={"path": p + "TG_criterios.json"}).status_code, 404)             # raw JSON is not a view
        self.assertEqual(self.c.get(self.base + "/text", params={"path": p + "TG_criterios.json", "technical": "true"}).status_code, 200)
        self.assertEqual(self.c.get(self.base + "/calculation", params={"path": p + "cargas.csv"}).status_code, 422)

    def test_users_cannot_see_the_workspace(self):
        settings.role = "auditor"            # reviews only: the engineering is for the engineering team and the organization that owns the project
        self.assertEqual(self.c.get(self.base).status_code, 403)
        self.assertEqual(self.c.get(self.base + "/svg", params={"path": "x.svg"}).status_code, 403)


if __name__ == "__main__":
    unittest.main()
