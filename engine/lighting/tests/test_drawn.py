"""A room checked as it is drawn: the luminaires the person placed replace the grid the engine would arrange; and what the platform keeps about a luminaire besides what the engine reads."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE))

from epc_lighting import catalogue, run  # noqa: E402
from epc_lighting.model import LightingError  # noqa: E402
import helpers  # noqa: E402


def room_with(positions):
    return helpers.document([helpers.room_dict(positions=positions)])


class TestDrawnLuminaires(unittest.TestCase):
    def test_the_room_is_checked_with_the_luminaires_it_brings_and_no_grid_is_made(self):
        out = run(room_with([{"x_m": 1.5, "y_m": 2.0, "tag": "LU-007"}, {"x_m": 4.5, "y_m": 2.0}])).as_dict()["rooms"][0]
        lay = out["layout"]
        self.assertEqual((lay["drawn"], lay["installed"], lay["rows_across_width"]), (True, 2, 0))
        self.assertEqual([p["tag"] for p in lay["positions"]][0], "LU-007")
        self.assertTrue(lay["positions"][1]["tag"].startswith("LU-"))
        self.assertFalse(lay["spacing_check"]["along_length"]["checked"])
        self.assertEqual(lay["required"], run(helpers.document([helpers.room_dict()])).as_dict()["rooms"][0]["layout"]["required"])         # what the room needs does not depend on what is drawn

    def test_the_verdict_follows_how_many_are_drawn(self):
        few = run(room_with([{"x_m": 3, "y_m": 2}])).as_dict()["rooms"][0]
        many = run(room_with([{"x_m": 1, "y_m": 1}, {"x_m": 3, "y_m": 1}, {"x_m": 5, "y_m": 1}, {"x_m": 1, "y_m": 3}, {"x_m": 3, "y_m": 3}, {"x_m": 5, "y_m": 3}])).as_dict()["rooms"][0]
        self.assertFalse(few["verification"]["complies"])
        self.assertTrue(many["verification"]["complies"])
        self.assertLess(few["verification"]["average_lux"], many["verification"]["average_lux"])

    def test_the_points_are_calculated_from_where_the_luminaires_are(self):
        corner = run(room_with([{"x_m": 0.2, "y_m": 0.2}, {"x_m": 0.4, "y_m": 0.2}])).as_dict()["rooms"][0]["points"]
        middle = run(room_with([{"x_m": 3.0, "y_m": 2.0}, {"x_m": 3.2, "y_m": 2.0}])).as_dict()["rooms"][0]["points"]
        self.assertTrue(corner["computed"] and middle["computed"])
        self.assertLess(corner["min_over_avg"], middle["min_over_avg"])                                    # the same count, worse spread

    def test_the_height_of_each_luminaire_can_be_given(self):
        lay = run(room_with([{"x_m": 3, "y_m": 2, "z_m": 2.4}, {"x_m": 4, "y_m": 2}])).as_dict()["rooms"][0]["layout"]["positions"]
        self.assertEqual(lay[0]["z_m"], 2.4)
        self.assertGreater(lay[1]["z_m"], 2.4)                                                              # the mounting height of the room (work plane included)

    def test_what_is_not_a_luminaire_inside_the_room_is_refused_with_what_to_correct(self):
        for bad in ([], "x", [{"x_m": 1}], [{"x_m": 99, "y_m": 1}], [{"x_m": 1, "y_m": -1}], [{"x_m": 1, "y_m": 1, "z_m": 0}], [3]):
            with self.assertRaises(LightingError, msg=str(bad)):
                run(room_with(bad))
        with self.assertRaises(LightingError) as many:
            run(room_with([{"x_m": 1, "y_m": 1}] * 2001))
        self.assertIn("up to 2000", str(many.exception))


class TestWhatThePlatformKeepsOfALuminaire(unittest.TestCase):
    ENTRY = {"name": {"es": "Panel", "en": "Panel"}, "kind": "interior", "lamps": 1, "lamp_flux_lm": 3000, "power_w": 30}

    def test_the_power_factor_the_favourite_flag_and_the_group_are_valid_and_not_part_of_the_document(self):
        entry = {**self.ENTRY, "power_factor": 0.9, "favorite": True, "group": "Offices"}
        self.assertEqual(catalogue.check("p", entry), [])
        self.assertEqual(set(catalogue.as_document("p", entry)) & {"power_factor", "favorite", "group"}, set())

    def test_a_power_factor_out_of_range_a_flag_that_is_not_one_or_a_long_group_are_said(self):
        for extra, word in (({"power_factor": 0}, "power_factor"), ({"power_factor": 1.2}, "power_factor"), ({"power_factor": True}, "power_factor"), ({"favorite": "yes"}, "favorite"), ({"group": "x" * 41}, "group")):
            problems = catalogue.check("p", {**self.ENTRY, **extra})
            self.assertTrue(any(word in p for p in problems), (extra, problems))


if __name__ == "__main__":
    unittest.main()
