#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pruebas de input_converter.py (CAL-012). Usan herramientas falsas (scripts) para no depender de LibreOffice."""
import os
import stat
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
from epc_documents import input_converter as C  # noqa: E402

SOFFICE_FALSO = """#!/bin/sh
# uso: soffice --headless --convert-to pdf --outdir DIR ORIGEN
out="$5"; src="$6"; base=$(basename "$src"); name="${base%.*}"
case "$src" in *malo*) echo "fallo simulado" >&2; exit 1;; esac
echo "%PDF-falso" > "$out/$name.pdf"
"""
PDFTOPPM_FALSO = """#!/bin/sh
# uso: pdftoppm -png -r DPI PDF PREFIJO
prefijo="$5"
echo x > "${prefijo}-1.png"; echo x > "${prefijo}-2.png"
"""


def _script(dir_, nombre, contenido):
    p = os.path.join(dir_, nombre)
    with open(p, "w", encoding="utf-8") as f:
        f.write(contenido)
    os.chmod(p, os.stat(p).st_mode | stat.S_IEXEC)
    return p


def _archivo(raiz, ruta, texto="x"):
    p = os.path.join(raiz, ruta)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(texto)
    return p


@unittest.skipIf(os.name == "nt", "the fake soffice is a shell script: needs a POSIX shell")
class TestConvertirEntrada(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.bin = os.path.join(self.tmp.name, "bin")
        os.makedirs(self.bin)
        os.environ["SOFFICE"] = _script(self.bin, "soffice", SOFFICE_FALSO)
        os.environ["PDFTOPPM"] = _script(self.bin, "pdftoppm", PDFTOPPM_FALSO)
        self.raiz = os.path.join(self.tmp.name, "entrada")
        os.makedirs(self.raiz)

    def tearDown(self):
        os.environ.pop("SOFFICE", None)
        os.environ.pop("PDFTOPPM", None)
        self.tmp.cleanup()

    def test_convierte_office_a_pdf_sin_tocar_el_original(self):
        orig = _archivo(self.raiz, "01-CONTRATO/presentacion.pptx", "contenido")
        res = C.procesar(self.raiz)
        self.assertEqual(res["resumen"]["fallos"], 0)
        copia = os.path.join(self.raiz, "_convertidos", "01-CONTRATO", "presentacion.pdf")
        self.assertTrue(os.path.exists(copia))
        self.assertEqual(open(orig, encoding="utf-8").read(), "contenido")

    def test_no_convierte_archivos_ya_pdf_ni_otros(self):
        _archivo(self.raiz, "a/plano.pdf")
        _archivo(self.raiz, "a/nota.txt")
        res = C.procesar(self.raiz)
        self.assertEqual(res["items"], [])

    def test_omite_si_la_copia_esta_vigente(self):
        _archivo(self.raiz, "a/x.docx")
        C.procesar(self.raiz)
        res = C.procesar(self.raiz)
        self.assertIn("omitido", res["items"][0]["estado"])

    def test_fallo_de_conversion_se_informa(self):
        _archivo(self.raiz, "a/malo.pptx")
        res = C.procesar(self.raiz)
        self.assertEqual(res["resumen"]["fallos"], 1)
        self.assertIn("fallo simulado", res["items"][0]["estado"])

    def test_imagenes_de_un_pdf_propio_y_de_uno_convertido(self):
        _archivo(self.raiz, "a/plano.pdf")
        _archivo(self.raiz, "a/slides.pptx")
        res = C.procesar(self.raiz, imagenes=True)
        acciones = sorted((i["original"], i["accion"]) for i in res["items"])
        self.assertEqual(acciones, [("a/plano.pdf", "imagenes"), ("a/slides.pptx", "imagenes"), ("a/slides.pptx", "pdf")])
        self.assertTrue(os.path.exists(os.path.join(self.raiz, "_convertidos", "a", "plano_paginas", "p-1.png")))

    def test_sin_libreoffice_no_falla_el_script(self):
        os.environ["SOFFICE"] = os.path.join(self.bin, "no_existe")
        _archivo(self.raiz, "a/x.pptx")
        res = C.procesar(self.raiz)
        self.assertEqual(res["items"][0]["estado"], "falta LibreOffice")

    def test_no_reprocesa_la_carpeta_de_salida(self):
        _archivo(self.raiz, "a/x.pptx")
        C.procesar(self.raiz, imagenes=True)
        res = C.procesar(self.raiz, imagenes=True)
        self.assertTrue(all(not i["original"].startswith("_convertidos") for i in res["items"]))

    def test_carpeta_inexistente(self):
        self.assertEqual(C.main([os.path.join(self.tmp.name, "nada")]), 2)

    def test_markdown_y_retorno(self):
        _archivo(self.raiz, "a/x.pptx")
        md = os.path.join(self.tmp.name, "informe.md")
        self.assertEqual(C.main([self.raiz, "--md", md]), 0)
        self.assertIn("Conversión de la información de entrada", open(md, encoding="utf-8").read())


if __name__ == "__main__":
    unittest.main()
