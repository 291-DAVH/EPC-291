"""Láminas A0 a A4 según IRAM 4504 (formatos, elementos gráficos y plegado)
e IRAM 4508 (rótulo), tal como las dibuja el Manual IRAM Ed. XXVII.

- Formato A0 841 x 1189 usado apaisado: 1189 de ancho x 841 de alto
  (hoja tipo "A", 4504 2.1.2 y fig. 1; la fig. 6 muestra el A0 vertical).
- Margen a = 20 en los cuatro lados: en A0 el archivado no lleva margen de
  25 sino una banda adhesiva aparte (4504 2.3.1 y fig. 16, detalle A).
  El valor 20 es el de la fig. 7 (margen izquierdo hasta el recuadro) y el
  de ISO 5457:1980 para A0, norma en la que se basa la revisión.
- Franja de coordenadas de 5 mm (fig. 6/7). Módulo "aproximadamente 105 en
  abscisas y 148,5 en ordenadas" (2.3.3), medido desde los bordes de la hoja y con
  cantidad par de campos para que las señales de centrado caigan en una división:
  12 columnas de 99,08 y 6 filas de 140,17. Letras M..A de izquierda a derecha
  (A del lado del rótulo, sin la I para no confundirla con 1), números 1..6 de
  abajo hacia arriba. Abajo y a la derecha van girados, como en la fig. 6.
- Escala de comparación de 200 mm sin cifras, a 10 mm del borde izquierdo,
  arriba (2.3.4, fig. 7).
- Señales de centrado de 0,5 mm desde el borde hasta 5 mm dentro de la zona útil (2.4.1, fig. 8).
- Flecha de orientación sobre la señal inferior, hacia el dibujante (2.5, fig. 6).
- Rótulo IRAM 4508 fig. 2 (175 x 51) como bloque propio. La lista de modificaciones
  fig. 3 (175 x 21,5) es otro bloque, aparte, que se coloca encima sólo si hace falta
  (posición en data-modificaciones del <svg>).

Unidades mm, origen arriba-izquierda. Uso: python3 lamina_iram.py A0|A1|A2|A3|A4 [salida.svg] [--mod]
Genera también bloque_rotulo_IRAM4508.svg y bloque_modificaciones_IRAM4508.svg junto a la salida.
"""
import os
import sys

# formato: (ancho, alto, margen izq., margen sup./der./inf., columnas, filas)
# A0: margen 20 en los 4 lados (archivado con banda adhesiva, fig. 16).
# A1..A4: margen de archivado 25 a la izquierda y a = 10 (2.3.1, 2.3.2, fig. 5).
# Coordenadas ~105 x 148,5 (2.3.3): A1 8 x 4 y A3 4 x 2 exactos como en la fig. 6;
# A0 12 x 6 y A2 6 x 3 (módulo ~99 x 140). A4 sin coordenadas (nota fig. 6).
FORMATOS = {
    "A0": (1189, 841, 20, 20, 12, 6),
    "A1": (841, 594, 25, 10, 8, 4),
    "A2": (594, 420, 25, 10, 6, 3),
    "A3": (420, 297, 25, 10, 4, 2),
    "A4": (210, 297, 25, 10, 0, 0),
}
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
MOD = "--mod" in sys.argv          # agrega la lista de modificaciones (fig. 3) sobre el rótulo
FMT = ARGS[0].upper() if ARGS else "A0"
W, H, A_IZQ, A, N_COL, N_FIL = FORMATOS[FMT]
CON_COORD = N_COL > 0
FR = 5 if CON_COORD else 0   # franja de coordenadas
FONT = "osifont, ISOCPEUR, 'DejaVu Sans', Arial, sans-serif"

# Espesores
W_REC = 1.0       # recuadro (línea A, grupo d de IRAM 4502)
W_UTIL = 0.5      # límite de la zona útil y divisiones de coordenadas
W_CENT = 0.5      # señales de centrado (4504 2.4.1)
W_08, W_04, W_02 = 0.8, 0.4, 0.2  # rótulo (4508 fig. 2)

out = []
grupos = {}


def g(name):
    grupos.setdefault(name, [])
    return grupos[name]


def line(grp, x1, y1, x2, y2, sw):
    g(grp).append(f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" stroke-width="{sw}"/>')


def rect(grp, x, y, w, h, sw):
    g(grp).append(f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="none" stroke-width="{sw}"/>')


def text(grp, x, y, s, h, anchor="start", key=None, rot=0, weight=None):
    """(x, y): línea base; h: altura nominal de mayúscula (IRAM 4503)."""
    fs = h / 0.72
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    k = f' data-key="{key}" data-placeholder="{{{key}}}"' if key else ""
    r = f' transform="rotate({rot} {x:g} {y:g})"' if rot else ""
    wgt = f' font-weight="{weight}"' if weight else ""
    g(grp).append(f'<text stroke="none" x="{x:g}" y="{y:g}" font-size="{fs:.3f}"{a}{k}{r}{wgt}>{s}</text>')


# ---------------- recuadro y zona útil ----------------
x0, y0, x1, y1 = A_IZQ, A, W - A, H - A             # recuadro
u0, v0, u1, v1 = x0 + FR, y0 + FR, x1 - FR, y1 - FR  # zona útil
rect("corte", 0, 0, W, H, 0.1)
rect("recuadro", x0, y0, x1 - x0, y1 - y0, W_REC)
if CON_COORD:
    rect("recuadro", u0, v0, u1 - u0, v1 - v0, W_UTIL)

# ---------------- coordenadas modulares ----------------
mx, my = W / max(N_COL, 1), H / max(N_FIL, 1)
letras = "MLKJHGFEDCBA"[12 - N_COL:]
th = 3.5
for i in range(1, N_COL):
    x = i * mx
    line("coordenadas", x, y0, x, v0, W_UTIL)
    line("coordenadas", x, v1, x, y1, W_UTIL)
for j in range(1, N_FIL):
    y = j * my
    line("coordenadas", x0, y, u0, y, W_UTIL)
    line("coordenadas", u1, y, x1, y, W_UTIL)
for i in range(N_COL):
    xa, xb = max(i * mx, u0), min((i + 1) * mx, u1)
    cx = (xa + xb) / 2
    text("coordenadas", cx, y0 + FR / 2 + th / 2, letras[i], th, "middle")
    # abajo: girada, como en la fig. 6
    text("coordenadas", cx + th / 2, v1 + FR / 2, letras[i], th, "middle", rot=-90)
for j in range(N_FIL):
    ya, yb = max(j * my, v0), min((j + 1) * my, v1)
    cy = (ya + yb) / 2
    num = str(N_FIL - j)
    text("coordenadas", x0 + FR / 2, cy + th / 2, num, th, "middle")
    text("coordenadas", u1 + FR / 2 + th / 2, cy, num, th, "middle", rot=-90)

# ---------------- escala de comparación (fig. 7) ----------------
if CON_COORD:  # el A4 de la fig. 6 no la lleva
    for k in range(0, 201, 10):
        line("escala_comparacion", 10, y0 + k, 15, y0 + k, W_02)
    line("escala_comparacion", 15, y0, 15, y0 + 200, W_02)

# ---------------- señales de centrado y flecha ----------------
cx, cy = W / 2, H / 2
line("centrado", cx, 0, cx, v0 + 5, W_CENT)
line("centrado", cx, H, cx, v1 - 5, W_CENT)
line("centrado", 0, cy, u0 + 5, cy, W_CENT)
line("centrado", W, cy, u1 - 5, cy, W_CENT)
# Flecha de orientación (detalle fig. 6): triángulo de ~6 mm con el vértice
# en el recuadro, parte superior llena sobre el límite de la zona útil.
if CON_COORD:  # el A4 de la fig. 6 no la lleva
    g("orientacion").append(
        f'<polygon points="{cx - 3:g},{v1 - 1:g} {cx + 3:g},{v1 - 1:g} {cx:g},{y1:g}" fill="none" stroke-width="{W_02}"/>')
    g("orientacion").append(
        f'<polygon points="{cx - 3:g},{v1 - 1:g} {cx + 3:g},{v1 - 1:g} {cx + 1:g},{v1 + 3:g} {cx - 1:g},{v1 + 3:g}" '
        f'fill="#000" stroke="none"/>')
    line("orientacion", cx, v1 - 1, cx, v1 - 4, W_04)
    line("orientacion", cx, v1 - 4, cx + 3, v1 - 4, W_04)
    line("orientacion", cx + 3, v1 - 4, cx + 3, v1 - 1, W_04)

# ---------------- rótulo IRAM 4508 fig. 2 y lista de modificaciones fig. 3 ----------------
RW, RH, MH = 175, 51, 21.5
rx, ry = u1 - RW, v1 - RH
cx_ = [0, 26, 46, 56, 75, 120, 175]   # columnas 26/20/10/19/45/55
XV = 64                               # borde izquierdo de la casilla 7
t25 = 2.5
lab = 1.8   # leyendas impresas en la fig. 2


def dibujar_rotulo(G):
    """Fig. 2: 175 x 51. Espesores 0,8 contorno, 0,4 límites de casilla, 0,2 subdivisiones."""
    L, T, V = G, G + "_txt", G + "_var"
    c = cx_
    rect(L, 0, 0, RW, RH, W_08)
    # (1) anotaciones complementarias: columna de 26 a todo lo alto
    line(L, c[1], 0, c[1], RH, W_04)
    text(V, 1.5, 5, "{notas}", t25, key="notas")
    # (5) Fecha / Nombre y Dib. / Rev. / Apr.: 4 renglones en 17 mm, columnas 20/10/19
    r5 = 17 / 4
    for k in (1, 2, 3):
        line(L, c[1], k * r5, c[4], k * r5, W_02)
    line(L, c[2], 0, c[2], 17, W_02)
    line(L, c[3], 0, c[3], 17, W_02)
    text(T, c[2] + 0.5, r5 - 1.1, "Fecha", lab)
    text(T, c[3] + 0.6, r5 - 1.1, "Nombre", lab)
    for k, s in enumerate(("Dib.", "Rev.", "Apr."), start=2):
        text(T, c[1] + 0.8, k * r5 - 1.1, s, lab)
    # (6) cliente: 45 x 17
    line(L, c[4], 0, c[4], 17, W_04)
    text(V, (c[4] + c[5]) / 2, 10, "{cliente}", 3.5, "middle", key="cliente")
    # límite inferior de 5 y 6
    line(L, c[1], 17, c[5], 17, W_04)
    # (2) Esc. 11, (3) método ISO (E) 9, (4) Toler. / Rug. 14; columna de 20 y casillero de valor hasta 64
    line(L, c[2], 17, c[2], RH, W_02)
    line(L, c[1], 28, XV, 28, W_02)
    line(L, c[1], 37, XV, 37, W_02)
    line(L, XV, 17, XV, RH, W_04)
    text(T, c[1] + 0.8, 17 + 2.6, "Esc.", lab)
    text(V, (c[2] + XV) / 2, 17 + 7.5, "{escala}", t25, "middle", key="escala")
    sy, sx = 32.5, c[1] + 3.5   # tronco de cono y dos circunferencias (IRAM 4501)
    g(L).append(f'<polygon points="{sx:g},{sy - 1.3:g} {sx + 5:g},{sy - 2.6:g} {sx + 5:g},{sy + 2.6:g} {sx:g},{sy + 1.3:g}" '
                f'fill="none" stroke-width="{W_02}"/>')
    g(L).append(f'<circle cx="{sx + 10.5:g}" cy="{sy:g}" r="2.6" fill="none" stroke-width="{W_02}"/>')
    g(L).append(f'<circle cx="{sx + 10.5:g}" cy="{sy:g}" r="1.3" fill="none" stroke-width="{W_02}"/>')
    line(L, sx - 1, sy, sx + 14.5, sy, W_02)
    text(T, c[1] + 0.8, 37 + 3.2, "Toler.", lab)
    text(T, c[1] + 0.8, RH - 1.5, "Rug.", lab)
    # (7) denominación: de 64 a 120, alto 34
    text(V, (XV + c[5]) / 2, 17 + 15, "{denominacion}", 5, "middle", key="denominacion")
    text(V, (XV + c[5]) / 2, 17 + 24, "{denominacion_2}", 3.5, "middle", key="denominacion_2")
    # columna de 55: (8) 17 / (9) 17 / (10) 8,5 / (11) 8,5
    line(L, c[5], 0, c[5], RH, W_04)
    line(L, c[5], 17, c[6], 17, W_04)
    line(L, c[5], 34, c[6], 34, W_04)
    line(L, c[5], 42.5, c[6], 42.5, W_04)
    text(V, (c[5] + c[6]) / 2, 10.5, "{empresa}", 5, "middle", key="empresa")
    text(V, (c[5] + c[6]) / 2, 17 + 11, "{plano_n}", 5, "middle", key="plano_n")
    text(V, (c[5] + c[6]) / 2, 34 + 5.5, "{emision}", t25, "middle", key="emision")
    text(V, (c[5] + c[6]) / 2, 42.5 + 5.5, "{reemplaza}", t25, "middle", key="reemplaza")


def dibujar_modificaciones(G):
    """Fig. 3: franja de 21,5 x 175 apoyada sobre el rótulo. (12) 120 de ancho
    para la lista de modificaciones "en la forma más conveniente"; (13) 55 para
    la clave o número propio cuando en (9) va el número del cliente."""
    L, V = G, G + "_var"
    line(L, 0, 0, RW, 0, W_04)
    line(L, 0, 0, 0, MH, W_08)
    line(L, RW, 0, RW, MH, W_08)
    line(L, 0, MH, RW, MH, W_08)   # coincide con el contorno superior del rótulo
    line(L, cx_[5], 0, cx_[5], MH, W_04)
    text(V, (cx_[5] + RW) / 2, 13, "{plano_propio}", 3.5, "middle", key="plano_propio")


dibujar_rotulo("rotulo")
BLOQUE_ROT = {k: grupos.pop(k) for k in ("rotulo", "rotulo_txt", "rotulo_var")}
dibujar_modificaciones("modif")
BLOQUE_MOD = {k: grupos.pop(k) for k in ("modif", "modif_var")}

# ---------------- salida ----------------
estilos = {
    "corte": 'stroke="#000"',
    "recuadro": 'stroke="#000" stroke-linecap="square"',
    "coordenadas": 'stroke="#000" fill="#000"',
    "escala_comparacion": 'stroke="#000"',
    "centrado": 'stroke="#000"',
    "orientacion": 'stroke="#000"',
    "rotulo": 'stroke="#000" stroke-linecap="square"',
    "rotulo_txt": 'fill="#000"',
    "rotulo_var": 'fill="#000"',
    "modif": 'stroke="#000" stroke-linecap="square"',
    "modif_var": 'fill="#000"',
}


def bloque(gid, partes, x, y, norma):
    out = [f'<g id="{gid}" transform="translate({x:g} {y:g})" data-norma="{norma}">']
    for name, items in partes.items():
        out.append(f'<g id="{gid}_{name}" {estilos[name]}>')
        out.extend(items)
        out.append('</g>')
    out.append('</g>')
    return out


def guardar_bloque(carpeta, nombre, gid, partes, w, h, norma, titulo):
    doc = ['<?xml version="1.0" encoding="UTF-8"?>',
           f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}mm" height="{h}mm" viewBox="-1 -1 {w + 2:g} {h + 2:g}" '
           f'data-norma="{norma}" data-insercion="esquina superior izquierda (0, 0)">',
           f'<title>{titulo}</title>', f'<g font-family="{FONT}">']
    doc += bloque(gid, partes, 0, 0, norma) + ['</g>', '</svg>']
    with open(os.path.join(carpeta, nombre), "w", encoding="utf-8") as f:
        f.write("\n".join(doc))


svg = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}" '
    f'data-format="{FMT}" data-norma="IRAM 4504 / IRAM 4508" '
    f'data-zona-util="{u0:g} {v0:g} {u1:g} {v1:g}" data-rotulo="{rx:g} {ry:g} {u1:g} {v1:g}" '
    f'data-modificaciones="{rx:g} {ry - MH:g} {u1:g} {ry:g}">',
    f'<title>Lamina {FMT} {W} x {H} IRAM 4504 / 4508</title>',
    f'<rect id="papel" x="0" y="0" width="{W}" height="{H}" fill="#fff"/>',
    f'<g font-family="{FONT}">',
]
for name, items in grupos.items():
    svg.append(f'<g id="{name}" {estilos[name]}>')
    svg.extend(items)
    svg.append('</g>')
svg += bloque("rotulo_IRAM4508", BLOQUE_ROT, rx, ry, "IRAM 4508 fig. 2")
if MOD:
    svg += bloque("modificaciones_IRAM4508", BLOQUE_MOD, rx, ry - MH, "IRAM 4508 fig. 3")
svg += ['<g id="dibujo"><!-- insertar el diagrama aqui, dentro de la zona util y fuera del rotulo --></g>',
        '</g>', '</svg>']

dst = os.path.abspath(ARGS[1] if len(ARGS) > 1 else f"lamina_IRAM_{FMT}{'_mod' if MOD else ''}.svg")
with open(dst, "w", encoding="utf-8") as f:
    f.write("\n".join(svg))
guardar_bloque(os.path.dirname(dst), "bloque_rotulo_IRAM4508.svg", "rotulo_IRAM4508", BLOQUE_ROT, RW, RH,
               "IRAM 4508 fig. 2", "Rotulo IRAM 4508 fig. 2 (175 x 51)")
guardar_bloque(os.path.dirname(dst), "bloque_modificaciones_IRAM4508.svg", "modificaciones_IRAM4508", BLOQUE_MOD, RW, MH,
               "IRAM 4508 fig. 3", "Lista de modificaciones IRAM 4508 fig. 3 (175 x 21,5)")
print(dst, f"zona util {u0}..{u1} x {v0}..{v1}; rotulo x {rx}..{u1}, y {ry}..{v1}; modificaciones y {ry - MH}..{ry}")
