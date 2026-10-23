"""Pruebas de hazen_williams.py — valores de referencia calculados A MANO (con logaritmos)."""
import unittest

import hazen_williams as H


class TestHW(unittest.TestCase):
    def test_loss_unit_manual(self):
        # Q = 1000 L/min, d = 100 mm, C = 120 (cálculo por logaritmos decimales):
        #  log10(Q^1,85) = 1,85·3 = 5,55                 -> 3,5481e5
        #  log10(C^1,85) = 1,85·2,07918 = 3,84649        -> 7,0224e3
        #  log10(d^4,87) = 4,87·2 = 9,74                 -> 5,4954e9
        #  J = 6,05e5 · 3,5481e5 / (7,0224e3 · 5,4954e9) = 2,14662e11 / 3,8591e13 = 5,5625e-3 bar/m
        self.assertAlmostEqual(H.perdida_unitaria_bar_m(1000, 100, 120), 5.5625e-3, places=6)

    def test_desviacion_contra_forma_si(self):
        # Cálculo independiente (forma SI con exponentes 1,852 / 4,8704 y 10,67): h/L = 0,05686 m/m
        # Δp = 1000·9,80665·0,05686/1e5 = 5,576e-3 bar/m. Desviación esperada ≈ −0,24 % (|dev| < 1 %).
        j = H.perdida_unitaria_bar_m(1000, 100, 120)
        j_indep = 5.576e-3
        desv = (j - j_indep) / j_indep
        self.assertLess(abs(desv), 0.01)

    def test_velocity(self):
        # Q = 1000 L/min = 0,0166667 m³/s ; A = π·0,1²/4 = 0,0078540 m² ; v = 2,1221 m/s
        self.assertAlmostEqual(H.velocidad_m_s(1000, 100), 2.1221, places=3)

    def test_pressure_static(self):
        # 10 m de columna: 1000 · 9,80665 · 10 / 1e5 = 0,980665 bar ; -10 m -> -0,980665
        self.assertAlmostEqual(H.presion_estatica_bar(10), 0.980665, places=6)
        self.assertAlmostEqual(H.presion_estatica_bar(-10), -0.980665, places=6)
        self.assertEqual(H.presion_estatica_bar(0), 0.0)

    def test_perdida_total(self):
        # L = 100 m + L_eq = 20 m = 120 m ; fricción = 5,5625e-3 · 120 = 0,6675 bar
        # estática (Δz = +10 m) = 0,980665 bar ; total = 1,648165 bar
        r = H.perdida_total(1000, 100, 120, 100, l_eq_m=20, dz_m=10)
        self.assertAlmostEqual(r["longitud_total_m"], 120.0, places=9)
        self.assertAlmostEqual(r["dp_friccion_bar"], 0.6675, places=4)
        self.assertAlmostEqual(r["dp_estatica_bar"], 0.980665, places=6)
        self.assertAlmostEqual(r["dp_total_bar"], 1.6482, places=3)

    def test_flow_zero(self):
        r = H.perdida_total(0, 100, 120, 100)
        self.assertEqual(r["dp_friccion_bar"], 0.0)
        self.assertEqual(r["velocidad_m_s"], 0.0)

    def test_escalamiento_con_caudal(self):
        # J ∝ Q^1,85: al duplicar Q, J se multiplica por 2^1,85 = 10^(1,85·0,30103) = 10^0,55691 = 3,6050
        j1 = H.perdida_unitaria_bar_m(500, 80, 130)
        j2 = H.perdida_unitaria_bar_m(1000, 80, 130)
        self.assertAlmostEqual(j2 / j1, 3.6050, places=3)

    def test_validaciones(self):
        with self.assertRaises(ValueError):
            H.perdida_unitaria_bar_m(-1, 100, 120)
        with self.assertRaises(ValueError):
            H.perdida_unitaria_bar_m(100, 0, 120)
        with self.assertRaises(ValueError):
            H.perdida_unitaria_bar_m(100, 100, 0)
        with self.assertRaises(ValueError):
            H.velocidad_m_s(100, -5)
        with self.assertRaises(ValueError):
            H.perdida_total(100, 100, 120, -1)
        with self.assertRaises(ValueError):
            H.perdida_total(100, 100, 120, 10, l_eq_m=-1)
        with self.assertRaises(ValueError):
            H.presion_estatica_bar(float("nan"))


if __name__ == "__main__":
    unittest.main()
