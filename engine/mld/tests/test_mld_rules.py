"""Poles and protection chains the multi-line expands: pure rules of the generator."""
import sys
import unittest
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ENGINE / a / "src") for a in ("mld", "sld", "calc", "symbols", "titleblock")]

from epc_mld import mld_generator as M   # noqa: E402


class TestPoles(unittest.TestCase):
    def test_poles_follow_the_phase_and_the_children(self):
        self.assertEqual([M.poles_of({"phase": p}, False) for p in ("3F", "1F", "3F+N")], [3, 2, 4])
        self.assertEqual([M.poles_of({"phase": p}, True) for p in ("3F", "1F")], [4, 2])

    def test_next_in_series_and_pole_ids(self):
        self.assertEqual((M.nxt(7, [6, 10, 16]), M.nxt(99, [6, 10])), (10, 10))
        cat = {"lv_mcb_3p_mld": 1, "lv_vfd_3p_mld": 1}
        self.assertEqual(M.pole_id("lv_mcb", 3, cat), "lv_mcb_3p_mld")
        self.assertEqual(M.pole_id("lv_vfd", 1, cat), "lv_vfd_3p_mld")           # fixed 3P devices
        self.assertIsNone(M.pole_id("lv_unknown", 3, cat))


if __name__ == "__main__":
    unittest.main()
