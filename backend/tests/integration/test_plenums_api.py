"""The board says its level and its place, and a plenum (vertical shaft) crosses the levels it is told to: its node is in the electrical sheet of each, also of the levels made afterwards."""
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from epc.core.config import settings
from epc.main import create_app
from epc.modules.layout import plenums

SCALE = {"p1": [0, 0], "p2": [100, 0], "distance_m": 10}                                                  # one unit is 0.1 m
ARCH = {"discipline": "arquitectura", "scale": SCALE, "origin": [0, 0], "nodes": [], "lines": [], "circuits": []}
ELEC = {"discipline": "electrica_BT", "scale": None, "origin": [0, 0], "nodes": [], "lines": [], "circuits": []}
PLENUM = {"code": "PL-1", "discipline": "electrica_BT", "level": "L-1", "x_m": 5.0, "y_m": 2.0, "altura_m": 3.0, "up": None, "down": None}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._old = (settings.projects_dir, settings.role, settings.data_dir)
        settings.projects_dir, settings.role, settings.data_dir = self.root, "admin", self.root / "_data"
        self.c = TestClient(create_app())
        r = self.c.post("/api/projects", json={"client_name": "Acme SA", "client_code": "ACME", "project_code": "P-1", "project_name": "Planta",
                                                "jurisdiction": "AR", "methodology": "pm2", "disciplines": ["electrical"]})
        self.assertEqual(r.status_code, 201, r.text)
        self.layout = "/api/projects/ACME/P-1/layout"
        self.sld = "/api/projects/ACME/P-1/sld"

    def tearDown(self):
        settings.projects_dir, settings.role, settings.data_dir = self._old
        self.tmp.cleanup()

    def levels(self, *names):
        """Architecture sheets of the levels (the first one carries the scale of the plan) and the electrical sheet of the first level named."""
        for name in names:
            self.assertEqual(self.c.put(f"{self.layout}/{name}", json=ARCH).status_code, 200, name)

    def nodes(self, level):
        sheet = self.c.get(f"{self.layout}/{level}@electrica_BT").json()
        return [n for n in sheet["drawing"]["nodes"] if n["kind"] == "PL"]


class TestBoardPlace(Base):
    def test_a_board_says_its_level_and_where_it_is_and_the_list_keeps_both(self):
        r = self.c.post(f"{self.sld}/boards", json={"name": "TGBT", "level": "L-1", "location": "Sala de tableros, subsuelo"})
        self.assertEqual(r.status_code, 201, r.text)
        listed = self.c.get(f"{self.sld}/boards").json()
        self.assertEqual([(b["name"], b["level"], b["location"]) for b in listed], [("TGBT", "L-1", "Sala de tableros, subsuelo")])
        again = self.c.get(f"{self.sld}?board={listed[0]['id']}").json()
        self.assertEqual((again["input"]["board"]["level"], again["input"]["titleblock"]["location"]), ("L-1", "Sala de tableros, subsuelo"))

    def test_the_plan_editor_is_told_where_each_board_is(self):
        self.c.post(f"{self.sld}/boards", json={"name": "TGBT", "level": "L-1", "location": "Subsuelo"})
        boards = self.c.get(self.layout).json()["boards"]
        self.assertEqual([(b["name"], b["level"], b["location"]) for b in boards], [("TGBT", "L-1", "Subsuelo")])

    def test_a_level_that_is_not_one_and_a_place_that_is_too_long_are_refused(self):
        for body in ({"name": "A", "level": "PB"}, {"name": "A", "level": "L100"}, {"name": "A", "location": "x" * 121}):
            self.assertEqual(self.c.post(f"{self.sld}/boards", json=body).status_code, 422, body)

    def test_a_board_without_level_or_place_is_still_made(self):
        self.assertEqual(self.c.post(f"{self.sld}/boards", json={"name": "TS"}).status_code, 201)
        self.assertEqual(self.c.get(f"{self.sld}/boards").json()[0]["level"], "")


class TestPlenums(Base):
    def test_a_plenum_for_all_the_levels_puts_its_node_in_the_electrical_sheet_of_each_at_the_same_place(self):
        self.levels("L0", "L-1", "L1")
        self.assertEqual(self.c.put(f"{self.layout}/L-1@electrica_BT", json=ELEC).status_code, 200)
        out = self.c.put(f"{self.layout}/plenums", json=PLENUM).json()
        self.assertEqual((len(out["plenums"]), out["added"]), (1, 3))                                       # one node in the sheet of each of the three levels
        for level in ("L-1", "L0", "L1"):
            found = self.nodes(level)
            self.assertEqual(len(found), 1, level)
            self.assertEqual((found[0]["attrs"]["pleno"], found[0]["attrs"]["altura_m"], found[0]["x"], found[0]["y"]), ("PL-1", 3.0, 50.0, -20.0), level)      # 5 m right, 2 m up: y goes down on the plan

    def test_a_reach_of_one_level_up_and_none_down_leaves_the_others_without_it(self):
        self.levels("L0", "L-1", "L1", "L2")
        self.c.put(f"{self.layout}/plenums", json={**PLENUM, "level": "L0", "up": 1, "down": 0})
        self.assertEqual([len(self.nodes(lv)) for lv in ("L0", "L1")], [1, 1])
        for level in ("L-1", "L2"):
            self.assertEqual(self.c.get(f"{self.layout}/{level}@electrica_BT").json()["saved"], False, level)               # no electrical sheet was made where it does not reach

    def test_a_level_made_later_inside_the_range_gets_its_node_and_one_outside_does_not(self):
        self.levels("L0")
        self.c.put(f"{self.layout}/plenums", json={**PLENUM, "level": "L0", "up": 1, "down": 0})
        self.levels("L1", "L2")
        self.assertEqual(len(self.nodes("L1")), 1)
        self.assertEqual(self.c.get(f"{self.layout}/L2@electrica_BT").json()["saved"], False)
        self.levels("L-1")
        self.assertEqual(self.c.get(f"{self.layout}/L-1@electrica_BT").json()["saved"], False)

    def test_defining_it_again_adds_nothing_and_changing_its_reach_extends_it(self):
        self.levels("L0", "L1", "L2")
        first = self.c.put(f"{self.layout}/plenums", json={**PLENUM, "level": "L0", "up": 0, "down": 0}).json()
        again = self.c.put(f"{self.layout}/plenums", json={**PLENUM, "level": "L0", "up": 0, "down": 0}).json()
        self.assertEqual((first["added"], again["added"], len(again["plenums"])), (1, 0, 1))
        wider = self.c.put(f"{self.layout}/plenums", json={**PLENUM, "level": "L0", "up": 2, "down": 0}).json()
        self.assertEqual((wider["added"], [len(self.nodes(lv)) for lv in ("L0", "L1", "L2")]), (2, [1, 1, 1]))

    def test_without_the_scale_of_the_plan_nothing_is_placed_yet(self):
        self.assertEqual(self.c.put(f"{self.layout}/L0", json={**ARCH, "scale": None}).status_code, 200)
        out = self.c.put(f"{self.layout}/plenums", json={**PLENUM, "level": "L0"}).json()
        self.assertEqual((len(out["plenums"]), out["added"]), (1, 0))

    def test_a_level_whose_plan_has_no_scale_gets_its_node_when_the_scale_is_calibrated(self):
        self.assertEqual(self.c.put(f"{self.layout}/L0", json=ARCH).status_code, 200)
        self.assertEqual(self.c.put(f"{self.layout}/L1", json={**ARCH, "scale": None}).status_code, 200)               # the plan of this level has not been calibrated
        self.c.put(f"{self.layout}/plenums", json={**PLENUM, "level": "L0"})
        self.assertEqual((len(self.nodes("L0")), self.c.get(f"{self.layout}/L1@electrica_BT").json()["saved"]), (1, False))
        self.assertEqual(self.c.put(f"{self.layout}/L1", json=ARCH).status_code, 200)                                  # now it is
        node = self.nodes("L1")
        self.assertEqual([(n["attrs"]["pleno"], n["x"], n["y"]) for n in node], [("PL-1", 50.0, -20.0)])

    def test_what_is_not_a_plenum_is_refused_with_what_to_correct(self):
        self.levels("L0")
        for bad in ({"code": ""}, {"code": "no spaces"}, {"level": "PB"}, {"discipline": "arquitectura"}, {"x_m": "a"}, {"altura_m": 0}, {"altura_m": 31}, {"up": -1}, {"up": 51}, {"down": 1.5}):
            self.assertEqual(self.c.put(f"{self.layout}/plenums", json={**PLENUM, "level": "L0", **bad}).status_code, 422, bad)
        self.assertEqual(self.c.get(f"{self.layout}/plenums").json(), {"plenums": []})

    def test_the_overview_lists_them_and_removing_one_leaves_its_nodes_in_the_drawings(self):
        self.levels("L0", "L1")
        self.c.put(f"{self.layout}/plenums", json={**PLENUM, "level": "L0"})
        self.assertEqual([p["code"] for p in self.c.get(self.layout).json()["plenums"]], ["PL-1"])
        self.assertEqual(self.c.delete(f"{self.layout}/plenums/electrica_BT/PL-1").json(), {"plenums": []})
        self.assertEqual(len(self.nodes("L1")), 1)


class TestReach(unittest.TestCase):
    def test_a_plenum_crosses_its_own_level_and_the_ones_within_its_reach_up_and_down(self):
        p = {"level": "L0", "up": 2, "down": 1}
        self.assertEqual([plenums.covers(p, f"L{n}") for n in (-2, -1, 0, 1, 2, 3)], [False, True, True, True, True, False])
        self.assertTrue(all(plenums.covers({"level": "L-1", "up": None, "down": None}, f"L{n}") for n in (-5, 0, 7)))
        self.assertEqual([plenums.number(x) for x in ("L-1", "L0", "L12")], [-1, 0, 12])


if __name__ == "__main__":
    unittest.main()
