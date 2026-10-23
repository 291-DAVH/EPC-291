"""Pruebas de aea_tables y aea_protection (valores contrastados a mano con el PDF)."""
import unittest
from epc_calc import aea_tables as T
from epc_calc import aea_protection as P
from epc_calc import aea_conductors as C


class TestTablas(unittest.TestCase):
    def test_771_16_i_coincide_con_modulo_previo(self):
        for s, (a, b) in C.IZ_771_16_I.items():
            self.assertEqual(T.iz_tabla("771.16.I", "pvc", "cu", s, "2x"), a)
            self.assertEqual(T.iz_tabla("771.16.I", "pvc", "cu", s, "3x"), b)

    def test_valores_del_pdf(self):
        self.assertEqual(T.iz_tabla("771.16.III", "pvc", "cu", 1.5, "C_3x", "B2CE"), 15)
        self.assertEqual(T.iz_tabla("771.16.III", "xlpe", "cu", 2.5, "C_2x", "B2CE"), 30)
        self.assertEqual(T.iz_tabla("771.16.V", "pvc", "cu", 2.5, "2x"), 33)
        self.assertEqual(T.iz_tabla("771.16.VI", "xlpe", "cu", 1.5, "c4_3x"), 29)

    def test_errores(self):
        with self.assertRaises(ValueError):
            T.iz_tabla("771.16.I", "pvc", "cu", 999, "2x")
        with self.assertRaises(ValueError):
            T.iz_tabla("771.16.I", "pvc", "cu", 2.5, "9x")
        with self.assertRaises(ValueError):
            T.iz_tabla("771.16.ZZ", "pvc", "cu", 2.5, "2x")

    def test_factores(self):
        self.assertEqual(T.factor_temperatura_aire("pvc", 40), 1.0)
        self.assertAlmostEqual(T.factor_temperatura_aire("xlpe", 50), T.cargar()["factores_correccion"]["771.16.II.a"]["factores"]["xlpe"][8])
        self.assertEqual(T.factor_temperatura_suelo("xlpe", 25), 1.0)
        self.assertEqual(T.factor_resistividad("D1", 1.0), 1.0)
        self.assertEqual(T.factor_resistividad("D2", 2.0), 0.75)
        self.assertAlmostEqual(T.factor_resistividad("D2", 1.25), 0.925)
        self.assertEqual(T.factor_agrupamiento_canos(3, True), 0.70)
        self.assertEqual(T.factor_agrupamiento_aire("1", 4), 0.65)
        self.assertEqual(T.factor_agrupamiento_aire("4", 20), 0.72)
        self.assertEqual(T.factor_agrupamiento_enterrado("c", 3, 2), 0.75)
        with self.assertRaises(ValueError):
            T.factor_temperatura_aire("pvc", 99)

    def test_tablas_monotonas(self):
        tabs = T.cargar()["tablas_capacidad"]
        for nom in ("771.16.I", "771.16.III", "771.16.V", "771.16.VI"):
            for b in tabs[nom]["bloques"]:
                for mat, filas in b["filas"].items():
                    ordenadas = sorted(filas, key=float)
                    for i in range(len(b["columnas"])):
                        col = [filas[s][i] for s in ordenadas if filas[s][i] is not None]
                        self.assertEqual(col, sorted(col), f"{nom} {b['aislacion']} {mat} col {i}")

    def test_iz_corregida(self):
        self.assertAlmostEqual(T.iz_corregida(200, ternas=2, clase5=True, f_agrup=0.8), 2 * 200 * 0.95 * 0.8)

    def test_constantes(self):
        self.assertEqual(T.constante("771.19.II_k_adiabatico")["epr_xlpe|cu"], 143.0)


class TestProteccion(unittest.TestCase):
    def test_i2(self):
        self.assertAlmostEqual(P.i2_convencional(250, "mccb"), 325.0)
        self.assertAlmostEqual(P.i2_convencional(16, "mcb"), 23.2)
        self.assertAlmostEqual(P.i2_convencional(100, "fusible_gg"), 160.0)

    def test_in_max(self):
        self.assertAlmostEqual(P.in_max_por_iz(100, "mcb"), 100.0)
        self.assertAlmostEqual(P.in_max_por_iz(100, "fusible_gg"), 1.45 * 100 / 1.6)

    def test_tn_tt_it(self):
        self.assertTrue(P.verifica_tn(0.5, 400)["cumple"])      # 200 V ≤ 230
        self.assertFalse(P.verifica_tn(0.7, 400)["cumple"])     # 280 V > 230
        self.assertAlmostEqual(P.ra_maxima_tt(0.03), 50 / 0.03)
        self.assertTrue(P.verifica_tt(1666, 0.03)["cumple"])
        self.assertAlmostEqual(P.corriente_falla_tt(230, 10, 20), 230 / 30)
        self.assertTrue(P.verifica_it_segunda_falla(0.5, 300)["cumple"])   # 300 V ≤ 400
        self.assertFalse(P.verifica_it_segunda_falla(0.5, 300, neutro_distribuido=True)["cumple"])  # 300 > 230


if __name__ == "__main__":
    unittest.main()
