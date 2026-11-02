"""Plantas de prueba diseñadas a mano, con la verdad conocida, para medir el motor.

Cada planta se escribe en `out/planta_prueba/<id>/` de tres maneras y con su verdad:
  - planta.svg  la presentación: hoja A3 a escala 1:100, capas con nombre profesional, color, cotas, notas y rótulo
  - planta.dxf  el CAD: capas A-MUROS-30/15/12, A-PUERTAS, A-VENTANAS... en centímetros
  - planta.png  la planta como una imagen (para el lector de imágenes), con el estilo de dibujo de la planta
  - verdad.json lo que hay: muros con su espesor, puertas, ventanas, huecos y ambientes

Unidades: centímetros, origen arriba a la izquierda, y hacia abajo (el marco del motor).
Espesores: 30 cm muros exteriores de ladrillo, 15 cm muros interiores, 12 cm tabiques.
Cada planta tiene un estilo de muro distinto (relleno, trama, contorno, color, gris con trama cruzada, plano azul) para ver cómo responde el motor a cada uno.

Uso: python scripts/planta_prueba.py [id ...]
"""
import json
import math
import sys
from pathlib import Path

import ezdxf
from PIL import Image, ImageChops, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "out" / "planta_prueba"

# ---- estilos de dibujo -------------------------------------------------------------------------------------------------------------------------------
# muro: relleno por espesor (None = sin relleno), trama (None / "diag" / "cruz"), color de la trama, contorno y su grosor; ambientes, puertas, vidrio, tinta, papel
ESTILOS = {
    "relleno": {"muro": {30: "#2f3439", 15: "#4b535b", 12: "#7a848e"}, "trama": None, "trama_color": None, "contorno": "#22262b", "contorno_px": 1,
                "ambientes": ["#e9eef5", "#dff0f2", "#eeeeea", "#f2efe6", "#f6eadf", "#f4f0e6", "#ebebeb"], "puerta": "#8a5a2b", "vidrio": "#2f7fc1", "tinta": "#22262b", "papel": "#ffffff"},
    "trama": {"muro": {30: "#ffffff", 15: "#ffffff", 12: "#ffffff"}, "trama": "diag", "trama_color": "#1d1d1d", "contorno": "#111111", "contorno_px": 3,
              "ambientes": ["#fbf3e4", "#f7e7d3", "#fdf8ee", "#f3e9dc", "#faf0e1", "#f6ecdf", "#efe6d8"], "puerta": "#333333", "vidrio": "#3a6ea5", "tinta": "#111111", "papel": "#fffdf8"},
    "contorno": {"muro": {30: None, 15: None, 12: None}, "trama": None, "trama_color": None, "contorno": "#000000", "contorno_px": 2,
                 "ambientes": [None] * 8, "puerta": "#000000", "vidrio": "#000000", "tinta": "#000000", "papel": "#ffffff"},
    "color": {"muro": {30: "#b5523b", 15: "#c96f55", 12: "#d99a83"}, "trama": None, "trama_color": None, "contorno": "#6e2a1c", "contorno_px": 2,
              "ambientes": ["#e8f0e3", "#dcebe4", "#eef2e6", "#e3ece0", "#f0f3e8", "#e6efe2", "#dde8d8"], "puerta": "#4f6d3a", "vidrio": "#2f7fc1", "tinta": "#2d3a26", "papel": "#ffffff"},
    "gris_cruz": {"muro": {30: "#cfcfcf", 15: "#d8d8d8", 12: "#e0e0e0"}, "trama": "cruz", "trama_color": "#8f8f8f", "contorno": "#d42a2a", "contorno_px": 2,
                  "ambientes": [None] * 8, "puerta": "#9a9a9a", "vidrio": "#18a8c9", "tinta": "#333333", "papel": "#ffffff"},
    "azul": {"muro": {30: None, 15: None, 12: None}, "trama": "diag", "trama_color": "#1f4e9c", "contorno": "#1f4e9c", "contorno_px": 2,
             "ambientes": ["#f1f5fd"] * 8, "puerta": "#1f4e9c", "vidrio": "#1f4e9c", "tinta": "#1f4e9c", "papel": "#ffffff"},
}

# ---- las plantas ---------------------------------------------------------------------------------------------------------------------------------------
# muros: (id, a, b, espesor) por su eje. aberturas: (id, tipo, muro, posición desde `a`, ancho, bisagra "a"/"b", lado +1/-1 respecto de la normal izquierda (-uy, ux)).
# ambientes: (nombre, (x0, y0, x1, y1) por ejes). mobiliario: ("rect", x0, y0, x1, y1, radio) / ("circ", cx, cy, r).
PLANTAS = {
    "p1": {
        "titulo": "Vivienda con estacionamiento", "estilo": "relleno", "ancho": 1400, "alto": 1000,
        "muros": [("m-n", (0, 0), (1400, 0), 30), ("m-e", (1400, 0), (1400, 1000), 30), ("m-s", (1400, 1000), (0, 1000), 30), ("m-o", (0, 1000), (0, 0), 30),
                  ("m-garaje", (500, 400), (500, 1000), 15), ("m-dorm-s", (0, 400), (500, 400), 15), ("m-dorm-e", (500, 0), (500, 400), 15),
                  ("m-nucleo", (500, 500), (1400, 500), 15), ("m-cocina-o", (900, 0), (900, 500), 15), ("t-bano-s", (500, 250), (900, 250), 12), ("t-deposito", (800, 0), (800, 250), 12)],
        "aberturas": [("P1", "puerta", "m-s", 450, 100, "b", 1), ("P2", "puerta", "m-garaje", 350, 80, "a", 1), ("P3", "puerta", "m-dorm-e", 330, 80, "b", -1),
                      ("P4", "puerta", "t-bano-s", 150, 70, "a", 1), ("P5", "puerta", "t-bano-s", 350, 60, "b", 1), ("P6", "puerta", "m-cocina-o", 380, 80, "a", 1),
                      ("H1", "hueco", "m-nucleo", 200, 100, None, 0), ("H2", "hueco", "m-nucleo", 650, 200, None, 0), ("G1", "porton", "m-s", 1150, 300, None, 0),
                      ("V1", "ventana", "m-n", 250, 150, None, 0), ("V2", "ventana", "m-o", 800, 120, None, 0), ("V3", "ventana", "m-n", 650, 60, None, 0),
                      ("V4", "ventana", "m-n", 1150, 180, None, 0), ("V5", "ventana", "m-e", 250, 120, None, 0), ("V6", "ventana", "m-e", 750, 200, None, 0),
                      ("V7", "ventana", "m-s", 150, 180, None, 0), ("V8", "ventana", "m-o", 300, 100, None, 0)],
        "ambientes": [("DORMITORIO", (0, 0, 500, 400)), ("BAÑO", (500, 0, 800, 250)), ("DEPÓSITO", (800, 0, 900, 250)), ("PASILLO", (500, 250, 900, 500)),
                      ("COCINA", (900, 0, 1400, 500)), ("ESTAR - COMEDOR", (500, 500, 1400, 1000)), ("ESTACIONAMIENTO", (0, 400, 500, 1000))],
        "mobiliario": [("rect", 160, 520, 340, 960, 45), ("rect", 60, 40, 220, 240, 6), ("rect", 310, 30, 470, 85, 0), ("rect", 520, 30, 680, 105, 20),
                       ("rect", 690, 170, 770, 220, 8), ("rect", 930, 30, 1370, 90, 0), ("rect", 960, 620, 1140, 710, 6), ("rect", 560, 880, 780, 960, 12)],
    },
    "p2": {
        "titulo": "Departamento de dos dormitorios", "estilo": "trama", "ancho": 1000, "alto": 800,
        "muros": [("m-n", (0, 0), (1000, 0), 30), ("m-e", (1000, 0), (1000, 800), 30), ("m-s", (1000, 800), (0, 800), 30), ("m-o", (0, 800), (0, 0), 30),
                  ("m-dorm", (600, 0), (600, 800), 15), ("m-dorm-div", (600, 400), (1000, 400), 15),
                  ("t-bano-o", (400, 0), (400, 250), 12), ("t-bano-s", (400, 250), (600, 250), 12), ("t-cocina", (0, 300), (250, 300), 12)],
        "aberturas": [("P1", "puerta", "m-s", 700, 100, "a", 1), ("P2", "puerta", "m-dorm", 300, 80, "b", -1), ("P3", "puerta", "m-dorm", 600, 80, "a", -1),
                      ("P4", "puerta", "t-bano-s", 100, 70, "a", 1),
                      ("V1", "ventana", "m-n", 800, 150, None, 0), ("V2", "ventana", "m-e", 600, 150, None, 0), ("V3", "ventana", "m-s", 200, 120, None, 0),
                      ("V4", "ventana", "m-o", 250, 200, None, 0), ("V5", "ventana", "m-n", 200, 120, None, 0), ("V6", "ventana", "m-n", 500, 60, None, 0)],
        "ambientes": [("COCINA", (0, 0, 400, 300)), ("BAÑO", (400, 0, 600, 250)), ("ESTAR - COMEDOR", (0, 300, 600, 800)), ("DORMITORIO 1", (600, 0, 1000, 400)),
                      ("DORMITORIO 2", (600, 400, 1000, 800))],
        "mobiliario": [("rect", 20, 20, 380, 80, 0), ("rect", 640, 40, 820, 240, 6), ("rect", 640, 560, 800, 760, 6), ("rect", 60, 640, 280, 720, 12),
                       ("circ", 380, 470, 55), ("rect", 430, 20, 580, 90, 18)],
    },
    "p3": {
        "titulo": "Oficinas con pasillo central", "estilo": "contorno", "ancho": 1600, "alto": 900,
        "muros": [("m-n", (0, 0), (1600, 0), 30), ("m-e", (1600, 0), (1600, 900), 30), ("m-s", (1600, 900), (0, 900), 30), ("m-o", (0, 900), (0, 0), 30),
                  ("m-pas-n", (0, 350), (1600, 350), 15), ("m-pas-s", (0, 550), (1600, 550), 15),
                  ("t-n1", (400, 0), (400, 350), 12), ("t-n2", (800, 0), (800, 350), 12), ("t-n3", (1200, 0), (1200, 350), 12),
                  ("t-s1", (400, 550), (400, 900), 12), ("t-s2", (800, 550), (800, 900), 12), ("t-s3", (1200, 550), (1200, 900), 12)],
        "aberturas": [("P0", "puerta", "m-o", 450, 100, "a", 1)] +
                     [(f"PN{i}", "puerta", "m-pas-n", 120 + 400 * i, 80, "a", 1) for i in range(4)] +
                     [(f"PS{i}", "puerta", "m-pas-s", 120 + 400 * i, 80, "a", -1) for i in range(4)] +
                     [(f"VN{i}", "ventana", "m-n", 200 + 400 * i, 180, None, 0) for i in range(4)] +
                     [(f"VS{i}", "ventana", "m-s", 200 + 400 * i, 180, None, 0) for i in range(4)],
        "ambientes": [(f"OFICINA {i + 1}", (400 * i, 0, 400 * (i + 1), 350)) for i in range(4)] + [("PASILLO", (0, 350, 1600, 550))] +
                     [(f"OFICINA {i + 5}", (400 * i, 550, 400 * (i + 1), 900)) for i in range(4)],
        "mobiliario": [("rect", 400 * i + 150, 120, 400 * i + 330, 190, 4) for i in range(4)] + [("rect", 400 * i + 150, 700, 400 * i + 330, 770, 4) for i in range(4)],
    },
    "p4": {
        "titulo": "Casa en L", "estilo": "color", "ancho": 1200, "alto": 1000,
        "muros": [("m-n", (0, 0), (1200, 0), 30), ("m-e", (1200, 0), (1200, 500), 30), ("m-l1", (1200, 500), (600, 500), 30), ("m-l2", (600, 500), (600, 1000), 30),
                  ("m-s", (600, 1000), (0, 1000), 30), ("m-o", (0, 1000), (0, 0), 30),
                  ("m-estar", (600, 0), (600, 500), 15), ("m-dorm-n", (0, 500), (600, 500), 15), ("m-bano-n", (0, 800), (600, 800), 15), ("t-lav", (300, 800), (300, 1000), 12)],
        "aberturas": [("P1", "puerta", "m-n", 900, 100, "a", 1), ("P2", "puerta", "m-dorm-n", 300, 80, "b", 1), ("P3", "puerta", "m-bano-n", 150, 70, "a", 1),
                      ("P4", "puerta", "m-bano-n", 450, 70, "b", 1), ("H1", "hueco", "m-estar", 250, 150, None, 0),
                      ("V1", "ventana", "m-o", 750, 150, None, 0), ("V2", "ventana", "m-e", 250, 150, None, 0), ("V3", "ventana", "m-o", 350, 120, None, 0),
                      ("V4", "ventana", "m-s", 450, 60, None, 0), ("V5", "ventana", "m-l1", 300, 150, None, 0), ("V6", "ventana", "m-l2", 150, 120, None, 0)],
        "ambientes": [("ESTAR", (0, 0, 600, 500)), ("COCINA - COMEDOR", (600, 0, 1200, 500)), ("DORMITORIO", (0, 500, 600, 800)), ("BAÑO", (0, 800, 300, 1000)),
                      ("LAVADERO", (300, 800, 600, 1000))],
        "mobiliario": [("rect", 60, 330, 300, 420, 12), ("rect", 640, 30, 1170, 90, 0), ("rect", 820, 250, 1000, 340, 6), ("rect", 330, 560, 560, 760, 6),
                       ("rect", 30, 900, 200, 970, 18), ("circ", 450, 900, 30)],
    },
    "p5": {
        "titulo": "Local comercial con garaje doble", "estilo": "gris_cruz", "ancho": 1200, "alto": 1200,
        "muros": [("m-n", (0, 0), (1200, 0), 30), ("m-e", (1200, 0), (1200, 1200), 30), ("m-s", (1200, 1200), (0, 1200), 30), ("m-o", (0, 1200), (0, 0), 30),
                  ("m-garaje", (0, 800), (1200, 800), 15), ("m-local", (700, 0), (700, 800), 15),
                  ("t-of-s", (700, 450), (1200, 450), 12), ("t-bano", (950, 450), (950, 800), 12)],
        "aberturas": [("P1", "puerta", "m-garaje", 350, 100, "a", 1), ("P2", "puerta", "m-local", 225, 80, "b", -1), ("P3", "puerta", "t-of-s", 125, 80, "a", 1),
                      ("P4", "puerta", "t-bano", 175, 70, "b", -1), ("G1", "porton", "m-s", 900, 260, None, 0), ("G2", "porton", "m-s", 300, 260, None, 0),
                      ("V1", "ventana", "m-n", 350, 250, None, 0), ("V2", "ventana", "m-n", 950, 150, None, 0), ("V3", "ventana", "m-e", 225, 120, None, 0),
                      ("V4", "ventana", "m-o", 800, 200, None, 0)],
        "ambientes": [("LOCAL", (0, 0, 700, 800)), ("OFICINA", (700, 0, 1200, 450)), ("DEPÓSITO", (700, 450, 950, 800)), ("BAÑO", (950, 450, 1200, 800)),
                      ("GARAJE", (0, 800, 1200, 1200))],
        "mobiliario": [("rect", 150, 860, 330, 1160, 40), ("rect", 750, 860, 930, 1160, 40), ("rect", 60, 60, 640, 140, 0), ("rect", 820, 150, 1060, 230, 4),
                       ("rect", 1120, 700, 1180, 780, 8)],
    },
    "p6": {
        "titulo": "Vivienda con estacionamiento (plano azul)", "estilo": "azul", "ancho": 1400, "alto": 1000, "como": "p1",
    },
}
NOTAS = [
    "Muros exteriores: ladrillo cerámico hueco 18 + revoques, e = 30 cm.",
    "Muros interiores portantes: ladrillo hueco 12 + revoques, e = 15 cm.",
    "Tabiques: placa de yeso doble sobre perfilería, e = 12 cm.",
    "Puertas interiores: placa 0,70 / 0,80 m; acceso principal 1,00 m.",
    "Cotas en metros, a ejes de muros. Niveles: N.P.T. ±0,00.",
]


def plano(pid: str) -> dict:
    p = dict(PLANTAS[pid])
    if "como" in p:
        base = PLANTAS[p["como"]]
        for k in ("muros", "aberturas", "ambientes", "mobiliario"):
            p[k] = base[k]
    return p


# ---- geometría ---------------------------------------------------------------------------------------------------------------------------------------
def muro(p, id_):
    return next(m for m in p["muros"] if m[0] == id_)


def eje(m):
    _, a, b, _ = m
    L = math.dist(a, b)
    u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    return a, u, (-u[1], u[0]), L


def tramos(p, m):
    """Los tramos de un muro entre sus aberturas, por su eje: (t0, t1)."""
    _, _, _, L = eje(m)
    cortes = sorted((pos - w / 2, pos + w / 2) for _, _, mid, pos, w, _, _ in p["aberturas"] if mid == m[0])
    out, t = [], -m[3] / 2
    for c0, c1 in cortes:
        out.append((t, c0))
        t = c1
    out.append((t, L + m[3] / 2))
    return [(a, b) for a, b in out if b - a > 1]


def rect(m, t0, t1):
    a, u, n, _ = eje(m)
    h = m[3] / 2
    q = lambda t, o: (a[0] + u[0] * t + n[0] * o, a[1] + u[1] * t + n[1] * o)     # noqa: E731
    return [q(t0, h), q(t1, h), q(t1, -h), q(t0, -h)]


def en_muro(m, t, o):
    a, u, n, _ = eje(m)
    return (a[0] + u[0] * t + n[0] * o, a[1] + u[1] * t + n[1] * o)


def puerta_geom(p, ab):
    """Bisagra, hoja cerrada y hoja abierta de una puerta: puntos en cm."""
    _, _, mid, pos, w, bis, lado = ab
    m = muro(p, mid)
    _, u, n, _ = eje(m)
    s = -1 if bis == "a" else 1
    t_bis = pos + (w / 2 if bis == "b" else -w / 2)
    hinge = en_muro(m, t_bis, lado * m[3] / 2)
    cerrada = (hinge[0] - s * u[0] * w, hinge[1] - s * u[1] * w)
    abierta = (hinge[0] + lado * n[0] * w, hinge[1] + lado * n[1] * w)
    return hinge, cerrada, abierta, w


def abertura_muro(p, ab):
    return muro(p, ab[2])


# ---- SVG ---------------------------------------------------------------------------------------------------------------------------------------------
OX, OY = 900, 600


def f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def pts(ps):
    return " ".join(f"{f(x + OX)},{f(y + OY)}" for x, y in ps)


def svg(pid: str, p: dict) -> str:
    st = ESTILOS[p["estilo"]]
    tinta = st["tinta"]
    W, H = p["ancho"], p["alto"]
    o = ['<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" width="420mm" height="297mm" viewBox="0 0 4200 2970" '
         'font-family="Helvetica, Arial, sans-serif">', f'<title>{p["titulo"]} - Planta arquitectónica - Esc. 1:100</title>']
    trama = st["trama"]
    defs = '<defs><pattern id="piso" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="#000" stroke-opacity="0.05" stroke-width="1"/></pattern>'
    if trama:
        defs += (f'<pattern id="trama" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="10" stroke="{st["trama_color"]}" stroke-width="1.6"/>'
                 + (f'<line x1="0" y1="0" x2="10" y2="0" stroke="{st["trama_color"]}" stroke-width="1.6"/>' if trama == "cruz" else "") + "</pattern>")
    o.append(defs + "</defs>")
    o.append(f'<rect width="4200" height="2970" fill="{st["papel"]}"/>')

    def capa(nombre, cuerpo):
        o.append(f'<g id="{nombre}" inkscape:groupmode="layer" inkscape:label="{nombre}">{cuerpo}</g>')

    cuerpo = ""
    for i, (nombre, (x0, y0, x1, y1)) in enumerate(p["ambientes"]):
        color = st["ambientes"][i % len(st["ambientes"])]
        if color:
            cuerpo += f'<rect x="{f(x0 + OX)}" y="{f(y0 + OY)}" width="{x1 - x0}" height="{y1 - y0}" fill="{color}"/>'
        cuerpo += f'<rect x="{f(x0 + OX)}" y="{f(y0 + OY)}" width="{x1 - x0}" height="{y1 - y0}" fill="url(#piso)"/>'
    capa("A-AMBIENTES", cuerpo)
    for e in (30, 15, 12):
        cuerpo = ""
        relleno = st["muro"][e] or st["papel"]
        for m in (m for m in p["muros"] if m[3] == e):
            for t0, t1 in tramos(p, m):
                poly = pts(rect(m, t0, t1))
                cuerpo += f'<polygon points="{poly}" fill="{relleno}"/>'
                if trama:
                    cuerpo += f'<polygon points="{poly}" fill="url(#trama)"/>'
                cuerpo += f'<polygon points="{poly}" fill="none" stroke="{st["contorno"]}" stroke-width="{st["contorno_px"] * 1.5}" data-muro="{m[0]}" data-espesor-cm="{e}"/>'
        capa(f"A-MUROS-{e}", cuerpo)
    cuerpo = ""
    for ab in (a for a in p["aberturas"] if a[1] == "puerta"):
        hinge, cerrada, abierta, w = puerta_geom(p, ab)
        cross = (cerrada[0] - hinge[0]) * (abierta[1] - hinge[1]) - (cerrada[1] - hinge[1]) * (abierta[0] - hinge[0])
        sweep = 1 if cross > 0 else 0
        cuerpo += (f'<g id="{ab[0]}"><path d="M{f(cerrada[0] + OX)} {f(cerrada[1] + OY)} A{w} {w} 0 0 {sweep} {f(abierta[0] + OX)} {f(abierta[1] + OY)}" fill="none" '
                   f'stroke="{st["puerta"]}" stroke-width="1.5" stroke-dasharray="8 5"/><line x1="{f(hinge[0] + OX)}" y1="{f(hinge[1] + OY)}" x2="{f(abierta[0] + OX)}" '
                   f'y2="{f(abierta[1] + OY)}" stroke="{st["puerta"]}" stroke-width="5"/></g>')
    for ab in (a for a in p["aberturas"] if a[1] == "porton"):
        m = abertura_muro(p, ab)
        _, _, _, pos, w, _, _ = ab
        a1, a2 = en_muro(m, pos - w / 2, 0), en_muro(m, pos + w / 2, 0)
        cuerpo += f'<line x1="{f(a1[0] + OX)}" y1="{f(a1[1] + OY - 50)}" x2="{f(a2[0] + OX)}" y2="{f(a2[1] + OY - 50)}" stroke="{st["puerta"]}" stroke-width="2" stroke-dasharray="14 8"/>'
    capa("A-PUERTAS", cuerpo)
    cuerpo = ""
    for ab in (a for a in p["aberturas"] if a[1] == "ventana"):
        m = abertura_muro(p, ab)
        _, _, _, pos, w, _, _ = ab
        h = m[3] / 2
        cuerpo += f'<polygon points="{pts([en_muro(m, pos - w / 2, h), en_muro(m, pos + w / 2, h), en_muro(m, pos + w / 2, -h), en_muro(m, pos - w / 2, -h)])}" fill="#ffffff" stroke="{tinta}" stroke-width="2"/>'
        for oo in (-4, 4):
            q1, q2 = en_muro(m, pos - w / 2, oo), en_muro(m, pos + w / 2, oo)
            cuerpo += f'<line x1="{f(q1[0] + OX)}" y1="{f(q1[1] + OY)}" x2="{f(q2[0] + OX)}" y2="{f(q2[1] + OY)}" stroke="{st["vidrio"]}" stroke-width="2"/>'
    capa("A-VENTANAS", cuerpo)
    cuerpo = '<g fill="none" stroke="#6f7780" stroke-width="2">'
    for mob in p["mobiliario"]:
        if mob[0] == "rect":
            _, x0, y0, x1, y1, r = mob
            cuerpo += f'<rect x="{x0 + OX}" y="{y0 + OY}" width="{x1 - x0}" height="{y1 - y0}" rx="{r}"/>'
        else:
            _, cx, cy, r = mob
            cuerpo += f'<circle cx="{cx + OX}" cy="{cy + OY}" r="{r}"/>'
    capa("A-MOBILIARIO", cuerpo + "</g>")
    cuerpo = ""
    for nombre, (x0, y0, x1, y1) in p["ambientes"]:
        area = (x1 - x0) * (y1 - y0) / 10000
        cx, cy = (x0 + x1) / 2 + OX, (y0 + y1) / 2 + OY
        fs = 22 if x1 - x0 > 250 else 15
        cuerpo += (f'<text x="{f(cx)}" y="{f(cy)}" text-anchor="middle" font-size="{fs}" font-weight="700" fill="{tinta}" letter-spacing="1">{nombre}</text>'
                   f'<text x="{f(cx)}" y="{f(cy + fs * 1.3)}" text-anchor="middle" font-size="{fs * 0.8}" fill="{tinta}" fill-opacity="0.7">' + f"{area:.2f} m²".replace(".", ",") + "</text>")
    capa("A-TEXTOS", cuerpo)
    cuerpo = '<g stroke="#9a2f2f" stroke-width="1.5" fill="#9a2f2f" font-size="20">'
    cuerpo += (f'<line x1="{OX}" y1="{OY - 120}" x2="{OX + W}" y2="{OY - 120}"/><line x1="{OX - 120}" y1="{OY}" x2="{OX - 120}" y2="{OY + H}"/>'
               + "".join(f'<line x1="{OX + x - 8}" y1="{OY - 112}" x2="{OX + x + 8}" y2="{OY - 128}" stroke-width="3"/>' for x in (0, W))
               + "".join(f'<line x1="{OX - 128}" y1="{OY + y + 8}" x2="{OX - 112}" y2="{OY + y - 8}" stroke-width="3"/>' for y in (0, H))
               + f'<text x="{OX + W / 2}" y="{OY - 132}" text-anchor="middle" stroke="none">' + f"{W / 100:.2f}".replace(".", ",") + "</text>"
               + f'<text x="{OX - 132}" y="{OY + H / 2}" text-anchor="middle" stroke="none" transform="rotate(-90 {OX - 132} {OY + H / 2})">' + f"{H / 100:.2f}".replace(".", ",") + "</text></g>")
    capa("A-COTAS", cuerpo)
    cuerpo = f'<rect x="60" y="60" width="4080" height="2850" fill="none" stroke="{tinta}" stroke-width="4"/>'
    cuerpo += f'<text x="{OX}" y="{OY + H + 230}" font-size="44" font-weight="700" fill="{tinta}" letter-spacing="3">PLANTA ARQUITECTÓNICA</text>'
    cuerpo += f'<text x="{OX}" y="{OY + H + 280}" font-size="24" fill="{tinta}" fill-opacity="0.7">{p["titulo"]} · Esc. 1:100 · N.P.T. ±0,00</text>'
    for i in range(5):
        cuerpo += f'<rect x="{OX + W - 500 + i * 100}" y="{OY + H + 215}" width="100" height="14" fill="{tinta if i % 2 == 0 else st["papel"]}" stroke="{tinta}" stroke-width="2"/>'
    cuerpo += "".join(f'<text x="{OX + W - 500 + i * 100}" y="{OY + H + 205}" font-size="18" text-anchor="middle" fill="{tinta}">{i}</text>' for i in range(6))
    cuerpo += (f'<g transform="translate({OX + W + 300} {OY + 40})"><circle r="55" fill="none" stroke="{tinta}" stroke-width="3"/><path d="M0 -50 L22 30 L0 15 L-22 30 Z" fill="{tinta}"/>'
               f'<text y="-70" font-size="30" font-weight="700" text-anchor="middle" fill="{tinta}">N</text></g>')
    bx, by = 2700, 1950
    cuerpo += f'<rect x="{bx}" y="{by}" width="1380" height="900" fill="#fafafa" stroke="{tinta}" stroke-width="3"/><text x="{bx + 40}" y="{by + 70}" font-size="30" font-weight="700" fill="{tinta}">NOTAS</text>'
    cuerpo += "".join(f'<text x="{bx + 40}" y="{by + 130 + i * 48}" font-size="22" fill="{tinta}">{i + 1}. {n}</text>' for i, n in enumerate(NOTAS))
    cuerpo += f'<line x1="{bx}" y1="{by + 700}" x2="{bx + 1380}" y2="{by + 700}" stroke="{tinta}" stroke-width="3"/>'
    cuerpo += f'<text x="{bx + 40}" y="{by + 760}" font-size="26" font-weight="700" fill="{tinta}">EPC-291 · {p["titulo"]}</text>'
    cuerpo += f'<text x="{bx + 40}" y="{by + 810}" font-size="22" fill="{tinta}" fill-opacity="0.7">Lámina {pid.upper()} · Formato A3 · Escala 1:100 · Estilo de muro: {p["estilo"]}</text>'
    capa("A-ROTULO", cuerpo)
    o.append("</svg>")
    return "\n".join(o)


# ---- DXF ---------------------------------------------------------------------------------------------------------------------------------------------
def dxf(p: dict, path: Path) -> None:
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 5
    for nombre, color in (("A-MUROS-30", 7), ("A-MUROS-15", 8), ("A-MUROS-12", 9), ("A-PUERTAS", 30), ("A-VENTANAS", 5), ("A-MOBILIARIO", 252), ("A-TEXTOS", 7)):
        doc.layers.add(nombre, color=color)
    msp = doc.modelspace()
    H = p["alto"]
    yup = lambda q: (q[0], H - q[1])                                          # noqa: E731
    for m in p["muros"]:
        for t0, t1 in tramos(p, m):
            msp.add_lwpolyline([yup(q) for q in rect(m, t0, t1)], close=True, dxfattribs={"layer": f"A-MUROS-{m[3]}"})
    for ab in (a for a in p["aberturas"] if a[1] == "puerta"):
        hinge, cerrada, abierta, w = puerta_geom(p, ab)
        h, c, a = yup(hinge), yup(cerrada), yup(abierta)
        ang = lambda q: math.degrees(math.atan2(q[1] - h[1], q[0] - h[0]))   # noqa: E731
        a0, a1 = ang(c), ang(a)
        if (a1 - a0) % 360 > 180:
            a0, a1 = a1, a0
        msp.add_arc(h, w, a0, a1, dxfattribs={"layer": "A-PUERTAS"})
        msp.add_line(h, a, dxfattribs={"layer": "A-PUERTAS"})
    for ab in (a for a in p["aberturas"] if a[1] == "ventana"):
        m = abertura_muro(p, ab)
        _, _, _, pos, w, _, _ = ab
        for oo in (-m[3] / 2, -4, 4, m[3] / 2):
            msp.add_line(yup(en_muro(m, pos - w / 2, oo)), yup(en_muro(m, pos + w / 2, oo)), dxfattribs={"layer": "A-VENTANAS"})
    for nombre, (x0, y0, x1, y1) in p["ambientes"]:
        msp.add_text(nombre, dxfattribs={"layer": "A-TEXTOS", "height": 18}).set_placement(yup(((x0 + x1) / 2 - 60, (y0 + y1) / 2)))
    doc.saveas(path)


# ---- PNG ---------------------------------------------------------------------------------------------------------------------------------------------
def png(p: dict, path: Path, px_por_cm: float = 1.5) -> None:
    st = ESTILOS[p["estilo"]]
    Mg = 120
    W, H = int(p["ancho"] * px_por_cm) + 2 * Mg, int(p["alto"] * px_por_cm) + 2 * Mg
    im = Image.new("RGB", (W, H), st["papel"])
    d = ImageDraw.Draw(im)
    P = lambda q: (Mg + q[0] * px_por_cm, Mg + q[1] * px_por_cm)              # noqa: E731
    for i, (_, (x0, y0, x1, y1)) in enumerate(p["ambientes"]):
        color = st["ambientes"][i % len(st["ambientes"])]
        if color:
            d.rectangle([P((x0, y0)), P((x1, y1))], fill=color)
    polys = [([P(q) for q in rect(m, t0, t1)], m[3]) for m in p["muros"] for t0, t1 in tramos(p, m)]
    for poly, e in polys:
        if st["muro"][e]:
            d.polygon(poly, fill=st["muro"][e])
        else:
            d.polygon(poly, fill=st["papel"])
    if st["trama"]:                                                           # the hatch, only inside the walls
        mask = Image.new("L", (W, H), 0)
        md = ImageDraw.Draw(mask)
        for poly, _ in polys:
            md.polygon(poly, fill=255)
        lines = Image.new("L", (W, H), 0)
        ld = ImageDraw.Draw(lines)
        for k in range(-H, W, 9):
            ld.line([(k, H), (k + H, 0)], fill=255, width=1)
            if st["trama"] == "cruz":
                ld.line([(k, 0), (k + H, H)], fill=255, width=1)
        im.paste(st["trama_color"], mask=ImageChops.multiply(mask, lines))
    for poly, _ in polys:
        d.line(poly + [poly[0]], fill=st["contorno"], width=st["contorno_px"])
    for ab in (a for a in p["aberturas"] if a[1] == "puerta"):
        hinge, cerrada, abierta, w = puerta_geom(p, ab)
        d.line([P(hinge), P(abierta)], fill=st["puerta"], width=3)
        a0 = math.degrees(math.atan2(cerrada[1] - hinge[1], cerrada[0] - hinge[0]))
        a1 = math.degrees(math.atan2(abierta[1] - hinge[1], abierta[0] - hinge[0]))
        if (a1 - a0) % 360 > 180:
            a0, a1 = a1, a0
        r = w * px_por_cm
        c = P(hinge)
        d.arc([c[0] - r, c[1] - r, c[0] + r, c[1] + r], a0, a1, fill=st["puerta"], width=2)
    for ab in (a for a in p["aberturas"] if a[1] == "ventana"):
        m = abertura_muro(p, ab)
        _, _, _, pos, w, _, _ = ab
        for oo, col in ((-m[3] / 2, st["tinta"]), (-4, st["vidrio"]), (4, st["vidrio"]), (m[3] / 2, st["tinta"])):
            d.line([P(en_muro(m, pos - w / 2, oo)), P(en_muro(m, pos + w / 2, oo))], fill=col, width=2)
    gris = (111, 119, 128)
    for mob in p["mobiliario"]:
        if mob[0] == "rect":
            _, x0, y0, x1, y1, r = mob
            d.rounded_rectangle([P((x0, y0)), P((x1, y1))], radius=r * px_por_cm, outline=gris, width=2)
        else:
            _, cx, cy, r = mob
            c = P((cx, cy))
            d.ellipse([c[0] - r * px_por_cm, c[1] - r * px_por_cm, c[0] + r * px_por_cm, c[1] + r * px_por_cm], outline=gris, width=2)
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except OSError:
        font = ImageFont.load_default()
    for nombre, (x0, y0, x1, y1) in p["ambientes"]:
        d.text(P(((x0 + x1) / 2 - len(nombre) * 5, (y0 + y1) / 2)), nombre, fill=st["tinta"], font=font)
    im.save(path)


def verdad(p: dict) -> dict:
    return {"titulo": p["titulo"], "estilo": p["estilo"], "unidades": "cm",
            "muros": [{"id": m[0], "a": m[1], "b": m[2], "espesor_cm": m[3]} for m in p["muros"]],
            "puertas": [{"id": a[0], "muro": a[2], "ancho_cm": a[4]} for a in p["aberturas"] if a[1] == "puerta"],
            "ventanas": [{"id": a[0], "muro": a[2], "ancho_cm": a[4]} for a in p["aberturas"] if a[1] == "ventana"],
            "huecos": [{"id": a[0], "muro": a[2], "ancho_cm": a[4]} for a in p["aberturas"] if a[1] in ("hueco", "porton")],
            "ambientes": [{"nombre": n, "m2": round((r[2] - r[0]) * (r[3] - r[1]) / 10000, 2)} for n, r in p["ambientes"]]}


def main() -> None:
    ids = sys.argv[1:] or list(PLANTAS)
    for pid in ids:
        p = plano(pid)
        out = SALIDA / pid
        out.mkdir(parents=True, exist_ok=True)
        (out / "planta.svg").write_text(svg(pid, p), encoding="utf-8")
        dxf(p, out / "planta.dxf")
        png(p, out / "planta.png")
        (out / "verdad.json").write_text(json.dumps(verdad(p), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{pid}: {p['titulo']} ({p['estilo']}) -> {out}")


if __name__ == "__main__":
    main()
