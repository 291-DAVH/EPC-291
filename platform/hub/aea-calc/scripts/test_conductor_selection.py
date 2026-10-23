"""Pruebas de conductor_selection.py (CAL-009) — cálculos a mano en los comentarios.

TABLAS FICTICIAS «solo para test»: no representan ninguna norma ni conductor real.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

import conductor_selection as S

AQUI = os.path.dirname(os.path.abspath(__file__))

# FICTICIA — SOLO PARA TEST (x = 0 para simplificar el cálculo a mano)
TABLE_TEST = {
    "_encabezado": "FICTICIO - solo para test",
    "fuente": {"id_nrm": "TEST", "edicion": "-", "tabla": "-", "pagina": "-"},
    "conductores": [
        {"seccion_mm2": 10, "i_adm_a": 60, "r_ohm_km": 1.0, "x_ohm_km": 0},
        {"seccion_mm2": 1.5, "i_adm_a": 10, "r_ohm_km": 10.0, "x_ohm_km": 0},   # desordenada a propósito
        {"seccion_mm2": 2.5, "i_adm_a": 20, "r_ohm_km": 5.0, "x_ohm_km": 0},
        {"seccion_mm2": 4, "i_adm_a": 30, "r_ohm_km": 2.5, "x_ohm_km": 0},
        {"seccion_mm2": 6, "i_adm_a": 40, "r_ohm_km": 2.0, "x_ohm_km": 0},
    ],
}
SERIES_TEST = [10, 16, 20, 25, 32, 40]   # FICTICIA — solo para test


class TestSeleccion(unittest.TestCase):
    def test_ampacity_governs(self):
        # Trifásica Ib = 24 A, L = 100 m, cosφ = 1, Un = 400 V, límite 3 % (12 V). In = 25 A.
        # Conducción: Iz ≥ 25 -> 4 mm² (30 A).
        # ΔU = √3·24·0,1·R = 4,1569·R ; con 4 mm² (R = 2,5): 10,39 V = 2,60 % ≤ 3 % -> 4 mm² cumple.
        r = S.seleccionar_conductor(24, 100, TABLE_TEST, 3, 400, 1.0, 3.0, serie_in=SERIES_TEST)
        self.assertEqual(r["resultado"], "OK")
        self.assertEqual(r["in_a"], 25)
        self.assertEqual(r["seccion_conduccion_mm2"], 4)
        self.assertEqual(r["seccion_caida_mm2"], 4)
        self.assertEqual(r["seccion_mm2"], 4)
        self.assertAlmostEqual(r["delta_u_pct"], 100 * 4.1569219 * 2.5 / 400, places=3)
        self.assertEqual(r["proteccion"], "OK")
        self.assertEqual(r["criterio_gobernante"], "conducción")

    def test_drop_governs(self):
        # Mismos datos con L = 200 m: ΔU = √3·24·0,2·R = 8,3138·R ≤ 12 V -> R ≤ 1,443 -> 10 mm² (R = 1)
        # (6 mm²: R = 2 -> 16,6 V = 4,16 % > 3 %). Conducción pediría 4 mm² -> gobierna la caída: 10 mm².
        r = S.seleccionar_conductor(24, 200, TABLE_TEST, 3, 400, 1.0, 3.0, serie_in=SERIES_TEST)
        self.assertEqual(r["seccion_conduccion_mm2"], 4)
        self.assertEqual(r["seccion_caida_mm2"], 10)
        self.assertEqual(r["seccion_mm2"], 10)
        self.assertEqual(r["criterio_gobernante"], "caída de tensión")
        self.assertAlmostEqual(r["delta_u_pct"], 100 * 8.3138438 / 400, places=3)

    def test_factores_de_correccion(self):
        # f = 0,8 · 0,9 = 0,72. Iz: 4 mm² = 21,6 A < 25 ; 6 mm² = 28,8 A ≥ 25 -> 6 mm².
        r = S.seleccionar_conductor(24, 100, TABLE_TEST, 3, 400, 1.0, 3.0, 0.8, 0.9, SERIES_TEST)
        self.assertEqual(r["seccion_conduccion_mm2"], 6)
        self.assertAlmostEqual(r["iz_a"], 28.8)
        self.assertAlmostEqual(r["f_total"], 0.72)

    def test_in_limita_la_seccion(self):
        # Serie solo [32]: In = 32 -> Iz ≥ 32 -> 6 mm² (40 A), aunque Ib = 24 A bastaría con 4 mm².
        r = S.seleccionar_conductor(24, 100, TABLE_TEST, 3, 400, 1.0, 3.0, serie_in=[32])
        self.assertEqual(r["seccion_conduccion_mm2"], 6)

    def test_sin_serie_protecciones_no_verificable(self):
        # Sin serie: Iz ≥ Ib = 24 -> 4 mm² (30 A)
        r = S.seleccionar_conductor(24, 100, TABLE_TEST, 3, 400, 1.0, 3.0)
        self.assertEqual(r["proteccion"], "NO VERIFICABLE")
        self.assertIsNone(r["in_a"])
        self.assertEqual(r["seccion_mm2"], 4)
        self.assertTrue(any("Sin serie" in a for a in r["advertencias"]))

    def test_single_phase(self):
        # Ib = 10 A, L = 50 m, Un = 230 V, límite 3 % = 6,9 V ; ΔU = 2·10·0,05·R = R.
        # R = 10 (1,5 mm²): 10 V > 6,9 ; R = 5 (2,5 mm²): 5 V = 2,17 % ✓. In = 10 -> Iz ≥ 10: 1,5 mm².
        r = S.seleccionar_conductor(10, 50, TABLE_TEST, 1, 230, 1.0, 3.0, serie_in=[10, 16])
        self.assertEqual(r["seccion_conduccion_mm2"], 1.5)
        self.assertEqual(r["seccion_caida_mm2"], 2.5)
        self.assertEqual(r["seccion_mm2"], 2.5)
        self.assertAlmostEqual(r["delta_u_pct"], 100 * 5 / 230, places=4)

    def test_no_verificable_sin_tabla(self):
        r = S.seleccionar_conductor(24, 100, None, 3, 400, 0.9, 3.0, serie_in=SERIES_TEST)
        self.assertEqual(r["resultado"], "NO VERIFICABLE")
        self.assertEqual(r["proteccion"], "NO VERIFICABLE")
        self.assertIn("tabla", r["motivo"])

    def test_no_cumple_si_la_tabla_no_alcanza(self):
        # L = 300 m: ΔU = 12,47·R ≥ 12,47 V (R mín = 1) > 12 V -> ninguna sección cumple la caída
        r = S.seleccionar_conductor(24, 300, TABLE_TEST, 3, 400, 1.0, 3.0, serie_in=SERIES_TEST)
        self.assertEqual(r["resultado"], "NO CUMPLE")
        self.assertIsNone(r["seccion_mm2"])
        self.assertIn("caída", r["motivo"])
        # Ib mayor que cualquier In de la serie
        r = S.seleccionar_conductor(70, 10, TABLE_TEST, 3, 400, 1.0, 3.0, serie_in=SERIES_TEST)
        self.assertEqual(r["resultado"], "NO CUMPLE")
        self.assertEqual(r["proteccion"], "NO CUMPLE")
        # Corriente mayor que la capacidad de la mayor sección
        r = S.seleccionar_conductor(50, 1, TABLE_TEST, 3, 400, 1.0, 3.0, 0.5, 0.5, [50])
        self.assertEqual(r["resultado"], "NO CUMPLE")
        self.assertIn("conducción", r["motivo"])

    def test_advertencia_tabla_ficticia(self):
        r = S.seleccionar_conductor(24, 100, TABLE_TEST, 3, 400, 1.0, 3.0)
        self.assertTrue(any("FICTICIA" in a for a in r["advertencias"]))

    def test_validaciones(self):
        with self.assertRaises(ValueError):
            S.seleccionar_conductor(-1, 100, TABLE_TEST, 3, 400, 1.0, 3.0)
        with self.assertRaises(ValueError):
            S.seleccionar_conductor(24, 100, TABLE_TEST, 3, 400, 1.0, 3.0, f_agrupamiento=1.2)
        with self.assertRaises(ValueError):
            S.seleccionar_conductor(24, 100, TABLE_TEST, 2, 400, 1.0, 3.0)   # fases inválidas (CAL-002)
        with self.assertRaises(ValueError):
            S.seleccionar_conductor(24, 100, TABLE_TEST, 3, 400, 1.0, 3.0, serie_in=[])
        with self.assertRaises(ValueError):
            S.cargar_tabla({"conductores": []})
        with self.assertRaises(ValueError):
            S.cargar_tabla({"conductores": [{"seccion_mm2": 1.5, "i_adm_a": 10}]})   # falta r
        with self.assertRaises(ValueError):
            S.cargar_tabla({"conductores": [{"seccion_mm2": 1.5, "i_adm_a": 10, "r_ohm_km": 1},
                                            {"seccion_mm2": 1.5, "i_adm_a": 12, "r_ohm_km": 1}]})

    def test_ejemplo_json_ficticio_y_cli(self):
        ruta = os.path.join(AQUI, "example_conductor_table.json")
        with open(ruta, encoding="utf-8") as f:
            crudo = json.load(f)
        self.assertIn("FICTICIO", crudo["_encabezado"])
        self.assertIn("reemplazar por extracto de norma", crudo["_encabezado"])
        t = S.cargar_tabla(ruta)
        self.assertTrue(any("FICTICIA" in a for a in t["advertencias"]))
        cp = subprocess.run([sys.executable, "-B", os.path.join(AQUI, "conductor_selection.py"), ruta,
                             "--ib", "24", "--longitud", "50", "--fases", "3", "--un", "400",
                             "--drop-max", "3", "--serie-in", "10,16,20,25,32", "--json"],
                            capture_output=True, text=True)
        self.assertIn(cp.returncode, (0, 1), cp.stderr)
        self.assertIn("resultado", json.loads(cp.stdout))
        # tabla inexistente -> NO VERIFICABLE (código 1)
        cp = subprocess.run([sys.executable, "-B", os.path.join(AQUI, "conductor_selection.py"), "/no/existe.json",
                             "--ib", "24", "--longitud", "50", "--fases", "3", "--un", "400",
                             "--drop-max", "3", "--json"], capture_output=True, text=True)
        self.assertEqual(cp.returncode, 1)
        self.assertEqual(json.loads(cp.stdout)["resultado"], "NO VERIFICABLE")

    def test_tabla_desde_archivo_temporal(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = os.path.join(tmp, "t.json")
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump(TABLE_TEST, f)
            r = S.seleccionar_conductor(24, 100, ruta, 3, 400, 1.0, 3.0, serie_in=SERIES_TEST)
            self.assertEqual(r["seccion_mm2"], 4)


if __name__ == "__main__":
    unittest.main()
