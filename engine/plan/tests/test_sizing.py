"""The size of conduits and trays from the cables they carry (epc_plan.sizing)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from epc_plan import core, sizing   # noqa: E402

P = core.PARAMS
KINDS = {"CN": {"atributos": ["diametro_mm"]}, "BN": {"atributos": ["ancho_mm", "alto_mm"]}}


def box(kind, circuits, cables):
    return {"tag": "T1", "line": "l1", "kind": kind, "circuits": circuits, "cables": cables}


class TestSizing(unittest.TestCase):
    def test_a_cable_takes_the_diameter_of_the_section_at_or_above_and_the_default_when_unknown(self):
        cfg = P["sizing"]
        self.assertEqual(sizing.cable_mm(2.5, cfg, 14.0), 10.5)
        self.assertEqual(sizing.cable_mm(3, cfg, 14.0), 12.0)               # between 2.5 and 4: the larger one
        self.assertEqual(sizing.cable_mm(400, cfg, 14.0), 60.0)             # beyond the table: the largest
        self.assertEqual(sizing.cable_mm(None, cfg, 14.0), 14.0)

    def test_a_conduit_is_the_smallest_that_holds_the_cable_within_its_limit(self):
        out = sizing.size_containers([box("CN", ["IUG-1"], 1)], {"IUG-1": 2.5}, {"IUG-1": 1}, KINDS, P)[0]
        self.assertEqual(out["size"], {"diametro_mm": 16.0})                    # 10.5 mm cable: 86.6 mm2 of 201 mm2 is 43 %, under the 53 % of one cable
        self.assertTrue(out["fits"])
        self.assertEqual(out["line"], "l1")

    def test_more_cables_need_a_larger_conduit_and_the_limit_falls(self):
        out = sizing.size_containers([box("CN", ["A", "B", "C"], 3)], {"A": 2.5, "B": 2.5, "C": 2.5}, {}, KINDS, P)[0]
        self.assertGreater(out["size"]["diametro_mm"], 16)
        self.assertLessEqual(out["used_pct"], out["limit_pct"])
        self.assertEqual(out["limit_pct"], 40.0)

    def test_a_tray_is_chosen_by_width_and_the_cables_of_a_circuit_count_by_its_ternas(self):
        out = sizing.size_containers([box("BN", ["TUG-1"], 2)], {"TUG-1": 4}, {"TUG-1": 2}, KINDS, P)[0]
        self.assertEqual(len(out["cable_mm"]), 2)
        self.assertEqual(out["size"], {"ancho_mm": 100.0, "alto_mm": 50.0})

    def test_when_nothing_holds_them_the_largest_is_returned_and_it_is_said(self):
        out = sizing.size_containers([box("CN", ["X"] * 1, 1)], {"X": 240}, {"X": 40}, KINDS, P)[0]
        self.assertFalse(out["fits"])
        self.assertEqual(out["size"], {"diametro_mm": 110.0})


if __name__ == "__main__":
    unittest.main()
