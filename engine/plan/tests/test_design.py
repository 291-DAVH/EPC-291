"""Automatic design of circuits and runs (epc_plan.design): rooms, limits per circuit, trunk and branches, checked by routing what is proposed with the engine itself."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from epc_plan import core, design   # noqa: E402


def rect(i, name, x0, y0, x1, y1):
    return {"id": i, "name": name, "points": [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]}


def doc(nodes):
    return {"schema_version": "1.0", "plan": {"id": "T", "level": "L0", "scale": {"p1": [0, 0], "p2": [100, 0], "distance_m": 10}, "origin": [0, 0]}, "discipline": "electrica_BT",
            "nodes": nodes, "lines": [], "circuits": []}


def node(i, kind, x, y):
    return {"id": i, "kind": kind, "x": x, "y": y}


def apply(document, proposal):
    """What the editor does with an accepted proposal: the lines, the circuits and the tag on each load."""
    d = copy.deepcopy(document)
    for i, ln in enumerate(proposal["lines"], 1):
        d["lines"].append({"id": f"p{i}", "kind": ln["kind"], "points": ln["points"], **({"circuit": ln["circuit"]} if ln.get("circuit") else {})})
    for n in d["nodes"]:
        if n["id"] in proposal["assignments"]:
            n["circuit"] = proposal["assignments"][n["id"]]
    d["circuits"] = [{"tag": c["tag"], "from": c["from"], "to": c["to"], "via": c["via"], "ternas": 1} for c in proposal["circuits"]]
    return d


BOARD = node("tb", "TB", 20, 250)
ROOMS = [rect("A", "Cocina", 100, 0, 400, 200), rect("B", "Living", 100, 220, 400, 480), rect("C", "Dormitorio", 420, 0, 700, 200)]


class TestDesign(unittest.TestCase):
    def lights(self, room, n, kind="LU", prefix="l"):
        pts = room["points"]
        x0, y0, x1, y1 = pts[0][0], pts[0][1], pts[2][0], pts[2][1]
        cols = max(1, int(n ** 0.5) + 1)
        return [node(f"{prefix}{room['id']}{i}", kind, x0 + 30 + (i % cols) * (x1 - x0 - 60) / max(1, cols - 1), y0 + 30 + (i // cols) * 40) for i in range(n)]

    def test_each_room_is_a_circuit_and_a_room_over_the_limit_is_split_in_balanced_groups(self):
        d = doc([BOARD, *self.lights(ROOMS[0], 9), *self.lights(ROOMS[1], 20), *self.lights(ROOMS[2], 3)])
        p = design.propose(d, ROOMS)
        by_room = {}
        for c in p["circuits"]:
            by_room.setdefault(c["room"], []).append(c["outlets"])
        self.assertEqual({k: sorted(v) for k, v in by_room.items()}, {"A": [9], "B": [10, 10], "C": [3]})
        self.assertTrue(all(c["outlets"] <= 15 for c in p["circuits"]))
        self.assertEqual(len({c["tag"] for c in p["circuits"]}), 4)
        self.assertEqual(len(p["assignments"]), 32)
        self.assertEqual(p["unassigned"], [])

    def test_each_family_of_load_has_its_own_circuits_in_a_room(self):
        d = doc([BOARD, *self.lights(ROOMS[0], 4), *self.lights(ROOMS[0], 3, "TG", "t"), *self.lights(ROOMS[0], 2, "TE", "e")])
        p = design.propose(d, ROOMS)
        got = sorted((c["family"], c["outlets"]) for c in p["circuits"])
        self.assertEqual(got, [("IUG", 4), ("TUE", 1), ("TUE", 1), ("TUG", 3)])               # a special socket is a circuit of its own
        self.assertTrue(all(c["tag"].startswith(c["family"]) for c in p["circuits"]))

    def test_tags_skip_the_ones_already_taken_and_the_limits_can_be_changed(self):
        d = doc([BOARD, *self.lights(ROOMS[0], 4)])
        p = design.propose(d, ROOMS, {"taken": ["IUG-01", "IUG-02"], "families": {"IUG": {"max_outlets": 2, "va_per_outlet": 150}}})
        self.assertEqual([c["tag"] for c in p["circuits"]], ["IUG-03", "IUG-04"])
        self.assertEqual([c["va"] for c in p["circuits"]], [300.0, 300.0])

    def test_what_is_proposed_is_routed_completely_by_the_engine(self):
        d = doc([BOARD, *self.lights(ROOMS[0], 9), *self.lights(ROOMS[1], 20), *self.lights(ROOMS[2], 3)])
        done = core.process(apply(d, design.propose(d, ROOMS)))
        self.assertTrue(all(r["found"] for r in done["circuits"].values()), done["circuits"])
        self.assertEqual(done["schedule"]["loads"]["unassigned"], [])
        self.assertEqual(sum(sum(v.values()) for v in done["schedule"]["loads"]["by_circuit"].values()), 32)
        self.assertGreater(done["schedule"]["total_length_m"], 0)
        self.assertFalse([w for w in done["warnings"] if "not routed" in w or "no circuit" in w], done["warnings"])

    def test_the_trunk_leaves_the_board_and_reaches_every_room_and_the_branches_start_at_its_entrance(self):
        d = doc([BOARD, *self.lights(ROOMS[0], 5), *self.lights(ROOMS[2], 5)])
        p = design.propose(d, ROOMS)
        trunk = [ln for ln in p["lines"] if ln["role"] == "trunk"]
        self.assertTrue(trunk and all(ln["kind"] == "BN" for ln in trunk))
        self.assertEqual(trunk[0]["points"][0], [20, 250])
        branches = [ln for ln in p["lines"] if ln["role"] == "branch"]
        self.assertTrue(all(ln["kind"] == "CN" and ln["circuit"] for ln in branches))
        for ln in branches:                                                                    # the conduit of a room starts inside or on the border of that room
            room = next(r for r in ROOMS if r["id"] == ln["room"])
            self.assertTrue(design.inside(tuple(ln["points"][0]), [tuple(q) for q in room["points"]]))
        for ln in p["lines"]:                                                                  # every stretch is horizontal or vertical
            for a, b in zip(ln["points"], ln["points"][1:]):
                self.assertTrue(abs(a[0] - b[0]) < 1e-6 or abs(a[1] - b[1]) < 1e-6)

    def test_loads_outside_every_room_and_a_drawing_without_a_board_are_said(self):
        d = doc([BOARD, *self.lights(ROOMS[0], 2), node("far", "LU", 900, 900)])
        p = design.propose(d, ROOMS)
        self.assertEqual(p["unassigned"], ["far"])
        self.assertTrue(any("outside every room" in w for w in p["warnings"]))
        nb = design.propose(doc(self.lights(ROOMS[0], 2)), ROOMS)
        self.assertEqual((nb["circuits"], nb["board"]), ([], ""))
        self.assertTrue(any("no board" in w for w in nb["warnings"]))

    def test_geometry_helpers(self):
        sq = [(0, 0), (10, 0), (10, 10), (0, 10)]
        self.assertTrue(design.inside((5, 5), sq))
        self.assertTrue(design.inside((10, 5), sq))
        self.assertFalse(design.inside((11, 5), sq))
        self.assertEqual(design.area(sq), 100)
        inner = {"id": "i", "points": [[2, 2], [4, 2], [4, 4], [2, 4]]}
        outer = {"id": "o", "points": [[0, 0], [10, 0], [10, 10], [0, 10]]}
        self.assertEqual(design.room_of((3, 3), [outer, inner])["id"], "i")                  # the smallest room that holds it
        self.assertEqual(design.l_path((0, 0), (5, 5), True), [(0, 0), (5, 0), (5, 5)])
        self.assertEqual(design.l_path((0, 0), (0, 5), True), [(0, 0), (0, 5)])
        self.assertEqual(design.chain([(10, 0), (1, 0), (5, 0)], (0, 0)), [1, 2, 0])


if __name__ == "__main__":
    unittest.main()
