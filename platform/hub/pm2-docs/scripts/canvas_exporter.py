#!/usr/bin/env python3
"""CAL-014 · canvas_exporter — Exporta los lienzos de Planificación, Cierre de Fase y Cierre de Proyecto a PDF.

Cada lienzo comparte el mismo lenguaje visual que el charter ejecutivo (CAL-013):
cajas con pestaña azul (#00829b), tipografía Calibri/Inter, fondo blanco, página 1660×1225 px.

Tipos soportados (argumento --tipo):
    planning  → planning_CANVAS.md        → 90-management/charter/planning_CANVAS.pdf
    phase     → PHASE_CANVAS_<fase>.md    → 90-management/charter/PHASE_CANVAS_<fase>.pdf
    closure   → CLOSURE_CANVAS.md         → 90-management/charter/CLOSURE_CANVAS.pdf

Uso:
    python3 -B canvas_exporter.py --tipo planning  MD_RUTA [--pdf RUTA] [--sin-docx]
    python3 -B canvas_exporter.py --tipo phase     MD_RUTA
    python3 -B canvas_exporter.py --tipo closure   MD_RUTA

Salidas: 0 = correcto; 1 = error.
Estado: BORRADOR — pendiente de validación por el usuario.
"""
import hashlib
import html
import json
import os
import re
import sys

__version__ = "0.1.0"

RE_COMENTARIO = re.compile(r"<!--(.*?)-->", re.S)
PENDIENTE = "Pendiente de definir"

# --- Cajas por tipo de canvas -----------------------------------------------------------------------
CAJAS_planning = (
    "Objetivo de la fase",
    "Entregables de la fase",
    "Criterios de aceptación",
    "Hitos de planificación",
    "Paquetes de trabajo",
    "Equipo y recursos",
    "Presupuesto y esfuerzo",
    "Riesgos de planificación",
    "Supuestos",
    "Decisiones requeridas",
    "Criterios de éxito de la fase",
)

CAJAS_PHASE = (
    "Fase cerrada",
    "Entregables completados",
    "Entregables pendientes",
    "Hitos cumplidos",
    "Variaciones",
    "Lecciones aprendidas",
    "Riesgos pendientes",
    "Criterios de aceptación",
    "Aprobación",
)

CAJAS_CLOSURE = (
    "Resumen del proyecto",
    "Logros y beneficios realizados",
    "Entregables finales",
    "Variaciones acumuladas",
    "Hitos del proyecto",
    "Lecciones aprendidas clave",
    "Presupuesto final",
    "Reconocimientos",
    "Aprobación formal",
)


# --- Utilidades comunes ------------------------------------------------------------------------------
def _sin_acentos(s):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower().strip()


def sello_md(texto):
    t = texto.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(t.encode("utf-8")).hexdigest()[:16]


def _limpiar(s):
    s = RE_COMENTARIO.sub("", s)
    return s.replace("`", "").strip()


def _tabla(lineas):
    filas = []
    for l in lineas:
        l = l.strip()
        if not l.startswith("|"):
            continue
        celdas = [c.strip() for c in l.strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", c) for c in celdas):
            continue
        filas.append(celdas)
    return (filas[0], filas[1:]) if filas else ([], [])


def _viñetas(lineas):
    out = []
    for l in lineas:
        m = re.match(r"^\s*[-*]\s+(.*)$", l)
        if m:
            out.append(_limpiar(m.group(1)))
    return out


def _parrafo(lineas):
    return _limpiar(" ".join(l.strip() for l in lineas if l.strip() and not l.strip().startswith("|")))


def _encontrar_raiz(ruta):
    d = os.path.dirname(os.path.abspath(ruta))
    for _ in range(12):
        if os.path.isdir(os.path.join(d, ".project")) or os.path.isdir(os.path.join(d, "90-management")):
            return d
        p = os.path.dirname(d)
        if p == d:
            break
        d = p
    return None


def _ruta_pdf(md_ruta, raiz):
    nombre = os.path.splitext(os.path.basename(md_ruta))[0]
    if raiz:
        charter_dir = os.path.join(raiz, "90-management", "Charter")
        os.makedirs(charter_dir, exist_ok=True)
        return os.path.join(charter_dir, nombre + ".pdf")
    return os.path.splitext(md_ruta)[0] + ".pdf"


def _ruta_docx(md_ruta, raiz):
    nombre = os.path.splitext(os.path.basename(md_ruta))[0]
    if raiz:
        charter_dir = os.path.join(raiz, "90-management", "Charter")
        os.makedirs(charter_dir, exist_ok=True)
        return os.path.join(charter_dir, nombre + ".docx")
    return os.path.splitext(md_ruta)[0] + ".docx"


def _ruta_html(md_ruta, raiz):
    nombre = os.path.splitext(os.path.basename(md_ruta))[0]
    if raiz:
        render_dir = os.path.join(raiz, ".project", "render")
        os.makedirs(render_dir, exist_ok=True)
        return os.path.join(render_dir, nombre + ".html")
    return os.path.splitext(md_ruta)[0] + ".html"


# --- Parser genérico ---------------------------------------------------------------------------------
def parsear(texto, cajas_tipo):
    t = texto.replace("\r\n", "\n")
    # Buscar el inicio (primera línea # o ##)
    for marca in ["# LIENZO ", "## LIENZO "]:
        k = t.find(marca)
        if k >= 0:
            t = t[k:]
            break
    avisos = []
    partes = re.split(r"(?m)^### ", t)
    cab = partes[0].split("\n")
    titulo_canvas = ""
    for l in cab:
        if l.startswith("## ") or l.startswith("# "):
            titulo_canvas = _limpiar(re.sub(r"^#+\s*", "", l))
            break
    h_tab, filas = _tabla(cab)
    valores = dict(zip(h_tab, filas[0])) if filas else {}
    encabezado = {
        "titulo": titulo_canvas,
        "proyecto": _limpiar(valores.get("Proyecto", "")),
        "version": _limpiar(valores.get("Versión", "")),
        "fecha": _limpiar(valores.get("Fecha", "")),
        "estado": _limpiar(valores.get("Estado", "")),
        "fase": _limpiar(valores.get("Fase", "")),
    }
    cajas = {}
    claves = {_sin_acentos(c): c for c in cajas_tipo}
    for p in partes[1:]:
        lineas = p.split("\n")
        nombre = lineas[0].strip()
        c = claves.get(_sin_acentos(nombre))
        if not c:
            avisos.append(f"Caja desconocida «{nombre}»: se ignora.")
            continue
        cajas[c] = {"lineas": lineas[1:]}
    for c in cajas_tipo:
        if c not in cajas:
            avisos.append(f"Falta la caja «{c}».")
    return {"encabezado": encabezado, "cajas": cajas, "avisos": avisos}


# --- HTML helpers ------------------------------------------------------------------------------------
def _e(s):
    s = html.escape(s or "", quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    if s.strip() == "[DEFINIR]":
        return f'<span class="pend">{PENDIENTE}</span>'
    return s.replace("[DEFINIR]", f'<span class="pend">{PENDIENTE}</span>')


def _ul(items):
    if not items:
        return f'<p class="pend">{PENDIENTE}</p>'
    return "<ul>" + "".join(f"<li>{_e(i)}</li>" for i in items) + "</ul>"


def _caja_lineas(d, nombre):
    return d["cajas"].get(nombre, {"lineas": []})["lineas"]


def _caja_ul(d, nombre):
    return _ul(_viñetas(_caja_lineas(d, nombre)))


def _caja_p(d, nombre):
    p = _parrafo(_caja_lineas(d, nombre))
    return f'<p class="big">{_e(p)}</p>' if p else f'<p class="pend">{PENDIENTE}</p>'


def _box(x, y, w, h, tab, cuerpo, tab_b=None, cuerpo_b=None, corte=None, cls=""):
    if tab_b is not None:
        parte = (f'<div class="b1" data-fit style="height:{corte}px">{cuerpo}</div>'
                 f'<div class="b2" data-fit style="top:{corte}px;height:{h - corte - 4}px">{cuerpo_b}</div>')
        punteada = f'<div class="dot" style="top:{corte}px"></div>'
        tb = f'<div class="tab bot">{tab_b}</div>'
    else:
        parte = f'<div class="b1" data-fit style="height:{h - 4}px">{cuerpo}</div>'
        punteada = tb = ""
    return (f'<section class="box {cls}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px">'
            f'<div class="tab top">{tab}</div>{parte}{punteada}{tb}</section>')


# Tabla de variaciones (Variaciones section)
def _tabla_variaciones(d, nombre):
    h, filas = _tabla(_caja_lineas(d, nombre))
    if not filas:
        return f'<p class="pend">{PENDIENTE}</p>'
    rows = []
    rows.append('<table class="var"><tr>' + "".join(f'<th>{html.escape(c)}</th>' for c in h) + '</tr>')
    for f in filas:
        rows.append('<tr>' + "".join(f'<td>{_e(_limpiar(c))}</td>' for c in f) + '</tr>')
    rows.append('</table>')
    return "".join(rows)


CSS_BASE = """
@page{size:1660px 1225px;margin:0}
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:#fff}
body{font-family:'Carlito','Calibri','Inter','Segoe UI',Arial,sans-serif;color:#222;width:1660px;height:1225px;position:relative;overflow:hidden}
.pend{color:#a05a00;font-style:italic;margin:0}
.titulo{position:absolute;left:30px;top:26px;font-size:44px;color:#00829b;font-weight:800;letter-spacing:.5px;line-height:1}
.titulo span{font-weight:300}
.proy{position:absolute;left:1020px;top:28px;width:600px;height:75px;border:2px solid #777;border-radius:18px;padding:8px 14px;font-size:15px;display:flex;flex-wrap:wrap;gap:2px 16px;align-content:center}
.proy .p1{width:100%;font-weight:700;font-size:19px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.proy small{color:#666}
.sub{position:absolute;left:30px;top:110px;width:1600px;font-size:17px;color:#00829b;font-style:italic;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.box{position:absolute;border:2px solid #777;border-radius:28px;background:#fff}
.tab{position:absolute;left:50%;transform:translateX(-50%);background:#fff;border:2px solid #777;border-radius:9px;color:#00829b;font-weight:800;font-size:13.5px;letter-spacing:.3px;padding:1px 14px;white-space:nowrap;z-index:3;line-height:20px}
.tab.top{top:-13px}.tab.bot{bottom:-13px}
.b1,.b2{position:absolute;left:0;right:0;padding:22px 20px 8px;font-size:14px;line-height:1.22;overflow:hidden}
.b2{padding-top:12px;padding-bottom:16px}
.dot{position:absolute;left:0;right:0;border-top:2px dotted #999}
ul{margin:0;padding-left:17px}li{margin:0 0 3px}
h4{margin:0 0 3px;font-size:12px;letter-spacing:1px;color:#444}
.cols{display:flex;gap:10px}.cols>div{flex:1}.vl{flex:0 0 2px!important;background:#777;align-self:stretch}
.big{font-size:18px;font-weight:700;line-height:1.2;margin:4px 0}
.var{border-collapse:collapse;width:100%;font-size:13px}
.var th{background:#00829b;color:#fff;padding:3px 6px;text-align:left;font-size:12px}
.var td{border:1px solid #ccc;padding:3px 6px}
.var tr:nth-child(even) td{background:#f5f5f5}
.badge{display:inline-block;padding:1px 8px;border-radius:10px;font-size:12px;font-weight:700;margin-right:4px}
.badge-verde{background:#d4edda;color:#155724}
.badge-rojo{background:#f8d7da;color:#721c24}
.badge-naranja{background:#fff3cd;color:#856404}
.pie{position:absolute;left:30px;bottom:6px;width:1600px;font-size:10.5px;color:#777;display:flex;justify-content:space-between}
"""

JS_AJUSTE = """
() => {
  const sobrantes = [];
  document.querySelectorAll('[data-fit]').forEach(el => {
    let fs = parseFloat(getComputedStyle(el).fontSize);
    while ((el.scrollHeight > el.clientHeight + 1 || el.scrollWidth > el.clientWidth + 1) && fs > 8.5) {
      fs -= 0.5; el.style.fontSize = fs + 'px';
    }
    if (el.scrollHeight > el.clientHeight + 1) {
      const t = el.parentElement.querySelector('.tab.top').textContent;
      sobrantes.push(t + (el.classList.contains('b2') ? ' (parte inferior)' : ''));
    }
  });
  return sobrantes;
}
"""


def _html_header(cab_proy, e, titulo_label, subtitulo=""):
    partes_label = titulo_label.split("·", 1)
    titulo_html = html.escape(partes_label[0].strip())
    span_html = f' <span>· {html.escape(partes_label[1].strip())}</span>' if len(partes_label) > 1 else ""
    proy_block = (
        f'<div class="proy"><div class="p1">{_e(cab_proy or "[DEFINIR]")}</div>'
        f'<span><small>Versión</small> {_e(e["version"])}</span>'
        f' <span><small>Fecha</small> {_e(e["fecha"])}</span>'
        f' <span><small>Estado</small> {_e(e["estado"])}</span></div>'
    )
    sub_html = f'<div class="sub">{_e(subtitulo)}</div>' if subtitulo else ""
    return (f'<div class="titulo">{titulo_html}{span_html}</div>'
            + proy_block + sub_html)


def _html_pie(nombre_md, sello, version):
    return (f'<div class="pie">'
            f'<span>Fuente: {html.escape(nombre_md)} · sha256:{sello} · Línea base {html.escape(version)}</span>'
            f'<span>Generado con canvas_exporter.py {__version__}</span></div>')


def _html_wrap(titulo_pagina, css_extra, body_items):
    return (f'<!doctype html><html lang="es"><head><meta charset="utf-8">'
            f'<title>{html.escape(titulo_pagina)}</title>'
            f'<style>{CSS_BASE}{css_extra}</style></head><body>'
            + "".join(body_items) + '</body></html>')


# ============================================================================================
# planning CANVAS
# ============================================================================================
CSS_planning = """
.hlabel{position:absolute;left:30px;top:450px;width:36px;height:55px}
.hlabel span{position:absolute;left:-34px;top:12px;width:104px;transform:rotate(-90deg);font-size:11.5px;font-weight:800;color:#00829b;line-height:1.05;text-align:center}
.hit-bar{position:absolute;top:450px;height:55px;left:72px;right:30px;display:flex;gap:6px;align-items:center}
.hit-item{flex:1;height:51px;border:2px solid #00829b;border-radius:8px;padding:4px 8px;font-size:12px;background:#fff;overflow:hidden}
.hit-item b{display:block;color:#00829b;font-size:12.5px;margin-bottom:2px}
.hit-sep{font-size:10px;font-weight:800;color:#00829b;flex:0 0 auto}
"""


def _planning_hitos(d):
    lineas = _caja_lineas(d, "Hitos de planificación")
    items = [_limpiar(m.group(1)) for l in lineas for m in [re.match(r"^\s*[-*]\s+(.*)$", l)] if m]
    if not items:
        h, filas = _tabla(lineas)
        items = [_limpiar(" | ".join(f)) for f in filas if f]
    if not items:
        items = [PENDIENTE]
    out = []
    for i, it in enumerate(items[:8]):
        parts = it.split("|", 1)
        label = parts[0].strip()
        fecha = parts[1].strip() if len(parts) > 1 else ""
        out.append(f'<div class="hit-item"><b>{_e(label)}</b>{_e(fecha)}</div>')
        if i < len(items) - 1 and i < 7:
            out.append('<span class="hit-sep">▶</span>')
    return '<div class="hit-bar">' + "".join(out) + '</div>'


def generar_html_planning(d, sello, nombre_md):
    e = d["encabezado"]
    cab = e["proyecto"] or e["titulo"]
    b = []
    b.append(_html_header(cab, e, "LIENZO DE PLANIFICACIÓN", e.get("fase", "")))
    b.append(_box(27, 150, 453, 285, "OBJETIVO DE LA FASE", _caja_ul(d, "Objetivo de la fase")))
    b.append(_box(487, 150, 503, 285, "ENTREGABLES DE LA FASE", _caja_ul(d, "Entregables de la fase")))
    b.append(_box(996, 150, 319, 285, "CRITERIOS DE ACEPTACIÓN", _caja_ul(d, "Criterios de aceptación")))
    b.append(_box(1322, 150, 311, 285, "SUPUESTOS", _caja_ul(d, "Supuestos")))
    b.append('<div class="hlabel"><span>HITOS DE PLANIFICACIÓN</span></div>')
    b.append(_planning_hitos(d))
    b.append(_box(27, 515, 453, 675, "PAQUETES DE TRABAJO", _caja_ul(d, "Paquetes de trabajo")))
    b.append(_box(487, 515, 503, 320, "EQUIPO Y RECURSOS", _caja_ul(d, "Equipo y recursos")))
    b.append(_box(487, 845, 503, 345, "PRESUPUESTO Y ESFUERZO", _caja_p(d, "Presupuesto y esfuerzo")))
    b.append(_box(996, 515, 319, 380, "RIESGOS DE PLANIFICACIÓN", _caja_ul(d, "Riesgos de planificación"),
                  "DECISIONES REQUERIDAS", _caja_ul(d, "Decisiones requeridas"), 190))
    b.append(_box(1322, 515, 311, 675, "CRITERIOS DE ÉXITO DE LA FASE", _caja_ul(d, "Criterios de éxito de la fase")))
    b.append(_box(996, 900, 319, 290, "VARIACIONES PERMITIDAS", _caja_p(d, "Decisiones requeridas")))
    b.append(_html_pie(nombre_md, sello, e["version"]))
    return _html_wrap(f"Planificación — {cab}", CSS_planning, b)


# ============================================================================================
# PHASE CANVAS
# ============================================================================================
CSS_PHASE = """
.estado-bar{position:absolute;left:30px;top:105px;width:1600px;display:flex;gap:10px;align-items:center;font-size:13px}
.estado-bar .fase-tag{font-weight:800;color:#00829b;font-size:16px}
"""


def _phase_variaciones(d):
    return _tabla_variaciones(d, "Variaciones")


def generar_html_phase(d, sello, nombre_md):
    e = d["encabezado"]
    cab = e["proyecto"] or e["titulo"]
    fase_label = e.get("fase", "") or "FASE"
    b = []
    b.append(_html_header(cab, e, f"LIENZO DE CIERRE DE FASE · {fase_label}"))
    b.append(_box(27, 150, 970, 155, "FASE CERRADA", _caja_p(d, "Fase cerrada")))
    b.append(_box(1004, 150, 625, 155, "APROBACIÓN", _caja_ul(d, "Aprobación")))
    b.append(_box(27, 315, 477, 285, "ENTREGABLES COMPLETADOS", _caja_ul(d, "Entregables completados"),
                  "ENTREGABLES PENDIENTES", _caja_ul(d, "Entregables pendientes"), 148))
    b.append(_box(511, 315, 477, 285, "HITOS CUMPLIDOS", _caja_ul(d, "Hitos cumplidos")))
    b.append(_box(995, 315, 634, 285, "VARIACIONES", _phase_variaciones(d)))
    b.append(_box(27, 610, 477, 570, "LECCIONES APRENDIDAS", _caja_ul(d, "Lecciones aprendidas")))
    b.append(_box(511, 610, 477, 570, "RIESGOS PENDIENTES", _caja_ul(d, "Riesgos pendientes"),
                  "CRITERIOS DE ACEPTACIÓN", _caja_ul(d, "Criterios de aceptación"), 290))
    b.append(_box(995, 610, 634, 570, "ESTADO FINAL", _caja_p(d, "Criterios de aceptación")))
    b.append(_html_pie(nombre_md, sello, e["version"]))
    return _html_wrap(f"Cierre de fase {fase_label} — {cab}", CSS_PHASE, b)


# ============================================================================================
# CLOSURE CANVAS
# ============================================================================================
CSS_CLOSURE = """
.hlabel{position:absolute;left:30px;top:450px;width:36px;height:55px}
.hlabel span{position:absolute;left:-34px;top:12px;width:104px;transform:rotate(-90deg);font-size:11.5px;font-weight:800;color:#00829b;line-height:1.05;text-align:center}
.hit-bar{position:absolute;top:450px;height:55px;left:72px;right:30px;display:flex;gap:6px;align-items:center}
.hit-item{flex:1;height:51px;border:2px solid #00829b;border-radius:8px;padding:4px 8px;font-size:12px;background:#fff;overflow:hidden}
.hit-item b{display:block;color:#00829b;font-size:12.5px;margin-bottom:2px}
.hit-sep{font-size:10px;font-weight:800;color:#00829b;flex:0 0 auto}
"""


def _closure_hitos(d):
    lineas = _caja_lineas(d, "Hitos del proyecto")
    items = [_limpiar(m.group(1)) for l in lineas for m in [re.match(r"^\s*[-*]\s+(.*)$", l)] if m]
    if not items:
        items = [PENDIENTE]
    out = []
    for i, it in enumerate(items[:8]):
        parts = it.split("|", 1)
        label = parts[0].strip()
        fecha = parts[1].strip() if len(parts) > 1 else ""
        out.append(f'<div class="hit-item"><b>{_e(label)}</b>{_e(fecha)}</div>')
        if i < len(items) - 1 and i < 7:
            out.append('<span class="hit-sep">▶</span>')
    return '<div class="hit-bar">' + "".join(out) + '</div>'


def generar_html_closure(d, sello, nombre_md):
    e = d["encabezado"]
    cab = e["proyecto"] or e["titulo"]
    b = []
    b.append(_html_header(cab, e, "LIENZO DE CIERRE DEL PROYECTO"))
    b.append(_box(27, 150, 614, 285, "RESUMEN DEL PROYECTO", _caja_p(d, "Resumen del proyecto")))
    b.append(_box(648, 150, 496, 285, "LOGROS Y BENEFICIOS REALIZADOS", _caja_ul(d, "Logros y beneficios realizados")))
    b.append(_box(1151, 150, 478, 285, "ENTREGABLES FINALES", _caja_ul(d, "Entregables finales")))
    b.append('<div class="hlabel"><span>HITOS DEL PROYECTO</span></div>')
    b.append(_closure_hitos(d))
    b.append(_box(27, 515, 614, 340, "VARIACIONES ACUMULADAS", _tabla_variaciones(d, "Variaciones acumuladas")))
    b.append(_box(648, 515, 496, 340, "LECCIONES APRENDIDAS CLAVE", _caja_ul(d, "Lecciones aprendidas clave")))
    b.append(_box(1151, 515, 478, 340, "PRESUPUESTO FINAL", _caja_p(d, "Presupuesto final"),
                  "RECONOCIMIENTOS", _caja_ul(d, "Reconocimientos"), 170))
    b.append(_box(27, 865, 614, 320, "APROBACIÓN FORMAL", _caja_ul(d, "Aprobación formal")))
    b.append(_box(648, 865, 982, 320, "CRITERIOS DE CIERRE CUMPLIDOS",
                  _caja_ul(d, "Logros y beneficios realizados")))
    b.append(_html_pie(nombre_md, sello, e["version"]))
    return _html_wrap(f"Cierre del proyecto — {cab}", CSS_CLOSURE, b)


# --- Exportación Word (python-docx) -------------------------------------------------------
def _docx_canvas(d, cajas_tipo, docx_ruta, sello, titulo, tipo):
    from docx import Document
    from docx.shared import RGBColor, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    COLOR = RGBColor(0x00, 0x82, 0x9B)
    doc = Document()
    for sec in doc.sections:
        sec.top_margin = Cm(2)
        sec.bottom_margin = Cm(2)
        sec.left_margin = Cm(2.5)
        sec.right_margin = Cm(2.5)

    h0 = doc.add_heading(titulo, level=0)
    h0.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in h0.runs:
        run.font.color.rgb = COLOR

    e = d["encabezado"]
    t = doc.add_table(rows=1, cols=3)
    t.style = "Table Grid"
    celdas = t.rows[0].cells
    celdas[0].text = f"Versión: {e['version']}"
    celdas[1].text = f"Fecha: {e['fecha']}"
    celdas[2].text = f"Estado: {e['estado']}"
    if e.get("fase"):
        doc.add_paragraph(f"Fase: {e['fase']}")
    doc.add_paragraph()

    for nombre in cajas_tipo:
        lineas = d["cajas"].get(nombre, {"lineas": []})["lineas"]
        h2 = doc.add_heading(nombre, level=1)
        for run in h2.runs:
            run.font.color.rgb = COLOR
        viñetas = _viñetas(lineas)
        parrafo = _parrafo(lineas)
        if viñetas:
            for item in viñetas:
                doc.add_paragraph(item, style="List Bullet")
        elif parrafo:
            doc.add_paragraph(parrafo)
        else:
            p = doc.add_paragraph("Pendiente de definir")
            p.runs[0].italic = True

    footer = doc.sections[0].footer
    pf = footer.paragraphs[0]
    pf.text = f"sha256:{sello} · canvas_exporter.py {__version__}"
    pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.save(docx_ruta)


# --- Exportación PDF ----------------------------------------------------------------------------------
def _pdf_con_chromium(html_texto, pdf_ruta, sello, titulo):
    from playwright.sync_api import sync_playwright
    kw = {}
    exe = "/opt/pw-browsers/chromium"
    if os.path.exists(exe):
        kw["executable_path"] = exe
    with sync_playwright() as p:
        nav = p.chromium.launch(**kw)
        pag = nav.new_page(viewport={"width": 1660, "height": 1225})
        pag.set_content(html_texto, wait_until="load")
        sobrantes = pag.evaluate(JS_AJUSTE)
        pag.pdf(path=pdf_ruta, width="1660px", height="1225px", print_background=True,
                prefer_css_page_size=True, margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
        nav.close()
    try:
        from pypdf import PdfReader, PdfWriter
        r = PdfReader(pdf_ruta)
        w = PdfWriter()
        for pg in r.pages:
            w.add_page(pg)
        w.add_metadata({"/Title": titulo, "/Subject": f"sha256:{sello}", "/Producer": f"canvas_exporter {__version__}"})
        with open(pdf_ruta, "wb") as f:
            w.write(f)
    except ImportError:
        pass
    return sobrantes


def _actualizar_seal(raiz, nombre_archivo, sello):
    if not raiz:
        return
    seal_path = os.path.join(raiz, ".project", "SEAL.json")
    try:
        if os.path.exists(seal_path):
            with open(seal_path, encoding="utf-8") as fh:
                data = json.load(fh)
        else:
            data = {"schema": "1.0", "note": "Mantenido por charter/canvas_exporter. No editar.", "files": {}}
        import datetime
        data.setdefault("files", {})[nombre_archivo] = {
            "sha256_16": sello,
            "updated": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        os.makedirs(os.path.dirname(seal_path), exist_ok=True)
        with open(seal_path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
    except Exception:
        pass


# --- API pública --------------------------------------------------------------------------------------
TIPOS = {
    "planning": {"cajas": CAJAS_planning, "generar_html": generar_html_planning, "label": "Lienzo de Planificación"},
    "phase":    {"cajas": CAJAS_PHASE,    "generar_html": generar_html_phase,    "label": "Lienzo de Cierre de Fase"},
    "closure":  {"cajas": CAJAS_CLOSURE,  "generar_html": generar_html_closure,  "label": "Lienzo de Cierre del Proyecto"},
}


def exportar_canvas(tipo, md_ruta, pdf_ruta=None, html_ruta=None, docx_ruta=None, sin_docx=False):
    if tipo not in TIPOS:
        raise ValueError(f"tipo debe ser: {', '.join(TIPOS)}")
    cfg = TIPOS[tipo]

    with open(md_ruta, encoding="utf-8") as f:
        texto = f.read()
    d = parsear(texto, cfg["cajas"])
    sello = sello_md(texto)
    nombre_md = os.path.basename(md_ruta)
    raiz = _encontrar_raiz(md_ruta)

    html_texto = cfg["generar_html"](d, sello, nombre_md)

    pdf_ruta = pdf_ruta or _ruta_pdf(md_ruta, raiz)
    html_ruta = html_ruta or _ruta_html(md_ruta, raiz)
    docx_ruta = docx_ruta or _ruta_docx(md_ruta, raiz)

    e = d["encabezado"]
    cab = e["proyecto"] or e["titulo"]
    fase = e.get("fase", "")
    titulo = f"{cfg['label']} — {cab}" + (f" · {fase}" if fase else "")

    res = {"modulo": "CAL-014", "version": __version__, "tipo": tipo, "md": md_ruta,
           "sello": sello, "avisos": list(d["avisos"]), "sobrantes": [],
           "pdf": None, "html": None, "docx": None}

    # HTML intermedio
    os.makedirs(os.path.dirname(html_ruta), exist_ok=True)
    with open(html_ruta, "w", encoding="utf-8") as f:
        f.write(html_texto)
    res["html"] = html_ruta

    # PDF
    os.makedirs(os.path.dirname(pdf_ruta), exist_ok=True)
    try:
        res["sobrantes"] = _pdf_con_chromium(html_texto, pdf_ruta, sello, titulo)
        res["pdf"] = pdf_ruta
    except Exception as ex:
        res["avisos"].append(f"PDF no generado ({type(ex).__name__}: {ex}); HTML en {html_ruta}")

    # Word
    if not sin_docx:
        os.makedirs(os.path.dirname(docx_ruta), exist_ok=True)
        try:
            _docx_canvas(d, cfg["cajas"], docx_ruta, sello, titulo, tipo)
            res["docx"] = docx_ruta
        except Exception as ex:
            res["avisos"].append(f"Word no generado ({type(ex).__name__}: {ex}). pip install python-docx")

    _actualizar_seal(raiz, nombre_md, sello)
    return res


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="Exporta lienzos PM² a PDF y Word.")
    ap.add_argument("md")
    ap.add_argument("--tipo", required=True, choices=list(TIPOS), help="planning / phase / closure")
    ap.add_argument("--pdf")
    ap.add_argument("--html")
    ap.add_argument("--docx")
    ap.add_argument("--sin-docx", action="store_true")
    a = ap.parse_args(argv)
    if not os.path.isfile(a.md):
        print(f"Error: no existe {a.md}", file=sys.stderr)
        return 1
    res = exportar_canvas(a.tipo, a.md, a.pdf, a.html, a.docx, a.sin_docx)
    print(json.dumps(res, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
