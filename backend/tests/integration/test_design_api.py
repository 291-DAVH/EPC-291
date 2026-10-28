"""Automatic design of circuits and runs on a sheet: rooms, the proposal, and the circuits created in the board once accepted."""
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from epc.core.config import settings
from epc.main import create_app
from tests.integration.test_sld_api import BOARD, CIRCUITS, TB

SCALE = {"p1": [0, 0], "p2": [100, 0], "distance_m": 10}
ROOMS = [{"id": "A", "name": "Cocina", "points": [[100, 0], [400, 0], [400, 200], [100, 200]]}, {"id": "B", "name": "Living", "points": [[100, 220], [400, 220], [400, 480], [100, 480]]}]


def lights(room_x, room_y, n):
    return [{"id": f"l{room_y}{i}", "kind": "LU", "x": room_x + 40 + (i % 6) * 40, "y": room_y + 30 + (i // 6) * 40} for i in range(n)]


DRAWING = {"discipline": "electrica_BT", "scale": SCALE, "origin": [0, 0], "rooms": ROOMS, "lines": [],
           "nodes": [{"id": "tb", "kind": "TB", "x": 20, "y": 250}, *lights(100, 0, 9), *lights(100, 220, 17)]}


class TestDesign(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._old = (settings.projects_dir, settings.role, settings.data_dir)
        settings.projects_dir, settings.role, settings.data_dir = self.root, "admin", self.root / "_data"
        self.c = TestClient(create_app())
        r = self.c.post("/api/projects", json={"client_name": "Acme SA", "client_code": "ACME", "project_code": "P-1", "project_name": "Planta",
                                                "jurisdiction": "AR", "methodology": "pm2", "disciplines": ["electrical"]})
        self.assertEqual(r.status_code, 201, r.text)
        self.base = "/api/projects/ACME/P-1/layout"

    def tearDown(self):
        settings.projects_dir, settings.role, settings.data_dir = self._old
        self.tmp.cleanup()

    def test_a_room_keeps_what_it_says_about_its_lighting_and_the_design_ignores_it(self):
        rooms = [{**ROOMS[0], "lighting": {"activity": "education.classroom", "luminaire": "led_panel_600", "height_m": 2.8}}, ROOMS[1]]
        r = self.c.put(f"{self.base}/L0", json={**DRAWING, "rooms": rooms})
        self.assertEqual(r.status_code, 200, r.text)
        saved = r.json()["drawing"]["rooms"]
        self.assertEqual(saved[0]["lighting"], {"activity": "education.classroom", "luminaire": "led_panel_600", "height_m": 2.8})
        self.assertIsNone(saved[1]["lighting"])
        runs = self.c.post(f"{self.base}/L0/design/runs", json={"drawing": {**DRAWING, "rooms": rooms}})
        self.assertEqual(runs.status_code, 200, runs.text)                                    # the plan engine never reads it

    def test_the_rooms_are_kept_with_the_sheet(self):
        r = self.c.put(f"{self.base}/L0", json=DRAWING)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual([x["name"] for x in r.json()["drawing"]["rooms"]], ["Cocina", "Living"])
        self.assertEqual(self.c.put(f"{self.base}/L0", json={**DRAWING, "rooms": [{"id": "x", "points": [[0, 0], [1, 1]]}]}).status_code, 422)

    def drawn(self):
        """The drawing once the person accepted the runs of step 1."""
        p = self.c.post(f"{self.base}/L0/design/runs", json={"drawing": DRAWING}).json()
        lines = [{"id": f"r{i}", "kind": ln["kind"], "points": ln["points"]} for i, ln in enumerate(p["lines"], 1)]
        return {**DRAWING, "lines": lines}

    def test_the_runs_are_straight_trunks_with_stubs_and_save_nothing(self):
        r = self.c.post(f"{self.base}/L0/design/runs", json={"drawing": DRAWING})
        self.assertEqual(r.status_code, 200, r.text)
        p = r.json()
        self.assertIn("BN", {ln["kind"] for ln in p["lines"]})
        self.assertTrue(all(ln["kind"] == ("BN" if ln["role"] == "trunk" else "CN") for ln in p["lines"]))
        self.assertTrue(all(len(ln["points"]) == 2 for ln in p["lines"]))                      # no bends
        self.assertEqual(p["stats"]["bends"], 0)
        self.assertEqual(self.c.get(self.base).json()["levels"], [])                           # nothing was stored

    def test_the_wiring_gives_circuits_by_room_within_the_limit_over_the_runs(self):
        r = self.c.post(f"{self.base}/L0/design/wiring", json={"drawing": self.drawn()})
        self.assertEqual(r.status_code, 200, r.text)
        p = r.json()
        self.assertEqual(sorted((c["room"], c["outlets"]) for c in p["circuits"]), [("A", 9), ("B", 8), ("B", 9)])
        self.assertTrue(all(x["found"] for x in p["routes"].values()), p["routes"])
        limited = self.c.post(f"{self.base}/L0/design/wiring", json={"drawing": self.drawn(), "families": {"IUG": {"max_outlets": 5, "va_per_outlet": 200}}}).json()
        self.assertTrue(all(c["outlets"] <= 5 and c["va_per_outlet"] == 200 for c in limited["circuits"]))

    def test_the_wiring_without_runs_asks_for_them(self):
        p = self.c.post(f"{self.base}/L0/design/wiring", json={"drawing": DRAWING}).json()
        self.assertTrue(any("no runs" in w for w in p["warnings"]))

    def test_the_accepted_circuits_are_created_in_the_board_and_a_second_time_changes_nothing(self):
        drawn = self.drawn()
        p = self.c.post(f"{self.base}/L0/design/wiring", json={"drawing": drawn}).json()
        body = {"circuits": [{"tag": c["tag"], "description": c["description"], "load": c["va"], "unit": "VA"} for c in p["circuits"]]}
        r = self.c.post(f"{self.base}/L0/design/circuits", json=body)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(len(r.json()["added"]), 3)
        board = self.c.get("/api/projects/ACME/P-1/sld").json()["input"]
        self.assertEqual({c["tag"] for c in board["circuits"]}, {c["tag"] for c in p["circuits"]})
        self.assertEqual({c["unit"] for c in board["circuits"]}, {"VA"})
        again = self.c.post(f"{self.base}/L0/design/circuits", json=body).json()
        self.assertEqual((again["added"], len(again["skipped"])), ([], 3))
        nxt = self.c.post(f"{self.base}/L0/design/wiring", json={"drawing": drawn}).json()      # the tags now in the board are not proposed again
        self.assertFalse({c["tag"] for c in nxt["circuits"]} & {c["tag"] for c in p["circuits"]})

    def test_the_boards_of_engineering_are_offered_and_the_drawing_keeps_which_one_feeds_each_load(self):
        self.assertEqual(self.c.get(self.base).json()["boards"], [])                           # no board yet: the editor asks to make it in Engineering first
        sld = "/api/projects/ACME/P-1/sld"
        self.assertEqual(self.c.put(sld, json={"board": {**BOARD, "name": "TGBT-02"}, "circuits": CIRCUITS, "titleblock": TB}).status_code, 200)
        boards = self.c.get(self.base).json()["boards"]
        self.assertEqual([b["name"] for b in boards], ["TGBT-02"])
        nodes = [{**n, "board": boards[0]["id"]} if n["kind"] in ("TB", "LU") else n for n in DRAWING["nodes"]]
        saved = self.c.put(f"{self.base}/L0", json={**DRAWING, "nodes": nodes}).json()["drawing"]["nodes"]
        self.assertTrue(all(n["board"] == boards[0]["id"] for n in saved))
        body = {"board": boards[0]["id"], "circuits": [{"tag": "IUG-01", "description": "Cocina", "load": 900, "unit": "VA"}]}
        self.assertEqual(self.c.post(f"{self.base}/L0/design/circuits", json=body).json()["board_id"], boards[0]["id"])
        self.assertEqual([c["board_id"] for c in self.c.get(self.base).json()["circuits"] if c["tag"] == "IUG-01"], [boards[0]["id"]])

    def test_a_drawing_without_a_board_gets_a_warning_not_an_error(self):
        nodes = [n for n in DRAWING["nodes"] if n["kind"] != "TB"]
        d = {**DRAWING, "nodes": nodes}
        self.assertTrue(any("no board" in w for w in self.c.post(f"{self.base}/L0/design/runs", json={"drawing": d}).json()["warnings"]))
        p = self.c.post(f"{self.base}/L0/design/wiring", json={"drawing": d}).json()
        self.assertEqual(p["circuits"], [])
        self.assertTrue(any("no board" in w for w in p["warnings"]))


if __name__ == "__main__":
    unittest.main()
