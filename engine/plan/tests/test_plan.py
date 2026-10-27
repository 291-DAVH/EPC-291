"""The plan-drawing engine (epc_plan): graph, tags, schedule, levels, networks and the DXF. Pure: no backend, no network."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
PKG = SRC / "epc_plan"
sys.path.insert(0, str(SRC))

import ezdxf   # noqa: E402
from epc_plan import core, dxfout, jobs   # noqa: E402


def load(name):
    return json.loads((HERE / "fixtures" / "plan" / name).read_text(encoding="utf-8"))


def drawing(nodes=(), lines=(), **extra):
    """A small drawing: 10 view units are 1 m (the two calibration points are 100 units apart and 10 m)."""
    return {"schema_version": "1.0", "plan": {"id": "T", "level": "L0", "scale": {"p1": [0, 0], "p2": [100, 0], "distance_m": 10}, "origin": [0, 0]},
            "discipline": "electrica_BT", "nodes": list(nodes), "lines": list(lines), **extra}


def node(i, kind, x, y, **kw):
    return {"id": i, "kind": kind, "x": x, "y": y, **kw}


def line(i, kind, pts, **kw):
    return {"id": i, "kind": kind, "points": pts, **kw}


class TestSample(unittest.TestCase):
    def test_the_sample_gives_the_expected_result(self):
        self.assertEqual(core.process(load("input.json")), load("expected_output.json"))

    def test_it_is_deterministic(self):
        self.assertEqual(core.process(load("input.json")), core.process(load("input.json")))

    def test_the_input_is_not_changed(self):
        doc = load("input.json")
        before = copy.deepcopy(doc)
        core.process(doc)
        self.assertEqual(doc, before)

    def test_the_output_has_the_fields_of_its_schema(self):
        schema = json.loads((PKG / "schema" / "output.schema.json").read_text(encoding="utf-8"))
        out = core.process(load("input.json"))
        for k in schema["required"]:
            self.assertIn(k, out)

    def test_nothing_imports_the_backend(self):
        for f in PKG.rglob("*.py"):
            self.assertNotRegex(f.read_text(encoding="utf-8"), r"^\s*(from|import)\s+epc\b", f.name)


class TestLevelsScaleOrigin(unittest.TestCase):
    def test_levels(self):
        for text, number in (("L0", 0), ("L1", 1), ("L12", 12), ("L-1", -1), ("L-30", -30)):
            self.assertEqual(core.parse_level(text), number)
        for bad in ("", "L", "L01", "L-0", "L+1", "1", "l1", "PB", None, 3):
            with self.assertRaises(core.PlanError, msg=str(bad)):
                core.parse_level(bad)

    def test_scale_gives_metres_per_unit(self):
        self.assertAlmostEqual(core.metres_per_unit({"p1": [0, 0], "p2": [30, 40], "distance_m": 5}), 0.1)

    def test_a_bad_scale_is_refused_with_a_clear_message(self):
        for scale, text in (({"p1": [1, 1], "p2": [1, 1], "distance_m": 5}, "same point"), ({"p1": [0, 0], "p2": [1, 0], "distance_m": 0}, "greater than zero"), ({}, "two points")):
            with self.assertRaisesRegex(core.PlanError, text):
                core.metres_per_unit(scale)

    def test_the_origin_moves_the_zero_and_y_points_up(self):
        doc = drawing([node("a", "TB", 100, 200)])
        doc["plan"]["origin"] = [50, 250]
        n = core.process(doc)["nodes"][0]
        self.assertEqual((n["x_m"], n["y_m"]), (5.0, 5.0))

    def test_a_bad_level_is_refused(self):
        doc = drawing()
        doc["plan"]["level"] = "PB"
        with self.assertRaisesRegex(core.PlanError, "L0 for the ground level"):
            core.process(doc)


class TestGraph(unittest.TestCase):
    def test_a_branch_ending_on_a_line_makes_a_junction_and_splits_it(self):
        out = core.process(drawing([node("a", "TB", 0, 0), node("b", "CM", 200, 0), node("c", "CP", 100, 100)],
                                   [line("main", "BN", [[0, 0], [200, 0]]), line("br", "CN", [[100, 0], [100, 100]])]))
        main = [s for s in out["stretches"] if s["line"] == "main"]
        branch = [s for s in out["stretches"] if s["line"] == "br"]
        self.assertEqual(sorted(s["length_m"] for s in main), [10.0, 10.0])
        self.assertEqual([s["length_m"] for s in branch], [10.0])
        junction = main[0]["to"]
        self.assertTrue(junction.startswith("auto:J"))
        self.assertEqual((main[1]["from"], branch[0]["from"]), (junction, junction))

    def test_two_lines_that_only_cross_are_not_connected_and_say_so(self):
        out = core.process(drawing([node(i, "CP", x, y) for i, x, y in (("a", 0, 50), ("b", 100, 50), ("c", 50, 0), ("d", 50, 100))],
                                   [line("h", "CN", [[0, 50], [100, 50]]), line("v", "CN", [[50, 0], [50, 100]])]))
        self.assertEqual(len(out["stretches"]), 2)
        self.assertTrue(any("cross" in w and "not connected" in w for w in out["warnings"]))

    def test_a_node_placed_on_the_crossing_connects_them(self):
        out = core.process(drawing([node(i, "CP", x, y) for i, x, y in (("a", 0, 50), ("b", 100, 50), ("c", 50, 0), ("d", 50, 100), ("x", 50, 50))],
                                   [line("h", "CN", [[0, 50], [100, 50]]), line("v", "CN", [[50, 0], [50, 100]])]))
        self.assertEqual(len(out["stretches"]), 4)
        self.assertFalse(any("cross" in w for w in out["warnings"]))

    def test_a_chamber_on_a_run_splits_it(self):
        out = core.process(drawing([node("a", "TB", 0, 0), node("m", "CM", 60, 0), node("b", "CP", 100, 0)], [line("l", "BN", [[0, 0], [100, 0]])]))
        self.assertEqual([s["length_m"] for s in out["stretches"]], [6.0, 4.0])

    def test_a_free_end_is_reported(self):
        out = core.process(drawing([node("a", "TB", 0, 0)], [line("l", "CN", [[0, 0], [50, 0]])]))
        self.assertTrue(any("free end" in w for w in out["warnings"]))

    def test_the_snap_tolerance_joins_a_line_that_stops_just_short(self):
        out = core.process(drawing([node("a", "TB", 0, 0), node("b", "CM", 100, 0)], [line("l", "CN", [[0, 0], [99, 0]])]))   # 1 unit = 0.1 m < 0.15 m
        self.assertFalse(any("free end" in w for w in out["warnings"]))

    def test_a_bent_line_keeps_its_length(self):
        out = core.process(drawing([node("a", "TB", 0, 0), node("b", "CM", 30, 40)], [line("l", "CN", [[0, 0], [30, 0], [30, 40]])]))
        self.assertEqual(out["stretches"][0]["length_m"], 7.0)


class TestTags(unittest.TestCase):
    def test_correlative_tags_per_prefix(self):
        out = core.process(drawing([node("a", "CM", 0, 0), node("b", "CM", 100, 0), node("c", "CP", 200, 0)],
                                   [line("l1", "CN", [[0, 0], [100, 0]]), line("l2", "CN", [[100, 0], [200, 0]])]))
        self.assertEqual([n["tag"] for n in out["nodes"] if n["placed"]], ["CM-001", "CM-002", "CP-001"])
        self.assertEqual([s["tag"] for s in out["stretches"]], ["CN-001", "CN-002"])

    def test_a_tag_the_person_wrote_is_kept_and_not_reused(self):
        out = core.process(drawing([node("a", "CM", 0, 0, tag="CM-001"), node("b", "CM", 100, 0)], [line("l", "CN", [[0, 0], [100, 0]])]))
        self.assertEqual([n["tag"] for n in out["nodes"]], ["CM-001", "CM-002"])

    def test_a_duplicated_tag_gets_a_new_one_and_a_warning(self):
        out = core.process(drawing([node("a", "CM", 0, 0, tag="X-1"), node("b", "CM", 100, 0, tag="X-1")], [line("l", "CN", [[0, 0], [100, 0]])]))
        self.assertEqual(out["nodes"][1]["tag"], "CM-001")
        self.assertTrue(any("duplicated tag X-1" in w for w in out["warnings"]))

    def test_ids_must_be_unique(self):
        with self.assertRaisesRegex(core.PlanError, "used twice"):
            core.process(drawing([node("a", "CM", 0, 0), node("a", "CM", 10, 0)]))

    def test_unknown_kinds_are_refused(self):
        with self.assertRaisesRegex(core.PlanError, "does not exist in the discipline"):
            core.process(drawing([node("a", "ZZ", 0, 0)]))
        with self.assertRaisesRegex(core.PlanError, "unknown discipline"):
            core.process({**drawing(), "discipline": "nope"})


class TestSchedule(unittest.TestCase):
    def test_counts_lengths_and_the_route_of_each_circuit(self):
        out = core.process(load("input.json"))
        sch = out["schedule"]
        self.assertEqual({k: n for k, n in sch["nodes"].items() if n}, {"CM": 1, "CP": 1, "TB": 1, "LU": 1, "TG": 1, "HV": 1})
        self.assertEqual(sch["lines"]["BN"], {"lines": 1, "stretches": 4, "length_m": 40.0})
        self.assertEqual(sch["circuit_routes"]["C-01"]["length_m"], 60.0)
        self.assertEqual(sch["total_length_m"], round(sum(s["length_m"] for s in out["stretches"]), 4))

    def test_a_line_references_the_circuit_it_never_creates_one(self):
        out = core.process(drawing([node("a", "TB", 0, 0), node("b", "CM", 100, 0)], [line("l", "CA", [[0, 0], [100, 0]], circuit="C-07")]))
        self.assertEqual(list(out["schedule"]["circuit_routes"]), ["C-07"])
        self.assertTrue(out["stretches"][0]["tag"].startswith("CA-"))


class TestNetworks(unittest.TestCase):
    RULES = [{"id": "r", "topic": "min_slope", "applies_to": "sanitaria_cloacas", "status": "approved", "table": [{"diameter_mm": 110, "slope_pct": 2.0}]}]

    def sewer(self, **extra):
        return {**drawing([node("o", "BR", 0, 0), node("a", "CI", 100, 0), node("b", "CI", 200, 0)],
                          [line("trunk", "CC", [[0, 0], [200, 0]], attrs={"diameter_mm": 110})], outlet="o", outlet_invert_m=10.0), "discipline": "sanitaria_cloacas", **extra}

    def test_the_flow_goes_to_the_outlet_and_levels_rise_upstream_by_the_rule(self):
        out = core.process(self.sewer(), rules=self.RULES)
        self.assertEqual(out["network"]["invert_m"], {"a": 10.2, "b": 10.4, "o": 10.0})
        self.assertTrue(out["network"]["validated"])
        self.assertEqual({(s["flows_from"], s["flows_to"]) for s in out["stretches"]}, {("a", "o"), ("b", "a")})
        self.assertEqual(out["rules_used"], ["r"])

    def test_a_pending_rule_gives_provisional_levels_and_says_so(self):
        out = core.process(self.sewer(), rules=[dict(self.RULES[0], status="pending")])
        self.assertFalse(out["network"]["validated"])
        self.assertTrue(any("provisional" in w for w in out["warnings"]))

    def test_a_rule_without_values_gives_no_levels_and_invents_nothing(self):
        out = core.process(self.sewer())              # the shipped rule has no slope values yet
        self.assertIsNone(out["network"])
        self.assertTrue(any("no slope values" in w for w in out["warnings"]))

    def test_a_node_apart_from_the_outlet_is_reported(self):
        doc = self.sewer()
        doc["nodes"].append(node("far", "CI", 500, 500))
        out = core.process(doc, rules=self.RULES)
        self.assertTrue(any("far is not connected to the outlet" in w for w in out["warnings"]))

    def test_an_unknown_outlet_is_refused(self):
        with self.assertRaisesRegex(core.PlanError, "not a node"):
            core.process(self.sewer(outlet="zz"), rules=self.RULES)


class TestCircuitRoutes(unittest.TestCase):
    """A circuit goes from an origin node to a destination node over the drawn stretches; a conduit takes one circuit, a tray takes as many as come."""

    def network(self, circuits, **extra):
        nodes = [node("A", "TB", 0, 0), node("B", "CM", 200, 0), node("C", "CP", 200, 100)]
        lines = [line("bn", "BN", [[0, 0], [200, 0]]), line("cn1", "CN", [[200, 0], [200, 100]]), line("cn2", "CN", [[0, 0], [0, 200], [200, 200], [200, 100]])]
        return core.process(drawing(nodes, lines, circuits=circuits, **extra))

    def test_the_shortest_way_is_taken_and_every_stretch_records_what_it_carries(self):
        out = self.network([{"tag": "C-01", "from": "A", "to": "C"}])
        route = out["circuits"]["C-01"]
        self.assertEqual((route["found"], route["stretches"], route["length_m"]), (True, ["BN-001", "CN-001"], 30.0))
        carried = {s["tag"]: s.get("carries") for s in out["stretches"]}
        self.assertEqual(carried["BN-001"], [{"circuit": "C-01", "ternas": 1}])
        self.assertIsNone(carried["CN-002"])

    def test_ternas_multiply_the_cable_length_and_the_cables_in_the_tray(self):
        out = self.network([{"tag": "C-01", "from": "A", "to": "C", "ternas": 3}])
        self.assertEqual(out["circuits"]["C-01"]["cable_length_m"], 90.0)
        self.assertEqual(next(c for c in out["schedule"]["containers"] if c["tag"] == "BN-001")["cables"], 3)

    def test_a_tray_carries_several_circuits_and_counts_their_cables(self):
        out = self.network([{"tag": "C-01", "from": "A", "to": "B", "ternas": 2}, {"tag": "C-02", "from": "A", "to": "B"}])
        tray = next(c for c in out["schedule"]["containers"] if c["tag"] == "BN-001")
        self.assertEqual((tray["circuits"], tray["cables"]), (["C-01", "C-02"], 3))

    def test_the_moment_length_weighs_each_load_by_its_power_and_a_single_destination_is_its_own_distance(self):
        nodes = [node("A", "TB", 0, 0), node("L1", "LU", 100, 0, circuit="C-01", attrs={"potencia_w": 100}), node("L2", "LU", 300, 0, circuit="C-01", attrs={"potencia_w": 300})]
        out = core.process(drawing(nodes, [line("bn", "BN", [[0, 0], [300, 0]])], circuits=[{"tag": "C-01", "from": "A"}]))
        route = out["circuits"]["C-01"]
        self.assertEqual((route["max_distance_m"], route["moment_length_m"]), (30.0, 25.0))
        self.assertEqual([(d["tag"], d["distance_m"], d["power_w"]) for d in route["loads_detail"]], [("LU-001", 10.0, 100.0), ("LU-002", 30.0, 300.0)])
        nodes[2]["attrs"] = {}                                                                 # a load without power: all weigh the same
        equal = core.process(drawing(nodes, [line("bn", "BN", [[0, 0], [300, 0]])], circuits=[{"tag": "C-01", "from": "A"}]))["circuits"]["C-01"]
        self.assertEqual(equal["moment_length_m"], 20.0)
        single = self.network([{"tag": "C-01", "from": "A", "to": "C"}])["circuits"]["C-01"]
        self.assertEqual((single["moment_length_m"], single["max_distance_m"]), (30.0, 30.0))

    def test_a_conduit_used_by_one_circuit_is_blocked_for_the_next_which_takes_another_way(self):
        out = self.network([{"tag": "C-01", "from": "A", "to": "C"}, {"tag": "C-02", "from": "A", "to": "C"}])
        self.assertEqual(out["circuits"]["C-01"]["stretches"], ["BN-001", "CN-001"])
        second = out["circuits"]["C-02"]
        self.assertEqual((second["stretches"], second["length_m"]), (["CN-002"], 50.0))
        self.assertNotIn("C-02", [c["circuit"] for s in out["stretches"] if s["tag"] == "CN-001" for c in s["carries"]])

    def test_when_every_way_is_blocked_the_circuit_is_not_routed_and_says_why(self):
        out = self.network([{"tag": "C-01", "from": "A", "to": "C"}, {"tag": "C-02", "from": "A", "to": "C"}, {"tag": "C-03", "from": "A", "to": "C"}])
        self.assertFalse(out["circuits"]["C-03"]["found"])
        self.assertTrue(any("C-03" in w and "another circuit already uses" in w for w in out["warnings"]))

    def test_a_conduit_with_a_drawn_cable_of_another_circuit_is_blocked_too(self):
        nodes = [node("A", "TB", 0, 0), node("B", "CM", 200, 0)]
        lines = [line("cn", "CN", [[0, 0], [200, 0]], circuit="C-09")]
        out = core.process(drawing(nodes, lines, circuits=[{"tag": "C-01", "from": "A", "to": "B"}]))
        self.assertFalse(out["circuits"]["C-01"]["found"])

    def test_the_same_circuit_may_use_a_conduit_again(self):
        nodes = [node("A", "TB", 0, 0), node("B", "CM", 200, 0)]
        lines = [line("cn", "CN", [[0, 0], [200, 0]], circuit="C-01")]
        out = core.process(drawing(nodes, lines, circuits=[{"tag": "C-01", "from": "A", "to": "B"}]))
        self.assertTrue(out["circuits"]["C-01"]["found"])

    def test_a_node_to_pass_through_forces_the_way(self):
        out = self.network([{"tag": "C-01", "from": "A", "to": "C", "via": ["B"]}])
        self.assertEqual(out["circuits"]["C-01"]["stretches"], ["BN-001", "CN-001"])

    def test_a_circuit_that_cannot_be_routed_is_reported_not_refused(self):
        for circuit, text in (({"tag": "C-01", "from": "A", "to": "ZZ"}, "no longer exists"), ({"tag": "C-01", "from": "A", "to": "A"}, "same node"),
                              ({"tag": "", "from": "A", "to": "C"}, "has no tag")):
            out = self.network([circuit])
            self.assertEqual(out["circuits"], {}, text)
            self.assertTrue(any(text in w for w in out["warnings"]), text)

    def test_a_circuit_defined_twice_keeps_the_first(self):
        out = self.network([{"tag": "C-01", "from": "A", "to": "B"}, {"tag": "C-01", "from": "A", "to": "C"}])
        self.assertEqual(out["circuits"]["C-01"]["to"], "B")
        self.assertTrue(any("defined twice" in w for w in out["warnings"]))

    def test_two_separate_networks_have_no_way_between_them(self):
        nodes = [node("A", "TB", 0, 0), node("B", "CM", 100, 0), node("X", "CM", 0, 500), node("Y", "CM", 100, 500)]
        lines = [line("l1", "BN", [[0, 0], [100, 0]]), line("l2", "BN", [[0, 500], [100, 500]])]
        out = core.process(drawing(nodes, lines, circuits=[{"tag": "C-01", "from": "A", "to": "Y"}]))
        self.assertFalse(out["circuits"]["C-01"]["found"])
        self.assertTrue(any("there is no way from" in w for w in out["warnings"]))


class TestLoads(unittest.TestCase):
    """Luminaires, sockets and HVAC units are placed, assigned to a circuit, and the circuit is routed from its origin to all of them."""

    def tree(self, circuits, loads, extra_nodes=(), extra_lines=()):
        nodes = [node("A", "TB", 0, 0), *loads, *extra_nodes]
        lines = [line("trunk", "BN", [[0, 0], [300, 0]]), line("branch", "BN", [[100, 0], [100, 100]]), *extra_lines]
        return core.process(drawing(nodes, lines, circuits=circuits))

    LOADS = [node("a", "LU", 100, 100, circuit="C-01"), node("b", "TG", 200, 0, circuit="C-01"), node("c", "HV", 300, 0, circuit="C-01")]

    def test_a_circuit_reaches_all_its_loads_and_the_shared_trunk_counts_once(self):
        out = self.tree([{"tag": "C-01", "from": "A"}], self.LOADS)
        route = out["circuits"]["C-01"]
        self.assertEqual((route["found"], route["loads"], route["length_m"]), (True, 3, 40.0))
        self.assertEqual(route["distance_to_load_m"], {"LU-001": 20.0, "TG-001": 20.0, "HV-001": 30.0})

    def test_the_loads_are_counted_per_circuit_and_kind(self):
        out = self.tree([{"tag": "C-01", "from": "A"}], self.LOADS)
        self.assertEqual(out["schedule"]["loads"]["by_circuit"], {"C-01": {"LU": 1, "TG": 1, "HV": 1}})
        self.assertEqual(out["schedule"]["loads"]["unassigned"], [])
        self.assertEqual({n["id"]: n.get("circuit") for n in out["nodes"] if n["placed"]}["a"], "C-01")

    def test_loads_without_a_circuit_are_listed_and_warned(self):
        out = self.tree([], [node("a", "LU", 100, 100), node("b", "TE", 200, 0)])
        self.assertEqual(out["schedule"]["loads"]["unassigned"], ["LU-001", "TE-001"])
        self.assertTrue(any("2 load(s) have no circuit yet" in w for w in out["warnings"]))

    def test_the_loads_of_a_circuit_nobody_routed_are_warned(self):
        out = self.tree([], self.LOADS)
        self.assertTrue(any("loads of circuit C-01 are not routed" in w for w in out["warnings"]))

    def test_a_load_apart_from_the_network_is_reported_and_the_rest_is_routed(self):
        far = node("z", "LU", 0, 900, circuit="C-01")
        out = self.tree([{"tag": "C-01", "from": "A"}], [*self.LOADS, far])
        route = out["circuits"]["C-01"]
        self.assertFalse(route["found"])
        self.assertEqual(route["unreached"], ["LU-002"])
        self.assertEqual(route["length_m"], 40.0)

    def test_a_destination_node_and_loads_can_be_combined(self):
        out = self.tree([{"tag": "C-01", "from": "A", "to": "c"}], [node("a", "LU", 100, 100, circuit="C-01"), node("c", "TB", 300, 0)])
        self.assertEqual(out["circuits"]["C-01"]["length_m"], 40.0)

    def test_a_circuit_without_destination_or_loads_is_reported(self):
        out = self.tree([{"tag": "C-01", "from": "A"}], [])
        self.assertEqual(out["circuits"], {})
        self.assertTrue(any("no destination node and no loads" in w for w in out["warnings"]))

    def test_a_conduit_to_the_loads_of_one_circuit_is_blocked_for_another(self):
        nodes = [node("A", "TB", 0, 0), node("p", "LU", 100, 0, circuit="C-01"), node("q", "LU", 100, 0 + 0, circuit="C-02")]
        out = core.process(drawing(nodes[:2] + [node("B", "TB", 0, 100)], [line("cn", "CN", [[0, 0], [100, 0]]), line("cn2", "CN", [[0, 100], [100, 0]])],
                                   circuits=[{"tag": "C-01", "from": "A"}, {"tag": "C-02", "from": "A"}]))
        self.assertTrue(out["circuits"]["C-01"]["found"])
        self.assertEqual(out["circuits"].get("C-02"), None)


class TestDxf(unittest.TestCase):
    def make(self, doc, version=""):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        path = Path(d.name) / "out.dxf"
        result = core.process(doc)
        warnings = dxfout.write_dxf(result, path, version)
        return result, path, warnings

    def test_the_dxf_has_layers_blocks_texts_and_passes_the_audit(self):
        result, path, warnings = self.make(load("input.json"))
        self.assertEqual(warnings, [])
        dxf = ezdxf.readfile(str(path))
        layers = {l.dxf.name for l in dxf.layers}
        self.assertTrue({"ELEC-BANDEJA", "ELEC-CANAL", "ELEC-CAMARA", "ELEC-CAJA", "ELEC-TABLERO", "PLAN-TAG", "PLAN-NODO"} <= layers)
        kinds = [e.dxftype() for e in dxf.modelspace()]
        self.assertEqual(kinds.count("LWPOLYLINE"), len(result["stretches"]))
        self.assertEqual(kinds.count("TEXT"), len(result["stretches"]))
        self.assertEqual(kinds.count("INSERT"), 6)
        tags = {a.dxf.text for e in dxf.modelspace().query("INSERT") for a in e.attribs}
        self.assertEqual(tags, {"TB-001", "CM-001", "CP-001", "LU-001", "TG-001", "HV-001"})
        self.assertEqual(dxf.units, 6)

    def test_every_offered_version_writes_a_file_that_reads_back(self):
        for v, code in (("R2000", "AC1015"), ("R2013", "AC1027"), ("R2018", "AC1032")):
            _, path, warnings = self.make(load("input.json"), v)
            self.assertEqual(warnings, [], v)
            self.assertEqual(ezdxf.readfile(str(path)).dxfversion, code)

    def test_the_default_version_is_the_latest_offered(self):
        _, path, _ = self.make(load("input.json"))
        self.assertEqual(ezdxf.readfile(str(path)).dxfversion, "AC1032")
        self.assertEqual(dxfout.versions()[-1], "R2018")

    def test_an_unknown_version_is_refused(self):
        with self.assertRaisesRegex(core.PlanError, "not available"):
            self.make(load("input.json"), "R14")

    def test_lengths_in_the_dxf_are_real_metres(self):
        _, path, _ = self.make(load("input.json"))
        total = 0.0
        for e in ezdxf.readfile(str(path)).modelspace().query("LWPOLYLINE"):
            pts = list(e.get_points("xy"))
            total += sum(((pts[i + 1][0] - pts[i][0]) ** 2 + (pts[i + 1][1] - pts[i][1]) ** 2) ** 0.5 for i in range(len(pts) - 1))
        self.assertAlmostEqual(total, core.process(load("input.json"))["schedule"]["total_length_m"], places=3)


class TestJobs(unittest.TestCase):
    def test_a_job_reports_its_status_and_ends_with_the_files(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            jobs.start(load("input.json"), out).join(30)
            st = json.loads((out / "status.json").read_text(encoding="utf-8"))
            self.assertEqual((st["state"], st["progress"]), ("done", 1.0))
            self.assertTrue((out / "result.json").exists())
            self.assertTrue((out / "PLAN-L0.dxf").exists())

    def test_bad_input_fails_in_the_status_with_a_clear_message(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            bad = load("input.json")
            bad["plan"]["level"] = "PB"
            jobs.start(bad, out).join(30)
            st = json.loads((out / "status.json").read_text(encoding="utf-8"))
            self.assertEqual(st["state"], "failed")
            self.assertIn("level", st["error"])


class TestDisciplines(unittest.TestCase):
    def test_every_discipline_with_tools_draws_in_layers_and_symbols_that_exist(self):
        from epc_dxf import layers
        known = {k.split(".", 1)[1] for k in layers.defaults() if k.startswith("plan.")}
        for pid in core.profiles():
            prof = core.load_profile(pid)
            for k in prof["tramos"] + prof["nodos"]:
                self.assertIn(k["capa_dxf"], known, f"{pid}:{k['id']}")
                self.assertTrue(k["simbolo_2d"] == "linea_simple" or k["simbolo_2d"] in core.SYMBOLS, f"{pid}:{k['id']}")

    def test_every_subdiscipline_offers_kinds_its_discipline_has(self):
        for pid in core.profiles():
            prof = core.load_profile(pid)
            kinds = {k["id"] for k in prof["tramos"] + prof["nodos"]}
            ids = [s["id"] for s in prof.get("subdisciplinas", [])]
            self.assertEqual(len(ids), len(set(ids)), pid)
            for s in prof.get("subdisciplinas", []):
                self.assertTrue(s["tipos"] and set(s["tipos"]) <= kinds, f"{pid}:{s['id']}")
        electrical = {s["id"]: set(s["tipos"]) for s in core.load_profile("electrica_BT")["subdisciplinas"]}
        self.assertTrue({"LU", "IN"} <= electrical["iluminacion"] and not {"TG", "TR"} & electrical["iluminacion"])      # each one has its own symbols
        self.assertTrue({"TR", "CE", "MT"} <= electrical["distribucion_mt"])

    def test_a_drawing_of_each_new_discipline_is_processed(self):
        for pid in ("hvac", "pci", "comunicaciones", "civil", "mecanica", "instrumentacion", "arquitectura"):
            prof = core.load_profile(pid)
            kinds = prof["nodos"] * 2                                         # a stretch needs two points: at least two nodes
            nodes = [{"id": f"n{i}", "kind": k["id"], "x": 10 + i * 20, "y": 10} for i, k in enumerate(kinds)]
            ln = [{"id": "l1", "kind": prof["tramos"][0]["id"], "points": [[10, 10], [10 + 20 * (len(nodes) - 1), 10]]}]
            out = core.process({**drawing(nodes, ln), "discipline": pid})
            self.assertEqual(out["schedule"]["lines"][prof["tramos"][0]["id"]]["lines"], 1, pid)


if __name__ == "__main__":
    unittest.main()


class TestPlenum(unittest.TestCase):
    """The plenum (a vertical shaft between levels): a symbol drawn as an SVG, a kind of node with its height, a layer of its own."""

    def test_the_symbol_is_read_from_its_svg(self):
        prims = core.SYMBOLS["pleno"]["prims"]
        self.assertEqual([p["t"] for p in prims], ["rect", "circle", "line", "line", "line", "line", "line"])
        self.assertEqual(prims[0], {"t": "rect", "w": 1.0, "h": 1.0})

    def test_a_plenum_is_a_node_with_a_shared_id_and_a_height_and_goes_to_its_layer_in_the_dxf(self):
        out = core.process(drawing([node("p0", "PL", 100, 100, attrs={"pleno": "P-01", "altura_m": 3.2})], []))
        placed = next(n for n in out["nodes"] if n["kind"] == "PL")
        self.assertEqual((placed["tag"], placed["attrs"]), ("PL-001", {"pleno": "P-01", "altura_m": 3.2}))
        with tempfile.TemporaryDirectory() as t:
            path = Path(t) / "plan.dxf"
            dxfout.write_dxf(out, path)
            doc = ezdxf.readfile(str(path))
            self.assertIn("ELEC-PLENO", {lay.dxf.name for lay in doc.layers})
            self.assertTrue(any(e.dxftype() == "INSERT" and e.dxf.layer == "ELEC-PLENO" for e in doc.modelspace()))


class TestRouteThroughPlenums(unittest.TestCase):
    """A cable that goes up or down through plenums adds the height of each one it passes, however many there are."""

    def run_plan(self, heights, circuits):
        pa, pb = ({"pleno": f"P-0{i}", "altura_m": h} if h is not None else {"pleno": f"P-0{i}"} for i, h in enumerate(heights, 1))
        nodes = [node("A", "TB", 0, 0), node("P1", "PL", 100, 0, attrs=pa), node("P2", "PL", 200, 0, attrs=pb), node("C", "CP", 300, 0)]
        return core.process(drawing(nodes, [line("bn", "BN", [[0, 0], [300, 0]])], circuits=circuits))

    def test_each_plenum_on_the_way_adds_its_own_height(self):
        out = self.run_plan([3.2, 2.0], [{"tag": "C-01", "from": "A", "to": "C"}, {"tag": "C-02", "from": "A", "to": "P1"}])
        two, one = out["circuits"]["C-01"], out["circuits"]["C-02"]
        self.assertEqual((two["plenums"], two["rise_m"], two["length_m"]), (["PL-001", "PL-002"], 5.2, 35.2))
        self.assertEqual((one["plenums"], one["length_m"]), (["PL-001"], 13.2))
        self.assertEqual(two["cable_length_m"], 35.2)

    def test_a_route_that_goes_through_no_plenum_is_unchanged(self):
        out = self.run_plan([3.2, 2.0], [{"tag": "C-01", "from": "A", "to": "A"}])
        self.assertNotIn("C-01", out["circuits"])
        flat = core.process(drawing([node("A", "TB", 0, 0), node("C", "CP", 300, 0)], [line("bn", "BN", [[0, 0], [300, 0]])], circuits=[{"tag": "C-01", "from": "A", "to": "C"}]))["circuits"]["C-01"]
        self.assertEqual((flat["plenums"], flat["rise_m"], flat["length_m"]), ([], 0.0, 30.0))

    def test_a_plenum_without_a_height_is_reported_and_adds_nothing(self):
        out = self.run_plan([None, 2.0], [{"tag": "C-01", "from": "A", "to": "C"}])
        self.assertEqual(out["circuits"]["C-01"]["length_m"], 32.0)
        self.assertTrue(any("has no height" in w for w in out["warnings"]))
