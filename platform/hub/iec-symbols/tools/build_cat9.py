import openpyxl, os, io, re, zipfile, shutil
import cairosvg
from PIL import Image as PILImage
from openpyxl.drawing.image import Image as XLImage
from openpyxl.drawing.spreadsheet_drawing import OneCellAnchor, AnchorMarker
from openpyxl.drawing.xdr import XDRPositiveSize2D
from openpyxl.utils.units import pixels_to_EMU
from openpyxl.styles import Font, Alignment
import sys
SRC = 'pkg8/src'
MODE = sys.argv[1]  # 'root' (zip) or 'project' (src folder)
OUT = sys.argv[2]
COLS = [('sld-lv-symbol', 'SLD LV', 2), ('mld-lv-symbol', 'MLD LV', 3), ('sld-mv-symbol', 'SLD MV', 4), ('mld-mv-symbol', 'MLD MV', 5)]
PREFIX = re.compile(r'^291_E_(?:LV|MV)_(?:SLD|MLD)_IEC60617_(.*)$')
def display(stem):
    core = PREFIX.match(stem).group(1)
    pole = ''
    m = re.search(r'_(\dp)$', core)
    if m: pole = ' ' + m.group(1).upper(); core = core[:m.start()]
    return core.replace('_', ' ').upper() + pole
rows = {}
for folder, col, ci in COLS:
    d = os.path.join(SRC, folder)
    if not os.path.isdir(d): continue
    for f in sorted(os.listdir(d)):
        if not f.endswith('.svg') or f.startswith('_library'): continue
        stem = f[:-4]
        rows.setdefault(display(stem), {})[ci] = (folder, stem)
wb = openpyxl.Workbook(); ws = wb.active; ws.title = 'Simbolos'
hdr = ['Simbolo', 'SLD LV', 'MLD LV', 'SLD MV', 'MLD MV']
ws.append(hdr)
for c in ws[1]: c.font = Font(bold=True)
ws.column_dimensions['A'].width = 26
links = []  # (row, col, folder, stem, index)
r = 2
for name in sorted(rows):
    ws.cell(r, 1, name).alignment = Alignment(vertical='center')
    for ci, (folder, stem) in rows[name].items():
        ws.cell(r, ci, stem + '.svg').alignment = Alignment(vertical='top', wrap_text=True)
        links.append((r, ci, folder, stem))
    r += 1
imgs = []
K = 4.0  # px per mm, identical for every symbol
def vbsize(path):
    t = open(path, encoding='utf-8').read()
    m = re.search(r'viewBox="([-\d.]+)[ ,]+([-\d.]+)[ ,]+([\d.]+)[ ,]+([\d.]+)"', t)
    return float(m.group(3)), float(m.group(4))
colw = {}; rowh = {}
sizes = {}
for (r, ci, folder, stem) in links:
    p = '%s/%s/%s.svg' % (SRC, folder, stem)
    vw, vh = vbsize(p)
    k = K
    if '_cell_' in stem: k = min(K, 380.0 / vh)   # MV cabinets (290 mm tall) would not fit a row at 4 px/mm
    w, h = max(1, int(vw * k)), max(1, int(vh * k)); sizes[(r, ci)] = (w, h)
    colw[ci] = max(colw.get(ci, 0), w); rowh[r] = max(rowh.get(r, 0), h)
for ci, w in colw.items(): ws.column_dimensions[openpyxl.utils.get_column_letter(ci)].width = (w + 20) / 7.0
for r_, h in rowh.items(): ws.row_dimensions[r_].height = (h + 28) * 0.75
for (r, ci, folder, stem) in links:
    w, h = sizes[(r, ci)]
    p = '%s/%s/%s.svg' % (SRC, folder, stem)
    im = PILImage.open(io.BytesIO(cairosvg.svg2png(url=p, output_width=w * 2))).convert('RGBA')
    bg = PILImage.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im)
    buf = io.BytesIO(); bg.convert('RGB').save(buf, 'PNG'); buf.seek(0)
    xi = XLImage(buf); xi.width, xi.height = w, h
    xi.anchor = OneCellAnchor(_from=AnchorMarker(col=ci - 1, colOff=57150, row=r - 1, rowOff=190500),
                              ext=XDRPositiveSize2D(pixels_to_EMU(w), pixels_to_EMU(h)))
    ws.add_image(xi); imgs.append((folder, stem))
    prefix = '' if MODE == 'project' else 'src/'
    ws.cell(r, ci).hyperlink = prefix + folder + '/' + stem + '.dxf'
tmp = OUT + '.tmp.xlsx'
wb.save(tmp)
# image hyperlinks to SVG: patch drawing xml and rels
prefix = '' if MODE == 'project' else 'src/'
zin = zipfile.ZipFile(tmp)
print(zin.read('xl/drawings/drawing1.xml')[:400])
drawing = 'xl/drawings/drawing1.xml'; rels = 'xl/drawings/_rels/drawing1.xml.rels'
dx = zin.read(drawing).decode('utf-8'); rx = zin.read(rels).decode('utf-8')
pics = list(re.finditer(r'<(?:xdr:)?cNvPr\b[^>]*?/>', dx))
assert len(pics) == len(imgs), (len(pics), len(imgs))
newrels = ''
out = []; last = 0
for i, m in enumerate(pics):
    folder, stem = imgs[i]
    rid = 'rIdSvg%d' % i
    newrels += '<Relationship Id="%s" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" Target="%s%s/%s.svg" TargetMode="External"/>' % (rid, prefix, folder, stem)
    tn = re.match(r'<([\w:]+)', m.group(0)).group(1)
    tag = m.group(0)[:-2] + '><a:hlinkClick xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" r:id="%s"/></%s>' % (rid, tn)
    out.append(dx[last:m.start()]); out.append(tag); last = m.end()
out.append(dx[last:])
dx2 = ''.join(out)
rx2 = rx.replace('</Relationships>', newrels + '</Relationships>')
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename == drawing: data = dx2.encode('utf-8')
        elif item.filename == rels: data = rx2.encode('utf-8')
        zout.writestr(item, data)
zin.close(); os.remove(tmp)
print('rows', len(rows), 'cells', len(links), 'images', len(imgs), 'out', OUT)
