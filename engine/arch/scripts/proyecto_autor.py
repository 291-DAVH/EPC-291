"""Proyectos de autoría propia: una lámina técnica por proyecto, cada uno más complejo que el anterior, para ver cómo evoluciona lo aprendido.

La lámina sigue la plantilla técnica:
  - columna derecha solo para notas generales, leyenda y cuadro de superficies; el rótulo vertical abajo a la derecha, integrado a esa columna
  - plantas en la franja superior, de izquierda a derecha de nivel bajo a alto, alineadas con ejes comunes
  - corte y fachada debajo de su planta de origen, compartiendo los ejes verticales
  - axonometría fija abajo a la izquierda
  - título y escala debajo de cada vista, alineados a su borde izquierdo

Salida en `out/proyectos/<id>/`: lamina.svg (A1, 1:100) y, por cada planta, <nivel>.png y <nivel>.dxf (para probar el motor) y motor_<nivel>.json.
Unidades del modelo: centímetros, y hacia abajo (sur). Las plantas reutilizan el formato y el dibujo de `planta_prueba.py`.

Uso: python scripts/proyecto_autor.py [id ...]
"""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import planta_prueba as pp                     # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "out" / "proyectos"
TINTA, PAPEL, GRIS, ROJO, AZUL = "#1f2328", "#ffffff", "#6b7280", "#b42318", "#2f6fb3"
FUENTE = "Helvetica, Arial, sans-serif"

# ---- proyecto 01: casa de dos niveles con terraza ----------------------------------------------------------------------------------------------------
P01 = {
    "id": "01", "titulo": "Casa de dos niveles con terraza", "lamina": "A-101", "complejidad": "2 niveles, escalera, terraza, corte, fachada y axonometría",
    "ejes_x": [("A", 0), ("B", 200), ("C", 400), ("D", 800)], "ejes_y": [("1", 0), ("2", 400), ("3", 750), ("4", 1200)],
    "corte_y": 575,
    "niveles": [
        {"id": "pb", "nombre": "PLANTA BAJA", "z": 0, "alto": 300, "estilo": "relleno", "ancho": 800, "alto_planta": 1200,
         "muros": [("m-n", (0, 0), (800, 0), 30), ("m-e", (800, 0), (800, 1200), 30), ("m-s", (0, 1200), (800, 1200), 30), ("m-o", (0, 0), (0, 1200), 30),
                   ("m-medio", (400, 0), (400, 750), 15), ("m-coc", (0, 400), (400, 400), 15), ("m-frente", (0, 750), (800, 750), 15), ("t-toil", (200, 400), (200, 750), 12)],
         "aberturas": [("P1", "puerta", "m-s", 200, 100, "a", -1), ("P2", "puerta", "m-medio", 250, 80, "a", -1), ("P3", "puerta", "m-frente", 100, 70, "a", -1),
                       ("H1", "hueco", "m-frente", 300, 150, None, 0), ("H2", "hueco", "m-frente", 600, 300, None, 0),
                       ("V1", "ventana", "m-n", 200, 150, None, 0), ("V2", "ventana", "m-n", 600, 200, None, 0), ("V3", "ventana", "m-o", 200, 120, None, 0),
                       ("V4", "ventana", "m-o", 975, 200, None, 0), ("V5", "ventana", "m-e", 375, 150, None, 0), ("V6", "ventana", "m-e", 975, 250, None, 0),
                       ("V7", "ventana", "m-s", 550, 300, None, 0), ("V8", "ventana", "m-o", 575, 60, None, 0)],
         "ambientes": [("COCINA", (0, 0, 400, 400)), ("COMEDOR", (400, 0, 800, 750)), ("TOILETTE", (0, 400, 200, 750)), ("ESCALERA", (200, 400, 400, 750)),
                       ("ESTAR", (0, 750, 800, 1200))],
         "mobiliario": [("rect", 20, 20, 380, 80, 0), ("rect", 20, 80, 80, 380, 0), ("rect", 500, 280, 700, 380, 6), ("rect", 60, 1100, 340, 1180, 12),
                        ("rect", 120, 950, 260, 1030, 6), ("circ", 120, 640, 22)],
         "escalera": (200, 400, 400, 750, "sube")},
        {"id": "pa", "nombre": "PLANTA ALTA", "z": 320, "alto": 280, "estilo": "relleno", "ancho": 800, "alto_planta": 1200,
         "muros": [("m-n", (0, 0), (800, 0), 30), ("m-e", (800, 0), (800, 750), 30), ("m-s", (0, 750), (800, 750), 30), ("m-o", (0, 0), (0, 750), 30),
                   ("m-medio", (400, 0), (400, 750), 15), ("m-dorm", (0, 400), (400, 400), 15), ("t-bano", (200, 400), (200, 750), 12)],
         "aberturas": [("P1", "puerta", "m-dorm", 300, 80, "a", -1), ("P2", "puerta", "m-medio", 600, 80, "b", -1), ("P3", "puerta", "t-bano", 200, 70, "a", 1),
                       ("P4", "puerta", "m-s", 600, 120, "b", -1),
                       ("V1", "ventana", "m-n", 200, 150, None, 0), ("V2", "ventana", "m-n", 600, 200, None, 0), ("V3", "ventana", "m-o", 200, 120, None, 0),
                       ("V4", "ventana", "m-e", 375, 180, None, 0), ("V5", "ventana", "m-o", 575, 60, None, 0)],
         "ambientes": [("DORMITORIO 1", (0, 0, 400, 400)), ("BAÑO", (0, 400, 200, 750)), ("ESCALERA", (200, 400, 400, 750)), ("DORMITORIO 2", (400, 0, 800, 750)),
                       ("TERRAZA", (0, 750, 800, 1200))],
         "mobiliario": [("rect", 60, 40, 220, 240, 6), ("rect", 520, 60, 700, 260, 6), ("rect", 20, 420, 180, 490, 18), ("circ", 100, 680, 22)],
         "escalera": (200, 400, 400, 750, "llega"), "barandas": [((0, 1200), (800, 1200)), ((0, 750), (0, 1200)), ((800, 750), (800, 1200))]},
        {"id": "pt", "nombre": "PLANTA DE AZOTEA", "z": 620, "alto": 240, "estilo": "relleno", "ancho": 800, "alto_planta": 1200,
         "muros": [("t-n", (200, 400), (400, 400), 15), ("t-e", (400, 400), (400, 750), 15), ("t-s", (200, 750), (400, 750), 15), ("t-o", (200, 400), (200, 750), 15)],
         "aberturas": [("P1", "puerta", "t-s", 100, 70, "a", -1)],
         "ambientes": [("SALA DE MÁQUINAS", (200, 400, 400, 750))], "mobiliario": [],
         "azotea": (0, 0, 800, 750), "proyeccion": (0, 750, 800, 1200)},
    ],
    "volumenes": [  # axonometría: (x0, y0, x1, y1, z0, z1)
        (0, 0, 800, 1200, 0, 300), (-20, -20, 820, 1220, 300, 320), (0, 0, 800, 750, 320, 600), (-20, -20, 820, 770, 600, 620),
        (0, 1180, 800, 1200, 320, 420), (0, 750, 20, 1180, 320, 420), (780, 750, 800, 1180, 320, 420), (200, 400, 400, 750, 620, 860)],
    "huecos_fachada": [  # en fachadas: ("s"/"e", desde, hasta, z0, z1)
        ("s", 150, 250, 0, 220), ("s", 400, 700, 90, 230), ("s", 540, 660, 320, 540), ("e", 300, 450, 90, 230), ("e", 850, 1100, 90, 230), ("e", 285, 465, 410, 550)],
    "notas": [
        "Muros exteriores de ladrillo cerámico hueco 18 cm + revoques, e = 30 cm.",
        "Muros interiores portantes ladrillo hueco 12 cm, e = 15 cm.",
        "Tabiques sanitarios de placa de yeso doble, e = 12 cm.",
        "Losas de H°A° e = 20 cm. Azotea transitable con pendiente 2 %.",
        "Escalera de H°A°, 14 alzadas de 22,9 cm y huellas de 25 cm.",
        "Cotas en metros a ejes. Niveles referidos a N.P.T. ±0,00.",
        "Baranda de terraza: mampostería h = 1,00 m sobre N.P.T. +3,20.",
    ],
}
PROYECTOS = {"01": P01}

# ---- lámina A1 (mm) ----------------------------------------------------------------------------------------------------------------------------------
HOJA = (841, 594)
COL_NOTAS = 650                       # comienza la columna derecha
ESC = 0.1                             # 1:100 -> 1 cm del modelo = 0,1 mm de lámina
FILA_PLANTAS = 60                     # borde superior de las plantas (y del eje 1)
X_PLANTAS = [70, 255, 440]            # borde izquierdo (eje A) de cada planta
SUELO_CORTES = 345                    # línea de N.P.T. ±0,00 en corte y fachada


def f(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def texto(x, y, t, tam=2.2, peso="400", color=TINTA, ancla="start", extra=""):
    return f'<text x="{f(x)}" y="{f(y)}" font-family="{FUENTE}" font-size="{f(tam)}" font-weight="{peso}" fill="{color}" text-anchor="{ancla}" {extra}>{t}</text>'


def burbuja(x, y, t):
    return f'<circle cx="{f(x)}" cy="{f(y)}" r="3.2" fill="{PAPEL}" stroke="{TINTA}" stroke-width="0.25"/>' + texto(x, y + 1.0, t, 2.8, "700", TINTA, "middle")


def titulo_vista(x, y, nombre, escala):
    """Título y escala debajo de la vista, alineado a su borde izquierdo."""
    numero, _, resto = nombre.partition(". ")
    return (f'<circle cx="{f(x + 3)}" cy="{f(y - 1.2)}" r="3.2" fill="{TINTA}"/>' + texto(x + 3, y, numero, 2.8, "700", PAPEL, "middle") +
            texto(x + 8, y, resto, 3.6, "700") + f'<line x1="{f(x + 8)}" y1="{f(y + 1.6)}" x2="{f(x + 70)}" y2="{f(y + 1.6)}" stroke="{TINTA}" stroke-width="0.35"/>' +
            texto(x + 8, y + 5.5, escala, 2.4, "400", GRIS))


# ---- planta ------------------------------------------------------------------------------------------------------------------------------------------
def planta(nivel: dict, ox: float, oy: float, proyecto: dict, numero: int) -> str:
    """Una planta a 1:100: ambientes, muros por espesor, aberturas, escalera, mobiliario, textos, ejes y corte."""
    p = {k: nivel[k] for k in ("muros", "aberturas", "ambientes", "mobiliario")}
    s = [f'<g id="PLANTA-{nivel["id"].upper()}" transform="translate({f(ox)} {f(oy)}) scale({ESC})">']
    colores = ["#eef2f6", "#f4efe6", "#e3eff1", "#efedf5", "#f2f2ec", "#eaf1e8"]
    if "azotea" in nivel:                                                          # azotea: losa con pendiente y proyección de la terraza
        x0, y0, x1, y1 = nivel["azotea"]
        s.append(f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" fill="#f1f3f5" stroke="{TINTA}" stroke-width="5"/>'
                 f'<rect x="{x0 + 15}" y="{y0 + 15}" width="{x1 - x0 - 30}" height="{y1 - y0 - 30}" fill="none" stroke="{TINTA}" stroke-width="2"/>')
        for k in range(1, 4):
            s.append(f'<line x1="{x0 + 200 * k}" y1="{y0 + 40}" x2="{x0 + 200 * k}" y2="{y1 - 40}" stroke="{GRIS}" stroke-width="1.5" stroke-dasharray="20 12"/>')
        s.append(f'<path d="M560 260 L700 260 M680 248 L700 260 L680 272" fill="none" stroke="{TINTA}" stroke-width="2.5"/>' + texto(565, 250, "PEND. 2 %", 20, "700"))
        x0, y0, x1, y1 = nivel["proyeccion"]
        s.append(f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" fill="none" stroke="{GRIS}" stroke-width="2" stroke-dasharray="25 15"/>'
                 + texto((x0 + x1) / 2, (y0 + y1) / 2, "PROYECCIÓN TERRAZA", 20, "400", GRIS, "middle"))
    for i, (nombre, (x0, y0, x1, y1)) in enumerate(p["ambientes"]):
        if nombre == "TERRAZA":
            s.append(f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" fill="#f6f1e7"/>')
            s.extend(f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="#d8cdb8" stroke-width="1.5"/>' for y in range(y0 + 50, y1, 50))
        elif "azotea" not in nivel:
            s.append(f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" fill="{colores[i % len(colores)]}"/>')
    for m in p["muros"]:                                                           # muros cortados: relleno según espesor, contorno grueso
        relleno = {30: "#2b3036", 15: "#565e67", 12: "#8a939c"}[m[3]]
        for t0, t1 in pp.tramos(p, m):
            s.append(f'<polygon points="{" ".join(f"{f(x)},{f(y)}" for x, y in pp.rect(m, t0, t1))}" fill="{relleno}" stroke="{TINTA}" stroke-width="3"/>')
    for a, b in nivel.get("barandas", []):                                        # baranda: muro bajo en línea media, sin cortar
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        nx, ny = -dy / L * 7.5, dx / L * 7.5
        s.append(f'<polygon points="{f(a[0] + nx)},{f(a[1] + ny)} {f(b[0] + nx)},{f(b[1] + ny)} {f(b[0] - nx)},{f(b[1] - ny)} {f(a[0] - nx)},{f(a[1] - ny)}" fill="{PAPEL}" stroke="{TINTA}" stroke-width="2.5"/>')
    if "escalera" in nivel:
        x0, y0, x1, y1, modo = nivel["escalera"]
        s.append(f'<rect x="{x0 + 15}" y="{y0 + 10}" width="{x1 - x0 - 30}" height="{y1 - y0 - 20}" fill="{PAPEL}" stroke="{TINTA}" stroke-width="2"/>')
        paso = (y1 - y0 - 20) / 14
        for k in range(1, 14):
            y = y0 + 10 + k * paso
            s.append(f'<line x1="{x0 + 15}" y1="{f(y)}" x2="{x1 - 15}" y2="{f(y)}" stroke="{TINTA}" stroke-width="1.5"/>')
        cx = (x0 + x1) / 2
        s.append(f'<path d="M{cx} {y1 - 20} L{cx} {y0 + 30} M{cx - 10} {y0 + 48} L{cx} {y0 + 30} L{cx + 10} {y0 + 48}" fill="none" stroke="{ROJO}" stroke-width="2.5"/>')
        s.append(texto(cx + 14, y1 - 30, "S" if modo == "sube" else "B", 22, "700", ROJO))
        if modo == "sube":                                                         # línea de corte de la escalera en el plano de corte
            s.append(f'<line x1="{x0 + 15}" y1="{y0 + 200}" x2="{x1 - 15}" y2="{y0 + 160}" stroke="{TINTA}" stroke-width="2.5"/>')
    for ab in (a for a in p["aberturas"] if a[1] == "puerta"):
        hinge, cerrada, abierta, w = pp.puerta_geom(p, ab)
        cross = (cerrada[0] - hinge[0]) * (abierta[1] - hinge[1]) - (cerrada[1] - hinge[1]) * (abierta[0] - hinge[0])
        s.append(f'<path d="M{f(cerrada[0])} {f(cerrada[1])} A{w} {w} 0 0 {1 if cross > 0 else 0} {f(abierta[0])} {f(abierta[1])}" fill="none" stroke="{TINTA}" stroke-width="1.2" stroke-dasharray="10 6"/>'
                 f'<line x1="{f(hinge[0])}" y1="{f(hinge[1])}" x2="{f(abierta[0])}" y2="{f(abierta[1])}" stroke="{TINTA}" stroke-width="4"/>')
    for ab in (a for a in p["aberturas"] if a[1] == "ventana"):
        m = pp.muro(p, ab[2])
        _, _, _, pos, w, _, _ = ab
        h = m[3] / 2
        marco = [pp.en_muro(m, pos - w / 2, h), pp.en_muro(m, pos + w / 2, h), pp.en_muro(m, pos + w / 2, -h), pp.en_muro(m, pos - w / 2, -h)]
        s.append(f'<polygon points="{" ".join(f"{f(x)},{f(y)}" for x, y in marco)}" fill="{PAPEL}" stroke="{TINTA}" stroke-width="2"/>')
        for o in (-3, 3):
            q1, q2 = pp.en_muro(m, pos - w / 2, o), pp.en_muro(m, pos + w / 2, o)
            s.append(f'<line x1="{f(q1[0])}" y1="{f(q1[1])}" x2="{f(q2[0])}" y2="{f(q2[1])}" stroke="{AZUL}" stroke-width="1.2"/>')
    for mob in p["mobiliario"]:
        if mob[0] == "rect":
            _, x0, y0, x1, y1, r = mob
            s.append(f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" rx="{r}" fill="none" stroke="{GRIS}" stroke-width="1.5"/>')
        else:
            s.append(f'<circle cx="{mob[1]}" cy="{mob[2]}" r="{mob[3]}" fill="none" stroke="{GRIS}" stroke-width="1.5"/>')
    for nombre, (x0, y0, x1, y1) in p["ambientes"]:
        if nombre == "ESCALERA":
            continue
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        tam = 22 if x1 - x0 >= 300 else 16
        s.append(texto(cx, cy, nombre, tam, "700", TINTA, "middle") + texto(cx, cy + tam * 1.25, f"{(x1 - x0) * (y1 - y0) / 1e4:.2f} m²".replace(".", ","), tam * 0.8, "400", GRIS, "middle"))
    s.append("</g>")
    # ejes comunes y corte (en mm de lámina)
    W, H = nivel["ancho"], nivel["alto_planta"]
    for nombre, x in proyecto["ejes_x"]:
        X = ox + x * ESC
        s.append(f'<line x1="{f(X)}" y1="{f(oy - 14)}" x2="{f(X)}" y2="{f(oy + H * ESC + 10)}" stroke="{GRIS}" stroke-width="0.18" stroke-dasharray="6 1.5 1 1.5"/>' + burbuja(X, oy - 17.5, nombre))
    for nombre, y in proyecto["ejes_y"]:
        Y = oy + y * ESC
        s.append(f'<line x1="{f(ox - 14)}" y1="{f(Y)}" x2="{f(ox + W * ESC + 10)}" y2="{f(Y)}" stroke="{GRIS}" stroke-width="0.18" stroke-dasharray="6 1.5 1 1.5"/>' + burbuja(ox - 17.5, Y, nombre))
    Y = oy + proyecto["corte_y"] * ESC
    for X, lado in ((ox - 8, -1), (ox + W * ESC + 8, 1)):
        s.append(f'<line x1="{f(X - 3)}" y1="{f(Y)}" x2="{f(X + 3)}" y2="{f(Y)}" stroke="{ROJO}" stroke-width="0.6"/>'
                 f'<path d="M{f(X)} {f(Y)} L{f(X)} {f(Y - 4)} L{f(X - 1.2)} {f(Y - 2.6)}" fill="none" stroke="{ROJO}" stroke-width="0.4"/>' + texto(X, Y + 3.6, "A", 2.6, "700", ROJO, "middle"))
    xs = [x for _, x in proyecto["ejes_x"]]                                       # cotas entre ejes, arriba
    cy = oy - 6
    for a, b in zip(xs, xs[1:]):
        s.append(f'<line x1="{f(ox + a * ESC)}" y1="{f(cy)}" x2="{f(ox + b * ESC)}" y2="{f(cy)}" stroke="{ROJO}" stroke-width="0.15"/>'
                 + texto(ox + (a + b) / 2 * ESC, cy - 0.8, f"{(b - a) / 100:.2f}".replace(".", ","), 1.8, "400", ROJO, "middle"))
    s.append(titulo_vista(ox - 14, oy + H * ESC + 22, f"{numero}. {nivel['nombre']}", "ESC. 1:100"))
    return "".join(s)


# ---- corte y fachada ---------------------------------------------------------------------------------------------------------------------------------
def cortes(proyecto: dict, ox: float) -> str:
    """Corte A-A por y = corte_y, mirando al norte: x en horizontal, alineado con los ejes de la planta de arriba."""
    yc = proyecto["corte_y"]
    s = [f'<g id="CORTE-AA">']
    Z = lambda z: SUELO_CORTES - z * ESC                                          # noqa: E731
    X = lambda x: ox + x * ESC                                                    # noqa: E731
    s.append(f'<rect x="{f(X(-60))}" y="{f(Z(0))}" width="{f(92)}" height="5" fill="url(#tierra)"/><line x1="{f(X(-60))}" y1="{f(Z(0))}" x2="{f(X(860))}" y2="{f(Z(0))}" stroke="{TINTA}" stroke-width="0.6"/>')
    for nivel in proyecto["niveles"]:
        for m in nivel["muros"]:
            (ax, ay), (bx, by) = m[1], m[2]
            if ax == bx and min(ay, by) <= yc <= max(ay, by):                    # muro cortado: banda llena hasta la losa siguiente
                corte = next((ab for ab in nivel["aberturas"] if ab[2] == m[0] and abs(min(ay, by) + ab[3] - yc) < ab[4] / 2), None)
                z0, z1 = nivel["z"], nivel["z"] + nivel["alto"]
                macizo = [(z0, z1)] if corte is None else [(z0, z0 + 90), (z0 + 230, z1)] if corte[1] == "ventana" else [(z0 + 220, z1)]
                for a, b in macizo:                                                  # what the opening leaves of the wall: sill and lintel, or just the lintel over a door
                    s.append(f'<rect x="{f(X(ax - m[3] / 2))}" y="{f(Z(b))}" width="{f(m[3] * ESC)}" height="{f((b - a) * ESC)}" fill="{TINTA}"/>')
                if corte is not None and corte[1] == "ventana":
                    for dx in (-3, 3):
                        s.append(f'<line x1="{f(X(ax + dx))}" y1="{f(Z(z0 + 230))}" x2="{f(X(ax + dx))}" y2="{f(Z(z0 + 90))}" stroke="{AZUL}" stroke-width="0.25"/>')
        if nivel["id"] in ("pb", "pa"):
            zl = nivel["z"] + nivel["alto"]                                       # losa superior cortada
            s.append(f'<rect x="{f(X(-20))}" y="{f(Z(zl + 20))}" width="{f(84)}" height="2" fill="{TINTA}"/>')
    s.append(f'<rect x="{f(X(200))}" y="{f(Z(880))}" width="{f(20 + 0.0)}" height="2" fill="{TINTA}"/>'.replace('width="20"', f'width="{f(20.0 * 1)}"'))
    s.append(f'<rect x="{f(X(185))}" y="{f(Z(880))}" width="{f(23)}" height="2" fill="{TINTA}"/>')
    s.append(f'<rect x="{f(X(-20))}" y="{f(Z(660))}" width="{f(3.5)}" height="{f(4)}" fill="{TINTA}"/><rect x="{f(X(785))}" y="{f(Z(660))}" width="{f(3.5)}" height="{f(4)}" fill="{TINTA}"/>')
    for k in range(14):                                                           # escalera vista en corte: perfil escalonado
        z = k * 320 / 14
        s.append(f'<rect x="{f(X(215))}" y="{f(Z(z + 320 / 14))}" width="{f(170 * ESC)}" height="{f(320 / 14 * ESC)}" fill="none" stroke="{GRIS}" stroke-width="0.15"/>' if k % 2 == 0 else "")
    for nombre, z in (("N.P.T. ±0,00 · PLANTA BAJA", 0), ("N.P.T. +3,20 · PLANTA ALTA", 320), ("N.P.T. +6,20 · AZOTEA", 620), ("+8,80 · SALA DE MÁQUINAS", 880)):
        s.append(f'<line x1="{f(X(-60))}" y1="{f(Z(z))}" x2="{f(X(1160))}" y2="{f(Z(z))}" stroke="{AZUL}" stroke-width="0.18" stroke-dasharray="6 1.5 1 1.5"/>'
                 f'<path d="M{f(X(1160))} {f(Z(z))} l2 -2 l2 2 z" fill="{AZUL}"/>' + texto(X(1160) + 5, Z(z) + 0.8, nombre, 1.9, "400", AZUL))
    for nombre, x in proyecto["ejes_x"]:
        s.append(f'<line x1="{f(X(x))}" y1="{f(Z(940))}" x2="{f(X(x))}" y2="{f(Z(-60))}" stroke="{GRIS}" stroke-width="0.18" stroke-dasharray="6 1.5 1 1.5"/>' + burbuja(X(x), Z(940) - 3.5, nombre))
    s.append("</g>")
    s.append(titulo_vista(ox - 14, SUELO_CORTES + 20, "4. CORTE A-A", "ESC. 1:100"))
    return "".join(s)


def fachada(proyecto: dict, ox: float) -> str:
    """Fachada sur (frente), x en horizontal, alineada con los ejes de la planta de arriba; los volúmenes retirados más claros."""
    Z = lambda z: SUELO_CORTES - z * ESC                                          # noqa: E731
    X = lambda x: ox + x * ESC                                                    # noqa: E731
    s = ['<g id="FACHADA-SUR">']
    s.append(f'<rect x="{f(X(-60))}" y="{f(Z(0))}" width="{f(92)}" height="5" fill="url(#tierra)"/>')
    caras = sorted(proyecto["volumenes"], key=lambda v: v[3])                     # de atrás (y menor) hacia adelante
    for x0, y0, x1, y1, z0, z1 in caras:
        tono = "#e9ecef" if y1 < 1100 else "#d6dbe0"
        s.append(f'<rect x="{f(X(x0))}" y="{f(Z(z1))}" width="{f((x1 - x0) * ESC)}" height="{f((z1 - z0) * ESC)}" fill="{tono}" stroke="{TINTA}" stroke-width="0.3"/>')
    for cara, a, b, z0, z1 in proyecto["huecos_fachada"]:
        if cara == "s":
            s.append(f'<rect x="{f(X(a))}" y="{f(Z(z1))}" width="{f((b - a) * ESC)}" height="{f((z1 - z0) * ESC)}" fill="#a9c7e3" stroke="{TINTA}" stroke-width="0.3"/>'
                     f'<line x1="{f(X((a + b) / 2))}" y1="{f(Z(z1))}" x2="{f(X((a + b) / 2))}" y2="{f(Z(z0))}" stroke="{TINTA}" stroke-width="0.15"/>')
    s.append(f'<line x1="{f(X(-60))}" y1="{f(Z(0))}" x2="{f(X(860))}" y2="{f(Z(0))}" stroke="{TINTA}" stroke-width="0.8"/>')
    for nombre, x in proyecto["ejes_x"]:
        s.append(f'<line x1="{f(X(x))}" y1="{f(Z(940))}" x2="{f(X(x))}" y2="{f(Z(-60))}" stroke="{GRIS}" stroke-width="0.18" stroke-dasharray="6 1.5 1 1.5"/>' + burbuja(X(x), Z(940) - 3.5, nombre))
    s.append("</g>")
    s.append(titulo_vista(ox - 14, SUELO_CORTES + 20, "5. FACHADA SUR", "ESC. 1:100"))
    return "".join(s)


# ---- axonometría -------------------------------------------------------------------------------------------------------------------------------------
def axonometria(proyecto: dict, ox: float, oy: float, k: float = 0.085) -> str:
    """Isométrico desde el sudeste: se ven el techo, la cara sur (+y) y la cara este (+x) de cada volumen, pintados de atrás hacia adelante."""
    c, sn = math.cos(math.radians(30)), math.sin(math.radians(30))
    P = lambda x, y, z: (ox + (x - y) * c * k, oy + ((x + y) * sn - z) * k)      # noqa: E731
    poly = lambda pts, fill: f'<polygon points="{" ".join(f"{f(a)},{f(b)}" for a, b in pts)}" fill="{fill}" stroke="{TINTA}" stroke-width="0.3" stroke-linejoin="round"/>'   # noqa: E731
    s = ['<g id="AXONOMETRIA">']
    s.append(poly([P(-120, -120, 0), P(950, -120, 0), P(950, 1350, 0), P(-120, 1350, 0)], "#f1f2ee"))
    sombra = [P(0, 1200, 0), P(-280, 1200, 0), P(-280, 0, 0), P(0, 0, 0)]                 # sun from the east: the shadow falls to the west
    s.append(f'<polygon points="{" ".join(f"{f(a)},{f(b)}" for a, b in sombra)}" fill="#000" fill-opacity="0.07"/>')
    for x0, y0, x1, y1, z0, z1 in sorted(proyecto["volumenes"], key=lambda v: (v[4], v[0] + v[1])):
        s.append(poly([P(x0, y1, z0), P(x1, y1, z0), P(x1, y1, z1), P(x0, y1, z1)], "#d9dde1"))      # sur
        s.append(poly([P(x1, y0, z0), P(x1, y1, z0), P(x1, y1, z1), P(x1, y0, z1)], "#b9c0c7"))      # este
        s.append(poly([P(x0, y0, z1), P(x1, y0, z1), P(x1, y1, z1), P(x0, y1, z1)], "#f7f8f9"))      # techo
        for cara, a, b, za, zb in proyecto["huecos_fachada"]:
            if cara == "s" and abs(y1 - 1200) < 1 and x0 <= a and b <= x1 and z0 <= za and zb <= z1:
                s.append(poly([P(a, y1, za), P(b, y1, za), P(b, y1, zb), P(a, y1, zb)], "#5f7f9e"))
            if cara == "s" and abs(y1 - 750) < 1 and z0 >= 320 and x0 <= a and b <= x1 and z0 <= za and zb <= z1:
                s.append(poly([P(a, y1, za), P(b, y1, za), P(b, y1, zb), P(a, y1, zb)], "#5f7f9e"))
            if cara == "e" and abs(x1 - 800) < 1 and y0 <= a and b <= y1 and z0 <= za and zb <= z1:
                s.append(poly([P(x1, a, za), P(x1, b, za), P(x1, b, zb), P(x1, a, zb)], "#4f6d8a"))
    s.append("</g>")
    return "".join(s)


# ---- columna de notas y rótulo -----------------------------------------------------------------------------------------------------------------------
def columna(proyecto: dict) -> str:
    x, w = COL_NOTAS, HOJA[0] - 12 - COL_NOTAS
    s = [f'<g id="NOTAS"><line x1="{x}" y1="12" x2="{x}" y2="{HOJA[1] - 12}" stroke="{TINTA}" stroke-width="0.5"/>']
    y = 26
    s.append(texto(x + 6, y, "NOTAS GENERALES", 3.4, "700"))
    y += 7
    for i, n in enumerate(proyecto["notas"]):
        s.append(texto(x + 6, y, f"{i + 1}.", 2.1, "700") + texto(x + 11, y, n, 2.1))
        y += 5.2
    y += 6
    s.append(texto(x + 6, y, "LEYENDA", 3.4, "700"))
    y += 6
    for color, t in (("#2b3036", "Muro exterior e = 30 cm"), ("#565e67", "Muro interior e = 15 cm"), ("#8a939c", "Tabique e = 12 cm"), (PAPEL, "Baranda / muro bajo h = 1,00 m")):
        s.append(f'<rect x="{x + 6}" y="{f(y - 3)}" width="14" height="3.6" fill="{color}" stroke="{TINTA}" stroke-width="0.3"/>' + texto(x + 24, y, t, 2.1))
        y += 6
    for color, ancho, trazo, t in ((GRIS, 0.3, "6 1.5 1 1.5", "Eje estructural"), (AZUL, 0.3, "6 1.5 1 1.5", "Nivel"), (ROJO, 0.6, "none", "Línea de corte")):
        s.append(f'<line x1="{x + 6}" y1="{f(y - 1.2)}" x2="{x + 20}" y2="{f(y - 1.2)}" stroke="{color}" stroke-width="{ancho}" stroke-dasharray="{trazo}"/>' + texto(x + 24, y, t, 2.1))
        y += 6
    y += 6
    s.append(texto(x + 6, y, "CUADRO DE SUPERFICIES", 3.4, "700"))
    y += 6
    total = 0.0
    for nivel in proyecto["niveles"]:
        s.append(texto(x + 6, y, nivel["nombre"], 2.2, "700"))
        y += 4.6
        for nombre, (x0, y0, x1, y1) in nivel["ambientes"]:
            a = (x1 - x0) * (y1 - y0) / 1e4
            cubierta = nombre != "TERRAZA"
            total += a if cubierta else 0
            s.append(texto(x + 10, y, nombre.title(), 2.0) + texto(x + w - 8, y, f"{a:.2f} m²".replace(".", ",") + ("" if cubierta else " (desc.)"), 2.0, "400", TINTA, "end"))
            y += 4.2
        y += 1.5
    s.append(f'<line x1="{x + 6}" y1="{f(y - 2)}" x2="{x + w - 6}" y2="{f(y - 2)}" stroke="{TINTA}" stroke-width="0.3"/>'
             + texto(x + 6, y + 2, "TOTAL CUBIERTO", 2.3, "700") + texto(x + w - 8, y + 2, f"{total:.2f} m²".replace(".", ","), 2.3, "700", TINTA, "end"))
    # rótulo vertical integrado abajo
    ry = HOJA[1] - 12 - 150
    s.append(f'<rect x="{x}" y="{ry}" width="{w}" height="150" fill="#f6f7f8" stroke="{TINTA}" stroke-width="0.5"/>')
    filas = [("PROYECTO", proyecto["titulo"]), ("AUTOR", "Claude · EPC-291 (proyecto de autoría propia)"), ("CONTENIDO", "Plantas, corte, fachada y axonometría"),
             ("ESCALA", "1:100"), ("FORMATO", "A1 (841 × 594 mm)"), ("FECHA", "2026-11-02"), ("REVISIÓN", "0"), ("NIVEL DE COMPLEJIDAD", proyecto["complejidad"])]
    yy = ry + 10
    for etiqueta, valor in filas:
        s.append(texto(x + 6, yy, etiqueta, 1.8, "700", GRIS) + texto(x + 6, yy + 4.4, valor, 2.4, "700" if etiqueta == "PROYECTO" else "400"))
        s.append(f'<line x1="{x}" y1="{f(yy + 7)}" x2="{x + w}" y2="{f(yy + 7)}" stroke="{TINTA}" stroke-width="0.15"/>')
        yy += 12.5
    s.append(texto(x + w - 6, HOJA[1] - 20, proyecto["lamina"], 11, "700", TINTA, "end"))
    s.append("</g>")
    return "".join(s)


def lamina(proyecto: dict) -> str:
    W, H = HOJA
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">',
         f'<title>{proyecto["titulo"]} — Lámina {proyecto["lamina"]}</title>',
         '<defs><pattern id="tierra" width="3" height="3" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="3" stroke="#8b8b8b" stroke-width="0.4"/></pattern></defs>',
         f'<rect width="{W}" height="{H}" fill="{PAPEL}"/><rect x="12" y="12" width="{W - 24}" height="{H - 24}" fill="none" stroke="{TINTA}" stroke-width="0.7"/>']
    for i, (nivel, x) in enumerate(zip(proyecto["niveles"], X_PLANTAS)):
        s.append(planta(nivel, x, FILA_PLANTAS, proyecto, i + 1))
    s.append(cortes(proyecto, X_PLANTAS[1]))
    s.append(fachada(proyecto, X_PLANTAS[2]))
    s.append(axonometria(proyecto, 140, 412))
    s.append(titulo_vista(26, 560, "6. AXONOMETRÍA SUDESTE", "SIN ESCALA"))
    s.append(columna(proyecto))
    s.append("</svg>")
    return "\n".join(s)


def probar_motor(proyecto: dict, out: Path) -> list:
    """Cada planta como imagen y como DXF, por el motor: lo que encuentra contra lo que tiene."""
    sys.path.insert(0, str(RAIZ / "src"))
    from epc_arch import recognize                                                # noqa: E402
    filas = []
    for nivel in proyecto["niveles"]:
        p = {"estilo": nivel["estilo"], "ancho": nivel["ancho"], "alto": nivel["alto_planta"], "muros": nivel["muros"], "aberturas": nivel["aberturas"],
             "ambientes": [a for a in nivel["ambientes"] if a[0] != "TERRAZA"], "mobiliario": nivel["mobiliario"]}
        pp.png(p, out / f"{nivel['id']}.png")
        pp.dxf(p, out / f"{nivel['id']}.dxf")
        verdad = {"puertas": sum(1 for a in p["aberturas"] if a[1] == "puerta"), "ventanas": sum(1 for a in p["aberturas"] if a[1] == "ventana")}
        for ext in ("dxf", "png"):
            r = recognize((out / f"{nivel['id']}.{ext}").read_bytes(), f"{nivel['id']}.{ext}")
            (out / f"motor_{nivel['id']}_{ext}.json").write_text(json.dumps(r.as_dict(), indent=1, ensure_ascii=False), encoding="utf-8")
            c = r.architecture.counts()
            filas.append((nivel["id"], ext, verdad, c, len(r.architecture.rooms)))
    return filas


def main() -> None:
    for pid in sys.argv[1:] or list(PROYECTOS):
        proyecto = PROYECTOS[pid]
        out = SALIDA / pid
        out.mkdir(parents=True, exist_ok=True)
        (out / "lamina.svg").write_text(lamina(proyecto), encoding="utf-8")
        print(f"proyecto {pid}: {proyecto['titulo']} -> {out / 'lamina.svg'}")
        for nid, ext, verdad, c, amb in probar_motor(proyecto, out):
            print(f"  {nid}.{ext:3}  puertas {c['doors']}/{verdad['puertas']}  ventanas {c['windows']}/{verdad['ventanas']}  muros {c['walls']}  ambientes {amb}")


if __name__ == "__main__":
    main()
