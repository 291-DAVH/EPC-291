import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE))

from epc_lighting import cu  # noqa: E402
from epc_lighting.tables import generic_table, parse_cu_table  # noqa: E402
import helpers  # noqa: E402

TABLE = generic_table()


class TestLookup(unittest.TestCase):
    def test_a_node_of_the_table_is_read_directly(self):
        value, kind = cu.lookup(TABLE, 1.0, (0.7, 0.7, 0.5))
        self.assertAlmostEqual(value, 1.00)
        self.assertEqual(kind, "table_exact")

    def test_between_rows_it_interpolates_along_k(self):
        value, kind = cu.lookup(TABLE, 1.25, (0.7, 0.7, 0.5))
        self.assertAlmostEqual(value, 1.08)
        self.assertEqual(kind, "table_interpolated_axis")

    def test_between_columns_it_stays_inside_the_neighbouring_values(self):
        value, kind = cu.lookup(TABLE, 1.0, (0.6, 0.6, 0.35))
        self.assertEqual(kind, "table_interpolated_reflectance")
        self.assertTrue(0.77 < value < 1.00)

    def test_outside_the_table_the_nearest_row_is_kept(self):
        value, kind = cu.lookup(TABLE, 10.0, (0.7, 0.7, 0.5))
        self.assertAlmostEqual(value, 1.33)
        self.assertEqual(kind, "table_out_of_range")

    def test_lookup_is_deterministic(self):
        self.assertEqual(cu.lookup(TABLE, 1.37, (0.55, 0.75, 0.15)), cu.lookup(TABLE, 1.37, (0.55, 0.75, 0.15)))

    def test_a_single_row_table_works(self):
        table = parse_cu_table({"axis_values": [1.0], "reflectances": [[0.5, 0.5, 0.2]], "values": [[0.6]]}, "t")
        self.assertAlmostEqual(cu.lookup(table, 2.0, (0.5, 0.5, 0.2))[0], 0.6)


class TestResolve(unittest.TestCase):
    AXES = {"k": 1.37, "rcr": 5 / 1.37}
    REFL = (0.6, 0.7, 0.2)

    def test_room_value_wins_over_everything(self):
        room, lum = helpers.first_room(coefficient_of_utilisation=0.9)
        est = cu.resolve(room, lum, self.AXES, self.REFL, [])
        self.assertEqual((est.value, est.confidence), (0.9, 1.0))

    def test_luminaire_value_comes_next(self):
        proj = helpers.project([helpers.room_dict(coefficient_of_utilisation=None)], [helpers.luminaire_dict(cu=0.8)])
        room, lum = proj.rooms[0], proj.luminaires["L1"]
        self.assertEqual(cu.resolve(room, lum, self.AXES, self.REFL, []).value, 0.8)

    def test_luminaire_table_then_generic_with_a_warning(self):
        proj = helpers.project([helpers.room_dict(coefficient_of_utilisation=None)])
        room, lum = proj.rooms[0], proj.luminaires["L1"]
        warnings = []
        est = cu.resolve(room, lum, self.AXES, self.REFL, warnings)
        self.assertEqual(est.confidence, 0.4)
        self.assertTrue(any("illustrative" in w for w in warnings))

    def test_a_table_given_with_the_luminaire_is_used(self):
        table = {"axis_values": [1.0, 2.0], "reflectances": [[0.6, 0.7, 0.2]], "values": [[0.5], [0.7]], "unit": "fraction"}
        proj = helpers.project([helpers.room_dict(coefficient_of_utilisation=None)], [helpers.luminaire_dict(cu_table=table)])
        est = cu.resolve(proj.rooms[0], proj.luminaires["L1"], {"k": 1.5, "rcr": 3.33}, self.REFL, [])
        self.assertAlmostEqual(est.value, 0.6)
        self.assertEqual(est.confidence, 0.9)

    def test_a_table_on_the_rcr_axis_is_read_with_rcr(self):
        table = {"axis": "rcr", "axis_values": [1.0, 5.0], "reflectances": [[0.6, 0.7, 0.2]], "values": [[0.9], [0.5]]}
        proj = helpers.project([helpers.room_dict(coefficient_of_utilisation=None)], [helpers.luminaire_dict(cu_table=table)])
        est = cu.resolve(proj.rooms[0], proj.luminaires["L1"], {"k": 2.5, "rcr": 2.0}, self.REFL, [])
        self.assertAlmostEqual(est.value, 0.8)

    def test_a_cu_above_one_is_flagged(self):
        room, lum = helpers.first_room(coefficient_of_utilisation=1.03)
        warnings = []
        cu.resolve(room, lum, self.AXES, self.REFL, warnings)
        self.assertTrue(any("above 1" in w for w in warnings))


if __name__ == "__main__":
    unittest.main()
