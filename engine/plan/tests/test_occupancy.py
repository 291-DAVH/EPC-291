"""How full a tray or a conduit is (epc_plan.occupancy)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from epc_plan import core, occupancy   # noqa: E402

CFG = core.PARAMS["occupancy"]


class TestOccupancy(unittest.TestCase):
    def test_a_tray_is_compared_with_its_width_and_height(self):
        f = occupancy.fill({"ancho_mm": 300, "alto_mm": 100}, 10, CFG)
        self.assertEqual((f["limit_pct"], f["status"]), (50.0, "ok"))
        self.assertAlmostEqual(f["used_pct"], 10 * 3.14159265 * 14 * 14 / 4 / 30000 * 100, places=1)

    def test_a_conduit_takes_the_limit_for_the_number_of_cables(self):
        one = occupancy.fill({"diametro_mm": 50}, 1, CFG)
        self.assertEqual((one["limit_pct"], one["status"]), (53.0, "ok"))
        many = occupancy.fill({"diametro_mm": 30}, 3, CFG)
        self.assertEqual((many["limit_pct"], many["status"]), (40.0, "over"))
        self.assertEqual(occupancy.fill({"diametro_mm": 50}, 2, CFG)["limit_pct"], 31.0)

    def test_the_cable_diameter_written_on_the_line_is_used(self):
        thin = occupancy.fill({"diametro_mm": 50, "diametro_cable_mm": 5}, 3, CFG)
        self.assertEqual((thin["cable_mm"], thin["status"]), (5.0, "ok"))

    def test_near_the_limit_is_said(self):
        self.assertEqual(occupancy.fill({"diametro_mm": 40}, 3, CFG)["status"], "near")       # 36.7 % against 40 %

    def test_without_a_size_or_cables_there_is_nothing_to_say(self):
        self.assertIsNone(occupancy.fill({}, 3, CFG))
        self.assertIsNone(occupancy.fill({"diametro_mm": 50}, 0, CFG))
        self.assertIsNone(occupancy.fill({"diametro_mm": "x"}, 3, CFG))


if __name__ == "__main__":
    unittest.main()
