"""A circuit drawn over several levels: the parts the sheets measured are chained through the plenums (layout.levels)."""
import unittest

from epc.modules.layout.levels import Part, combine


def board_part(level="L0", to_exit=13.0, **extra):
    """The sheet of the board: from the board to the plenum (10 m of stretch and the 3 m height of the plenum)."""
    return Part(level, {"found": True, "unreached": [], "length_m": to_exit, "loads": 0, "loads_detail": [{"tag": "PL-001", "distance_m": to_exit, "power_w": None}], "destination_distance_m": to_exit, **extra}, None)


def upper_part(level="L1", loads=((8.0, None), (18.0, None)), length=18.0, rise=3.0, exit_at=None, **extra):
    """A sheet above: from the plenum (its height counted again on entry) to its loads."""
    detail = [{"tag": f"LU-{i}", "distance_m": d, "power_w": w} for i, (d, w) in enumerate(loads, 1)]
    return Part(level, {"found": True, "unreached": [], "length_m": length, "loads": len(detail), "loads_detail": detail, "destination_distance_m": exit_at, **extra}, rise)


class TestAcrossLevels(unittest.TestCase):
    def test_two_levels_chain_through_the_plenum_and_count_its_height_once(self):
        m = combine([board_part(), upper_part()])
        self.assertTrue(m["usable"])
        self.assertEqual(m["levels"], ["L0", "L1"])
        self.assertEqual(m["length_m"], 28.0)                                   # 13 up to the plenum + 18 on the upper sheet, minus the 3 m of the plenum counted on both
        self.assertEqual((m["max_distance_m"], m["moment_length_m"], m["loads_n"]), (28.0, 23.0, 2))     # loads 18 and 28 m from the board

    def test_the_loads_are_weighed_by_their_power_when_every_one_has_it(self):
        m = combine([board_part(), upper_part(loads=((8.0, 1000.0), (18.0, 3000.0)))])
        self.assertEqual(m["moment_length_m"], (18 * 1000 + 28 * 3000) / 4000)

    def test_a_third_level_starts_where_the_second_one_leaves(self):
        second = upper_part("L1", loads=((8.0, None),), length=13.0, exit_at=13.0)       # 10 m to the next plenum and 3 m of its height; its own entry height is 3 m
        third = upper_part("L2", loads=((5.0, None),), length=8.0)                        # 5 m from the plenum plus the 3 m of the entry
        m = combine([board_part(), second, third])
        self.assertTrue(m["usable"])
        self.assertEqual(m["length_m"], 13.0 + (13.0 - 3.0) + (8.0 - 3.0))
        self.assertEqual(m["max_distance_m"], 25.0)                                      # the second sheet is entered at 13 m and left at 13 + 10; the last load is 5 - 3 m past that entry

    def test_a_basement_and_an_upper_level_both_hang_from_the_board(self):
        down = upper_part("L-1", loads=((6.0, None),), length=6.0, rise=3.0)
        m = combine([board_part(), upper_part(), down])
        self.assertTrue(m["usable"])
        self.assertEqual(sorted(m["levels"]), ["L-1", "L0", "L1"])
        self.assertEqual(m["loads_n"], 3)

    def test_a_circuit_that_does_not_chain_is_not_measured(self):
        self.assertFalse(combine([upper_part("L1"), upper_part("L2")])["usable"])               # no sheet starts at the board
        self.assertFalse(combine([board_part(), board_part("L1")])["usable"])                  # two sheets start at the board
        self.assertFalse(combine([board_part(to_exit=13.0, destination_distance_m=None), upper_part()])["usable"])          # the sheet of the board says nothing about its plenum
        same = combine([board_part(), upper_part("L0")])                                        # a second sheet at the level of the board has nothing to hang from
        self.assertEqual((same["usable"], same["reason"]), (False, "levels"))

    def test_a_part_that_could_not_be_routed_makes_the_measure_incomplete(self):
        m = combine([board_part(), upper_part(found=False, unreached=["LU-2"])])
        self.assertEqual((m["usable"], m["reason"]), (False, "incomplete"))


if __name__ == "__main__":
    unittest.main()
