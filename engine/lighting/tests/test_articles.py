"""The engine reproduces the worked examples of the supplied articles."""
import math
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE))

from epc_lighting import run  # noqa: E402
from epc_lighting.pointcalc import Source, illuminance_at  # noqa: E402
from epc_lighting.document import parse_project  # noqa: E402
import helpers  # noqa: E402


class TestLumenMethodExample(unittest.TestCase):
    """UPV article: classroom 4 x 6 x 2.6 m, 300 lux, 2 x 2400 lm, CU 0.97, Cm 0.8."""

    @classmethod
    def setUpClass(cls):
        cls.room = run(helpers.document()).as_dict()["rooms"][0]

    def test_room_index(self):
        self.assertAlmostEqual(self.room["geometry"]["room_index_k"], 1.37, delta=0.005)

    def test_mounting_height_is_as_high_as_possible(self):
        self.assertEqual(self.room["geometry"]["mounting_height_m"]["value"], 1.75)

    def test_total_flux(self):
        self.assertAlmostEqual(self.room["flux"]["required_lm"], 9278.35, delta=0.01)

    def test_number_of_luminaires(self):
        self.assertAlmostEqual(self.room["flux"]["luminaires_exact"], 1.93, delta=0.005)
        self.assertEqual(self.room["flux"]["luminaires_required"], 2)

    def test_layout_is_one_row_of_two_at_1_5_3_1_5(self):
        lay = self.room["layout"]
        self.assertEqual((lay["rows_across_width"], lay["columns_along_length"]), (1, 2))
        self.assertEqual([p["x_m"] for p in lay["positions"]], [1.5, 4.5])
        self.assertEqual({p["y_m"] for p in lay["positions"]}, {2.0})
        self.assertEqual(lay["wall_distance_x_m"], 1.5)

    def test_spacing_of_3_m_against_2_8_m_is_accepted_as_the_article_does(self):
        check = self.room["layout"]["spacing_check"]["along_length"]
        self.assertEqual(check["status"], "within_tolerance")
        self.assertEqual(check["max_spacing_m"], 2.8)

    def test_verification_310_lux(self):
        self.assertAlmostEqual(self.room["verification"]["average_lux"], 310.40, delta=0.01)
        self.assertTrue(self.room["verification"]["complies"])


class TestLumenMethodExercise(unittest.TestCase):
    """The closing exercise: same luminaire, H = 3.5 m, 10 m wide; the article gives 21844.66 lm and 5 luminaires."""

    @classmethod
    def setUpClass(cls):
        room = helpers.room_dict(width_m=10, height_m=3.5, coefficient_of_utilisation=1.03)
        cls.room = run(helpers.document([room])).as_dict()["rooms"][0]

    def test_flux_and_count(self):
        self.assertAlmostEqual(self.room["flux"]["required_lm"], 21844.66, delta=0.01)
        self.assertEqual(self.room["flux"]["luminaires_required"], 5)

    def test_grid_is_3_by_2(self):
        lay = self.room["layout"]
        self.assertEqual((lay["rows_across_width"], lay["columns_along_length"]), (3, 2))

    def test_the_grid_holds_six_so_the_check_uses_six_not_the_articles_five(self):
        # The article verifies with 5 luminaires (329.6 lux) although its own 3 x 2 grid holds 6.
        self.assertEqual(self.room["layout"]["installed"], 6)
        self.assertAlmostEqual(self.room["verification"]["average_lux"], 329.6 * 6 / 5, delta=0.1)


class TestPointByPointExample(unittest.TestCase):
    """UPV point-by-point article: H = 1.25 m, d = 0.6 m, 525 cd/klm at 25.64 deg, 2000 lm -> 1050 cd, ~493 lux."""

    def setUp(self):
        lum = parse_project(helpers.document()).luminaires["L1"]
        self.source = Source(0.0, 0.0, 1.25, lum.photometry, 2000.0)
        self.point = (0.6, 0.0, 0.0)
        self.cos_a = 1.25 / math.hypot(1.25, 0.6)

    def test_horizontal_plane(self):
        expected = 1050 * self.cos_a ** 3 / 1.25 ** 2
        e = illuminance_at([self.source], self.point)
        self.assertAlmostEqual(e, expected, delta=0.5)
        self.assertAlmostEqual(e, 493.18, delta=1.5)  # the article rounds cos^3 to 0.73 and H^2 to 1.56

    def test_vertical_plane_facing_the_luminaire(self):
        sin_a = 0.6 / math.hypot(1.25, 0.6)
        expected = 1050 * self.cos_a ** 2 * sin_a / 1.25 ** 2
        self.assertAlmostEqual(illuminance_at([self.source], self.point, (-1.0, 0.0, 0.0)), expected, delta=0.5)

    def test_vertical_plane_facing_away_receives_nothing(self):
        self.assertEqual(illuminance_at([self.source], self.point, (1.0, 0.0, 0.0)), 0.0)


if __name__ == "__main__":
    unittest.main()
