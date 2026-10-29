"""Automatic design in two steps (epc_plan.design): straight runs with the fewest trunks, then the wiring by room over the runs that are drawn. Checked by routing what is proposed with the engine."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from epc_plan import core, design   # noqa: E402


def rect(i, name, x0, y0, x1, y1):
    return {"id": i, "name": name, "points": [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]}


def doc(nodes, lines=()):
    return {"schema_version": "1.0", "plan": {"id": "T", "level": "L0", "scale": {"p1": [0, 0], "p2": [100, 0], "distance_m": 10}, "origin": [0, 0]}, "discipline": "electrica_BT",
            "nodes": nodes, "lines": list(lines), "circuits": []}


def node(i, kind, x, y):
    return {"id": i, "kind": kind, "x": x, "y": y}


def with_runs(document, proposal):
    """What the editor does with accepted runs: the lines in the drawing."""
    d = copy.deepcopy(document)
    for i, ln in enumerate(proposal["lines"], 1):
        d["lines"].append({"id": f"p{i}", "kind": ln["kind"], "points": ln["points"]})
    return d


def reaches_every_load(document, board="tb"):
    """One circuit from the board to every load: found and nothing left out."""
    d = copy.deepcopy(document)
    loads = [n["id"] for n in d["nodes"] if n["kind"] in ("LU", "TG")]
    for n in d["nodes"]:
        if n["id"] in loads:
            n["circuit"] = "X"
    d["circuits"] = [{"tag": "X", "from": board, "to": "", "via": [], "ternas": 1}]
    r = core.process(d)["circuits"]["X"]
    return r["found"], r["unreached"], r["loads"]


BOARD = node("tb", "TB", 20, 250)
BANDS = [node(f"a{i}", "LU", 100 + i * 70, 40) for i in range(8)] + [node(f"b{i}", "LU", 100 + i * 70, 250) for i in range(8)] + [node(f"c{i}", "LU", 100 + i * 70, 460) for i in range(8)]


class TestRuns(unittest.TestCase):
    def test_loads_in_three_bands_give_three_straight_trunks_hanging_from_one_spine(self):
        p = design.propose_runs(doc([BOARD, *BANDS]))
        self.assertEqual(p["orientation"], "horizontal")
        trunks = [ln for ln in p["lines"] if ln["role"] == "trunk"]
        horizontal = [ln for ln in trunks if abs(ln["points"][0][1] - ln["points"][1][1]) < 1e-6]
        vertical = [ln for ln in trunks if abs(ln["points"][0][0] - ln["points"][1][0]) < 1e-6]
        self.assertEqual((len(horizontal), len(vertical)), (3, 1))                         # a trunk per band and the spine
        self.assertEqual(sorted(round(ln["points"][0][1]) for ln in horizontal), [40, 250, 460])
        self.assertEqual(p["stats"]["bends"], 0)
        self.assertTrue(all(ln["kind"] == ("BN" if ln["role"] == "trunk" else "CN") for ln in p["lines"]))

    def test_no_line_has_a_bend_and_every_one_is_horizontal_or_vertical(self):
        p = design.propose_runs(doc([BOARD, *BANDS, node("x", "TG", 333, 111)]))
        for ln in p["lines"]:
            self.assertEqual(len(ln["points"]), 2)
            (x0, y0), (x1, y1) = ln["points"]
            self.assertTrue(abs(x0 - x1) < 1e-6 or abs(y0 - y1) < 1e-6)

    def test_loads_in_columns_give_vertical_trunks(self):
        cols = [node(f"c{c}{i}", "LU", 100 + c * 200, 60 + i * 60) for c in range(3) for i in range(7)]
        p = design.propose_runs(doc([node("tb", "TB", 20, 30), *cols]))
        self.assertEqual(p["orientation"], "vertical")
        self.assertEqual(p["stats"]["trunks"], 4)                                           # three columns and the spine

    def test_the_layout_is_shorter_than_running_a_line_to_each_load_from_the_board(self):
        d = doc([BOARD, *BANDS])
        p = design.propose_runs(d)
        star = sum(abs(n["x"] - BOARD["x"]) + abs(n["y"] - BOARD["y"]) for n in BANDS) * 0.1
        self.assertLess(p["stats"]["trunk_length"] + p["stats"]["stub_length"], star / 3)

    def test_the_runs_reach_every_load_when_the_engine_routes_them(self):
        d = doc([BOARD, *BANDS, node("x", "TG", 333, 111), node("y", "LU", 90, 130)])
        found, unreached, loads = reaches_every_load(with_runs(d, design.propose_runs(d)))
        self.assertEqual((found, unreached, loads), (True, [], len(BANDS) + 2))

    def test_a_trunk_that_crosses_the_spine_is_cut_there_so_it_touches_it(self):
        # three rooms as the lighting calculation fills them: the loads of the first two straddle the row of the board, so a trunk of columns goes through the spine
        spots = [(115, 110), (145, 110), (115, 130), (145, 130), (215, 110), (245, 110), (215, 130), (111.4, 170), (134.3, 170), (157.1, 170), (180, 170), (202.9, 170), (225.7, 170), (248.6, 170)]
        d = doc([node("tb", "TB", 60, 150)] + [node(f"l{i}", "LU", x, y) for i, (x, y) in enumerate(spots, 1)])
        p = design.propose_runs(d, {"board": "tb"})
        self.assertEqual(p["warnings"], [])
        self.assertEqual(p["closed"], 0)                                                                  # nothing had to be added: the layout itself touches everything
        self.assertTrue(reaches_every_load(with_runs(d, p)))
        spine = [ln["points"] for ln in p["lines"] if ln["role"] == "trunk" and abs(ln["points"][0][1] - ln["points"][-1][1]) < 1e-6 and abs(ln["points"][0][1] - 150) < 1e-6]
        for ln in p["lines"]:
            if ln["role"] == "trunk" and abs(ln["points"][0][0] - ln["points"][-1][0]) < 1e-6:           # a column
                ys = sorted(y for _, y in ln["points"])
                self.assertFalse(ys[0] + 1e-6 < 150 < ys[1] - 1e-6, ln["points"])                         # none of them goes through the row of the spine
        self.assertTrue(spine)

    def test_a_load_the_layout_left_apart_is_joined_to_the_nearest_run_and_one_that_cannot_be_is_said(self):
        d = doc([node("tb", "TB", 0, 0), node("a", "LU", 50, 0), node("near", "LU", 50, 30), node("far", "LU", 400, 300)])
        trunk = {"kind": "BN", "points": [[0, 0], [100, 0]], "role": "trunk"}
        board = d["nodes"][0]
        loads = [{"id": i, "x": x, "y": y} for i, x, y in (("a", 50, 0), ("near", 50, 30), ("far", 400, 300))]
        extra, warnings = design._close_runs(d, board, loads, [trunk])
        self.assertEqual([e["points"] for e in extra], [[[50, 0], [50, 30]]])                           # perpendicular to the trunk, ending on the load
        self.assertEqual(extra[0]["kind"], "CN")
        self.assertEqual(len(warnings), 1)
        self.assertIn("1 load(s) cannot be reached", warnings[0])
        self.assertIn("LU-003", warnings[0])                                                              # the tag the person sees on the plan

    def test_a_single_row_is_one_trunk_and_stubs(self):
        row = [node(f"r{i}", "LU", 100 + i * 60, 100 + (30 if i in (1, 4) else 0)) for i in range(6)]
        p = design.propose_runs(doc([node("tb", "TB", 40, 100), *row]))
        self.assertEqual(p["stats"]["trunks"], 1)
        self.assertEqual(p["stats"]["stubs"], 2)                                            # the loads off the trunk's line get a stub

    def test_a_drawing_without_a_board_or_without_loads_says_so(self):
        self.assertTrue(any("no board" in w for w in design.propose_runs(doc(BANDS))["warnings"]))
        self.assertTrue(any("no loads" in w for w in design.propose_runs(doc([BOARD]))["warnings"]))

    def test_the_best_number_of_trunks_is_found_by_cost(self):
        pts = [(0, 0), (50, 2), (100, 0), (0, 500), (50, 498), (100, 500)]
        two = design.partitions(pts)[2]
        self.assertEqual([len(g) for g in two], [3, 3])
        self.assertEqual(len(design.best_layout(pts, (0, 250))["trunks"]), 3)               # two rows and the spine (the board is on it: no feeder)


ROOMS = [rect("A", "Cocina", 100, 0, 400, 200), rect("B", "Living", 100, 220, 400, 480), rect("C", "Dormitorio", 420, 0, 700, 200)]


def lights(room, n, kind="LU", prefix="l"):
    pts = room["points"]
    x0, y0, x1, y1 = pts[0][0], pts[0][1], pts[2][0], pts[2][1]
    cols = max(1, int(n ** 0.5) + 1)
    return [node(f"{prefix}{room['id']}{i}", kind, x0 + 30 + (i % cols) * (x1 - x0 - 60) / max(1, cols - 1), y0 + 30 + (i // cols) * 40) for i in range(n)]


class TestBoards(unittest.TestCase):
    def test_only_the_loads_fed_from_the_board_of_the_symbol_are_designed(self):
        tb = {**BOARD, "board": "b1"}
        mine = [{**n, "board": "b1"} for n in BANDS[:8]]
        other = [{**n, "board": "b2"} for n in BANDS[8:12]]
        free = BANDS[12:16]                                                      # not tied to a board yet: they go with whichever is designed
        both = design.propose_runs(doc([tb, *mine, *other, *free]))
        alone = design.propose_runs(doc([tb, *mine, *free]))
        self.assertEqual(both["lines"], alone["lines"])                            # the loads of the other board change nothing here
        only_other = design.propose_runs(doc([{**BOARD, "board": "b3"}, *other]))
        self.assertTrue(any("no loads" in w for w in only_other["warnings"]))     # the loads of another board are not this board's


class TestWiring(unittest.TestCase):
    def drawn(self, nodes):
        d = doc(nodes)
        return with_runs(d, design.propose_runs(d))

    def test_each_room_is_a_circuit_and_a_room_over_the_limit_is_split_in_balanced_groups(self):
        d = self.drawn([BOARD, *lights(ROOMS[0], 9), *lights(ROOMS[1], 20), *lights(ROOMS[2], 3)])
        p = design.propose_wiring(d, ROOMS)
        by_room = {}
        for c in p["circuits"]:
            by_room.setdefault(c["room"], []).append(c["outlets"])
        self.assertEqual({k: sorted(v) for k, v in by_room.items()}, {"A": [9], "B": [10, 10], "C": [3]})
        self.assertTrue(all(c["outlets"] <= 15 for c in p["circuits"]))
        self.assertEqual(len({c["tag"] for c in p["circuits"]}), 4)
        self.assertEqual(len(p["assignments"]), 32)
        self.assertEqual(p["warnings"], [])
        self.assertTrue(all(r["found"] for r in p["routes"].values()), p["routes"])

    def test_each_family_of_load_has_its_own_circuits_in_a_room(self):
        d = self.drawn([BOARD, *lights(ROOMS[0], 4), *lights(ROOMS[0], 3, "TG", "t"), *lights(ROOMS[0], 2, "TE", "e")])
        got = sorted((c["family"], c["outlets"]) for c in design.propose_wiring(d, ROOMS)["circuits"])
        self.assertEqual(got, [("IUG", 4), ("TUE", 1), ("TUE", 1), ("TUG", 3)])               # a special socket is a circuit of its own

    def test_the_emergency_luminaires_of_a_room_are_a_circuit_of_their_own_with_the_power_they_say(self):
        d = self.drawn([BOARD, *lights(ROOMS[0], 3), *lights(ROOMS[0], 2, "LE", "e")])
        for n in [n for n in d["nodes"] if n["kind"] == "LE"]:
            n["attrs"] = {"lighting": {"power_w": 3, "power_va": 4}}
        p = design.propose_wiring(d, ROOMS)
        got = sorted((c["family"], c["tag"][:3], c["outlets"], c["va"]) for c in p["circuits"])
        self.assertEqual(got, [("IUE", "IUE", 2, 8.0), ("IUG", "IUG", 3, 300.0)])

    def test_tags_skip_the_ones_already_taken_and_the_limits_can_be_changed(self):
        d = self.drawn([BOARD, *lights(ROOMS[0], 4)])
        p = design.propose_wiring(d, ROOMS, {"taken": ["IUG-01", "IUG-02"], "families": {"IUG": {"max_outlets": 2, "va_per_outlet": 150}}})
        self.assertEqual([c["tag"] for c in p["circuits"]], ["IUG-03", "IUG-04"])
        self.assertEqual([c["va"] for c in p["circuits"]], [300.0, 300.0])

    def test_a_luminaire_that_says_its_power_brings_it_and_the_others_use_the_typical_value(self):
        d = self.drawn([BOARD, *lights(ROOMS[0], 3)])
        for n, w in zip([n for n in d["nodes"] if n["kind"] == "LU"], (40, 25.5, None)):
            if w is not None:
                n["attrs"] = {"lighting": {"power_w": w}}
        self.assertEqual([c["va"] for c in design.propose_wiring(d, ROOMS)["circuits"]], [165.5])        # 40 + 25.5 + the 100 VA typical of the third one

    def test_the_apparent_power_of_a_luminaire_wins_over_its_watts(self):
        d = self.drawn([BOARD, *lights(ROOMS[0], 2)])
        luminaires = [n for n in d["nodes"] if n["kind"] == "LU"]
        luminaires[0]["attrs"] = {"lighting": {"power_w": 36, "power_va": 40}}
        luminaires[1]["attrs"] = {"lighting": {"power_w": 36, "power_va": -1}}                      # not a power: the watts are taken
        self.assertEqual([c["va"] for c in design.propose_wiring(d, ROOMS)["circuits"]], [76.0])

    def test_a_power_that_is_not_a_positive_number_is_not_taken(self):
        d = self.drawn([BOARD, *lights(ROOMS[0], 2)])
        luminaires = [n for n in d["nodes"] if n["kind"] == "LU"]
        luminaires[0]["attrs"] = {"lighting": {"power_w": True}}
        luminaires[1]["attrs"] = {"lighting": {"power_w": -5}}
        self.assertEqual([c["va"] for c in design.propose_wiring(d, ROOMS)["circuits"]], [200.0])

    def test_without_runs_it_asks_for_them_and_a_load_the_runs_do_not_reach_is_said(self):
        bare = doc([BOARD, *lights(ROOMS[0], 3)])
        self.assertTrue(any("no runs" in w for w in design.propose_wiring(bare, ROOMS)["warnings"]))
        d = self.drawn([BOARD, *lights(ROOMS[0], 3)])
        d["nodes"].append(node("far", "LU", 390, 190))                                            # inside the room but no run was drawn to it
        p = design.propose_wiring(d, ROOMS)
        self.assertTrue(any("do not reach" in w for w in p["warnings"]), p["warnings"])
        self.assertFalse(all(r["found"] for r in p["routes"].values()))

    def test_loads_outside_every_room_and_a_drawing_without_a_board_are_said(self):
        d = self.drawn([BOARD, *lights(ROOMS[0], 2), node("far", "LU", 900, 900)])
        p = design.propose_wiring(d, ROOMS)
        self.assertEqual(p["unassigned"], ["far"])
        self.assertTrue(any("outside every room" in w for w in p["warnings"]))
        nb = design.propose_wiring(doc(lights(ROOMS[0], 2)), ROOMS)
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
        self.assertEqual(design.chain([(10, 0), (1, 0), (5, 0)], (0, 0)), [1, 2, 0])


if __name__ == "__main__":
    unittest.main()
