"""Pruebas de aea_ampacity y de las columnas de instalación en aea_pipeline (valores a mano)."""
import unittest
from epc_calc import aea_ampacity as A
from epc_calc import aea_tables as T
from epc_calc import aea_pipeline as P

TABLERO = {"TENSION_V": 380, "ICC_KA": 10, "FP_DEFAULT": 0.85}


class TestAmpacity(unittest.TestCase):
    def test_defecto_es_cu_pvc_b1(self):
        p = A.parametros({})
        self.assertEqual((p["aislacion"], p["material"], p["metodo"]), ("pvc", "cu", "B1"))
        self.assertEqual(A.iz(p, 4, 3), 25)       # Tabla 771.16.I
        self.assertEqual(A.iz(p, 2.5, 1), 21)

    def test_xlpe_bandeja_con_factores(self):
        base = A.parametros({"AISLACION": "xlpe", "METODO": "C"})
        self.assertEqual(A.iz(base, 1.5, 3), 20)  # C_3x XLPE Cu 1,5 mm²
        p = A.parametros({"AISLACION": "xlpe", "METODO": "C", "N_TERNAS": 2, "CLASE": 5, "AGRUP_CIRCUITOS": 3})
        self.assertAlmostEqual(A.iz(p, 1.5, 3), 2 * 20 * 0.95 * 0.79)   # IV ítem 2, n = 3

    def test_temperatura(self):
        p = A.parametros({"AISLACION": "xlpe", "METODO": "E", "TEMP_AMBIENTE_C": 50})
        f = T.cargar()["factores_correccion"]["771.16.II.a"]
        fx = f["factores"]["xlpe"][f["temperaturas_c"]["xlpe"].index(50)]
        self.assertAlmostEqual(A.iz(p, 1.5, 3), 21 * fx)

    def test_enterrado(self):
        p = A.parametros({"AISLACION": "pvc", "METODO": "D1", "RESIST_TERMICA_KMW": 2.0})
        self.assertAlmostEqual(A.iz(p, 2.5, 1), 33 * 0.89)    # 771.16.V 2x = 33; VII.b D1 = 0,89

    def test_iz_informada_y_errores(self):
        p = A.parametros({"IZ_A": 300, "N_TERNAS": 2})
        self.assertEqual(A.iz(p, 185, 3), 600)
        with self.assertRaises(ValueError):
            A.iz(A.parametros({"AISLACION": "xlpe", "METODO": "B1"}), 4, 3)
        with self.assertRaises(ValueError):
            A.parametros({"MATERIAL": "fe"})
        with self.assertRaises(ValueError):
            A.parametros({"METODO": "Z"})

    def test_metodo_por_descripcion_y_sinonimos(self):
        p = A.parametros({"METODO": "Bandeja no perforada o de fondo sólido", "MATERIAL": "Aluminio", "AISLACION": "XLPE"})
        self.assertEqual((p["metodo"], p["material"], p["aislacion"]), ("C", "al", "xlpe"))
        for cod, desc in A.METODOS_DESCRIPCION.items():
            self.assertEqual(A.parametros({"METODO": desc})["metodo"], cod)
            self.assertEqual(A.parametros({"METODO": cod.lower()})["metodo"], cod)

    def test_aluminio(self):
        p = A.parametros({"MATERIAL": "al"})
        self.assertFalse(A.seccion_valida(p, 10))
        self.assertTrue(A.seccion_valida(p, 16))
        self.assertAlmostEqual(A.resistencia_ohm_km(16, "al", 90), 1.91 * (1 + 0.00403 * 70))
        self.assertEqual(A.temp_conductor(A.parametros({"AISLACION": "xlpe"})), 90.0)


class TestPipeline(unittest.TestCase):
    def _circ(self, **extra):
        c = {"TAG": "C-01", "CARGA": 120, "UNIDAD_CARGA": "A", "FASE": "3F", "LONGITUD_m": 40,
             "KIND": "mccb", "TOPOLOGY": "single"}
        c.update(extra)
        return [c]

    def test_aluminio_requiere_mayor_o_igual_seccion(self):
        cu, _ = P.calculate(TABLERO, self._circ())
        al, _ = P.calculate(TABLERO, self._circ(MATERIAL="al"))
        self.assertGreaterEqual(al["C-01"]["S"], cu["C-01"]["S"])
        self.assertGreaterEqual(al["C-01"]["S"], 16)

    def test_defecto_no_cambia(self):
        a, _ = P.calculate(TABLERO, self._circ())
        b, _ = P.calculate(TABLERO, self._circ(AISLACION="pvc", MATERIAL="cu", METODO="B1", CLASE=2, N_TERNAS=1))
        self.assertEqual(a, b)

    def test_ternas_reducen_seccion(self):
        una, _ = P.calculate(TABLERO, self._circ(CARGA=300, AISLACION="xlpe", METODO="C"))
        dos, _ = P.calculate(TABLERO, self._circ(CARGA=300, AISLACION="xlpe", METODO="C", N_TERNAS=2))
        self.assertLess(dos["C-01"]["S"], una["C-01"]["S"])

    def test_metodo_sin_tabla_da_aviso(self):
        _, avisos = P.calculate(TABLERO, self._circ(AISLACION="xlpe", METODO="B1"))
        self.assertTrue(any("B1 con XLPE" in a for a in avisos))


if __name__ == "__main__":
    unittest.main()
