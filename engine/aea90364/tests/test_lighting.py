"""Pruebas de lighting.py — valores de referencia calculados A MANO (ver comentarios)."""
import math
import unittest

from epc_aea90364 import lighting as L


class TestFlujo(unittest.TestCase):
    def test_caso_nave_n_minimo_50(self):
        # E·A = 300 · 1600 = 480 000 lm
        # Φ·UF·MF = 20 000 · 0,60 · 0,80 = 12 000 · 0,80 = 9 600 lm
        # N = 480 000 / 9 600 = 50 (exacto) -> N mínimo = 50
        self.assertAlmostEqual(L.flujo_n_luminarias(300, 1600, 20000, 0.60, 0.80), 50.0, places=6)
        self.assertEqual(L.n_luminarias_minimo(300, 1600, 20000, 0.60, 0.80), 50)

    def test_redondeo_hacia_arriba(self):
        # E·A = 500 · 96 = 48 000 ; Φ·UF·MF = 4 000·0,55 = 2 200 ; ·0,80 = 1 760
        # N = 48 000 / 1 760 = 27,2727 -> 28
        self.assertEqual(L.n_luminarias_minimo(500, 96, 4000, 0.55, 0.80), 28)

    def test_e_medio_con_54_luminarias(self):
        # E = 54 · 20 000 · 0,60 · 0,80 / 1 600 = 54 · 9 600 / 1 600 = 54 · 6 = 324 lx
        self.assertAlmostEqual(L.illuminance_mean_flux(54, 1600, 20000, 0.60, 0.80), 324.0, places=6)

    def test_validaciones(self):
        with self.assertRaises(ValueError):
            L.flujo_n_luminarias(300, 1600, 20000, 1.2, 0.8)   # UF > 1
        with self.assertRaises(ValueError):
            L.flujo_n_luminarias(-300, 1600, 20000, 0.6, 0.8)  # E < 0
        with self.assertRaises(ValueError):
            L.flujo_n_luminarias(300, 0, 20000, 0.6, 0.8)      # A = 0
        with self.assertRaises(ValueError):
            L.flujo_n_luminarias(300, 1600, 20000, 0.6, 0)     # MF = 0


class TestMalla(unittest.TestCase):
    def test_malla_40x40_n50(self):
        # Candidatas con N ≥ 50 y relación ≤ 1,5 en 40×40 (relación = ny/nx o nx/ny):
        #  50 = 5×10 (r=2), 51 = 3×17, 52 = 4×13, 53 primo: no cumplen.
        #  54 = 6×9: sx = 40/6 = 6,667 ; sy = 40/9 = 4,444 ; r = 9/6 = 1,5 -> cumple (≤ 1,5)
        # => N = 54 (se elige nx=6, ny=9 por empate con 9×6 y menor nx)
        nx, ny = L.seleccionar_malla(50, 40, 40)
        self.assertEqual((nx, ny), (6, 9))

    def test_malla_30x20_n12(self):
        # 12 = 4×3 -> sx = 30/4 = 7,5 ; sy = 20/3 = 6,667 ; r = 1,125 ≤ 1,5 OK
        # 3×4 daría sx=10, sy=5 (r=2) y 6×2 daría 5 y 10 (r=2): no cumplen.
        self.assertEqual(L.seleccionar_malla(12, 30, 20), (4, 3))

    def test_malla_imposible(self):
        with self.assertRaises(ValueError):
            L.seleccionar_malla(2, 40, 1, 1.5, n_max_lado=5)

    def test_validaciones_malla(self):
        with self.assertRaises(ValueError):
            L.seleccionar_malla(0, 10, 10)
        with self.assertRaises(ValueError):
            L.seleccionar_malla(4, -1, 10)
        with self.assertRaises(ValueError):
            L.seleccionar_malla(4, 10, 10, relacion_max=0.9)

    def test_points_grid(self):
        # Sala 4×2, nx=2, ny=1 -> celdas de 2×2, centros (1,1) y (3,1)
        self.assertEqual(L.points_grid(4, 2, 2, 1), [(1.0, 1.0), (3.0, 1.0)])


class TestPuntoAPunto(unittest.TestCase):
    def test_bajo_la_luminaria(self):
        # E = Φ/(π h²) = 1000 / (π·4) = 250/π = 250 · 0,318310 = 79,577 lx
        self.assertAlmostEqual(L.illuminance_lambertian(1000, 2.0, 0, 0), 79.577, places=2)

    def test_outside_of_axis(self):
        # h = 2, distancia horizontal 1,5 -> d² = 4 + 2,25 = 6,25 ; d⁴ = 39,0625
        # E = (Φ/π) · h² / d⁴ = 318,310 · 4 / 39,0625 = 318,310 · 0,1024 = 32,595 lx
        self.assertAlmostEqual(L.illuminance_lambertian(1000, 2.0, 0.9, 1.2), 32.595, places=2)

    def test_grilla_minima(self):
        # Sala 2×2, 1 luminaria en (1,1), Φ = π, h = 1 (Φ/π = 1), banda 0, paso 1 -> 9 puntos.
        # E = 1/d⁴ con d² = 1 + r²:
        #   centro r=0       : 1                (1 punto)
        #   medios de borde  : r²=1 -> 1/4      (4 puntos)
        #   esquinas         : r²=2 -> 1/9      (4 puntos)
        # E_min = 1/9 = 0,11111 ; E_max = 1 ; E_medio = (1 + 4/4 + 4/9)/9 = (22/9)/9 = 22/81 = 0,27160
        # U0 = (1/9)/(22/81) = 9/22 = 0,40909 ; E_max/E_min = 9
        r = L.evaluar_malla(2, 2, [(1, 1)], math.pi, 1.0, banda_m=0.0, paso_m=1.0)
        self.assertEqual(r["n_puntos"], 9)
        self.assertAlmostEqual(r["e_min"], 1 / 9, places=6)
        self.assertAlmostEqual(r["e_max"], 1.0, places=6)
        self.assertAlmostEqual(r["e_medio"], 0.271605, places=5)
        self.assertAlmostEqual(r["u0"], 0.409091, places=5)
        self.assertAlmostEqual(r["relacion_max_min"], 9.0, places=6)

    def test_banda_perimetral_excluida(self):
        # Sala 4×4, luminaria en (2,2), banda 1 m, paso 1 -> puntos x,y ∈ {1,2,3}:
        # mismas distancias relativas que el caso anterior -> mismos resultados (9 puntos).
        r = L.evaluar_malla(4, 4, [(2, 2)], math.pi, 1.0, banda_m=1.0, paso_m=1.0)
        self.assertEqual(r["n_puntos"], 9)
        self.assertAlmostEqual(r["e_min"], 1 / 9, places=6)
        self.assertAlmostEqual(r["u0"], 9 / 22, places=5)

    def test_validaciones(self):
        with self.assertRaises(ValueError):
            L.evaluar_malla(4, 4, [(2, 2)], 100, 1.0, banda_m=2.0)   # banda consume la sala
        with self.assertRaises(ValueError):
            L.evaluar_malla(4, 4, [], 100, 1.0)                     # sin luminarias
        with self.assertRaises(ValueError):
            L.evaluar_malla(4, 4, [(2, 2)], 100, 0)                 # h = 0
        with self.assertRaises(ValueError):
            L.evaluar_malla(4, 4, [(2, 2)], 100, 1.0, banda_m=-1)   # banda < 0


class TestEmergencia(unittest.TestCase):
    def test_one_luminaire_complies(self):
        # Sala 2×2, h = 1, Φ = 15 lm, banda 0, paso 1 (misma geometría que test_grilla_minima):
        # E_max = Φ/π = 15/3,14159 = 4,7746 lx ; E_min = E_max/9 = 0,53052 lx ≥ 0,5 ; relación = 9 ≤ 40
        r = L.size_emergency(2, 2, 1.0, 15, banda_m=0.0, paso_m=1.0)
        self.assertEqual((r["n"], r["nx"], r["ny"]), (1, 1, 1))
        self.assertAlmostEqual(r["e_min"], 0.530516, places=5)
        self.assertAlmostEqual(r["e_max"], 4.774648, places=5)
        self.assertAlmostEqual(r["relacion_max_min"], 9.0, places=6)

    def test_flux_insufficient(self):
        # Φ = 13: E_min = 13/(9π) = 0,4598 lx < 0,5 -> con n_max = 1 no hay solución
        with self.assertRaises(ValueError):
            L.size_emergency(2, 2, 1.0, 13, banda_m=0.0, paso_m=1.0, n_max=1)

    def test_relacion_configurable(self):
        # Con Φ = 15 la relación es 9; si se exige ≤ 8 no cumple con n_max = 1
        with self.assertRaises(ValueError):
            L.size_emergency(2, 2, 1.0, 15, relacion_max=8.0, banda_m=0.0, paso_m=1.0, n_max=1)

    def test_e_min_configurable(self):
        # Con exigencia 0,5 y Φ = 13 no cumple; con exigencia 0,4 sí (0,4598 ≥ 0,4)
        r = L.size_emergency(2, 2, 1.0, 13, e_min_req_lx=0.4, banda_m=0.0, paso_m=1.0, n_max=1)
        self.assertEqual(r["n"], 1)

    def test_validaciones(self):
        with self.assertRaises(ValueError):
            L.size_emergency(2, 2, 0, 15)
        with self.assertRaises(ValueError):
            L.size_emergency(2, 2, 1.0, 15, n_max=0)


class TestFlujoCompleto(unittest.TestCase):
    def test_size_normal(self):
        # N_min = 50 (ver arriba) ; malla 6×9 = 54 ; E medio por flujo = 324 lx
        r = L.size_normal(300, 40, 40, 8.0, 20000, 0.60, 0.80)
        self.assertEqual(r["n_min"], 50)
        self.assertEqual(r["n"], 54)
        self.assertAlmostEqual(r["e_medio_flujo"], 324.0, places=6)
        self.assertLess(r["e_min"], r["e_medio_directo"])
        self.assertLess(r["e_medio_directo"], r["e_max"])

    def test_plano_trabajo_invalido(self):
        with self.assertRaises(ValueError):
            L.size_normal(300, 40, 40, 8.0, 20000, 0.6, 0.8, plano_trabajo_m=9.0)


class TestRutaYConformidad(unittest.TestCase):
    def test_point_under_one_luminaire(self):
        # E = Φ/(π·h²) = 3 000 / (π · 4) = 238,732 lx (bajo la luminaria, h = 2 m)
        e = L.illuminance_in_point([(0.0, 0.0)], 3000, 2.0, 0.0, 0.0)
        self.assertAlmostEqual(e, 3000 / (math.pi * 4), places=6)

    def test_point_sum_of_two_luminaires(self):
        # Punto equidistante (dx = 1, dy = 0) de dos luminarias a ±1 m, h = 1 m:
        # d² = 1 + 1 = 2 ; E1 = (Φ/π)·h²/d⁴ = (Φ/π)/4 ; dos luminarias -> (Φ/π)/2 = 100/(2π)
        e = L.illuminance_in_point([(-1.0, 0.0), (1.0, 0.0)], 100, 1.0, 0.0, 0.0)
        self.assertAlmostEqual(e, 100 / (2 * math.pi), places=6)

    def test_axis_of_path(self):
        # Luminarias en x=0 y x=4, h=2, Φ=1 000 lm ; eje y=0 de x=0 a x=4, paso 2 -> x = 0, 2, 4
        # x=0: E = (Φ/π)[h²/h⁴ + h²/(16+4)²] = (1000/π)(1/4 + 4/400) = (1000/π)(0,26) = 82,761
        # x=2: dos luminarias a dx=2: d²=8, h²/d⁴ = 4/64 = 0,0625 -> (1000/π)(0,125) = 39,789
        r = L.iluminancia_eje_ruta([(0.0, 0.0), (4.0, 0.0)], 1000, 2.0, (0.0, 0.0), (4.0, 0.0),
                                   paso_m=2.0, e_min_req_lx=1.0)
        self.assertEqual(r["n_puntos"], 3)
        self.assertAlmostEqual(r["e_max"], 1000 / math.pi * 0.26, places=6)
        self.assertAlmostEqual(r["e_min"], 1000 / math.pi * 0.125, places=6)
        self.assertTrue(r["cumple"])
        r2 = L.iluminancia_eje_ruta([(0.0, 0.0), (4.0, 0.0)], 1000, 2.0, (0.0, 0.0), (4.0, 0.0),
                                    paso_m=2.0, e_min_req_lx=50.0)
        self.assertFalse(r2["cumple"])

    def test_eje_incluye_extremo_final(self):
        # Longitud 5 m con paso 2 -> x = 0, 2, 4 y el extremo 5 : 4 puntos
        r = L.iluminancia_eje_ruta([(0.0, 0.0)], 1000, 2.0, (0.0, 0.0), (5.0, 0.0), paso_m=2.0)
        self.assertEqual(r["n_puntos"], 4)

    def test_eje_validaciones(self):
        with self.assertRaises(ValueError):
            L.iluminancia_eje_ruta([(0.0, 0.0)], 1000, 2.0, (1.0, 1.0), (1.0, 1.0))
        with self.assertRaises(ValueError):
            L.illuminance_in_point([], 1000, 2.0, 0.0, 0.0)

    def test_conformidad_caso_h023(self):
        # Caso de la prueba: exigida 500 lx, flujo 576 lx, punto a punto 465 lx.
        # 0,9 · 500 = 450 -> 465 ≥ 450 y 576 ≥ 500 -> conforme
        c = L.conformidad_iluminancia(500, 576, 465)
        self.assertTrue(c["conforme"])
        self.assertAlmostEqual(c["e_directo_min_aceptable_lx"], 450.0)
        # punto a punto 440 < 450 -> no conforme
        self.assertFalse(L.conformidad_iluminancia(500, 576, 440)["conforme"])
        # flujo 480 < 500 -> no conforme aunque el directo pase
        c = L.conformidad_iluminancia(500, 480, 470)
        self.assertFalse(c["conforme"])
        self.assertFalse(c["flujo_ok"])
        self.assertTrue(c["directo_ok"])

    def test_ugr_no_verificable_sin_datos(self):
        self.assertEqual(L.verificar_ugr()["resultado"], "NO VERIFICABLE")
        self.assertEqual(L.verificar_ugr(ugr_calculado=19)["resultado"], "NO VERIFICABLE")
        self.assertIsNone(L.verificar_ugr(ugr_max=19)["cumple"])

    def test_ugr_con_datos_externos(self):
        self.assertEqual(L.verificar_ugr(18.5, 19)["resultado"], "CUMPLE")
        self.assertEqual(L.verificar_ugr(20, 19)["resultado"], "NO CUMPLE")
        with self.assertRaises(ValueError):
            L.verificar_ugr(-1, 19)


if __name__ == "__main__":
    unittest.main()
