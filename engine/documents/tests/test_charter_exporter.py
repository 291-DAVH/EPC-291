"""Pruebas de charter_exporter.py (CAL-013) y de la consistencia charter técnico ↔ ejecutivo (CAL-010, A3-19/A3-20)."""
import os
import re
import shutil
import tempfile
import unittest

from epc_documents import charter_exporter as X
from epc_documents import document_verifier as V

charter = """# project-charter.md — Project Charter

| Campo | Valor |
|---|---|
| Proyecto | Subestación Planta Norte |
| Código de proyecto | EJ01 |
| Versión de la línea base | 1.0 |
| Estado | APROBADO |
| Fecha | 2026-11-02 |

---

# GUÍA DEL ARCHIVO (no editar)

Ejemplo de ID de guía: RIE-999.

# REGISTRO DEL PROYECTO (generado por Claude)

## 3. Descripción del proyecto

### 3.1 Alcance

**3.1.1 Incluye (IN).** ALD-001 ingeniería base; ALD-002 pliego.

**3.1.2 Excluye (OUT).** EXC-001 detalle.

### 3.2 Criterios de éxito

| N.º | Criterio | Tipo | Fuente |
|---|---|---|---|
| 1 | Pliego aprobado | Crítico | CAC-001 |

### 3.7 Supuestos

| ID | Supuesto | Fecha |
|---|---|---|
| SUP-001 | Cortocircuito según carta | 2026-11-20 |

### 3.8 Riesgos

| ID | Riesgo | Prob. | Impacto | Nivel | Estrategia | Acción | Responsable |
|---|---|---|---|---|---|---|---|
| RIE-001 | Falta el cortocircuito | 3 | 5 | 15 | Reducir | Pedirlo | PM |
| RIE-002 | Cargas tarde | 3 | 3 | 9 | Reducir | Fecha límite | PM |

## 4. Costo, plazo y recursos

### 4.1 Costo

`[DEFINIR]` — campo libre.

### 4.2 Plazo e hitos

12 semanas.

| ID | Hito | Fecha objetivo |
|---|---|---|
| H-01 | Línea base | 2026-11-02 |
| H-02 | Emisión ifa | 2026-12-07 |

### 4.3 Recursos previstos

Ninguno.

## 7. Plan de paquetes

| Orden | Paquete | Documentos | Depende de |
|---|---|---|---|
| 1 | PQ-01 | Criterios | — |
| 2 | PQ-02 | Unifilar | PQ-01 |

## 8. Preguntas pendientes

Ninguna.
"""

EJEC = """# project-charter-executive.md

# LIENZO EJECUTIVO (generado por Claude)

## Subestación Planta Norte

| Proyecto | Versión | Fecha | Estado |
|---|---|---|---|
| EJ01 · Subestación Planta Norte | 1.0 | 2026-11-02 | APROBADO |

**En una frase:** ampliar la alimentación.

### Alcance

| Dentro del alcance | Fuera del alcance |
|---|---|
| Ingeniería base <!-- fuente: ALD-001 --> | Detalle <!-- fuente: EXC-001 --> |
| Pliego <!-- fuente: ALD-002 --> | |

### Supuestos

- Cortocircuito según carta. <!-- fuente: SUP-001 -->

### Hitos

| Inicio | Planificación | Ejecución | Cierre |
|---|---|---|---|
| Línea base 2026-11-02 | | Emisión ifa 2026-12-07 | |

### Riesgos

| Riesgo | Prob. | Impacto | Nivel | Qué haremos |
|---|---|---|---|---|
| RIE-001 · Falta el cortocircuito | 3 | 5 | 15 | Pedirlo |
| RIE-002 · Cargas tarde | 3 | 3 | 9 | Fecha límite |

### Presupuesto

A definir por el cliente.

### Plazo

12 semanas.

### Criterios críticos de éxito

- Pliego aprobado. <!-- fuente: CAC-001 -->

### Desglose del trabajo

| Orden | Paquete | Qué contiene | Depende de |
|---|---|---|---|
| 1 | PQ-01 | Criterios | — |
| 2 | PQ-02 | Unifilar | PQ-01 |
"""


def _w(ruta, contenido, modo="w"):
    with open(ruta, modo, **({} if "b" in modo else {"encoding": "utf-8"})) as f:
        f.write(contenido)


def msgs(h):
    return [m for _s, _c, m in h]


class TestConsistencia(unittest.TestCase):
    def test_coherentes(self):
        self.assertEqual(V.comprobar_charter_ejecutivo(charter, EJEC), [])

    def test_version_fecha_estado(self):
        e = EJEC.replace("| 1.0 | 2026-11-02 | APROBADO |", "| 1.1 | 2026-11-03 | BORRADOR |")
        m = " ".join(msgs(V.comprobar_charter_ejecutivo(charter, e)))
        self.assertIn("Versión distinta", m)
        self.assertIn("Fecha distinta", m)
        self.assertIn("Estado distinto", m)

    def test_id_faltante_y_sobrante(self):
        e = EJEC.replace(" <!-- fuente: SUP-001 -->", "").replace("<!-- fuente: ALD-002 -->", "<!-- fuente: ALD-009 -->")
        m = " ".join(msgs(V.comprobar_charter_ejecutivo(charter, e)))
        self.assertIn("no incluye SUP-001", m)
        self.assertIn("no incluye ALD-002", m)
        self.assertIn("cita ALD-009", m)

    def test_id_de_la_guia_no_cuenta(self):
        self.assertNotIn("RIE-999", " ".join(msgs(V.comprobar_charter_ejecutivo(charter, EJEC))))

    def test_nivel_de_riesgo_distinto(self):
        e = EJEC.replace("| 3 | 5 | 15 |", "| 2 | 5 | 10 |")
        self.assertTrue(any("RIE-001" in m and "distintos" in m for m in msgs(V.comprobar_charter_ejecutivo(charter, e))))

    def test_nivel_incoherente_es_aviso(self):
        e = EJEC.replace("| 3 | 3 | 9 |", "| 3 | 3 | 8 |")
        c = charter.replace("| 3 | 3 | 9 |", "| 3 | 3 | 8 |")
        h = V.comprobar_charter_ejecutivo(c, e)
        self.assertEqual([s for s, _c, _m in h], ["AVISO", "AVISO"])

    def test_paquetes_orden_y_dependencias(self):
        e = EJEC.replace("| PQ-01 |\n", "| PQ-01, PQ-09 |\n")
        self.assertTrue(any("PQ-02" in m and "dependencias" in m for m in msgs(V.comprobar_charter_ejecutivo(charter, e))))
        e2 = EJEC.replace("| 1 | PQ-01 |", "| 1 | PQ-02 |").replace("| 2 | PQ-02 |", "| 2 | PQ-01 |")
        self.assertTrue(any("Orden de paquetes" in m for m in msgs(V.comprobar_charter_ejecutivo(charter, e2))))

    def test_hitos(self):
        e = EJEC.replace("2026-12-07", "2026-12-08")
        self.assertTrue(any("Fechas de hitos" in m for m in msgs(V.comprobar_charter_ejecutivo(charter, e))))

    def test_costo(self):
        e = EJEC.replace("A definir por el cliente.", "USD 1 000")
        self.assertTrue(any("A definir por el cliente" in m for m in msgs(V.comprobar_charter_ejecutivo(charter, e))))
        c = charter.replace("`[DEFINIR]` — campo libre.", "Monto informado por el cliente: 50 000 (DEC-003).")
        e2 = EJEC.replace("A definir por el cliente.", "Monto informado por el cliente: 50 000 (DEC-003).")
        self.assertEqual(V.comprobar_charter_ejecutivo(c, e2), [])
        self.assertTrue(any("no es el costo" in m for m in msgs(V.comprobar_charter_ejecutivo(c, EJEC.replace("A definir por el cliente.", "Otro monto")))))


class TestProyectoYPdf(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.d, "02_PROJECT"))
        self.ch = os.path.join(self.d, "02_PROJECT", "project-charter.md")
        self.ex = os.path.join(self.d, "02_PROJECT", "project-charter-executive.md")

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def _escribir(self, ejec=EJEC):
        _w(self.ch, charter, "w")
        _w(self.ex, ejec, "w")

    def _hall(self, cat):
        return [h for h in V.verificar_proyecto(self.d)["hallazgos"] if h["categoria"] == cat]

    def test_pdf_ausente_aviso_si_borrador_error_si_aprobado(self):
        self._escribir(EJEC.replace("APROBADO", "BORRADOR"))
        _w(self.ch, charter.replace("APROBADO", "BORRADOR"), "w")
        self.assertEqual([h["severidad"] for h in self._hall("charter_ejecutivo_pdf")], ["AVISO"])
        self._escribir()
        self.assertEqual([h["severidad"] for h in self._hall("charter_ejecutivo_pdf")], ["ERROR"])

    @unittest.skipUnless(shutil.which("pdftotext") and os.path.exists("/opt/pw-browsers/chromium"), "needs poppler (pdftotext) and the Playwright chromium used by the exporter")
    def test_pdf_con_sello(self):
        self._escribir()
        s = X.sello_md(EJEC)
        pdf = os.path.join(self.d, "02_PROJECT", "PROJECT_charter_EXECUTIVE.pdf")
        _w(pdf, b"%PDF-1.4\n/Subject (sha256:" + s.encode() + b")\n", "wb")
        self.assertEqual(self._hall("charter_ejecutivo_pdf"), [])
        _w(pdf, b"%PDF-1.4\n/Subject (sha256:0000000000000000)\n", "wb")
        self.assertEqual([h["severidad"] for h in self._hall("charter_ejecutivo_pdf")], ["ERROR"])

    def test_plantilla_con_guia_no_se_compara(self):
        self._escribir("# X\n\n# GUÍA DEL ARCHIVO (no editar)\n\n" + EJEC.replace("1.0", "9.9"))
        self.assertEqual(self._hall("charter_ejecutivo"), [])

    def test_sellos_iguales_en_ambos_modulos(self):
        self.assertEqual(X.sello_md(EJEC), V.sello_charter_md(EJEC))
        self.assertEqual(X.sello_md("a\r\nb"), X.sello_md("a\nb"))


class TestExportador(unittest.TestCase):
    def test_parsear_cajas_e_ids(self):
        d = X.parsear(EJEC)
        self.assertEqual(d["encabezado"]["version"], "1.0")
        self.assertIn("Riesgos", d["cajas"])
        self.assertIn("ALD-001", [i for i in d["cajas"]["Alcance"]["ids"]])
        self.assertTrue(any("Falta la caja" in a for a in d["avisos"]))

    def test_riesgos(self):
        rs = X.riesgos(X.parsear(EJEC))
        self.assertEqual([r["id"] for r in rs], ["RIE-001", "RIE-002"])
        self.assertEqual([r["nivel"] for r in rs], [15, 9])

    def test_html_contiene_cajas_y_sello(self):
        d = X.parsear(EJEC)
        h = X.generar_html(d, X.sello_md(EJEC))
        self.assertIn("sha256:" + X.sello_md(EJEC), h)
        self.assertIn("RIE-001", h)
        self.assertIn("A definir por el cliente", h)

    def test_definir_se_muestra_pendiente(self):
        h = X.generar_html(X.parsear(EJEC.replace("ampliar la alimentación.", "`[DEFINIR]`")), "0" * 16)
        self.assertIn("Pendiente de definir", h)

    def test_exportar_solo_html_y_verificar(self):
        with tempfile.TemporaryDirectory() as t:
            md = os.path.join(t, "E.md")
            _w(md, EJEC, "w")
            r = X.exportar(md, solo_html=True)
            self.assertTrue(os.path.exists(r["html"]))
            self.assertEqual(X.verificar(md)["estado"], "FALTA_PDF")

    @unittest.skipUnless(os.path.exists("/opt/pw-browsers/chromium") or shutil.which("chromium") or shutil.which("chromium-browser"), "sin Chromium")
    def test_pdf_una_pagina_con_sello(self):
        try:
            import pypdf
        except ImportError:
            self.skipTest("sin pypdf")
        with tempfile.TemporaryDirectory() as t:
            md = os.path.join(t, "E.md")
            _w(md, EJEC, "w")
            r = X.exportar(md)
            if not r["pdf"]:
                self.skipTest("Chromium no disponible: " + "; ".join(r["avisos"]))
            self.assertEqual(len(pypdf.PdfReader(r["pdf"]).pages), 1)
            self.assertEqual(X.verificar(md)["estado"], "OK")
            _w(md, "\n<!-- cambio -->\n", "a")
            self.assertEqual(X.verificar(md)["estado"], "DESACTUALIZADO")


if __name__ == "__main__":
    unittest.main()
