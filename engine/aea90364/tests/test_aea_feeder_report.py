"""Pruebas de la Memoria de Cálculo y Síntesis del alimentador principal."""
import os
import shutil
import tempfile
import unittest

from epc_aea90364 import aea_feeder_report as AFR
from epc_aea90364 import aea_pipeline as P


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def _datos():
    tablero = {"TENSION_V": 380, "ICC_KA": 36, "FP_DEFAULT": 0.85, "SISTEMA": "TN-S"}
    circuitos = [
        {"TAG": "C-01", "DESCRIPCION": "ALIMENTADOR TD-PB", "CARGA": 250, "UNIDAD_CARGA": "A",
         "PARENT_TAG": None, "KIND": "mccb", "TOPOLOGY": "single", "FASE": "3F", "LONGITUD_m": 40,
         "CABLE_TIPO": "tetra_sep"},
        {"TAG": "M-01", "DESCRIPCION": "EXTRACTOR", "CARGA": 11, "UNIDAD_CARGA": "kW", "PARENT_TAG": None,
         "KIND": "auto", "TOPOLOGY": "dol_ol", "FASE": "3F", "LONGITUD_m": 30, "FP": 0.85, "RENDIMIENTO": 0.9},
    ]
    datos, _ = P.calculate(tablero, circuitos)
    return tablero, circuitos, datos


class TestAlimentadorPrincipal(unittest.TestCase):
    def test_elige_primer_mccb_sin_padre(self):
        _, circuitos, _ = _datos()
        self.assertEqual(AFR.alimentador_principal(circuitos)["TAG"], "C-01")

    def test_tag_explicito(self):
        _, circuitos, _ = _datos()
        self.assertEqual(AFR.alimentador_principal(circuitos, "M-01")["TAG"], "M-01")

    def test_sin_alimentador(self):
        with self.assertRaises(ValueError):
            AFR.alimentador_principal([{"TAG": "X", "KIND": "mcb", "PARENT_TAG": None}])


class TestDocumentos(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.base = os.path.join(self.dir, "P")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_genera_mc_y_sp_solo_del_principal(self):
        tablero, circuitos, datos = _datos()
        rutas = AFR.generar_documentos(self.base, tablero, circuitos, datos)
        self.assertEqual(len(rutas), 2)
        mc = _leer(self.base + "_MC.md")
        sp = _leer(self.base + "_SP.md")
        for etapa in ("Etapa 1", "Etapa 2", "Etapa 3", "Etapa 4", "Etapa 5", "Etapa 6"):
            self.assertIn(etapa, mc)
        self.assertIn("C-01", mc)
        self.assertNotIn("M-01", mc)
        self.assertIn("Requisito normativo", sp)
        self.assertNotIn("M-01", sp)

    def test_numeros_con_coma_y_resultado(self):
        tablero, circuitos, datos = _datos()
        AFR.generar_documentos(self.base, tablero, circuitos, datos)
        mc = _leer(self.base + "_MC.md")
        self.assertIn("Resultado global:", mc)
        self.assertIn(" %", mc)

    def test_sintesis_maximo_tres_observaciones(self):
        tablero, circuitos, datos = _datos()
        AFR.generar_documentos(self.base, tablero, circuitos, datos)
        sp = _leer(self.base + "_SP.md")
        obs = sp.split("**Observaciones**")[1].strip().splitlines()
        self.assertLessEqual(len([l for l in obs if l[:1].isdigit()]), 3)


if __name__ == "__main__":
    unittest.main()
