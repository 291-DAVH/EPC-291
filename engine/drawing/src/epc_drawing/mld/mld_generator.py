"""Generador de multifilar (MLD) de un tablero en láminas IRAM.

Parte del mismo dato que el unifilar y del cálculo de epc_calc (que ya aplica los criterios de diseño): cada línea del unifilar se "despliega" en
sus conductores (L1 L2 L3 N) a paso uniforme de 10 mm, con los símbolos MLD_LV de la biblioteca (`<id>_<n>p_mld`) sin escalar.

  from epc_drawing.mld import mld_generator
  mld_generator.generate(data, calc, out_dir, "MLD_TGBT-01")

`data` = {"board": {...}, "circuits": [...], "titleblock": {...}} (el JSON del formulario); `calc` = {"datos": {TAG: {In, Ib, icu, S, dU, disp}},
"detalle": {...}} (resultado de epc_calc.aea_pipeline). Devuelve la lista de hojas generadas (SVG y DXF).
Rótulo y láminas: epc_drawing.sld.deps (mismo mecanismo que el unifilar; SLD_ROTULO_DIR apunta al Excel del rótulo).
"""
import datetime
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional
from xml.sax.saxutils import escape as xesc

from lxml import etree

from epc_drawing.sld import deps as VL

PITCH = 10.0                      # paso entre polos (mm), retícula de la biblioteca
COL_GAP = 16.0                    # separación entre columnas de circuitos
BLUE, RED, GREEN, BLACK = "#0000ff", "#ff0000", "#139b48", "#000000"
FONT = "Arial, Helvetica, sans-serif"
FS_TXT = round(2.0 / 0.716, 2)
FS_TIT = round(3.0 / 0.716, 2)
FS_DES = round(2.5 / 0.716, 2)
BAR_STEP = 5.0                    # separación entre barras L1 L2 L3 N
X0, XMAX = 62.0, 640.0            # zona útil de la lámina A1 para el diagrama
Y_BUS = 62.0
MOTOR_TOPO = {"dol", "dol_ol", "star_delta", "softstarter", "vfd", "dol_rcd"}
POLE_NAMES = {1: ["L"], 2: ["L", "N"], 3: ["L1", "L2", "L3"], 4: ["L1", "L2", "L3", "N"]}


def library_dir() -> str:
    from epc_drawing.symbols import library_dir as lib
    return str(lib("mld-lv-symbol"))


class Sheet:
    """Elementos SVG de una hoja y utilidades de dibujo."""

    def __init__(self, lib: str):
        self.lib = lib
        self.cat = {s["id"]: s for s in json.load(open(os.path.join(lib, "_catalog.json"), encoding="utf-8-sig"))["symbols"]}
        self.d: List[str] = []
        self.used: set = set()
        self._cache: Dict[str, str] = {}

    # ---- primitivas
    def line(self, x1, y1, x2, y2, col=BLUE, w=0.25, dash=None):
        dash = f' stroke-dasharray="{dash}"' if dash else ""
        self.d.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{col}" stroke-width="{w}"{dash}/>')

    def dot(self, x, y, col=BLUE):
        self.d.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="0.9" fill="{col}" stroke="{col}" stroke-width="0.18"/>')

    def text(self, x, y, s, size=FS_TXT, bold=False, anchor="start", col=BLACK, rot=None):
        b = ' font-weight="bold"' if bold else ""
        r = f' transform="rotate({rot} {x:.2f} {y:.2f})"' if rot is not None else ""
        self.d.append(f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" font-family="{xesc(FONT)}" text-anchor="{anchor}" fill="{col}"{b}{r}>{xesc(str(s))}</text>')

    def rect(self, x, y, w, h, col=BLUE, w_=0.25, dash=None, fill="none"):
        dash = f' stroke-dasharray="{dash}"' if dash else ""
        self.d.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{fill}" stroke="{col}" stroke-width="{w_}"{dash}/>')

    # ---- símbolos
    def symbol_file(self, sid: str) -> Optional[str]:
        s = self.cat.get(sid)
        f = os.path.join(self.lib, s["file"]) if s else None
        return f if f and os.path.isfile(f) else None

    def bottom(self, sid: str) -> float:
        s = self.cat.get(sid)
        if not s:
            return 10.0
        ys = [p["y"] for p in s["ports"] if p["id"].startswith(("bottom", "bot_"))]
        return max(ys) if ys else s["size"]["h"]

    def place(self, sid: str, slots: dict, x: float, y: float):
        f = self.symbol_file(sid)
        self.used.add(sid)
        if not f:
            print("AVISO: falta símbolo", sid, "-> recuadro ??", file=sys.stderr)
            self.rect(x - 5, y, 30, 12)
            self.text(x + 8, y + 7, "??", anchor="middle")
            return
        if sid not in self._cache:
            tree = etree.parse(f)
            el = tree.xpath(f"//*[@id='{sid}']")
            node = el[0] if el else tree.getroot()
            lbl = tree.xpath("//*[@id='label_slots']")
            self._cache[sid] = etree.tostring(node, encoding="unicode") + "".join(etree.tostring(g, encoding="unicode") for g in lbl)
        frag = etree.fromstring('<g xmlns="http://www.w3.org/2000/svg">' + self._cache[sid] + "</g>")
        for sl in frag.xpath(".//*[@id='label_slots']"):
            sl.attrib.pop("id", None)
            sl.set("fill", BLACK)
            for t_ in sl.iter():
                t_.attrib.pop("font-weight", None)
        for p in frag.xpath(".//*[@id='ports']") + frag.xpath(".//*[local-name()='metadata']"):
            if p.getparent() is not None:
                p.getparent().remove(p)
        frag.attrib.pop("id", None)
        for el in frag.xpath(".//*[@data-key]"):
            val = slots.get(el.get("data-key"))
            if val is not None and str(val).strip():
                el.text = str(val)
                for ch in list(el):
                    el.remove(ch)
            elif el.getparent() is not None:
                el.getparent().remove(el)
        self.d.append(f'<g class="sym" data-sid="{sid}" transform="translate({x:.2f},{y:.2f})">' + etree.tostring(frag, encoding="unicode") + "</g>")


def pole_id(base: str, n: int, cat: dict) -> Optional[str]:
    """Id MLD de `base` (lv_mcb, lv_contactor...) con n polos, o el más cercano disponible (>= n)."""
    for k in [n] + [m for m in (1, 2, 3, 4) if m > n]:
        sid = f"{base}_{k}p_mld"
        if sid in cat:
            return sid
    fixed = f"{base}_3p_mld"                      # variador, arrancador, motor, UPS: solo 3P
    return fixed if fixed in cat else None


def nxt(x, series):
    return next((v for v in series if v >= x - 1e-9), series[-1])


def poles_of(c: dict, has_kids: bool) -> int:
    ph = str(c.get("phase") or "3F").upper()
    if has_kids:
        return 4 if ph.startswith("3") else 2
    if ph == "3F+N":
        return 4
    return 2 if ph.startswith("1") else 3


def device_chain(c: dict, in_a: float, icu: float, n: int, has_kids: bool, tag: str) -> List[tuple]:
    """Cadena vertical de símbolos MLD del circuito: [(base_id, slots, n_polos)] (misma lógica que el unifilar)."""
    topo = str(c.get("topology") or "single").lower()
    kind = str(c.get("kind") or "auto").lower()
    big = in_a >= 63
    mcb = ("lv_mcb", {"curve_rating": f"C{in_a:g}", "breaking_capacity": f"{icu:g} kA"}, n)
    if has_kids:
        return [("lv_rccb", {"rated_current": f"{in_a:g} A", "sensitivity": "30 mA"}, n)]
    el: List[tuple] = []
    if topo in MOTOR_TOPO:
        km = ("lv_contactor", {"tag": "KM1"}, 3)
        ol = ("lv_thermal_overload", {"tag": "OL"}, 3)
        head = ("lv_mccb_basic", {"tag": tag}, 3) if big else ("lv_mcb", {"curve_rating": f"C{in_a:g}", "breaking_capacity": f"{icu:g} kA"}, 3)
        if topo == "dol":
            el = [("lv_mcb", {"curve_rating": f"MA {in_a:g}", "breaking_capacity": f"{icu:g} kA"}, 3), km]
        elif topo == "dol_ol":
            el = [head, km, ol]
        elif topo == "star_delta":
            el = [head, km, ("lv_contactor", {"tag": "KM2 Y"}, 3), ("lv_contactor", {"tag": "KM3 D"}, 3), ol]
        elif topo == "softstarter":
            el = [head, ("lv_soft_starter", {"tag": "SS"}, 3)]
        elif topo == "vfd":
            el = [head, ("lv_vfd", {"tag": "VFD", "rated_current": f"{in_a:g} A"}, 3)]
        else:                                           # dol_rcd
            el = [("lv_rcbo", {"curve_rating": f"C{in_a:g}", "sensitivity": "30 mA", "breaking_capacity": f"{icu:g} kA", "tag": tag}, 4), km]
    else:
        if kind == "mccb_motorized":
            el = [("lv_mccb_motorized", {"rated_current": f"{in_a:g} A", "breaking_capacity": f"{icu:g} kA"}, n)]
        elif kind == "mccb" or (kind == "auto" and in_a > 63):
            el = [("lv_mccb_basic", {"tag": tag}, n)]
        elif kind == "rcbo":
            el = [("lv_rcbo", {"curve_rating": f"C{in_a:g}", "sensitivity": "30 mA", "breaking_capacity": f"{icu:g} kA", "tag": tag}, 2 if n == 2 else 4)]
        elif kind == "rccb":
            el = [("lv_rccb", {"rated_current": f"{in_a:g} A", "sensitivity": "30 mA"}, 2 if n == 2 else 4)]
        else:
            el = [mcb]
    if "UPS" in str(c.get("description") or "").upper():
        el.append(("lv_ups", {"tag": tag}, 3))
    return el


class Generator:
    def __init__(self, data: dict, calc: dict, lib: Optional[str] = None):
        self.data = data
        self.board = data["board"]
        self.calc = calc["datos"]
        self.detail = calc.get("detalle", {})
        self.lib = lib or library_dir()
        self.circuits = {c["tag"]: c for c in data["circuits"]}
        self.order = [c["tag"] for c in data["circuits"]]
        self.kids = {t: [u for u in self.order if (self.circuits[u].get("parent_tag") or "") == t] for t in self.order}
        self.roots = [t for t in self.order if not (self.circuits[t].get("parent_tag") or "") or self.circuits[t]["parent_tag"] not in self.circuits]

    # ---- anchos
    def width(self, t: str) -> float:
        own = max(poles_of(self.circuits[t], bool(self.kids[t])) * PITCH, 3 * PITCH) + COL_GAP
        return max(own, sum(self.width(k) for k in self.kids[t])) if self.kids[t] else own

    def leaves(self, t: str) -> int:
        return 1 if not self.kids[t] else sum(self.leaves(k) for k in self.kids[t])

    # ---- hoja
    def paginate(self, maxw: float = XMAX - X0) -> List[List[str]]:
        sheets: List[List[str]] = [[]]
        used = 0.0
        for t in self.roots:
            w = self.width(t)
            if sheets[-1] and used + w > maxw:
                sheets.append([])
                used = 0.0
            sheets[-1].append(t)
            used += w
        return sheets

    def draw_sheet(self, roots: List[str], idx: int, total: int) -> tuple:
        sh = Sheet(self.lib)
        self.sh = sh
        self.phase_n = 0
        self.leaf_bottoms: List[tuple] = []
        bus_x1 = X0 + sum(self.width(t) for t in roots) - COL_GAP / 2 + 6
        bus = {n: Y_BUS + i * BAR_STEP for i, n in enumerate(["L1", "L2", "L3", "N"])}
        for n, y in bus.items():
            sh.line(X0 - 14, y, bus_x1, y, BLUE, 0.5)
            sh.text(X0 - 16, y + 1, n, anchor="end")
        V = float(self.board.get("voltage_v") or 380)
        sh.text(X0 - 16, Y_BUS - 8, f"BARRAS {V:g} V · {self.board.get('system', 'TN-S')} · Icc {float(self.board.get('icc_ka') or 0):g} kA", bold=True)
        if idx > 1:
            sh.text(X0 - 14, Y_BUS - 3, f"← VIENE DE HOJA {idx - 1}", bold=True)
        if idx < total:
            sh.text(bus_x1, Y_BUS - 3, f"CONTINÚA EN HOJA {idx + 1} →", anchor="end", bold=True)
        y_top = Y_BUS + 3 * BAR_STEP + 14
        x = X0
        for t in roots:
            self.layout(t, x, y_top, bus)
            x += self.width(t)
        # barra PE y cajas de carga
        leg = max(len(self.cable_text(t, n)) for t, _, _, n in self.leaf_bottoms) * FS_TXT * 0.58          # largo de la leyenda de cable más larga
        y_pe = max(b for _, _, b, _ in self.leaf_bottoms) + 8 + leg
        sh.line(X0 - 14, y_pe, bus_x1, y_pe, GREEN, 0.25, "10 1 2 1")
        sh.text(X0 - 16, y_pe + 1, "PE", anchor="end", col=GREEN)
        y_out = y_pe + 14
        for t, x0, b, n in self.leaf_bottoms:
            self.leaf_tail(t, x0, b, n, y_pe, y_out)
        return sh, y_out + 40

    def next_phase(self) -> str:
        p = ["L1", "L2", "L3"][self.phase_n % 3]
        self.phase_n += 1
        return p

    def conductors(self, n: int) -> List[str]:
        if n == 4:
            return ["L1", "L2", "L3", "N"]
        if n == 3:
            return ["L1", "L2", "L3"]
        return [self.next_phase(), "N"] if n == 2 else [self.next_phase()]

    def layout(self, t: str, x_left: float, y_top: float, bus: Dict[str, float]):
        """Dibuja el circuito t (y sus hijos) en la columna que empieza en x_left, colgando de las barras `bus` (nombre -> y)."""
        sh, c = self.sh, self.circuits[t]
        r = self.calc[t]
        has_kids = bool(self.kids[t])
        n = poles_of(c, has_kids)
        w = self.width(t)
        x0 = x_left + (w - COL_GAP - (n - 1) * PITCH) / 2                       # eje del primer polo
        names = self.conductors(n)
        top_y = y_top
        for i, name in enumerate(names):                                        # bajada de cada conductor desde su barra
            xi = x0 + i * PITCH
            sh.line(xi, bus[name], xi, top_y)
            sh.dot(xi, bus[name])
        chain = device_chain(c, r["In"], r["icu"], n, has_kids, t)
        y = top_y
        prev_n = n
        for k, (base, slots, pn) in enumerate(chain):
            sid = pole_id(base, pn, sh.cat)
            if k > 0:
                for i in range(min(prev_n, pn if sid else prev_n)):
                    sh.line(x0 + i * PITCH, y - 4.0, x0 + i * PITCH, y)
            if sid:
                sh.place(sid, slots, x0, y)
                y += sh.bottom(sid) + 4.0
            prev_n = pn
        bottom = y - 4.0
        if has_kids:                                                            # sub-barras del grupo y sus hijos
            sub = {nm: bottom + 8 + i * BAR_STEP for i, nm in enumerate(names)}
            kx0 = x_left
            xs = []
            for kid in self.kids[t]:
                xs.append((kid, kx0))
                kx0 += self.width(kid)
            span0 = min(x0, xs[0][1] + 6)
            span1 = max(x0 + (n - 1) * PITCH, kx0 - COL_GAP / 2)
            for i, name in enumerate(names):
                xi = x0 + i * PITCH
                sh.line(xi, bottom, xi, sub[name])
                sh.dot(xi, sub[name])
                sh.line(span0, sub[name], span1, sub[name], BLUE, 0.5)
                sh.text(span0 - 2, sub[name] + 1, name, anchor="end", size=FS_TXT * 0.8)
            for kid, kx in xs:
                self.layout(kid, kx, bottom + 8 + len(names) * BAR_STEP + 10, sub)
            return
        self.leaf_bottoms.append((t, x0, bottom, n))
        self.leaf_names = getattr(self, "leaf_names", {})
        self.leaf_names[t] = names

    def leaf_tail(self, t: str, x0: float, bottom: float, n: int, y_pe: float, y_out: float):
        """Cable de salida (rojo) por conductor, leyenda, carga y conexión a PE."""
        sh, c, r = self.sh, self.circuits[t], self.calc[t]
        cable_y = y_out - 12
        for i in range(n):
            xi = x0 + i * PITCH
            sh.line(xi, bottom, xi, cable_y, RED)
            sh.line(xi - 1.2, cable_y - 2.4, xi, cable_y, RED)
            sh.line(xi + 1.2, cable_y - 2.4, xi, cable_y, RED)
            sh.line(xi, cable_y, xi, y_out, RED)
        yl = y_pe - 3                                                          # leyenda a la izquierda del primer conductor, justo sobre la barra PE, leída de abajo hacia arriba
        sh.text(x0 - 2.2, yl, f"{t} / {float(c.get('length_m') or 0):g} m", size=FS_DES, bold=True, rot=-90)
        sh.text(x0 - 7.6, yl, self.cable_text(t, n), rot=-90)
        # PE
        xpe = x0 + n * PITCH
        sh.line(xpe, y_pe, xpe, y_out + 6, GREEN, 0.25, "10 1 2 1")
        # carga
        topo = str(c.get("topology") or "single").lower()
        motor_sid = pole_id("lv_motor_3ph", 3, sh.cat)
        if topo in MOTOR_TOPO and motor_sid and n == 3:
            sh.place(motor_sid, {"tag": t, "rated_current": f"{r['Ib']:.1f} A", "power": f"{self.load_kw(c, r):.1f} kW"}, x0, y_out)
            tail = y_out + sh.bottom(motor_sid)
        else:
            sh.rect(x0 - 5, y_out, (n - 1) * PITCH + 10, 14, BLUE, 0.25)
            sh.text(x0 + (n - 1) * PITCH / 2, y_out + 6, t, anchor="middle", bold=True)
            sh.text(x0 + (n - 1) * PITCH / 2, y_out + 10.5, f"{self.load_kw(c, r):.1f} kW · {r['Ib']:.1f} A", anchor="middle")
            tail = y_out + 14
        sh.text(x0 - 5, y_out + 34, str(c.get("destination") or c.get("description") or ""), size=FS_TXT)

    def cable_text(self, t: str, n: int) -> str:
        S = self.calc[t]["S"]
        pe = max(2.5, S if S <= 16 else (16 if S <= 35 else S / 2))
        return f"{n}x{S:g} + PE {pe:g} mm²  XLPE/Cu IRAM 2178"

    @staticmethod
    def load_kw(c: dict, r: dict) -> float:
        """kW aproximados desde Ib (referencial): para la leyenda de la carga."""
        import math
        ph = str(c.get("phase") or "3F").upper()
        fp = float(c.get("fp") or 0.85)
        return (math.sqrt(3) if ph.startswith("3") else 1.0) * 0.38 * r["Ib"] * fp * (1.0 if ph.startswith("3") else 0.58)

    # ---- lámina
    def build(self, out_dir: Path, name: str, maxw: float = XMAX - X0) -> List[dict]:
        out_dir.mkdir(parents=True, exist_ok=True)
        sheets = self.paginate(maxw)
        names = [name if len(sheets) == 1 else f"{name}_H{i}" for i in range(1, len(sheets) + 1)]
        tb = self.data.get("titleblock", {})
        VL.sincronizar(names, {"Denominación (línea 1)": self.board.get("name"), "Denominación (línea 2)": "DIAGRAMA MULTIFILAR BT",
                               "Proyecto": self.board.get("project")})
        made = []
        for i, (roots, nm) in enumerate(zip(sheets, names), 1):
            sh, _ = self.draw_sheet(roots, i, len(sheets))
            title = f"{self.board.get('name', '')} (multifilar)" + (f" · hoja {i} de {len(sheets)}" if len(sheets) > 1 else "")
            sh.text(X0 - 16, 38, title, size=FS_TIT, bold=True)
            sh.text(X0 - 16, 44, "Referencial: conductores desplegados del unifilar; cálculo de epc_calc con los criterios de diseño del proyecto.", size=FS_TXT)
            svg, dxf = self.write_sheet(sh, i - 1, nm, out_dir)
            made.append({"name": nm, "svg": svg, "dxf": dxf})
        return made

    def write_sheet(self, sh: Sheet, index: int, name: str, out_dir: Path) -> tuple:
        lam_path, mod_path = VL.rotulo(index, fmt="A1")
        lam = Path(lam_path).read_text(encoding="utf-8")
        today = datetime.date.today().strftime("%d/%m/%Y")
        vals = {"cliente": "No indicado", "denominacion": self.board.get("name", ""), "denominacion_2": "DIAGRAMA MULTIFILAR BT", "empresa": "—",
                "plano_n": str(self.board.get("project") or ""), "plano_propio": name, "escala": "S/E", "emision": today, "reemplaza": "—",
                "notas": "Referencial: ver cálculo"}
        pend = set(re.findall(r"\{([a-z_0-9]+)\}", lam))
        for k in pend:
            vals.setdefault(k, "")
        for k, v in vals.items():
            lam = lam.replace("{" + k + "}", xesc(v))
        body = "\n".join(sh.d)
        m = re.search(r'<g id="dibujo">.*?</g>', lam, re.S)
        if m and "<!-- insertar" in m.group(0):
            final = lam[:m.start()] + '<g id="dibujo">' + body + "</g>" + lam[m.end():]
        else:
            idx = lam.rfind("</svg>")
            final = lam[:idx] + '<g id="diagrama_MLD">' + body + "</g>\n" + lam[idx:]
        etree.fromstring(final.encode("utf-8"))
        svg_path = out_dir / f"{name}.svg"
        svg_path.write_text(final, encoding="utf-8", newline="\n")
        dxf_path = self.to_dxf(svg_path, final, out_dir, name)
        return str(svg_path), str(dxf_path) if dxf_path else None

    @staticmethod
    def to_dxf(svg_path: Path, final: str, out_dir: Path, name: str):
        """DXF por el mismo convertidor del paquete (trazos) y las capas 291-* del unifilar."""
        from epc_drawing.sld import capas_dxf
        tmp_svg = out_dir / f"{name}_trazos.svg"
        tmp_svg.write_text(final, encoding="utf-8", newline="\n")
        try:
            VL.svg_a_dxf(str(tmp_svg))
            tmp_dxf = out_dir / f"{name}_trazos.dxf"
            capas_dxf.aplicar(str(tmp_dxf))
            capas_dxf.colorear(str(tmp_svg), str(tmp_dxf))
            os.replace(tmp_dxf, out_dir / f"{name}.dxf")
            tmp_svg.unlink(missing_ok=True)
            return out_dir / f"{name}.dxf"
        except PermissionError:
            print(f"AVISO no se pudo escribir {name}.dxf: está abierto en otro programa", file=sys.stderr)
            return None


def generate(data: dict, calc: dict, out_dir, name: str, lib: Optional[str] = None, maxw: float = XMAX - X0) -> List[dict]:
    g = Generator(data, calc, lib)
    made = g.build(Path(out_dir), name, maxw)
    for m in made:
        print("OK", m["name"], "circuitos", len(g.order), file=sys.stderr)
    return made


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Multi-line diagram (MLD) of a board from the form data and its calculation")
    ap.add_argument("--input", required=True, help="board.json (board, circuits, titleblock)")
    ap.add_argument("--calc", required=True, help="<base>_dimensionado.json (contract of aea_export)")
    ap.add_argument("--detail", help="<base>_dimensionado_detalle.json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", required=True)
    a = ap.parse_args(argv)
    data = json.loads(Path(a.input).read_text(encoding="utf-8"))
    calc = {"datos": json.loads(Path(a.calc).read_text(encoding="utf-8")),
            "detalle": json.loads(Path(a.detail).read_text(encoding="utf-8")) if a.detail else {}}
    made = generate(data, calc, a.out, a.name)
    print("OK", ", ".join(m["name"] for m in made))
    return 0


if __name__ == "__main__":
    sys.exit(main())
