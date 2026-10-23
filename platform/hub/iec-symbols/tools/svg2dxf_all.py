import re, sys, os, math
import xml.etree.ElementTree as ET

SRC, DST = sys.argv[1], sys.argv[2]
STEM = os.path.splitext(os.path.basename(SRC))[0]
BLOCK = STEM  # block name == file name (without extension)
NS = '{http://www.w3.org/2000/svg}'
LAY_SYM, LAY_TXT = '0', '0'  # all entities on layer 0
TAGS = ('tag',)
TAG_COLOR = '#0000ff'  # tag and symbol fixed text: blue (true color)
ATTR_COLOR = '#000000'  # other attributes: black (ACI 7)
ALLOWED_LW = [0,5,9,13,15,18,20,25,30,35,40,50,53,60,70,80,90,100,106,120,140,158,200,211]

PARAM_LABELS = {
    'tag': 'Tag', 'poles': 'Polos', 'curve_rating': 'Curva', 'breaking_capacity': 'Capacidad',
    'rated_current': 'In', 'current': 'Corriente', 'manufacturer': 'Fabricante', 'model': 'Modelo',
    'voltage': 'Tensión', 'power': 'Potencia', 'power_kw': 'Potencia', 'power_kva': 'Potencia',
    'sensitivity': 'Sensibilidad', 'designation': 'Designación', 'scale_range': 'Escala',
    'ct_ratio': 'Relación TI', 'vt_ratio': 'Relación TV', 'ratio': 'Relación', 'series': 'Serie',
    'serial': 'Nro. serie', 'short_circuit_current': 'Icc', 'class': 'Clase', 'trip_unit': 'Unidad de disparo',
    'load': 'Carga', 'kvar': 'kVAr', 'accuracy_class': 'Clase de precisión', 'impedance': 'Impedancia',
    'protection': 'Protección', 'fuse_rating': 'Calibre fusible', 'time': 'Tiempo', 'vector': 'Grupo vectorial',
    'cable_tag': 'Tag', 'cable_spec': 'Sección del cable', 'cable_insulation': 'Aislación / norma',
    'impulse_current': 'Ipk', 'ansi_functions': 'Funciones ANSI', 'capacity': 'Capacidad',
}

import sys as _s; _s.path.insert(0, os.path.expanduser('~')); from params import LABELS as _L
PARAM_LABELS.update(_L)

def label_for(key):
    return PARAM_LABELS.get(key, key.replace('_', ' ').capitalize())

def P(*pairs):
    return ''.join('%s\n%s\n' % (c, v) for c, v in pairs)

def lwval(w):
    v = round(float(w) * 100)
    return min(ALLOWED_LW, key=lambda a: abs(a - v))

def colorpairs(c):
    if not c or c == 'none':
        return ''
    v = int(c.lstrip('#'), 16)
    if v == 0:
        return P(('62', 7))  # black -> ACI 7 (white)
    return P(('420', v))

LTYPES = {}
def ltype_name(dash):
    if not dash:
        return None
    nums = [float(x) for x in dash.replace(',', ' ').split()]
    if len(nums) % 2:
        nums = nums * 2
    name = 'SVG_' + '_'.join(('%g' % n).replace('.', 'p') for n in nums)
    LTYPES[name] = nums
    return name

def lt_pair(lt):
    return P(('6', lt)) if lt else ''

def lwcol(stroke, sw):
    return colorpairs(stroke) + P(('370', -1))  # lineweight ByLayer

def parse_path(d):
    toks = re.findall(r'[MLCQZmlcqz]|-?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?', d)
    arity = {'M': 2, 'L': 2, 'C': 6, 'Q': 4, 'Z': 0}
    subs, cur, cmd, i = [], None, None, 0
    while i < len(toks):
        t = toks[i]
        if len(t) == 1 and t.upper() in arity:
            cmd = t.upper(); i += 1
            if cmd == 'Z':
                if cur: cur['closed'] = True
                continue
        n = arity[cmd]
        if i + n > len(toks):
            break
        vals = [float(v) for v in toks[i:i + n]]
        i += n
        if cmd == 'M':
            cur = {'pts': [(vals[0], vals[1])], 'closed': False, 'curved': False}
            subs.append(cur)
            cmd = 'L'
            continue
        if cur is None:
            continue
        x0, y0 = cur['pts'][-1]
        if cmd == 'L':
            cur['pts'].append((vals[0], vals[1]))
        elif cmd == 'C':
            cur['curved'] = True
            x1, y1, x2, y2, x3, y3 = vals
            for k in range(1, 13):
                s = k / 12.0; u = 1 - s
                cur['pts'].append((u**3*x0 + 3*u*u*s*x1 + 3*u*s*s*x2 + s**3*x3,
                                   u**3*y0 + 3*u*u*s*y1 + 3*u*s*s*y2 + s**3*y3))
        elif cmd == 'Q':
            cur['curved'] = True
            x1, y1, x2, y2 = vals
            for k in range(1, 9):
                s = k / 8.0; u = 1 - s
                cur['pts'].append((u*u*x0 + 2*u*s*x1 + s*s*x2, u*u*y0 + 2*u*s*y1 + s*s*y2))
    return subs

def ent_line(x1, y1, x2, y2, stroke, sw, lt):
    return (P(('0', 'LINE'), ('8', LAY_SYM)) + lt_pair(lt) + P(('100', 'AcDbEntity')) + lwcol(stroke, sw)
            + P(('100', 'AcDbLine'), ('10', x1), ('20', -y1), ('30', 0), ('11', x2), ('21', -y2), ('31', 0)))

def ent_poly(pts, closed, stroke, sw, lt):
    body = P(('0', 'LWPOLYLINE'), ('8', LAY_SYM)) + lt_pair(lt) + P(('100', 'AcDbEntity')) + lwcol(stroke, sw)
    body += P(('100', 'AcDbPolyline'), ('90', len(pts)), ('70', 1 if closed else 0))
    return body + ''.join(P(('10', x), ('20', -y)) for x, y in pts)

def ent_circle(cx, cy, r, stroke, sw, lt):
    return (P(('0', 'CIRCLE'), ('8', LAY_SYM)) + lt_pair(lt) + P(('100', 'AcDbEntity')) + lwcol(stroke, sw)
            + P(('100', 'AcDbCircle'), ('10', cx), ('20', -cy), ('30', 0), ('40', r)))

def ent_solid(pts, fill):
    p = pts
    c = [p[0], p[1], p[2], p[2]] if len(p) == 3 else [p[0], p[1], p[3], p[2]]
    return (P(('0', 'SOLID'), ('8', LAY_SYM), ('100', 'AcDbEntity')) + colorpairs(fill)
            + P(('100', 'AcDbTrace'),
                ('10', c[0][0]), ('20', -c[0][1]), ('30', 0), ('11', c[1][0]), ('21', -c[1][1]), ('31', 0),
                ('12', c[2][0]), ('22', -c[2][1]), ('32', 0), ('13', c[3][0]), ('23', -c[3][1]), ('33', 0)))

def ent_hatch(pts, fill):
    return (P(('0', 'HATCH'), ('8', LAY_SYM), ('100', 'AcDbEntity')) + colorpairs(fill)
            + P(('100', 'AcDbHatch'), ('10', 0), ('20', 0), ('30', 0), ('210', 0), ('220', 0), ('230', 1),
                ('2', 'SOLID'), ('70', 1), ('71', 0), ('91', 1), ('92', 3), ('72', 0), ('73', 1), ('93', len(pts)))
            + ''.join(P(('10', x), ('20', -y)) for x, y in pts)
            + P(('97', 0), ('75', 0), ('76', 1), ('98', 0)))

def halign(anchor):
    return {'end': '2', 'middle': '1'}.get(anchor, '0')

def style_for(el, is_var):
    if is_var:
        return 'ARIAL'
    return 'ARIAL_BLACK' if (el.get('font-weight') or '').lower() == 'bold' else 'ARIAL'

def text_xy(el):
    """Insertion point and DXF rotation. Supports x/y or transform='translate(a b) rotate(r)', plus parent group offset."""
    ox, oy = float(el.get('_dx', 0)), float(el.get('_dy', 0))
    tr = el.get('transform')
    if tr:
        m = re.search(r'translate\(\s*([-\d.]+)[ ,]+([-\d.]+)\s*\)', tr)
        x, y = float(m.group(1)), float(m.group(2))
        r = re.search(r'rotate\(\s*([-\d.]+)', tr)
        rot = -float(r.group(1)) if r else 0.0
        return x + ox, y + oy, rot
    return float(el.get('x')) + ox, float(el.get('y')) + oy, 0.0

def ent_text(el, text):
    x, y, rot = text_xy(el)
    out = (P(('0', 'TEXT'), ('8', LAY_TXT), ('100', 'AcDbEntity')) + colorpairs(TAG_COLOR)
           + P(('100', 'AcDbText'), ('10', x), ('20', -y), ('30', 0), ('40', '1.7'),
               ('1', text), ('72', halign(el.get('text-anchor', 'start'))), ('11', x), ('21', -y), ('31', 0),
               ('50', rot), ('7', style_for(el, False))))
    return out

def ent_attdef(el, key, default):
    x, y, rot = text_xy(el)
    out = (P(('0', 'ATTDEF'), ('8', LAY_TXT), ('100', 'AcDbEntity')) + colorpairs(TAG_COLOR if key in TAGS else ATTR_COLOR)
           + P(('100', 'AcDbText'), ('10', x), ('20', -y), ('30', 0), ('40', '2.5' if key in TAGS else '1.7'),
               ('1', default), ('72', halign(el.get('text-anchor', 'start'))), ('11', x), ('21', -y), ('31', 0),
               ('50', rot), ('7', style_for(el, True)),
               ('100', 'AcDbAttributeDefinition'), ('280', 0), ('3', default), ('2', key.upper()), ('70', 0)))
    return out

root = ET.parse(SRC).getroot()
symbol = None
for g in root.iter(NS + 'g'):
    if g.get('id') == STEM:
        symbol = g; break
if symbol is None:  # file was renamed: take the main top-level symbol group (not ports / label_slots)
    for g in root:
        if g.tag == NS + 'g' and g.get('id') not in (None, 'ports', 'label_slots'):
            symbol = g; break
if symbol is None:
    raise SystemExit('no group id=%s in %s' % (STEM, SRC))

shapes, slot_texts = [], []
def group_translate(g):
    m = re.search(r'translate\(\s*([-\d.]+)[ ,]+([-\d.]+)\s*\)', g.get('transform') or '')
    return (float(m.group(1)), float(m.group(2))) if m else (0.0, 0.0)

def walk(node, dx=0.0, dy=0.0):
    for ch in node:
        t = ch.tag.replace(NS, '')
        if t == 'g':
            if ch.get('display') == 'none' or ch.get('id') in ('ports', 'label_slots'):
                continue
            gx, gy = group_translate(ch)
            walk(ch, dx + gx, dy + gy)
        elif t in ('line', 'path', 'rect', 'circle', 'text'):
            ch.set('_dx', repr(dx)); ch.set('_dy', repr(dy))
            shapes.append(ch)
walk(symbol)
for g in root.iter(NS + 'g'):
    if g.get('id') == 'label_slots':
        for ch in g:
            if ch.tag.replace(NS, '') == 'text':
                slot_texts.append(ch)

ents, attdefs = [], []
for el in shapes:
    t = el.tag.replace(NS, '')
    stroke, fill = el.get('stroke'), el.get('fill', 'none')
    sw, dash = el.get('stroke-width', '0.25'), el.get('stroke-dasharray')
    lt = ltype_name(dash) if (dash and t != 'text') else None
    if t == 'line':
        ox, oy = float(el.get('_dx', 0)), float(el.get('_dy', 0))
        ents.append(ent_line(float(el.get('x1')) + ox, float(el.get('y1')) + oy, float(el.get('x2')) + ox, float(el.get('y2')) + oy, stroke, sw, lt))
    elif t == 'rect':
        ox, oy = float(el.get('_dx', 0)), float(el.get('_dy', 0))
        x, y = float(el.get('x')) + ox, float(el.get('y')) + oy
        w, h = float(el.get('width')), float(el.get('height'))
        pts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
        if stroke and stroke != 'none': ents.append(ent_poly(pts, True, stroke, sw, lt))
        if fill != 'none': ents.append(ent_hatch(pts, fill))
    elif t == 'circle':
        ox, oy = float(el.get('_dx', 0)), float(el.get('_dy', 0))
        cx, cy, r = float(el.get('cx')) + ox, float(el.get('cy')) + oy, float(el.get('r'))
        if stroke and stroke != 'none': ents.append(ent_circle(cx, cy, r, stroke, sw, lt))
        if fill != 'none':
            pts = [(cx + r * math.cos(2 * math.pi * k / 48), cy + r * math.sin(2 * math.pi * k / 48)) for k in range(48)]
            ents.append(ent_hatch(pts, fill))
    elif t == 'path':
        for s in parse_path(el.get('d', '')):
            ox, oy = float(el.get('_dx', 0)), float(el.get('_dy', 0))
            pts, closed = [(px + ox, py + oy) for px, py in s['pts']], s['closed']
            if not closed and len(pts) > 2 and abs(pts[0][0]-pts[-1][0]) < 1e-3 and abs(pts[0][1]-pts[-1][1]) < 1e-3:
                closed = True  # closed by returning to start point (no Z)
            if stroke and stroke != 'none' and len(pts) >= 2:
                ents.append(ent_poly(pts, closed, stroke, sw, lt))
            if fill != 'none' and closed and len(pts) >= 3:
                if not s['curved'] and len(pts) in (3, 4):
                    ents.append(ent_solid(pts, fill))
                else:
                    ents.append(ent_hatch(pts, fill))
    elif t == 'text':
        txt = ''.join(el.itertext())
        m = re.search(r'\{(\w+)\}', txt)
        if el.get('data-key'):
            attdefs.append(ent_attdef(el, el.get('data-key'), label_for(el.get('data-key'))))
        elif m:
            attdefs.append(ent_attdef(el, m.group(1), label_for(m.group(1))))
        else:
            ents.append(ent_text(el, txt))
for el in slot_texts:
    key = el.get('data-key')
    if key:
        attdefs.append(ent_attdef(el, key, label_for(key)))

ltype_defs = P(('0', 'LTYPE'), ('2', 'CONTINUOUS'), ('70', 0), ('3', 'Solid line'), ('72', 65), ('73', 0), ('40', 0.0))
for name, nums in LTYPES.items():
    ltype_defs += P(('0', 'LTYPE'), ('2', name), ('70', 0), ('3', 'SVG dash'), ('72', 65), ('73', len(nums)),
                    ('40', sum(abs(n) for n in nums)))
    ltype_defs += ''.join(P(('49', n if i % 2 == 0 else -n)) for i, n in enumerate(nums))

header = P(('0', 'SECTION'), ('2', 'HEADER'), ('9', '$ACADVER'), ('1', 'AC1015'),
           ('9', '$DWGCODEPAGE'), ('3', 'ANSI_1252'), ('9', '$INSUNITS'), ('70', 4), ('9', '$MEASUREMENT'), ('70', 1), ('0', 'ENDSEC'))
tables = P(('0', 'SECTION'), ('2', 'TABLES'))
tables += P(('0', 'TABLE'), ('2', 'LTYPE'), ('70', 1 + len(LTYPES))) + ltype_defs + P(('0', 'ENDTAB'))
tables += P(('0', 'TABLE'), ('2', 'LAYER'), ('70', 1), ('0', 'LAYER'), ('2', '0'), ('70', 0), ('62', 7), ('6', 'CONTINUOUS'), ('0', 'ENDTAB'))
tables += P(('0', 'TABLE'), ('2', 'STYLE'), ('70', 3),
            ('0', 'STYLE'), ('2', 'STANDARD'), ('70', 0), ('40', 0.0), ('41', 1.0), ('50', 0.0), ('71', 0), ('42', 2.5), ('3', 'txt'),
            ('0', 'STYLE'), ('2', 'ARIAL'), ('70', 0), ('40', 0.0), ('41', 1.0), ('50', 0.0), ('71', 0), ('42', 2.5), ('3', 'arial.ttf'),
            ('0', 'STYLE'), ('2', 'ARIAL_BLACK'), ('70', 0), ('40', 0.0), ('41', 1.0), ('50', 0.0), ('71', 0), ('42', 2.5), ('3', 'ariblk.ttf'),
            ('0', 'ENDTAB'))
tables += P(('0', 'ENDSEC'))

def _rank(s):
    if '\n2\nTAG\n' in s: return 0
    if '\n2\nMANUFACTURER\n' in s: return 2
    return 1
attdefs.sort(key=_rank)  # tag first, manufacturer last
blocks = (P(('0', 'SECTION'), ('2', 'BLOCKS'), ('0', 'BLOCK'), ('8', '0'), ('2', BLOCK), ('70', 0),
            ('10', 0), ('20', 0), ('30', 0), ('3', BLOCK))
          + ''.join(ents) + ''.join(attdefs)
          + P(('0', 'ENDBLK'), ('8', '0'), ('0', 'ENDSEC')))
entities = P(('0', 'SECTION'), ('2', 'ENTITIES'), ('0', 'INSERT'), ('8', '0'), ('2', BLOCK),
             ('10', 0), ('20', 0), ('30', 0), ('0', 'ENDSEC'))

import codecs
codecs.register_error('dxfesc', lambda e: (''.join('\\U+%04X' % ord(c) for c in e.object[e.start:e.end]), e.end))
with open(DST, 'w', encoding='cp1252', errors='dxfesc', newline='\n') as f:
    f.write(header + tables + blocks + entities + P(('0', 'EOF')))
print('%s: block=%s geom=%d attdef=%d ltypes=%d' % (STEM, BLOCK, len(ents), len(attdefs), len(LTYPES)))
