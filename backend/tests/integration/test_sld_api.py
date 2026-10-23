"""SLD data entry and generation (runs the real plugin generator on a small board)."""
import tempfile
import time
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from epc.core.config import settings
from epc.main import create_app

BOARD = {"name": "TGBT-01 – Tablero de prueba", "voltage_v": 380, "system": "TN-S", "icc_ka": 25, "fp_default": 0.85, "frequency_hz": 50,
         "project": "PRJ-1", "feeder_length_m": 20}
CIRCUITS = [
    {"tag": "C-01", "description": "ALIMENTADOR TD-1", "load": 63, "unit": "A", "destination": "TD-1", "topology": "single", "phase": "3F", "length_m": 30, "kind": "mccb"},
    {"tag": "M-01", "description": "EXTRACTOR EXT-01", "load": 7.5, "unit": "kW", "destination": "EXT-01", "topology": "dol", "phase": "3F", "length_m": 25, "fp": 0.85, "efficiency": 0.9},
    {"tag": "G-01", "description": "RCCB TOMAS", "load": None, "unit": "A", "destination": "TOMAS", "topology": "single", "phase": "3F", "kind": "rccb"},
    {"tag": "G-01-A", "description": "Tomas 1", "load": 2.2, "unit": "kW", "destination": "TOMAS 1", "parent_tag": "G-01", "topology": "single", "phase": "1F", "length_m": 15, "kind": "mcb"},
]
TB = {"company": "Oficina de Ingeniería SA", "client": "Acme SA", "drawn_by": "D. Villena", "description": "Planta"}


class TestSld(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._old = (settings.projects_dir, settings.role, settings.data_dir)
        settings.projects_dir, settings.role, settings.data_dir = self.root, "admin", self.root / "_data"
        self.c = TestClient(create_app())
        r = self.c.post("/api/projects", json={"client_name": "Acme SA", "client_code": "ACME", "project_code": "P-1", "project_name": "Planta",
                                                "jurisdiction": "AR", "methodology": "pm2", "disciplines": ["electrical"]})
        self.assertEqual(r.status_code, 201, r.text)
        self.base = "/api/projects/ACME/P-1/sld"
        self.pkg = self.root / "ACME" / "P-1" / "workspace" / "02-engineering" / "electrical" / "PQ-01"

    def tearDown(self):
        settings.projects_dir, settings.role, settings.data_dir = self._old
        self.tmp.cleanup()

    def wait(self):
        for _ in range(240):
            st = self.c.get(self.base + "/status").json()
            if st["state"] in ("done", "failed"):
                return st
            time.sleep(0.5)
        self.fail("generation did not finish")

    def test_defaults_use_the_project_and_the_design_criteria(self):
        self.c.put("/api/projects/ACME/P-1/engineering/criteria/nominal_voltage_v", json={"value": 400, "source": "client"})
        v = self.c.get(self.base).json()
        self.assertFalse(v["saved"])
        self.assertEqual((v["input"]["board"]["voltage_v"], v["input"]["board"]["project"], v["input"]["titleblock"]["client"]), (400, "P-1", "Acme SA"))
        self.assertIn("dol_ol", v["options"]["topologies"])

    def test_example_comes_from_the_plugin_workbook(self):
        ex = self.c.get(self.base + "/example").json()
        self.assertGreater(len(ex["circuits"]), 20)
        self.assertEqual(ex["board"]["system"], "TN-S")

    def test_validation(self):
        bad = [({"board": {**BOARD, "name": " "}}, "board.name"), ({"board": {**BOARD, "voltage_v": 5}}, "board.voltage_v"),
               ({"circuits": []}, "circuits"),
               ({"circuits": [{**CIRCUITS[0], "tag": "A,B"}]}, "circuit:A,B.tag"),
               ({"circuits": [CIRCUITS[0], CIRCUITS[0]]}, "circuit:C-01.tag"),
               ({"circuits": [{**CIRCUITS[0], "unit": "BTU"}]}, "circuit:C-01.unit"),
               ({"circuits": [{**CIRCUITS[0], "load": None}]}, "circuit:C-01.load"),
               ({"circuits": [{**CIRCUITS[0], "parent_tag": "NOPE"}]}, "circuit:C-01.parent_tag"),
               ({"circuits": [{**CIRCUITS[0], "tag": "A", "parent_tag": "B"}, {**CIRCUITS[1], "tag": "B", "parent_tag": "A"}]}, "circuits")]
        for patch, key in bad:
            body = {"board": BOARD, "circuits": CIRCUITS, "titleblock": TB, **patch}
            r = self.c.put(self.base, json=body)
            self.assertEqual(r.status_code, 422, key)
            self.assertIn(key, r.json()["detail"]["errors"])

    def test_generate_requires_saved_data(self):
        self.assertEqual(self.c.post(self.base + "/generate").status_code, 422)

    def test_save_generate_and_see_the_diagram_in_engineering(self):
        r = self.c.put(self.base, json={"board": BOARD, "circuits": CIRCUITS, "titleblock": TB})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertTrue(r.json()["saved"])
        self.assertTrue((self.pkg / "src" / "sld-input.json").exists())
        self.assertEqual(self.c.post(self.base + "/generate").status_code, 202)
        st = self.wait()
        self.assertEqual(st["state"], "done", st)
        outs = st["outputs"]
        self.assertTrue(all(any(o.endswith(ext) for o in outs) for ext in (".svg", ".dxf", ".pdf")), outs)
        for o in outs:
            self.assertTrue((self.pkg / o).exists(), o)
        ov = self.c.get("/api/projects/ACME/P-1/engineering").json()
        self.assertTrue(any(d["kind"] == "single_line" for d in ov["diagrams"]))
        svg = self.c.get("/api/projects/ACME/P-1/engineering/svg", params={"path": "electrical/PQ-01/" + next(o for o in outs if o.endswith(".svg"))})
        self.assertEqual(svg.status_code, 200)
        self.assertIn("Oficina de Ingeniería SA", svg.text)        # titleblock data entered in the form reaches the drawing
        # a new run replaces the previous files (different board name -> different file names)
        self.c.put(self.base, json={"board": {**BOARD, "name": "OTRO-02"}, "circuits": CIRCUITS, "titleblock": TB})
        self.c.post(self.base + "/generate")
        st2 = self.wait()
        self.assertEqual(st2["state"], "done", st2)
        self.assertTrue(all("OTRO-02" in o for o in st2["outputs"]))
        self.assertFalse(any((self.pkg / o).exists() for o in outs))

    def test_design_criteria_govern_the_calculation_that_feeds_the_diagram(self):
        feeder = [{"tag": "C-01", "description": "ALIMENTADOR TD-1", "load": 100, "unit": "A", "destination": "TD-1", "topology": "single", "phase": "3F",
                   "length_m": 60, "kind": "mccb"}]
        self.assertEqual(self.c.put(self.base, json={"board": BOARD, "circuits": feeder, "titleblock": TB}).status_code, 200)
        self.c.post(self.base + "/generate")
        self.assertEqual(self.wait()["state"], "done")
        r1 = self.c.get(self.base + "/calculation").json()
        row1 = r1["rows"][0]
        self.assertEqual((row1["tipo"], row1["limite_pct"]), ("seccional", 1.0))
        self.assertTrue(row1["cumple"])
        self.assertEqual(r1["criteria"]["limits_pct"], {"seccional": 1.0, "terminal": 3.0, "motor": 5.0})
        # a tighter feeder limit in the project's design criteria needs more copper, and the drawing says so
        self.c.put("/api/projects/ACME/P-1/engineering/criteria/vd_sectional_pct", json={"value": 0.5, "source": "client", "note": "pedido del cliente"})
        self.c.post(self.base + "/generate")
        st = self.wait()
        self.assertEqual(st["state"], "done", st)
        row2 = self.c.get(self.base + "/calculation").json()["rows"][0]
        self.assertEqual(row2["limite_pct"], 0.5)
        self.assertGreater(row2["S"], row1["S"])
        self.assertLessEqual(row2["du_propia_pct"], 0.5)
        svg = (self.pkg / next(o for o in st["outputs"] if o.endswith(".svg") and "TABLA" not in o)).read_text(encoding="utf-8")
        self.assertIn("seccionales 0.5 %", svg)
        self.assertTrue(any(o.endswith("_criterios.json") for o in st["outputs"]))
        self.assertTrue(any(o.endswith("_dimensionado.json") for o in st["outputs"]))

    def test_multi_line_diagram_from_the_same_calculation(self):
        self.assertEqual(self.c.put(self.base, json={"board": BOARD, "circuits": CIRCUITS, "titleblock": TB}).status_code, 200)
        self.assertEqual(self.c.post(self.base + "/generate", params={"diagrams": "bogus"}).status_code, 422)
        self.c.post(self.base + "/generate")
        sld = self.wait()
        self.assertEqual(sld["state"], "done", sld)
        self.assertEqual(self.c.post(self.base + "/generate", params={"diagrams": "mld"}).status_code, 202)
        st = self.wait()
        self.assertEqual(st["state"], "done", st)
        outs = st["outputs"]
        self.assertTrue(any("/SLD_" in o and o.endswith(".dxf") for o in outs), outs)                     # the SLD of the earlier run is kept
        for ext in (".svg", ".dxf", ".pdf"):
            self.assertTrue(any("/MLD_" in o and o.endswith(ext) for o in outs), (ext, outs))
        for o in outs:
            self.assertTrue((self.pkg / o).exists(), o)
        ov = self.c.get("/api/projects/ACME/P-1/engineering").json()
        kinds = {d["name"]: d["kind"] for d in ov["diagrams"]}
        self.assertTrue(any(k == "multi_line" for k in kinds.values()) and any(k == "single_line" for k in kinds.values()), kinds)
        mld = next(o for o in outs if "/MLD_" in o and o.endswith(".svg"))
        svg = (self.pkg / mld).read_text(encoding="utf-8")
        self.assertIn("multifilar", svg)
        self.assertIn("Oficina de Ingeniería SA", svg)                                                    # same titleblock as the SLD
        for tag in ("C-01", "M-01", "G-01-A"):
            self.assertIn(tag, svg)

    def test_users_cannot_use_it(self):
        settings.role = "user"
        self.assertEqual(self.c.get(self.base).status_code, 403)
        self.assertEqual(self.c.post(self.base + "/generate").status_code, 403)


if __name__ == "__main__":
    unittest.main()
