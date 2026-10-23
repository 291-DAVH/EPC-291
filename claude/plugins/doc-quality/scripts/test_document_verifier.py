"""Pruebas de document_verifier.py (CAL-010). Crean mini-proyectos en un directorio temporal."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

import document_verifier as V

AQUI = os.path.dirname(os.path.abspath(__file__))

LME = """# DELIVERABLES

| ID | Código | Título | Categoría | Fase | Tipo | Aplica (SÍ/NO) | Estado | Rev. | Fecha prevista |
|---|---|---|---|---|---|---|---|---|---|
| ENT-001 | AB01-E-MC-001 | Balance | Cálculos | ID | MC | SÍ | ENGINEERING | {rev1} | 2026-10-10 |
| ENT-002 | AB01-E-MD-001 | Memoria | Documentación | ID | MD | SÍ | ENGINEERING | {rev2} | 2026-10-12 |
| ENT-003 | AB01-E-ET-001 | Especificación | Documentación | ID | ET | NO | — | — | — |
"""

REGISTRO = """# ASSUMPTIONS_AND_decisions

| ID | Fecha | Texto |
|---|---|---|
| DEC-001 | 2026-10-07 | Decisión uno |
| DEC-002 | 2026-10-08 | Decisión dos |
| SUP-001 | 2026-10-07 | Supuesto uno |
"""

INFO = """# PROJECT_INFORMATION

| ID | Dato | Estado |
|---|---|---|
| INF-001 | Plano del cliente | PENDING |
"""

CAMBIOS = """# CHANGE_REQUESTS

| ID | Fecha | Descripción |
|---|---|---|
| rfc-001 | 2026-10-21 | Cambio uno |
| rfc-002 | 2026-10-22 | Cambio dos |
| rfc-003 | 2026-10-23 | Cambio tres |
| rfc-004 | 2026-10-24 | Cambio cuatro |
"""


def _origen(rev):
    """Origen de una fila de control: una revisión 00.n (n >= 1) nace de la rfc-n (DOCUMENT_RULES.md, 9)."""
    partes = [x for x in rev.split(".") if x.isdigit()]   # sin el sufijo de fase
    if len(partes) == 3 and int(partes[2]) >= 1:
        return f"REV-{int(partes[2]):03d}"          # comentario incorporado (00.R.c, c >= 1)
    if len(partes) >= 2 and int(partes[1]) >= 1:
        return f"rfc-{int(partes[1]):03d}"
    return "—"


def doc(codigo, rev, titulo, cuerpo="", rev_tabla=None, rev_titulo=None, rev_ctrl=None):
    ctrl = rev_ctrl or rev
    return (f"# {codigo}_Rev{rev_titulo or rev} — {titulo}\n\n| Campo | Valor |\n|---|---|\n"
            f"| Código | {codigo} |\n| Revisión | {rev_tabla or rev} |\n\n"
            f"## Control de revisiones\n\n| Rev. | Fecha | Descripción |\n|---|---|---|\n"
            f"| 00.0 | 2026-10-08 | Inicial |\n| {ctrl} | 2026-10-20 | Cambio {_origen(ctrl)} |\n\n{cuerpo}\n")


def escribir(raiz, ruta, texto):
    p = os.path.join(raiz, ruta)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(texto)
    return p


def proyecto_base(raiz, rev1="00.2", rev2="00.2", cuerpo1="", cuerpo2="", **kw1):
    escribir(raiz, "90-management/deliverables.md", LME.format(rev1=rev1, rev2=rev2))
    escribir(raiz, "assumptions-and-decisions.md", REGISTRO)
    escribir(raiz, "project-information.md", INFO)
    escribir(raiz, "change-requests.md", CAMBIOS)
    escribir(raiz, "02/AB01-E-MC-001_Rev00.2.md", doc("AB01-E-MC-001", "00.2", "Balance", cuerpo1, **kw1))
    escribir(raiz, "02/AB01-E-MD-001_Rev00.2.md", doc("AB01-E-MD-001", "00.2", "Memoria", cuerpo2))


def hallazgos(res, cat):
    return [h for h in res["hallazgos"] if h["categoria"] == cat]


class TestProyectoLimpio(unittest.TestCase):
    def test_sin_hallazgos(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d, cuerpo1="Ver `AB01-E-MD-001` Rev 00.2 y DEC-001, SUP-001, INF-001, rfc-001.",
                          cuerpo2="Según AB01-E-MC-001 vigente. Ver DEC-001 a DEC-002.")
            r = V.verificar_proyecto(d)
            self.assertEqual(r["resumen"]["errores"], 0, r["hallazgos"])
            self.assertEqual(r["resumen"]["avisos"], 0, r["hallazgos"])
            self.assertEqual(r["resumen"]["documentos_con_codigo"], 2)
            self.assertEqual(r["documentos_vigentes"]["AB01-E-MC-001"], "00.2")
            self.assertEqual(r["resumen"]["citas_rev_revisadas"], 1)    # «vigente» no cuenta como discrepancia
            self.assertGreaterEqual(r["registros"]["DEC"], 2)


class TestRevision(unittest.TestCase):
    def test_cabecera_distinta_del_archivo(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d, rev_tabla="00.1")
            rs = hallazgos(V.verificar_proyecto(d), "revision")
            self.assertEqual(len(rs), 1)
            self.assertIn("cabecera dice 00.1", rs[0]["mensaje"])

    def test_titulo_y_control_distintos(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d, rev_titulo="00.3", rev_ctrl="00.4")
            msgs = " | ".join(h["mensaje"] for h in hallazgos(V.verificar_proyecto(d), "revision"))
            self.assertIn("título dice 00.3", msgs)
            self.assertIn("Control de revisiones» dice 00.4", msgs)

    def test_lme_desactualizada(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d, rev1="00.1")
            rs = hallazgos(V.verificar_proyecto(d), "revision")
            self.assertEqual(len(rs), 1)
            self.assertEqual(rs[0]["archivo"], "deliverables.md")
            self.assertIn("ENT-001", rs[0]["mensaje"])

    def test_annex_con_otra_revision(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d)
            escribir(d, "02/AB01-E-MC-001_Rev00.1_annex_A_calculo.py", "print(1)\n")
            rs = hallazgos(V.verificar_proyecto(d), "revision")
            self.assertEqual(len(rs), 1)
            self.assertIn("anexo", rs[0]["mensaje"])

    def test_version_superada_y_lme_sin_archivo_y_archivo_fuera_de_lme(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d)
            escribir(d, "02/AB01-E-MC-001_Rev00.1.md", doc("AB01-E-MC-001", "00.1", "Balance"))
            escribir(d, "02/AB01-E-PL-001_Rev00.1.md", doc("AB01-E-PL-001", "00.1", "Plano"))
            r = V.verificar_proyecto(d)
            self.assertEqual(len(hallazgos(r, "version_superada")), 1)
            self.assertEqual(len(hallazgos(r, "lme")), 1)
            self.assertIn("AB01-E-PL-001", hallazgos(r, "lme")[0]["mensaje"])
            os.remove(os.path.join(d, "02/AB01-E-MD-001_Rev00.2.md"))
            self.assertTrue(any("AB01-E-MD-001" in h["mensaje"] for h in hallazgos(V.verificar_proyecto(d), "lme")))

    def test_archivo_historico_se_omite(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d)
            escribir(d, "03_ENGINEERING/Archive/AB01-E-MC-001_Rev00.1.md", doc("AB01-E-MC-001", "00.1", "Balance"))
            r = V.verificar_proyecto(d)
            self.assertEqual(r["resumen"]["errores"] + r["resumen"]["avisos"], 0)

    def test_entregables_se_omite_y_editables_se_recorre(self):
        """07_DELIVERABLES guarda copias de lo entregado (Rev 00): no cuentan como duplicado ni versión superada."""
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d)
            escribir(d, "07_DELIVERABLES/ifa/20261202_TR-001_Rev00/Documents/AB01-E-MC-001_Rev00.md",
                     doc("AB01-E-MC-001", "00", "Balance"))
            r = V.verificar_proyecto(d)
            self.assertEqual(r["resumen"]["errores"] + r["resumen"]["avisos"], 0)
            # un documento superado dentro de 03_ENGINEERING (fuera del archivo histórico) sí se detecta
            escribir(d, "03_ENGINEERING/Calculations/AB01-E-MC-001_Rev00.1.md", doc("AB01-E-MC-001", "00.1", "Balance"))
            self.assertEqual(len(hallazgos(V.verificar_proyecto(d), "version_superada")), 1)

    def test_sin_lme_no_falla(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d)
            os.remove(os.path.join(d, "90-management", "deliverables.md"))
            r = V.verificar_proyecto(d)
            self.assertIn("deliverables.md", r["nota_lme"])
            self.assertEqual(r["resumen"]["errores"], 0)


class TestCitas(unittest.TestCase):
    def test_cita_rev_desactualizada(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d, cuerpo1="Usa `AB01-E-MD-001` Rev 00.1 y AB01-E-MD-001_Rev00.2.")
            rs = hallazgos(V.verificar_proyecto(d), "cita_rev")
            self.assertEqual(len(rs), 1)
            self.assertIn("Rev 00.1", rs[0]["mensaje"])
            self.assertIn("vigente es 00.2", rs[0]["mensaje"])
            self.assertTrue(rs[0]["archivo"].endswith(":" + rs[0]["archivo"].split(":")[-1]))

    def test_cita_corta_y_rev_de_entrega_y_vigente(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d, cuerpo1="`MD-001` Rev 00.1 (vieja). MD-001 Rev 00 (entrega). MD-001 Rev vigente.")
            rs = hallazgos(V.verificar_proyecto(d), "cita_rev")
            self.assertEqual(len(rs), 1)          # solo la 00.1; «Rev 00» y «vigente» son válidas

    def test_filas_de_control_de_revisiones_no_cuentan(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d, cuerpo1="| 00.1 | 2026-10-08 | Corrige AB01-E-MD-001 Rev 00.1 |")
            self.assertEqual(hallazgos(V.verificar_proyecto(d), "cita_rev"), [])

    def test_gestion_se_omite_salvo_citas_todos(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d)
            escribir(d, "AUD.md", "# Auditoría\nSe auditó AB01-E-MC-001 Rev 00.1.\n")
            self.assertEqual(hallazgos(V.verificar_proyecto(d), "cita_rev"), [])
            self.assertEqual(len(hallazgos(V.verificar_proyecto(d, citas_todos=True), "cita_rev")), 1)


class TestMarcasEIds(unittest.TestCase):
    def test_conteo_de_marcas(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d, cuerpo1="[DEFINIR] [DEFINIR] [VERIFICAR] [PENDIENTE INF-001] "
                                     "`[SUPUESTO SUP-001]` [SUPUESTO SUP-002]")
            r = V.verificar_proyecto(d)
            m = r["marcas_por_documento"]["02/AB01-E-MC-001_Rev00.2.md"]
            self.assertEqual((m["DEFINIR"], m["VERIFICAR"], m["PENDIENTE INF"], m["SUPUESTO"], m["total"]),
                             (2, 1, 1, 2, 6))
            self.assertEqual(r["resumen"]["marcas_abiertas_total"], 6)

    def test_ids_inexistentes(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d, cuerpo1="Ver DEC-009, SUP-001, INF-007, REV-001, rfc-009 y DEC-001 a DEC-003.")
            r = V.verificar_proyecto(d)
            faltan = sorted(h["mensaje"].split()[0] for h in hallazgos(r, "id_inexistente"))
            # DEC-001 a DEC-003 se expande: DEC-003 no existe; REV-001 no existe en este mini-proyecto
            self.assertEqual(faltan, ["DEC-003", "DEC-009", "INF-007", "REV-001", "rfc-009"])
            self.assertEqual(r["resumen"]["ids_inexistentes"], 5)

    def test_riesgos_rie_se_validan_contra_el_registro(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d, cuerpo1="Riesgos RIE-001 y RIE-009; formato RIE-nnn.")
            escribir(d, "90-management/assumptions-and-decisions.md",
                     "# Registro\n\n| ID | Riesgo |\n|---|---|\n| RIE-001 | Falta dato del cliente |\n")
            faltan = [h["mensaje"].split()[0] for h in hallazgos(V.verificar_proyecto(d), "id_inexistente")]
            self.assertEqual(faltan, ["RIE-009"])

    def test_placeholders_no_son_ids(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d, cuerpo1="Formato DEC-nnn, rfc-nn e INF-xxx.")
            self.assertEqual(hallazgos(V.verificar_proyecto(d), "id_inexistente"), [])


class TestSalida(unittest.TestCase):
    def test_markdown_y_json_y_codigos_de_retorno(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d, cuerpo1="[DEFINIR]")
            md, js = os.path.join(d, "s.md"), os.path.join(d, "s.json")
            cmd = [sys.executable, "-B", os.path.join(AQUI, "document_verifier.py"), d]
            cp = subprocess.run(cmd + ["--md", md, "--json", js], capture_output=True, text=True)
            self.assertEqual(cp.returncode, 0, cp.stderr)
            with open(md, encoding="utf-8") as f:
                self.assertIn("No reemplaza la auditoría", f.read())
            with open(js, encoding="utf-8") as f:
                self.assertEqual(json.load(f)["resumen"]["errores"], 0)
            # con un error -> 1
            escribir(d, "02/AB01-E-MD-001_Rev00.2.md", doc("AB01-E-MD-001", "00.2", "Memoria", "DEC-099"))
            self.assertEqual(subprocess.run(cmd, capture_output=True, text=True).returncode, 1)
            # carpeta inexistente -> 2
            cp = subprocess.run([sys.executable, "-B", os.path.join(AQUI, "document_verifier.py"),
                                 os.path.join(d, "no_existe")], capture_output=True, text=True)
            self.assertEqual(cp.returncode, 2)

    def test_estricto_falla_con_avisos(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d)
            escribir(d, "02/AB01-E-PL-001_Rev00.1.md", doc("AB01-E-PL-001", "00.1", "Plano"))   # aviso: fuera de LME
            cmd = [sys.executable, "-B", os.path.join(AQUI, "document_verifier.py"), d]
            self.assertEqual(subprocess.run(cmd, capture_output=True, text=True).returncode, 0)
            self.assertEqual(subprocess.run(cmd + ["--estricto"], capture_output=True, text=True).returncode, 1)


class TestPliegoModular(unittest.TestCase):
    """El pliego (tipo PG) no tiene archivo con código: su código y revisión están en 00_Index_and_Control.md."""

    def _con_pliego(self, d, rev_indice):
        proyecto_base(d)
        lme = open(os.path.join(d, "90-management", "deliverables.md"), encoding="utf-8").read()
        lme += "| ENT-004 | AB01-G-PG-001 | Pliego técnico | Documentación | LIC | PG | SÍ | DRAFT | 00.2 | 2026-10-20 |\n"
        escribir(d, "90-management/deliverables.md", lme)
        escribir(d, "03_ENGINEERING/Technical_Specs/00_Index_and_Control.md",
                 f"# Índice\n\n| Campo | Valor |\n|---|---|\n| Código del pliego | `AB01-G-PG-001` |\n| Revisión | {rev_indice} |\n")

    def test_pliego_con_indice_no_genera_aviso_de_archivo_faltante(self):
        with tempfile.TemporaryDirectory() as d:
            self._con_pliego(d, "00.2")
            r = V.verificar_proyecto(d)
            self.assertEqual([h for h in r["hallazgos"] if "AB01-G-PG-001" in h["mensaje"]], [], r["hallazgos"])

    def test_pliego_con_revision_distinta_de_la_lme(self):
        with tempfile.TemporaryDirectory() as d:
            self._con_pliego(d, "00.1")
            rs = [h for h in V.verificar_proyecto(d)["hallazgos"] if "AB01-G-PG-001" in h["mensaje"]]
            self.assertEqual(len(rs), 1)
            self.assertEqual(rs[0]["severidad"], "ERROR")
            self.assertIn("Rev 00.1", rs[0]["mensaje"])


def formato(texto, **kw):
    """Hallazgos de formato Pandoc como {categoría: [(severidad, línea)]}."""
    out = {}
    for sev, cat, linea, _ in V.comprobar_formato_pandoc(texto, **kw):
        out.setdefault(cat, []).append((sev, linea))
    return out


class TestFormatoPandoc(unittest.TestCase):
    """RG-20: Markdown compatible con Pandoc (títulos sin numeración, viñetas con «-», una sola «#»)."""

    LIMPIO = ("---\ntitle: \"Memoria\"\nrevision: \"00.1\"\n---\n\n# Memoria de cálculo\n\n## Objetivo\n\n"
              "Texto con una lista:\n\n- **Término:** descripción.\n  - Subitem con dos espacios.\n- Otro.\n\n"
              "1. Primer paso\n2. Segundo paso\n\n### Detalle\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n"
              "Ver el capítulo Marco Normativo y la tabla Resumen de cargas.\n")

    def test_documento_correcto_sin_hallazgos(self):
        self.assertEqual(V.comprobar_formato_pandoc(self.LIMPIO), [])

    def test_titulo_numerado_es_error(self):
        casos = ["# 1. Alcance", "## 2.1 Criterios", "# 3) Normas", "## A. Datos", "# IV. Resultados",
                 "## 05.1 Sección", "# 05 — Requisitos", "# Capítulo 4 Ensayos", "##3. Sin espacio"]
        for c in casos:
            with self.subTest(c=c):
                r = formato(f"{c}\n\nTexto.\n")
                self.assertEqual(r.get("formato_titulo_numerado"), [("ERROR", 1)], r)

    def test_titulo_sin_numerar_no_es_error(self):
        for c in ("# Alcance", "## Criterios de diseño", "### 5G y redes", "## Parte A, documentos del paquete", "## Documentos del paquete (Parte A)"):
            with self.subTest(c=c):
                self.assertNotIn("formato_titulo_numerado", formato(f"{c}\n\nTexto.\n"))

    def test_vinetas_asterisco_o_mas_son_error(self):
        r = formato("# T\n\n* uno\n* **NEGRITA** dos\n\n+ tres\n")
        self.assertEqual(r["formato_vineta"], [("ERROR", 3), ("ERROR", 4), ("ERROR", 6)])

    def test_no_confunde_negrita_cursiva_ni_regla_horizontal(self):
        r = formato("# T\n\n**Negrita** al inicio\n\n*Cursiva* al inicio\n\n* * *\n\n---\n\n- ok\n")
        self.assertNotIn("formato_vineta", r)

    def test_codigo_y_comentarios_y_yaml_se_ignoran(self):
        txt = ("---\ntitle: \"# 1. No es título\"\nlista:\n  * x\n---\n\n# Doc\n\n```markdown\n# 1. Alcance\n* viñeta\n```\n\n"
               "<!--\n# 2. Comentario\n* viñeta\n-->\n\nTexto.\n")
        self.assertEqual(V.comprobar_formato_pandoc(txt), [])

    def test_mas_de_un_nivel_uno_es_aviso(self):
        r = formato("# Uno\n\ntexto\n\n# Dos\n")
        self.assertEqual(r["formato_h1_multiple"], [("AVISO", 5)])

    def test_salto_de_niveles_es_aviso(self):
        r = formato("# Doc\n\n## A\n\n#### Salta\n\n## B\n\n### C\n")
        self.assertEqual(r["formato_salto_nivel"], [("AVISO", 5)])
        self.assertNotIn("formato_salto_nivel", formato("## A\n\n### B\n\n## C\n"))     # empezar en `##` no es salto

    def test_referencias_numericas_son_aviso(self):
        txt = "# Doc\n\nVer sección 3.2 del documento.\n\nSegún el capítulo 4 y el apartado 2.1.\n\nVéase cap. 05.\n"
        r = formato(txt)
        self.assertEqual([x[1] for x in r["formato_referencia_numerica"]], [3, 5, 7])
        self.assertTrue(all(x[0] == "AVISO" for x in r["formato_referencia_numerica"]))

    def test_cita_a_archivo_del_framework_no_es_referencia_numerica(self):
        self.assertNotIn("formato_referencia_numerica",
                         formato("# Doc\n\nSegún `DOCUMENT_RULES.md`, sección 9, la revisión es 00.n.\n"))

    def test_referencias_numericas_se_pueden_omitir(self):
        txt = "# Doc\n\nVer sección 3.2.\n"
        self.assertNotIn("formato_referencia_numerica", formato(txt, referencias_numericas=False))
        self.assertNotIn("formato_referencia_numerica", formato(txt, omitir_lineas_ref={3}))

    def test_lista_sin_linea_en_blanco_es_aviso(self):
        r = formato("# Doc\n\nTexto previo:\n- uno\n- dos\n\nOtro texto\n1. paso\n")
        self.assertEqual(r["formato_lista_sin_blanco"], [("AVISO", 4), ("AVISO", 8)])

    def test_lista_tras_titulo_o_subitems_no_es_aviso(self):
        txt = "# Doc\n\n## Sec\n- uno\n  - sub\n- dos\n  continuación\n- tres\n"
        self.assertNotIn("formato_lista_sin_blanco", formato(txt))

    def test_tabuladores_son_aviso(self):
        r = formato("# Doc\n\nTexto\tcon tab\n")
        self.assertEqual(r["formato_tabulador"], [("AVISO", 3)])

    def test_integracion_proyecto_errores_y_avisos(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d, cuerpo1="## 2.1 Datos\n\n* viñeta mala\n\nVer sección 3.2.\n",
                          cuerpo2="# Segundo nivel uno\n")
            r = V.verificar_proyecto(d)
            self.assertEqual(len(hallazgos(r, "formato_titulo_numerado")), 1)
            self.assertEqual(hallazgos(r, "formato_titulo_numerado")[0]["severidad"], "ERROR")
            self.assertEqual(hallazgos(r, "formato_titulo_numerado")[0]["archivo"], "02/AB01-E-MC-001_Rev00.2.md:15")
            self.assertEqual(len(hallazgos(r, "formato_vineta")), 1)
            self.assertEqual(len(hallazgos(r, "formato_referencia_numerica")), 1)
            self.assertEqual(len(hallazgos(r, "formato_h1_multiple")), 1)       # el título del documento + el «#» extra
            self.assertGreaterEqual(r["resumen"]["errores"], 2)

    def test_archivos_del_framework_y_pliegos_no_se_verifican(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d)
            escribir(d, "CLAUDE.md", "# CLAUDE\n\n## 1. Objetivo\n\n* viñeta del framework\n")
            escribir(d, "90-management/audit-register.md", "# R\n\n## 1. Objetivo\n\n* v\n")
            escribir(d, "03_ENGINEERING/Technical_Specs/01_Scope.md", "# Alcance\n\n## 1.1 Algo\n\n* v\n")
            r = V.verificar_proyecto(d)
            self.assertEqual([h for h in r["hallazgos"] if h["categoria"].startswith("formato")], [], r["hallazgos"])
            # un acta del proyecto (no framework) sí se verifica
            escribir(d, "90-management/Governance/Communications/MINUTES-001_Meeting.md", "# Acta\n\n## 1. Temas\n")
            r = V.verificar_proyecto(d)
            self.assertEqual(len(hallazgos(r, "formato_titulo_numerado")), 1)
            self.assertIn("MINUTES-001_Meeting.md:3", hallazgos(r, "formato_titulo_numerado")[0]["archivo"])

    def test_revision_en_bloque_yaml(self):
        yaml_ok = ("---\ntitle: \"Balance\"\ncode: \"AB01-E-MC-001\"\nrevision: \"00.2\"\nstatus: \"DRAFT\"\ndate: \"2026-10-20\"\n---\n\n"
                   "# Balance\n\n## Control de revisiones\n\n| Rev. | Fecha | Descripción |\n|---|---|---|\n| 00.0 | 2026-10-08 | Inicial |\n| 00.2 | 2026-10-20 | Cambio rfc-002 |\n")
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d)
            escribir(d, "02/AB01-E-MC-001_Rev00.2.md", yaml_ok)
            r = V.verificar_proyecto(d)
            self.assertEqual(hallazgos(r, "revision"), [], r["hallazgos"])
            escribir(d, "02/AB01-E-MC-001_Rev00.2.md", yaml_ok.replace('revision: "00.2"', 'revision: "00.1"'))
            rs = hallazgos(V.verificar_proyecto(d), "revision")
            self.assertEqual(len(rs), 1)
            self.assertIn("dice 00.1", rs[0]["mensaje"])


class TestEsquemaDeRevisiones(unittest.TestCase):
    """Rev 00.0 / 00.n por rfc / 00 solo para el cliente / 01 as-built (DOCUMENT_RULES.md, sección 9)."""

    def test_filas_de_entrega_00_no_son_la_revision_vigente(self):
        txt = doc("AB01-E-MC-001", "00.2", "Balance").replace(
            "| 00.2 | 2026-10-20 | Cambio rfc-002 |\n",
            "| 00.2 | 2026-10-20 | Cambio rfc-002 |\n| 00 | 2026-10-25 | Entrega TR-001 |\n")
        self.assertEqual(V._cabecera(txt)[2], "00.2")
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d)
            escribir(d, "02/AB01-E-MC-001_Rev00.2.md", txt)
            r = V.verificar_proyecto(d)
            self.assertEqual(hallazgos(r, "revision"), [], r["hallazgos"])
            self.assertEqual(hallazgos(r, "rev_sin_rfc"), [])

    def test_fila_00_n_sin_su_rfc_es_aviso(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d)
            txt = doc("AB01-E-MC-001", "00.2", "Balance").replace("Cambio rfc-002", "Cambio sin origen")
            escribir(d, "02/AB01-E-MC-001_Rev00.2.md", txt)
            rs = hallazgos(V.verificar_proyecto(d), "rev_sin_rfc")
            self.assertEqual(len(rs), 1)
            self.assertIn("rfc-002", rs[0]["mensaje"])

    def test_revision_de_tres_digitos_con_su_comentario_es_valida(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d, rev1="00.0.2", rev2="00.2")
            escribir(d, "02/AB01-E-MC-001_Rev00.0.2.md", doc("AB01-E-MC-001", "00.0.2", "Balance"))
            os.remove(os.path.join(d, "02/AB01-E-MC-001_Rev00.2.md"))
            r = V.verificar_proyecto(d)
            self.assertEqual(hallazgos(r, "revision"), [], r["hallazgos"])
            self.assertEqual(hallazgos(r, "rev_sin_comentario"), [])
            self.assertEqual(hallazgos(r, "version_superada"), [])

    def test_fila_00_r_c_sin_comentario_es_aviso(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d, rev1="00.0.2", rev2="00.2")
            txt = doc("AB01-E-MC-001", "00.0.2", "Balance").replace("Cambio REV-002", "Cambio sin origen")
            escribir(d, "02/AB01-E-MC-001_Rev00.0.2.md", txt)
            os.remove(os.path.join(d, "02/AB01-E-MC-001_Rev00.2.md"))
            rs = hallazgos(V.verificar_proyecto(d), "rev_sin_comentario")
            self.assertEqual(len(rs), 1)
            self.assertIn("00.0.2", rs[0]["mensaje"])

    def test_avance_de_fase_cuenta_como_origen(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d, rev1="00.0.1", rev2="00.2")
            txt = doc("AB01-E-MC-001", "00.0.1", "Balance").replace("Cambio REV-001", "Avance de fase a ID")
            escribir(d, "02/AB01-E-MC-001_Rev00.0.1.md", txt)
            os.remove(os.path.join(d, "02/AB01-E-MC-001_Rev00.2.md"))
            self.assertEqual(hallazgos(V.verificar_proyecto(d), "rev_sin_comentario"), [])

    def test_sufijo_de_fase_en_archivo_cabecera_y_lme(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d, rev1="00.0.2.IB", rev2="00.2")
            os.remove(os.path.join(d, "02/AB01-E-MC-001_Rev00.2.md"))
            escribir(d, "02/AB01-E-MC-001_Rev00.0.2.IB.md", doc("AB01-E-MC-001", "00.0.2.IB", "Balance"))
            r = V.verificar_proyecto(d)
            self.assertEqual(hallazgos(r, "revision"), [], r["hallazgos"])
            self.assertEqual(hallazgos(r, "rev_sin_comentario"), [])

    def test_avance_de_fase_cambia_solo_el_sufijo(self):
        """00.0.2.IB -> 00.0.2.ID: no suma numeros y no exige REV-nnn ni rfc."""
        txt = doc("AB01-E-MC-001", "00.0.2.ID", "Balance").replace(
            "| 00.0.2.ID | 2026-10-20 | Cambio REV-002 |\n",
            "| 00.0.2.IB | 2026-10-20 | Cambio REV-002 |\n| 00.0.2.ID | 2026-11-20 | Avance de fase |\n")
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d, rev1="00.0.2.ID", rev2="00.2")
            os.remove(os.path.join(d, "02/AB01-E-MC-001_Rev00.2.md"))
            escribir(d, "02/AB01-E-MC-001_Rev00.0.2.ID.md", txt)
            r = V.verificar_proyecto(d)
            self.assertEqual(hallazgos(r, "revision"), [], r["hallazgos"])
            self.assertEqual(hallazgos(r, "rev_sin_comentario"), [])

    def test_clave_rev_con_sufijo_ordena_por_fase(self):
        revs = ["00.2.34.IC", "00.2.34.IB", "00.2.34.ID", "00.2.34.IE", "00.2.35.IB"]
        self.assertEqual(sorted(revs[::-1], key=V._clave_rev), revs)

    def test_clave_rev_ordena_tres_digitos(self):
        revs = ["00.0", "00.0.1", "00.0.10", "00.1", "00.1.2", "01"]
        self.assertEqual(sorted(revs, key=V._clave_rev), revs)

    def test_salto_de_00_0_a_00_2_es_valido(self):
        # la revisión sigue al número de la rfc: no hay 00.1 y no es un error
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d)
            r = V.verificar_proyecto(d)
            self.assertEqual(r["resumen"]["errores"], 0, r["hallazgos"])
            self.assertEqual(r["resumen"]["avisos"], 0, r["hallazgos"])

    def test_rev_00_en_editables_es_aviso(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d)
            escribir(d, "02/AB01-E-MD-001_Rev00.md", doc("AB01-E-MD-001", "00", "Memoria"))
            rs = hallazgos(V.verificar_proyecto(d), "rev_00_en_editables")
            self.assertEqual(len(rs), 1)
            self.assertIn("07_DELIVERABLES", rs[0]["mensaje"])

    def test_rev_00_en_entregables_no_se_verifica(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d)
            escribir(d, "07_DELIVERABLES/20261029_TR-001_Rev00/AB01-E-MD-001_Rev00.md", doc("AB01-E-MD-001", "00", "Memoria"))
            r = V.verificar_proyecto(d)
            self.assertEqual(hallazgos(r, "rev_00_en_editables"), [])
            self.assertEqual(r["resumen"]["documentos_con_codigo"], 2)

    def test_borrador_fuera_del_archivo_historico_es_aviso(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d)
            escribir(d, "02/AB01-E-MC-001_Rev00.2_draft-1.md", doc("AB01-E-MC-001", "00.2", "Balance"))
            r = V.verificar_proyecto(d)
            rs = hallazgos(r, "borrador_fuera_de_archivo")
            self.assertEqual(len(rs), 1)
            self.assertEqual(hallazgos(r, "version_superada"), [])        # el borrador no compite con la vigente
            self.assertEqual(r["resumen"]["documentos_con_codigo"], 2)

    def test_borrador_en_archivo_historico_se_omite(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d)
            escribir(d, "03_ENGINEERING/Archive/AB01-E-MC-001/AB01-E-MC-001_Rev00.2_draft-1.md",
                     doc("AB01-E-MC-001", "00.2", "Balance"))
            r = V.verificar_proyecto(d)
            self.assertEqual(hallazgos(r, "borrador_fuera_de_archivo"), [])
            self.assertEqual(r["resumen"]["avisos"], 0, r["hallazgos"])

    def test_as_built_rev_01_es_la_vigente(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d, rev1="01")
            escribir(d, "02/AB01-E-MC-001_Rev01.md", doc("AB01-E-MC-001", "01", "Balance"))
            os.remove(os.path.join(d, "02/AB01-E-MC-001_Rev00.2.md"))
            r = V.verificar_proyecto(d)
            self.assertEqual(r["documentos_vigentes"]["AB01-E-MC-001"], "01")
            self.assertEqual(hallazgos(r, "revision"), [], r["hallazgos"])

    def test_drawing_status_es_archivo_del_framework(self):
        self.assertIn("drawing-status.md", V.ARCHIVOS_FRAMEWORK)
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d)
            escribir(d, "drawing-status.md", "# DRAWING_STATUS\n\n## 1. Guía\n\n* viñeta\n")
            r = V.verificar_proyecto(d)
            self.assertEqual([h for h in r["hallazgos"] if h["categoria"].startswith("formato")], [])

    def test_archivos_de_arranque_son_del_framework(self):
        for n in ("starting-data.md", "project-scope.md", "project-charter.md"):
            self.assertIn(n, V.ARCHIVOS_FRAMEWORK)
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d)
            escribir(d, "starting-data.md", "# DATOS\n\n## 1. Identificación\n\n- [x] Electricidad\n")
            escribir(d, "project-scope.md", "# SCOPE\n\n## A. Alcance\n\n| ALD-001 | Eléctrico |\n")
            r = V.verificar_proyecto(d)
            self.assertEqual([h for h in r["hallazgos"] if h["categoria"].startswith("formato")], [])


    def test_archivos_de_gestion_en_carpetas_del_framework_no_se_verifican(self):
        """Los .md de gestión en 02_PROJECT / 90-management están exentos; en otra carpeta, no."""
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d)
            malo = "# X\n\n## 1. Identificación\n\n- [x] Electricidad\n"
            escribir(d, "02_PROJECT/starting-data.md", malo)
            escribir(d, "90-management/project-status.md", malo)
            r = V.verificar_proyecto(d)
            self.assertEqual([h for h in r["hallazgos"] if h["categoria"].startswith("formato")], [])
            escribir(d, "03_ENGINEERING/Lists/project-status.md", malo)
            r = V.verificar_proyecto(d)
            self.assertTrue([h for h in r["hallazgos"] if h["categoria"].startswith("formato")])


    def test_registros_generados_por_los_scripts_de_flujo_se_omiten(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d)
            malo = "# X\n\n## 1. Identificación\n\n- [x] algo\n"
            escribir(d, "90-management/ledger/EVENTS.md", malo)
            escribir(d, "06_RELEASED/RELEASE_ifa.md", malo)
            r = V.verificar_proyecto(d)
            self.assertEqual([h for h in r["hallazgos"] if h["categoria"].startswith("formato")], [])


class TestConfidencialidadEconomica(unittest.TestCase):
    """RG-21: cifras económicas del cliente no se plasman en el proyecto."""

    def test_cifra_con_moneda_es_error(self):
        for texto in ("El monto es $ 1.500.000.", "Presupuesto oficial USD 20.000.", "Cuesta 1500 pesos.",
                      "Total US$ 35,50", "Importe de 12.000 EUR."):
            with self.subTest(texto=texto):
                with tempfile.TemporaryDirectory() as d:
                    proyecto_base(d, cuerpo1=texto)
                    h = hallazgos(V.verificar_proyecto(d), "confidencialidad_economica")
                    self.assertEqual([x["severidad"] for x in h], ["ERROR"], h)

    def test_palabra_de_costo_con_cifra_grande_es_aviso(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d, cuerpo1="El presupuesto asignado ronda 250.000 según la carta.")
            h = hallazgos(V.verificar_proyecto(d), "confidencialidad_economica")
            self.assertEqual([x["severidad"] for x in h], ["AVISO"])

    def test_texto_tecnico_no_da_falsos_positivos(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d, cuerpo1="Plazo de 120 horas hábiles. Interruptor de 25 A, 380 V, 50 Hz. "
                                     "Sin precios ni presupuesto en este documento. Fecha 2026-10-07. "
                                     "Ver PAR-001 y el costo de PAR-002 según DEC-001.")
            self.assertEqual(hallazgos(V.verificar_proyecto(d), "confidencialidad_economica"), [])

    def test_excepcion_autorizada_con_dec_existente(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d, cuerpo1="Monto $ 1.500 [ECON-AUTORIZADO DEC-001]")
            self.assertEqual(hallazgos(V.verificar_proyecto(d), "confidencialidad_economica"), [])

    def test_excepcion_con_dec_inexistente_sigue_siendo_hallazgo(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d, cuerpo1="Monto $ 1.500 [ECON-AUTORIZADO DEC-099]")
            h = hallazgos(V.verificar_proyecto(d), "confidencialidad_economica")
            self.assertEqual(len(h), 1)
            self.assertIn("DEC-099", h[0]["mensaje"])

    def test_bloques_de_codigo_se_ignoran(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d, cuerpo1="```\nprecio = $ 1.500\n```")
            self.assertEqual(hallazgos(V.verificar_proyecto(d), "confidencialidad_economica"), [])

    def test_registro_de_entrada_se_revisa_y_los_archivos_del_framework_no(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d)
            escribir(d, "01-input/_INPUT_REGISTER.md", "| 1 | oferta | USD 20.000 |\n")
            escribir(d, "01-input/MINUTES-000_Initial_Request.md", "Presupuesto de $ 900.000\n")
            escribir(d, "01-input/01_CONTRACTS_AND_TENDERS/nota.md", "USD 5.000\n")   # original del usuario
            escribir(d, "COMMANDS.md", "Ejemplo: $ 1.500\n")                                      # framework
            h = hallazgos(V.verificar_proyecto(d), "confidencialidad_economica")
            archivos = sorted(x["archivo"].split(":")[0] for x in h)
            self.assertEqual(archivos, ["01-input/MINUTES-000_Initial_Request.md",
                                        "01-input/_INPUT_REGISTER.md"])

    def test_resumen_cuenta_los_hallazgos(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d, cuerpo1="Monto $ 1.500.")
            self.assertEqual(V.verificar_proyecto(d)["resumen"]["hallazgos_confidencialidad"], 1)


class TestIdsDeDatosMaestros(unittest.TestCase):
    """PAR, ALD, CAC y NOR citados deben existir en algún registro."""

    def test_par_inexistente(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d, cuerpo1="Tensión según PAR-002 y ALD-004.")
            faltan = sorted(h["mensaje"].split()[0] for h in hallazgos(V.verificar_proyecto(d), "id_inexistente"))
            self.assertEqual(faltan, ["ALD-004", "PAR-002"])

    def test_par_existente(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d, cuerpo1="Tensión según PAR-001, norma NOR-001 y CAC-001.")
            escribir(d, "project-information.md", INFO + "\n| PAR-001 | Tensión | 380 |\n| NOR-001 | IEC | 2020 |\n| CAC-001 | FAT | |\n")
            self.assertEqual(hallazgos(V.verificar_proyecto(d), "id_inexistente"), [])

    def test_ejemplos_del_framework_no_son_ids(self):
        with tempfile.TemporaryDirectory() as d:
            proyecto_base(d, cuerpo1="Ejemplo EJ-PAR-001 y PAR-nnn.")
            self.assertEqual(hallazgos(V.verificar_proyecto(d), "id_inexistente"), [])


if __name__ == "__main__":
    unittest.main()
