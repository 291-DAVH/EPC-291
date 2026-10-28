import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE))

from epc_lighting import run  # noqa: E402
import helpers  # noqa: E402


def area(**changes):
    base = {"id": "A1", "area_m2": 800, "target_lux": 50, "luminaire": "F1", "beam_utilisation": 0.7, "enclosure": "open"}
    base.update(changes)
    return base


def calculate(**changes):
    result = run(helpers.document(rooms=[], areas=[area(**changes)]))
    return result.as_dict()["areas"][0], result.warnings


class TestFloodlightMethod(unittest.TestCase):
    def test_count_is_n_equals_e_s_over_phi_cbu_fm_rounded_up(self):
        a, _ = calculate()
        self.assertAlmostEqual(a["flux"]["luminaires_exact"], 50 * 800 / (36000 * 0.7 * 0.65), places=3)
        self.assertEqual(a["flux"]["luminaires_required"], 3)
        self.assertEqual(a["tags"], ["LU-001", "LU-002", "LU-003"])

    def test_it_verifies_with_the_installed_count(self):
        a, _ = calculate()
        self.assertAlmostEqual(a["verification"]["average_lux"], 3 * 36000 * 0.7 * 0.65 / 800, places=2)
        self.assertTrue(a["verification"]["complies"])

    def test_a_closed_fixture_needs_fewer_units(self):
        open_, _ = calculate(enclosure="open", target_lux=120)
        closed, _ = calculate(enclosure="closed", target_lux=120)
        self.assertLess(closed["flux"]["luminaires_required"], open_["flux"]["luminaires_required"])

    def test_missing_cbu_is_assumed_with_low_confidence(self):
        a, _ = calculate(beam_utilisation=None)
        self.assertEqual(a["factors"]["beam_utilisation"]["confidence"], 0.4)
        self.assertIn("assumed", a["factors"]["beam_utilisation"]["reason"])

    def test_cbu_outside_the_usual_range_warns(self):
        _, low = calculate(beam_utilisation=0.5)
        _, high = calculate(beam_utilisation=0.95)
        self.assertTrue(any("below 0.6" in w for w in low))
        self.assertTrue(any("above 0.9" in w for w in high))

    def test_energy_is_reported_when_the_luminaire_declares_power(self):
        fl = dict(helpers.FLOODLIGHT, power_w=430)
        a = run(helpers.document(rooms=[], luminaires=[fl], areas=[area(operating_hours_per_year=4000)])).as_dict()["areas"][0]
        self.assertEqual(a["energy"]["installed_power_w"], 1290.0)
        self.assertEqual(a["energy"]["annual_energy_kwh"], 5160.0)

    def test_without_power_there_is_no_energy_block(self):
        a, _ = calculate()
        self.assertIsNone(a["energy"])


if __name__ == "__main__":
    unittest.main()
