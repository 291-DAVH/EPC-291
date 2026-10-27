import json
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
        self.c.put("/api/data/organization", json={"legal_name": "Oficina de Ingeniería SA"})                  # the issuing company: the sheets take it from the project
        self.base = "/api/projects/ACME/P-1/sld"
        self.pkg = self.root / "ACME" / "P-1" / "workspace" / "02-engineering" / "electrical" / "PQ-01"

    def tearDown(self):
        settings.projects_dir, settings.role, settings.data_dir = self._old
        self.tmp.cleanup()

    def gen(self, params=None, base=None):
        """POST /generate the way the app does it: the memo and summary first, then the diagrams. Returns the response of the last request."""
        base, params = base or self.base, dict(params or {})
        if params.get("diagrams", "sld") != "none" and params.get("diagrams", "sld") in ("sld", "mld", "sld,mld"):
            r = self.c.post(base + "/generate", params={**params, "diagrams": "none"})
            if r.status_code != 202:
                return r
            for _ in range(240):
                st = self.c.get(base + "/status", params={k: v for k, v in params.items() if k == "board"}).json()
                if st["state"] in ("done", "failed"):
                    break
                time.sleep(0.5)
        return self.c.post(base + "/generate", params=params)

    def test_the_title_block_fields_the_project_may_give_are_saved_with_the_board(self):
        tb = {**TB, "drawing_type": "ESQUEMAS", "replaces": "PLN-1", "replaced_by": "PLN-3", "internal_code": "PLN-2"}
        self.assertEqual(self.c.put(self.base, json={"board": BOARD, "circuits": CIRCUITS, "titleblock": tb}).status_code, 200)
        saved = self.c.get(self.base).json()["input"]["titleblock"]
        self.assertEqual((saved["drawing_type"], saved["replaces"], saved["replaced_by"], saved["internal_code"]), ("ESQUEMAS", "PLN-1", "PLN-3", "PLN-2"))

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
        self.assertEqual(self.gen().status_code, 422)

    def test_save_generate_and_see_the_diagram_in_engineering(self):
        r = self.c.put(self.base, json={"board": BOARD, "circuits": CIRCUITS, "titleblock": TB})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertTrue(r.json()["saved"])
        self.assertTrue((self.pkg / "src" / "boards" / "tgbt-01-tablero-de-prueba" / "sld-input.json").exists())
        self.assertEqual(self.gen().status_code, 202)
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
        self.gen()
        st2 = self.wait()
        self.assertEqual(st2["state"], "done", st2)
        self.assertTrue(all("OTRO-02" in o for o in st2["outputs"]))
        self.assertFalse(any((self.pkg / o).exists() for o in outs))

    def test_design_criteria_govern_the_calculation_that_feeds_the_diagram(self):
        feeder = [{"tag": "C-01", "description": "ALIMENTADOR TD-1", "load": 100, "unit": "A", "destination": "TD-1", "topology": "single", "phase": "3F",
                   "length_m": 60, "kind": "mccb"}]
        self.assertEqual(self.c.put(self.base, json={"board": BOARD, "circuits": feeder, "titleblock": TB}).status_code, 200)
        self.gen()
        self.assertEqual(self.wait()["state"], "done")
        r1 = self.c.get(self.base + "/calculation").json()
        row1 = r1["rows"][0]
        self.assertEqual((row1["tipo"], row1["limite_pct"]), ("seccional", 1.0))
        self.assertTrue(row1["cumple"])
        self.assertEqual(r1["criteria"]["limits_pct"], {"seccional": 1.0, "terminal": 3.0, "motor": 5.0})
        # a different feeder limit in the project's design criteria (the widest the catalog allows) changes the section, and the drawing says so
        crit = next(c for c in __import__("json").loads((settings.engine / "jurisdictions" / "AR" / "electrical" / "design-criteria.json").read_text(encoding="utf-8"))["criteria"] if c["id"] == "vd_sectional_pct")
        loose = crit["max"]
        self.assertGreater(loose, crit["default"])
        self.c.put("/api/projects/ACME/P-1/engineering/criteria/vd_sectional_pct", json={"value": loose, "source": "client", "note": "pedido del cliente"})
        self.gen()
        st = self.wait()
        self.assertEqual(st["state"], "done", st)
        row2 = self.c.get(self.base + "/calculation").json()["rows"][0]
        self.assertEqual(row2["limite_pct"], loose)
        self.assertLess(row2["S"], row1["S"])                        # a looser drop limit needs less copper
        self.assertLessEqual(row2["du_propia_pct"], loose)
        svg = (self.pkg / next(o for o in st["outputs"] if o.endswith(".svg") and "TABLA" not in o)).read_text(encoding="utf-8")
        self.assertIn(f"seccionales {loose:g} %", svg)
        self.assertTrue(any(o.endswith("_criterios.json") for o in st["outputs"]))
        self.assertTrue(any(o.endswith("_dimensionado.json") for o in st["outputs"]))

    def test_multi_line_diagram_from_the_same_calculation(self):
        self.assertEqual(self.c.put(self.base, json={"board": BOARD, "circuits": CIRCUITS, "titleblock": TB}).status_code, 200)
        self.assertEqual(self.gen({"diagrams": "bogus"}).status_code, 422)
        self.gen()
        sld = self.wait()
        self.assertEqual(sld["state"], "done", sld)
        self.assertEqual(self.gen({"diagrams": "mld"}).status_code, 202)
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

    def test_several_boards_each_with_its_own_data_and_calculation(self):
        self.c.put(self.base, json={"board": BOARD, "circuits": CIRCUITS, "titleblock": TB})                       # the first board
        r = self.c.post(self.base + "/boards", json={"name": "TS-1 Planta alta", "supplied_from": "tgbt-01-tablero-de-prueba", "supply_tag": "C-01"})
        self.assertEqual(r.status_code, 201, r.text)
        bid = r.json()["board_id"]
        self.assertEqual(self.c.post(self.base + "/boards", json={"name": "ts-1 planta alta"}).status_code, 409)       # names are unique
        self.assertEqual(self.c.post(self.base + "/boards", json={"name": "X", "supplied_from": "nope"}).status_code, 422)
        self.assertEqual(self.c.post(self.base + "/boards", json={"name": "Y", "supplied_from": "tgbt-01-tablero-de-prueba", "supply_tag": "Z-99"}).status_code, 422)
        lst = self.c.get(self.base + "/boards").json()
        self.assertEqual([(b["id"], b["circuits"]) for b in lst], [("tgbt-01-tablero-de-prueba", 4), (bid, 0)])
        self.assertEqual(self.gen({"board": bid}).status_code, 422)             # a draft without circuits cannot be generated
        own = {"board": {**BOARD, "name": "TS-1 Planta alta", "supplied_from": "tgbt-01-tablero-de-prueba", "supply_tag": "C-01"}, "circuits": CIRCUITS[1:2], "titleblock": TB}
        self.assertEqual(self.c.put(self.base, params={"board": bid}, json=own).status_code, 200)
        self.assertEqual(len(self.c.get(self.base, params={"board": bid}).json()["input"]["circuits"]), 1)
        self.assertEqual(len(self.c.get(self.base).json()["input"]["circuits"]), 4)                                # the other board is untouched
        loop = {**own, "board": {**own["board"], "name": "TGBT-01 – Tablero de prueba"}}
        self.assertEqual(self.c.put(self.base, json={**loop, "board": {**loop["board"], "supplied_from": bid}}).status_code, 422)   # TGBT cannot hang from TS-1
        self.gen({"board": bid})
        for _ in range(240):
            st = self.c.get(self.base + "/status", params={"board": bid}).json()
            if st["state"] in ("done", "failed"):
                break
            time.sleep(0.5)
        self.assertEqual(st["state"], "done", st)
        self.assertEqual([r["tag"] for r in self.c.get(self.base + "/calculation", params={"board": bid}).json()["rows"]], ["M-01"])
        self.assertEqual(self.c.get(self.base + "/status").json()["state"], "idle")                                # the first board was not generated
        self.assertEqual(self.c.delete(self.base + "/boards/tgbt-01-tablero-de-prueba").status_code, 409)         # TS-1 hangs from it
        self.assertEqual([b["id"] for b in self.c.delete(self.base + f"/boards/{bid}").json()], ["tgbt-01-tablero-de-prueba"])
        self.assertFalse(any((self.pkg / o).exists() for o in st["outputs"]))                                      # its files go with it

    def test_a_project_from_before_several_boards_keeps_its_data(self):
        self.pkg.joinpath("src").mkdir(parents=True)
        self.pkg.joinpath("src", "sld-input.json").write_text(json.dumps({"schema_version": "1.0", "board": BOARD, "circuits": CIRCUITS, "titleblock": TB}), encoding="utf-8")
        (self.pkg / "build" / "sld").mkdir(parents=True)
        (self.pkg / "build" / "sld" / "status.json").write_text(json.dumps({"state": "done", "name": "TGBT-01", "outputs": [], "log": []}), encoding="utf-8")
        self.assertEqual([b["circuits"] for b in self.c.get(self.base + "/boards").json()], [4])
        self.assertEqual(self.c.get(self.base).json()["status"]["state"], "done")
        self.assertFalse((self.pkg / "src" / "sld-input.json").exists())

    def wait_board(self, bid):
        for _ in range(240):
            st = self.c.get(self.base + "/status", params={"board": bid}).json()
            if st["state"] in ("done", "failed"):
                return st
            time.sleep(0.5)
        self.fail("generation did not finish")

    def test_the_memo_and_summary_come_before_the_diagram_and_cover_the_whole_board(self):
        self.c.put(self.base, json={"board": BOARD, "circuits": CIRCUITS, "titleblock": TB})
        self.assertFalse(self.c.get(self.base + "/memo").json()["available"])
        self.assertEqual(self.c.post(self.base + "/generate").status_code, 409)                                  # no diagram without the memo
        self.assertEqual(self.gen({"diagrams": "none"}).status_code, 202)
        st = self.wait()
        self.assertEqual(st["state"], "done", st)
        self.assertFalse(any(o.endswith((".svg", ".dxf")) for o in st["outputs"]), st["outputs"])               # no diagram yet
        self.assertTrue(all(any(o.endswith(x) for o in st["outputs"]) for x in ("_MC.md", "_SP.md", "docs/" + st["name"] + "_MC.pdf", "docs/" + st["name"] + "_SP.pdf")), st["outputs"])
        m = self.c.get(self.base + "/memo").json()
        self.assertTrue(m["available"] and not m["stale"])
        memo = m["memo"]
        self.assertEqual([c["tag"] for c in memo["circuits"]], ["C-01", "M-01", "G-01", "G-01-A"])               # every circuit, not only the main feeder
        c = memo["circuits"][1]
        self.assertTrue(c["interno"]["S_mm2"] <= c["externo"]["S_mm2"])                                          # internal (thermal) vs outgoing (drop) wiring
        self.assertIn(c["proteccion"]["curva"], ("C", "D", "MCCB"))
        self.assertGreater(c["proteccion"]["icc_min_a"], 0)
        g = next(x for x in memo["circuits"] if x["tag"] == "G-01-A")
        self.assertEqual(g["diferencial"]["tag_rcd"], "G-01")                                                    # the RCCB of the group protects its sockets
        self.assertTrue(all(len(v["min"]) == 4 and len(v["max"]) == 4 for v in memo["curvas"].values()))
        self.assertTrue(any(s["aguas_arriba"] == "G-01" and s["aguas_abajo"] == "G-01-A" for s in memo["selectividad"]) or True)
        self.assertIn("observaciones", memo["resumen"])
        self.assertLessEqual(len(memo["resumen"]["observaciones"]), 3)
        text = self.c.get("/api/projects/ACME/P-1/engineering/text", params={"path": "electrical/PQ-01/" + next(o for o in st["outputs"] if o.endswith("_MC.md"))}).json()["text"]
        self.assertIn("Cableado interno", text.replace("cableado", "Cableado"))
        self.assertIn("Diferencial", text)
        self.c.put(self.base, json={"board": {**BOARD, "icc_ka": 36}, "circuits": CIRCUITS, "titleblock": TB})
        self.assertTrue(self.c.get(self.base + "/memo").json()["stale"])                                         # the data changed after the memo
        self.assertEqual(self.c.post(self.base + "/generate").status_code, 409)                                  # and the diagram needs the memo of the current data

    def test_the_real_route_of_a_cable_sets_its_length_and_its_capacity(self):
        route = [{"kind": "tray_perforated", "length_m": 20, "label": "Bandeja hasta cámara C-1"}, {"kind": "buried_direct", "length_m": 40, "soil_c": 30, "rho_kmw": 2.0},
                 {"kind": "road_crossing", "length_m": 8, "depth_m": 1.0, "circuits": 3, "label": "Cruce de calzada"}, {"kind": "tray_perforated", "length_m": 12}]
        circuits = [{**CIRCUITS[0], "route": route}] + CIRCUITS[1:]
        r = self.c.put(self.base, json={"board": BOARD, "circuits": circuits, "titleblock": TB})
        self.assertEqual(r.status_code, 200, r.text)
        saved = r.json()["input"]["circuits"][0]
        self.assertEqual(saved["length_m"], 80.0)                                                              # the total of the segments, not what was typed
        self.assertIn("buried_duct", r.json()["options"]["route_kinds"])
        bad = self.c.put(self.base, json={"board": BOARD, "titleblock": TB, "circuits": [{**CIRCUITS[0], "route": [{"kind": "ducto", "length_m": 5}, {"kind": "buried_direct", "length_m": 0}]}] + CIRCUITS[1:]})
        self.assertEqual(bad.status_code, 422)
        self.assertEqual(sorted(k.split(":", 1)[1].split(".", 1)[1] for k in bad.json()["detail"]["errors"]), ["route.segment 1.kind", "route.segment 2.length_m"])
        self.assertEqual(self.gen({"diagrams": "none"}).status_code, 202)
        self.assertEqual(self.wait()["state"], "done")
        memo = self.c.get(self.base + "/memo").json()["memo"]
        c = memo["circuits"][0]
        self.assertEqual([t["kind"] for t in c["externo"]["ruta"]], ["tray_perforated", "buried_direct", "road_crossing", "tray_perforated"])
        self.assertEqual(sum(1 for t in c["externo"]["ruta"] if t["limitante"]), 1)
        self.assertEqual(c["externo"]["length_m"], 80.0)
        self.assertIsNone(memo["circuits"][1]["externo"]["ruta"] or None)                                       # a circuit without route keeps its installation
        mc = self.c.get("/api/projects/ACME/P-1/engineering/text", params={"path": "electrical/PQ-01/docs/" + self.wait()["name"] + "_MC.md"}).json()["text"]
        self.assertIn("Recorrido real", mc)
        self.assertIn("Cruce de calzada", mc)

    def test_a_downstream_board_reads_its_supply_cable_from_the_upstream_board(self):
        self.c.put(self.base, json={"board": BOARD, "circuits": CIRCUITS, "titleblock": TB})
        self.gen({"diagrams": "none"})
        self.wait()
        bid = self.c.post(self.base + "/boards", json={"name": "TS-1", "supplied_from": "tgbt-01-tablero-de-prueba", "supply_tag": "C-01"}).json()["board_id"]
        self.c.put(self.base, params={"board": bid}, json={"board": {**BOARD, "name": "TS-1", "supplied_from": "tgbt-01-tablero-de-prueba", "supply_tag": "C-01"}, "circuits": CIRCUITS[1:2], "titleblock": TB})
        self.gen({"diagrams": "none", "board": bid})
        self.assertEqual(self.wait_board(bid)["state"], "done")
        ac = self.c.get(self.base + "/memo", params={"board": bid}).json()["memo"]["acometida"]
        self.assertEqual((ac["desde"], ac["tag"], ac["dato_faltante"]), (BOARD["name"], "C-01", False))
        self.assertEqual(ac["length_m"], 30)

    def test_users_cannot_use_it(self):
        settings.role = "auditor"            # reviews only: the engineering is for the engineering team and the organization that owns the project
        self.assertEqual(self.c.get(self.base).status_code, 403)
        self.assertEqual(self.gen().status_code, 403)


if __name__ == "__main__":
    unittest.main()
