#!/usr/bin/env python3
"""Generador referencial de SLD (unifilar BT) desde plantilla MINIMAL v2."""
import sys, os, math, json, textwrap, datetime, re
from xml.sax.saxutils import escape as xesc
import openpyxl
from lxml import etree
try:
    import cairosvg  # optional: only needed for PNG previews; requires the Cairo DLL on Windows
except (ImportError, OSError):
    cairosvg = None
from epc_dxf import roles as ROLES
from epc_symbols import library_dir

LIB, XLSX, OUT, NAME, LAMINA, MODBLOCK = sys.argv[1:7]
if LIB == 'default': LIB = str(library_dir('sld-lv-symbol'))       # símbolos: epc_symbols
from epc_calc.aea_pipeline import TOPOLOGIAS_MOTOR         # which topologies are motors (the choice of symbols); the numbers come from the calculation
os.makedirs(OUT, exist_ok=True)
CAT = {i['id']: i for i in json.load(open(os.path.join(LIB, '_catalog.json'), encoding='utf-8-sig'))['symbols']}
# El dibujo no calcula: todo número sale del cálculo de epc_calc (aea_pipeline y board_figures), que entrega board_design como archivos JSON.
#   SLD_CALC_JSON    = {TAG: {In, Ib, icu, S, dU, disp}} (contrato de aea_export)
#   SLD_CALC_DETAIL  = {TAG: {limite_pct, du_propia_pct, p_kw, pe_mm2, neutro_mm2, kind, ...}}
#   SLD_FIGURES_JSON = cifras del tablero: barra, acometida, verificaciones y notas (board_figures)
def _calculo(var):
    f = os.environ.get(var)
    if not f:
        sys.exit(f'FALTA {var}: el unifilar solo dibuja; el cálculo lo entrega epc_calc (board_design.design)')
    return json.load(open(f, encoding='utf-8'))
PRE, DET, FIG = _calculo('SLD_CALC_JSON'), _calculo('SLD_CALC_DETAIL'), _calculo('SLD_FIGURES_JSON')
PITCH, X0, YBAR, GAP = 68.0, 58.0, 85.0, 3.0
BLUE, RED, GREEN, BLACK = '#0000ff', '#ff0000', '#139b48', '#000000'
FONT = "Arial, Helvetica, sans-serif"
# Alturas de letra IRAM 4503 (h = altura de mayuscula Arial, 0,716 em):
H_TXT, H_TIT = 2.0, 3.0                      # mm
FS_TXT = round(H_TXT/0.716, 2)               # font-size 2,79 para h 2 mm
FS_TIT = round(H_TIT/0.716, 2)               # font-size 4,19 para h 3 mm
FS_DES = round(2.5/0.716, 2)                # designación del cable en negrita: h 2,5 mm = font 3,49
LS = 3.4                                     # interlineado (mm), ~1,7 h
SIG = {
 'lv_mccb_basic': ('MCCB', 'Interruptor automatico en caja moldeada'),
 'lv_mccb_motorized': ('MCCB M', 'Interruptor en caja moldeada motorizado'),
 'lv_mcb': ('MCB', 'Interruptor termomagnetico / guardamotor (MPCB)'),
 'lv_rcbo': ('RCBO', 'Interruptor termomagnetico diferencial'),
 'lv_rccb': ('RCCB', 'Interruptor diferencial'),
 'lv_contactor': ('KM', 'Contactor'),
 'lv_thermal_overload': ('OL', 'Rele termico de sobrecarga'),
 'lv_soft_starter': ('SS', 'Arrancador suave'),
 'lv_vfd': ('VFD', 'Variador de frecuencia'),
 'lv_motor_3ph': ('M 3~', 'Motor trifasico'),
 'lv_load_box_kw': ('LOAD', 'Carga generica (kW)'),
 'lv_ups': ('UPS', 'Sistema de alimentacion ininterrumpida'),
 'lv_cable_arrow_in': ('ACOM.', 'Cable de acometida'),
 'lv_cable_arrow_out': ('SAL.', 'Cable de salida hacia la carga'),
 'lv_busbar_node': ('BUS', 'Derivacion desde barra'),
 'lv_earth_pe': ('PE', 'Puesta a tierra / PE'),
}
# ---------- entrada ----------
wb = openpyxl.load_workbook(XLSX, data_only=True)
TB = {}
for row in wb['TABLERO'].iter_rows(values_only=True):
    if row and row[0] in ('NOMBRE','TENSION_V','SISTEMA','ICC_KA','FP_DEFAULT','FRECUENCIA_HZ','PROYECTO','LONG_ACOMETIDA_m'):
        TB[row[0]] = row[1]
TB['NOMBRE_BASE'] = TB['NOMBRE']   # nombre sin sufijo de hoja: es el que va al rótulo (el número de hoja está en Página)
if os.environ.get('SLD_TITLE_SUFFIX'): TB['NOMBRE'] = f"{TB['NOMBRE']} {os.environ['SLD_TITLE_SUFFIX']}"
V = float(TB['TENSION_V']); ICC = float(TB['ICC_KA']); FPDEF = float(TB.get('FP_DEFAULT') or 0.85)
rows = list(wb['CIRCUITOS'].iter_rows(values_only=True))
hi = next(i for i, r in enumerate(rows) if r and r[0] == 'TAG')
hdr = [str(h).strip() if h is not None else '' for h in rows[hi]]
def num(x):
    return float(x) if x not in (None, '') else None
C, ORDER = {}, []
for r in rows[hi+1:]:
    if not r or r[0] is None: continue
    tag = str(r[0]).strip()
    if tag.lower().startswith(('campo', 'fila')): continue
    d = dict(zip(hdr, r))
    C[tag] = dict(tag=tag, desc=str(d.get('DESCRIPCION') or ''), carga=num(d.get('CARGA')),
                  unit=str(d.get('UNIDAD_CARGA') or 'kW').strip(), dest=str(d.get('DESTINO') or ''),
                  parent=(str(d['PARENT_TAG']).strip() if d.get('PARENT_TAG') else None),
                  topo=str(d.get('TOPOLOGY') or 'single').strip().lower(),
                  fase=str(d.get('FASE') or '3F').strip().upper(), L=num(d.get('LONGITUD_m')) or 0.0,
                  fp=num(d.get('FP')), eff=num(d.get('RENDIMIENTO')),
                  kind=str(d.get('KIND') or 'auto').strip().lower(), notas=str(d.get('NOTAS') or ''),
                  tipo=str(d.get('CABLE_TIPO') or 'tetra_sep').strip().lower())
    ORDER.append(tag)
KIDS = {t: [u for u in ORDER if C[u]['parent'] == t] for t in ORDER}
ROOTS_ALL = [t for t in ORDER if not C[t]['parent'] or C[t]['parent'] not in C]
_sub = [x.strip() for x in os.environ.get('SLD_SUBSET', '').split(',') if x.strip()]
ROOTS = [t for t in ROOTS_ALL if (not _sub or t in _sub)]
def _desc(t): return [t] + [u for k in KIDS[t] for u in _desc(k)]
DRAWN = set(u for t in ROOTS for u in _desc(t))
_nl = max(1, len([t for t in DRAWN if not KIDS[t]]))
PITCH = min(68.0, (539.0 if _sub else 540.0) / _nl)   # hoja paginada: 40 mm reservados a la derecha de la barra para 'continua en hoja'
PREV_H = os.environ.get('SLD_PREV', ''); NEXT_H = os.environ.get('SLD_NEXT', '')

# ---------- cifras del cálculo (solo se leen) ----------
R = {}
for t in ORDER:
    pc, dt_ = PRE[t], DET[t]
    R[t] = dict(Ib=pc['Ib'], P=dt_['p_kw'], In=pc['In'], icu=pc['icu'], S=pc['S'], PE=dt_['pe_mm2'], N=dt_['neutro_mm2'], dv=dt_['du_propia_pct'], lim=dt_['limite_pct'],
                motor=dt_['topologia'] in TOPOLOGIAS_MOTOR, ph=dt_['fases'], fp=dt_['fp'], L=dt_['largo_m'], parent=bool(KIDS[t]), kind=dt_['kind'], disp=pc['disp'])
RCD = f"{FIG['rcd_ma']:g} mA"

# ---------- cadenas de símbolos ----------
def mcb(pol, In, icu): return ('lv_mcb', {'poles': pol, 'curve_rating': f'C{In}', 'breaking_capacity': f'{icu} kA'})
def chain(t):
    c = C[t]; r = R[t]; ph = r['ph']; In = r['In']; icu = r['icu']; pol3 = '3P' if ph == 3 else '1P'
    if KIDS[t]:
        return [('lv_rccb', {'poles': '4P' if ph == 3 else '2P', 'rated_current': f'{In} A', 'sensitivity': RCD})]
    el = []
    if r['motor']:
        topo = c['topo']; big = In >= 63
        if topo == 'dol':
            el = [('lv_mcb', {'poles': '3P MPCB', 'curve_rating': f'MA {In}', 'breaking_capacity': f'{icu} kA'}), ('lv_contactor', {'tag': 'KM1'})]
        elif topo == 'dol_ol':
            el = [mcb(pol3, In, icu), ('lv_contactor', {'tag': 'KM1'}), ('lv_thermal_overload', {'tag': 'OL'})]
        elif topo == 'star_delta':
            el = [('lv_mccb_basic', {'tag': t}) if big else mcb(pol3, In, icu), ('lv_contactor', {'tag': 'KM1'}),
                  ('lv_contactor', {'tag': 'KM2 Y'}), ('lv_contactor', {'tag': 'KM3 D'}), ('lv_thermal_overload', {'tag': 'OL'})]
        elif topo == 'softstarter':
            el = [('lv_mccb_basic', {'tag': t}) if big else mcb(pol3, In, icu), ('lv_soft_starter', {'tag': 'SS'})]
        elif topo == 'vfd':
            el = [mcb(pol3, In, icu), ('lv_vfd', {'rated_current': f'{In} A'})]
        elif topo == 'dol_rcd':
            el = [('lv_rcbo', {'poles': pol3, 'curve_rating': f'C{In}', 'sensitivity': RCD, 'breaking_capacity': f'{icu} kA', 'tag': t}),
                  ('lv_contactor', {'tag': 'KM1'})]
        else:
            el = [mcb(pol3, In, icu)]
    else:
        k = r['kind']                                       # lo decidió el cálculo (auto -> mcb o mccb)
        if k == 'mccb_motorized':
            el = [('lv_mccb_motorized', {'rated_current': f'{In} A', 'breaking_capacity': f'{icu} kA'})]
        elif k == 'mccb':
            el = [('lv_mccb_basic', {'tag': t})]
        elif k == 'rcbo':
            el = [('lv_rcbo', {'poles': '1P+N' if ph == 1 else '3P+N', 'curve_rating': f'C{In}', 'sensitivity': RCD, 'breaking_capacity': f'{icu} kA', 'tag': t})]
        elif k == 'rccb':
            el = [('lv_rccb', {'poles': '2P' if ph == 1 else '4P', 'rated_current': f'{In} A', 'sensitivity': RCD})]
        else:
            el = [mcb(pol3, In, icu)]
    if 'UPS' in c['desc'].upper():
        el.append(('lv_ups', {'tag': t}))
    return el
def load_of(t):
    r = R[t]
    if r['motor']:
        return ('lv_motor_3ph', {'power_kw': f"{r['P']:.1f} kW", 'current': f"{r['Ib']:.1f} A", 'tag': t})
    return ('lv_load_box_kw', {'tag': t})
def disp_of(t): return R[t]['disp']

# ---------- helpers SVG ----------
D = []; USED = set(); LEAVES = []
_cache = {}
def _sym_file(sid):
    """Symbol SVG path. iec-symbols >= 0.4.14 names files 291_E_LV_SLD_IEC60617_<id without 'lv_'>.svg;
    older libraries used <id>.svg. The catalog 'file' key is not reliable, so try both."""
    for name in (sid + '.svg', f"291_E_LV_SLD_IEC60617_{sid[3:] if sid.startswith('lv_') else sid}.svg"):
        f = os.path.join(LIB, name)
        if os.path.exists(f):
            return f
    return os.path.join(LIB, sid + '.svg')


def sym_svg(sid, slots, x, y):
    if not os.path.exists(_sym_file(sid)):
        print('AVISO: falta símbolo', sid, '-> recuadro ??', file=sys.stderr)
        return (f'<g class="sym" data-layer="sld.diagram" transform="translate({x:.2f},{y:.2f})">'
                '<rect x="-5" y="0" width="10" height="10" fill="none" stroke="#0000ff" stroke-width="0.25"/>'
                '<text x="0" y="6.4" font-size="3.47" text-anchor="middle" font-family="Arial, sans-serif" fill="#000000">??</text></g>')
    if sid not in _cache:
        tree = etree.parse(_sym_file(sid))
        el = tree.xpath(f"//*[@id='{sid}']")
        node = el[0] if el else tree.getroot()
        lbl = tree.xpath("//*[@id='label_slots']")
        extra = ''.join(etree.tostring(g, encoding='unicode') for g in lbl)
        _cache[sid] = etree.tostring(node, encoding='unicode') + extra
    frag = etree.fromstring('<g xmlns="http://www.w3.org/2000/svg">' + _cache[sid] + '</g>')
    for sl in frag.xpath(".//*[@id='label_slots']"):
        sl.attrib.pop('id', None); sl.set('fill', '#000000'); sl.set('data-layer', 'sld.text')      # los textos de un símbolo son anotación
        for t_ in sl.iter():
            t_.attrib.pop('font-weight', None)
    for p in frag.xpath(".//*[@id='ports']") + frag.xpath(".//*[local-name()='metadata']"):
        if p.getparent() is not None: p.getparent().remove(p)
    frag.attrib.pop('id', None)
    if sid == 'lv_busbar_node':                    # quita el 'BUS' fijo de cada nodo: se rotula solo en el extremo izquierdo
        for t_ in frag.xpath(".//*[local-name()='text']"):
            if ''.join(t_.itertext()).strip() == 'BUS' and t_.getparent() is not None:
                t_.getparent().remove(t_)
    for el in frag.xpath(".//*[@data-key]"):
        key = el.get('data-key'); val = slots.get(key)
        if val is not None and str(val).strip() != '':
            el.text = str(val)
            for ch in list(el): el.remove(ch)
        elif el.getparent() is not None:
            el.getparent().remove(el)
    return f'<g class="sym" data-layer="sld.diagram" data-sid="{sid}" transform="translate({x:.2f},{y:.2f})">' + etree.tostring(frag, encoding='unicode') + '</g>'
def place(sid, slots, x, y):
    USED.add(sid); D.append(sym_svg(sid, slots, x, y))
def bottom_off(sid):
    if sid not in CAT: return 10.0 if not os.path.exists(_sym_file(sid)) else 5.0
    p = [q for q in CAT[sid].get('ports', []) if q['id'] == 'bottom']
    return p[0]['y'] if p else CAT[sid]['size']['h']
ROL = 'sld.diagram'            # rol de las líneas que se dibujan ahora (la tabla y las referencias son anotación: sld.text)
def line(x1, y1, x2, y2, col=BLUE, w=0.25, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    D.append(f'<line data-layer="{ROL}" x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{col}" stroke-width="{w}"{d}/>')
_S_DIAG = (400.0 - 35.0) / 608.0 if os.environ.get('SLD_FORMATO', 'A1') == 'A3' else 1.0   # escala del diagrama y tabla en A3
_TXT_VIS = FS_TXT / _S_DIAG if _S_DIAG != 1.0 else None   # A3: texto del diagrama y tabla a 2 mm visibles (None = tamaño normal)
_SP = 1.6 if _TXT_VIS is not None else 1.0   # A3: más separación entre líneas de texto (2 mm) para que no se solapen
def T(x, y, s, size=FS_TXT, bold=False, anchor='start', col=BLACK):
    if _TXT_VIS is not None: size = _TXT_VIS
    b = ' font-weight="bold"' if bold else ''
    D.append(f'<text data-layer="sld.text" x="{x:.2f}" y="{y:.2f}" font-size="{size}" font-family="{xesc(FONT)}" text-anchor="{anchor}" fill="{col}"{b}>{xesc(str(s))}</text>')
def draw_chain(elems, xc, y):
    prev = None; yy = y
    for sid, sl in elems:
        if prev is not None: line(xc, prev, xc, yy)
        place(sid, sl, xc, yy)
        prev = yy + bottom_off(sid)
        yy = prev + GAP
    return prev
def gw(t): return PITCH if not KIDS[t] else sum(gw(k) for k in KIDS[t])
def prot_block(t, xc, y_top):
    el = chain(t); r = R[t]
    if not el: return
    sid, sl = el[0]
    lines = [(SIG.get(sid, (sid,))[0], True), (f"{r['In']} A · {r['icu']} kA", False)]
    if sl.get('poles'): lines.insert(1, (sl['poles'], False))
    for i, (txt, b) in enumerate(lines):
        T(xc + 11, y_top + 3 + i*3.6, txt, bold=b)

def layout(t, x_left, y_top, top=False):
    w = gw(t); xc = x_left + w/2
    if top: place('lv_busbar_node', {}, xc, YBAR - 0.78)   # sin etiqueta por nodo: la barra se rotula una sola vez
    # datos de protección van en los slots del propio símbolo (sin bloque duplicado)
    bottom = draw_chain(chain(t), xc, y_top)
    if KIDS[t]:
        yb = bottom + 6
        line(xc, bottom, xc, yb)
        xs = []; x = x_left
        for k in KIDS[t]:
            kw = gw(k); xk = x + kw/2; xs.append(xk)
            layout(k, x, yb + 4)
            line(xk, yb, xk, yb + 4)
            x += kw
        line(xs[0], yb, xs[-1], yb)
    else:
        LEAVES.append((t, xc, bottom))

# ---------- diagrama ----------
x_end = X0 + sum(gw(t) for t in ROOTS)
BUS_END = 638.0   # barra principal y PE: hasta el limite del recuadro gris menos 5 mm
T(638, 28, TB['NOMBRE'], size=FS_TIT, bold=True, anchor='end')   # dentro del recuadro, esquina superior derecha   # nombre del tablero: esquina superior derecha del recuadro
T(638, 28 + 3.4*_SP, f"Sistema {TB['SISTEMA']} · {V:.0f} V · {int(TB.get('FRECUENCIA_HZ') or 50)} Hz · FP {FPDEF:g} · Icc {ICC:g} kA", anchor='end')
XA = X0 + gw(ROOTS[0]) / 2          # eje de la acometida = eje del primer circuito
place('lv_cable_arrow_in', {}, XA, 30)
line(XA, 35, XA, 40, RED)
place('lv_mccb_basic', {'tag': 'Q-GRAL'}, XA, 40)
line(XA, 75, XA, YBAR)
BUS_START = 40.0 if PREV_H else XA   # hoja con barra que viene: la barra llega al borde izquierdo del recuadro + 5 mm
line(BUS_START, YBAR, BUS_END, YBAR, BLUE, 0.7)
if PREV_H: T(BUS_START, YBAR - 2, f"← VIENE DE HOJA {PREV_H}", bold=True)
if NEXT_H: T(BUS_END, YBAR + 4.6, f"CONTINÚA EN HOJA {NEXT_H} →", anchor="end", bold=True)
_bdp = FIG['bar']['in_a']
T(XA + 4, YBAR - 2, 'BUS', bold=True)                  # extremo izquierdo, una sola vez
T(BUS_END, YBAR - 6, f"BARRA PRINCIPAL {_bdp} A · {V:.0f} V · {TB['SISTEMA']}", anchor='end')  # extremo derecho, sobre la barra
T(BUS_END, YBAR - 2, f"Icc {ICC:g} kA · 3F+N", anchor='end')
# texto de la acometida, junto al cable de entrada (horizontal, sobre el Q-GRAL): el cable y su protección vienen del tablero superior
_ac = FIG['feeder']
T(XA + 6, 31.5, f"ACOMETIDA / {_ac['length_m']:g} m", size=FS_DES, bold=True)
T(XA + 6, 31.5 + 3.0*_SP, 'Seccion y proteccion: Pendiente (tablero superior)' if _ac['pending'] else f"{_ac['S_mm2']} mm² · XLPE/Cu IRAM 2178")
T(XA + 6, 31.5 + 6.0*_SP, f"Barra {V:.0f} V · In {_bdp} A · Icc {ICC:g} kA" + ('' if _ac['pending'] or _ac['du_pct'] is None else f" · ΔU {_ac['du_pct']:.2f} %"))
x = X0
for t in ROOTS:
    layout(t, x, YBAR + 4.22, top=True); x += gw(t)
def _leg_strings(t):
    r = R[t]; S = r['S']; PE = r['PE']; N = r['N']; tipo = C[t]['tipo']
    if r['ph'] == 1:
        l2 = f"2x{S} mm²" if tipo == 'tetra_inc' else f"2x{S} + PE {PE:g} mm²"
    elif tipo == 'unifilar':
        l2 = f"3x1x{S} + 1x{N} + PE {PE:g} mm²"
    elif tipo == 'tetra_inc':
        l2 = f"3x{S}/2x{PE:g} mm²"
    else:
        l2 = f"3x{S}/{N} mm² + PE {PE:g} mm²"
    return [(f"{t} / {r['L']:g} m", FS_DES, 0.66), (l2, FS_TXT, 0.58), ("XLPE/Cu  IRAM 2178", FS_TXT, 0.58)]
# longitud estimada (mm) de la leyenda mas larga: ancho medio Arial ~0,58 em (negrita ~0,66 em)
LEG_MAX = max(len(txt) * fs * k for t, _, _ in LEAVES for txt, fs, k in _leg_strings(t))
GAP_PE = 5.0
# barra PE a 3 mm de la base de los simbolos; texto de leyenda a GAP_PE mm por encima de la barra
CABLE_H = 52.07   # símbolo lv_cable_run: origen arriba, flecha a 52,07 mm, tramo de salida hasta 60,07 mm
y_out = max(max(a for _, _, a in LEAVES) + 3 + GAP_PE + 2 + 8 + LEG_MAX, max(a for _, _, a in LEAVES) + CABLE_H + 8 + 3)  # ta = y_out-8, la flecha del símbolo queda en ta
LEG_TOPS = []
for t, xc, ab in LEAVES:
    ta = y_out - 8                            # flecha de salida (lv_cable_run) a 8 mm de la carga
    r = R[t]
    l2 = _leg_strings(t)[1][0]
    O = ta - CABLE_H                          # origen del símbolo lv_cable_run (extremo superior del tramo)
    assert O >= ab - 1e-6, f'cable {t}: tramo superior demasiado corto ({O - ab:.1f} mm)'
    line(xc, ab, xc, O, RED)
    place('lv_cable_run', {'cable_tag': f"{t} / {r['L']:g} m", 'cable_spec': l2, 'cable_insulation': 'XLPE/Cu IRAM 2178'}, xc, O)
    LEG_TOPS.append(ta - 2 - max(len(f"{t} / {r['L']:g} m"), len(l2), len('XLPE/Cu IRAM 2178')) * 2.3)
    lsid, lsl = load_of(t)
    place(lsid, lsl, xc, y_out)
y_pe = max(ab for _, _, ab in LEAVES) + 3; x_pe0 = 46   # debajo de todos los simbolos de ramas, encima de leyendas
print('PE y', round(y_pe,1), 'leyendas desde', round(min(LEG_TOPS),1), file=sys.stderr)                     # barra PE encima de las leyendas de cable (como en la referencia)
x_cab1 = min(xc for _, xc, _ in LEAVES)                       # primer cable de salida
line(x_pe0, y_pe, BUS_END, y_pe, GREEN, 0.25, '10 1 2 1')
place('lv_earth_pe', {'tag': 'PE'}, x_pe0, y_pe)
T(x_cab1 - 5, y_pe - 1.5, 'BARRA PE', anchor='end', col=GREEN)   # 5 mm antes de la linea roja
# recuadro gris de linea entrecortada fina: engloba el tablero; las cargas quedan fuera (en campo)
BOX_X0, BOX_Y0, BOX_X1 = 35.0, 20.0, 643.0   # 5 mm desde los limites internos de la hoja
BOX_Y1 = y_out - 2.0
D.append(f'<rect data-layer="sld.diagram" x="{BOX_X0:.2f}" y="{BOX_Y0:.2f}" width="{BOX_X1-BOX_X0:.2f}" height="{BOX_Y1-BOX_Y0:.2f}" fill="none" stroke="#808080" stroke-width="0.25" stroke-dasharray="4 2"/>')
TREE = []
def walk(t):
    TREE.append(t)
    for k in KIDS[t]: walk(k)
for t in ROOTS: walk(t)

_k_tab = len(D)   # A3: marca de inicio de la tabla
ROL = 'sld.text'   # desde aquí, tabla de circuitos y columna de referencias: anotación
# ---------- tabla de circuitos (bajo el diagrama) ----------
cols = [('TAG',16),('DESCRIPCIÓN',120),('P [kW]',18),('FASE',14),('Ib [A]',18),('In [A]',18),('Icu [kA]',18),
        ('DISPOSITIVO',150),('CABLE F/N [mm²]',30),('PE [mm²]',18),('L [m]',16),('ΔU [%]',20)]
TW = 610.0; tot = sum(w for _, w in cols); cw = [w*TW/tot for _, w in cols]
TX = 30.0; HH = 8.0; RH = 6.0
TY = 575.0 - HH - len(TREE)*RH
line(TX, TY, TX + TW, TY, BLACK, 0.25)
xx = TX
for (h, _), w in zip(cols, cw):
    T(xx + 1, TY + 5.4, h, bold=True); xx += w
line(TX, TY + HH, TX + TW, TY + HH, BLACK, 0.25)
ry = TY + HH
for t in TREE:
    c = C[t]; r = R[t]
    vals = [t, c['desc'][:55], f"{r['P']:.2f}", c['fase'], f"{r['Ib']:.1f}", f"{r['In']}", f"{r['icu']}",
            disp_of(t)[:85], ('—' if r['parent'] else f"{r['S']}"), f"{r['PE']:g}",
            ('—' if r['parent'] else f"{r['L']:g}"), ('—' if r['parent'] else f"{r['dv']:.2f}")]
    xx = TX
    for v, w in zip(vals, cw):
        T(xx + 1, ry + 4.2, v); xx += w
    ry += RH
    line(TX, ry, TX + TW, ry, BLACK, 0.25)
xx = TX
for w in cw:
    line(xx, TY, xx, ry, BLACK, 0.25); xx += w
line(TX + TW, TY, TX + TW, ry, BLACK, 0.25)
SIN_TABLA = os.environ.get('SLD_SIN_TABLA', '') == '1'   # la tabla de cálculo sale en su propia lámina
if SIN_TABLA: del D[_k_tab:]   # la tabla no va en las hojas del diagrama
_k_ref = len(D)   # A3: marca de inicio de la columna de referencias
# ---------- columna derecha (referencias, cálculos, verificación) ----------
notes = FIG['note']

COMPACTO = os.environ.get('SLD_FORMATO', 'A1') == 'A3'   # A3: referencias en 3 columnas a 2 mm, junto al rótulo
if COMPACTO:
    _yfin_tab = 20.0 + (BOX_Y1 - 20.0) * _S_DIAG + (18.0 if SIN_TABLA else 18.0 + (HH + len(TREE) * RH) * _S_DIAG)
    RX, XC, XV = 30.0, 122.0, 178.0
    Y0 = _yfin_tab + 3.0
    TIT, LSR, WRAP, WRAPC, LSC = FS_TXT, 3.6, 30, 36, 3.0
else:
    line(648, 15, 648, 500, BLACK, 0.25)
    RX = XC = XV = 655.0
    Y0 = 22.0
    TIT, LSR, WRAP, WRAPC, LSC = FS_TIT, 5.5, 80, 80, LS
_TXT_VIS = None   # de aquí en adelante, el texto usa su tamaño (referencias en A3 ya van a 2 mm)
y = Y0
T(RX, y, 'REFERENCIAS', size=TIT, bold=True); y += 6
for sid in sorted(USED):
    if sid not in SIG: continue
    sg, ds = SIG[sid]
    T(RX, y, sg, bold=True); T(RX + 18, y, ds); y += LSR
line(RX, y, RX + 14, y, BLACK, 0.7); T(RX + 18, y + 1, 'Barra de potencia BDP (trazo 0,7)'); y += LSR
line(RX, y, RX + 14, y, GREEN, 0.25, '10 1 2 1'); T(RX + 18, y + 1, 'Barra PE / proteccion (verde)')
y_refs_fin = y + LSR

y = Y0
T(XC, y, 'CALCULOS (referencial)', size=TIT, bold=True); y += 6
calc_lines = FIG['lines']
for ln in calc_lines:
    for w_ in textwrap.wrap(ln, WRAPC if COMPACTO else 80):
        T(XC, y, w_); y += LSC

y = Y0
T(XV, y, 'VERIFICACION', size=TIT, bold=True); y += 6
leaves = [t for t in ORDER if not KIDS[t] and t in DRAWN]
dvmax = max((R[t]['dv'] for t in ORDER if not KIDS[t]), default=0.0)
checks = [(c['text'], c['ok']) for c in FIG['checks']]
dif_pending = FIG['differential_missing']
for txt, ok in checks:
    st = 'PENDIENTE' if ok is None else 'OK' if ok else 'REVISAR'
    wr = textwrap.wrap(txt, WRAP)
    for i, w_ in enumerate(wr):
        T(XV, y, w_ + (f'  [{st}]' if i == len(wr) - 1 else '')); y += LSC
    y += 0.5
if dif_pending:
    for w_ in textwrap.wrap('Sin diferencial: ' + ', '.join(dif_pending), WRAP):
        T(XV, y, w_, col='#b00000'); y += LSC
y += 1.5
if COMPACTO:
    for ln in textwrap.wrap('Calculo referencial; no reemplaza la memoria de calculo.', WRAP):
        T(XV, y, ln); y += LSC
else:   # A1: notas al pie de la columna derecha, como antes
    ny = max(y + 4, 500 - LS*len(textwrap.wrap(notes, 115)) - 2)
    T(XV, ny - 3, 'NOTAS', size=TIT, bold=True)
    for i, ln in enumerate(textwrap.wrap(notes, 115)):
        T(XV, ny + i*LS, ln)
    y = ny
_alto_ref = max(y, y_refs_fin, Y0 + 8 * LS + 10) - Y0   # altura real del bloque de referencias (A3)

# ---------- hoja solo de tabla (SLD_SOLO_TABLA=1): la tabla de circuitos sale en su propia lámina ----------
SOLO_TABLA = os.environ.get('SLD_SOLO_TABLA', '') == '1'
if SOLO_TABLA:
    D = D[_k_tab:_k_ref]
# ---------- rótulo + modificaciones + export ----------
FORMATO = os.environ.get('SLD_FORMATO', 'A1')   # A1 (por defecto) o A3 (prueba: diagrama reducido a la zona útil A3)
ESCALA_A3 = (0.46, 0.36)   # escala máxima del diagrama y tabla en A3 (la referencia se ajusta al espacio libre)
today = datetime.date.today().strftime('%d/%m/%Y')
if LAMINA == 'default':   # rótulo: se pide al servicio de epc_titleblock (los datos del proyecto vienen en EPC_TITLEBLOCK_JSON); sin Excel ni subprocesos
    from epc_titleblock import service as TBS
    _pedido = json.load(open(os.environ['EPC_TITLEBLOCK_JSON'], encoding='utf-8')) if os.environ.get('EPC_TITLEBLOCK_JSON') else {}
    _nombres = os.environ.get('SLD_NAMES', NAME).split(',')
    _campos = {'denominacion': TB.get('NOMBRE_BASE'), 'denominacion_2': 'TABLA DE CÁLCULO DE CIRCUITOS' if NAME.endswith('_TABLA') else 'DIAGRAMA UNIFILAR BT',
               'proyecto': TB.get('PROYECTO'), 'pagina': f'{_nombres.index(NAME) + 1} / {len(_nombres)}'}
    _res = TBS.render({**_pedido, 'sheets': [{'name': NAME, 'format': FORMATO, 'fields': _campos}]})
    for _w in _res['warnings']: print('AVISO', _w, file=sys.stderr)
    lam, mod = _res['sheets'][0]['svg'], _res['sheets'][0]['modifications_block']
else:
    lam, mod = open(LAMINA, encoding='utf-8').read(), open(MODBLOCK, encoding='utf-8').read()
lam = ROLES.tag_iram_sheet(lam)   # marco y rótulo de la plantilla IRAM, con su rol de capa
vals = {'cliente': 'No indicado', 'denominacion': TB['NOMBRE'], 'denominacion_2': 'DIAGRAMA UNIFILAR BT',
        'empresa': '—', 'plano_n': str(TB.get('PROYECTO') or ''), 'plano_propio': NAME,
        'escala': 'S/E', 'emision': today, 'reemplaza': '—', 'notas': 'Referencial: ver columnas de calculo'}
# campos del rótulo que el SLD no calcula (empresa, cliente, códigos...): en blanco, no quedan {clave} visibles
_pend = set(re.findall(r'\{([a-z_0-9]+)\}', lam)) | set(re.findall(r'\{([a-z_0-9]+)\}', mod))
_vacios = sorted(k for k in _pend if k not in vals)
for k in _vacios: vals[k] = ''
if _vacios: print('AVISO rótulo sin datos del proyecto (quedan en blanco):', ', '.join(_vacios), file=sys.stderr)
for k, v in vals.items():
    lam = lam.replace('{' + k + '}', xesc(v))
inner = mod[mod.find('>', mod.find('<svg')) + 1: mod.rfind('</svg>')]
for k, v in vals.items():
    inner = inner.replace('{' + k + '}', xesc(v))
MOD_LISTA = False   # lista de modificaciones (fig. 3): activar sólo cuando la hoja tenga revisiones cargadas
if MOD_LISTA and 'id="modificaciones_IRAM4508"' not in lam:   # el SVG del plugin ya trae la lista si la fila lo indica
    D.append(f'<g transform="translate(652,507.5)">{inner}</g>')
if SOLO_TABLA:
    # hoja de tabla: la tabla ocupa el ancho de la zona útil, arriba a la izquierda (5 mm de margen)
    _st = min(1.0, (400.0 - 30.0) / 610.0) if FORMATO == 'A3' else 1.0
    body = f'<g transform="translate({30.0 - 30.0*_st:.2f},{20.0 - TY*_st:.2f}) scale({_st:.4f})">' + '\n'.join(D) + '</g>'
elif FORMATO == 'A3':
    # A3 (prueba): el recuadro del diagrama ocupa todo el ancho de la zona útil con 5 mm a izquierda, derecha y arriba
    _s = (400.0 - 35.0) / (BOX_X1 - BOX_X0)                         # recuadro 35..643 (608 mm A1) -> 35..400 mm A3
    _yd = 20.0 + (BOX_Y1 - 20.0) * _s                                # fin del recuadro en A3
    _yt = _yd + 18.0                                                 # tabla de circuitos bajo el diagrama (debajo de las etiquetas de carga)
    _yt_fin = _yt + (HH + len(TREE) * RH) * _s
    _sr = 1.0   # referencias en coordenadas de la hoja (ya van a 2 mm y en columnas)
    _grupos = [
        (D[:_k_tab], _s, 35.0 - 35.0*_s, 20.0 - 20.0*_s),
        (D[_k_tab:_k_ref], _s, 35.0 - 30.0*_s, _yt - TY*_s),
        (D[_k_ref:], _sr, 0.0, 0.0),
    ]
    print(f'A3: escala diagrama {_s:.3f}, referencias {_sr:.3f}', file=sys.stderr)
    body = '\n'.join(f'<g transform="translate({tx:.2f},{ty:.2f}) scale({k:.4f})">' + '\n'.join(parte) + '</g>'
                     for parte, k, tx, ty in _grupos)
else:
    body = '\n'.join(D)
_m = re.search(r'<g id="dibujo">.*?</g>', lam, re.S)
if _m and '<!-- insertar' in _m.group(0):
    final = lam[:_m.start()] + '<g id="dibujo">' + body + '</g>' + lam[_m.end():]
else:
    print('AVISO: no se encontró la casilla dibujo en la lámina; el diagrama va en un grupo aparte', file=sys.stderr)
    idx = lam.rfind('</svg>')
    final = lam[:idx] + '<g id="diagrama_SLD">' + body + '</g>\n' + lam[idx:]
left = re.findall(r'>\{[a-z_0-9]+\}<', final)
if left: print('AVISO placeholders sin reemplazar:', left[:5])
etree.fromstring(final.encode('utf-8'))
svg_path = os.path.join(OUT, NAME + '.svg')
open(svg_path, 'w', encoding='utf-8').write(final)
# El SVG en desarrollo pasa a entregable por el servicio de epc_dxf (capas del catálogo, símbolos como bloques, color y grosor del trazo).
from epc_dxf import deliverable as DL
for ln in DL.convert(svg_path, symbol_library=LIB)['messages']:
    print(ln, file=sys.stderr)
summ = {t: dict(In=R[t]['In'], Ib=round(R[t]['Ib'], 1), icu=R[t]['icu'], S=R[t]['S'], dU=round(R[t]['dv'], 2), disp=disp_of(t)) for t in TREE}
json.dump(summ, open(os.path.join(OUT, NAME + '_calculo.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('OK', NAME, 'circuitos', len(TREE), 'y_out', round(y_out, 1), 'fin tabla', round(ry, 1), 'dU max', round(dvmax, 2))
