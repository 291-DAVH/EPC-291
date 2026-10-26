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
        self.assertEqual(sch["nodes"], {"CM": 1, "CP": 1, "TB": 1})
        self.assertEqual(sch["lines"]["BN"], {"lines": 1, "stretches": 2, "length_m": 40.0})
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
        self.assertEqual(kinds.count("INSERT"), 3)
        tags = {a.dxf.text for e in dxf.modelspace().query("INSERT") for a in e.attribs}
        self.assertEqual(tags, {"TB-001", "CM-001", "CP-001"})
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


if __name__ == "__main__":
    unittest.main()
