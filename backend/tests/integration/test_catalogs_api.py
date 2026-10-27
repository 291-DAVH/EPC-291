"""The catalogs of drawing at three levels: the MASTER's (global), the company's and the project's. The nearest level wins and each stores only its own changes."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

from epc.core.config import settings
from epc.core.fsutil import read_json, write_json
from epc.main import create_app
from epc.modules.catalogs import public as catalogs
from epc.modules.identity import public as identity
from epc.modules.projects import public as projects

PROJECT = "/api/projects/ACME/P-1"


class TestCatalogLevels(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._old = (settings.projects_dir, settings.role, settings.data_dir)
        settings.projects_dir, settings.role, settings.data_dir = self.root, "admin", self.root / "_data"
        self.c = TestClient(create_app())
        self.c.post("/api/projects", json={"client_name": "Acme SA", "client_code": "ACME", "project_code": "P-1", "project_name": "Planta",
                                           "jurisdiction": "AR", "methodology": "pm2", "disciplines": ["electrical"]})
        self.d = projects.get_project_dir("ACME", "P-1")
        meta = self.d / ".epc" / "project.json"
        write_json(meta, {**read_json(meta, {}), "org": "acme-co"})                   # the project belongs to a company
        patcher = mock.patch.object(identity, "active_org_slug", return_value="acme-co")
        patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        settings.projects_dir, settings.role, settings.data_dir = self._old
        self.tmp.cleanup()

    def name_of(self, view):
        return view["layers"]["sld.diagram"]["name"]

    def test_the_nearest_level_wins_and_each_stores_only_its_own_changes(self):
        self.c.put("/api/layers", json={"layers": {"sld.diagram": {"name": "GLOBAL", "color": 3}}})
        company = self.c.put("/api/data/drawing-layers", json={"layers": {"sld.diagram": {"name": "EMPRESA"}}}).json()
        self.assertEqual((self.name_of(company), company["layers"]["sld.diagram"]["color"], company["inherits"]), ("EMPRESA", 3, "global"))
        project = self.c.get(f"{PROJECT}/drawing-layers").json()
        self.assertEqual((self.name_of(project), project["changed"]), ("EMPRESA", []))                       # it follows the company until it changes something
        mine = self.c.put(f"{PROJECT}/drawing-layers", json={"layers": {"sld.diagram": {"name": "PROYECTO", "color": 3, "lineweight": 0.5}}}).json()
        self.assertEqual((self.name_of(mine), mine["changed"]), ("PROYECTO", ["sld.diagram"]))
        stored = json.loads(catalogs.files(self.d)["layers"][-1].read_text(encoding="utf-8"))["layers"]
        self.assertEqual(stored, {"sld.diagram": {"name": "PROYECTO", "lineweight": 0.5}})                  # color 3 comes from above: not stored again
        self.assertEqual(self.name_of(self.c.get("/api/data/drawing-layers").json()), "EMPRESA")             # the company is not changed by its project
        self.assertEqual(self.name_of(self.c.get("/api/layers").json()), "GLOBAL")
        reset = self.c.delete(f"{PROJECT}/drawing-layers").json()
        self.assertEqual((self.name_of(reset), reset["changed"]), ("EMPRESA", []))

    def test_the_engine_is_told_the_files_in_order_of_authority(self):
        files = catalogs.files(self.d)
        self.assertEqual([p.parent.name for p in files["layers"]], ["global", "acme-co", "00-setup"])
        self.assertEqual(files["solutions"][-1].name, "standard-solutions.json")
        self.assertEqual(len(catalogs.files()["layers"]), 1)                                                 # nothing in particular: the global one

    def test_wrong_values_are_refused_at_any_level(self):
        bad = self.c.put(f"{PROJECT}/drawing-layers", json={"layers": {"sld.text": {"color": 999}}})
        self.assertEqual(bad.status_code, 422)
        self.assertEqual(self.c.put("/api/data/drawing-layers", json={"layers": {"nope.x": {"name": "X"}}}).status_code, 422)
        self.assertFalse(catalogs.files(self.d)["layers"][-1].exists())

    def test_a_company_level_request_needs_a_company(self):
        with mock.patch.object(identity, "active_org_slug", return_value=""):
            self.assertEqual(self.c.get("/api/data/drawing-layers").status_code, 422)

    def test_standard_solutions_follow_the_same_rule_and_change_what_the_calculation_is_made_with(self):
        before = catalogs.solutions_digest(self.d)
        base = self.c.get(f"{PROJECT}/standard-solutions").json()
        doc = {"solutions": copy.deepcopy(base["solutions"]), "add_ons": base["add_ons"]}
        doc["solutions"]["lighting-differential-mcb"]["enabled"] = True
        mine = self.c.put(f"{PROJECT}/standard-solutions", json=doc).json()
        self.assertEqual(mine["changed"], ["lighting-differential-mcb"])
        self.assertNotEqual(catalogs.solutions_digest(self.d), before)                                       # the memo of this project is stale
        self.assertEqual(self.c.get("/api/data/standard-solutions").json()["changed"], [])    # the company is untouched
        self.assertEqual(self.c.get("/api/solutions").json()["changed"], [])
        self.c.delete(f"{PROJECT}/standard-solutions")
        self.assertEqual(catalogs.solutions_digest(self.d), before)

    def test_every_change_at_every_level_leaves_a_record(self):
        self.c.put("/api/data/drawing-layers", json={"layers": {"sld.diagram": {"name": "EMPRESA"}}})
        self.c.put(f"{PROJECT}/drawing-layers", json={"layers": {"sld.diagram": {"name": "PROYECTO"}}})
        self.c.delete(f"{PROJECT}/drawing-layers")
        events = self.c.get("/api/identity/audit", params={"limit": 50}).json()
        seen = {(e["action"], e["target"]) for e in events}
        self.assertTrue({("drawing_layers_changed", "company:acme-co"), ("drawing_layers_changed", projects.project_id(self.d)), ("drawing_layers_reset", projects.project_id(self.d))} <= seen)


if __name__ == "__main__":
    unittest.main()
