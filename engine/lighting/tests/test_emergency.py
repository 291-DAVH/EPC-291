"""Antipanic emergency lighting, escape routes, the UGR comparison and the flux/direct check. The worked cases are those of `epc_aea90364.lighting` (CAL-001), whose results this engine keeps."""
import math
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE))

from epc_lighting import checks, emergency, run  # noqa: E402
from epc_lighting.model import LightingError  # noqa: E402
import helpers  # noqa: E402


class TestLambertian(unittest.TestCase):
    def test_under_the_luminaire_it_is_flux_over_pi_h_squared(self):
        self.assertAlmostEqual(emergency.lambertian_lux(1000, 2.0, 0, 0), 79.577, places=2)          # 1000 / (pi * 4)

    def test_off_axis_it_falls_with_the_fourth_power_of_the_distance(self):
        self.assertAlmostEqual(emergency.lambertian_lux(1000, 2.0, 0.9, 1.2), 32.595, places=2)      # d^2 = 6.25: 318.31 * 4 / 39.0625

    def test_the_grid_has_a_luminaire_in_the_centre_of_each_cell(self):
        self.assertEqual(emergency.grid_positions(4, 2, 2, 1), [(1.0, 1.0), (3.0, 1.0)])


class TestEvaluate(unittest.TestCase):
    def test_a_2_by_2_room_with_one_luminaire_gives_the_hand_calculated_figures(self):
        # flux = pi, h = 1: E = 1 / d^4 -> centre 1, edge middles 1/4 (4 points), corners 1/9 (4 points)
        r = emergency.evaluate(2, 2, [(1, 1)], math.pi, 1.0, 0.0, 1.0)
        self.assertEqual(r["points"], 9)
        self.assertAlmostEqual(r["e_min"], 1 / 9, places=6)
        self.assertAlmostEqual(r["e_max"], 1.0, places=6)
        self.assertAlmostEqual(r["e_avg"], 22 / 81, places=6)
        self.assertAlmostEqual(r["max_over_min"], 9.0, places=6)

    def test_the_band_along_the_walls_is_left_out(self):
        r = emergency.evaluate(4, 4, [(2, 2)], math.pi, 1.0, 1.0, 1.0)
        self.assertEqual(r["points"], 9)
        self.assertAlmostEqual(r["e_min"], 1 / 9, places=6)

    def test_a_band_that_takes_the_whole_room_or_a_negative_one_is_refused(self):
        with self.assertRaises(LightingError):
            emergency.evaluate(4, 4, [(2, 2)], 100, 1.0, 2.0, 1.0)
        with self.assertRaises(LightingError):
            emergency.evaluate(4, 4, [(2, 2)], 100, 1.0, -1.0, 1.0)


class TestAntipanic(unittest.TestCase):
    def size(self, flux, **kw):
        args = dict(length_m=2, width_m=2, height_m=1.0, flux_lm=flux, e_min_lux=0.5, ratio_max=40.0, band_m=0.0, step_m=1.0, n_max=1, spacing_ratio_max=1.5)
        return emergency.size_antipanic(**{**args, **kw})

    def test_one_luminaire_of_15_lm_complies(self):
        r = self.size(15)
        self.assertEqual((r["count"], r["columns"], r["rows"]), (1, 1, 1))
        self.assertAlmostEqual(r["e_min"], 0.530516, places=5)                                        # 15 / (9 pi)
        self.assertAlmostEqual(r["e_max"], 4.774648, places=5)                                        # 15 / pi
        self.assertAlmostEqual(r["max_over_min"], 9.0, places=6)

    def test_not_enough_flux_or_a_ratio_too_tight_gives_no_grid(self):
        self.assertEqual(self.size(13), {})                                                           # 13 / (9 pi) = 0.46 lux
        self.assertEqual(self.size(15, ratio_max=8.0), {})

    def test_the_minimum_illuminance_is_a_parameter(self):
        self.assertEqual(self.size(13, e_min_lux=0.4)["count"], 1)

    def test_more_luminaires_are_tried_in_grids_whose_spacings_stay_alike(self):
        r = emergency.size_antipanic(20, 20, 4.0, 300, 0.5, 40.0, 0.5, 0.5, 400, 1.5)
        self.assertEqual(r["count"], r["columns"] * r["rows"])
        self.assertGreaterEqual(r["e_min"], 0.5)
        self.assertLessEqual(r["max_over_min"], 40.0)
        sx, sy = 20 / r["columns"], 20 / r["rows"]
        self.assertLessEqual(max(sx, sy) / min(sx, sy), 1.5 + 1e-9)


class TestRouteAxis(unittest.TestCase):
    def test_under_one_luminaire_and_between_two(self):
        two = [(0.0, 0.0), (4.0, 0.0)]
        r = emergency.route_axis(two, 1000, 2.0, (0.0, 0.0), (4.0, 0.0), 2.0)
        self.assertEqual(r["points"], 3)
        self.assertAlmostEqual(r["e_max"], 1000 / math.pi * 0.26, places=6)                           # x = 0: 1/4 + 4/400
        self.assertAlmostEqual(r["e_min"], 1000 / math.pi * 0.125, places=6)                          # x = 2: two luminaires at d^2 = 8

    def test_the_end_of_the_route_is_included_and_a_route_without_length_is_refused(self):
        self.assertEqual(emergency.route_axis([(0.0, 0.0)], 1000, 2.0, (0.0, 0.0), (5.0, 0.0), 2.0)["points"], 4)          # 0, 2, 4 and 5
        with self.assertRaises(LightingError):
            emergency.route_axis([(0.0, 0.0)], 1000, 2.0, (1.0, 1.0), (1.0, 1.0), 2.0)


class TestChecks(unittest.TestCase):
    def test_ugr_is_not_verifiable_without_a_value_or_a_limit_and_compares_when_it_has_both(self):
        self.assertEqual(checks.ugr(None, 19)["result"], "not_verifiable")
        self.assertEqual(checks.ugr(19, None)["result"], "not_verifiable")
        self.assertIsNone(checks.ugr(None, None)["complies"])
        self.assertEqual(checks.ugr(18.5, 19)["result"], "meets")
        self.assertEqual(checks.ugr(20, 19)["result"], "does_not_meet")
        with self.assertRaises(LightingError):
            checks.ugr(-1, 19)

    def test_the_direct_average_must_reach_90_percent_of_the_target_and_the_flux_average_the_target(self):
        ok = checks.direct_check(500, 576, 465)                                                        # 0.9 * 500 = 450
        self.assertTrue(ok["complies"])
        self.assertEqual(ok["direct_min_acceptable_lux"], 450.0)
        self.assertFalse(checks.direct_check(500, 576, 440)["complies"])
        low_flux = checks.direct_check(500, 480, 470)
        self.assertEqual((low_flux["complies"], low_flux["flux_ok"], low_flux["direct_ok"]), (False, False, True))


class TestInThePipeline(unittest.TestCase):
    def doc(self, **item):
        room = {"id": "E1", "name": "Hall", "width_m": 20, "length_m": 20, "height_m": 4.0, "luminaire": "EM", **item}
        return {"schema_version": "1.0", "luminaires": [{"id": "EM", "name": "Emergency 3 W", "lamp_flux_lm": 300, "power_w": 3}], "emergency": [room]}

    def test_a_room_gets_its_grid_tags_and_figures(self):
        out = run(self.doc()).as_dict()
        e = out["emergency"][0]
        self.assertEqual(out["counts"]["emergency"], 1)
        self.assertTrue(e["verification"]["complies"])
        self.assertEqual(len(e["layout"]["positions"]), e["layout"]["installed"])
        self.assertEqual(e["layout"]["positions"][0]["tag"], "LE-001")
        self.assertEqual(e["layout"]["positions"][0]["z_m"], 4.0)
        self.assertEqual(e["energy"]["installed_power_w"], 3 * e["layout"]["installed"])
        self.assertEqual((e["criteria"]["min_lux"]["value"], e["criteria"]["min_lux"]["confidence"]), (0.5, 0.5))          # typical criteria say how sure they are

    def test_the_criteria_of_the_document_win_and_are_certain(self):
        e = run(self.doc(e_min_lux=1.0, max_over_min=20)).as_dict()["emergency"][0]
        self.assertEqual((e["criteria"]["min_lux"], e["criteria"]["max_over_min"]), ({"value": 1.0, "reason": "given in the document", "confidence": 1.0}, {"value": 20.0, "reason": "given in the document", "confidence": 1.0}))
        self.assertGreaterEqual(e["verification"]["min_lux"], 1.0)

    def test_the_escape_routes_are_checked_against_the_minimum_illuminance(self):
        e = run(self.doc(routes=[{"id": "R1", "start_m": [0, 10], "end_m": [20, 10]}, {"id": "R2", "start_m": [0, 10], "end_m": [20, 10], "e_min_lux": 1000}])).as_dict()["emergency"][0]
        self.assertEqual([(r["id"], r["complies"]) for r in e["routes"]], [("R1", True), ("R2", False)])
        self.assertEqual(e["routes"][1]["target_min_lux"], 1000.0)

    def test_a_room_no_grid_can_light_is_reported_as_not_complying_with_the_way_out(self):
        out = run(self.doc(e_min_lux=500)).as_dict()
        e = out["emergency"][0]
        self.assertEqual((e["verification"], e["layout"]["installed"], e["routes"]), ({"complies": False}, 0, []))
        self.assertTrue(any("no grid of up to" in w for w in out["warnings"]))

    def test_a_route_outside_the_room_and_a_badly_made_point_are_refused_with_what_to_correct(self):
        with self.assertRaises(LightingError) as outside:
            run(self.doc(routes=[{"start_m": [0, 0], "end_m": [30, 10]}]))
        self.assertIn("end_m[0]", str(outside.exception))
        with self.assertRaises(LightingError):
            run(self.doc(routes=[{"start_m": [0], "end_m": [1, 1]}]))
        with self.assertRaises(LightingError):
            run(self.doc(routes="x"))

    def test_the_ugr_of_a_room_is_compared_with_the_limit_of_its_activity(self):
        doc = helpers.document([helpers.room_dict(activity="education.classroom", ugr_calculated=17)])
        room = run(doc).as_dict()["rooms"][0]
        self.assertEqual(room["ugr"]["result"], "meets")
        self.assertEqual(room["ugr"]["limit"], room["target"]["ugr_l_max"])
        no_value = run(helpers.document([helpers.room_dict(activity="education.classroom")])).as_dict()["rooms"][0]
        self.assertEqual(no_value["ugr"]["result"], "not_verifiable")

    def test_a_room_with_points_says_whether_the_direct_average_backs_the_flux_one(self):
        room = run(helpers.document([helpers.room_dict()])).as_dict()["rooms"][0]
        self.assertEqual(set(room["verification"]["direct_check"]), {"complies", "flux_ok", "direct_ok", "direct_factor", "direct_min_acceptable_lux"})

    def test_the_document_and_the_result_keep_the_schemas(self):
        try:
            import jsonschema
        except ImportError:  # pragma: no cover
            self.skipTest("jsonschema is not installed")
        schemas = HERE.parent / "src" / "epc_lighting" / "schema"
        doc = self.doc(routes=[{"start_m": [0, 10], "end_m": [20, 10]}])
        jsonschema.validate(doc, __import__("json").loads((schemas / "input.schema.json").read_text(encoding="utf-8")))
        jsonschema.validate(run(doc).as_dict(), __import__("json").loads((schemas / "output.schema.json").read_text(encoding="utf-8")))

    def test_a_document_with_only_emergency_rooms_is_not_empty(self):
        self.assertFalse(any("nothing was calculated" in w for w in run(self.doc()).as_dict()["warnings"]))


if __name__ == "__main__":
    unittest.main()
