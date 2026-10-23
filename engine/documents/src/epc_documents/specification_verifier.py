#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CAL-011 · specification_verifier — Autocontrol mecánico de la redacción de un pliego modular.

ESTADO: BORRADOR — pendiente de validación por el usuario.

ES UNA AYUDA DE AUTOCONTROL: NO REEMPLAZA EL JUICIO DEL AUDITOR (project-audit.md, A4-13). Las comprobaciones
son heurísticas (frases y patrones de texto): pueden dar falsos positivos y no pueden decidir si un texto
responde a otra pregunta distinta de la del capítulo; eso lo juzga el redactor y, después, el auditor.

QUÉ ES UN PLIEGO MODULAR (TECHNICAL_SPECIFICATIONS_GUIDE.md)
    Una carpeta (`03_ENGINEERING/Technical_Specs/`) con `00_Index_and_Control.md` y un archivo Markdown por capítulo,
    `NN_Nombre.md`, numerados desde 01 sin saltos:
        01_Scope  02_Descriptive_Report  03_Regulatory_Framework  04_General_Execution_Conditions
        05_Design_Requirements  06_Tests_and_Inspections  07_Precommissioning  08_Commissioning
        09_Technical_Documentation  10_Contractor_Responsibilities   (y 11, 12… adicionales al final)

COMPROBACIONES (por capítulo y número de línea; nivel ERROR o AVISO)
    (a) Patrón `NN_Nombre.md`; numeración contigua desde 01 (ERROR por salto, duplicado o capítulo estándar
        faltante); presencia de `00_Index_and_Control.md` (ERROR); nombre distinto del estándar (AVISO);
        archivo .md fuera del patrón (AVISO).
    (b) Encabezado con código del pliego (tipo PG) y revisión, y línea «Pregunta que responde» (ERROR si
        faltan); mismo código y revisión en todos los capítulos y en el índice (ERROR si difieren);
        sección «Pendientes y supuestos» (AVISO si falta).
    (c) Frases de obligación del Contratista («El Contratista deberá», «Será responsabilidad», «La Ingeniería
        de Detalle deberá», «a cargo del Contratista»): ERROR en los capítulos 01, 02, 03, 05 y 09; AVISO en
        06, 07 y 08; permitidas en 04 y 10.
    (d) Capítulo 05: la redacción debe tener como sujeto el resultado (la instalación, la solución, el
        sistema); AVISO si aparece «El Contratista» o «La Ingeniería» en líneas que (c) no marcó ya.
    (e) Referencias normativas repetidas fuera del capítulo 03 («según la norma», «según IEC/IRAM/AEA/NFPA/
        EN/ISO/ASTM/IEEE/NEC», «normativa vigente», «de acuerdo con la norma / reglamentación»): AVISO por
        capítulo, con conteo y líneas. Se cita el `NOR-nnn`; la norma se define solo en el 03.
    (f) Párrafos casi duplicados entre capítulos distintos (similitud de conjunto de palabras >= 0,8, párrafos
        de >= 12 palabras): AVISO.
    (g) Capítulos vacíos o con solo la plantilla (AVISO); marcas abiertas `[DEFINIR]` / `[VERIFICAR]` contadas
        por capítulo (informativo, no es un hallazgo).
    (h) Precios o condiciones comerciales (moneda, «precio», «$», «USD», «forma de pago»…): AVISO (RG-05).
    (i) Capítulo «No aplica a este proyecto» sin una `DEC-nnn` citada: ERROR.
    (j) Referencias hacia adelante («capítulo 07» o «capítulo Commissioning» escrito en el 04): AVISO.
    (k) Formato Markdown compatible con Pandoc (DOCUMENT_RULES.md, RG-20), en cada capítulo y en el índice
        (misma función que CAL-010, `comprobar_formato_pandoc`): título con numeración manual
        (`# 1. Alcance`, `## 04.1 Planificación`, `# 05 — Requisitos`) = ERROR; viñetas `*` o `+` = ERROR;
        más de un `#` de nivel 1, salto de niveles de título, referencias numéricas («sección 3.2»,
        «capítulo 4», «apartado 2.1») y lista sin línea en blanco previa = AVISO. Un capítulo lleva un solo `#`
        (su nombre) y sus secciones son `##` sin número; se cita por nombre («ver el capítulo Marco Normativo»).
        El encabezado del índice puede ser un bloque YAML (`code`, `revision`, `status`…) o la tabla Campo/Valor.

QUÉ NO HACE
    No valida contenido técnico, unidades ni datos de la línea base; no sigue enlaces; ignora los bloques de
    código (``` ... ```) y los comentarios HTML. No revisa la carpeta `Annexes/`.

SALIDA Y CÓDIGO DE RETORNO
    Markdown (`--md`, o salida estándar) y JSON (`--json`). Retorno 0 si no hay hallazgos ERROR (los AVISO no
    fallan, salvo `--estricto`); 1 si los hay; 2 si la carpeta no existe.

USO (desde la raíz del proyecto)
    python3 -B 98_LIBRARY/calculations/specification_verifier.py <carpeta_Technical_Specs> [--md output.md] [--json output.json]
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict

from epc_documents.document_verifier import comprobar_formato_pandoc     # CAL-010: misma función de formato (RG-20)

__version__ = "0.2.0"

CAPITULOS_ESTANDAR = {
    1: "Scope",
    2: "Descriptive_Report",
    3: "Regulatory_Framework",
    4: "General_Execution_Conditions",
    5: "Design_Requirements",
    6: "Tests_and_Inspections",
    7: "Precommissioning",
    8: "Commissioning",
    9: "Technical_Documentation",
    10: "Contractor_Responsibilities",
}
NOMBRES_VISIBLES = {          # nombre con el que se cita un capítulo en el texto («ver el capítulo Marco Normativo»)
    1: "Alcance", 2: "Memoria Descriptiva", 3: "Marco Normativo", 4: "Condiciones Generales de Ejecución",
    5: "Requisitos de Diseño", 6: "Ensayos e Inspecciones", 7: "Precommissioning", 8: "Commissioning",
    9: "Documentación Técnica", 10: "Responsabilidades del Contratista",
}
INDICE = "00_Index_and_Control.md"
CAP_ERROR = {1, 2, 3, 5, 9}      # frases de obligación del Contratista: ERROR
CAP_AVISO = {6, 7, 8}            # AVISO (4 y 10 las admiten)
UMBRAL_SIMILITUD = 0.8
MIN_PALABRAS_PARRAFO = 12
MIN_PALABRAS_CONTENIDO = 15

CODIGO = r"[A-Z][A-Z0-9]{1,7}-[A-Z]{1,2}-[A-Z]{2}-\d{3}"
RE_CAP = re.compile(r"^(\d{2})_([A-Za-z0-9]+(?:_[A-Za-z0-9]+)*)\.md$")
RE_CODIGO = re.compile(r"(?<![A-Za-z0-9-])" + CODIGO + r"(?![A-Za-z0-9-])")
RE_REV_FILA = re.compile(r"^\|\s*Revisi[oó]n\s*\|\s*`?(\d{2}(?:\.\d+){0,2}(?:\.(?:IC|IB|ID|IE))?)`?\s*\|", re.IGNORECASE)
RE_ESTADO_FILA = re.compile(r"^\|\s*Estado\s*\|\s*`?([^|`]+?)`?\s*\|", re.IGNORECASE)
RE_REV_YAML = re.compile(r"^revision\s*:\s*[\"']?\s*(\d{2}(?:\.\d+){0,2}(?:\.(?:IC|IB|ID|IE))?)", re.IGNORECASE)
RE_ESTADO_YAML = re.compile(r"^status\s*:\s*[\"']?\s*([^\"'#\n]+?)\s*[\"']?\s*$", re.IGNORECASE)
RE_PREGUNTA = re.compile(r"pregunta\s+que\s+responde", re.IGNORECASE)
RE_PENDIENTES = re.compile(r"^#{1,6}\s+.*pendientes\s+y\s+supuestos", re.IGNORECASE)
RE_NOAPLICA = re.compile(r"no\s+aplica\s+a\s+este\s+proyecto", re.IGNORECASE)
RE_DEC = re.compile(r"(?<![A-Za-z0-9-])DEC-\d{3,4}\b")
RE_MARCA = re.compile(r"\[(DEFINIR|VERIFICAR)\]")
RE_MARCA_ANY = re.compile(r"\[(?:DEFINIR|VERIFICAR|PENDIENTE[^\]\n]*|SUPUESTO[^\]\n]*|DECISI[OÓ]N[^\]\n]*)\]")
RE_PLACEHOLDER = re.compile(r"<[^<>\n]{1,80}>")

RE_OBLIGACION = [re.compile(p, re.IGNORECASE) for p in (
    r"\bEl\s+Contratista\s+deber[aá]n?\b",
    r"\bSer[aá]n?\s+(?:de\s+)?responsabilidad\b",
    r"\bLa\s+Ingenier[ií]a\s+de\s+Detalle\s+deber[aá]\b",
    r"\ba\s+cargo\s+del\s+Contratista\b",
)]
RE_SUJETO_PROCESO = re.compile(r"\bEl\s+Contratista\b|\bLa\s+Ingenier[ií]a\b", re.IGNORECASE)
RE_NORMA = [re.compile(p, re.IGNORECASE) for p in (
    r"\bseg[uú]n\s+(?:la\s+)?(?:normas?\b|(?:IEC|IRAM|AEA|NFPA|EN|ISO|ASTM|IEEE|NEC)\b)",
    r"\bnormativa\s+vigente\b",
    r"\bde\s+acuerdo\s+con\s+(?:la\s+)?(?:norma|reglamentaci)",
)]
RE_COMERCIAL = [re.compile(p, re.IGNORECASE) for p in (
    r"\bprecios?\b", r"\bforma\s+de\s+pago\b", r"\bmoneda\b", r"\bcondiciones\s+comerciales\b")] + \
    [re.compile(p) for p in (r"\$", r"\bUSD\b", r"\bEUR\b", r"€")]
RE_REF_CAP = re.compile(r"\bcap[ií]tulos?\s+(\d{1,2})\b|\bcap\.\s*(\d{1,2})\b", re.IGNORECASE)
RE_REF_CAP_NOMBRE = re.compile(
    r"\bcap[ií]tulos?\s+[«\"“'`]?\s*(" + "|".join(re.escape(v) for v in sorted(NOMBRES_VISIBLES.values(), key=len, reverse=True)) + r")\b",
    re.IGNORECASE)
_NUMERO_POR_NOMBRE = {v.lower(): k for k, v in NOMBRES_VISIBLES.items()}


def _leer(ruta):
    try:
        with open(ruta, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def _lineas(texto):
    """Devuelve [(n, linea)] de las líneas que NO están en bloques de código ni en comentarios HTML."""
    out = []
    en_codigo = False
    en_comentario = False
    for n, linea in enumerate(texto.splitlines(), 1):
        s = linea.strip()
        if s.startswith("```") or s.startswith("~~~"):
            en_codigo = not en_codigo
            continue
        if en_codigo:
            continue
        if en_comentario:
            if "-->" in s:
                en_comentario = False
            continue
        if s.startswith("<!--"):
            if "-->" not in s:
                en_comentario = True
            continue
        out.append((n, linea))
    return out


def _hallazgo(sev, cat, archivo, linea, msg):
    return {"severidad": sev, "categoria": cat, "archivo": archivo, "linea": linea, "mensaje": msg}


def _es_estructura(linea):
    s = linea.strip()
    return (not s) or s.startswith(("#", "|", ">", "---", "***"))


def _parrafos(lineas):
    """Párrafos de prosa: [(línea de inicio, texto)]. Cada viñeta o ítem numerado es un párrafo propio."""
    out, buf, ini = [], [], None

    def cerrar():
        nonlocal buf, ini
        if buf:
            out.append((ini, " ".join(buf)))
        buf, ini = [], None

    for n, l in lineas:
        if _es_estructura(l):
            cerrar()
            continue
        s = l.strip()
        if re.match(r"^([-*+]|\d+[.)])\s+", s):
            cerrar()
            s = re.sub(r"^([-*+]|\d+[.)])\s+", "", s)
        if ini is None:
            ini = n
        buf.append(s)
    cerrar()
    return out


def _palabras_contenido(lineas):
    """Cantidad de palabras de prosa, sin encabezados, tablas, citas, marcas ni marcadores <...>."""
    total = 0
    for _, l in lineas:
        if _es_estructura(l):
            continue
        s = RE_MARCA_ANY.sub(" ", l)
        s = RE_PLACEHOLDER.sub(" ", s)
        total += len(re.findall(r"\w+", s))
    return total


def _cabecera(lineas_todas):
    """(código, línea del código, revisión, línea de la revisión, estado) de las primeras 40 líneas."""
    cod = lcod = rev = lrev = estado = None
    for n, l in lineas_todas[:40]:
        if cod is None:
            m = RE_CODIGO.search(l)
            if m:
                cod, lcod = m.group(0), n
        if rev is None:
            m = RE_REV_FILA.match(l.strip()) or RE_REV_YAML.match(l.strip())
            if m:
                rev, lrev = m.group(1), n
        if estado is None:
            m = RE_ESTADO_FILA.match(l.strip()) or RE_ESTADO_YAML.match(l.strip())
            if m:
                estado = m.group(1).strip()
    return cod, lcod, rev, lrev, estado


def _tipo_codigo(cod):
    return cod.split("-")[2] if cod else None


def listar(carpeta):
    """(capítulos {n: [archivos]}, otros .md fuera del patrón [archivos])."""
    caps, otros = defaultdict(list), []
    for fn in sorted(os.listdir(carpeta)):
        ruta = os.path.join(carpeta, fn)
        if os.path.isdir(ruta) or fn.startswith(".") or not fn.lower().endswith(".md"):
            continue
        if fn == INDICE:
            continue
        m = RE_CAP.match(fn)
        if m and int(m.group(1)) >= 1:
            caps[int(m.group(1))].append(fn)
        else:
            otros.append(fn)
    return caps, otros


def verificar_pliego(carpeta):
    """Verifica la carpeta de un pliego modular y devuelve un dict con hallazgos, capítulos y resumen."""
    if not os.path.isdir(carpeta):
        raise ValueError(f"No existe la carpeta del pliego: {carpeta}")
    carpeta = os.path.abspath(carpeta)
    hall = []
    caps, otros = listar(carpeta)

    # (a) estructura y numeración
    ruta_indice = os.path.join(carpeta, INDICE)
    indice_existe = os.path.isfile(ruta_indice)
    if not indice_existe:
        hall.append(_hallazgo("ERROR", "estructura", INDICE, None, "Falta 00_Index_and_Control.md (portada, lista de capítulos y control de revisiones)."))
    for fn in otros:
        hall.append(_hallazgo("AVISO", "estructura", fn, None, "Archivo .md fuera del patrón NN_Nombre.md (sin tildes ni espacios, número desde 01): no se trata como capítulo."))
    maximo = max(list(caps) + [10])
    for n in range(1, maximo + 1):
        if n not in caps:
            estandar = CAPITULOS_ESTANDAR.get(n)
            detalle = f" (estándar: {n:02d}_{estandar}.md)" if estandar else ""
            hall.append(_hallazgo("ERROR", "numeracion", f"{n:02d}", None,
                                  f"Falta el capítulo {n:02d}{detalle}: la numeración debe ser contigua desde 01 y un capítulo que no aplica se conserva con su leyenda."))
    for n, fns in sorted(caps.items()):
        if len(fns) > 1:
            hall.append(_hallazgo("ERROR", "numeracion", ", ".join(fns), None, f"Número de capítulo {n:02d} duplicado: {', '.join(fns)}."))
    capitulos = {}
    for n, fns in sorted(caps.items()):
        fn = fns[0]
        nombre = RE_CAP.match(fn).group(2)
        if n in CAPITULOS_ESTANDAR and nombre != CAPITULOS_ESTANDAR[n]:
            hall.append(_hallazgo("AVISO", "numeracion", fn, None,
                                  f"El nombre del capítulo {n:02d} difiere del estándar ({n:02d}_{CAPITULOS_ESTANDAR[n]}.md)."))
        capitulos[n] = {"archivo": fn, "ruta": os.path.join(carpeta, fn), "nombre": nombre}

    # índice
    cod_ind = rev_ind = None
    if indice_existe:
        li = _lineas(_leer(ruta_indice))
        cod_ind, lc, rev_ind, lr, _ = _cabecera(li)
        if cod_ind is None:
            hall.append(_hallazgo("ERROR", "encabezado", INDICE, None, "El índice no declara el código del pliego."))
        elif _tipo_codigo(cod_ind) != "PG":
            hall.append(_hallazgo("AVISO", "encabezado", INDICE, lc, f"El código {cod_ind} no es de tipo PG (pliego técnico)."))
        if rev_ind is None:
            hall.append(_hallazgo("ERROR", "encabezado", INDICE, None, "El índice no declara la revisión del pliego (fila «Revisión» o `revision:` del bloque YAML)."))
        for sev, cat, linea, msg in comprobar_formato_pandoc(_leer(ruta_indice)):
            hall.append(_hallazgo(sev, cat, INDICE, linea, msg))

    # análisis por capítulo
    textos = {}
    resumen_caps = []
    for n, c in sorted(capitulos.items()):
        fn = c["archivo"]
        texto = _leer(c["ruta"])
        todas = [(i, l) for i, l in enumerate(texto.splitlines(), 1)]
        lin = _lineas(texto)
        textos[n] = lin
        cod, lcod, rev, lrev, estado = _cabecera(todas)
        no_aplica = any(RE_NOAPLICA.search(l) for _, l in lin)
        # (b) encabezado
        if cod is None:
            hall.append(_hallazgo("ERROR", "encabezado", fn, None, "El encabezado no declara el código del pliego."))
        else:
            if _tipo_codigo(cod) != "PG":
                hall.append(_hallazgo("AVISO", "encabezado", fn, lcod, f"El código {cod} no es de tipo PG (pliego técnico)."))
            if cod_ind and cod != cod_ind:
                hall.append(_hallazgo("ERROR", "encabezado", fn, lcod, f"El código {cod} difiere del del índice ({cod_ind})."))
        if rev is None:
            hall.append(_hallazgo("ERROR", "encabezado", fn, None, "El encabezado no declara la revisión (fila «Revisión»)."))
        elif rev_ind and rev != rev_ind:
            hall.append(_hallazgo("ERROR", "encabezado", fn, lrev, f"La revisión {rev} difiere de la del índice ({rev_ind}): el pliego tiene una sola revisión."))
        if not any(RE_PREGUNTA.search(l) for _, l in lin[:60]):
            hall.append(_hallazgo("ERROR", "encabezado", fn, None, "Falta la línea «Pregunta que responde»."))
        if not no_aplica and not any(RE_PENDIENTES.match(l.strip()) for _, l in lin):
            hall.append(_hallazgo("AVISO", "estructura", fn, None, "Falta la sección «Pendientes y supuestos»."))
        # (i) no aplica
        if no_aplica and not RE_DEC.search("\n".join(l for _, l in lin)):
            ln = next(i for i, l in lin if RE_NOAPLICA.search(l))
            hall.append(_hallazgo("ERROR", "no_aplica", fn, ln, "Capítulo «No aplica a este proyecto» sin una DEC-nnn que lo justifique."))
        # (g) vacío
        palabras = _palabras_contenido(lin)
        vacio = (not no_aplica) and palabras < MIN_PALABRAS_CONTENIDO
        if vacio:
            hall.append(_hallazgo("AVISO", "vacio", fn, None, f"Capítulo vacío o con solo la plantilla ({palabras} palabras de contenido)."))
        marcas = {"DEFINIR": 0, "VERIFICAR": 0}
        for _, l in lin:
            for m in RE_MARCA.finditer(l):
                marcas[m.group(1)] += 1
        # (c) y (d) obligaciones
        marcadas = set()
        for i, l in lin:
            if l.strip().startswith(("#", ">")):
                continue
            for rx in RE_OBLIGACION:
                m = rx.search(l)
                if m:
                    marcadas.add(i)
                    if n in CAP_ERROR:
                        hall.append(_hallazgo("ERROR", "obligacion", fn, i, f"Frase de obligación del Contratista («{m.group(0)}») en un capítulo donde corresponde a 04 o 10."))
                    elif n in CAP_AVISO:
                        hall.append(_hallazgo("AVISO", "obligacion", fn, i, f"Frase de obligación del Contratista («{m.group(0)}»): verifique que describe el método del ensayo y que la obligación contractual está en 04 o 10."))
                    break
        if n == 5:
            for i, l in lin:
                if i in marcadas or l.strip().startswith(("#", ">")):
                    continue
                m = RE_SUJETO_PROCESO.search(l)
                if m:
                    hall.append(_hallazgo("AVISO", "sujeto", fn, i, f"Requisitos de diseño con sujeto de proceso («{m.group(0)}»): redacte con el resultado como sujeto (la instalación, la solución, el sistema)."))
        # (e) normativa repetida fuera de 03
        if n != 3:
            lineas_norma = []
            for i, l in lin:
                if l.strip().startswith(("#", ">")):
                    continue
                cuenta = sum(len(rx.findall(l)) for rx in RE_NORMA)
                lineas_norma += [i] * cuenta
            if lineas_norma:
                muestra = ", ".join(str(x) for x in sorted(set(lineas_norma))[:8])
                hall.append(_hallazgo("AVISO", "normativa", fn, min(lineas_norma),
                                      f"{len(lineas_norma)} referencia(s) normativa(s) genéricas fuera del capítulo 03 (líneas {muestra}): cite el NOR-nnn en lugar de reescribir la norma."))
        # (h) comercial
        for i, l in lin:
            if l.strip().startswith(">"):
                continue
            for rx in RE_COMERCIAL:
                m = rx.search(l)
                if m:
                    hall.append(_hallazgo("AVISO", "comercial", fn, i, f"Posible precio o condición comercial («{m.group(0)}»): el pliego no los contiene (RG-05)."))
                    break
        # (j) referencias hacia adelante (por número o por nombre)
        lineas_adelante = set()
        for i, l in lin:
            if l.strip().startswith(("|", "#", ">")):
                continue
            for m in RE_REF_CAP.finditer(l):
                destino = int(m.group(1) or m.group(2))
                if destino > n:
                    lineas_adelante.add(i)
                    hall.append(_hallazgo("AVISO", "referencia_adelante", fn, i, f"Referencia hacia adelante al capítulo {destino:02d}: un capítulo no anticipa capítulos posteriores."))
            for m in RE_REF_CAP_NOMBRE.finditer(l):
                destino = _NUMERO_POR_NOMBRE[m.group(1).lower()]
                if destino > n:
                    lineas_adelante.add(i)
                    hall.append(_hallazgo("AVISO", "referencia_adelante", fn, i, f"Referencia hacia adelante al capítulo «{m.group(1)}»: un capítulo no anticipa capítulos posteriores."))
        # (k) formato Markdown compatible con Pandoc (RG-20)
        for sev, cat, linea, msg in comprobar_formato_pandoc(texto, omitir_lineas_ref=lineas_adelante):
            hall.append(_hallazgo(sev, cat, fn, linea, msg))
        resumen_caps.append({"numero": n, "archivo": fn, "estado": estado, "revision": rev, "palabras": palabras,
                             "vacio": vacio, "no_aplica": no_aplica, "marcas": marcas})

    # (f) párrafos casi duplicados entre capítulos distintos
    pares = []
    for n, lin in sorted(textos.items()):
        for ini, txt in _parrafos(lin):
            pal = re.findall(r"\w+", txt.lower())
            if len(pal) >= MIN_PALABRAS_PARRAFO:
                pares.append((n, ini, pal, set(pal)))
    vistos = set()
    for a in range(len(pares)):
        na, la, pa, sa = pares[a]
        for b in range(a + 1, len(pares)):
            nb, lb, pb, sb = pares[b]
            if na == nb:
                continue
            if min(len(sa), len(sb)) / max(len(sa), len(sb)) < UMBRAL_SIMILITUD:
                continue
            sim = len(sa & sb) / len(sa | sb)
            if sim >= UMBRAL_SIMILITUD and (nb, lb) not in vistos:
                vistos.add((nb, lb))
                hall.append(_hallazgo("AVISO", "duplicado", capitulos[nb]["archivo"], lb,
                                      f"Párrafo casi idéntico (similitud {sim:.2f}) al de {capitulos[na]['archivo']}, línea {la}: cada dato se define una sola vez."))

    hall.sort(key=lambda h: (h["severidad"] != "ERROR", h["archivo"], h["linea"] or 0, h["categoria"]))
    n_err = sum(1 for h in hall if h["severidad"] == "ERROR")
    return {
        "modulo": "CAL-011", "version": __version__, "carpeta": carpeta,
        "codigo_pliego": cod_ind, "revision_pliego": rev_ind,
        "resumen": {"capitulos": len(capitulos), "errores": n_err, "avisos": len(hall) - n_err,
                    "marcas_definir": sum(c["marcas"]["DEFINIR"] for c in resumen_caps),
                    "marcas_verificar": sum(c["marcas"]["VERIFICAR"] for c in resumen_caps)},
        "capitulos": resumen_caps, "hallazgos": hall,
        "aviso": "Ayuda de autocontrol: heurística; no reemplaza el juicio del redactor ni la auditoría (project-audit.md, A4-13).",
    }


def generar_markdown(res):
    r = res["resumen"]
    L = ["# Verificación mecánica del pliego (CAL-011)", "",
         "> Ayuda de autocontrol heurística. **No reemplaza el juicio del auditor** (`project-audit.md`, A4-13): "
         "si un texto responde otra pregunta que la de su capítulo es una decisión humana.", "",
         f"Carpeta: `{res['carpeta']}`", "",
         f"Pliego: `{res['codigo_pliego'] or '—'}` · Revisión: `{res['revision_pliego'] or '—'}`", "",
         "| Indicador | Valor |", "|---|---|",
         f"| Capítulos | {r['capitulos']} |", f"| Errores | {r['errores']} |", f"| Avisos | {r['avisos']} |",
         f"| Marcas `[DEFINIR]` abiertas | {r['marcas_definir']} |", f"| Marcas `[VERIFICAR]` abiertas | {r['marcas_verificar']} |", "",
         "## Capítulos", "",
         "| N.º | Archivo | Estado | Palabras | `[DEFINIR]` | `[VERIFICAR]` | Errores | Avisos |",
         "|---|---|---|---:|---:|---:|---:|---:|"]
    for c in res["capitulos"]:
        e = sum(1 for h in res["hallazgos"] if h["archivo"] == c["archivo"] and h["severidad"] == "ERROR")
        a = sum(1 for h in res["hallazgos"] if h["archivo"] == c["archivo"] and h["severidad"] == "AVISO")
        L.append(f"| {c['numero']:02d} | `{c['archivo']}` | {c['estado'] or '—'} | {c['palabras']} | "
                 f"{c['marcas']['DEFINIR']} | {c['marcas']['VERIFICAR']} | {e} | {a} |")
    L += ["", "## Hallazgos", ""]
    if res["hallazgos"]:
        L += ["| Severidad | Categoría | Archivo | Línea | Detalle |", "|---|---|---|---:|---|"]
        for h in res["hallazgos"]:
            L.append(f"| {h['severidad']} | {h['categoria']} | `{h['archivo']}` | {h['linea'] or '—'} | {h['mensaje'].replace('|', '/')} |")
    else:
        L.append("Sin hallazgos.")
    L.append("")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description="CAL-011: autocontrol mecánico de un pliego modular "
                                 "(ayuda de autocontrol; no reemplaza el juicio del auditor).")
    ap.add_argument("carpeta", help="carpeta del pliego (03_ENGINEERING/Technical_Specs)")
    ap.add_argument("--md", help="ruta de salida Markdown (si se omite y no hay --json, va a stdout)")
    ap.add_argument("--json", dest="json_out", help="ruta de salida JSON")
    ap.add_argument("--estricto", action="store_true", help="los avisos también hacen fallar (retorno 1)")
    a = ap.parse_args(argv)
    try:
        res = verificar_pliego(a.carpeta)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    md = generar_markdown(res)
    if a.json_out:
        with open(a.json_out, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
            f.write("\n")
    if a.md:
        with open(a.md, "w", encoding="utf-8") as f:
            f.write(md)
    if not a.md and not a.json_out:
        sys.stdout.write(md)
    r = res["resumen"]
    return 1 if (r["errores"] or (a.estricto and r["avisos"])) else 0


if __name__ == "__main__":
    sys.exit(main())
