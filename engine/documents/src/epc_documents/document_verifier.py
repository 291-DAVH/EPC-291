#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CAL-010 · document_verifier — Autocontrol mecánico de cierre documental.

ESTADO: BORRADOR — pendiente de validación por el usuario.

ES UNA AYUDA DE AUTOCONTROL: NO REEMPLAZA LA AUDITORÍA (project-audit.md). Detecta
inconsistencias mecánicas; no juzga el contenido técnico.

QUÉ VERIFICA (carpeta del proyecto, Python 3 estándar)
    (a) Coincidencia de la revisión entre la portada/cabecera (fila «Revisión» de la tabla de
        cabecera, título `# CÓDIGO_RevNN.n` y última fila de «Control de revisiones» que no sea una fila de
        entrega «00»), el nombre del archivo (`CÓDIGO_RevNN.n.md`, anexos `..._annex_*`) y la Lista Maestra de
        Entregables (tabla de `deliverables.md` con columnas «Código» y «Rev.»), cuando se
        pueda parsear. También avisa de versiones superadas fuera de `03_ENGINEERING/Archive`,
        de documentos con archivo que no figuran en la LME y de entradas de la LME sin archivo.
        Esquema de revisiones (DOCUMENT_RULES.md, sección 9): `00.0` línea base interna, `00.0.c` con
        `c` comentarios incorporados (cada uno un `REV-nnn`), `00.n` por la `rfc-n` (`00.n.c` con comentarios
        posteriores), `00` solo lo ve el cliente (carpeta 07_DELIVERABLES, que se omite), `01` as-built y `02`+
        posteriores. AVISO si un editable lleva `Rev00` (sin punto), si una fila `00.n` (n >= 1) del control
        de revisiones no cita la `rfc-00n`, si una fila `00.R.c` (c >= 1) no cita ningún `REV-nnn` y si hay
        archivos `_draft-n` heredados fuera de `Archive`.
    (b) Citas «Rev» entre documentos de ingeniería (`CÓDIGO Rev 00.2`, `CÓDIGO_Rev00.2`,
        `MC-001 Rev 00.2`) contra la revisión vigente del documento citado. Las citas
        «vigente» son válidas; si el documento citado está en una revisión interna `00.n[.c]`, una cita
        «Rev 00» (designación de entrega) se acepta. Solo se revisan los documentos con código
        (no actas, auditorías ni hojas de revisión, que citan revisiones históricas); con
        `--citas-todos` se revisan todos los `.md`.
    (c) Marcas abiertas `[DEFINIR]`, `[VERIFICAR]`, `[PENDIENTE INF-…]`, `[SUPUESTO …]`
        contadas por documento (informativo).
    (d) IDs citados (`DEC-`, `SUP-`, `INF-`, `REV-`, `rfc-`, `PAR-`, `ALD-`, `CAC-`, `NOR-`, `RIE-`) que no existen en los registros
        (una fila de tabla que empieza con el ID, en cualquier `.md` del proyecto). Los rangos
        «DEC-001 a DEC-005» se expanden.

    (h) Consistencia del charter técnico con el ejecutivo (project-audit.md, A3-19 y A3-20), cuando
        `project-charter-executive.md` ya es un lienzo generado (sin la guía de la plantilla): misma versión,
        fecha y estado; mismos `ALD`, `EXC`, `CAC`, `SUP`, `RIE` y `PQ` (lo que falta o sobra = ERROR);
        misma probabilidad, impacto y nivel de cada `RIE`; mismo orden y dependencias de los `PQ`; mismas fechas
        de hitos; costo `[DEFINIR]` ⇔ «A definir por el cliente.»; y el sello `sha256` del PDF contra el `.md`
        (PDF ausente = AVISO en borrador y ERROR si está APROBADO; sello distinto = ERROR). La equivalencia de
        significado la juzga la auditoría humana (A3-19).

    (e) Pliego modular (tipo PG): la LME se contrasta con el código y la revisión de
        `00_Index_and_Control.md` (no exige archivo con código; ver `specification_verifier.py`, CAL-011).
    (f) Formato Markdown compatible con Pandoc (DOCUMENT_RULES.md, RG-20), en cada `.md` del proyecto:
        título con numeración manual (`# 1. Alcance`, `## 2.1 …`, `# A. …`, `# IV. …`, `# 05 — …`) = ERROR;
        viñetas con `*` o `+` = ERROR; más de un `#` de nivel 1, salto de niveles de título (`##` → `####`),
        referencias numéricas en el texto («sección 3.2», «capítulo 4», «apartado 2.1», «cap. 05»), lista sin
        línea en blanco previa y tabuladores = AVISO. Se ignoran el bloque YAML inicial, los bloques de código
        y los comentarios HTML. NO se verifican los archivos del propio framework (los `.md` de gestión de
        `02_PROJECT`, `90-management`, `04_REVIEW/Review_Sheets`, `05_AUDIT` y de la raíz; `99_core` se omite: conservan su numeración
        interna porque no se convierten a Word) ni la carpeta `Technical_Specs` (la cubre `specification_verifier.py`).

    (g) Confidencialidad económica (DOCUMENT_RULES.md, RG-21): cifras con moneda (`$ 1.500`, `USD 20.000`,
        `1500 pesos`, `US$`, `€`) = ERROR; una palabra de costo (presupuesto, costo, precio, monto, honorarios,
        tarifa, importe) seguida de una cifra de 4 o más dígitos o con separador de miles = AVISO. Se revisan los
        `.md` del proyecto (no los del framework), `_INPUT_REGISTER.md` y los `MINUTES-*.md` de
        `01-input`. Una línea con la marca `[ECON-AUTORIZADO DEC-nnn]` queda exceptuada
        (pedido expreso del usuario registrado como decisión; la `DEC-nnn` debe existir).

QUÉ NO HACE
    No valida unidades, cálculos ni contenido; no sigue enlaces; solo cita adyacente (una lista
    «`MC-001`, `MC-002` Rev 00.2» solo comprueba la última). La revisión se lee de la tabla de cabecera
    («| Revisión | 00.2 |») o del bloque YAML inicial (`revision: "00.2"`). Se omiten `03_ENGINEERING/Archive`,
    `07_DELIVERABLES` (copias limpias de lo entregado, solo lectura: no son documentos de trabajo),
    `98_LIBRARY`, `01-input`, `.git` y `__pycache__`.

SALIDA Y CÓDIGO DE RETORNO
    Markdown (`--md`, o salida estándar) y JSON (`--json`). Retorno 0 si no hay hallazgos de
    severidad ERROR (los AVISO no fallan, salvo `--estricto`); 1 si los hay; 2 si la carpeta
    no existe.

USO (desde la raíz del proyecto)
    python3 -B 98_LIBRARY/calculations/document_verifier.py <carpeta_del_proyecto> [--md output.md]
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict

__version__ = "0.8.0"

# 07_DELIVERABLES contiene copias limpias de lo ya entregado (revisiones 00 de lo editable): se omite para
# no duplicar documentos ni dar falsos «superados» ni «duplicados». Se contrasta contra 03_ENGINEERING en la
# auditoría de entrega (project-audit.md, A1-16), no con esta herramienta.
CARPETAS_OMITIDAS = {"Archive", "98_LIBRARY", "99_core", "01-input", "07_DELIVERABLES", "ledger",
                     ".git", "__pycache__", "node_modules"}
CODIGO = r"[A-Z][A-Z0-9]{1,7}-[A-Z]{1,2}-[A-Z]{2}-\d{3}"
RE_ARCHIVO = re.compile(r"^(?P<codigo>" + CODIGO + r")(?P<medio>.*?)_?Rev(?P<rev>\d{2}(?:\.\d+){0,2}(?:\.(?:IC|IB|ID|IE))?)(?P<resto>.*)\.(?P<ext>[A-Za-z0-9]+)$")
RE_CITA = re.compile(r"(?P<codigo>" + CODIGO + r"|(?<![A-Z0-9-])[A-Z]{2}-\d{3})(?P<sep>[`\s_]*)"
                     r"Rev(?:isi[oó]n|\.)?\s*(?P<rev>\d{2}(?:\.\d+){0,2}(?:\.(?:IC|IB|ID|IE))?|vigente)", re.IGNORECASE)
RE_MARCA = re.compile(r"\[(DEFINIR|VERIFICAR|PENDIENTE[^\]\n]*|SUPUESTO[^\]\n]*)\]")
TIPOS_ID = ("DEC", "SUP", "INF", "REV", "rfc", "PAR", "ALD", "CAC", "NOR", "RIE")
RE_ID = re.compile(r"(?<![A-Za-z0-9-])(" + "|".join(TIPOS_ID) + r")-(\d{1,4})\b")
RE_RANGO = re.compile(r"(?<![A-Za-z0-9-])(" + "|".join(TIPOS_ID) + r")-(\d{1,4})`?\s*(?:a|al|–|—|-)\s*`?\1-(\d{1,4})\b")
RE_FILA_REV = re.compile(r"^\|\s*(\d{2}(?:\.\d+){0,2}(?:\.(?:IC|IB|ID|IE))?)\s*\|")
RE_ENCABEZADO_CONTROL = re.compile(r"^\|\s*Rev\.?\s*\|", re.IGNORECASE)    # encabezado de «Control de revisiones»
RE_BORRADOR = re.compile(r"_draft-\d+", re.IGNORECASE)
RE_CAB_REV = re.compile(r"^\|\s*(?:Revisi[oó]n|Rev\.?)\s*\|\s*([^|]+?)\s*\|", re.IGNORECASE)
RE_TITULO = re.compile(r"^#\s+(" + CODIGO + r")(?:_?Rev\s*(\d{2}(?:\.\d+){0,2}(?:\.(?:IC|IB|ID|IE))?))?")
RE_CAB_REV_YAML = re.compile(r"^revision\s*:\s*[\"']?\s*(\d{2}(?:\.\d+){0,2}(?:\.(?:IC|IB|ID|IE))?)", re.IGNORECASE)

# --- Formato Markdown compatible con Pandoc (DOCUMENT_RULES.md, RG-20) ---------------------------------
# Archivos del propio framework: conservan su numeración interna (no se convierten a Word) y no se verifican.
ARCHIVOS_FRAMEWORK = {
    "assumptions-and-decisions.md", "CAD_standards.md", "change-requests.md", "CLAUDE.md", "client-requirements.md",
    "COMMANDS.md", "starting-data.md", "deliverables.md", "DESIGN_RULES.md", "DOCUMENT_RULES.md", "drawing-status.md", "engineering-standards.md",
    "folder-templates.md", "goals.md", "lessons-learned.md", "TECHNICAL_SPECIFICATIONS_GUIDE.md", "project-audit.md",
    "project-charter.md", "project-charter-executive.md", "project-information.md", "project-scope.md", "project-status.md", "audit-register.md", "review-sheet.md", "schedule-ccpm.md",
    "traceability-matrix.md",
    # Gestión (M8): planes, registros y plantillas con numeración interna propia
    "project-handbook.md", "stakeholders.md", "comm-plan.md", "risk-plan.md", "quality-hse-plan.md", "procurement-plan.md",
    "acceptance-transition-plan.md", "effort-baseline.md", "issue-log.md", "ncr-log.md", "site-rfi-log.md", "redline-log.md",
    "punch-list.md", "close-checklist.md", "management-templates.md",
}
# Carpetas (relativas a la raíz del proyecto) donde viven los archivos de gestión del framework.
DIRS_FRAMEWORK = {"", "02_PROJECT", "90-management", "04_REVIEW/Review_Sheets", "05_AUDIT",
                  "90-management/Governance", "90-management/Governance/Communications",
                  "90-management/Governance/Communications/rfi", "90-management/Governance/Quality_and_HSE",
                  "90-management/Planning", "90-management/reports"}
CARPETA_PLIEGOS = "Technical_Specs"          # la verifica specification_verifier.py (CAL-011)
# Título con numeración manual: la expresión del RG-20 más las variantes «05 — Nombre» y «Capítulo 5».
RE_TITULO_NUM = re.compile(r"^#+\s*(\d+[\.\)]|\d+\.\d+|[A-Z]\.\s|[IVX]+\.)")
RE_TITULO_NUM_EXTRA = re.compile(r"^#+\s*(?:\d+\s*[\u2014\u2013:]|\d+\s+-\s|(?:cap[i\u00ed]tulo|secci[o\u00f3]n|apartado)\s+\d+)", re.IGNORECASE)
RE_VINETA_PROHIBIDA = re.compile(r"^\s*[*+]\s+\S")
RE_REGLA_HORIZONTAL = re.compile(r"^\s*([-*_])(\s*\1){2,}\s*$")
RE_ITEM_LISTA = re.compile(r"^(\s*)(?:-|\d{1,3}[.)])\s+\S")
RE_ITEM_CUALQUIERA = re.compile(r"^\s*(?:[-*+]|\d{1,3}[.)])\s+")
RE_REF_NUMERICA = re.compile(r"\b(?:secci[o\u00f3]n(?:es)?|cap[i\u00ed]tulos?|apartados?)\s+\d+(?:\.\d+)*\b|\bcap\.\s*\d+\b", re.IGNORECASE)
RE_ARCHIVO_FRAMEWORK = re.compile(r"\b[A-Z][A-Z_]{3,}\.md\b")     # «DOCUMENT_RULES.md, sección 9» es una cita al framework


def _leer(ruta):
    try:
        with open(ruta, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def _lineas_formato(texto):
    """[(n, linea)] de las líneas de prosa: sin el bloque YAML inicial, sin bloques de código ni comentarios HTML."""
    out = []
    todas = texto.splitlines()
    inicio = 0
    if todas and todas[0].strip() == "---":
        for k in range(1, len(todas)):
            if todas[k].strip() in ("---", "..."):
                inicio = k + 1
                break
    en_codigo = en_comentario = False
    for n in range(inicio, len(todas)):
        linea = todas[n]
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
        out.append((n + 1, linea))
    return out


def comprobar_formato_pandoc(texto, referencias_numericas=True, omitir_lineas_ref=()):
    """Comprobaciones de formato Markdown compatible con Pandoc (DOCUMENT_RULES.md, RG-20).

    Devuelve [(severidad, categoria, linea, mensaje)] ordenado por línea. `omitir_lineas_ref` son líneas cuyas
    referencias numéricas ya informó otra comprobación (para no duplicar el aviso)."""
    res = []
    lineas = _lineas_formato(texto)
    niveles = []                      # [(n, nivel)]
    tabuladores = []
    previa = None                     # (n, linea) de la línea anterior (en la numeración original)
    for n, l in lineas:
        s = l.strip()
        if "\t" in l:
            tabuladores.append(n)
        m = re.match(r"^(#{1,6})\s+\S", l)
        if m:
            niveles.append((n, len(m.group(1))))
        if l.startswith("#") and (RE_TITULO_NUM.match(l) or RE_TITULO_NUM_EXTRA.match(l)):
            res.append(("ERROR", "formato_titulo_numerado", n,
                        f"Título con numeración manual («{s[:60]}»): escriba solo el texto; la numeración la aplica la plantilla Word."))
        if RE_VINETA_PROHIBIDA.match(l) and not RE_REGLA_HORIZONTAL.match(l):
            res.append(("ERROR", "formato_vineta", n,
                        f"Viñeta con «{s[0]}» («{s[:40]}»): use siempre «- » (evita «* **NEGRITA**»)."))
        # lista sin línea en blanco previa
        if RE_ITEM_LISTA.match(l) and not RE_REGLA_HORIZONTAL.match(l) and previa is not None and previa[0] == n - 1:
            pl = previa[1]
            if (pl.strip() and not pl.lstrip().startswith("#") and not RE_ITEM_CUALQUIERA.match(pl)
                    and not pl[:1].isspace() and not pl.lstrip().startswith(">")):
                res.append(("AVISO", "formato_lista_sin_blanco", n,
                            "La lista no tiene una línea en blanco antes: Pandoc puede unirla al párrafo anterior."))
        if referencias_numericas and n not in omitir_lineas_ref and not l.startswith("#"):
            if not RE_ARCHIVO_FRAMEWORK.search(l):
                mm = RE_REF_NUMERICA.search(l)
                if mm:
                    res.append(("AVISO", "formato_referencia_numerica", n,
                                f"Referencia por número («{mm.group(0)}»): cite por nombre («ver el capítulo Marco Normativo»), "
                                "porque Word renumera los títulos."))
        previa = (n, l)
    h1 = [n for n, nivel in niveles if nivel == 1]
    if len(h1) > 1:
        res.append(("AVISO", "formato_h1_multiple", h1[1],
                    f"Hay {len(h1)} títulos de nivel 1 (`#`, líneas {', '.join(str(x) for x in h1[:6])}): un documento lleva un solo `#`; el resto son `##`, `###`…"))
    for (n0, a), (n1, b) in zip(niveles, niveles[1:]):
        if b > a + 1:
            res.append(("AVISO", "formato_salto_nivel", n1,
                        f"Salto de niveles de título: de {'#' * a} a {'#' * b} (falta {'#' * (a + 1)})."))
    if tabuladores:
        res.append(("AVISO", "formato_tabulador", tabuladores[0],
                    f"{len(tabuladores)} línea(s) con tabuladores (primera en {tabuladores[0]}): use espacios."))
    res.sort(key=lambda x: (x[2], x[1]))
    return res


# --- Confidencialidad económica (DOCUMENT_RULES.md, RG-21) ------------------------------------------
_NUM = r"\d{1,3}(?:[.,]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?"
RE_MONEDA = re.compile(
    r"(?:US\$|U\$S|\$|€|\b(?:USD|ARS|EUR|U\$D)\b)\s*(?:" + _NUM + r")"
    r"|(?<![\w.,-])(?:" + _NUM + r")\s*(?:USD|ARS|EUR|€|\$|pesos|d[oó]lares|euros|millones\s+de\s+pesos)\b",
    re.IGNORECASE)
RE_PALABRA_COSTO = re.compile(
    r"\b(?:presupuesto|costos?|precios?|montos?|honorarios|tarifas?|importes?)\b[^\n]{0,40}?"
    r"(?<![\w\-/.])(?:\d{1,3}(?:[.,]\d{3})+|\d{4,})(?![\w\-/])", re.IGNORECASE)
RE_ECON_OK = re.compile(r"\[ECON-AUTORIZADO\s+(DEC-\d{1,4})\]")


def comprobar_confidencialidad(texto):
    """RG-21: devuelve [(severidad, categoria, linea, mensaje, dec_autorizada|None)] con cifras económicas."""
    out, en_codigo = [], False
    for n, linea in enumerate(texto.splitlines(), 1):
        if linea.lstrip().startswith("```"):
            en_codigo = not en_codigo
            continue
        if en_codigo:
            continue
        ok = RE_ECON_OK.search(linea)
        dec = ok.group(1) if ok else None
        linea_sin = RE_ECON_OK.sub(" ", linea)
        if RE_MONEDA.search(linea_sin):
            out.append(("ERROR", "confidencialidad_economica", n,
                        "Cifra con moneda: los costos, precios y montos del cliente no se plasman en el proyecto "
                        "(RG-21); quitarla o registrar la excepción pedida por el usuario como DEC-nnn.", dec))
        elif RE_PALABRA_COSTO.search(linea_sin):
            out.append(("AVISO", "confidencialidad_economica", n,
                        "Palabra de costo seguida de una cifra: revisar que no sea un dato económico del cliente (RG-21).", dec))
    return out


def _recorrer(raiz):
    for dirpath, dirnames, filenames in os.walk(raiz):
        dirnames[:] = sorted(d for d in dirnames if d not in CARPETAS_OMITIDAS and not d.startswith("."))
        for fn in sorted(filenames):
            if fn.startswith("RELEASE_"):        # registros generados por release-documents.py (06_RELEASED)
                continue
            yield os.path.join(dirpath, fn)


def _norm_rev(texto):
    """Extrae 'NN.n' (o 'NN') de un texto; None si no hay revisión."""
    if texto is None:
        return None
    m = re.search(r"\d{2}(?:\.\d+){0,2}(?:\.(?:IC|IB|ID|IE))?", str(texto))
    return m.group(0) if m else None


FASES_REV = {"IC": 0, "IB": 1, "ID": 2, "IE": 3}


def _partes_rev(rev):
    """(números, fase): '00.2.34.IB' -> (['00', '2', '34'], 'IB'); '00.0' -> (['00', '0'], None)."""
    a = rev.split(".")
    fase = a.pop().upper() if a and a[-1].upper() in FASES_REV else None
    return a, fase


def _clave_rev(rev):
    a, fase = _partes_rev(rev)
    return (int(a[0]), int(a[1]) if len(a) > 1 else -1, int(a[2]) if len(a) > 2 else -1,
            FASES_REV[fase] if fase else -1)


def es_archivo_framework(p, raiz):
    """True si p está en una carpeta de gestión del framework (DIRS_FRAMEWORK)."""
    d = os.path.relpath(os.path.dirname(p), raiz).replace(os.sep, "/")
    return ("" if d == "." else d) in DIRS_FRAMEWORK


def _parsear_lme(raiz):
    """Devuelve ({codigo: {id, rev, estado, aplica}}, nota). Lee el primer cuadro de
    deliverables.md con columnas «Código» y «Rev.»."""
    ruta = os.path.join(raiz, "90-management", "deliverables.md")
    if not os.path.exists(ruta):
        return None, "No se encontró deliverables.md: se omite la comparación con la LME."
    cols = None
    out = {}
    for linea in _leer(ruta).splitlines():
        if not linea.startswith("|"):
            if cols is not None and out:
                break
            cols = None if not out else cols
            continue
        celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
        bajas = [re.sub(r"[\s`*]", "", c.lower()) for c in celdas]
        if cols is None:
            if "código" in bajas and any(b.startswith("rev") for b in bajas) and "id" in bajas:
                cols = {"id": bajas.index("id"), "codigo": bajas.index("código"),
                        "rev": next(i for i, b in enumerate(bajas) if b.startswith("rev")),
                        "estado": bajas.index("estado") if "estado" in bajas else None,
                        "aplica": next((i for i, b in enumerate(bajas) if b.startswith("aplica")), None)}
            continue
        if set("".join(celdas)) <= set("-: "):
            continue
        if len(celdas) <= max(v for v in cols.values() if v is not None):
            continue
        codigo = celdas[cols["codigo"]].strip("` ")
        if not re.fullmatch(CODIGO, codigo):
            continue
        out[codigo] = {"id": celdas[cols["id"]].strip("` "), "rev": _norm_rev(celdas[cols["rev"]]),
                       "estado": celdas[cols["estado"]] if cols["estado"] is not None else "",
                       "aplica": celdas[cols["aplica"]].strip("` ") if cols["aplica"] is not None else ""}
    if not out:
        return None, "La LME de deliverables.md no se pudo parsear (sin filas con código): se omite."
    return out, None


def _cabecera(texto):
    """(rev de la tabla de cabecera, rev del título, rev de la última fila de control que no es de entrega,
    [(rev, línea)] de todas las filas del «Control de revisiones»). Las filas «00» (sin punto) son filas de
    entrega al cliente (TR-nnn) y no cuentan como revisión vigente; solo se leen las filas de la tabla cuyo
    encabezado empieza con «Rev.»."""
    rev_tabla = rev_titulo = None
    filas = []
    en_control = False
    for linea in texto.splitlines()[:200]:
        m = RE_CAB_REV.match(linea) or RE_CAB_REV_YAML.match(linea)
        if m and rev_tabla is None:
            rev_tabla = _norm_rev(m.group(1))
        t = RE_TITULO.match(linea)
        if t and t.group(2) and rev_titulo is None:
            rev_titulo = t.group(2)
        if RE_ENCABEZADO_CONTROL.match(linea):
            en_control = True
            continue
        if not linea.startswith("|"):
            en_control = False
            continue
        f = RE_FILA_REV.match(linea)
        if f and en_control:
            filas.append((f.group(1), linea))
    internas = [rv for rv, _ in filas if rv != "00"]
    return rev_tabla, rev_titulo, (internas[-1] if internas else None), filas


def _indices_pliego(archivos):
    """{código del pliego: revisión} leído de cada `00_Index_and_Control.md` (código con tipo PG)."""
    out = {}
    for p in archivos:
        if os.path.basename(p) != "00_Index_and_Control.md":
            continue
        lineas = _leer(p).splitlines()[:40]
        cod = next((m.group(0) for m in (re.search(r"[A-Z][A-Z0-9]{1,7}-[A-Z]{1,2}-PG-\d{3}", l) for l in lineas) if m), None)
        if cod is None:
            continue
        rev = next((_norm_rev(m.group(1)) for m in (RE_CAB_REV.match(l) or RE_CAB_REV_YAML.match(l) for l in lineas) if m), None)
        out[cod] = rev
    return out


# --- Consistencia charter técnico ↔ charter ejecutivo (project-audit.md, A3-19 y A3-20) -----------------
RE_ID_charter = re.compile(r"(?<![A-Za-z0-9-])(ALD|EXC|CAC|SUP|RIE|PQ)-(\d{1,4})\b")
RE_COMENT_HTML = re.compile(r"<!--.*?-->", re.DOTALL)
RE_FECHA_ISO = re.compile(r"\d{4}-\d{2}-\d{2}")
RE_SELLO_PDF = re.compile(r"sha256:([0-9a-f]{16})")
TIPOS_charter = ("ALD", "EXC", "CAC", "SUP", "RIE", "PQ")


def sello_charter_md(texto):
    """sha256 (16 hex) del texto con saltos LF; el mismo que estampa charter_exporter.py (CAL-013)."""
    import hashlib
    t = texto.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(t.encode("utf-8")).hexdigest()[:16]


def _limpio(s):
    return re.sub(r"\s+", " ", RE_COMENT_HTML.sub("", s).replace("`", "").replace("**", "")).strip()


def _seccion(texto, patron_titulo):
    """Texto de la sección cuyo título (###/##) cumple patron_titulo, hasta el siguiente título de igual o mayor rango."""
    lineas = texto.split("\n")
    for i, l in enumerate(lineas):
        m = re.match(r"^(#{2,3})\s+(.*)$", l)
        if m and re.search(patron_titulo, m.group(2), re.IGNORECASE):
            n = len(m.group(1))
            fin = len(lineas)
            for j in range(i + 1, len(lineas)):
                m2 = re.match(r"^(#{1,3})\s", lineas[j])
                if m2 and len(m2.group(1)) <= n:
                    fin = j
                    break
            return "\n".join(lineas[i + 1:fin])
    return None


def _filas(texto):
    """Filas de datos de la primera tabla Markdown del texto: lista de listas de celdas limpias."""
    filas = []
    for l in (texto or "").split("\n"):
        s = l.strip()
        if not s.startswith("|"):
            continue
        celdas = [_limpio(c) for c in s.strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in celdas if c) and any(celdas):
            continue
        filas.append(celdas)
    return filas[1:] if filas else []


def _ids_charter(texto):
    return {t: sorted({f"{t}-{n.zfill(3) if t != 'PQ' else n.zfill(2)}" for tt, n in RE_ID_charter.findall(texto) if tt == t})
            for t in TIPOS_charter}


def _campos_cabecera(texto):
    campos = {}
    for l in texto.split("\n")[:25]:
        m = re.match(r"^\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*$", l)
        if m:
            campos[_limpio(m.group(1)).lower()] = _limpio(m.group(2))
    return campos


def _campos_lienzo(lienzo):
    """Encabezado del lienzo: tabla horizontal «Proyecto | Versión | Fecha | Estado» antes de la primera caja."""
    previo = re.split(r"(?m)^### ", lienzo, maxsplit=1)[0]
    filas = [[_limpio(c) for c in l.strip().strip("|").split("|")] for l in previo.split("\n") if l.strip().startswith("|")]
    filas = [f for f in filas if not all(re.fullmatch(r":?-{2,}:?", c) for c in f if c)]
    if len(filas) < 2:
        return {}
    return {k.lower(): v for k, v in zip(filas[0], filas[1])}


def _nivel_o_none(s):
    m = re.search(r"\d+", s or "")
    return int(m.group(0)) if m else None


def comprobar_charter_ejecutivo(txt_charter, txt_ejec):
    """Contrasta el charter técnico con el ejecutivo. Devuelve [(severidad, categoria, mensaje)]."""
    h = []
    def err(msg, sev="ERROR"):
        h.append((sev, "charter_ejecutivo", msg))
    k = txt_charter.find("# REGISTRO DEL PROYECTO")
    reg = txt_charter[k:] if k >= 0 else txt_charter
    k2 = txt_ejec.find("# LIENZO EJECUTIVO")
    lienzo = txt_ejec[k2:] if k2 >= 0 else txt_ejec
    # encabezado
    cab_c = _campos_cabecera(txt_charter)
    cab_e = _campos_lienzo(lienzo)
    ver_c = _norm_ver(cab_c.get("versión de la línea base"))
    ver_e = _norm_ver(cab_e.get("versión"))
    if ver_c != ver_e:
        err(f"Versión distinta: charter técnico «{ver_c}», ejecutivo «{ver_e}».")
    if cab_c.get("fecha", "") != cab_e.get("fecha", ""):
        err(f"Fecha distinta: charter técnico «{cab_c.get('fecha', '')}», ejecutivo «{cab_e.get('fecha', '')}».")
    est_c = cab_c.get("estado", "").upper()
    est_e = cab_e.get("estado", "").upper()
    if est_c != est_e:
        err(f"Estado distinto: charter técnico «{est_c}», ejecutivo «{est_e}».")
    pr_c, cod_c, pr_e = cab_c.get("proyecto", ""), cab_c.get("código de proyecto", ""), cab_e.get("proyecto", "")
    if "[DEFINIR]" not in pr_c + pr_e + cod_c and not any(x and x.lower() in pr_e.lower() for x in (pr_c, cod_c)):
        err(f"El proyecto del ejecutivo («{pr_e}») no coincide con el del charter técnico («{pr_c}» / «{cod_c}»).", "AVISO")
    # IDs
    ic, ie = _ids_charter(reg), _ids_charter(lienzo)
    for t in TIPOS_charter:
        falta = [i for i in ic[t] if i not in ie[t]]
        sobra = [i for i in ie[t] if i not in ic[t]]
        if falta:
            err(f"El ejecutivo no incluye {', '.join(falta)} del charter técnico.")
        if sobra:
            err(f"El ejecutivo cita {', '.join(sobra)}, que no figura en el charter técnico.")
    # riesgos: probabilidad, impacto y nivel
    def riesgos(filas, tecnico):
        out = {}
        for f in filas:
            m = RE_ID_charter.search(f[0]) if f else None
            if not m or m.group(1) != "RIE":
                continue
            rid = f"RIE-{m.group(2).zfill(3)}"
            out[rid] = tuple(_nivel_o_none(x) for x in (f[2:5] if tecnico else f[1:4]) ) if len(f) >= (5 if tecnico else 4) else (None,) * 3
        return out
    rc = riesgos(_filas(_seccion(reg, r"^3\.8\b")), True)
    re_ = riesgos(_filas(_seccion(lienzo, r"^Riesgos$")), False)
    for rid in sorted(set(rc) & set(re_)):
        if rc[rid] != re_[rid]:
            err(f"{rid}: prob./impacto/nivel distintos (técnico {rc[rid]}, ejecutivo {re_[rid]}).")
    for nom, d in (("técnico", rc), ("ejecutivo", re_)):
        for rid, (p, i, n) in sorted(d.items()):
            if None not in (p, i, n) and p * i != n:
                err(f"{rid} ({nom}): el nivel {n} no es prob. × impacto ({p} × {i}).", "AVISO")
    # paquetes: orden y dependencias
    def paquetes(filas):
        out = []
        for f in filas:
            m = re.search(r"PQ-\d+", f[1]) if len(f) > 1 else None
            if m:
                out.append((m.group(0), tuple(sorted(set(re.findall(r"PQ-\d+", f[-1]))))))
        return out
    pc = paquetes(_filas(_seccion(reg, r"^7\.")))
    pe = paquetes(_filas(_seccion(lienzo, r"^Desglose del trabajo$")))
    if [p for p, _ in pc] != [p for p, _ in pe]:
        err(f"Orden de paquetes distinto: técnico {[p for p, _ in pc]}, ejecutivo {[p for p, _ in pe]}.")
    else:
        for (p, dc), (_, de) in zip(pc, pe):
            if dc != de:
                err(f"{p}: dependencias distintas (técnico {list(dc)}, ejecutivo {list(de)}).")
    # hitos: mismas fechas
    sec_h_c = _seccion(reg, r"^4\.2\b") or ""
    fc = {x for f in _filas(sec_h_c) for x in RE_FECHA_ISO.findall(" ".join(f))}
    fe = set(RE_FECHA_ISO.findall(_limpio(_seccion(lienzo, r"^Hitos$") or "")))
    if fc != fe:
        err(f"Fechas de hitos distintas: solo en técnico {sorted(fc - fe)}, solo en ejecutivo {sorted(fe - fc)}.")
    # costo
    costo = _limpio(_seccion(reg, r"^4\.1\b") or "")
    pres = _limpio(_seccion(lienzo, r"^Presupuesto$") or "")
    if "[DEFINIR]" in costo:
        if not ("a definir por el cliente" in pres.lower() or "[DEFINIR]" in pres):
            err(f"El costo del charter técnico está [DEFINIR] y el ejecutivo dice «{pres}» (debe decir «A definir por el cliente.»).")
    else:
        if costo and pres and pres not in costo and costo not in pres:
            err(f"El presupuesto del ejecutivo («{pres}») no es el costo del charter técnico («{costo}»).")
        if costo and not re.search(r"DEC-\d+", costo):
            err("El costo del charter técnico no cita la DEC-nnn que lo autoriza.", "AVISO")
    return h


def _norm_ver(v):
    return re.sub(r"\s*\(.*?\)\s*", "", v or "").strip()


def comprobar_pdf_ejecutivo(ruta_md, txt_ejec, aprobado):
    """Compara el sello sha256 del PDF con el del .md. Devuelve [(sev, cat, msg)]."""
    pdf = os.path.splitext(ruta_md)[0] + ".pdf"
    esperado = sello_charter_md(txt_ejec)
    sev_falta = "ERROR" if aprobado else "AVISO"
    if not os.path.exists(pdf):
        return [(sev_falta, "charter_ejecutivo_pdf", "No existe PROJECT_charter_EXECUTIVE.pdf; generarlo con "
                 "`python3 -B 98_LIBRARY/calculations/charter_exporter.py 02_PROJECT/project-charter-executive.md`.")]
    with open(pdf, "rb") as f:
        crudo = f.read().decode("latin-1")
    m = RE_SELLO_PDF.search(crudo)
    s = m.group(1) if m else None
    if s is None:
        try:
            import subprocess
            out = subprocess.run(["pdftotext", pdf, "-"], capture_output=True, text=True, timeout=30).stdout
            m = RE_SELLO_PDF.search(out)
            s = m.group(1) if m else None
        except (OSError, Exception):
            s = None
    if s is None:
        return [(sev_falta, "charter_ejecutivo_pdf", "El PDF del charter ejecutivo no lleva sello sha256; regenerarlo con charter_exporter.py.")]
    if s != esperado:
        return [("ERROR", "charter_ejecutivo_pdf", f"El PDF del charter ejecutivo (sello {s}) no corresponde al .md vigente (sello {esperado}); regenerarlo.")]
    return []


def _hallazgo(sev, cat, archivo, msg):
    return {"severidad": sev, "categoria": cat, "archivo": archivo, "mensaje": msg}


def _agrupar_documentos(archivos, rel, hall):
    """Documentos con código y revisión en el nombre: {código: [{ruta, rev, ext, anexo, medio}]}. Los borradores sueltos se avisan y no cuentan."""
    docs = defaultdict(list)
    for p in archivos:
        m = RE_ARCHIVO.match(os.path.basename(p))
        if m and RE_BORRADOR.search(m.group("resto")):
            hall.append(_hallazgo("AVISO", "borrador_fuera_de_archivo", rel(p),
                                  "Ya no existen borradores con la revisión fija: toda versión nueva es una revisión (00.0.1, 00.1…). "
                                  "Archivar el archivo en 03_ENGINEERING/Archive/<código>/ o renombrarlo."))
            continue
        if m:
            docs[m.group("codigo")].append({"ruta": p, "rev": m.group("rev"), "ext": m.group("ext").lower(),
                                            "anexo": "annex" in m.group("resto").lower(),
                                            "medio": m.group("medio")})
    return docs


def _revisiones_vigentes(docs, rel, hall):
    """Revisión vigente de cada código (la mayor de los documentos principales) y los avisos de versiones superadas, Rev 00 y anexos desfasados."""
    vigente = {}
    for cod, lista in docs.items():
        principales = [d for d in lista if not d["anexo"]]
        base = principales or lista
        vigente[cod] = max((d["rev"] for d in base), key=_clave_rev)
        for d in lista:
            if d["rev"] != vigente[cod] and not d["anexo"]:
                hall.append(_hallazgo("AVISO", "version_superada", rel(d["ruta"]),
                                      f"Rev {d['rev']} de {cod} fuera de 03_ENGINEERING/Archive; la vigente es {vigente[cod]}."))
        for d in lista:
            if d["rev"] == "00" and not d["anexo"]:
                hall.append(_hallazgo("AVISO", "rev_00_en_editables", rel(d["ruta"]),
                                      "Rev 00 (sin punto) es la designación de entrega al cliente y solo existe en 07_DELIVERABLES; "
                                      "un editable lleva 00.0, 00.n, 01 o posterior."))
        for d in lista:
            if d["anexo"] and d["rev"] != vigente[cod]:
                hall.append(_hallazgo("ERROR", "revision", rel(d["ruta"]),
                                      f"El anexo es Rev {d['rev']} pero el documento {cod} vigente es Rev {vigente[cod]}."))
    return vigente


def _verificar_filas_control(d, filas_ctrl, rel, hall):
    """Filas del «Control de revisiones»: la Rev 00.n nace de la rfc-n y cada unidad del último dígito, de un comentario REV-nnn."""
    previa = None
    for rv, linea in filas_ctrl:
        partes, fase = _partes_rev(rv)
        numeros = partes[:3]
        cambia_solo_fase = previa is not None and numeros == previa and fase is not None
        if partes[0] == "00" and len(partes) >= 2:
            if int(partes[1]) >= 1 and (len(partes) < 3 or int(partes[2]) == 0) \
                    and not re.search(r"rfc-0*" + str(int(partes[1])) + r"\b", linea) and not cambia_solo_fase:
                hall.append(_hallazgo("AVISO", "rev_sin_rfc", rel(d["ruta"]),
                                      f"La fila {rv} del control de revisiones no cita la rfc-{int(partes[1]):03d}: "
                                      "la Rev 00.n (último dígito en cero) solo nace de la rfc-n."))
            elif len(partes) == 3 and int(partes[2]) >= 1 and not cambia_solo_fase \
                    and not re.search(r"\bREV-\d+|avance de fase", linea, re.IGNORECASE):
                hall.append(_hallazgo("AVISO", "rev_sin_comentario", rel(d["ruta"]),
                                      f"La fila {rv} del control de revisiones no cita ningún REV-nnn (ni «Avance de fase»): "
                                      "cada unidad del último dígito corresponde a un comentario incorporado."))
        if partes[0] == "00" and len(partes) >= 2:
            previa = numeros


def _verificar_coherencia_revision(docs, vigente, lme, rel, hall):
    """(a) Coherencia de la revisión entre nombre de archivo, cabecera, título, control de revisiones y LME."""
    for cod, lista in sorted(docs.items()):
        for d in lista:
            if d["anexo"] or d["ext"] != "md" or d["rev"] != vigente[cod]:
                continue
            rev_tabla, rev_titulo, rev_ctrl, filas_ctrl = _cabecera(_leer(d["ruta"]))
            _verificar_filas_control(d, filas_ctrl, rel, hall)
            for etiqueta, valor in (("fila «Revisión» de la cabecera", rev_tabla), ("título", rev_titulo),
                                    ("última fila de «Control de revisiones»", rev_ctrl)):
                if valor is not None and valor != d["rev"]:
                    hall.append(_hallazgo("ERROR", "revision", rel(d["ruta"]),
                                          f"{etiqueta} dice {valor} pero el nombre del archivo dice {d['rev']}."))
            if rev_tabla is None:
                hall.append(_hallazgo("AVISO", "revision", rel(d["ruta"]),
                                      "No se encontró la fila «Revisión» (ni `revision:` en el bloque YAML) en la cabecera (no se pudo comparar)."))
        if lme is not None and cod in lme and lme[cod]["rev"] is not None and lme[cod]["rev"] != vigente[cod]:
            hall.append(_hallazgo("ERROR", "revision", "deliverables.md",
                                  f"La LME ({lme[cod]['id']}) dice Rev {lme[cod]['rev']} para {cod} pero el archivo vigente es Rev {vigente[cod]}."))
        if lme is not None and cod not in lme:
            hall.append(_hallazgo("AVISO", "lme", rel(docs[cod][0]["ruta"]),
                                  f"{cod} tiene archivo pero no figura en la LME (no existe oficialmente)."))


def _verificar_pliegos_lme(lme, docs, archivos, hall):
    """Pliego modular (tipo PG): su «archivo» es la carpeta Technical_Specs; el código y la revisión del conjunto
    figuran en 00_Index_and_Control.md (TECHNICAL_SPECIFICATIONS_GUIDE.md). Su coherencia interna la verifica specification_verifier.py (CAL-011)."""
    pliegos = _indices_pliego(archivos)
    if lme is None:
        return
    for cod, e in sorted(lme.items()):
        aplica_no = e["aplica"].upper().startswith("NO")
        if cod in pliegos:
            if e["rev"] is not None and pliegos[cod] is not None and e["rev"] != pliegos[cod] and not aplica_no:
                hall.append(_hallazgo("ERROR", "revision", "deliverables.md",
                                      f"La LME ({e['id']}) dice Rev {e['rev']} para el pliego {cod} pero su "
                                      f"00_Index_and_Control.md dice Rev {pliegos[cod]}."))
            continue
        if cod not in docs and e["rev"] is not None and not aplica_no:
            hall.append(_hallazgo("AVISO", "lme", "deliverables.md",
                                  f"La LME ({e['id']}) indica Rev {e['rev']} para {cod} pero no hay archivo en el proyecto."))


def _verificar_citas(docs, vigente, md, citas_todos, rel, hall):
    """(b) Citas «CÓDIGO Rev x» entre documentos frente a la revisión vigente. Devuelve cuántas citas se revisaron."""
    sufijo = defaultdict(set)
    for cod in docs:
        sufijo[cod.split("-", 2)[2]].add(cod)
    if citas_todos:
        objetivo = md
    else:
        objetivo = [d["ruta"] for c, l in docs.items() for d in l if d["ext"] == "md" and d["rev"] == vigente[c]]
    n_citas = 0
    for p in objetivo:
        propio = RE_ARCHIVO.match(os.path.basename(p))
        propio = propio.group("codigo") if propio else None
        for n, linea in enumerate(_leer(p).splitlines(), 1):
            if RE_FILA_REV.match(linea):
                continue
            for m in RE_CITA.finditer(linea):
                cod = m.group("codigo").upper()
                if not re.fullmatch(CODIGO, cod):
                    cand = sufijo.get(cod, set())
                    if len(cand) != 1:
                        continue
                    cod = next(iter(cand))
                if cod == propio or cod not in vigente:
                    continue
                n_citas += 1
                cit = m.group("rev").lower()
                if cit == "vigente":
                    continue
                vig = vigente[cod]
                if "." not in cit:
                    if vig.split(".")[0] == cit:
                        continue          # «Rev 00» = designación de entrega de una revisión interna 00.n[.c]
                    ok = False
                else:
                    ok = cit == vig
                if not ok:
                    hall.append(_hallazgo("ERROR", "cita_rev", f"{rel(p)}:{n}",
                                          f"Cita {cod} Rev {m.group('rev')} pero la revisión vigente es {vig}."))
    return n_citas


def _marcas_e_ids(md, archivos_md, rel, hall):
    """(c) Marcas abiertas por documento y (d) IDs citados que no existen. Devuelve (marcas, ids definidos, ids inexistentes)."""
    marcas = {}
    definidos = defaultdict(set)
    citados = defaultdict(lambda: defaultdict(set))    # id -> archivos
    for p, txt in archivos_md.items():
        for linea in txt.splitlines():
            m = re.match(r"^\|\s*`?((?:" + "|".join(TIPOS_ID) + r")-\d{1,4})`?\s*\|", linea)
            if m:
                definidos[m.group(1).split("-")[0]].add(m.group(1))
    for p, txt in archivos_md.items():
        cuenta = defaultdict(int)
        for m in RE_MARCA.finditer(txt):
            t = m.group(1)
            clave = "DEFINIR" if t == "DEFINIR" else "VERIFICAR" if t == "VERIFICAR" else \
                "PENDIENTE INF" if t.startswith("PENDIENTE") else "SUPUESTO"
            cuenta[clave] += 1
        if cuenta:
            marcas[rel(p)] = {**{k: cuenta.get(k, 0) for k in ("DEFINIR", "VERIFICAR", "PENDIENTE INF", "SUPUESTO")},
                              "total": sum(cuenta.values())}
        ids_rango = set()
        for m in RE_RANGO.finditer(txt):
            a, b = int(m.group(2)), int(m.group(3))
            ancho = len(m.group(2))
            if 0 <= b - a <= 200:
                for k in range(a, b + 1):
                    ids_rango.add(f"{m.group(1)}-{str(k).zfill(ancho)}")
        sin_rango = RE_RANGO.sub(" ", txt)
        for m in RE_ID.finditer(sin_rango):
            citados[f"{m.group(1)}-{m.group(2)}"][rel(p)] = True
        for i in ids_rango:
            citados[i][rel(p)] = True
    inexistentes = {}
    for i, fs in sorted(citados.items()):
        tipo = i.split("-")[0]
        if i not in definidos[tipo]:
            inexistentes[i] = sorted(fs)
    for i, fs in inexistentes.items():
        hall.append(_hallazgo("ERROR", "id_inexistente", ", ".join(fs[:3]) + (" ..." if len(fs) > 3 else ""),
                              f"{i} se cita pero no existe en ningún registro del proyecto."))
    return marcas, definidos, inexistentes


def _verificar_formato(md, raiz, archivos_md, rel, hall):
    """(f) Formato Markdown compatible con Pandoc (RG-20): no se verifican los archivos del framework ni Technical_Specs. Devuelve cuántos archivos se revisaron."""
    n_formato = 0
    for p in md:
        nombre = os.path.basename(p)
        if nombre in ARCHIVOS_FRAMEWORK and es_archivo_framework(p, raiz):
            continue
        if CARPETA_PLIEGOS in rel(p).split("/")[:-1]:
            continue
        n_formato += 1
        for sev, cat, linea, msg in comprobar_formato_pandoc(archivos_md[p]):
            hall.append(_hallazgo(sev, cat, f"{rel(p)}:{linea}", msg))
    return n_formato


def _verificar_confidencialidad(md, raiz, archivos_md, definidos, rel, hall):
    """(g) Confidencialidad económica (RG-21): .md del proyecto (no del framework) y el registro y actas de entrada. Devuelve cuántos hallazgos hubo."""
    candidatos = []
    for p in md:
        nombre = os.path.basename(p)
        if nombre in ARCHIVOS_FRAMEWORK and es_archivo_framework(p, raiz):
            continue
        candidatos.append(p)
    entrada = os.path.join(raiz, "01-input")
    if os.path.isdir(entrada):
        for dp, _dn, fn in os.walk(entrada):
            for f in fn:
                if f.lower().endswith(".md") and (f == "_INPUT_REGISTER.md" or f.upper().startswith("MINUTES-")):
                    candidatos.append(os.path.join(dp, f))
    n_econ = 0
    for p in candidatos:
        txt = archivos_md[p] if p in archivos_md else _leer(p)
        for sev, cat, linea, msg, dec in comprobar_confidencialidad(txt):
            if dec is not None:
                if dec in definidos["DEC"]:
                    continue
                msg = f"La excepción cita {dec}, que no existe en los registros. " + msg
            n_econ += 1
            hall.append(_hallazgo(sev, cat, f"{rel(p)}:{linea}", msg))
    return n_econ


def _verificar_charter(raiz, hall):
    """(h) Consistencia charter técnico ↔ charter ejecutivo (A3-19 / A3-20). Devuelve cuántos hallazgos hubo."""
    p_ch = os.path.join(raiz, "02_PROJECT", "project-charter.md")
    p_ex = os.path.join(raiz, "02_PROJECT", "project-charter-executive.md")
    n_charter = 0
    if os.path.isfile(p_ch) and os.path.isfile(p_ex) and "# GUÍA DEL ARCHIVO" not in _leer(p_ex):
        t_ch, t_ex = _leer(p_ch), _leer(p_ex)
        aprobado = "APROBADO" in t_ex[:600].upper()
        for sev, cat, msg in comprobar_charter_ejecutivo(t_ch, t_ex) + comprobar_pdf_ejecutivo(p_ex, t_ex, aprobado):
            n_charter += 1
            hall.append(_hallazgo(sev, cat, "02_PROJECT/project-charter-executive.md", msg))
    return n_charter


def verificar_proyecto(raiz, citas_todos=False):
    """Recorre la carpeta del proyecto y devuelve un dict con hallazgos, marcas y resumen."""
    if not os.path.isdir(raiz):
        raise ValueError(f"No existe la carpeta del proyecto: {raiz}")
    raiz = os.path.abspath(raiz)
    rel = lambda p: os.path.relpath(p, raiz).replace(os.sep, "/")
    hall = []
    lme, nota_lme = _parsear_lme(raiz)

    archivos = list(_recorrer(raiz))
    md = [p for p in archivos if p.lower().endswith(".md")]
    docs = _agrupar_documentos(archivos, rel, hall)
    vigente = _revisiones_vigentes(docs, rel, hall)
    _verificar_coherencia_revision(docs, vigente, lme, rel, hall)
    _verificar_pliegos_lme(lme, docs, archivos, hall)
    n_citas = _verificar_citas(docs, vigente, md, citas_todos, rel, hall)
    archivos_md = {p: _leer(p) for p in md}
    marcas, definidos, inexistentes = _marcas_e_ids(md, archivos_md, rel, hall)
    n_formato = _verificar_formato(md, raiz, archivos_md, rel, hall)
    n_econ = _verificar_confidencialidad(md, raiz, archivos_md, definidos, rel, hall)
    n_charter = _verificar_charter(raiz, hall)
    hall.sort(key=lambda h: (h["severidad"] != "ERROR", h["categoria"], h["archivo"]))
    n_err = sum(1 for h in hall if h["severidad"] == "ERROR")
    return {
        "modulo": "CAL-010", "version": __version__, "carpeta": raiz,
        "nota_lme": nota_lme,
        "resumen": {"archivos_md": len(md), "documentos_con_codigo": len(docs), "citas_rev_revisadas": n_citas,
                    "archivos_formato_revisados": n_formato, "errores": n_err, "avisos": len(hall) - n_err,
                    "marcas_abiertas_total": sum(v["total"] for v in marcas.values()),
                    "ids_inexistentes": len(inexistentes), "hallazgos_confidencialidad": n_econ,
                    "hallazgos_charter_ejecutivo": n_charter},
        "hallazgos": hall, "marcas_por_documento": marcas,
        "registros": {t: len(definidos[t]) for t in TIPOS_ID},
        "documentos_vigentes": {c: vigente[c] for c in sorted(vigente)},
        "aviso": "Ayuda de autocontrol: no reemplaza la auditoría (project-audit.md).",
    }


def generar_markdown(res):
    r = res["resumen"]
    L = ["# Verificación mecánica de documentos (CAL-010)", "",
         "> Ayuda de autocontrol. **No reemplaza la auditoría** (`project-audit.md`).", "",
         f"Carpeta: `{res['carpeta']}`", "",
         "| Indicador | Valor |", "|---|---|",
         f"| Archivos .md revisados | {r['archivos_md']} |",
         f"| Documentos con código | {r['documentos_con_codigo']} |",
         f"| Citas «Rev» revisadas | {r['citas_rev_revisadas']} |",
         f"| Archivos revisados en formato Pandoc | {r['archivos_formato_revisados']} |",
         f"| Errores | {r['errores']} |", f"| Avisos | {r['avisos']} |",
         f"| Marcas abiertas (total) | {r['marcas_abiertas_total']} |",
         f"| IDs citados que no existen | {r['ids_inexistentes']} |",
         f"| Hallazgos de confidencialidad económica (RG-21) | {r['hallazgos_confidencialidad']} |", ""]
    if res["nota_lme"]:
        L += [f"> {res['nota_lme']}", ""]
    L += ["## Hallazgos", ""]
    if res["hallazgos"]:
        L += ["| Severidad | Categoría | Archivo | Detalle |", "|---|---|---|---|"]
        for h in res["hallazgos"]:
            L.append(f"| {h['severidad']} | {h['categoria']} | `{h['archivo']}` | {h['mensaje'].replace('|', '/')} |")
    else:
        L.append("Sin hallazgos.")
    L += ["", "## Marcas abiertas por documento", ""]
    if res["marcas_por_documento"]:
        L += ["| Documento | `[DEFINIR]` | `[VERIFICAR]` | `[PENDIENTE INF-…]` | `[SUPUESTO …]` | Total |",
              "|---|---:|---:|---:|---:|---:|"]
        for d, v in sorted(res["marcas_por_documento"].items()):
            L.append(f"| `{d}` | {v['DEFINIR']} | {v['VERIFICAR']} | {v['PENDIENTE INF']} | {v['SUPUESTO']} | {v['total']} |")
    else:
        L.append("Sin marcas abiertas.")
    L += ["", "## Registros encontrados", "",
          "| Tipo | IDs definidos |", "|---|---:|"]
    L += [f"| {t} | {n} |" for t, n in res["registros"].items()]
    L.append("")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description="CAL-010: verificación mecánica de documentos del proyecto "
                                 "(ayuda de autocontrol; no reemplaza la auditoría).")
    ap.add_argument("carpeta", help="carpeta raíz del proyecto")
    ap.add_argument("--md", help="ruta de salida Markdown (si se omite y no hay --json, va a stdout)")
    ap.add_argument("--json", dest="json_out", help="ruta de salida JSON")
    ap.add_argument("--estricto", action="store_true", help="los avisos también hacen fallar (retorno 1)")
    ap.add_argument("--citas-todos", action="store_true", help="revisar citas «Rev» en todos los .md")
    a = ap.parse_args(argv)
    try:
        res = verificar_proyecto(a.carpeta, a.citas_todos)
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
