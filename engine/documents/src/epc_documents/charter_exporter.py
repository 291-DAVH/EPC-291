#!/usr/bin/env python3
"""CAL-013 · charter_exporter — Exporta el charter ejecutivo (Markdown) a PDF de una página y Word.

Lee `project-charter-executive.md` (habitualmente en `.project/data/`), dibuja el lienzo en
HTML + CSS —misma disposición que el *Project Initiation Canvas* de PM²: cajas con pestañas, matriz de
riesgos 5×5, organigrama de gobierno, círculos de partes interesadas e hitos por fase— y lo exporta a PDF
con Chromium (Playwright). Genera también un `.docx` para firma y archivo usando Pandoc.

El HTML intermedio se guarda en `.project/render/` (invisible al usuario).
El PDF y el Word van a `90-management/charter/` (visibles, para lectura y firma).

En el pie del PDF (y en sus metadatos) y en el SEAL.json deja el sello `sha256` del `.md`,
para que la auditoría compruebe que los entregables corresponden al texto vigente.

Uso:
    python3 -B charter_exporter.py MD_RUTA [--pdf RUTA] [--docx RUTA] [--html RUTA]
                                            [--sin-pdf] [--sin-docx] [--solo-html] [--verificar]
    Sin opciones deriva todas las rutas automáticamente desde la raíz del proyecto.
    `--verificar` no genera nada: comprueba que el PDF existente lleva el sello del `.md` actual.

Salidas: 0 = correcto; 1 = error de uso o de formato; 2 = PDF desactualizado (con `--verificar`).
Estado: BORRADOR — pendiente de validación por el usuario.
"""
import hashlib
import html
import json
import math
import os
import re
import subprocess
import sys

__version__ = "0.2.0"

CAJAS = ("Alcance", "Contexto", "Entregables", "Resultados deseados", "Beneficios", "Supuestos",
         "Restricciones y dependencias", "Hitos", "Riesgos", "Gobierno y equipo", "Otras partes interesadas",
         "Presupuesto", "Plazo", "Criterios críticos de éxito", "Factores críticos de éxito",
         "Desglose del trabajo", "Se solicita a la dirección")
PENDIENTE = "Pendiente de definir"
RE_COMENTARIO = re.compile(r"<!--(.*?)-->", re.S)
RE_ID = re.compile(r"\b(?:ALD|EXC|CAC|SUP|RIE|PQ|DEC|INF|CR|rfc)-\d{1,4}\b")
ROLES_GOB = ("AGB", "PSC", "PO", "SP", "BM", "PM", "BIG", "PCT", "PST")
ROLES_TEXTO = {"AGB": "Cuerpo de gobierno", "PSC": "Comité de dirección", "PO": "Propietario del proyecto",
               "SP": "Proveedor de la solución", "BM": "Gerente de negocio", "PM": "Responsable del proyecto",
               "BIG": "Grupo de implementación", "PCT": "Equipo central", "PST": "Equipo de apoyo"}


def _sin_acentos(s):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower().strip()


def sello_md(texto):
    """sha256 (16 primeros hex) del texto con saltos de línea normalizados a LF."""
    t = texto.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(t.encode("utf-8")).hexdigest()[:16]


# --- Raíz del proyecto --------------------------------------------------------------------------------
def _encontrar_raiz(ruta):
    """Sube desde `ruta` hasta encontrar un dir que contenga .project/ o 90-management/; devuelve None si no."""
    d = os.path.dirname(os.path.abspath(ruta))
    for _ in range(12):
        if os.path.isdir(os.path.join(d, ".project")) or os.path.isdir(os.path.join(d, "90-management")):
            return d
        p = os.path.dirname(d)
        if p == d:
            break
        d = p
    return None


def _rutas_por_defecto(md_ruta):
    """Devuelve (pdf_ruta, html_ruta, docx_ruta) derivadas desde la raíz del proyecto."""
    nombre = os.path.splitext(os.path.basename(md_ruta))[0]
    raiz = _encontrar_raiz(md_ruta)
    if raiz:
        charter_dir = os.path.join(raiz, "90-management", "Charter")
        render_dir = os.path.join(raiz, ".project", "render")
        os.makedirs(charter_dir, exist_ok=True)
        os.makedirs(render_dir, exist_ok=True)
        return (
            os.path.join(charter_dir, nombre + ".pdf"),
            os.path.join(render_dir, nombre + ".html"),
            os.path.join(charter_dir, nombre + ".docx"),
        )
    base = os.path.splitext(md_ruta)[0]
    return base + ".pdf", base + ".html", base + ".docx"


# --- Análisis del Markdown ---------------------------------------------------------------------------
def _limpiar(s):
    s = RE_COMENTARIO.sub("", s)
    return s.replace("`", "").strip()


def _ids(s):
    return sorted(set(RE_ID.findall(" ".join(RE_COMENTARIO.findall(s)) + " " + RE_COMENTARIO.sub("", s))))


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


def parsear(texto):
    """Devuelve {'encabezado': {...}, 'cajas': {nombre: {'lineas': [...], 'ids': [...]}}, 'avisos': [...]}."""
    t = texto.replace("\r\n", "\n")
    k = t.find("# LIENZO EJECUTIVO")
    if k >= 0:
        t = t[k:]
    avisos = []
    partes = re.split(r"(?m)^### ", t)
    cab = partes[0].split("\n")
    titulo = ""
    for l in cab:
        if l.startswith("## "):
            titulo = _limpiar(l[3:])
    h, filas = _tabla(cab)
    valores = dict(zip(h, filas[0])) if filas else {}
    frase = ""
    for l in cab:
        m = re.match(r"^\*\*En una frase:\*\*\s*(.*)$", l.strip())
        if m:
            frase = _limpiar(m.group(1))
    encabezado = {"titulo": titulo, "proyecto": _limpiar(valores.get("Proyecto", "")),
                  "version": _limpiar(valores.get("Versión", "")), "fecha": _limpiar(valores.get("Fecha", "")),
                  "estado": _limpiar(valores.get("Estado", "")), "frase": frase}
    cajas = {}
    claves = {_sin_acentos(c): c for c in CAJAS}
    for p in partes[1:]:
        lineas = p.split("\n")
        nombre = lineas[0].strip()
        c = claves.get(_sin_acentos(nombre))
        if not c:
            avisos.append(f"Caja desconocida «{nombre}»: se ignora.")
            continue
        cuerpo = lineas[1:]
        cajas[c] = {"lineas": cuerpo, "ids": _ids("\n".join(cuerpo))}
    for c in CAJAS:
        if c not in cajas:
            avisos.append(f"Falta la caja «{c}».")
    return {"encabezado": encabezado, "cajas": cajas, "avisos": avisos}


# --- Dibujo HTML --------------------------------------------------------------------------------------
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


def _caja(d, nombre):
    return d["cajas"].get(nombre, {"lineas": [], "ids": []})["lineas"]


def _nivel(fila, h):
    try:
        i = h.index("Nivel")
        return int(re.search(r"\d+", fila[i]).group())
    except (ValueError, AttributeError, IndexError):
        try:
            p = int(re.search(r"\d+", fila[h.index("Prob.")]).group())
            im = int(re.search(r"\d+", fila[h.index("Impacto")]).group())
            return p * im
        except (ValueError, AttributeError, IndexError):
            return 0


def riesgos(d):
    h, filas = _tabla(_caja(d, "Riesgos"))
    out = []
    for f in filas:
        r = dict(zip(h, f))
        txt = _limpiar(r.get("Riesgo", ""))
        m = re.match(r"^(RIE-\d+)\s*[·\-–:]\s*(.*)$", txt)
        rid, texto = (m.group(1), m.group(2)) if m else ("", txt)
        try:
            prob = int(re.search(r"\d+", r.get("Prob.", "")).group())
            imp = int(re.search(r"\d+", r.get("Impacto", "")).group())
        except (AttributeError, ValueError):
            prob = imp = 0
        nivel = _nivel(f, h) or prob * imp
        out.append({"id": rid, "texto": texto, "prob": prob, "imp": imp, "nivel": nivel,
                    "accion": _limpiar(r.get("Qué haremos", ""))})
    return out


def _matriz(rs):
    celdas = {}
    for r in rs:
        if 1 <= r["prob"] <= 5 and 1 <= r["imp"] <= 5 and r["id"]:
            celdas.setdefault((r["imp"], r["prob"]), []).append(r["id"].replace("RIE-", ""))
    filas = ['<tr><th class="ax" rowspan="5"><span>IMPACTO</span></th>']
    for i, imp in enumerate(range(5, 0, -1)):
        if i:
            filas.append("<tr>")
        filas.append(f'<th class="n">{imp}</th>')
        for prob in range(1, 6):
            alto = imp * prob >= 15
            ids = celdas.get((imp, prob), [])
            filas.append(f'<td class="{"alto" if alto else ""}">{"<br>".join(ids)}</td>')
        filas.append("</tr>")
    filas.append('<tr><th></th><th></th>' + "".join(f'<th class="n">{p}</th>' for p in range(1, 6)) + "</tr>")
    filas.append('<tr><th></th><th></th><th colspan="5" class="ax2">PROBABILIDAD</th></tr>')
    return '<table class="matriz">' + "".join(filas) + "</table>"


def _lista_riesgos(rs):
    if not rs:
        return f'<p class="pend">{PENDIENTE}</p>'
    out = []
    for r in sorted(rs, key=lambda r: -r["nivel"]):
        nivel = f'<span class="niv {"alto" if r["nivel"] >= 15 else ""}">{r["nivel"]}</span>' if r["nivel"] else ""
        idt = f'<b>{html.escape(r["id"])}</b> · ' if r["id"] else ""
        acc = f'<br><i>→ {_e(r["accion"])}</i>' if r["accion"] else ""
        out.append(f'<li>{nivel}{idt}{_e(r["texto"])}{acc}</li>')
    return '<ul class="rlist">' + "".join(out) + "</ul>"


def _alcance(d):
    h, filas = _tabla(_caja(d, "Alcance"))
    dentro = [_limpiar(f[0]) for f in filas if f and f[0]]
    fuera = [_limpiar(f[1]) for f in filas if len(f) > 1 and f[1]]
    return ('<div class="cols"><div><h4>DENTRO</h4>' + _ul(dentro) + '</div><div class="vl"></div><div><h4>FUERA</h4>'
            + _ul(fuera) + "</div></div>")


def _fases(d):
    h, filas = _tabla(_caja(d, "Hitos"))
    f = filas[0] if filas else []
    nombres = ["Inicio", "Planificación", "Ejecución", "Cierre"]
    marcas = ["LPP", "LPE", "FIN"]
    xs = [(70, 292), (365, 347), (715, 677), (1390, 243)]
    out = []
    for i, n in enumerate(nombres):
        celda = _limpiar(f[i]) if i < len(f) else "[DEFINIR]"
        items = [x.strip() for x in celda.split(" · ") if x.strip()]
        x, w = xs[i]
        out.append(f'<div class="fase f{i}" style="left:{x}px;width:{w}px"><div class="fin"><b>{n}</b><div class="hit">'
                   + "".join(f"<span>{_e(it)}</span>" for it in items) + "</div></div></div>")
        if i < 3:
            out.append(f'<em class="marca" style="left:{xs[i + 1][0] - 8}px">{marcas[i]}</em>')
    return "".join(out)


def _gobierno(d):
    h, filas = _tabla(_caja(d, "Gobierno y equipo"))
    quien = {}
    for f in filas:
        m = re.search(r"\((AGB|PSC|PO|SP|BM|PM|BIG|PCT|PST)\)", f[0] if f else "")
        if m and len(f) > 1:
            quien[m.group(1)] = f[1]

    def org(c, cls=""):
        q = quien.get(c, "[DEFINIR]")
        return (f'<div class="org {cls}"><div><b>{c}</b> {ROLES_TEXTO[c]}</div>'
                f'<div class="who">{_e(_limpiar(q))}</div></div>')
    return ('<div class="gob">' + org("AGB", "agb")
            + '<div class="psc"><div class="r1">' + org("PSC") + '</div><div class="r2">' + org("PO") + org("SP")
            + '</div><div class="r2">' + org("BM") + org("PM") + '</div><div class="r2 g">' + org("BIG") + org("PCT")
            + "</div></div>" + org("PST", "pst") + "</div>")


def _interesados(d):
    h, filas = _tabla(_caja(d, "Otras partes interesadas"))
    lista, puntos = [], []
    radios = {"alta": 34, "media": 58, "baja": 80}
    for i, f in enumerate(filas, 1):
        nombre = _limpiar(f[0]) if f else ""
        interes = _limpiar(f[1]) if len(f) > 1 else ""
        infl = _limpiar(f[2]) if len(f) > 2 else ""
        lista.append(f'<li><b>{i}.</b> {_e(nombre)}'
                     + (f" — {_e(interes)}" if interes else "") + (f" <i>({_e(infl)})</i>" if infl else "") + "</li>")
        r = radios.get(_sin_acentos(infl), 70)
        ang = math.radians(-90 + i * 137.5)
        puntos.append((i, 95 + r * math.cos(ang), 95 + r * math.sin(ang)))
    svg = ('<svg viewBox="0 0 190 190" class="radar"><circle cx="95" cy="95" r="88" class="c3"/>'
           '<circle cx="95" cy="95" r="68" class="c2"/><circle cx="95" cy="95" r="46" class="c1"/>'
           '<circle cx="95" cy="95" r="20" class="c0"/><line x1="95" y1="2" x2="95" y2="188" class="ej"/>'
           '<line x1="2" y1="95" x2="188" y2="95" class="ej"/>'
           + "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="8" class="pt"/>'
                     f'<text x="{x:.1f}" y="{y + 3.5:.1f}" class="pn">{i}</text>' for i, x, y in puntos)
           + '<text x="95" y="98.5" class="pc">P</text></svg>')
    cuerpo = ('<ul class="num">' + "".join(lista) + "</ul>") if lista else f'<p class="pend">{PENDIENTE}</p>'
    return (f'<div class="stk"><div class="stl">{cuerpo}</div>'
            f'<div class="str">{svg}<small>Más cerca del centro, más influencia.</small></div></div>')


def _paquetes(d):
    h, filas = _tabla(_caja(d, "Desglose del trabajo"))
    if not filas:
        return f'<p class="pend">{PENDIENTE}</p>'
    out = []
    for f in filas:
        r = dict(zip(h, f))
        dep = _limpiar(r.get("Depende de", "")) or "—"
        out.append(f'<li><b>{_e(_limpiar(r.get("Paquete", "")))}</b> · {_e(_limpiar(r.get("Qué contiene", "")))}'
                   f' <span class="dep">← {_e(dep)}</span></li>')
    return '<ol class="wbs">' + "".join(out) + "</ol>"


def _parrafo_caja(d, nombre):
    p = _parrafo(_caja(d, nombre))
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


CSS = """
@page{size:1660px 1225px;margin:0}
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:#fff}
body{font-family:'Carlito','Calibri','Inter','Segoe UI',Arial,sans-serif;color:#222;width:1660px;height:1225px;position:relative;overflow:hidden}
.pend{color:#a05a00;font-style:italic;margin:0}
.titulo{position:absolute;left:30px;top:26px;font-size:50px;color:#00829b;font-weight:800;letter-spacing:.5px;line-height:1}
.titulo span{font-weight:300}
.proy{position:absolute;left:995px;top:28px;width:525px;height:75px;border:2px solid #777;border-radius:18px;padding:8px 14px;font-size:15px;display:flex;flex-wrap:wrap;gap:2px 16px;align-content:center}
.proy .p1{width:100%;font-weight:700;font-size:19px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.proy small{color:#666}
.frase{position:absolute;left:30px;top:110px;width:1600px;font-size:17px;color:#00829b;font-style:italic;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.box{position:absolute;border:2px solid #777;border-radius:28px;background:#fff}
.tab{position:absolute;left:50%;transform:translateX(-50%);background:#fff;border:2px solid #777;border-radius:9px;color:#00829b;font-weight:800;font-size:13.5px;letter-spacing:.3px;padding:1px 14px;white-space:nowrap;z-index:3;line-height:20px}
.tab.top{top:-13px}.tab.bot{bottom:-13px}
.b1,.b2{position:absolute;left:0;right:0;padding:22px 20px 8px;font-size:14px;line-height:1.22;overflow:hidden}
.b2{padding-top:12px;padding-bottom:16px}
.dot{position:absolute;left:0;right:0;border-top:2px dotted #999}
ul{margin:0;padding-left:17px}li{margin:0 0 3px}
h4{margin:0 0 3px;font-size:12px;letter-spacing:1px;color:#444}
.cols{display:flex;gap:10px}.cols>div{flex:1}.vl{flex:0 0 2px!important;background:#777;align-self:stretch}
.big{font-size:21px;font-weight:700;line-height:1.2;margin:4px 0}
.hlabel{position:absolute;left:30px;top:470px;width:36px;height:55px}
.hlabel span{position:absolute;left:-34px;top:12px;width:104px;transform:rotate(-90deg);font-size:11.5px;font-weight:800;color:#00829b;line-height:1.05;text-align:center}
.fase{position:absolute;top:470px;height:55px;background:#777;clip-path:polygon(0 0,calc(100% - 26px) 0,100% 50%,calc(100% - 26px) 100%,0 100%,24px 50%)}
.fase.f0{clip-path:polygon(0 0,calc(100% - 26px) 0,100% 50%,calc(100% - 26px) 100%,0 100%)}
.fase.f3{clip-path:polygon(0 0,100% 0,100% 100%,0 100%,24px 50%)}
.fase .fin{position:absolute;inset:2px;background:#fff;padding:3px 30px 2px 34px;font-size:13px;line-height:1.15;overflow:hidden;clip-path:inherit}
.fase.f0 .fin{padding-left:14px}
.fase .fin b{font-size:13.5px}.fase .hit{display:block;font-size:12px;color:#333}.fase .hit span{margin-right:12px;white-space:nowrap}
.marca{position:absolute;top:488px;width:30px;font-size:9.5px;font-style:normal;font-weight:800;color:#00829b;z-index:4;text-align:center;background:#fff;line-height:1}
.matriz{border-collapse:collapse;margin:0 auto}.matriz td{width:52px;height:38px;border:1px dotted #aaa;text-align:center;font-size:10.5px;font-weight:700;line-height:1.05;padding:0}
.matriz td.alto{background:#dcdcdc}.matriz th.n{font-size:12px;font-weight:700;width:20px;text-align:center}
.matriz th.ax span{display:block;transform:rotate(-90deg);font-size:11px;white-space:nowrap;width:12px}.matriz .ax2{font-size:11px;letter-spacing:1px;text-align:center;padding-top:2px}
.rlist{list-style:none;padding:0;margin-top:8px}.rlist li{border-top:1px dotted #aaa;padding:5px 0;font-size:13px}
.niv{display:inline-block;min-width:22px;text-align:center;border:1.5px solid #777;border-radius:6px;font-weight:800;font-size:12px;margin-right:6px}.niv.alto{background:#dcdcdc}
.gob{position:relative;height:100%}
.org{border:1.5px solid #777;border-radius:7px;padding:2px 6px;font-size:11.5px;line-height:1.15;background:#fff;overflow:hidden}
.org b{color:#00829b}.org .who{font-weight:700;font-size:12.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.agb{width:290px;margin:0 auto 8px;text-align:center}
.psc{border:1.5px dotted #888;border-radius:8px;padding:6px;margin-right:36px}
.psc .r1{width:210px;margin:0 auto 6px}.psc .r2{display:flex;gap:8px;margin-bottom:6px}.psc .r2 .org{flex:1}
.pst{position:absolute;right:0;top:36px;width:28px;height:196px;padding:0;display:flex;align-items:center;justify-content:center}
.pst>div{transform:rotate(-90deg);white-space:nowrap;font-size:11px}.pst .who{display:none}
.stk{display:flex;gap:10px;height:100%}.stl{flex:1;overflow:hidden}.str{flex:0 0 190px;text-align:center}.str small{display:block;font-size:11px;color:#666;margin-top:2px}
ul.num{list-style:none;padding:0}ul.num li{margin-bottom:5px}
.radar{width:190px;height:190px}.radar circle{fill:none;stroke:#888;stroke-width:1.5}.radar .c3,.radar .c2,.radar .c0{fill:#fff}.radar .c1{fill:#ebebeb}
.radar .ej{stroke:#999;stroke-dasharray:3 3;stroke-width:1}.radar .pt{fill:#00829b;stroke:none}.radar .pn{fill:#fff;font-size:10px;font-weight:800;text-anchor:middle}
.radar .pc{fill:#00829b;font-size:12px;font-weight:800;text-anchor:middle}
.wbs{margin:0;padding-left:20px}.wbs li{margin-bottom:4px}.dep{color:#00829b;font-size:12px;white-space:nowrap}
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


def generar_html(d, sello):
    e = d["encabezado"]
    rs = riesgos(d)
    cab_proy = e["proyecto"] or e["titulo"]
    b = []
    b.append('<div class="titulo">LIENZO DE INICIO <span>DEL PROYECTO</span></div>')
    b.append(f'<div class="proy"><div class="p1">{_e(cab_proy or "[DEFINIR]")}</div>'
             f'<span><small>Versión</small> {_e(e["version"])}</span> <span><small>Fecha</small> {_e(e["fecha"])}</span> '
             f'<span><small>Estado</small> {_e(e["estado"])}</span></div>')
    if e["frase"]:
        b.append(f'<div class="frase">{_e(e["frase"])}</div>')
    ul = lambda n: _ul(_viñetas(_caja(d, n)))
    b.append(_box(27, 167, 453, 293, "ALCANCE", _alcance(d), "CONTEXTO DEL PROYECTO", ul("Contexto"), 178))
    b.append(_box(487, 167, 503, 293, "ENTREGABLES", ul("Entregables")))
    b.append(_box(996, 167, 316, 293, "RESULTADOS DESEADOS", ul("Resultados deseados"), "BENEFICIOS", ul("Beneficios"), 146))
    b.append(_box(1320, 167, 313, 293, "SUPUESTOS", ul("Supuestos"), "RESTRICCIONES Y DEPENDENCIAS",
                  ul("Restricciones y dependencias"), 146))
    b.append('<div class="hlabel"><span>HITOS POR<br>FASE</span></div>')
    b.append(_fases(d))
    b.append(_box(27, 540, 453, 635, "RIESGOS",
                  '<div style="text-align:center;margin-top:2px">' + _matriz(rs) + "</div>" + _lista_riesgos(rs)))
    b.append(_box(487, 540, 503, 300, "GOBIERNO Y EQUIPO", _gobierno(d)))
    b.append(_box(487, 850, 503, 325, "OTRAS PARTES INTERESADAS", _interesados(d)))
    b.append(_box(996, 540, 316, 380, "PRESUPUESTO", _parrafo_caja(d, "Presupuesto"), "PLAZO", _parrafo_caja(d, "Plazo"), 190))
    b.append(_box(1318, 540, 314, 380, "CRITERIOS CRÍTICOS DE ÉXITO", ul("Criterios críticos de éxito"),
                  "FACTORES CRÍTICOS DE ÉXITO", ul("Factores críticos de éxito"), 190))
    b.append(_box(996, 950, 380, 225, "DESGLOSE DEL TRABAJO", _paquetes(d)))
    b.append(_box(1384, 950, 248, 225, "SE SOLICITA A LA DIRECCIÓN", ul("Se solicita a la dirección")))
    b.append(f'<div class="pie"><span>Fuente: project-charter-executive.md · sha256:{sello} · '
             f'Línea base {html.escape(e["version"])} · {html.escape(e["fecha"])}</span>'
             f'<span>Generado con charter_exporter.py {__version__}</span></div>')
    return ('<!doctype html><html lang="es"><head><meta charset="utf-8">'
            f'<title>Charter ejecutivo — {html.escape(cab_proy)}</title><style>{CSS}</style></head><body>'
            + "".join(b) + "</body></html>")


# --- Exportación PDF -----------------------------------------------------------------------------------
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
        w.add_metadata({"/Title": titulo, "/Subject": f"sha256:{sello}", "/Producer": f"charter_exporter {__version__}"})
        with open(pdf_ruta, "wb") as f:
            w.write(f)
    except ImportError:
        pass
    return sobrantes


# --- Exportación Word (python-docx) -------------------------------------------------------
def _docx_con_python_docx(d, docx_ruta, sello, titulo):
    """Genera un .docx del charter ejecutivo usando python-docx (sin Pandoc)."""
    from docx import Document
    from docx.shared import Pt, RGBColor, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    COLOR = RGBColor(0x00, 0x82, 0x9B)

    doc = Document()
    for sec in doc.sections:
        sec.top_margin = Cm(2)
        sec.bottom_margin = Cm(2)
        sec.left_margin = Cm(2.5)
        sec.right_margin = Cm(2.5)

    # Título
    h = doc.add_heading(titulo, level=0)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in h.runs:
        run.font.color.rgb = COLOR

    # Metadata
    e = d["encabezado"]
    t = doc.add_table(rows=1, cols=3)
    t.style = "Table Grid"
    celdas = t.rows[0].cells
    celdas[0].text = f"Versión: {e['version']}"
    celdas[1].text = f"Fecha: {e['fecha']}"
    celdas[2].text = f"Estado: {e['estado']}"
    doc.add_paragraph()

    if e["frase"]:
        p = doc.add_paragraph(f"\"{e['frase']}\"")
        p.runs[0].italic = True

    # Secciones
    for nombre in CAJAS:
        datos = d["cajas"].get(nombre, {"lineas": []})
        lineas = datos["lineas"]
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

    # Pie con sello
    footer = doc.sections[0].footer
    pf = footer.paragraphs[0]
    pf.text = f"sha256:{sello} · charter_exporter.py {__version__}"
    pf.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.save(docx_ruta)
    return None


# --- SEAL.json -----------------------------------------------------------------------------------------
def _actualizar_seal(raiz, nombre_archivo, sello):
    """Registra el sello en .project/SEAL.json."""
    if not raiz:
        return
    seal_path = os.path.join(raiz, ".project", "SEAL.json")
    try:
        if os.path.exists(seal_path):
            with open(seal_path, encoding="utf-8") as fh:
                data = json.load(fh)
        else:
            data = {"schema": "1.0", "note": "Mantenido por charter_exporter.py. No editar manualmente.", "files": {}}
        import datetime
        data.setdefault("files", {})[nombre_archivo] = {
            "sha256_16": sello,
            "updated": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        os.makedirs(os.path.dirname(seal_path), exist_ok=True)
        with open(seal_path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
    except Exception:
        pass  # no interrumpir el flujo principal si el sello falla


# --- Exportación principal -----------------------------------------------------------------------------
def exportar(md_ruta, pdf_ruta=None, html_ruta=None, docx_ruta=None, solo_html=False, sin_docx=False):
    with open(md_ruta, encoding="utf-8") as f:
        texto = f.read()
    d = parsear(texto)
    sello = sello_md(texto)
    html_texto = generar_html(d, sello)

    raiz = _encontrar_raiz(md_ruta)
    pdf_def, html_def, docx_def = _rutas_por_defecto(md_ruta)

    pdf_ruta = pdf_ruta or pdf_def
    html_ruta = html_ruta or html_def
    docx_ruta = docx_ruta or docx_def

    nombre_base = os.path.basename(md_ruta)
    res = {"modulo": "CAL-013", "version": __version__, "md": md_ruta, "sello": sello,
           "avisos": list(d["avisos"]), "sobrantes": [], "pdf": None, "html": None, "docx": None}

    # HTML intermedio siempre en .project/render/
    os.makedirs(os.path.dirname(html_ruta), exist_ok=True)
    with open(html_ruta, "w", encoding="utf-8") as f:
        f.write(html_texto)
    res["html"] = html_ruta

    if not solo_html:
        titulo = f"Charter ejecutivo — {d['encabezado']['proyecto'] or d['encabezado']['titulo']}"
        os.makedirs(os.path.dirname(pdf_ruta), exist_ok=True)
        try:
            res["sobrantes"] = _pdf_con_chromium(html_texto, pdf_ruta, sello, titulo)
            res["pdf"] = pdf_ruta
        except Exception as ex:
            res["avisos"].append(f"No se pudo generar el PDF ({type(ex).__name__}: {ex}); HTML en {html_ruta}")

        if not sin_docx:
            os.makedirs(os.path.dirname(docx_ruta), exist_ok=True)
            try:
                warn = _docx_con_python_docx(d, docx_ruta, sello, titulo)
                res["docx"] = docx_ruta
                if warn:
                    res["avisos"].append(f"Pandoc (Word): {warn}")
            except Exception as ex:
                res["avisos"].append(
                    f"No se pudo generar el Word ({type(ex).__name__}: {ex}). "
                    "Instalá python-docx: pip install python-docx"
                )

    _actualizar_seal(raiz, nombre_base, sello)
    return res


def sello_de_pdf(pdf_ruta):
    """Devuelve el sello sha256 que lleva el PDF (metadatos o texto del pie), o None."""
    try:
        from pypdf import PdfReader
        r = PdfReader(pdf_ruta)
        s = (r.metadata or {}).get("/Subject", "") or ""
        m = re.search(r"sha256:([0-9a-f]{16})", s)
        if m:
            return m.group(1)
        txt = "\n".join((p.extract_text() or "") for p in r.pages)
        m = re.search(r"sha256:([0-9a-f]{16})", txt)
        return m.group(1) if m else None
    except ImportError:
        pass
    try:
        out = subprocess.run(["pdftotext", pdf_ruta, "-"], capture_output=True, text=True, timeout=30).stdout
        m = re.search(r"sha256:([0-9a-f]{16})", out)
        return m.group(1) if m else None
    except (OSError, subprocess.SubprocessError):
        return None


def verificar(md_ruta, pdf_ruta=None):
    if pdf_ruta is None:
        pdf_ruta, _, _ = _rutas_por_defecto(md_ruta)
    with open(md_ruta, encoding="utf-8") as f:
        esperado = sello_md(f.read())
    if not os.path.exists(pdf_ruta):
        return {"estado": "FALTA_PDF", "esperado": esperado, "pdf": None}
    s = sello_de_pdf(pdf_ruta)
    if s is None:
        return {"estado": "SIN_SELLO", "esperado": esperado, "pdf": None}
    return {"estado": "OK" if s == esperado else "DESACTUALIZADO", "esperado": esperado, "pdf": s}


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="Exporta el charter ejecutivo (.md) a PDF de una página y Word.")
    ap.add_argument("md")
    ap.add_argument("--pdf")
    ap.add_argument("--html")
    ap.add_argument("--docx")
    ap.add_argument("--solo-html", action="store_true")
    ap.add_argument("--sin-docx", action="store_true", help="No generar el .docx")
    ap.add_argument("--verificar", action="store_true")
    a = ap.parse_args(argv)
    if not os.path.isfile(a.md):
        print(f"Error: no existe {a.md}", file=sys.stderr)
        return 1
    if a.verificar:
        r = verificar(a.md, a.pdf)
        print(json.dumps(r, ensure_ascii=False))
        return 0 if r["estado"] == "OK" else 2
    res = exportar(a.md, a.pdf, a.html, a.docx, a.solo_html, a.sin_docx)
    print(json.dumps(res, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
