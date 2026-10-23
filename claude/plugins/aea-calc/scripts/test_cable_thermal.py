"""Pruebas de cable_thermal.py — valores de referencia calculados A MANO."""
import unittest

import cable_thermal as T


class TestTermico(unittest.TestCase):
    def test_constantes_k(self):
        self.assertEqual(T.k_material("Cu", "PVC"), 115)
        self.assertEqual(T.k_material("Cu", "XLPE"), 143)
        self.assertEqual(T.k_material("Al", "PVC"), 76)
        self.assertEqual(T.k_material("Al", "XLPE"), 94)
        with self.assertRaises(ValueError):
            T.k_material("Cu", "EPR")

    def test_section_min(self):
        # S = 10 000 · √0,5 / 143 = 10 000 · 0,707107 / 143 = 7 071,07 / 143 = 49,448 mm²
        self.assertAlmostEqual(T.seccion_minima_mm2(10000, 0.5, 143), 49.448, places=2)
        # Caso de raíz exacta: I = 8 000 A, t = 4 s (√4 = 2), k = 115 -> S = 16 000/115 = 139,13 mm²
        self.assertAlmostEqual(T.seccion_minima_mm2(8000, 4, 115), 139.130, places=2)

    def test_verification_complies(self):
        # S = 50 mm², k = 143: k²S² = 143² · 50² = 20 449 · 2 500 = 51 122 500 A²s
        # I²t = 10 000² · 0,5 = 1e8 · 0,5 = 5e7 A²s -> 5e7 ≤ 5,11225e7 : cumple
        # margen = 51 122 500 / 50 000 000 = 1,02245 ; t_max = 51 122 500 / 1e8 = 0,511225 s
        # I_max (0,5 s) = 143·50/√0,5 = 7 150 / 0,707107 = 10 111,6 A
        v = T.verificar_i2t(10000, 0.5, 143, 50)
        self.assertAlmostEqual(v["i2t"], 5.0e7, places=0)
        self.assertAlmostEqual(v["k2s2"], 51122500.0, places=0)
        self.assertTrue(v["cumple"])
        self.assertAlmostEqual(v["margen"], 1.02245, places=5)
        self.assertAlmostEqual(v["t_max_s"], 0.511225, places=6)
        self.assertAlmostEqual(v["i_max_a"], 10111.6, places=1)
        self.assertAlmostEqual(v["s_min_mm2"], 49.448, places=2)
        self.assertEqual(v["advertencias"], [])

    def test_verification_not_complies(self):
        # S = 35 mm²: k²S² = 20 449 · 1 225 = 25 050 025 < 5e7 -> no cumple ; margen = 0,501
        v = T.verificar_i2t(10000, 0.5, 143, 35)
        self.assertFalse(v["cumple"])
        self.assertAlmostEqual(v["k2s2"], 25050025.0, places=0)
        self.assertAlmostEqual(v["margen"], 0.5010, places=3)

    def test_limit_equality(self):
        # S = S_min exacta: I = 8 000, t = 4, k = 100 -> S_min = 160 mm²; k²S² = 1e4 · 25 600 = 2,56e8 ;
        # I²t = 6,4e7 · 4 = 2,56e8 -> igualdad -> cumple
        self.assertTrue(T.verificar_i2t(8000, 4, 100, 160)["cumple"])

    def test_time_max(self):
        # t_max = (115 · 25)² / 5 000² = 2 875² / 25e6 = 8 265 625 / 25 000 000 = 0,33063 s
        self.assertAlmostEqual(T.tiempo_maximo_s(5000, 115, 25), 0.33063, places=5)

    def test_warnings_time(self):
        self.assertTrue(any("adiabático" in a for a in T.verificar_i2t(1000, 6.0, 143, 50)["advertencias"]))
        self.assertTrue(any("Joule" in a for a in T.verificar_i2t(1000, 0.05, 143, 50)["advertencias"]))

    def test_section_commercial(self):
        # S_min = 49,45 -> en [35, 50, 70] la menor ≥ 49,45 es 50
        self.assertEqual(T.seccion_comercial_superior(49.45, [70, 35, 50]), 50)
        with self.assertRaises(ValueError):
            T.seccion_comercial_superior(100, [35, 50, 70])
        with self.assertRaises(ValueError):
            T.seccion_comercial_superior(10, [])

    def test_validaciones(self):
        with self.assertRaises(ValueError):
            T.seccion_minima_mm2(0, 0.5, 143)
        with self.assertRaises(ValueError):
            T.seccion_minima_mm2(1000, -1, 143)
        with self.assertRaises(ValueError):
            T.seccion_minima_mm2(1000, 0.5, 0)
        with self.assertRaises(ValueError):
            T.verificar_i2t(1000, 0.5, 143, 0)
        with self.assertRaises(ValueError):
            T.tiempo_maximo_s(0, 143, 50)


if __name__ == "__main__":
    unittest.main()
