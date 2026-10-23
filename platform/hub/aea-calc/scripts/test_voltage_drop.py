"""Pruebas de voltage_drop.py — valores de referencia calculados A MANO."""
import unittest

import voltage_drop as C


class TestCaida(unittest.TestCase):
    # Datos base: I = 100 A, L = 200 m = 0,2 km, R = 0,5 Ω/km, X = 0,1 Ω/km, cosφ = 0,8 -> senφ = 0,6
    # R·cosφ + X·senφ = 0,5·0,8 + 0,1·0,6 = 0,40 + 0,06 = 0,46 Ω/km
    # I·L·(...) = 100 · 0,2 · 0,46 = 9,2 V

    def test_three_phase(self):
        # ΔU = √3 · 9,2 = 1,7320508 · 9,2 = 15,9349 V ; % de 400 V = 3,9837 %
        r = C.caida_tension(3, 100, 200, 0.5, 0.1, 0.8, 400)
        self.assertAlmostEqual(r["delta_u_v"], 15.9349, places=3)
        self.assertAlmostEqual(r["delta_u_pct"], 3.9837, places=3)

    def test_single_phase(self):
        # ΔU = 2 · 9,2 = 18,4 V ; % de 230 V = 18,4/230 = 0,08 -> 8,0 %
        r = C.caida_tension(1, 100, 200, 0.5, 0.1, 0.8, 230)
        self.assertAlmostEqual(r["delta_u_v"], 18.4, places=6)
        self.assertAlmostEqual(r["delta_u_pct"], 8.0, places=6)

    def test_fp_unitario(self):
        # cosφ = 1 -> senφ = 0: ΔU = √3 · 50 · 1 km · 0,4 = √3 · 20 = 34,641 V (X no influye)
        self.assertAlmostEqual(C.drop_voltage_three_phase_v(50, 1000, 0.4, 0.09, 1.0), 34.641, places=3)

    def test_pf_zero_only_reactance(self):
        # cosφ = 0 -> senφ = 1: ΔU = 2 · 10 · 0,5 km · 0,08 = 0,8 V (R no influye)
        self.assertAlmostEqual(C.drop_voltage_single_phase_v(10, 500, 0.9, 0.08, 0.0), 0.8, places=6)

    def test_load_capacitive(self):
        # cosφ = 0,8 capacitiva: senφ = -0,6 -> R·cosφ + X·senφ = 0,40 - 0,06 = 0,34
        # ΔU monofásica = 2 · 100 · 0,2 · 0,34 = 13,6 V
        self.assertAlmostEqual(C.drop_voltage_single_phase_v(100, 200, 0.5, 0.1, 0.8, capacitiva=True), 13.6, places=6)

    def test_current_zero(self):
        self.assertEqual(C.drop_voltage_three_phase_v(0, 100, 0.5, 0.1, 0.8), 0.0)

    def test_length_max(self):
        # Monofásica, ΔU_max = 10 V: L = 10 / (2 · 100 · 0,46 Ω/km) = 10/92 = 0,108696 km = 108,696 m
        self.assertAlmostEqual(C.longitud_maxima_m(1, 10, 100, 0.5, 0.1, 0.8), 108.696, places=2)
        # Trifásica, ΔU_max = 12 V (3 % de 400): L = 12 / (1,7320508 · 100 · 0,46) = 12/79,6743 = 0,150613 km
        self.assertAlmostEqual(C.longitud_maxima_m(3, 12, 100, 0.5, 0.1, 0.8), 150.613, places=2)

    def test_complies_limit(self):
        self.assertTrue(C.complies_limit(3.9837, 4.0))
        self.assertFalse(C.complies_limit(4.1, 4.0))
        self.assertTrue(C.complies_limit(4.0, 4.0))

    def test_validaciones(self):
        with self.assertRaises(ValueError):
            C.caida_tension(2, 100, 200, 0.5, 0.1, 0.8, 400)      # fases inválidas
        with self.assertRaises(ValueError):
            C.caida_tension(3, -1, 200, 0.5, 0.1, 0.8, 400)       # I < 0
        with self.assertRaises(ValueError):
            C.caida_tension(3, 100, -5, 0.5, 0.1, 0.8, 400)       # L < 0
        with self.assertRaises(ValueError):
            C.caida_tension(3, 100, 200, 0.5, 0.1, 1.2, 400)      # fp > 1
        with self.assertRaises(ValueError):
            C.caida_tension(3, 100, 200, 0.5, 0.1, 0.8, 0)        # Un = 0
        with self.assertRaises(ValueError):
            C.caida_tension(3, 100, 200, -0.5, 0.1, 0.8, 400)     # R < 0
        with self.assertRaises(ValueError):
            C.longitud_maxima_m(3, 0, 100, 0.5, 0.1, 0.8)         # ΔU_max = 0
        with self.assertRaises(ValueError):
            C.longitud_maxima_m(3, 10, 100, 0.0, 0.0, 0.8)        # z = 0


if __name__ == "__main__":
    unittest.main()
