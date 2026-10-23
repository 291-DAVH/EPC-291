"""Pruebas de specification_verifier.py (CAL-011). Crean mini-pliegos en un directorio temporal."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

from epc_documents import specification_verifier as V

AQUI = os.path.dirname(os.path.abspath(__file__))
COD = "AB01-G-PG-001"

# Un texto propio (distinto) por capítulo, para que el pliego base no dispare la comprobación de duplicados.
CUERPOS = {
    1: "Se ejecutarán la ampliación del tablero principal, el tendido de alimentadores y el suministro de los equipos de maniobra indicados en el listado de alcance del proyecto.",
    2: "La planta actual funciona con un único transformador y una sala de celdas antigua, y el proyecto incorpora una segunda alimentación para mejorar la continuidad del servicio.",
    3: "Se adoptan las normas de producto y de instalación registradas en la línea base, con las ediciones y los reglamentos locales que rigen sobre la obra y su puesta en servicio.",
    4: "El Contratista deberá coordinar los cortes con la operación del cliente, proteger las instalaciones en servicio y planificar el montaje por etapas sin interferir con la producción.",
    5: "La instalación deberá mantener la selectividad entre protecciones y la solución deberá admitir una ampliación futura del veinte por ciento sin reemplazar equipos principales.",
    6: "Se verificarán la continuidad de los conductores, la resistencia de aislación y los ajustes de las protecciones, comparando cada medición con los valores de aceptación acordados.",
    7: "Antes de energizar se comprueba el montaje mecánico, el apriete de conexiones, la identificación de cables y la existencia de los certificados de los materiales instalados.",
    8: "Se validan las secuencias de transferencia, las alarmas hacia el sistema de control y los enclavamientos entre tableros, operando el conjunto con carga representativa.",
    9: "Se entregarán los planos conformes a obra, los diagramas unifilares actualizados, las memorias de cálculo, los protocolos de ensayo firmados y los manuales de los equipos.",
    10: "El Contratista deberá desarrollar la ingeniería de detalle, verificar las medidas en campo, compatibilizar las disciplinas y responder por la calidad y las garantías de los trabajos.",
}


def escribir(carpeta, nombre, texto):
    p = os.path.join(carpeta, nombre)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(texto)
    return p


def indice(codigo=COD, rev="00.1", yaml=True):
    """Índice con bloque YAML de portada (estándar, RG-20) o, con yaml=False, con la tabla Campo/Valor."""
    if yaml:
        cab = (f"---\ntitle: \"Pliego técnico\"\nsubtitle: \"Proyecto AB01\"\ncode: \"{codigo}\"\nrevision: \"{rev}\"\n"
               "status: \"DRAFT\"\ndate: \"2026-10-07\"\n---\n\n# Índice y control\n\n")
    else:
        cab = (f"# Índice y control\n\n| Campo | Valor |\n|---|---|\n| Código del pliego | `{codigo}` |\n"
               f"| Revisión | {rev} |\n| Estado | DRAFT |\n\n")
    return cab + f"## Control de revisiones\n\n| Rev. | Fecha |\n|---|---|\n| {rev} | 2026-10-07 |\n"


def capitulo(num, cuerpo=None, codigo=COD, rev="00.1", pregunta=True, pendientes=True, estado="DRAFT", extra=""):
    nombre = V.CAPITULOS_ESTANDAR.get(num, f"Anexo_{num}")
    t = [f"# {nombre.replace('_', ' ')}", "", "| Campo | Valor |", "|---|---|"]
    if codigo:
        t.append(f"| Pliego | `{codigo}` |")
    t.append(f"| Capítulo | {num:02d} — {nombre.replace('_', ' ')} |")
    if rev:
        t.append(f"| Revisión | {rev} |")
    t += [f"| Estado | {estado} |", ""]
    if pregunta:
        t += ["> **Pregunta que responde:** ¿Pregunta del capítulo?", ""]
    t += ["## Desarrollo", "", cuerpo if cuerpo is not None else CUERPOS.get(num, "Texto propio del capítulo adicional sin relación con otros capítulos del pliego técnico."), ""]
    if extra:
        t += [extra, ""]
    if pendientes:
        t += ["## Pendientes y supuestos", "", "Ninguno.", ""]
    return "\n".join(t)


def pliego(d, cambios=None):
    """Pliego base correcto de 10 capítulos. `cambios` = {número: texto de capítulo o None para omitirlo}."""
    cambios = cambios or {}
    escribir(d, V.INDICE, indice())
    for n, nombre in V.CAPITULOS_ESTANDAR.items():
        txt = cambios.get(n, capitulo(n))
        if txt is not None:
            escribir(d, f"{n:02d}_{nombre}.md", txt)


def cats(res, cat, sev=None):
    return [h for h in res["hallazgos"] if h["categoria"] == cat and (sev is None or h["severidad"] == sev)]


class TestPliegoLimpio(unittest.TestCase):
    def test_pliego_base_sin_hallazgos(self):
        with tempfile.TemporaryDirectory() as d:
            pliego(d)
            r = V.verificar_pliego(d)
            self.assertEqual(r["resumen"]["errores"], 0, r["hallazgos"])
            self.assertEqual(r["resumen"]["avisos"], 0, r["hallazgos"])
            self.assertEqual(r["resumen"]["capitulos"], 10)
            self.assertEqual(r["codigo_pliego"], COD)
            self.assertEqual(r["revision_pliego"], "00.1")


class TestNumeracion(unittest.TestCase):
    def test_falta_indice(self):
        with tempfile.TemporaryDirectory() as d:
            pliego(d)
            os.remove(os.path.join(d, V.INDICE))
            self.assertEqual(len(cats(V.verificar_pliego(d), "estructura", "ERROR")), 1)

    def test_salto_de_numeracion(self):
        with tempfile.TemporaryDirectory() as d:
            pliego(d)
            os.remove(os.path.join(d, "05_Design_Requirements.md"))
            rs = cats(V.verificar_pliego(d), "numeracion", "ERROR")
            self.assertEqual(len(rs), 1)
            self.assertIn("05", rs[0]["mensaje"])

    def test_numero_duplicado(self):
        with tempfile.TemporaryDirectory() as d:
            pliego(d)
            escribir(d, "03_Other_Standard.md", capitulo(3, cuerpo="Texto alternativo completamente distinto que no se parece a ningún otro párrafo del pliego."))
            rs = [h for h in cats(V.verificar_pliego(d), "numeracion", "ERROR") if "duplicado" in h["mensaje"]]
            self.assertEqual(len(rs), 1)

    def test_faltan_capitulos_estandar_finales(self):
        with tempfile.TemporaryDirectory() as d:
            pliego(d)
            for fn in ("08_Commissioning.md", "09_Technical_Documentation.md", "10_Contractor_Responsibilities.md"):
                os.remove(os.path.join(d, fn))
            self.assertEqual(len(cats(V.verificar_pliego(d), "numeracion", "ERROR")), 3)

    def test_capitulos_adicionales_contiguos_y_con_salto(self):
        with tempfile.TemporaryDirectory() as d:
            pliego(d)
            escribir(d, "11_Data_Sheet.md", capitulo(11))
            self.assertEqual(V.verificar_pliego(d)["resumen"]["errores"], 0)
            escribir(d, "13_Final_Annex.md", capitulo(13, cuerpo="Contenido del anexo final con frases y datos que no se repiten en ninguna otra parte del pliego."))
            rs = cats(V.verificar_pliego(d), "numeracion", "ERROR")
            self.assertEqual(len(rs), 1)
            self.assertIn("12", rs[0]["mensaje"])

    def test_nombre_no_estandar_y_archivo_fuera_de_patron(self):
        with tempfile.TemporaryDirectory() as d:
            pliego(d)
            os.rename(os.path.join(d, "07_Precommissioning.md"), os.path.join(d, "07_Pre_Commissioning.md"))
            escribir(d, "Notas sueltas.md", "borrador")
            r = V.verificar_pliego(d)
            self.assertEqual(r["resumen"]["errores"], 0, r["hallazgos"])
            self.assertEqual(len(cats(r, "numeracion", "AVISO")), 1)
            self.assertEqual(len(cats(r, "estructura", "AVISO")), 1)


class TestEncabezado(unittest.TestCase):
    def test_sin_codigo_sin_revision_sin_pregunta(self):
        with tempfile.TemporaryDirectory() as d:
            pliego(d, {3: None})
            escribir(d, "03_Regulatory_Framework.md", capitulo(3, codigo=None, rev=None, pregunta=False))
            rs = cats(V.verificar_pliego(d), "encabezado", "ERROR")
            msgs = " | ".join(h["mensaje"] for h in rs)
            self.assertEqual(len(rs), 3, msgs)
            self.assertIn("código", msgs)
            self.assertIn("revisión", msgs)
            self.assertIn("Pregunta que responde", msgs)

    def test_codigo_y_revision_distintos_del_indice(self):
        with tempfile.TemporaryDirectory() as d:
            pliego(d)
            escribir(d, "06_Tests_and_Inspections.md", capitulo(6, codigo="AB01-G-PG-002", rev="00.2"))
            rs = cats(V.verificar_pliego(d), "encabezado", "ERROR")
            self.assertEqual(len(rs), 2)
            self.assertTrue(all(h["archivo"] == "06_Tests_and_Inspections.md" for h in rs))
            self.assertTrue(all(h["linea"] for h in rs))

    def test_falta_pendientes_y_supuestos(self):
        with tempfile.TemporaryDirectory() as d:
            pliego(d, {9: capitulo(9, pendientes=False)})
            rs = cats(V.verificar_pliego(d), "estructura", "AVISO")
            self.assertEqual(len(rs), 1)
            self.assertEqual(rs[0]["archivo"], "09_Technical_Documentation.md")


class TestObligaciones(unittest.TestCase):
    def test_obligacion_en_capitulos_prohibidos_es_error_con_linea(self):
        with tempfile.TemporaryDirectory() as d:
            frases = {1: "El Contratista deberá ejecutar todo.", 2: "Será responsabilidad del cliente y del Contratista.",
                      3: "La Ingeniería de Detalle deberá verificar las normas.", 5: "Los trabajos quedan a cargo del Contratista.",
                      9: "El Contratista deberá presentar los planos."}
            pliego(d, {n: capitulo(n, extra=f) for n, f in frases.items()})
            rs = cats(V.verificar_pliego(d), "obligacion", "ERROR")
            self.assertEqual(sorted(h["archivo"][:2] for h in rs), ["01", "02", "03", "05", "09"])
            self.assertTrue(all(isinstance(h["linea"], int) for h in rs))

    def test_obligacion_permitida_en_04_y_10(self):
        with tempfile.TemporaryDirectory() as d:
            pliego(d)   # 04 y 10 ya contienen «El Contratista deberá»
            r = V.verificar_pliego(d)
            self.assertEqual(cats(r, "obligacion"), [])

    def test_obligacion_en_06_07_08_es_aviso(self):
        with tempfile.TemporaryDirectory() as d:
            pliego(d, {n: capitulo(n, extra="El Contratista deberá registrar cada medición.") for n in (6, 7, 8)})
            r = V.verificar_pliego(d)
            self.assertEqual(len(cats(r, "obligacion", "AVISO")), 3)
            self.assertEqual(r["resumen"]["errores"], 0)

    def test_cap05_sujeto_de_proceso_es_aviso_sin_duplicar_el_error(self):
        with tempfile.TemporaryDirectory() as d:
            pliego(d, {5: capitulo(5, extra="La Ingeniería definirá los esquemas.\nEl Contratista deberá dimensionar los cables.")})
            r = V.verificar_pliego(d)
            self.assertEqual(len(cats(r, "sujeto", "AVISO")), 1)
            self.assertEqual(len(cats(r, "obligacion", "ERROR")), 1)

    def test_bloques_de_codigo_se_ignoran(self):
        with tempfile.TemporaryDirectory() as d:
            pliego(d, {2: capitulo(2, extra="```text\nEl Contratista deberá hacer todo\n```")})
            self.assertEqual(cats(V.verificar_pliego(d), "obligacion"), [])


class TestNormativaYDuplicados(unittest.TestCase):
    def test_normativa_repetida_fuera_del_03(self):
        with tempfile.TemporaryDirectory() as d:
            extra = "El tablero cumplirá según IEC 61439 y según la norma local.\nSe aplica la normativa vigente y de acuerdo con la reglamentación."
            pliego(d, {5: capitulo(5, extra=extra), 3: capitulo(3, extra=extra)})
            rs = cats(V.verificar_pliego(d), "normativa", "AVISO")
            self.assertEqual(len(rs), 1)
            self.assertEqual(rs[0]["archivo"], "05_Design_Requirements.md")
            self.assertIn("4 referencia", rs[0]["mensaje"])

    def test_parrafos_casi_duplicados_entre_capitulos(self):
        with tempfile.TemporaryDirectory() as d:
            igual = "La alimentación de emergencia deberá mantener los servicios esenciales de la planta durante la falla de la red principal por al menos dos horas continuas."
            pliego(d, {1: capitulo(1, extra=igual), 5: capitulo(5, extra=igual.replace("dos horas", "dos horas"))})
            rs = cats(V.verificar_pliego(d), "duplicado", "AVISO")
            self.assertEqual(len(rs), 1)
            self.assertEqual(rs[0]["archivo"], "05_Design_Requirements.md")
            self.assertIn("01_Scope.md", rs[0]["mensaje"])

    def test_duplicado_en_el_mismo_capitulo_o_corto_no_se_marca(self):
        with tempfile.TemporaryDirectory() as d:
            largo = "La alimentación de emergencia deberá mantener los servicios esenciales de la planta durante la falla de la red principal por al menos dos horas continuas."
            corto = "Se instalará un tablero nuevo."
            pliego(d, {1: capitulo(1, extra=largo + "\n\n" + largo), 2: capitulo(2, extra=corto), 5: capitulo(5, extra=corto)})
            self.assertEqual(cats(V.verificar_pliego(d), "duplicado"), [])


class TestVacioNoAplicaYComercial(unittest.TestCase):
    def test_capitulo_vacio_o_solo_plantilla_y_marcas(self):
        with tempfile.TemporaryDirectory() as d:
            plantilla = "<!-- guía interna -->\n`[DEFINIR]` — capítulo sin redactar\n\n- [VERIFICAR] dato dudoso\n- [DEFINIR] otro dato"
            pliego(d, {8: capitulo(8, cuerpo=plantilla)})
            r = V.verificar_pliego(d)
            self.assertEqual(len(cats(r, "vacio", "AVISO")), 1)
            c8 = next(c for c in r["capitulos"] if c["numero"] == 8)
            self.assertEqual(c8["marcas"], {"DEFINIR": 2, "VERIFICAR": 1})
            self.assertEqual(r["resumen"]["marcas_definir"], 2)
            self.assertEqual(r["resumen"]["errores"], 0)

    def test_no_aplica_sin_dec_es_error_y_con_dec_es_correcto(self):
        with tempfile.TemporaryDirectory() as d:
            pliego(d, {7: capitulo(7, cuerpo="No aplica a este proyecto (DEC-nnn).")})
            rs = cats(V.verificar_pliego(d), "no_aplica", "ERROR")
            self.assertEqual(len(rs), 1)
            self.assertIsInstance(rs[0]["linea"], int)
            pliego(d, {7: capitulo(7, cuerpo="No aplica a este proyecto (DEC-012).")})
            r = V.verificar_pliego(d)
            self.assertEqual(cats(r, "no_aplica"), [])
            self.assertEqual(cats(r, "vacio"), [])

    def test_precios_y_condiciones_comerciales(self):
        with tempfile.TemporaryDirectory() as d:
            pliego(d, {1: capitulo(1, extra="El precio unitario es de $ 1200 por equipo."),
                         4: capitulo(4, extra="La forma de pago será mensual en USD.\nEl Contratista deberá coordinar los cortes con la operación.")})
            rs = cats(V.verificar_pliego(d), "comercial", "AVISO")
            self.assertEqual(sorted(h["archivo"][:2] for h in rs), ["01", "04"])
            self.assertTrue(all(h["linea"] for h in rs))


class TestReferenciasAdelante(unittest.TestCase):
    def test_referencia_hacia_adelante_si_hacia_atras_no(self):
        with tempfile.TemporaryDirectory() as d:
            pliego(d, {4: capitulo(4, extra="Las responsabilidades se detallan en el capítulo 10 y las normas en el capítulo 03."),
                         6: capitulo(6, extra="Los criterios de diseño están en el cap. 5.")})
            rs = cats(V.verificar_pliego(d), "referencia_adelante", "AVISO")
            self.assertEqual(len(rs), 1)
            self.assertEqual(rs[0]["archivo"], "04_General_Execution_Conditions.md")
            self.assertIn("10", rs[0]["mensaje"])


class TestFormatoPandoc(unittest.TestCase):
    """RG-20: títulos sin numeración, viñetas con «-», un solo «#» por capítulo, referencias por nombre."""

    def test_pliego_base_cumple_el_formato(self):
        with tempfile.TemporaryDirectory() as d:
            pliego(d)
            r = V.verificar_pliego(d)
            self.assertEqual([h for h in r["hallazgos"] if h["categoria"].startswith("formato")], [])

    def test_indice_con_tabla_en_lugar_de_yaml_tambien_vale(self):
        with tempfile.TemporaryDirectory() as d:
            pliego(d)
            escribir(d, V.INDICE, indice(yaml=False))
            r = V.verificar_pliego(d)
            self.assertEqual(r["resumen"]["errores"], 0, r["hallazgos"])
            self.assertEqual(r["codigo_pliego"], COD)
            self.assertEqual(r["revision_pliego"], "00.1")

    def test_indice_yaml_con_revision_distinta_en_un_capitulo(self):
        with tempfile.TemporaryDirectory() as d:
            pliego(d, {3: capitulo(3, rev="00.2")})
            rs = cats(V.verificar_pliego(d), "encabezado", "ERROR")
            self.assertEqual(len(rs), 1)
            self.assertIn("00.2", rs[0]["mensaje"])

    def test_titulos_numerados_son_error(self):
        with tempfile.TemporaryDirectory() as d:
            num = capitulo(2).replace("# Descriptive Report", "# 02 — Descriptive Report").replace("## Desarrollo", "## 02.1 Desarrollo")
            pliego(d, {2: num, 5: capitulo(5).replace("## Desarrollo", "## 1. Desarrollo")})
            rs = cats(V.verificar_pliego(d), "formato_titulo_numerado", "ERROR")
            self.assertEqual(sorted((h["archivo"][:2], h["linea"]) for h in rs), [("02", 1), ("02", 12), ("05", 12)])
            self.assertEqual(V.verificar_pliego(d)["resumen"]["errores"], 3)

    def test_vinetas_con_asterisco_o_mas_son_error(self):
        with tempfile.TemporaryDirectory() as d:
            pliego(d, {6: capitulo(6, extra="Controles previstos:\n\n* **Continuidad** de conductores\n+ Aislación\n- Viñeta correcta")})
            rs = cats(V.verificar_pliego(d), "formato_vineta", "ERROR")
            self.assertEqual(len(rs), 2)
            self.assertTrue(all(h["archivo"].startswith("06") for h in rs))

    def test_varios_h1_salto_de_nivel_y_lista_sin_blanco_son_aviso(self):
        with tempfile.TemporaryDirectory() as d:
            extra = "# Otro título\n\n#### Salto\n\nLos ensayos son:\n- uno\n- dos"
            pliego(d, {6: capitulo(6, extra=extra)})
            r = V.verificar_pliego(d)
            for cat in ("formato_h1_multiple", "formato_salto_nivel", "formato_lista_sin_blanco"):
                self.assertEqual(len(cats(r, cat, "AVISO")), 1, cat)
            self.assertEqual(r["resumen"]["errores"], 0)

    def test_referencias_numericas_son_aviso_y_las_adelante_no_se_duplican(self):
        with tempfile.TemporaryDirectory() as d:
            pliego(d, {4: capitulo(4, extra="Ver la sección 3.2 del documento.\n\nLas responsabilidades están en el capítulo 10."),
                         6: capitulo(6, extra="Según el apartado 2.1 y el capítulo 05.")})
            r = V.verificar_pliego(d)
            n4 = [h for h in cats(r, "formato_referencia_numerica") if h["archivo"].startswith("04")]
            n6 = [h for h in cats(r, "formato_referencia_numerica") if h["archivo"].startswith("06")]
            self.assertEqual(len(n4), 1)             # la línea del «capítulo 10» ya es una referencia hacia adelante: no se avisa dos veces
            self.assertEqual(len(cats(r, "referencia_adelante")), 1)
            self.assertEqual(len(n6), 1)

    def test_referencia_hacia_adelante_por_nombre(self):
        with tempfile.TemporaryDirectory() as d:
            pliego(d, {4: capitulo(4, extra="Las obligaciones se detallan en el capítulo Responsabilidades del Contratista y las normas en el capítulo Marco Normativo."),
                         8: capitulo(8, extra="Ver el capítulo «Alcance» y el capítulo Commissioning.")})
            rs = cats(V.verificar_pliego(d), "referencia_adelante", "AVISO")
            self.assertEqual(len(rs), 1)
            self.assertEqual(rs[0]["archivo"], "04_General_Execution_Conditions.md")
            self.assertIn("Responsabilidades del Contratista", rs[0]["mensaje"])
            self.assertEqual(cats(V.verificar_pliego(d), "formato_referencia_numerica"), [])

    def test_formato_del_indice_se_verifica(self):
        with tempfile.TemporaryDirectory() as d:
            pliego(d)
            escribir(d, V.INDICE, indice().replace("## Control de revisiones", "## 3. Control de revisiones"))
            rs = cats(V.verificar_pliego(d), "formato_titulo_numerado", "ERROR")
            self.assertEqual([h["archivo"] for h in rs], [V.INDICE])

    def test_yaml_y_codigo_no_generan_hallazgos_de_formato(self):
        with tempfile.TemporaryDirectory() as d:
            extra = "Ejemplo de plantilla:\n\n```markdown\n# 1. Alcance\n* viñeta\n```"
            pliego(d, {6: capitulo(6, extra=extra)})
            self.assertEqual([h for h in V.verificar_pliego(d)["hallazgos"] if h["categoria"].startswith("formato")], [])


class TestSalidasYCLI(unittest.TestCase):
    def _cli(self, *args):
        return subprocess.run([sys.executable, "-B", "-m", "epc_documents.specification_verifier", *args],
                              capture_output=True, text=True)

    def test_retornos_y_archivos_de_salida(self):
        with tempfile.TemporaryDirectory() as d:
            carpeta = os.path.join(d, "Technical_Specs")
            os.makedirs(carpeta)
            pliego(carpeta)
            md, js = os.path.join(d, "output.md"), os.path.join(d, "output.json")
            cp = self._cli(carpeta, "--md", md, "--json", js)
            self.assertEqual(cp.returncode, 0, cp.stderr)
            with open(md, encoding="utf-8") as f:
                texto = f.read()
            self.assertIn("No reemplaza el juicio del auditor", texto)
            self.assertIn("05_Design_Requirements.md", texto)
            with open(js, encoding="utf-8") as f:
                self.assertEqual(json.load(f)["resumen"]["errores"], 0)
            os.remove(os.path.join(carpeta, "02_Descriptive_Report.md"))
            self.assertEqual(self._cli(carpeta).returncode, 1)

    def test_carpeta_inexistente_y_estricto(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(self._cli(os.path.join(d, "no_existe")).returncode, 2)
            pliego(d, {1: capitulo(1, extra="El precio es fijo.")})   # solo AVISO
            self.assertEqual(self._cli(d).returncode, 0)
            self.assertEqual(self._cli(d, "--estricto").returncode, 1)

    def test_markdown_lista_hallazgos_con_linea(self):
        with tempfile.TemporaryDirectory() as d:
            pliego(d, {2: capitulo(2, extra="El Contratista deberá hacerlo.")})
            md = V.generar_markdown(V.verificar_pliego(d))
            self.assertIn("| ERROR | obligacion | `02_Descriptive_Report.md` |", md)


if __name__ == "__main__":
    unittest.main()
