"""Genera la biblioteca de símbolos de planta (muebles, sanitarios, artefactos, aberturas) en `biblioteca/svg/` y su catálogo `biblioteca/catalogo.json`.

Convenciones: 1 unidad del SVG = 1 cm, origen arriba a la izquierda, y hacia abajo (el mismo marco que el plan space del motor, ver `epc_arch.model`); el símbolo se dibuja mirando
hacia arriba (cabecera de cama, respaldo de sillón y fondo de mueble en el borde superior). Solo trazos, sin relleno de color: el color lo pone quien los use.
Son dibujos propios, hechos a partir de lo observado en las muestras (no copias de ellas).

Uso: python scripts/generar_biblioteca.py
"""
import json
import math
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "biblioteca"
STROKE = 'fill="none" stroke="#111" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round"'


def rect(x, y, w, h, r=0, extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" {extra}/>'


def line(x1, y1, x2, y2):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"/>'


def circle(cx, cy, r):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}"/>'


def ellipse(cx, cy, rx, ry):
    return f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}"/>'


def silla(x, y, lado=45, mirando="abajo"):
    """Silla cuadrada con respaldo; `mirando` indica hacia dónde se sienta quien la usa."""
    r = rect(x, y, lado, lado, 4)
    b = 8
    resp = {"abajo": rect(x + 4, y - b + 4, lado - 8, b, 2), "arriba": rect(x + 4, y + lado - 4, lado - 8, b, 2),
            "izq": rect(x + lado - 4, y + 4, b, lado - 8, 2), "der": rect(x - b + 4, y + 4, b, lado - 8, 2)}[mirando]
    return r + resp


# ---- símbolos: nombre -> (categoría, ancho, alto, cuerpo SVG, descripción) ----

def cama(w, l=200):
    almohadas = 2 if w >= 140 else 1
    aw = (w - 30) / almohadas
    cuerpo = [rect(0, 0, w, l, 4), rect(5, 0, w - 10, 10, 2), line(0, l * 0.35, w, l * 0.35)]
    for i in range(almohadas):
        cuerpo.append(rect(10 + i * (aw + 10), 18, aw, 40, 8))
    return "".join(cuerpo)


def sofa(w, prof=90, brazos=20):
    return "".join([rect(0, 0, w, prof, 6), rect(0, 0, w, 22, 6), rect(0, 0, brazos, prof, 6), rect(w - brazos, 0, brazos, prof, 6),
                    *[line(brazos + (w - 2 * brazos) / n * i, 22, brazos + (w - 2 * brazos) / n * i, prof) for n in [max(2, round(w / 70))] for i in range(1, n)]])


def mesa_con_sillas(w, h, n_largo, n_corto=0):
    mx, my = 50, 50
    out = [rect(mx, my, w, h, 4)]
    for i in range(n_largo):
        x = mx + (w / n_largo) * (i + 0.5) - 22
        out += [silla(x, my - 52, 45, "abajo"), silla(x, my + h + 7, 45, "arriba")]
    for i in range(n_corto):
        out += [silla(mx - 52, my + h / 2 - 22, 45, "der"), silla(mx + w + 7, my + h / 2 - 22, 45, "izq")] if i == 0 else []
    return "".join(out)


def mesa_redonda(d, n):
    c = d / 2 + 55
    out = [circle(c, c, d / 2)]
    for i in range(n):
        a = 2 * math.pi * i / n - math.pi / 2
        cx, cy = c + (d / 2 + 30) * math.cos(a), c + (d / 2 + 30) * math.sin(a)
        out.append(circle(round(cx, 1), round(cy, 1), 22))
    return "".join(out)


def inodoro():
    return rect(5, 0, 40, 18, 3) + '<path d="M10 18 H40 V45 Q40 70 25 70 Q10 70 10 45 Z"/>' + ellipse(25, 44, 11, 15)


def lavabo(w=60, p=45):
    return rect(0, 0, w, p, 6) + ellipse(w / 2, p / 2 + 2, w / 2 - 10, p / 2 - 9) + circle(w / 2, 6, 2)


def banera(w=170, p=70):
    return rect(0, 0, w, p, 8) + rect(6, 6, w - 12, p - 12, 14) + circle(w - 18, p / 2, 4)


def ducha(l=90):
    return rect(0, 0, l, l) + line(0, 0, l, l) + line(l, 0, 0, l) + circle(l / 2, l / 2, 5) + circle(12, 12, 4)


def cocina_hornallas(l=60):
    out = [rect(0, 0, l, l, 2)]
    for cx, cy, r in ((l * .27, l * .27, 9), (l * .73, l * .27, 7), (l * .27, l * .73, 7), (l * .73, l * .73, 9)):
        out += [circle(cx, cy, r), circle(cx, cy, r * 0.45)]
    return "".join(out)


def heladera(l=70):
    return rect(0, 0, l, l, 3) + line(0, l * .35, l, l * .35) + line(8, 8, 8, 22) + line(8, l * .35 + 8, 8, l * .35 + 22)


def mesada_fregadero(w=150, p=60):
    return rect(0, 0, w, p) + rect(w * .25, 8, w * .30, p - 16, 5) + rect(w * .60, 8, w * .18, p - 16, 5) + circle(w * .25 + w * .15, 5, 2)


def placard(w=180, p=60):
    puertas = max(2, round(w / 60))
    return rect(0, 0, w, p) + "".join(line(w / puertas * i, 0, w / puertas * i, p) for i in range(1, puertas)) + line(0, p / 2, w, p / 2 + 0)


def escritorio(w=120, p=60):
    return rect(0, 0, w, p) + rect(w - 45, 8, 38, p - 16, 3) + silla(w / 2 - 22, p + 6, 45, "arriba")


def mueble_tv(w=160, p=40):
    return rect(0, 0, w, p) + rect(w / 2 - 55, 6, 110, 6, 1)


def escalera(w=90, largo=270, escalones=14):
    paso = largo / escalones
    return rect(0, 0, w, largo) + "".join(line(0, paso * i, w, paso * i) for i in range(1, escalones)) + line(w / 2, largo - 10, w / 2, 14) + f'<path d="M{w/2-8} 30 L{w/2} 14 L{w/2+8} 30"/>'


def arbol(d=200):
    pts = []
    n = 18
    for i in range(n):
        a = 2 * math.pi * i / n
        r = d / 2 * (0.82 if i % 2 else 1.0)
        pts.append(f"{d/2 + r*math.cos(a):.1f},{d/2 + r*math.sin(a):.1f}")
    return f'<polygon points="{" ".join(pts)}"/>' + circle(d / 2, d / 2, d * .08)


def auto(w=180, l=450):
    return rect(0, 0, w, l, 40) + rect(20, 60, w - 40, 70, 12) + rect(22, 280, w - 44, 60, 12) + rect(30, 135, w - 60, 140, 14)


def puerta(ancho=90):
    return rect(0, 0, ancho, 10) + line(0, 5, 0, 5 + ancho) + f'<path d="M{ancho} 5 A{ancho} {ancho} 0 0 0 0 {5 + ancho}"/>'


def ventana(ancho=120):
    return rect(0, 0, ancho, 12) + line(0, 4, ancho, 4) + line(0, 8, ancho, 8)


SIMBOLOS = {
    "cama-individual": ("dormitorio", 90, 200, cama(90), "Cama individual 0,90 x 2,00 m, cabecera arriba."),
    "cama-matrimonial": ("dormitorio", 160, 200, cama(160), "Cama matrimonial 1,60 x 2,00 m con dos almohadas."),
    "cama-king": ("dormitorio", 200, 200, cama(200), "Cama king 2,00 x 2,00 m."),
    "placard": ("dormitorio", 180, 60, placard(180), "Placard / ropero de 1,80 x 0,60 m con tres puertas."),
    "escritorio": ("dormitorio", 120, 111, escritorio(), "Escritorio de 1,20 x 0,60 m con cajonera y silla."),
    "sofa-3": ("estar", 200, 90, sofa(200), "Sofá de tres cuerpos 2,00 x 0,90 m."),
    "sofa-2": ("estar", 150, 90, sofa(150), "Sofá de dos cuerpos 1,50 x 0,90 m."),
    "sillon": ("estar", 90, 90, sofa(90), "Sillón individual 0,90 x 0,90 m."),
    "mueble-tv": ("estar", 160, 40, mueble_tv(), "Mueble de TV de 1,60 x 0,40 m."),
    "mesa-comedor-6": ("comedor", 260, 190, mesa_con_sillas(160, 90, 3, 1), "Mesa rectangular 1,60 x 0,90 m con seis sillas."),
    "mesa-comedor-4": ("comedor", 220, 190, mesa_con_sillas(120, 90, 2), "Mesa rectangular 1,20 x 0,90 m con cuatro sillas."),
    "mesa-redonda-4": ("comedor", 200, 200, mesa_redonda(90, 4), "Mesa redonda de 0,90 m con cuatro sillas."),
    "silla": ("comedor", 45, 53, silla(0, 8, 45, "abajo"), "Silla de comedor 0,45 m."),
    "inodoro": ("bano", 50, 70, inodoro(), "Inodoro con depósito, 0,50 x 0,70 m."),
    "lavabo": ("bano", 60, 45, lavabo(), "Lavabo de 0,60 x 0,45 m."),
    "banera": ("bano", 170, 70, banera(), "Bañera de 1,70 x 0,70 m."),
    "ducha": ("bano", 90, 90, ducha(), "Receptáculo de ducha de 0,90 x 0,90 m."),
    "cocina-4-hornallas": ("cocina", 60, 60, cocina_hornallas(), "Cocina de cuatro hornallas, 0,60 x 0,60 m."),
    "heladera": ("cocina", 70, 70, heladera(), "Heladera de 0,70 x 0,70 m."),
    "mesada-fregadero": ("cocina", 150, 60, mesada_fregadero(), "Mesada con pileta doble y escurridor, 1,50 x 0,60 m."),
    "escalera-recta": ("circulacion", 90, 270, escalera(), "Escalera recta de 0,90 m de ancho, 14 escalones, con flecha de subida."),
    "puerta-batiente": ("abertura", 90, 100, puerta(), "Puerta batiente de 0,90 m con arco de giro y hoja (lo que el motor reconoce como puerta)."),
    "ventana": ("abertura", 120, 12, ventana(), "Ventana de 1,20 m: dos trazos entre las caras del muro."),
    "arbol": ("exterior", 200, 200, arbol(), "Árbol en planta, copa de 2,00 m."),
    "auto": ("exterior", 180, 450, auto(), "Auto en planta (garaje), 1,80 x 4,50 m."),
}


def svg(nombre, ancho, alto, cuerpo, categoria) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{ancho}" height="{alto}" viewBox="0 0 {ancho} {alto}" data-symbol="{nombre}" data-category="{categoria}" data-units="cm">\n'
            f'<g id="{nombre}" {STROKE}>{cuerpo}</g>\n</svg>\n')


def main() -> None:
    (SALIDA / "svg").mkdir(parents=True, exist_ok=True)
    catalogo = []
    for nombre, (cat, w, h, cuerpo, desc) in SIMBOLOS.items():
        (SALIDA / "svg" / f"{nombre}.svg").write_text(svg(nombre, w, h, cuerpo, cat), encoding="utf-8")
        catalogo.append({"nombre": nombre, "categoria": cat, "ancho_cm": w, "alto_cm": h, "archivo": f"svg/{nombre}.svg", "descripcion": desc})
    (SALIDA / "catalogo.json").write_text(json.dumps({"schema_version": "1.0", "unidades": "cm", "simbolos": catalogo}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    hoja = ['<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="1100" viewBox="0 0 1400 1100"><rect width="1400" height="1100" fill="#fff"/>']
    x = y = 20
    fila = 0
    for nombre, (cat, w, h, cuerpo, _) in SIMBOLOS.items():
        esc = min(1.0, 200 / max(w, h)) if max(w, h) > 200 else 1.0
        if x + w * esc > 1380:
            x, y, fila = 20, y + fila + 50, 0
        hoja.append(f'<g transform="translate({x} {y}) scale({esc})" {STROKE}>{cuerpo}</g><text x="{x}" y="{y + h * esc + 14}" font-size="11" font-family="sans-serif">{nombre}</text>')
        x += w * esc + 30
        fila = max(fila, h * esc)
    hoja.append("</svg>\n")
    (SALIDA / "hoja-contacto.svg").write_text("\n".join(hoja), encoding="utf-8")
    print(f"{len(SIMBOLOS)} símbolos en {SALIDA}")


if __name__ == "__main__":
    main()
