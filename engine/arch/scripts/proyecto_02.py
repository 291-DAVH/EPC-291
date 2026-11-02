"""Proyecto 02 de autoría propia: vivienda de dos niveles con cochera, estudio y terraza. Más complejo que el 01: cotas encadenadas, etiquetas
inteligentes vinculadas al modelo y una segunda lámina con tablas de carpinterías y de acabados.

Reglas que sigue (además de la plantilla de lámina del proyecto 01):
  - Ningún texto genérico describe objetos: puertas (círculo), ventanas (hexágono), muros (rectángulo con su tipo) y locales (número, nombre y
    área; en A-202 también sus códigos de acabado en rombos) llevan su etiqueta, y su texto sale de los parámetros del modelo.
  - Las directrices van todas a 45°, con un quiebre horizontal corto, y se colocan buscando un lugar libre: no se cruzan entre sí, no pisan
    otras etiquetas, muros ni escaleras, y quedan dentro del edificio, donde no hay cotas.
  - Las tablas de puertas, ventanas y materiales se calculan del modelo (las cantidades se cuentan) y se filtran a lo que aparece en las
    plantas de la lámina. Tienen el ancho de la columna derecha, títulos en negrita de 3 mm y datos de 2 mm.

Salida en `out/proyectos/02/`: A-201.svg (arquitectura), A-202.svg (carpinterías y acabados), pb/pa .png/.dxf y motor_*.json.
Uso: python scripts/proyecto_02.py
"""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import planta_prueba as pp                                       # noqa: E402
from proyecto_autor import AZUL, GRIS, PAPEL, RAIZ, ROJO, TINTA, burbuja, f, texto, titulo_vista   # noqa: E402

SALIDA = RAIZ / "out" / "proyectos" / "02"
ESC = 0.1                              # 1:100 -> 1 cm del modelo = 0,1 mm de lámina
HOJA = (841, 594)

# ---- tipos (los parámetros de los que salen las etiquetas y las tablas) -------------------------------------------------------------------------------
PUERTAS = {
    "P-01": {"ancho": 1.00, "alto": 2.10, "material": "Marco aluminio / Hoja madera maciza", "apertura": "Abatible", "obs": "Acceso principal. Cerradura de seguridad de 3 puntos."},
    "P-02": {"ancho": 0.80, "alto": 2.10, "material": "Marco aluminio / Hoja placa MDF", "apertura": "Abatible", "obs": "Dormitorios, cocina, estudio y cochera. Cerradura de sobreponer."},
    "P-03": {"ancho": 0.70, "alto": 2.10, "material": "Marco aluminio / Hoja placa MDF", "apertura": "Abatible", "obs": "Baños y lavadero. Rejilla de ventilación inferior."},
    "P-04": {"ancho": 1.20, "alto": 2.10, "material": "Aluminio negro / DVH 4-9-4", "apertura": "Corrediza", "obs": "Salida a terraza. Burlete perimetral."},
    "PO-01": {"ancho": 3.00, "alto": 2.30, "material": "Perfil de acero / Panel de chapa inyectada", "apertura": "Seccional", "obs": "Cochera. Motor automático con control remoto."},
}
VENTANAS = {
    "V-01": {"ancho": 1.50, "alto": 1.20, "antepecho": 0.90, "material": "Aluminio negro / Vidrio float 6 mm", "apertura": "Corrediza", "obs": "Dormitorios, cocina, comedor y estudio. Incluye mosquitero."},
    "V-02": {"ancho": 0.60, "alto": 0.40, "antepecho": 1.70, "material": "Aluminio negro / Vidrio esmerilado 4 mm", "apertura": "Proyectante", "obs": "Baños y lavadero. Vidrio de privacidad."},
    "V-03": {"ancho": 2.50, "alto": 2.20, "antepecho": 0.00, "material": "Aluminio negro / DVH laminado 3+3", "apertura": "Paño fijo + corrediza", "obs": "Estar. Vidrio laminado de seguridad."},
    "V-04": {"ancho": 1.00, "alto": 0.60, "antepecho": 1.50, "material": "Aluminio negro / Vidrio float 4 mm", "apertura": "Basculante", "obs": "Cochera. Ventilación permanente."},
}
MUROS = {30: "M-01", 15: "M-02", 12: "M-03"}                   # tipo de muro por espesor
MATERIALES = {  # código: (elemento, descripción técnica, acabado / color, marca / ref., espesor, observaciones)
    "M-01": ("Muro exterior", "Ladrillo cerámico hueco 18 cm con revoque grueso y fino a la cal.", "Látex exterior / Gris cálido", "Sherwin Williams", "0.30", "Hidrófugo en el revoque exterior."),
    "M-02": ("Muro interior", "Ladrillo cerámico hueco 12 cm con revoques.", "Látex mate / Blanco", "Alba", "0.15", "Enduido y lijado previo."),
    "M-03": ("Tabique sanitario", "Placa de yeso resistente a la humedad, doble, sobre perfiles de 70 mm.", "Revestido según RE-01", "Durlock", "0.12", "Lana de vidrio de 50 mm."),
    "P-01": ("Piso general", "Porcelanato rectificado 60 × 60 cm de alto tránsito.", "Mate / Gris grafito", "Porcelanosa", "0.01", "Junta de 2 mm. Adhesivo de alta adherencia."),
    "P-02": ("Piso húmedo", "Cerámico antideslizante 30 × 30 cm.", "Antideslizante / Gris claro", "San Lorenzo", "0.008", "Pendiente 1 % hacia la rejilla."),
    "P-03": ("Piso cochera", "Hormigón llaneado con endurecedor superficial.", "Llaneado / Gris natural", "Sika", "0.10", "Juntas de dilatación cada 3 m."),
    "P-04": ("Piso terraza", "Deck de madera plástica (WPC) para exterior.", "Textura madera / Café", "Hunter Douglas", "0.02", "Fijación oculta sobre rastreles de aluminio."),
    "C-01": ("Cielorraso", "Placa de yeso suspendida, junta tomada.", "Látex / Blanco", "Durlock", "0.0125", "Altura libre 2.60 m (PB) y 2.50 m (PA)."),
    "C-02": ("Cielorraso húmedo", "Placa de yeso resistente a la humedad, suspendida.", "Pintura antihongos / Blanco", "Durlock", "0.0125", "Tapa de inspección de 60 × 60 cm."),
    "C-03": ("Cielorraso cochera", "Losa de H°A° vista con sellador.", "Gris natural", "N/A", "—", "Sin cielorraso suspendido."),
    "RE-01": ("Revestimiento", "Azulejo cerámico esmaltado 30 × 60 cm.", "Brillante / Blanco", "San Lorenzo", "0.008", "Hasta 2.10 m en baños; sobre mesada en cocina."),
}
COLOR_PISO = {"P-01": "#eceff3", "P-02": "#e1eef1", "P-03": "#e6e6e3", "P-04": "#f3ead9"}
HUMEDO = ("P-02", "C-02", "RE-01")
SECO = ("P-01", "C-01")

# ---- el modelo ---------------------------------------------------------------------------------------------------------------------------------------
# aberturas: (id, tipo, muro, posición desde `a`, ancho, bisagra, lado, clave del tipo)
PB = {
    "id": "pb", "nombre": "PLANTA BAJA", "z": 0, "alto": 300, "ancho": 1200, "fondo": 1000,
    "muros": [("m-n", (0, 0), (1200, 0), 30), ("m-e", (1200, 0), (1200, 1000), 30), ("m-s", (0, 1000), (1200, 1000), 30), ("m-o", (0, 0), (0, 1000), 30),
              ("m-1", (400, 0), (400, 1000), 15), ("m-2", (0, 400), (400, 400), 15), ("m-3", (800, 600), (1200, 600), 15), ("m-4", (800, 0), (800, 600), 15),
              ("t-1", (800, 250), (1200, 250), 12), ("t-2", (1000, 0), (1000, 250), 12)],
    "aberturas": [("PB-P1", "puerta", "m-s", 800, 100, "a", -1, "P-01"), ("PB-P2", "puerta", "m-1", 200, 80, "a", 1, "P-02"), ("PB-P3", "puerta", "m-1", 450, 80, "b", 1, "P-02"),
                  ("PB-P4", "puerta", "m-4", 185, 70, "b", -1, "P-03"), ("PB-P5", "puerta", "t-1", 300, 70, "a", -1, "P-03"), ("PB-P6", "puerta", "m-3", 200, 80, "a", -1, "P-02"),
                  ("PB-G1", "porton", "m-s", 200, 300, None, 0, "PO-01"),
                  ("PB-V1", "ventana", "m-n", 200, 150, None, 0, "V-01"), ("PB-V2", "ventana", "m-n", 600, 150, None, 0, "V-01"), ("PB-V3", "ventana", "m-n", 900, 60, None, 0, "V-02"),
                  ("PB-V4", "ventana", "m-n", 1100, 60, None, 0, "V-02"), ("PB-V5", "ventana", "m-e", 425, 150, None, 0, "V-01"), ("PB-V6", "ventana", "m-e", 800, 250, None, 0, "V-03"),
                  ("PB-V7", "ventana", "m-s", 1050, 250, None, 0, "V-03"), ("PB-V8", "ventana", "m-o", 200, 150, None, 0, "V-01"), ("PB-V9", "ventana", "m-o", 700, 100, None, 0, "V-04")],
    "locales": [("COCINA", (0, 0, 400, 400), "PB-01", ("P-01", "C-01", "RE-01")), ("COMEDOR", (400, 0, 800, 400), "PB-02", SECO), ("TOILETTE", (800, 0, 1000, 250), "PB-03", HUMEDO),
                ("LAVADERO", (1000, 0, 1200, 250), "PB-04", HUMEDO), ("COCHERA", (0, 400, 400, 1000), "PB-05", ("P-03", "C-03")), ("HALL", (400, 400, 800, 600), "PB-06", SECO),
                ("ESTUDIO", (800, 250, 1200, 600), "PB-07", SECO), ("ESTAR", (400, 600, 1200, 1000), "PB-08", SECO)],
    "escalera": (420, 500, 770, 600, "sube"),
    "mobiliario": [("rect", 20, 20, 380, 80, 0), ("rect", 20, 80, 80, 380, 0), ("rect", 500, 150, 700, 250, 6), ("rect", 90, 520, 310, 960, 40), ("rect", 470, 890, 770, 975, 12),
                   ("rect", 1100, 300, 1180, 480, 2), ("rect", 820, 20, 900, 90, 18), ("rect", 1020, 20, 1180, 90, 4)],
}
PA = {
    "id": "pa", "nombre": "PLANTA ALTA", "z": 320, "alto": 280, "ancho": 1200, "fondo": 1000,
    "muros": [("m-n", (0, 0), (1200, 0), 30), ("m-e", (1200, 0), (1200, 600), 30), ("m-s", (0, 600), (1200, 600), 30), ("m-o", (0, 0), (0, 600), 30),
              ("m-1", (0, 400), (1200, 400), 15), ("m-2", (400, 0), (400, 400), 15), ("m-3", (800, 0), (800, 400), 15),
              ("t-1", (200, 400), (200, 600), 12), ("t-2", (1000, 400), (1000, 600), 12)],
    "aberturas": [("PA-P1", "puerta", "m-1", 300, 80, "a", -1, "P-02"), ("PA-P2", "puerta", "m-1", 600, 80, "a", -1, "P-02"), ("PA-P3", "puerta", "m-1", 900, 80, "b", -1, "P-02"),
                  ("PA-P4", "puerta", "t-1", 50, 70, "a", 1, "P-03"), ("PA-P5", "puerta", "t-2", 50, 70, "a", -1, "P-03"), ("PA-P6", "corrediza", "m-s", 885, 120, None, 0, "P-04"),
                  ("PA-V1", "ventana", "m-n", 200, 150, None, 0, "V-01"), ("PA-V2", "ventana", "m-n", 600, 150, None, 0, "V-01"), ("PA-V3", "ventana", "m-n", 1000, 150, None, 0, "V-01"),
                  ("PA-V4", "ventana", "m-o", 200, 150, None, 0, "V-01"), ("PA-V5", "ventana", "m-o", 500, 60, None, 0, "V-02"), ("PA-V6", "ventana", "m-e", 200, 150, None, 0, "V-01"),
                  ("PA-V7", "ventana", "m-e", 500, 60, None, 0, "V-02"), ("PA-V8", "ventana", "m-s", 595, 150, None, 0, "V-01")],
    "locales": [("DORMITORIO 1", (0, 0, 400, 400), "PA-01", SECO), ("DORMITORIO 2", (400, 0, 800, 400), "PA-02", SECO), ("DORMITORIO 3", (800, 0, 1200, 400), "PA-03", SECO),
                ("BAÑO 1", (0, 400, 200, 600), "PA-04", HUMEDO), ("PASILLO", (200, 400, 1000, 600), "PA-05", SECO), ("BAÑO 2", (1000, 400, 1200, 600), "PA-06", HUMEDO),
                ("TERRAZA", (0, 600, 1200, 1000), "PA-07", ("P-04",))],
    "escalera": (420, 500, 770, 600, "llega"), "barandas": [((0, 1000), (1200, 1000)), ((0, 600), (0, 1000)), ((1200, 600), (1200, 1000)), ((420, 500), (770, 500))],
    "mobiliario": [("rect", 60, 60, 260, 280, 6), ("rect", 500, 60, 700, 280, 6), ("rect", 900, 60, 1100, 280, 6), ("rect", 20, 520, 180, 580, 18), ("rect", 1020, 520, 1180, 580, 18)],
}
PT = {
    "id": "pt", "nombre": "PLANTA DE AZOTEA", "z": 620, "alto": 60, "ancho": 1200, "fondo": 1000, "muros": [], "aberturas": [], "locales": [], "mobiliario": [],
    "azotea": (0, 0, 1200, 600), "proyeccion": (0, 600, 1200, 1000),
}
P02 = {
    "id": "02", "titulo": "Vivienda de dos niveles con cochera, estudio y terraza", "complejidad": "Cotas encadenadas, etiquetas vinculadas al modelo, tablas de carpinterías y acabados",
    "ejes_x": [("A", 0), ("B", 400), ("C", 800), ("D", 1200)], "ejes_y": [("1", 0), ("2", 400), ("3", 600), ("4", 1000)],
    "niveles": [PB, PA, PT], "corte_y": 550,
    "losas": [(-20, 1220, 300, 320), (-20, 1220, 600, 620)], "parapetos": [(0, 15, 620, 680), (1185, 1200, 620, 680)],
    "escalera_corte": (770, 420, 0, 320, 14),
    "cotas_nivel": [("±0,00 PB", 0), ("+3,20 PA", 320), ("+6,20 AZOTEA", 620)],
    "volumenes": [(0, 0, 1200, 1000, 0, 300), (-20, -20, 1220, 1020, 300, 320), (0, 0, 1200, 600, 320, 600), (-20, -20, 1220, 620, 600, 620),
                  (0, 0, 1200, 15, 620, 680), (0, 0, 15, 600, 620, 680), (0, 585, 1200, 600, 620, 680), (1185, 0, 1200, 600, 620, 680),
                  (0, 980, 1200, 1000, 320, 420), (0, 600, 20, 980, 320, 420), (1180, 600, 1200, 980, 320, 420)],
    "notas": [
        "Toda designación de puertas, ventanas, muros y locales se hace por etiqueta; ver tablas de la lámina A-202.",
        "Cotas en metros. Cadena 1: vanos; cadena 2: ejes; cadena 3: total a caras exteriores.",
        "Niveles referidos a N.P.T. ±0,00 = +0,15 sobre la vereda.",
        "Losas de H°A° e = 20 cm; azotea inaccesible con pendiente 2 % y parapeto h = 0,60 m.",
        "Escalera de H°A° de 14 alzadas (22,9 cm) y huellas de 25 cm.",
        "Baranda de terraza y de vacío de escalera h = 1,00 m.",
    ],
}


# ---- utilidades de geometría en la lámina ------------------------------------------------------------------------------------------------------------
def modelo(nivel: dict) -> dict:
    """El nivel en el formato de `planta_prueba` (aberturas de 7 campos)."""
    return {"muros": nivel["muros"], "aberturas": [a[:7] for a in nivel["aberturas"]], "ambientes": [(n, r) for n, r, _, _ in nivel["locales"]], "mobiliario": nivel["mobiliario"]}


def caja_de(pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def se_tocan(a, b, pad=0.0):
    return not (a[2] + pad <= b[0] or b[2] + pad <= a[0] or a[3] + pad <= b[1] or b[3] + pad <= a[1])


def cruza_caja(p, q, box):
    """¿El segmento p-q atraviesa la caja? (Liang-Barsky)"""
    t0, t1 = 0.0, 1.0
    dx, dy = q[0] - p[0], q[1] - p[1]
    for pk, qk in ((-dx, p[0] - box[0]), (dx, box[2] - p[0]), (-dy, p[1] - box[1]), (dy, box[3] - p[1])):
        if pk == 0:
            if qk < 0:
                return False
        else:
            t = qk / pk
            if pk < 0:
                t0 = max(t0, t)
            else:
                t1 = min(t1, t)
            if t0 > t1:
                return False
    return True


def se_cruzan(p1, p2, p3, p4):
    d = lambda a, b, c: (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])     # noqa: E731
    return d(p1, p2, p3) * d(p1, p2, p4) < 0 and d(p3, p4, p1) * d(p3, p4, p2) < 0


class Ubicador:
    """Coloca etiquetas sin pisar nada: cajas ocupadas, directrices ya trazadas y un recinto del que no deben salir (donde no hay cotas)."""

    def __init__(self, recinto):
        self.recinto = recinto
        self.cajas = []                       # (caja, clave): la clave permite ignorar el muro del que sale una directriz
        self.lineas = []
        self.cotas = []                       # segmentos de las cotas: ninguna etiqueta ni directriz los toca

    def ocupar(self, caja, clave=None):
        self.cajas.append((caja, clave))

    def libre(self, caja, segmentos=(), ignorar=None, holgura=0.5):
        r = self.recinto
        if caja[0] < r[0] or caja[1] < r[1] or caja[2] > r[2] or caja[3] > r[3]:
            return False
        if any(se_tocan(caja, c, holgura) for c, _ in self.cajas):
            return False
        if any(cruza_caja(a, b, (caja[0] - 0.4, caja[1] - 0.4, caja[2] + 0.4, caja[3] + 0.4)) for a, b in self.cotas):
            return False
        for p, q in segmentos:
            if any(cruza_caja(p, q, c) for c, k in self.cajas if k != ignorar):
                return False
            if any(se_cruzan(p, q, a, b) for a, b in self.lineas + self.cotas):
                return False
        return True

    def con_directriz(self, ancla, dirs, mitad, ignorar=None, largos=(6, 8, 10, 13, 16, 20)):
        """Etiqueta al final de una directriz a 45° con un quiebre horizontal de 2 mm. Devuelve (centro, segmentos) o None."""
        for L in largos:
            for dx, dy in dirs:
                e = (ancla[0] + dx * L, ancla[1] + dy * L)
                sg = 1 if dx > 0 else -1
                s = (e[0] + 2 * sg, e[1])
                c = (s[0] + sg * mitad[0], s[1])
                caja = (c[0] - mitad[0], c[1] - mitad[1], c[0] + mitad[0], c[1] + mitad[1])
                segs = [(ancla, e), (e, s)]
                inicio = (ancla[0] + dx * 0.6, ancla[1] + dy * 0.6)                 # the anchor itself sits on its element: checked from just past it
                if self.libre(caja, [(inicio, e), (e, s)], ignorar):
                    self.ocupar(caja)
                    self.lineas += segs
                    return c, segs
        return None


# ---- símbolos de etiqueta ----------------------------------------------------------------------------------------------------------------------------
def tag_puerta(c, t):
    return f'<circle cx="{f(c[0])}" cy="{f(c[1])}" r="3.1" fill="{PAPEL}" stroke="{TINTA}" stroke-width="0.25"/>' + texto(c[0], c[1] + 0.6, t, 1.6, "700", TINTA, "middle")


def tag_ventana(c, t):
    r = 3.4
    pts = " ".join(f"{f(c[0] + r * math.cos(math.radians(a)))},{f(c[1] + r * math.sin(math.radians(a)))}" for a in range(0, 360, 60))
    return f'<polygon points="{pts}" fill="{PAPEL}" stroke="{AZUL}" stroke-width="0.25"/>' + texto(c[0], c[1] + 0.6, t, 1.6, "700", AZUL, "middle")


def tag_muro(c, t):
    return (f'<rect x="{f(c[0] - 4.2)}" y="{f(c[1] - 1.8)}" width="8.4" height="3.6" rx="0.4" fill="{PAPEL}" stroke="{TINTA}" stroke-width="0.25"/>'
            + texto(c[0], c[1] + 0.6, t, 1.6, "700", TINTA, "middle"))


def rombo(c, t, color=TINTA, r=2.7):
    return (f'<polygon points="{f(c[0])},{f(c[1] - r)} {f(c[0] + r * 1.35)},{f(c[1])} {f(c[0])},{f(c[1] + r)} {f(c[0] - r * 1.35)},{f(c[1])}" fill="{PAPEL}" stroke="{color}" stroke-width="0.22"/>'
            + texto(c[0], c[1] + r * 0.18, t, r * 0.46, "700", color, "middle"))


def directriz(segs, color=TINTA):
    (a, _), _ = segs[0], None
    return (f'<circle cx="{f(a[0])}" cy="{f(a[1])}" r="0.45" fill="{color}"/>'
            + "".join(f'<line x1="{f(p[0])}" y1="{f(p[1])}" x2="{f(q[0])}" y2="{f(q[1])}" stroke="{color}" stroke-width="0.18"/>' for p, q in segs))


# ---- cotas -------------------------------------------------------------------------------------------------------------------------------------------
def cadena(puntos, eje, pos, ref, horizontal=True, ub=None, corta=None):
    """Cadena de cotas: `puntos` en mm a lo largo, línea de cota en `pos`, líneas de referencia desde `ref`. Sus líneas quedan registradas en `ub`."""
    s = []
    puntos = sorted(set(round(p, 3) for p in puntos))
    if corta is not None:                                                          # short extension lines: they stop `corta` mm from the dimension line
        ref = pos + (corta + 1.2 if pos < ref else -corta - 1.2)
    if ub is not None:
        ext = [((p, ref), (p, pos)) if horizontal else ((ref, p), (pos, p)) for p in puntos]
        dim = ((puntos[0], pos), (puntos[-1], pos)) if horizontal else ((pos, puntos[0]), (pos, puntos[-1]))
        ub.cotas += ext + [dim]
    for p in puntos:
        if horizontal:
            s.append(f'<line x1="{f(p)}" y1="{f(ref + (1.2 if pos > ref else -1.2))}" x2="{f(p)}" y2="{f(pos + (1.4 if pos > ref else -1.4))}" stroke="{ROJO}" stroke-width="0.12"/>'
                     f'<line x1="{f(p - 0.8)}" y1="{f(pos + 0.8)}" x2="{f(p + 0.8)}" y2="{f(pos - 0.8)}" stroke="{ROJO}" stroke-width="0.35"/>')
        else:
            s.append(f'<line x1="{f(ref + (1.2 if pos > ref else -1.2))}" y1="{f(p)}" x2="{f(pos + (1.4 if pos > ref else -1.4))}" y2="{f(p)}" stroke="{ROJO}" stroke-width="0.12"/>'
                     f'<line x1="{f(pos - 0.8)}" y1="{f(p + 0.8)}" x2="{f(pos + 0.8)}" y2="{f(p - 0.8)}" stroke="{ROJO}" stroke-width="0.35"/>')
    a, b = puntos[0], puntos[-1]
    s.append(f'<line x1="{f(a)}" y1="{f(pos)}" x2="{f(b)}" y2="{f(pos)}" stroke="{ROJO}" stroke-width="0.15"/>' if horizontal else
             f'<line x1="{f(pos)}" y1="{f(a)}" x2="{f(pos)}" y2="{f(b)}" stroke="{ROJO}" stroke-width="0.15"/>')
    for p, q in zip(puntos, puntos[1:]):
        valor = f"{(q - p) / ESC / 100:.2f}".replace(".", ",")
        m = (p + q) / 2
        if q - p < 4.5:                                                            # dimension too short for its figure: written beside
            m = q + 2.6
        if horizontal:
            s.append(texto(m, pos - 0.9, valor, 1.6, "400", ROJO, "middle"))
        else:
            s.append(texto(pos - 0.9, m, valor, 1.6, "400", ROJO, "middle", f'transform="rotate(-90 {f(pos - 0.9)} {f(m)})"'))
    return "".join(s)


SIN_ETIQUETA = []                      # elements a sheet could not tag: the tagging rule says there must be none


# ---- una planta --------------------------------------------------------------------------------------------------------------------------------------
def planta(proj, nivel, ox, oy, numero, modo):
    """`modo` "arq" (A-201: cotas y etiquetas de muro) o "acab" (A-202: locales con sus códigos de acabado)."""
    M = lambda x, y: (ox + x * ESC, oy + y * ESC)                                # noqa: E731
    p = modelo(nivel)
    W, H = nivel["ancho"], nivel["fondo"]
    s = [f'<g id="{modo.upper()}-{nivel["id"].upper()}">']
    tiene_terraza = any(n == "TERRAZA" for n, _, _, _ in nivel["locales"])
    pie = 1015 if (nivel["id"] == "pb" or tiene_terraza or "proyeccion" in nivel) else H + 15
    recinto = (*M(-15, -15), *M(W + 15, pie))
    BANDA = 15                                            # band outside the walls for tags, between the walls and the dimensions
    ub = Ubicador((recinto[0] - BANDA + 1, recinto[1] - BANDA + 1, recinto[2] + BANDA - 1, recinto[3] + BANDA - 1))
    # azotea
    if "azotea" in nivel:
        x0, y0, x1, y1 = nivel["azotea"]
        a, b = M(x0, y0), M(x1, y1)
        s.append(f'<rect x="{f(a[0])}" y="{f(a[1])}" width="{f(b[0] - a[0])}" height="{f(b[1] - a[1])}" fill="#f1f3f5" stroke="{TINTA}" stroke-width="0.5"/>'
                 f'<rect x="{f(a[0] + 1.5)}" y="{f(a[1] + 1.5)}" width="{f(b[0] - a[0] - 3)}" height="{f(b[1] - a[1] - 3)}" fill="none" stroke="{TINTA}" stroke-width="0.2"/>')
        for k in range(1, 6):
            xx = a[0] + (b[0] - a[0]) * k / 6
            s.append(f'<line x1="{f(xx)}" y1="{f(a[1] + 4)}" x2="{f(xx)}" y2="{f(b[1] - 4)}" stroke="{GRIS}" stroke-width="0.15" stroke-dasharray="2 1.2"/>')
        c = M(900, 300)
        s.append(f'<path d="M{f(c[0] - 8)} {f(c[1])} L{f(c[0] + 8)} {f(c[1])} M{f(c[0] + 6)} {f(c[1] - 1.2)} L{f(c[0] + 8)} {f(c[1])} L{f(c[0] + 6)} {f(c[1] + 1.2)}" fill="none" stroke="{TINTA}" stroke-width="0.3"/>'
                 + texto(c[0], c[1] - 1.5, "2 %", 1.8, "700", TINTA, "middle"))
        x0, y0, x1, y1 = nivel["proyeccion"]
        a, b = M(x0, y0), M(x1, y1)
        s.append(f'<rect x="{f(a[0])}" y="{f(b[1] - (b[1] - a[1]))}" width="{f(b[0] - a[0])}" height="{f(b[1] - a[1])}" fill="none" stroke="{GRIS}" stroke-width="0.2" stroke-dasharray="2.5 1.5"/>')
    # locales
    for nombre, (x0, y0, x1, y1), _, acab in nivel["locales"]:
        a, b = M(x0, y0), M(x1, y1)
        color = COLOR_PISO.get(acab[0], "#f2f2f2") if modo == "acab" else ("#f6f1e7" if nombre == "TERRAZA" else "#f3f4f1")
        s.append(f'<rect x="{f(a[0])}" y="{f(a[1])}" width="{f(b[0] - a[0])}" height="{f(b[1] - a[1])}" fill="{color}"/>')
        if nombre == "TERRAZA":
            s.extend(f'<line x1="{f(a[0])}" y1="{f(yy)}" x2="{f(b[0])}" y2="{f(yy)}" stroke="#d8cdb8" stroke-width="0.15"/>' for yy in [a[1] + k * 4 for k in range(1, int((b[1] - a[1]) / 4))])
    # muros
    tramos = []
    for m in p["muros"]:
        relleno = {30: "#2b3036", 15: "#565e67", 12: "#8a939c"}[m[3]]
        for t0, t1 in pp.tramos(p, m):
            pts = [M(*q) for q in pp.rect(m, t0, t1)]
            s.append(f'<polygon points="{" ".join(f"{f(x)},{f(y)}" for x, y in pts)}" fill="{relleno}" stroke="{TINTA}" stroke-width="0.3"/>')
            caja = caja_de(pts)
            tramos.append((m, t0, t1, caja))
            ub.ocupar(caja, m[0])
    for a, b in nivel.get("barandas", []):
        pa_, pb_ = M(*a), M(*b)
        dx, dy = pb_[0] - pa_[0], pb_[1] - pa_[1]
        L = math.hypot(dx, dy)
        nx, ny = -dy / L * 0.6, dx / L * 0.6
        pts = [(pa_[0] + nx, pa_[1] + ny), (pb_[0] + nx, pb_[1] + ny), (pb_[0] - nx, pb_[1] - ny), (pa_[0] - nx, pa_[1] - ny)]
        s.append(f'<polygon points="{" ".join(f"{f(x)},{f(y)}" for x, y in pts)}" fill="{PAPEL}" stroke="{TINTA}" stroke-width="0.22"/>')
        ub.ocupar(caja_de(pts))
    # escalera
    if "escalera" in nivel:
        x0, y0, x1, y1, modo_e = nivel["escalera"]
        a, b = M(x0, y0), M(x1, y1)
        s.append(f'<rect x="{f(a[0])}" y="{f(a[1])}" width="{f(b[0] - a[0])}" height="{f(b[1] - a[1])}" fill="{PAPEL}" stroke="{TINTA}" stroke-width="0.25"/>')
        for k in range(1, 14):
            xx = b[0] - (b[0] - a[0]) * k / 14
            s.append(f'<line x1="{f(xx)}" y1="{f(a[1])}" x2="{f(xx)}" y2="{f(b[1])}" stroke="{TINTA}" stroke-width="0.15"/>')
        ym = (a[1] + b[1]) / 2
        s.append(f'<path d="M{f(b[0] - 1)} {f(ym)} L{f(a[0] + 2)} {f(ym)} M{f(a[0] + 3.5)} {f(ym - 1)} L{f(a[0] + 2)} {f(ym)} L{f(a[0] + 3.5)} {f(ym + 1)}" fill="none" stroke="{ROJO}" stroke-width="0.3"/>'
                 + texto(b[0] - 3, ym - 1.2, "S" if modo_e == "sube" else "B", 2.2, "700", ROJO, "middle"))
        if modo_e == "sube":
            s.append(f'<line x1="{f(a[0] + (b[0] - a[0]) * 0.45)}" y1="{f(a[1])}" x2="{f(a[0] + (b[0] - a[0]) * 0.52)}" y2="{f(b[1])}" stroke="{TINTA}" stroke-width="0.35"/>')
        ub.ocupar((a[0], a[1], b[0], b[1]))
    # mobiliario
    for mob in p["mobiliario"]:
        _, x0, y0, x1, y1, r = mob
        a, b = M(x0, y0), M(x1, y1)
        s.append(f'<rect x="{f(a[0])}" y="{f(a[1])}" width="{f(b[0] - a[0])}" height="{f(b[1] - a[1])}" rx="{f(r * ESC)}" fill="none" stroke="{GRIS}" stroke-width="0.15"/>')
    # aberturas
    giros = []
    for ab in nivel["aberturas"]:
        id_, tipo, mid, pos, w, _, _, clave = ab
        m = pp.muro(p, mid)
        if tipo == "puerta":
            h, c, o, _ = pp.puerta_geom(p, ab[:7])
            H_, C_, O_ = M(*h), M(*c), M(*o)
            r = w * ESC
            cross = (C_[0] - H_[0]) * (O_[1] - H_[1]) - (C_[1] - H_[1]) * (O_[0] - H_[0])
            s.append(f'<path d="M{f(C_[0])} {f(C_[1])} A{f(r)} {f(r)} 0 0 {1 if cross > 0 else 0} {f(O_[0])} {f(O_[1])}" fill="none" stroke="{TINTA}" stroke-width="0.12" stroke-dasharray="1 0.6"/>'
                     f'<line x1="{f(H_[0])}" y1="{f(H_[1])}" x2="{f(O_[0])}" y2="{f(O_[1])}" stroke="{TINTA}" stroke-width="0.4"/>')
            uc = ((C_[0] - H_[0]) / r, (C_[1] - H_[1]) / r)
            uo = ((O_[0] - H_[0]) / r, (O_[1] - H_[1]) / r)
            bis = (uc[0] + uo[0], uc[1] + uo[1])
            n_ = math.hypot(*bis)
            centro = (H_[0] + bis[0] / n_ * r * 0.55, H_[1] + bis[1] / n_ * r * 0.55)
            giros.append((caja_de([H_, C_, O_]), centro, clave))
        elif tipo in ("corrediza", "porton"):
            h_ = m[3] / 2
            for k, o in enumerate((-h_ / 3, h_ / 3) if tipo == "corrediza" else (0,)):
                q1 = M(*pp.en_muro(m, pos - w / 2 + (w / 2 if k else 0), o))
                q2 = M(*pp.en_muro(m, pos + (w / 2 if k else 0) - (0 if k else 0) if tipo == "corrediza" else pos + w / 2, o))
                if tipo == "corrediza":
                    q1 = M(*pp.en_muro(m, pos - w / 2 + k * w * 0.45, o))
                    q2 = M(*pp.en_muro(m, pos + w * 0.05 + k * w * 0.45, o))
                s.append(f'<line x1="{f(q1[0])}" y1="{f(q1[1])}" x2="{f(q2[0])}" y2="{f(q2[1])}" stroke="{TINTA}" stroke-width="{0.5 if tipo == "corrediza" else 0.25}"'
                         + (' stroke-dasharray="2 1"' if tipo == "porton" else "") + "/>")
            cen = M(*pp.en_muro(m, pos, 0))
            dentro = M(*pp.en_muro(m, pos, -1 if mid == "m-s" else 1))
            sg = 1 if dentro[1] > cen[1] or dentro[0] > cen[0] else -1
            giros.append((None, (cen[0], cen[1] - 5.5) if mid == "m-s" else (cen[0] + sg * 5.5, cen[1]), clave))
        elif tipo == "ventana":
            h_ = m[3] / 2
            marco = [M(*pp.en_muro(m, pos - w / 2, h_)), M(*pp.en_muro(m, pos + w / 2, h_)), M(*pp.en_muro(m, pos + w / 2, -h_)), M(*pp.en_muro(m, pos - w / 2, -h_))]
            s.append(f'<polygon points="{" ".join(f"{f(x)},{f(y)}" for x, y in marco)}" fill="{PAPEL}" stroke="{TINTA}" stroke-width="0.2"/>')
            for o in (-3, 3):
                q1, q2 = M(*pp.en_muro(m, pos - w / 2, o)), M(*pp.en_muro(m, pos + w / 2, o))
                s.append(f'<line x1="{f(q1[0])}" y1="{f(q1[1])}" x2="{f(q2[0])}" y2="{f(q2[1])}" stroke="{AZUL}" stroke-width="0.12"/>')
            ub.ocupar(caja_de(marco), mid)
    # ejes y burbujas (norte y oeste)
    for nombre, x in proj["ejes_x"]:
        X = M(x, 0)[0]
        s.append(f'<line x1="{f(X)}" y1="{f(oy - 30 - (0 if modo == "arq" else -12))}" x2="{f(X)}" y2="{f(recinto[3] + 3)}" stroke="{GRIS}" stroke-width="0.15" stroke-dasharray="6 1.5 1 1.5"/>' + burbuja(X, oy - (33.5 if modo == "arq" else 21.5), nombre))
    for nombre, y in proj["ejes_y"]:
        if y > (pie - 15) + 1:
            continue
        Y = M(0, y)[1]
        s.append(f'<line x1="{f(ox - 14 - BANDA)}" y1="{f(Y)}" x2="{f(recinto[2] + 3)}" y2="{f(Y)}" stroke="{GRIS}" stroke-width="0.15" stroke-dasharray="6 1.5 1 1.5"/>' + burbuja(ox - 17.5 - BANDA, Y, nombre))
    # cotas: norte (vanos y ejes), este (vanos, ejes, total), sur (total)
    if modo == "arq":
        def vanos(mid, eje_x):
            m = next((m for m in p["muros"] if m[0] == mid), None)
            if m is None:
                return []
            out = []
            for ab in nivel["aberturas"]:
                if ab[2] == mid:
                    for t in (ab[3] - ab[4] / 2, ab[3] + ab[4] / 2):
                        q = M(*pp.en_muro(m, t, 0))
                        out.append(q[0] if eje_x else q[1])
            return out
        top, izq, der = M(0, -15)[1], M(-15, 0)[0], M(W + 15, 0)[0]
        xs_ext = [izq, der]
        s.append(cadena(xs_ext + vanos("m-n", True), "x", top - 17, top, ub=ub, corta=4))
        s.append(cadena([M(x, 0)[0] for _, x in proj["ejes_x"]], "x", top - 23, top - 17, ub=ub))
        bajo = M(0, pie)[1]
        s.append(cadena(xs_ext, "x", bajo + 17, bajo, ub=ub))
        ys_ext = [M(0, -15)[1], bajo]
        s.append(cadena(ys_ext + vanos("m-e", False), "y", der + 17, der, horizontal=False, ub=ub, corta=4))
        s.append(cadena([M(0, y)[1] for _, y in proj["ejes_y"] if y <= pie - 15 + 1], "y", der + 23, der + 17, horizontal=False, ub=ub))
        s.append(cadena(ys_ext, "y", der + 29, der + 23, horizontal=False, ub=ub))
        if nivel["id"] in ("pb", "pa"):                                            # marca del corte A-A
            Y = M(0, proj["corte_y"])[1]
            for X in (izq - 20, der + 34):
                s.append(f'<line x1="{f(X - 2.5)}" y1="{f(Y)}" x2="{f(X + 2.5)}" y2="{f(Y)}" stroke="{ROJO}" stroke-width="0.6"/>'
                         f'<path d="M{f(X)} {f(Y)} L{f(X)} {f(Y - 3.5)} L{f(X - 1.1)} {f(Y - 2.3)}" fill="none" stroke="{ROJO}" stroke-width="0.35"/>' + texto(X, Y + 3.4, "A", 2.4, "700", ROJO, "middle"))
    # etiquetas: locales, puertas, giros como obstáculos, ventanas, muros
    capas = []
    for caja_giro, centro, clave in giros:                                       # door tags first: they sit in their swing, the room tags move round them
        capas.append(tag_puerta(centro, clave))
        ub.ocupar((centro[0] - 3.2, centro[1] - 3.2, centro[0] + 3.2, centro[1] + 3.2))
    for nombre, (x0, y0, x1, y1), num, acab in nivel["locales"]:
        a, b = M(x0, y0), M(x1, y1)
        area = (x1 - x0) * (y1 - y0) / 1e4
        linea2 = f"{num} · " + f"{area:.2f} m²".replace(".", ",")
        cx0, cy0 = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        n_acab = len(acab) if modo == "acab" else 0
        formas = []                                                                # (text sizes, finish codes below or beside): the first that fits is used
        for t1, t2, rr in ((2.0, 1.6, 2.7), (1.6, 1.3, 2.1), (1.4, 1.15, 1.85), (1.25, 1.05, 1.6)):
            paso = rr * 2.3
            texto_w = max(len(nombre) * t1 * 0.58, len(linea2) * t2 * 0.56) + 2.4
            texto_h = t1 * 1.35 + t2 * 1.6 + 1.2
            if not n_acab:
                formas.append((t1, t2, None, texto_w, texto_h, rr))
            else:
                formas.append((t1, t2, "abajo", max(texto_w, n_acab * paso + 1.5), texto_h + rr * 2 + 0.6, rr))
                formas.append((t1, t2, "lado", texto_w + n_acab * paso + 1.5, max(texto_h, rr * 2 + 0.8), rr))
        ubicado = None
        for t1, t2, disp, ancho, alto, rr in formas:
            cands = [(cx0 + dx, cy0 + dy) for dx, dy in [(0, 0), (0, -6), (0, 6), (-8, 0), (8, 0), (0, -11), (0, 11), (-12, -6), (12, 6), (-12, 6), (12, -6)]]
            cands += sorted(((a[0] + ancho / 2 + i * 1.5, a[1] + alto / 2 + j * 1.5) for i in range(max(0, int((b[0] - a[0] - ancho) / 1.5)) + 1)
                             for j in range(max(0, int((b[1] - a[1] - alto) / 1.5)) + 1)), key=lambda q: (q[0] - cx0) ** 2 + (q[1] - cy0) ** 2)
            for cx, cy in cands:
                caja = (cx - ancho / 2, cy - alto / 2, cx + ancho / 2, cy + alto / 2)
                if caja[0] >= a[0] and caja[2] <= b[0] and caja[1] >= a[1] and caja[3] <= b[1] and ub.libre(caja, holgura=0.2):
                    ubicado = (cx, cy, caja, t1, t2, disp, ancho, alto, rr)
                    break
            if ubicado:
                break
        if not ubicado:
            SIN_ETIQUETA.append(f"{nivel['id']}:{num} (encimada)")
            t1, t2, disp, ancho, alto, rr = formas[-1]
            ubicado = (cx0, cy0, (cx0 - ancho / 2, cy0 - alto / 2, cx0 + ancho / 2, cy0 + alto / 2), t1, t2, disp, ancho, alto, rr)
        cx, cy, caja, t1, t2, disp, ancho, alto, rr = ubicado
        paso = rr * 2.3
        ub.ocupar(caja)
        tx = cx if disp != "lado" else caja[0] + (ancho - n_acab * paso - 1.5) / 2
        ty = caja[1] if disp != "lado" else cy - (t1 * 1.35 + t2 * 1.6 + 1.2) / 2
        cap = (f'<rect x="{f(caja[0])}" y="{f(caja[1])}" width="{f(ancho)}" height="{f(alto)}" rx="0.6" fill="{PAPEL}" fill-opacity="0.92" stroke="{TINTA}" stroke-width="0.2"/>'
               + texto(tx, ty + t1 * 1.35, nombre, t1, "700", TINTA, "middle") + texto(tx, ty + t1 * 1.35 + t2 * 1.6, linea2, t2, "400", GRIS, "middle"))
        for k, cod in enumerate(acab if n_acab else ()):
            if disp == "abajo":
                cap += rombo((cx + (k - (n_acab - 1) / 2) * paso, caja[3] - rr - 0.3), cod, r=rr)
            else:
                cap += rombo((caja[2] - 0.75 - (n_acab - k - 0.5) * paso, cy), cod, r=rr)
        capas.append(cap)
    for caja_giro, _, _ in giros:
        if caja_giro:
            ub.ocupar(caja_giro, "giro")
    centro_ed = M(W / 2, (pie - 15) / 2)
    for ab in nivel["aberturas"]:
        if ab[1] != "ventana":
            continue
        m = pp.muro(p, ab[2])
        anc = M(*pp.en_muro(m, ab[3], 0))
        _, u, n, _ = pp.eje(m)
        hacia = 1 if (centro_ed[0] - anc[0]) * n[0] + (centro_ed[1] - anc[1]) * n[1] > 0 else -1
        dirs = [((h * n[0] + sgn * u[0]) / math.sqrt(2), (h * n[1] + sgn * u[1]) / math.sqrt(2)) for h in (hacia, -hacia) for sgn in (1, -1)]
        r = ub.con_directriz(anc, dirs[:2], (3.4, 3.0), ignorar=ab[2], largos=(6, 8, 10, 13, 16)) or ub.con_directriz(anc, dirs[2:], (3.4, 3.0), ignorar=ab[2], largos=(5, 7, 9, 12, 16))
        if r:
            c, segs = r
            capas.append(directriz(segs, AZUL) + tag_ventana(c, ab[7]))
        else:
            SIN_ETIQUETA.append(f"{nivel['id']}:{ab[0]}")
    if modo == "arq":
        etiquetados = set()
        for m, t0, t1, caja in sorted(tramos, key=lambda z: -(z[2] - z[1])):
            if m[0] in etiquetados:
                continue
            _, u, n, _ = pp.eje(m)
            for frac in (0.5, 0.3, 0.7, 0.15, 0.85, 0.4, 0.6, 0.22, 0.78):
                anc = M(*pp.en_muro(m, t0 + (t1 - t0) * frac, 0))
                exterior = m[0].startswith("m-") and m[0] in ("m-n", "m-e", "m-s", "m-o")
                lados = [1 if (centro_ed[0] - anc[0]) * n[0] + (centro_ed[1] - anc[1]) * n[1] > 0 else -1] if exterior else [1, -1]
                dirs = [((h * n[0] + sgn * u[0]) / math.sqrt(2), (h * n[1] + sgn * u[1]) / math.sqrt(2)) for h in lados for sgn in (1, -1)]
                r = ub.con_directriz(anc, dirs, (4.2, 1.8), ignorar=m[0])
                if r:
                    c, segs = r
                    capas.append(directriz(segs) + tag_muro(c, MUROS[m[3]]))
                    etiquetados.add(m[0])
                    break
        SIN_ETIQUETA.extend(f"{nivel['id']}:{m[0]}" for m in p["muros"] if m[0] not in etiquetados)
    s.extend(capas)
    s.append("</g>")
    titulo_y = (recinto[3] + 27) if modo == "arq" else recinto[3] + 10
    s.append(titulo_vista(ox - 18, titulo_y, f"{numero}. {nivel['nombre']}", "ESC. 1:100"))
    return "".join(s)


# ---- corte, fachada y axonometría --------------------------------------------------------------------------------------------------------------------
def huecos(proj):
    """Vanos de las fachadas sur y este, con sus alturas tomadas de los tipos: (cara, desde, hasta, z0, z1, coordenada del muro)."""
    out = []
    for nivel in proj["niveles"]:
        p = modelo(nivel)
        for ab in nivel["aberturas"]:
            if ab[2] not in ("m-s", "m-e"):
                continue
            m = pp.muro(p, ab[2])
            tipo = PUERTAS.get(ab[7]) or VENTANAS.get(ab[7])
            z0 = nivel["z"] + tipo.get("antepecho", 0) * 100
            q1, q2 = pp.en_muro(m, ab[3] - ab[4] / 2, 0), pp.en_muro(m, ab[3] + ab[4] / 2, 0)
            if ab[2] == "m-s":
                out.append(("s", min(q1[0], q2[0]), max(q1[0], q2[0]), z0, z0 + tipo["alto"] * 100, m[1][1]))
            else:
                out.append(("e", min(q1[1], q2[1]), max(q1[1], q2[1]), z0, z0 + tipo["alto"] * 100, m[1][0]))
    return out


def corte(proj, ox, suelo):
    yc = proj["corte_y"]
    Z = lambda z: suelo - z * ESC                                                 # noqa: E731
    X = lambda x: ox + x * ESC                                                    # noqa: E731
    W = proj["niveles"][0]["ancho"]
    s = ['<g id="CORTE-AA">', f'<rect x="{f(X(-80))}" y="{f(Z(0))}" width="{f((W + 160) * ESC)}" height="5" fill="url(#tierra)"/>']
    for nivel in proj["niveles"]:
        for m in nivel["muros"]:
            (ax, ay), (bx, by) = m[1], m[2]
            if ax != bx or not min(ay, by) <= yc <= max(ay, by):
                continue
            ab = next((a for a in nivel["aberturas"] if a[2] == m[0] and abs(min(ay, by) + a[3] - yc) < a[4] / 2), None)
            z0, z1 = nivel["z"], nivel["z"] + nivel["alto"]
            if ab is None:
                macizo = [(z0, z1)]
            elif ab[1] == "ventana":
                t = VENTANAS[ab[7]]
                macizo = [(z0, z0 + t["antepecho"] * 100), (z0 + (t["antepecho"] + t["alto"]) * 100, z1)]
            else:
                macizo = [(z0 + PUERTAS[ab[7]]["alto"] * 100, z1)]
            for a, b in macizo:
                if b > a:
                    s.append(f'<rect x="{f(X(ax - m[3] / 2))}" y="{f(Z(b))}" width="{f(m[3] * ESC)}" height="{f((b - a) * ESC)}" fill="{TINTA}"/>')
            if ab is not None and ab[1] == "ventana":
                t = VENTANAS[ab[7]]
                for dx in (-3, 3):
                    s.append(f'<line x1="{f(X(ax + dx))}" y1="{f(Z(z0 + (t["antepecho"] + t["alto"]) * 100))}" x2="{f(X(ax + dx))}" y2="{f(Z(z0 + t["antepecho"] * 100))}" stroke="{AZUL}" stroke-width="0.2"/>')
    for x0, x1, z0, z1 in proj["losas"] + proj["parapetos"]:
        s.append(f'<rect x="{f(X(x0))}" y="{f(Z(z1))}" width="{f((x1 - x0) * ESC)}" height="{f((z1 - z0) * ESC)}" fill="{TINTA}"/>')
    xb, xt, z0, z1, n = proj["escalera_corte"]
    paso, alza = (xt - xb) / n, (z1 - z0) / n
    pts = [(xb, z0)]
    for k in range(n):
        pts += [(xb + k * paso, z0 + (k + 1) * alza), (xb + (k + 1) * paso, z0 + (k + 1) * alza)]
    pts += [(xt, z1 - 20), (xb - paso * 0.8, z0)]
    s.append(f'<polygon points="{" ".join(f"{f(X(x))},{f(Z(z))}" for x, z in pts)}" fill="{TINTA}" fill-opacity="0.85"/>')
    s.append(f'<line x1="{f(X(-80))}" y1="{f(Z(0))}" x2="{f(X(W + 80))}" y2="{f(Z(0))}" stroke="{TINTA}" stroke-width="0.6"/>')
    for nombre, z in proj["cotas_nivel"]:
        s.append(f'<line x1="{f(X(-80))}" y1="{f(Z(z))}" x2="{f(X(W + 120))}" y2="{f(Z(z))}" stroke="{AZUL}" stroke-width="0.15" stroke-dasharray="6 1.5 1 1.5"/>'
                 f'<path d="M{f(X(W + 120))} {f(Z(z))} l1.6 -1.6 l1.6 1.6 z" fill="{AZUL}"/>' + texto(X(W + 120) + 4, Z(z) + 0.7, nombre, 1.8, "400", AZUL))
    for nombre, x in proj["ejes_x"]:
        s.append(f'<line x1="{f(X(x))}" y1="{f(Z(760))}" x2="{f(X(x))}" y2="{f(Z(-60))}" stroke="{GRIS}" stroke-width="0.15" stroke-dasharray="6 1.5 1 1.5"/>' + burbuja(X(x), Z(760) - 3.5, nombre))
    s.append("</g>" + titulo_vista(ox - 18, suelo + 18, "4. CORTE A-A", "ESC. 1:100"))
    return "".join(s)


def fachada(proj, ox, suelo):
    Z = lambda z: suelo - z * ESC                                                 # noqa: E731
    X = lambda x: ox + x * ESC                                                    # noqa: E731
    W = proj["niveles"][0]["ancho"]
    hs = [h for h in huecos(proj) if h[0] == "s"]
    s = ['<g id="FACHADA-SUR">', f'<rect x="{f(X(-80))}" y="{f(Z(0))}" width="{f((W + 160) * ESC)}" height="5" fill="url(#tierra)"/>']
    for x0, y0, x1, y1, z0, z1 in sorted(proj["volumenes"], key=lambda v: v[3]):
        tono = "#e9ecef" if y1 < 900 else "#d6dbe0"
        s.append(f'<rect x="{f(X(x0))}" y="{f(Z(z1))}" width="{f((x1 - x0) * ESC)}" height="{f((z1 - z0) * ESC)}" fill="{tono}" stroke="{TINTA}" stroke-width="0.25"/>')
        for _, a, b, za, zb, y in hs:
            if abs(y - y1) < 1 and z0 <= za and zb <= z1:
                s.append(f'<rect x="{f(X(a))}" y="{f(Z(zb))}" width="{f((b - a) * ESC)}" height="{f((zb - za) * ESC)}" fill="#a9c7e3" stroke="{TINTA}" stroke-width="0.25"/>'
                         f'<line x1="{f(X((a + b) / 2))}" y1="{f(Z(zb))}" x2="{f(X((a + b) / 2))}" y2="{f(Z(za))}" stroke="{TINTA}" stroke-width="0.12"/>')
    s.append(f'<line x1="{f(X(-80))}" y1="{f(Z(0))}" x2="{f(X(W + 80))}" y2="{f(Z(0))}" stroke="{TINTA}" stroke-width="0.8"/>')
    for nombre, x in proj["ejes_x"]:
        s.append(f'<line x1="{f(X(x))}" y1="{f(Z(760))}" x2="{f(X(x))}" y2="{f(Z(-60))}" stroke="{GRIS}" stroke-width="0.15" stroke-dasharray="6 1.5 1 1.5"/>' + burbuja(X(x), Z(760) - 3.5, nombre))
    s.append("</g>" + titulo_vista(ox - 18, suelo + 18, "5. FACHADA SUR", "ESC. 1:100"))
    return "".join(s)


def axonometria(proj, ox, oy, k=0.075, numero=6):
    c, sn = math.cos(math.radians(30)), math.sin(math.radians(30))
    P = lambda x, y, z: (ox + (x - y) * c * k, oy + ((x + y) * sn - z) * k)      # noqa: E731
    poly = lambda pts, fill: f'<polygon points="{" ".join(f"{f(a)},{f(b)}" for a, b in pts)}" fill="{fill}" stroke="{TINTA}" stroke-width="0.25" stroke-linejoin="round"/>'   # noqa: E731
    W, H = proj["niveles"][0]["ancho"], proj["niveles"][0]["fondo"]
    s = ['<g id="AXONOMETRIA">', poly([P(-120, -120, 0), P(W + 150, -120, 0), P(W + 150, H + 150, 0), P(-120, H + 150, 0)], "#f1f2ee"),
         f'<polygon points="{" ".join(f"{f(a)},{f(b)}" for a, b in [P(0, H, 0), P(-110, H, 0), P(-110, 0, 0), P(0, 0, 0)])}" fill="#000" fill-opacity="0.07"/>']
    hs = huecos(proj)
    for x0, y0, x1, y1, z0, z1 in sorted(proj["volumenes"], key=lambda v: (v[4], v[0] + v[1])):
        s.append(poly([P(x0, y1, z0), P(x1, y1, z0), P(x1, y1, z1), P(x0, y1, z1)], "#d9dde1"))
        s.append(poly([P(x1, y0, z0), P(x1, y1, z0), P(x1, y1, z1), P(x1, y0, z1)], "#b9c0c7"))
        s.append(poly([P(x0, y0, z1), P(x1, y0, z1), P(x1, y1, z1), P(x0, y1, z1)], "#f7f8f9"))
        for cara, a, b, za, zb, coord in hs:
            if cara == "s" and abs(coord - y1) < 1 and z0 <= za and zb <= z1 and x0 <= a and b <= x1:
                s.append(poly([P(a, y1, za), P(b, y1, za), P(b, y1, zb), P(a, y1, zb)], "#5f7f9e"))
            if cara == "e" and abs(coord - x1) < 1 and z0 <= za and zb <= z1 and y0 <= a and b <= y1:
                s.append(poly([P(x1, a, za), P(x1, b, za), P(x1, b, zb), P(x1, a, zb)], "#4f6d8a"))
    s.append("</g>")
    return "".join(s) + titulo_vista(26, 568, f"{numero}. AXONOMETRÍA SUDESTE", "SIN ESCALA")


# ---- columna derecha ---------------------------------------------------------------------------------------------------------------------------------
def envolver(t, ancho_mm, tam):
    por_linea = max(4, int(ancho_mm / (tam * 0.52)))
    palabras, lineas, actual = str(t).split(), [], ""
    for p in palabras:
        if len(actual) + len(p) + (1 if actual else 0) > por_linea:
            lineas.append(actual)
            actual = p
        else:
            actual = f"{actual} {p}" if actual else p
    return lineas + [actual] if actual else lineas or [""]


def tabla(x, y, w, titulo, columnas, filas):
    """Tabla del ancho de la columna: título en negrita de 3 mm, encabezados en negrita, datos de 2 mm con texto envuelto."""
    total = sum(r for _, r in columnas)
    anchos = [w * r / total for _, r in columnas]
    s = [texto(x, y, titulo, 3.0, "700")]
    y += 2.5
    def fila(celdas, tam, peso, fondo=None):
        nonlocal y
        partes = [envolver(c, a - 2, tam) for c, a in zip(celdas, anchos)]
        alto = max(len(p) for p in partes) * tam * 1.25 + 2
        if fondo:
            s.append(f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(alto)}" fill="{fondo}"/>')
        xx = x
        for lineas, a in zip(partes, anchos):
            for i, l in enumerate(lineas):
                s.append(texto(xx + 1, y + tam * 1.05 + i * tam * 1.25 + 0.6, l, tam, peso))
            xx += a
        s.append(f'<line x1="{f(x)}" y1="{f(y + alto)}" x2="{f(x + w)}" y2="{f(y + alto)}" stroke="{TINTA}" stroke-width="0.12"/>')
        y += alto
        return alto
    y0 = y
    fila([n for n, _ in columnas], 1.8, "700", "#e9ecef")
    for celdas in filas:
        fila(celdas, 2.0, "400")
    xx = x
    for a in anchos[:-1]:
        xx += a
        s.append(f'<line x1="{f(xx)}" y1="{f(y0)}" x2="{f(xx)}" y2="{f(y)}" stroke="{TINTA}" stroke-width="0.12"/>')
    s.append(f'<rect x="{f(x)}" y="{f(y0)}" width="{f(w)}" height="{f(y - y0)}" fill="none" stroke="{TINTA}" stroke-width="0.3"/>')
    return "".join(s), y


def rotulo(x, w, proj, lamina, contenido):
    ry = HOJA[1] - 12 - 112
    s = [f'<rect x="{x}" y="{ry}" width="{w}" height="112" fill="#f6f7f8" stroke="{TINTA}" stroke-width="0.5"/>']
    filas = [("PROYECTO", proj["titulo"]), ("AUTOR", "Claude · EPC-291 (proyecto de autoría propia)"), ("CONTENIDO", contenido), ("ESCALA", "1:100"),
             ("FORMATO / FECHA / REV.", "A1 (841 × 594 mm) · 2026-11-02 · Rev. 0"), ("NIVEL DE COMPLEJIDAD", proj["complejidad"])]
    yy = ry + 9
    for etiqueta, valor in filas:
        s.append(texto(x + 6, yy, etiqueta, 1.8, "700", GRIS) + texto(x + 6, yy + 4.2, valor, 2.3, "700" if etiqueta == "PROYECTO" else "400"))
        s.append(f'<line x1="{x}" y1="{f(yy + 6.5)}" x2="{x + w}" y2="{f(yy + 6.5)}" stroke="{TINTA}" stroke-width="0.15"/>')
        yy += 12.5
    s.append(texto(x + w - 6, HOJA[1] - 19, lamina, 11, "700", TINTA, "end"))
    return "".join(s)


def leyenda_etiquetas(x, y):
    s = [texto(x + 6, y, "ETIQUETAS", 3.0, "700")]
    y += 7
    for dib, t in ((tag_puerta((x + 10, y - 1), "P-01"), "Puerta: tipo (ver tabla de puertas, A-202)"),
                   (tag_ventana((x + 10, y + 7), "V-01"), "Ventana: tipo (ver tabla de ventanas, A-202)"),
                   (tag_muro((x + 10, y + 15), "M-01"), "Muro: tipo y material (ver tabla de acabados)"),
                   (rombo((x + 10, y + 23), "P-01"), "Acabado: código de material")):
        s.append(dib)
    for k, t in enumerate(("Puerta: tipo (ver tabla de puertas, A-202)", "Ventana: tipo (ver tabla de ventanas, A-202)", "Muro: tipo y material (ver tabla de acabados)",
                           "Acabado de piso, cielorraso o revestimiento")):
        s.append(texto(x + 18, y + k * 8, t, 2.0))
    y += 31
    s.append(f'<rect x="{x + 4}" y="{f(y - 3)}" width="14" height="6.4" rx="0.6" fill="{PAPEL}" stroke="{TINTA}" stroke-width="0.2"/>' + texto(x + 11, y - 0.4, "LOCAL", 1.6, "700", TINTA, "middle")
             + texto(x + 11, y + 2.2, "PB-01 · m²", 1.3, "400", GRIS, "middle") + texto(x + 22, y + 0.6, "Local: nombre, número y superficie", 2.0))
    return "".join(s), y + 10


def hoja(cuerpo, titulo):
    W, H = HOJA
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}"><title>{titulo}</title>'
            '<defs><pattern id="tierra" width="3" height="3" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="3" stroke="#8b8b8b" stroke-width="0.4"/></pattern></defs>'
            f'<rect width="{W}" height="{H}" fill="{PAPEL}"/><rect x="12" y="12" width="{W - 24}" height="{H - 24}" fill="none" stroke="{TINTA}" stroke-width="0.7"/>{cuerpo}</svg>')


def lamina_arquitectura(proj):
    col = 640
    s = []
    for i, (nivel, ox) in enumerate(zip(proj["niveles"], (62, 256, 450))):
        s.append(planta(proj, nivel, ox, 64, i + 1, "arq"))
    s.append(corte(proj, 256, 345))
    s.append(fachada(proj, 450, 345))
    s.append(axonometria(proj, 112, 448))
    w = HOJA[0] - 12 - col
    s.append(f'<line x1="{col}" y1="12" x2="{col}" y2="{HOJA[1] - 12}" stroke="{TINTA}" stroke-width="0.5"/>')
    y = 24
    s.append(texto(col + 6, y, "NOTAS GENERALES", 3.0, "700"))
    y += 6.5
    for i, n in enumerate(proj["notas"]):
        for j, l in enumerate(envolver(n, w - 16, 2.0)):
            s.append((texto(col + 6, y, f"{i + 1}.", 2.0, "700") if j == 0 else "") + texto(col + 11, y, l, 2.0))
            y += 3.6
        y += 1.2
    y += 6
    ley, y = leyenda_etiquetas(col, y)
    s.append(ley)
    y += 6
    filas = []
    total = 0.0
    for nivel in proj["niveles"]:
        for nombre, (x0, y0, x1, y1), num, _ in nivel["locales"]:
            a = (x1 - x0) * (y1 - y0) / 1e4
            total += a if nombre != "TERRAZA" else 0
            filas.append([num, nombre.title(), f"{a:.2f}".replace(".", ",") + (" (desc.)" if nombre == "TERRAZA" else "")])
    filas.append(["", "TOTAL CUBIERTO", f"{total:.2f}".replace(".", ",")])
    t, y = tabla(col + 6, y, w - 12, "CUADRO DE LOCALES", [("LOCAL", 1), ("NOMBRE", 2.4), ("SUP. (m²)", 1.3)], filas)
    s.append(t)
    s.append(rotulo(col, w, proj, "A-201", "Plantas, corte, fachada y axonometría"))
    return hoja("".join(s), f"{proj['titulo']} — A-201")


def lamina_carpinterias(proj):
    col = 400
    w = HOJA[0] - 12 - col
    niveles = [n for n in proj["niveles"] if n["locales"]]
    s = []
    for i, (nivel, ox) in enumerate(zip(niveles, (62, 232))):
        s.append(planta(proj, nivel, ox, 64, i + 1, "acab"))
    s.append(axonometria(proj, 112, 448, numero=3))
    s.append(f'<line x1="{col}" y1="12" x2="{col}" y2="{HOJA[1] - 12}" stroke="{TINTA}" stroke-width="0.5"/>')
    # cantidades contadas del modelo y filtro de lo que aparece en las plantas de la lámina
    cuenta = {}
    for nivel in niveles:
        for ab in nivel["aberturas"]:
            cuenta[ab[7]] = cuenta.get(ab[7], 0) + 1
    usados = set()
    for nivel in niveles:
        usados |= {MUROS[m[3]] for m in nivel["muros"]}
        for _, _, _, acab in nivel["locales"]:
            usados |= set(acab)
    m = lambda v: f"{v:.2f}"                                                      # noqa: E731
    cols_c = [("CLAVE / TAG", 1.1), ("CANT.", 0.7), ("ANCHO (m)", 0.9), ("ALTO (m)", 0.9), ("ALFÉIZAR / ANTEPECHO (m)", 1.3), ("MATERIAL (Marco / Hoja)", 2.6),
              ("TIPO DE APERTURA", 1.6), ("UBICACIÓN / OBSERVACIONES", 3.3)]
    y = 24
    t, y = tabla(col + 6, y, w - 12, "TABLA DE CARPINTERÍAS — PUERTAS", cols_c,
                 [[k, str(cuenta[k]), m(v["ancho"]), m(v["alto"]), "—", v["material"], v["apertura"], v["obs"]] for k, v in PUERTAS.items() if k in cuenta])
    s.append(t)
    y += 9
    t, y = tabla(col + 6, y, w - 12, "TABLA DE CARPINTERÍAS — VENTANAS", cols_c,
                 [[k, str(cuenta[k]), m(v["ancho"]), m(v["alto"]), m(v["antepecho"]), v["material"], v["apertura"], v["obs"]] for k, v in VENTANAS.items() if k in cuenta])
    s.append(t)
    y += 9
    t, y = tabla(col + 6, y, w - 12, "TABLA DE ACABADOS Y MATERIALES",
                 [("CÓDIGO", 0.9), ("ELEMENTO", 1.5), ("DESCRIPCIÓN TÉCNICA", 3.2), ("ACABADO / COLOR", 1.9), ("MARCA / REF.", 1.4), ("ESPESOR (m)", 1.0), ("OBSERVACIONES", 2.6)],
                 [[k, *v] for k, v in MATERIALES.items() if k in usados])
    s.append(t)
    y += 6
    s.append(texto(col + 6, y, "Cantidades contadas del modelo; materiales filtrados a los que aparecen en las plantas de esta lámina.", 1.8, "400", GRIS))
    s.append(rotulo(col, w, proj, "A-202", "Plantas de acabados, carpinterías y materiales"))
    return hoja("".join(s), f"{proj['titulo']} — A-202")


def probar_motor(proj, out):
    sys.path.insert(0, str(RAIZ / "src"))
    from epc_arch import recognize                                                 # noqa: E402
    filas = []
    for nivel in proj["niveles"]:
        if not nivel["muros"]:
            continue
        p = {"estilo": "relleno", "ancho": nivel["ancho"], "alto": nivel["fondo"], "muros": nivel["muros"],
             "aberturas": [a[:7] if a[1] != "corrediza" else (*a[:1], "hueco", *a[2:7]) for a in nivel["aberturas"]],
             "ambientes": [(n, r) for n, r, _, _ in nivel["locales"] if n != "TERRAZA"], "mobiliario": nivel["mobiliario"]}
        pp.png(p, out / f"{nivel['id']}.png")
        pp.dxf(p, out / f"{nivel['id']}.dxf")
        verdad = {"puertas": sum(1 for a in p["aberturas"] if a[1] == "puerta"), "ventanas": sum(1 for a in p["aberturas"] if a[1] == "ventana")}
        for ext in ("dxf", "png"):
            r = recognize((out / f"{nivel['id']}.{ext}").read_bytes(), f"{nivel['id']}.{ext}")
            (out / f"motor_{nivel['id']}_{ext}.json").write_text(json.dumps(r.as_dict(), indent=1, ensure_ascii=False), encoding="utf-8")
            filas.append((nivel["id"], ext, verdad, r.architecture.counts(), len(r.architecture.rooms)))
    return filas


def main():
    SALIDA.mkdir(parents=True, exist_ok=True)
    (SALIDA / "A-201.svg").write_text(lamina_arquitectura(P02), encoding="utf-8")
    (SALIDA / "A-202.svg").write_text(lamina_carpinterias(P02), encoding="utf-8")
    print(f"proyecto 02: {P02['titulo']} -> {SALIDA}")
    print("  sin etiqueta:", ", ".join(SIN_ETIQUETA) or "ninguno")
    if "--sin-motor" not in sys.argv:
        for nid, ext, verdad, c, amb in probar_motor(P02, SALIDA):
            print(f"  {nid}.{ext:3}  puertas {c['doors']}/{verdad['puertas']}  ventanas {c['windows']}/{verdad['ventanas']}  muros {c['walls']}  ambientes {amb}")


if __name__ == "__main__":
    main()
