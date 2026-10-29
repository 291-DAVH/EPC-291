"""A circuit drawn on two levels is measured through its plenum: the board takes the length the plans measured instead of the one typed."""
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from epc.core.config import settings
from epc.main import create_app
from tests.integration.test_sld_api import BOARD, CIRCUITS, TB

SCALE = {"p1": [0, 0], "p2": [100, 0], "distance_m": 10}
ARCH = {"discipline": "arquitectura", "scale": SCALE, "origin": [0, 0], "nodes": [], "lines": [], "circuits": []}


def plenum(x):
    return {"id": "pl", "kind": "PL", "x": x, "y": 0, "attrs": {"pleno": "PL-001", "altura_m": 3.0}}


def sheet(nodes, lines, circuits):
    return {"discipline": "electrica_BT", "scale": None, "origin": [0, 0], "nodes": nodes, "lines": lines, "circuits": circuits}


class TestAcrossLevelsApi(unittest.TestCase):
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

    def put(self, key, body):
        r = self.c.put(f"{self.layout}/{key}", json=body)
        self.assertEqual(r.status_code, 200, r.text)

    def draw(self, with_upper=True):
        """The board and its plenum on L0 (10 m apart); on L1 the plenum and two luminaires of the same circuit 5 and 15 m from it."""
        circuit = {"tag": "M-01"}
        self.put("L0", ARCH)
        self.put("L1", ARCH)
        self.put("L0@electrica_BT", sheet([{"id": "tb", "kind": "TB", "x": 0, "y": 0}, plenum(100)], [{"id": "bn", "kind": "BN", "points": [[0, 0], [100, 0]]}], [{**circuit, "from": "tb", "to": "pl"}]))
        if with_upper:
            loads = [{"id": "l1", "kind": "LU", "x": 50, "y": 0, "circuit": "M-01"}, {"id": "l2", "kind": "LU", "x": 150, "y": 0, "circuit": "M-01"}]
            self.put("L1@electrica_BT", sheet([plenum(0), *loads], [{"id": "bn", "kind": "BN", "points": [[0, 0], [150, 0]]}], [{**circuit, "from": "pl"}]))

    def lengths(self):
        self.assertEqual(self.c.put(self.sld, json={"board": BOARD, "circuits": [{**c, "length_m": 25} for c in CIRCUITS], "titleblock": TB}).status_code, 200)
        return self.c.get(self.sld).json()["lengths"]["M-01"]

    def test_the_board_takes_the_length_measured_over_both_levels_with_the_plenum_counted_once(self):
        self.draw()
        m = self.lengths()
        self.assertEqual((m["used"], m["setting"]), ("plan", "auto"))
        self.assertEqual(m["levels"], ["L0@electrica_BT", "L1@electrica_BT"])
        self.assertEqual(m["plan_total_m"], 28.0)                              # 10 m + 3 m of plenum to the shaft, and 15 m of stretch on the upper level
        self.assertEqual(m["plan_max_m"], 28.0)                                # the far luminaire: 13 m to the plenum landing + 15 m
        self.assertEqual(m["plan_m"], 23.0)                                    # the moment length of the two luminaires, 18 and 28 m from the board
        self.assertTrue(m["moments"])

    def test_a_circuit_missing_its_upper_sheet_is_just_one_level_and_a_cut_one_falls_back_to_the_data(self):
        self.draw(with_upper=False)
        m = self.lengths()
        self.assertEqual(m["levels"], ["L0@electrica_BT"])                       # only the board's sheet: measured as before (to its destination)
        self.put("L1@electrica_BT", sheet([{"id": "l1", "kind": "LU", "x": 50, "y": 0, "circuit": "M-01"}], [], [{"tag": "M-01", "from": "l1"}]))
        cut = self.lengths()
        self.assertEqual((cut["used"], cut["reason"]), ("data", "levels"))     # nothing starts at a plenum there: it does not chain, the typed length stays


if __name__ == "__main__":
    unittest.main()
