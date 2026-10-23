"""Pruebas de hvac_airflow.py — valores de referencia calculados A MANO."""
import unittest

import hvac_airflow as A


class TestHVAC(unittest.TestCase):
    def test_conversiones(self):
        # 360 m³/h ÷ 3,6 = 100 L/s ; 100 L/s × 3,6 = 360 m³/h
        self.assertAlmostEqual(A.m3h_a_ls(360), 100.0, places=9)
        self.assertAlmostEqual(A.ls_a_m3h(100), 360.0, places=9)
        self.assertAlmostEqual(A.ls_a_m3h(A.m3h_a_ls(1234.5)), 1234.5, places=9)

    def test_flow_by_load(self):
        # ρ·cp = 1,2 · 1,006 = 1,2072 kJ/(m³·K) ; Q = 10 kW, ΔT = 10 K
        # V̇ = 10 / (1,2072 · 10) = 0,828363 m³/s = 2 982,1 m³/h = 828,36 L/s
        c = A.flow_by_load_sensible(10.0, 10.0)
        self.assertAlmostEqual(c["m3_s"], 0.828363, places=5)
        self.assertAlmostEqual(c["m3_h"], 2982.1, places=1)
        self.assertAlmostEqual(c["l_s"], 828.36, places=1)

    def test_load_reverse(self):
        # Q = 1,2072 · (3600/3600 = 1 m³/s) · 5 K = 6,036 kW
        self.assertAlmostEqual(A.load_sensible_kw(3600, 5.0), 6.036, places=6)

    def test_delta_t(self):
        # ΔT = 6,036 / (1,2072 · 1) = 5 K
        self.assertAlmostEqual(A.delta_t_por_caudal(6.036, 3600), 5.0, places=6)

    def test_propiedades_personalizadas(self):
        # ρ = 1,0 ; cp = 1,0 ; Q = 3,6 kW ; ΔT = 1 K -> V̇ = 3,6 m³/s = 12 960 m³/h
        self.assertAlmostEqual(A.caudal_por_carga_sensible_m3h(3.6, 1.0, rho=1.0, cp=1.0), 12960.0, places=6)

    def test_load_zero(self):
        self.assertEqual(A.caudal_por_carga_sensible_m3h(0, 10), 0.0)

    def test_renewals(self):
        # Vol = 10·6·3 = 180 m³ ; 6 ren/h -> 1 080 m³/h = 300 L/s
        r = A.flow_by_renewals(180, 6)
        self.assertAlmostEqual(r["m3_h"], 1080.0, places=9)
        self.assertAlmostEqual(r["l_s"], 300.0, places=9)
        # n = 1 080 / 180 = 6
        self.assertAlmostEqual(A.renovaciones_por_hora(1080, 180), 6.0, places=9)

    def test_validaciones(self):
        for f, args in ((A.caudal_por_carga_sensible_m3h, (10, 0)),
                        (A.caudal_por_carga_sensible_m3h, (-1, 10)),
                        (A.caudal_por_carga_sensible_m3h, (10, 10, 0)),
                        (A.caudal_por_carga_sensible_m3h, (10, 10, 1.2, 0)),
                        (A.load_sensible_kw, (-5, 10)),
                        (A.delta_t_por_caudal, (5, 0)),
                        (A.flow_by_renewals, (0, 6)),
                        (A.flow_by_renewals, (180, -1)),
                        (A.renovaciones_por_hora, (100, 0)),
                        (A.m3h_a_ls, (-1,)),
                        (A.ls_a_m3h, (float("inf"),))):
            with self.assertRaises(ValueError, msg=f"{f.__name__}{args}"):
                f(*args)


if __name__ == "__main__":
    unittest.main()
