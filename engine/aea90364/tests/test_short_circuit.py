"""Pruebas de short_circuit.py — valores de referencia calculados A MANO."""
import math
import unittest

from epc_aea90364 import short_circuit as S


class TestBasicos(unittest.TestCase):
    def test_c(self):
        self.assertEqual(S.factor_c(6), 1.05)
        self.assertEqual(S.factor_c(10), 1.10)
        with self.assertRaises(ValueError):
            S.factor_c(8)

    def test_in_trafo(self):
        # In = 1 000 000 / (√3 · 400) = 1 000 000 / 692,820 = 1 443,38 A
        self.assertAlmostEqual(S.corriente_asignada_trafo(1e6, 400), 1443.38, places=1)

    def test_z_trafo(self):
        # Z_T = 0,06 · 400² / 1 000 000 = 0,06 · 0,16 = 0,0096 Ω (9,6 mΩ)
        r, x = S.impedancia_transformador(1e6, 400, 6)
        self.assertEqual(r, 0.0)
        self.assertAlmostEqual(x, 0.0096, places=9)

    def test_z_trafo_con_pcu(self):
        # Pcu = 10 kW: R_T = 10 000 · 400² / (10⁶)² = 10 000 · 160 000 / 10¹² = 0,0016 Ω
        # X_T = √(0,0096² − 0,0016²) = √(9,216e-5 − 0,256e-5) = √8,96e-5 = 0,0094657 Ω
        r, x = S.impedancia_transformador(1e6, 400, 6, pcu_w=10000)
        self.assertAlmostEqual(r, 0.0016, places=9)
        self.assertAlmostEqual(x, 0.0094657, places=6)

    def test_z_red_por_potencia(self):
        # Sk'' = 500 MVA, Un = 400 V, c = 1,05: Z_Q = 1,05 · 160 000 / 500e6 = 3,36e-4 Ω
        # X/R = 10: R = Z/√101 = 3,36e-4/10,04988 = 3,3433e-5 ; X = 10·R = 3,3433e-4
        r, x = S.impedancia_red(400, 1.05, sk_va=500e6)
        self.assertAlmostEqual(r, 3.3433e-5, places=8)
        self.assertAlmostEqual(x, 3.3433e-4, places=7)
        self.assertAlmostEqual(math.hypot(r, x), 3.36e-4, places=9)

    def test_z_red_por_corriente_equivale_a_potencia(self):
        # Ik_Q = 50 kA a 400 V: Z_Q = 1,05 · 400 / (√3 · 50 000) = 420 / 86 602,5 = 4,8497e-3 Ω
        r, x = S.impedancia_red(400, 1.05, ik_a=50000)
        self.assertAlmostEqual(math.hypot(r, x), 4.8497e-3, places=6)

    def test_red_argumentos(self):
        with self.assertRaises(ValueError):
            S.impedancia_red(400, 1.05)                         # ninguno
        with self.assertRaises(ValueError):
            S.impedancia_red(400, 1.05, sk_va=1e8, ik_a=1e4)    # ambos

    def test_cable(self):
        # r = 0,2 Ω/km, x = 0,08 Ω/km, L = 50 m = 0,05 km: R = 0,01 Ω ; X = 0,004 Ω
        r, x = S.impedance_cable(0.2, 0.08, 50)
        self.assertAlmostEqual(r, 0.01, places=9)
        self.assertAlmostEqual(x, 0.004, places=9)
        # 2 en paralelo: mitad
        r, x = S.impedance_cable(0.2, 0.08, 50, n_paralelo=2)
        self.assertAlmostEqual(r, 0.005, places=9)
        self.assertAlmostEqual(x, 0.002, places=9)


class TestIk(unittest.TestCase):
    def test_trafo_red_infinita(self):
        # Ik'' = c·In/uk = 1,05 · 1 443,38 / 0,06 = 1,05 · 24 056,3 = 25 259,1 A
        # (equivale a 1,05·400/(√3·0,0096) = 420/0,0166277 = 25 259 A)
        res = S.calcular_ik(400, 1.05, red=None, trafo={"sn_va": 1e6, "uk_pct": 6})
        self.assertAlmostEqual(res["ik_a"], 25259.1, delta=1.0)
        self.assertAlmostEqual(res["ik_a"], 1.05 * 1443.38 / 0.06, delta=5.0)

    def test_trafo_red_infinita_c110(self):
        # c = 1,10: 1,10 · 24 056,3 = 26 461,9 A
        res = S.calcular_ik(400, S.factor_c(10), trafo={"sn_va": 1e6, "uk_pct": 6})
        self.assertAlmostEqual(res["ik_a"], 26461.9, delta=2.0)

    def test_cadena_red_trafo_cable(self):
        # R = 0,01 + 3,3433e-5 = 0,010033433 ; X = 3,3433e-4 + 0,0096 + 0,004 = 0,013934330
        # |Z| = √(1,00669e-4 + 1,94166e-4) = √2,94835e-4 = 0,0171708 Ω
        # Ik'' = 1,05·400 / (1,7320508 · 0,0171708) = 420 / 0,0297407 = 14 122 A
        res = S.calcular_ik(400, 1.05, red={"sk_va": 500e6}, trafo={"sn_va": 1e6, "uk_pct": 6},
                            cables=[{"r_ohm_km": 0.2, "x_ohm_km": 0.08, "longitud_m": 50}])
        self.assertAlmostEqual(res["r_ohm"], 0.0100334, places=6)
        self.assertAlmostEqual(res["x_ohm"], 0.0139343, places=6)
        self.assertAlmostEqual(res["z_ohm"], 0.0171708, places=6)
        self.assertAlmostEqual(res["ik_a"], 14122.0, delta=15.0)

    def test_solo_red_devuelve_la_corriente_dada(self):
        # Z_Q = c·Un/(√3·Ik_Q) -> Ik'' = c·Un/(√3·Z_Q) = Ik_Q : con 30 kA debe dar 30 000 A
        res = S.calcular_ik(400, 1.05, red={"ik_a": 30000})
        self.assertAlmostEqual(res["ik_a"], 30000.0, delta=0.5)

    def test_advertencias(self):
        res = S.calcular_ik(400, 1.05, trafo={"sn_va": 1e6, "uk_pct": 6})
        texto = " ".join(res["advertencias"])
        self.assertIn("motores", texto)
        self.assertIn("κ", texto)

    def test_con_kt(self):
        # x_T (p.u.) = 0,0096 / (400²/10⁶ = 0,16) = 0,06 ; K_T = 0,95·1,05/(1 + 0,036) = 0,9975/1,036 = 0,96284
        # Ik'' = 25 259,1 / 0,96284 = 26 233,9 A
        res = S.calcular_ik(400, 1.05, trafo={"sn_va": 1e6, "uk_pct": 6}, aplicar_kt=True)
        self.assertAlmostEqual(res["ik_a"], 26234.0, delta=3.0)
        with self.assertRaises(ValueError):
            S.calcular_ik(400, 1.05, red={"ik_a": 1e4}, aplicar_kt=True)

    def test_validaciones(self):
        with self.assertRaises(ValueError):
            S.calcular_ik(400, 1.05)                                   # Z = 0 (red infinita sin nada)
        with self.assertRaises(ValueError):
            S.calcular_ik(-400, 1.05, trafo={"sn_va": 1e6, "uk_pct": 6})
        with self.assertRaises(ValueError):
            S.impedancia_transformador(1e6, 400, 0)
        with self.assertRaises(ValueError):
            S.impedancia_transformador(1e6, 400, 6, pcu_w=100000)       # R ≥ Z
        with self.assertRaises(ValueError):
            S.impedance_cable(0.2, 0.08, -1)
        with self.assertRaises(ValueError):
            S.impedance_cable(0.2, 0.08, 10, n_paralelo=0)


class TestOpcionales(unittest.TestCase):
    def test_factor_kt(self):
        # 0,95·1,05 / (1 + 0,6·0,06) = 0,9975 / 1,036 = 0,96284
        self.assertAlmostEqual(S.factor_kt(0.06, 1.05), 0.96284, places=5)

    def test_contribution_motor(self):
        # Sr = 100 kVA, 400 V: Ir = 100 000/(√3·400) = 144,338 A ; ILR/Ir = 6 ; c = 1,05
        # Ik_M = 1,05 · 6 · 144,338 = 909,33 A
        self.assertAlmostEqual(S.aporte_motor(100e3, 400, 6, 1.05), 909.33, places=1)

    def test_motors_negligible(self):
        # 5 % de 25 000 A = 1 250 A: 909 ≤ 1 250 -> despreciable ; 1 300 > 1 250 -> no
        self.assertTrue(S.motors_negligible(909.0, 25000.0))
        self.assertFalse(S.motors_negligible(1300.0, 25000.0))

    def test_kappa(self):
        # R/X = 0 -> κ = 1,02 + 0,98 = 2,00
        self.assertAlmostEqual(S.factor_kappa(0.0, 5.0), 2.0, places=9)
        # R/X = 0,1: exp(−0,3) = 0,740818 ; κ = 1,02 + 0,98·0,740818 = 1,02 + 0,726002 = 1,746002
        self.assertAlmostEqual(S.factor_kappa(1.0, 10.0), 1.746002, places=5)
        # X = 0 -> κ = 1,02
        self.assertAlmostEqual(S.factor_kappa(1.0, 0.0), 1.02, places=9)
        with self.assertRaises(ValueError):
            S.factor_kappa(0.0, 0.0)

    def test_current_peak(self):
        # R = 0: κ = 2 ; i_p = 2 · 1,41421 · 10 000 = 28 284,3 A
        self.assertAlmostEqual(S.corriente_pico(10000, 0.0, 1.0), 28284.3, places=1)
        # R/X = 0,1: i_p = 1,746002 · 1,414214 · 10 000 = 24 692,0 A
        self.assertAlmostEqual(S.corriente_pico(10000, 1.0, 10.0), 24692.0, delta=1.0)


if __name__ == "__main__":
    unittest.main()
