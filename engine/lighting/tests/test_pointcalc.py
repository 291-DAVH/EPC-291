import math
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE))

from epc_lighting import photometry, pointcalc, run  # noqa: E402
from epc_lighting.model import LightingError, Photometry  # noqa: E402
from epc_lighting.pointcalc import Source  # noqa: E402
from epc_lighting.tables import parse_photometry  # noqa: E402
import helpers  # noqa: E402

UNIFORM = Photometry((0.0, 90.0), (0.0,), ((500.0, 500.0),))


class TestPhotometry(unittest.TestCase):
    def test_intensity_scales_with_lamp_flux(self):
        self.assertAlmostEqual(photometry.intensity_cd(UNIFORM, 30, 0, 2000), 1000.0)

    def test_between_angles_it_is_linear_and_beyond_the_last_it_is_zero(self):
        phot = Photometry((0.0, 60.0), (0.0,), ((400.0, 100.0),))
        self.assertAlmostEqual(photometry.intensity_cd(phot, 30, 0, 1000), 250.0)
        self.assertEqual(photometry.intensity_cd(phot, 75, 0, 1000), 0.0)

    def test_c_planes_interpolate_and_wrap_at_360(self):
        phot = parse_photometry({"gamma_deg": [0, 90], "c_deg": [0, 180], "intensity_cd_per_klm": [[100, 100], [300, 300]]}, "p")
        self.assertAlmostEqual(photometry.intensity_cd(phot, 10, 90, 1000), 200.0)
        self.assertAlmostEqual(photometry.intensity_cd(phot, 10, 270, 1000), 200.0)
        self.assertAlmostEqual(photometry.intensity_cd(phot, 10, 360, 1000), 100.0)
        self.assertAlmostEqual(photometry.intensity_cd(phot, 10, -90, 1000), 200.0)

    def test_an_isotropic_table_emits_all_the_lamp_flux(self):
        iso = Photometry((0.0, 180.0), (0.0,), ((1000 / (4 * math.pi),) * 2,))
        self.assertAlmostEqual(photometry.emitted_fraction(iso), 1.0, delta=0.01)

    def test_a_hemisphere_table_reports_its_output_ratio(self):
        weak = Photometry((0.0, 90.0), (0.0,), ((100.0, 100.0),))
        full = Photometry((0.0, 90.0), (0.0,), ((1000 / (2 * math.pi),) * 2,))
        self.assertAlmostEqual(photometry.emitted_fraction(weak), 0.628, delta=0.01)
        self.assertAlmostEqual(photometry.emitted_fraction(full), 1.0, delta=0.01)
        self.assertGreater(photometry.emitted_fraction(UNIFORM), 1.0)  # 500 cd/klm all over a hemisphere is impossible


class TestIlluminance(unittest.TestCase):
    def test_a_point_below_a_uniform_source_gets_i_over_h_squared(self):
        src = Source(0, 0, 2.0, UNIFORM, 1000.0)
        self.assertAlmostEqual(pointcalc.illuminance_at([src], (0, 0, 0)), 500 / 4)

    def test_mirror_points_get_the_same_light(self):
        a, b = Source(1, 2, 2.5, UNIFORM, 1000.0), Source(5, 2, 2.5, UNIFORM, 1000.0)
        left = pointcalc.illuminance_at([a, b], (0.5, 1.0, 0.85))
        right = pointcalc.illuminance_at([a, b], (5.5, 1.0, 0.85))
        self.assertAlmostEqual(left, right)

    def test_a_point_above_the_source_gets_nothing_on_a_horizontal_plane(self):
        src = Source(0, 0, 1.0, UNIFORM, 1000.0)
        self.assertEqual(pointcalc.illuminance_at([src], (0, 0, 2.0)), 0.0)

    def test_two_sources_add_up(self):
        one = Source(0, 0, 2.0, UNIFORM, 1000.0)
        self.assertAlmostEqual(pointcalc.illuminance_at([one, one], (0, 0, 0)), 2 * pointcalc.illuminance_at([one], (0, 0, 0)))


class TestGrid(unittest.TestCase):
    def test_cell_centres_cover_the_room(self):
        points = pointcalc.grid_points(4, 6, 0.5)
        self.assertEqual(len(points), 12 * 8)
        self.assertAlmostEqual(points[0][0], 0.25)
        self.assertAlmostEqual(max(p[0] for p in points), 5.75)

    def test_a_huge_room_is_coarsened_to_the_point_limit(self):
        self.assertLessEqual(len(pointcalc.grid_points(200, 300, 0.5)), 2500)


class TestGrid(unittest.TestCase):
    def test_the_shape_of_the_grid_is_the_one_of_its_points(self):
        nx, ny = pointcalc.grid_shape(4, 6, 0.5)
        self.assertEqual((nx, ny), (12, 8))
        self.assertEqual(len(pointcalc.grid_points(4, 6, 0.5)), nx * ny)

    def test_the_grid_is_only_given_when_asked_and_has_one_value_per_cell_row_by_row(self):
        lone = [Source(1.0, 1.0, 3.0, UNIFORM, 1000.0)]
        plain, _ = pointcalc.calculate(lone, 2.0, 2.0, 0.0, 1.0, 0.8)
        self.assertNotIn("grid", plain)
        report, _ = pointcalc.calculate(lone, 2.0, 2.0, 0.0, 1.0, 0.8, with_grid=True)
        grid = report["grid"]
        self.assertEqual((grid["nx"], grid["ny"], grid["dx_m"], grid["dy_m"]), (2, 2, 1.0, 1.0))
        self.assertEqual(len(grid["maintained_lux"]), 4)
        self.assertAlmostEqual(grid["maintained_lux"][0], grid["maintained_lux"][3], places=1)           # symmetric under a source in the middle
        self.assertAlmostEqual(sum(grid["maintained_lux"]) / 4, report["avg_lux"], delta=0.2)             # the same figures as the statistics


class TestInPipeline(unittest.TestCase):
    def test_the_option_reaches_the_report_of_a_room_with_photometry(self):
        from epc_lighting import Options
        pts = run(helpers.document([helpers.room_dict()]), Options(return_grid=True)).as_dict()["rooms"][0]["points"]
        self.assertEqual(len(pts["grid"]["maintained_lux"]), pts["grid"]["nx"] * pts["grid"]["ny"])
        self.assertNotIn("grid", self._points())


    def _points(self, **kw):
        return run(helpers.document([helpers.room_dict(**kw)])).as_dict()["rooms"][0]["points"]

    def test_the_grid_report_has_the_uniformity_figures(self):
        pts = self._points()
        self.assertTrue(pts["computed"])
        for key in ("min_lux", "avg_lux", "max_lux", "min_over_avg", "max_over_avg", "photometry_output_ratio"):
            self.assertIn(key, pts)
        self.assertLess(pts["min_lux"], pts["avg_lux"])

    def test_requested_points_are_reported_with_their_normal(self):
        pts = self._points(points=[{"id": "P1", "x_m": 1.5, "y_m": 2.0}, {"id": "P2", "x_m": 1.5, "y_m": 2.0, "normal": [1, 0, 0]}])["points"]
        self.assertEqual([p["id"] for p in pts], ["P1", "P2"])
        self.assertGreater(pts[0]["maintained_lux"], pts[1]["maintained_lux"])
        self.assertAlmostEqual(pts[0]["maintained_lux"], pts[0]["initial_lux"] * 0.8, places=2)

    def test_without_photometry_it_says_why_instead_of_failing(self):
        lum = helpers.luminaire_dict()
        del lum["photometry"]
        doc = helpers.document([helpers.room_dict()], [lum])
        pts = run(doc).as_dict()["rooms"][0]["points"]
        self.assertEqual(pts["computed"], False)
        self.assertIn("no photometry", pts["reason"])

    def test_asking_for_points_without_photometry_warns(self):
        lum = helpers.luminaire_dict()
        del lum["photometry"]
        doc = helpers.document([helpers.room_dict(points=[{"x_m": 1, "y_m": 1}])], [lum])
        self.assertTrue(any("has no photometry" in w for w in run(doc).warnings))

    def test_a_table_that_emits_more_than_the_lamps_is_flagged(self):
        phot = {"gamma_deg": [0, 90, 180], "intensity_cd_per_klm": [2000, 2000, 2000]}
        doc = helpers.document([helpers.room_dict()], [helpers.luminaire_dict(photometry=phot)])
        self.assertTrue(any("emits" in w and "lamp flux" in w for w in run(doc).warnings))

    def test_points_can_be_switched_off(self):
        from epc_lighting.model import Options
        pts = run(helpers.document(), Options(compute_points=False)).as_dict()["rooms"][0]["points"]
        self.assertFalse(pts["computed"])

    def test_a_point_outside_the_room_is_refused(self):
        with self.assertRaisesRegex(LightingError, r"x_m: must be at most 6"):
            run(helpers.document([helpers.room_dict(points=[{"x_m": 9, "y_m": 1}])]))


if __name__ == "__main__":
    unittest.main()
