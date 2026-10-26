"""Capas del SLD y del MLD: cada entidad va al rol de capa que le toca (nombre, color y grosor: catálogo de epc_dxf).

Todos los DXF del SLD llevan exactamente la misma tabla de capas, con su estado:
color, tipo de línea, encendida/apagada, congelada y bloqueada.
Asignación por región (mm sobre lámina A1 841 x 594):
  - rótulo IRAM (x >= 648 y y >= 500) y logos       -> sld.titleblock
  - marco / zona útil de la lámina (cerca del borde) -> sld.sheet
  - resto de textos y columna de referencias/cálculos -> sld.text
  - resto de líneas del diagrama (símbolos y conductores) -> sld.diagram
  Pendiente: separar símbolos de conductores (requiere etiquetar el SVG).
"""
import math
import os
import ezdxf
import xml.etree.ElementTree as ET

from epc_dxf import layers as _L

# Las capas no se escriben aquí: el catálogo (epc_dxf.layers) dice cómo se llama y cómo se ve cada rol.
ROLES = ('sld.diagram', 'sld.text', 'sld.titleblock', 'sld.sheet')
ANTIGUAS = ('LINEAS', 'TEXTO', 'LOGOS')
RX, RY = 648.0, 500.0          # esquina del rótulo (mm)
BORDE = 35.0                   # distancia al borde de la lámina para considerarlo marco


def _en_rotulo(x, y):
    return x >= RX and y >= RY


def _en_marco(pts, w=841.0, h=594.0):
    return all(x <= BORDE or x >= w - BORDE or y <= BORDE or y >= h - BORDE for x, y in pts)


def _puntos(e):
    t = e.dxftype()
    if t == 'LINE':
        return [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]
    if t == 'LWPOLYLINE':
        return [(p[0], p[1]) for p in e.get_points('xy')]
    if t == 'TEXT':
        return [(e.dxf.insert.x, e.dxf.insert.y)]
    return []


def _color_svg(e):
    """(r, g, b) del trazo de una forma SVG, o None si no tiene trazo."""
    c = getattr(e, 'stroke', None)
    if c is None or c.value is None or str(c.value).lower() == 'none':
        return None
    return (int(c.red), int(c.green), int(c.blue))


def _catalogo(catalog):
    return _L.resolve(catalog)


def _formato_a3(a3):
    return (os.environ.get('SLD_FORMATO', 'A1') == 'A3') if a3 is None else a3


def _poner_rol(ent, extra, cat):
    """El rol del elemento en el SVG (`data-layer`) manda sobre la zona de la lámina: la entidad va a la capa que el catálogo da a ese rol."""
    if extra.get('role'):
        ent.dxf.layer = _L.name(extra['role'], cat)


def colorear(svg_path, dxf_path, catalog=None, a3=None):
    """Restituye color y grosor del trazo del SVG en las entidades del DXF.

    El convertidor del plugin no conserva el color (todo queda con el color de la capa).
    Recorre las formas del SVG en el mismo orden en que el convertidor las escribe
    y asigna a cada entidad LINE/LWPOLYLINE/TEXT su color y grosor. Los logos (HATCH y
    contorno en capa LOGOS) no se tocan.
    """
    import sys as _sys
    cat = _catalogo(catalog)
    from ezdxf.colors import rgb2int
    from svgelements import SVG, Circle, Ellipse, Path, Polygon, Rect, Shape, SimpleLine, Text
    from epc_dxf import svg_to_dxf as S
    svg = SVG.parse(svg_path, reify=True)
    elementos = list(svg.elements())
    formas = [e for e in elementos if isinstance(e, Shape) and not isinstance(e, Text)]
    _, omitir = S._logos(svg_path, formas)
    # secuencia esperada de entidades: (tipo, color, grosor_mm) o None para logos
    import os as _os
    a3 = _formato_a3(a3)
    # A3: el texto del rótulo del plugin está fuera de <g id="dibujo">; el del diagrama y la tabla, dentro.
    # Se empareja cada texto del SVG con su nodo XML en orden (mismo texto), así no depende de la posición.
    fuera = {}
    if a3:
        lista = []
        def _recorrer(el, dentro):
            etiqueta = el.tag.split('}')[-1]
            d = dentro or el.get('id') == 'dibujo'
            if etiqueta == 'text':
                cadena = ''.join(el.itertext()).strip()
                if cadena: lista.append((cadena, not d))
            for hijo in el:
                _recorrer(hijo, d)
        _recorrer(ET.parse(svg_path).getroot(), False)
        p_xml = 0
        for idx, e in enumerate(elementos):
            if isinstance(e, Text) and e.text and e.text.strip():
                cad = e.text.strip()
                j = p_xml
                while j < len(lista) and lista[j][0] != cad: j += 1
                if j < len(lista):
                    fuera[idx] = lista[j][1]; p_xml = j + 1
    FACTOR_TEXTO = 1.7 / 2.0   # el texto principal (2 mm en el SVG) queda en 1,7 mm; los demás, proporcionales
    alto_mm = 0.0
    if svg.height is not None:
        alto_mm = float(svg.height.in_px() if hasattr(svg.height, 'in_px') else svg.height) / S.PX_POR_MM
    esperado = []
    rellenos = []   # (color, bucles) de las formas cerradas con relleno (flechas, puntos de unión...)
    for idx, e in enumerate(elementos):
        if isinstance(e, Text):
            if e.text and e.text.strip():
                px, py = S._pos_mm(e)
                es_rotulo = bool(fuera.get(idx, False)) and px >= 230.0 and 231.0 <= py <= 282.5   # rótulo: fuera del dibujo y en su zona
                negrita = str(e.values.get('font-weight', '')).lower() == 'bold' or float(getattr(e, 'font_weight', 400) or 400) >= 600
                col_txt = S._relleno(e)   # el color de un texto SVG es su relleno
                if a3 and not es_rotulo:
                    if fuera.get(idx, False):
                        altura = 1.7   # letras del marco de la lámina
                    else:   # proporcional al SVG: altura de mayúscula = 0,716 · tamaño de fuente efectivo
                        sc = math.sqrt(abs(e.transform.determinant)) / S.PX_POR_MM
                        altura = max(1.0, round(FACTOR_TEXTO * 0.716 * float(e.font_size or 2.0) * sc, 2))
                    esperado.append(('TEXT', col_txt, altura, {'bold': negrita, 'pos': None if fuera.get(idx, False) else (px, py), 'role': e.values.get('data-layer')}))
                else:
                    esperado.append(('TEXT', None if es_rotulo else col_txt, None, {'bold': negrita and not es_rotulo, 'role': e.values.get('data-layer')}))
            continue
        if not isinstance(e, (SimpleLine, Rect, Polygon, Circle, Ellipse, Path)):
            continue
        if getattr(e, 'id', None) == 'papel':
            continue
        if id(e) in omitir:
            for _ in S._polilineas(e):
                esperado.append(('LOGO', None, None, {}))
            continue
        ancho = float(getattr(e, 'stroke_width', 0.25) or 0.25) / S.PX_POR_MM
        # trazos discontinuos: patrón del SVG (unidades de usuario) pasado a mm con la escala del grupo
        patron = None
        dash = e.values.get('stroke-dasharray')
        sw0 = float(e.values.get('stroke-width') or 0)
        if dash and str(dash).lower() != 'none' and sw0 > 0:
            nums = [float(x) for x in str(dash).replace(',', ' ').split()]
            if len(nums) % 2: nums *= 2
            patron = [v * ancho / sw0 for v in nums]
        polis = S._polilineas(e)
        for _ in polis:
            esperado.append(('LINE', _color_svg(e), ancho, {'dash': patron, 'role': e.values.get('data-layer')}))
        col_rell = S._relleno(e)
        if col_rell and col_rell != (255, 255, 255):
            bucles = [pts for pts, cerr in polis if cerr and len(pts) > 2]
            if bucles: rellenos.append((col_rell, bucles))
    doc = ezdxf.readfile(dxf_path)
    ents = [x for x in doc.modelspace() if x.dxftype() in ('TEXT', 'LINE', 'LWPOLYLINE')]
    if len(ents) != len(esperado):
        print(f'AVISO colores DXF: {len(ents)} entidades vs {len(esperado)} formas; no se asignan colores', file=_sys.stderr)
        return False
    if 'ARIAL_BOLD' not in doc.styles:
        doc.styles.add('ARIAL_BOLD', font='arialbd.ttf')
    tipos_dash = {}
    def _color(ent, col):
        if col is None: return
        if col == (0, 0, 0): ent.dxf.color = 7          # negro -> color 7 (se ve negro o blanco según el fondo del CAD)
        else: ent.dxf.true_color = rgb2int(col)
    textos_diagrama = []
    for ent, (tipo, color, ancho, extra) in zip(ents, esperado):
        _poner_rol(ent, extra, cat)
        if tipo == 'TEXT':
            if extra.get('bold'): ent.dxf.style = 'ARIAL_BOLD'
            if extra.get('pos'):   # el convertidor del plugin corre textos del diagrama (lógica de rótulo): vuelven a su posición del SVG
                ox, oy = _ancla(ent)
                ent.translate(extra['pos'][0] - ox, (alto_mm - extra['pos'][1]) - oy, 0)
            if ancho:                            # ancho = altura del texto (mm) en este caso
                ent.dxf.height = ancho
                textos_diagrama.append(ent)
            _color(ent, color)
            continue
        if tipo == 'LOGO' or color is None:
            continue
        pat = extra.get('dash')
        if pat:   # linetype propio para este patrón (independiente de la capa)
            clave = tuple(round(v, 3) for v in pat)
            if clave not in tipos_dash:
                nombre = f'SVG_DASH_{len(tipos_dash) + 1}'
                segs = [v if i % 2 == 0 else -v for i, v in enumerate(pat)]
                doc.linetypes.add(nombre, pattern=[sum(abs(x) for x in segs)] + segs)
                tipos_dash[clave] = nombre
            ent.dxf.linetype = tipos_dash[clave]
        if ent.dxf.layer in {_L.name('sld.titleblock', cat), _L.name('sld.sheet', cat)}:   # rótulo y marco: quedan con el color de su capa
            continue
        _color(ent, color)
        if tipo == 'LINE' and ancho:
            ent.dxf.lineweight = max(0, min(211, int(round(ancho * 100))))
    # rellenos de las formas cerradas (flechas rojas, puntos de unión...): HATCH como en el SVG
    msp = doc.modelspace()
    for col, bucles in rellenos:
        for exterior, interiores in S._area_relleno(bucles):
            h = msp.add_hatch(color=7, dxfattribs={'layer': _L.name('sld.titleblock', cat) if col == (0, 0, 0) else _L.name('sld.diagram', cat)})
            if col != (0, 0, 0): h.dxf.true_color = rgb2int(col)
            h.paths.add_polyline_path([(x, alto_mm - y) for x, y in exterior], is_closed=True)
            for hueco in interiores:
                h.paths.add_polyline_path([(x, alto_mm - y) for x, y in hueco], is_closed=True)
    if textos_diagrama:
        _separar_textos(textos_diagrama)
    doc.saveas(dxf_path)
    return True


def _caja_texto(e):
    """Polígono (mm) que ocupa un TEXT, aprox.: ancho ~0,6·altura por carácter, orientado con su rotación."""
    from shapely.geometry import Polygon
    h = float(e.dxf.height)
    w = max(len(e.dxf.text), 1) * 0.6 * h
    r = math.radians(float(e.dxf.get('rotation', 0.0)))
    ux, uy, vx, vy = math.cos(r), math.sin(r), -math.sin(r), math.cos(r)
    ax, ay = _ancla(e)
    off = 0.0
    al = str(e.get_placement()[0])
    if 'CENTER' in al or 'MIDDLE' in al: off = -w / 2
    elif 'RIGHT' in al: off = -w
    bx, by = ax + ux * off, ay + uy * off
    pts = [(bx, by), (bx + ux * w, by + uy * w), (bx + ux * w + vx * h, by + uy * w + vy * h), (bx + vx * h, by + vy * h)]
    return Polygon(pts), (vx, vy)


def _ancla(e):
    p = e.get_placement()[1]
    return float(p[0]), float(p[1])


MARGEN_CABLE_MM = 0.0   # (los textos de cable se reparten con _apilar_cables)
PASO_CABLE_MM = 3.4     # separación entre líneas del texto de un mismo cable


def _margen(e):
    return MARGEN_CABLE_MM if float(e.dxf.get('rotation', 0.0)) % 180 else 0.0


def _apilar_cables(textos):
    """Reparte las líneas de texto de cada cable (rotadas, misma altura) con PASO_CABLE_MM,
    manteniendo su orden y su centro. Un mismo cable tiene sus líneas a menos de 7,5 mm entre sí."""
    grupos = {}
    for e in textos:
        rot = float(e.dxf.get('rotation', 0.0)) % 180
        if not rot: continue
        grupos.setdefault(round(rot, 1), []).append(e)
    for rot, lista in grupos.items():
        r = math.radians(rot)
        vx, vy = -math.sin(r), math.cos(r)            # perpendicular a la línea de texto
        ordenados = sorted(lista, key=lambda e: _ancla(e)[0] * vx + _ancla(e)[1] * vy)
        cable = []
        for e in ordenados:
            p = _ancla(e)[0] * vx + _ancla(e)[1] * vy
            if cable and p - (_ancla(cable[-1])[0] * vx + _ancla(cable[-1])[1] * vy) > 7.5:
                _repartir(cable, vx, vy)
                cable = []
            cable.append(e)
        if cable: _repartir(cable, vx, vy)


def _repartir(lista, vx, vy):
    if len(lista) < 2: return
    pos = [_ancla(e)[0] * vx + _ancla(e)[1] * vy for e in lista]
    centro = sum(pos) / len(pos)
    for k, e in enumerate(lista):
        destino = centro + (k - (len(lista) - 1) / 2) * PASO_CABLE_MM
        delta = destino - pos[k]
        e.translate(vx * delta, vy * delta, 0)


def _separar_textos(textos, pasadas=60):
    """Empuja en perpendicular a la línea de texto los que se solapan (paso ~1,4 altura)."""
    _apilar_cables(textos)
    for _ in range(pasadas):
        cajas = [_caja_texto(e) for e in textos]
        movido = False
        for j in range(len(textos)):
            pj, vj = cajas[j]
            mj = _margen(textos[j])
            for i in range(j):
                pi = cajas[i][0]
                mi = _margen(textos[i])
                a, b = pi.buffer(mi / 2), pj.buffer(mj / 2)
                if not a.intersects(b) or a.intersection(b).area < 1e-4:
                    continue
                cj, ci = pj.centroid, pi.centroid
                sgn = 1.0 if ((cj.x - ci.x) * vj[0] + (cj.y - ci.y) * vj[1]) >= 0 else -1.0
                paso = 1.4 * float(textos[j].dxf.height) * sgn
                textos[j].translate(vj[0] * paso, vj[1] * paso, 0)
                cajas[j] = _caja_texto(textos[j])
                pj = cajas[j][0]
                movido = True
        if not movido:
            break


def aplicar(dxf_path, catalog=None):
    doc = ezdxf.readfile(dxf_path)
    cat = _catalogo(catalog)
    diagrama, textos, rotulo, lamina = (_L.apply(doc, r, cat) for r in ROLES)
    for e in doc.modelspace():
        t = e.dxftype()
        if t not in ('LINE', 'LWPOLYLINE', 'TEXT', 'HATCH'):
            continue
        pts = _puntos(e) if t != 'HATCH' else []
        if t == 'HATCH':                       # relleno de logos
            e.dxf.layer = rotulo; continue
        if t == 'TEXT':
            x, y = pts[0]
            e.dxf.layer = rotulo if _en_rotulo(x, y) else textos
            continue
        if pts and all(_en_rotulo(x, y) for x, y in pts):
            e.dxf.layer = rotulo
        elif _en_marco(pts):
            e.dxf.layer = lamina
        elif pts and all(x >= RX for x, _ in pts):
            e.dxf.layer = textos
        else:
            e.dxf.layer = diagrama
    for nombre in ANTIGUAS:
        if nombre in doc.layers:
            try:
                doc.layers.remove(nombre)
            except Exception:
                pass
    doc.saveas(dxf_path)
    return sorted(_L.name(r, cat) for r in ROLES)
