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

    def test_users_cannot_see_the_workspace(self):
        settings.role = "user"
        self.assertEqual(self.c.get(self.base).status_code, 403)
        self.assertEqual(self.c.get(self.base + "/svg", params={"path": "x.svg"}).status_code, 403)


if __name__ == "__main__":
    unittest.main()
