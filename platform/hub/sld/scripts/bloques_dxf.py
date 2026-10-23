"""Símbolos SLD como bloques DXF (INSERT) tomados de iec60617-symbol-generator.

Flujo (sld_generator.py):
  1. separar(svg_final, lib): quita del SVG los símbolos que tienen bloque DXF y devuelve
     su posición absoluta (mm, coordenadas SVG = mm) y sus valores de atributos.
  2. el SVG sin esos símbolos pasa por el convertidor del plugin y capas_dxf.
  3. insertar(dxf, lib, instancias, alto_mm): importa cada bloque (una sola definición),
     y coloca un INSERT por aparición con su escala (A3 = escala del grupo) y sus atributos.
Las capas de los bloques se reasignan a las capas 291-* del SLD.
"""
import os, re
from lxml import etree
import ezdxf
from ezdxf.addons import importer

CAPA_SIMBOLO = '291-E-DIAGRAMA'
CAPA_TEXTO = '291-E-TEXTOS'
_ORIG = {'SIMBOLO': CAPA_SIMBOLO, 'ROTULO': CAPA_TEXTO, '0': CAPA_SIMBOLO}


def _comp(a, b):
    """Compone transformaciones afines simples (k, tx, ty): p -> k*p + t.  a∘b."""
    return (a[0] * b[0], a[0] * b[1] + a[1], a[0] * b[2] + a[2])


def _af(t):
    res = (1.0, 0.0, 0.0)
    for nombre, args in re.findall(r'(translate|scale)\(([^)]*)\)', t or ''):
        v = [float(x) for x in re.split(r'[\s,]+', args.strip()) if x]
        op = (1.0, v[0], v[1] if len(v) > 1 else 0.0) if nombre == 'translate' else (v[0], 0.0, 0.0)
        res = _comp(res, op)
    return res


def _absoluta(el):
    cadena = []
    n = el
    while n is not None:
        cadena.append(n.get('transform'))
        n = n.getparent()
    res = (1.0, 0.0, 0.0)
    for t in reversed(cadena):
        res = _comp(res, _af(t))
    return res


def _bloque_disponible(lib, sid):
    return bool(sid) and os.path.isfile(os.path.join(lib, sid + '.dxf'))


def separar(svg_texto, lib):
    """Devuelve (svg_sin_simbolos, instancias). Instancia: sid, X, Y (mm SVG), k, valores."""
    raiz = etree.fromstring(svg_texto.encode('utf-8'))
    instancias = []
    for g in raiz.xpath("//*[@class='sym' and @data-sid]"):
        sid = g.get('data-sid')
        if not _bloque_disponible(lib, sid):
            continue
        kx, tx, ty = _absoluta(g)
        valores = {}
        for el in g.xpath(".//*[@data-key]"):
            t = ''.join(el.itertext()).strip()
            if t:
                valores[el.get('data-key').upper()] = t
        instancias.append(dict(sid=sid, X=tx, Y=ty, k=kx, valores=valores))
        g.getparent().remove(g)
    return etree.tostring(raiz, encoding='unicode'), instancias


def insertar(dxf_path, lib, instancias, alto_mm):
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    sids = sorted({i['sid'] for i in instancias})
    nombres = []
    for sid in sids:
        src = ezdxf.readfile(os.path.join(lib, sid + '.dxf'))
        imp = importer.Importer(src, doc)
        nombres.append(sid.upper())
        if sid.upper() not in doc.blocks:
            imp.import_block(sid.upper())
        imp.finalize()
    # capas de los bloques -> capas del SLD (colores, alturas y estilos de texto: los del plugin, sin cambios)
    for nombre in nombres:
        for e in doc.blocks.get(nombre):
            e.dxf.layer = _ORIG.get(e.dxf.layer, CAPA_SIMBOLO)
    for capa in ('SIMBOLO', 'ROTULO'):
        if capa in doc.layers:
            try:
                doc.layers.remove(capa)
            except Exception:
                pass
    for i in instancias:
        k = i['k']
        ref = msp.add_blockref(i['sid'].upper(), (i['X'], alto_mm - i['Y']),
                               dxfattribs={'layer': CAPA_SIMBOLO, 'xscale': k, 'yscale': k, 'zscale': k})
        tags = [a.dxf.tag for a in doc.blocks.get(i['sid'].upper()).query('ATTDEF')]
        ref.add_auto_attribs({t: i['valores'].get(t, '') for t in tags})
        for a in ref.attribs:
            a.dxf.layer = CAPA_TEXTO
    doc.saveas(dxf_path)
    return len(instancias), len(sids)
