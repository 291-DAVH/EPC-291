#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CAL-012 · input_converter — Conversión de la información de entrada para poder leerla.

ESTADO: BORRADOR — pendiente de validación por el usuario.

PARA QUÉ SIRVE
    Algunos archivos de `01-input` no se pueden leer bien tal como llegan, por ejemplo
    presentaciones (.pptx, .odp) con imágenes vectoriales o dibujos, o documentos Office antiguos. El PDF
    es el formato más fiable para leerlos. Este script:

    1. Convierte a PDF los archivos Office / OpenDocument (.pptx, .ppt, .odp, .docx, .doc, .odt, .xlsx, .xls,
       .ods, .rtf) con LibreOffice en modo sin pantalla (`soffice --headless`).
    2. Con `--imagenes`, genera una imagen PNG por página de cada PDF (propio o convertido) con `pdftoppm`,
       para poder mirar las páginas cuyo contenido es gráfico y no texto.

    NUNCA modifica ni borra los originales. Las copias se guardan en una carpeta hermana `_convertidos/`
    dentro de la carpeta indicada, con la misma ruta relativa (`_convertidos/01_CONTRACTS_AND_TENDERS/x.pdf`,
    `_convertidos/.../x_paginas/p-01.png`). Claude registra cada copia en `_INPUT_REGISTER.md` como
    «copia de lectura de <original>». Si la copia ya existe y es más nueva que el original, se omite.

REQUISITOS
    Python 3 estándar. LibreOffice (`soffice`, o la ruta en la variable de entorno SOFFICE) para el paso 1 y
    `pdftoppm` (poppler, o la ruta en PDFTOPPM) para `--imagenes`. Si falta una herramienta, el script lo
    informa en el resultado y sigue con lo demás; no falla.

LIMITACIONES
    No hace OCR: un PDF escaneado sigue siendo una imagen (se ve con `--imagenes`, pero no se extrae texto).
    La conversión de LibreOffice puede variar el diseño respecto de Office. No convierte DWG ni DXF.

USO (desde la raíz del proyecto)
    python3 -B 98_LIBRARY/calculations/input_converter.py 01-input [--imagenes] [--dpi 110]
        [--md output.md] [--json output.json]

SALIDA Y CÓDIGO DE RETORNO
    Informe Markdown (salida estándar o `--md`) y JSON (`--json`). Retorno 0 si no hubo fallos de conversión,
    1 si alguno falló, 2 si la carpeta no existe.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys

__version__ = "0.1.0"

EXT_OFFICE = {".pptx", ".ppt", ".odp", ".docx", ".doc", ".odt", ".xlsx", ".xls", ".ods", ".rtf"}
CARPETA_SALIDA = "_convertidos"
TIEMPO_MAX_S = 180


def _herramienta(variable, nombres):
    """Ruta de una herramienta externa: variable de entorno, o la primera de `nombres` que exista en el PATH."""
    v = os.environ.get(variable)
    if v:
        return v if (os.path.isfile(v) or shutil.which(v)) else None
    for n in nombres:
        r = shutil.which(n)
        if r:
            return r
    return None


def _reciente(copia, original):
    return os.path.exists(copia) and os.path.getmtime(copia) >= os.path.getmtime(original)


def _recorrer(raiz):
    for dp, dn, fn in os.walk(raiz):
        dn[:] = sorted(d for d in dn if d != CARPETA_SALIDA and not d.startswith("."))
        for f in sorted(fn):
            yield os.path.join(dp, f)


def convertir_a_pdf(origen, destino_dir, soffice):
    """Convierte un archivo Office a PDF en destino_dir. Devuelve (ruta_pdf|None, mensaje)."""
    os.makedirs(destino_dir, exist_ok=True)
    try:
        r = subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", destino_dir, origen],
                           capture_output=True, text=True, timeout=TIEMPO_MAX_S)
    except subprocess.TimeoutExpired:
        return None, f"tiempo agotado ({TIEMPO_MAX_S} s)"
    except OSError as e:
        return None, f"no se pudo ejecutar LibreOffice: {e}"
    pdf = os.path.join(destino_dir, os.path.splitext(os.path.basename(origen))[0] + ".pdf")
    if r.returncode != 0 or not os.path.exists(pdf):
        return None, (r.stderr or r.stdout or "LibreOffice no generó el PDF").strip()[:200]
    return pdf, "ok"


def pdf_a_imagenes(pdf, destino_dir, pdftoppm, dpi=110):
    """Genera p-01.png, p-02.png... en destino_dir. Devuelve (cantidad, mensaje)."""
    os.makedirs(destino_dir, exist_ok=True)
    try:
        r = subprocess.run([pdftoppm, "-png", "-r", str(dpi), pdf, os.path.join(destino_dir, "p")],
                           capture_output=True, text=True, timeout=TIEMPO_MAX_S)
    except subprocess.TimeoutExpired:
        return 0, f"tiempo agotado ({TIEMPO_MAX_S} s)"
    except OSError as e:
        return 0, f"no se pudo ejecutar pdftoppm: {e}"
    n = len([f for f in os.listdir(destino_dir) if f.lower().endswith(".png")])
    if r.returncode != 0 or n == 0:
        return 0, (r.stderr or "pdftoppm no generó imágenes").strip()[:200]
    return n, "ok"


def procesar(carpeta, imagenes=False, dpi=110):
    if not os.path.isdir(carpeta):
        raise ValueError(f"No existe la carpeta: {carpeta}")
    carpeta = os.path.abspath(carpeta)
    salida = os.path.join(carpeta, CARPETA_SALIDA)
    soffice = _herramienta("SOFFICE", ("soffice", "libreoffice"))
    pdftoppm = _herramienta("PDFTOPPM", ("pdftoppm",))
    items, avisos = [], []
    if imagenes and not pdftoppm:
        avisos.append("pdftoppm no está disponible: no se generaron imágenes de página.")
    for ruta in _recorrer(carpeta):
        ext = os.path.splitext(ruta)[1].lower()
        relativa = os.path.relpath(ruta, carpeta).replace(os.sep, "/")
        reldir = os.path.dirname(relativa)
        pdf = None
        if ext in EXT_OFFICE:
            destino = os.path.join(salida, reldir)
            copia = os.path.join(destino, os.path.splitext(os.path.basename(ruta))[0] + ".pdf")
            if _reciente(copia, ruta):
                items.append({"original": relativa, "accion": "pdf", "estado": "omitido (copia vigente)", "copia": os.path.relpath(copia, carpeta).replace(os.sep, "/")})
                pdf = copia
            elif not soffice:
                items.append({"original": relativa, "accion": "pdf", "estado": "falta LibreOffice", "copia": None})
                continue
            else:
                pdf, msg = convertir_a_pdf(ruta, destino, soffice)
                items.append({"original": relativa, "accion": "pdf", "estado": msg if pdf is None else "convertido",
                              "copia": os.path.relpath(pdf, carpeta).replace(os.sep, "/") if pdf else None})
        elif ext == ".pdf":
            pdf = ruta
        if imagenes and pdf and pdftoppm:
            base = os.path.splitext(os.path.basename(pdf))[0]
            dest_img = os.path.join(salida, reldir, base + "_paginas")
            if os.path.isdir(dest_img) and _reciente(dest_img, pdf) and any(f.endswith(".png") for f in os.listdir(dest_img)):
                items.append({"original": relativa, "accion": "imagenes", "estado": "omitido (copia vigente)", "copia": os.path.relpath(dest_img, carpeta).replace(os.sep, "/")})
            else:
                n, msg = pdf_a_imagenes(pdf, dest_img, pdftoppm, dpi)
                items.append({"original": relativa, "accion": "imagenes", "estado": f"{n} página(s)" if n else msg,
                              "copia": os.path.relpath(dest_img, carpeta).replace(os.sep, "/") if n else None})
    fallos = [i for i in items if i["copia"] is None]
    return {"modulo": "CAL-012", "version": __version__, "carpeta": carpeta,
            "herramientas": {"soffice": soffice, "pdftoppm": pdftoppm},
            "items": items, "avisos": avisos,
            "resumen": {"archivos_procesados": len(items), "fallos": len(fallos)}}


def generar_markdown(res):
    L = ["# Conversión de la información de entrada (CAL-012)", "",
         "> Copias de lectura: los originales no se modifican. Registrarlas en `_INPUT_REGISTER.md`.", "",
         f"Carpeta: `{res['carpeta']}`", "",
         f"Procesados: {res['resumen']['archivos_procesados']} · Fallos: {res['resumen']['fallos']}", ""]
    for a in res["avisos"]:
        L.append(f"> {a}")
    if res["avisos"]:
        L.append("")
    if res["items"]:
        L += ["| Original | Acción | Estado | Copia |", "|---|---|---|---|"]
        for i in res["items"]:
            L.append(f"| `{i['original']}` | {i['accion']} | {i['estado'].replace('|', '/')} | {('`' + i['copia'] + '`') if i['copia'] else '—'} |")
    else:
        L.append("No había archivos para convertir.")
    L.append("")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description="CAL-012: convierte a PDF (y a imágenes) la información de entrada "
                                 "para poder leerla. No modifica los originales.")
    ap.add_argument("carpeta", help="carpeta a procesar (normalmente 01-input)")
    ap.add_argument("--imagenes", action="store_true", help="además, una imagen PNG por página de cada PDF")
    ap.add_argument("--dpi", type=int, default=110, help="resolución de las imágenes (defecto 110)")
    ap.add_argument("--md", help="ruta de salida Markdown")
    ap.add_argument("--json", dest="json_out", help="ruta de salida JSON")
    a = ap.parse_args(argv)
    try:
        res = procesar(a.carpeta, a.imagenes, a.dpi)
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
    return 1 if res["resumen"]["fallos"] else 0


if __name__ == "__main__":
    sys.exit(main())
