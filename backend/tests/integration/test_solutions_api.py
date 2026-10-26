"""The document of standard solutions: the MASTER reads and changes it in the console, and the calculation and the drawings use it."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

import ezdxf  # noqa: F401  (the delivered DXF is read by other tests; kept to fail early if the engine is missing)
from fastapi.testclient import TestClient

from epc.core.config import settings
from epc.main import create_app


class TestSolutions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._old = (settings.projects_dir, settings.role, settings.data_dir)
        settings.projects_dir, settings.role, settings.data_dir = self.root, "admin", self.root / "_data"
        self.c = TestClient(create_app())

    def tearDown(self):
        settings.projects_dir, settings.role, settings.data_dir = self._old
        self.tmp.cleanup()

    def test_the_default_document_is_offered_with_the_symbols_of_the_library(self):
        v = self.c.get("/api/solutions").json()
        self.assertEqual(v["changed"], [])
        self.assertIn("motor-dol-ol", v["solutions"])
        self.assertFalse(v["solutions"]["lighting-differential-mcb"]["enabled"])
        ids = {s["id"] for s in v["symbols"]}
        self.assertTrue({"lv_mcb", "lv_rccb", "lv_contactor"} <= ids)
        self.assertIn("rated_current", [x["key"] for x in next(s for s in v["symbols"] if s["id"] == "lv_rccb")["slots"]])

    def test_a_change_is_stored_as_a_difference_and_a_reset_goes_back_to_the_default(self):
        v = self.c.get("/api/solutions").json()
        doc = {"solutions": copy.deepcopy(v["solutions"]), "add_ons": v["add_ons"]}
        doc["solutions"]["lighting-differential-mcb"]["enabled"] = True
        out = self.c.put("/api/solutions", json=doc).json()
        self.assertEqual(out["changed"], ["lighting-differential-mcb"])
        stored = json.loads(settings.solutions_file.read_text(encoding="utf-8"))
        self.assertEqual(set(stored["solutions"]), {"lighting-differential-mcb"})
        back = self.c.delete("/api/solutions").json()
        self.assertEqual(back["changed"], [])
        self.assertFalse(settings.solutions_file.exists())

    def test_a_removed_solution_is_stored_as_null_and_a_document_without_a_last_resort_is_refused(self):
        v = self.c.get("/api/solutions").json()
        doc = {"solutions": {i: s for i, s in v["solutions"].items() if i != "motor-vfd"}, "add_ons": v["add_ons"]}
        out = self.c.put("/api/solutions", json=doc).json()
        self.assertNotIn("motor-vfd", out["solutions"])
        self.assertEqual(json.loads(settings.solutions_file.read_text(encoding="utf-8"))["solutions"], {"motor-vfd": None})
        bare = {"solutions": {i: s for i, s in v["solutions"].items() if s["when"]}, "add_ons": {}}
        refused = self.c.put("/api/solutions", json=bare)
        self.assertEqual(refused.status_code, 422)
        self.assertIn("solutions", refused.json()["detail"]["errors"])

    def test_an_unknown_symbol_and_a_wrong_value_are_refused_and_nothing_is_stored(self):
        v = self.c.get("/api/solutions").json()
        doc = {"solutions": copy.deepcopy(v["solutions"]), "add_ons": {}}
        doc["solutions"]["circuit-mcb"]["chain"][0]["symbol"] = "lv_does_not_exist"
        doc["solutions"]["motor-vfd"]["priority"] = "high"
        refused = self.c.put("/api/solutions", json=doc)
        self.assertEqual(refused.status_code, 422)
        self.assertTrue({"solutions.circuit-mcb.chain[0].symbol", "solutions.motor-vfd.priority"} <= set(refused.json()["detail"]["errors"]))
        self.assertFalse(settings.solutions_file.exists())

    def test_the_board_calculation_uses_the_document_of_the_master(self):
        from tests.integration.test_sld_api import BOARD, CIRCUITS, TB
        self.c.put("/api/data/organization", json={"legal_name": "Oficina SA"})
        self.c.post("/api/projects", json={"client_name": "Acme SA", "client_code": "ACME", "project_code": "P-1", "project_name": "Planta",
                                           "jurisdiction": "AR", "methodology": "pm2", "disciplines": ["electrical"]})
        circuits = [{**c, "description": "ILUMINACION", "kind": "auto", "length_m": 10} if c["tag"] == "G-01-A" else c for c in CIRCUITS]
        self.c.put("/api/projects/ACME/P-1/sld", json={"board": BOARD, "circuits": circuits, "titleblock": TB})

        def disp():
            r = self.c.post("/api/projects/ACME/P-1/sld/generate", params={"diagrams": "none"})
            self.assertEqual(r.status_code, 202, r.text)
            import time
            for _ in range(240):
                st = self.c.get("/api/projects/ACME/P-1/sld/status").json()
                if st["state"] in ("done", "failed"):
                    break
                time.sleep(0.5)
            self.assertEqual(st["state"], "done", st)
            rows = self.c.get("/api/projects/ACME/P-1/sld/calculation").json()["rows"]
            return next(r for r in rows if r["tag"] == "G-01-A")["disp"]
        self.assertEqual(disp(), "MCB (13 A)")
        v = self.c.get("/api/solutions").json()
        doc = {"solutions": copy.deepcopy(v["solutions"]), "add_ons": v["add_ons"]}
        doc["solutions"]["lighting-differential-mcb"]["enabled"] = True
        self.c.put("/api/solutions", json=doc)
        self.assertEqual(disp(), "RCCB > MCB (13 A)")

    def test_the_rules_of_groups_are_edited_like_the_rest_and_put_the_circuits_behind_a_differential(self):
        from tests.integration.test_sld_api import BOARD, TB
        self.c.put("/api/data/organization", json={"legal_name": "Oficina SA"})
        self.c.post("/api/projects", json={"client_name": "Acme SA", "client_code": "ACME", "project_code": "P-1", "project_name": "Planta",
                                           "jurisdiction": "AR", "methodology": "pm2", "disciplines": ["electrical"]})
        lights = [{"tag": f"L-{i:02d}", "description": "ILUMINACION", "load": 1.0, "unit": "kW", "destination": "", "parent_tag": "", "topology": "single", "phase": "1F", "length_m": 15, "kind": "auto"}
                  for i in range(1, 4)]
        self.c.put("/api/projects/ACME/P-1/sld", json={"board": BOARD, "circuits": lights, "titleblock": TB})
        v = self.c.get("/api/solutions").json()
        self.assertFalse(v["groups"]["differential-lighting"]["enabled"])
        doc = {"solutions": v["solutions"], "add_ons": v["add_ons"], "groups": copy.deepcopy(v["groups"])}
        doc["groups"]["differential-lighting"]["enabled"] = True
        out = self.c.put("/api/solutions", json=doc).json()
        self.assertEqual(out["changed"], ["differential-lighting"])
        bad = copy.deepcopy(doc)
        bad["groups"]["differential-lighting"]["max_circuits"] = 0
        self.assertEqual(self.c.put("/api/solutions", json=bad).status_code, 422)
        import time
        self.assertEqual(self.c.post("/api/projects/ACME/P-1/sld/generate", params={"diagrams": "none"}).status_code, 202)
        for _ in range(240):
            st = self.c.get("/api/projects/ACME/P-1/sld/status").json()
            if st["state"] in ("done", "failed"):
                break
            time.sleep(0.5)
        self.assertEqual(st["state"], "done", st)
        rows = {r["tag"]: r for r in self.c.get("/api/projects/ACME/P-1/sld/calculation").json()["rows"]}
        self.assertEqual(rows["GD-L01"]["description"], "Diferencial de iluminación 1")
        self.assertTrue(rows["GD-L01"]["disp"].startswith("RCCB"))


if __name__ == "__main__":
    unittest.main()
