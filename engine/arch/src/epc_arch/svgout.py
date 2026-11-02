"""The recognized plan as an SVG with layers: the original linework faint underneath and, over it, one group per kind of element (`ARQ-MUROS`, `ARQ-PUERTAS`, `ARQ-VENTANAS`, `ARQ-HUECOS`),
each element with its id and confidence. The SVG is the frame of the plan space (see `model`): one unit of the SVG is one unit of the coordinates in the result.

Drawn by the conventions of architectural drawing (Sierra Mejía, *Dibujo técnico arquitectónico: estándares básicos*): the weight of a line says what it is. Cut walls are the heaviest (solid
poché, corners closed); windows are drawn shut, with their frame along both faces of the wall in a medium line and the glass in the finest; doors are drawn open, the leaf square to its closed
position in a fine line and the swing as a dashed projection line; plain openings are dashed. Rooms are softly tinted with their area, and under the plan its title, scale and a graphic scale."""
import math
from typing import List, Tuple
from xml.sax.saxutils import escape

from epc_arch.geometry import arc_point, arc_span, axis_of, segment_distance
from epc_arch.model import Architecture, Opening, Primitives, Wall

ROOM_TINTS = ("#f4f0e8", "#edf1ec", "#ecf0f4", "#f3edee", "#f1efe4")              # soft floor tints, one per room in turn
LAYERS = (("ARQ-MUROS", "arq.wall"), ("ARQ-PUERTAS", "arq.door"), ("ARQ-VENTANAS", "arq.window"), ("ARQ-HUECOS", "arq.opening"))
INK, PAPER, GLASS, DOOR, HOLE, SWEEP = "#1f2933", "#ffffff", "#3b82c4", "#6b7280", "#9aa5b1", "#f1efe9"
Pt = Tuple[float, float]
FONT = "Helvetica, Arial, sans-serif"


def pens(T: float) -> dict:
    """Line weights for a plan whose walls are T thick, from the table of weights at 1:100 (walls 0.4-0.5 mm, windows 0.15, doors and furniture 0.10, glass 0.05) with a wall of about 0.15 m:
    each weight in plan units is a share of T."""
    return {"cut": T * 0.04, "window": T * 0.10, "door": T * 0.07, "glass": T * 0.035, "aux": T * 0.05}


def _f(v: float) -> str:
    return f"{v:.2f}".rstrip("0").rstrip(".")


def _pts(points: List[Pt]) -> str:
    return " ".join(f"{_f(x)},{_f(y)}" for x, y in points)


def _unit(w: Wall) -> Pt:
    dx, dy = w.b[0] - w.a[0], w.b[1] - w.a[1]
    n = math.hypot(dx, dy) or 1.0
    return dx / n, dy / n


def _joined(w: Wall, others: List[Wall], reach: float) -> Tuple[bool, bool]:
    """Whether each end of a wall meets another wall that is not in line with it: that end is a corner or a T and is drawn out to the far face so the corner closes with no notch."""
    ux, uy = _unit(w)
    ends = []
    for p in (w.a, w.b):
        hit = False
        for o in others:
            if o is w:
                continue
            ox, oy = _unit(o)
            if abs(ux * oy - uy * ox) < 0.5:                       # nearly parallel: a continuation or a neighbour, not a corner
                continue
            if segment_distance(p, p, o.a, o.b) <= reach:
                hit = True
                break
        ends.append(hit)
    return ends[0], ends[1]


def _quad(w: Wall, ext_a: float = 0.0, ext_b: float = 0.0) -> str:
    ux, uy = _unit(w)
    ox, oy = -uy * w.thickness / 2, ux * w.thickness / 2
    a = (w.a[0] - ux * ext_a, w.a[1] - uy * ext_a)
    b = (w.b[0] + ux * ext_b, w.b[1] + uy * ext_b)
    return _pts([(a[0] + ox, a[1] + oy), (b[0] + ox, b[1] + oy), (b[0] - ox, b[1] - oy), (a[0] - ox, a[1] - oy)])


def _wall(w: Wall, others: List[Wall]) -> str:
    ja, jb = _joined(w, others, 0.75 * w.thickness)
    pts = _quad(w, w.thickness / 2 if ja else 0.0, w.thickness / 2 if jb else 0.0)
    return f'<polygon id="{w.id}" data-confidence="{w.confidence:.2f}" data-thickness="{_f(w.thickness)}" points="{pts}" fill="{INK}" stroke="{INK}" stroke-width="{_f(w.thickness * 0.04)}" stroke-linejoin="miter"/>'


def _cut(o: Opening, T: float) -> str:
    """A rectangle of paper across the wall where something opens it, so a door or a window leaves a clean gap even when the wall was drawn through it."""
    ux, uy = axis_of(o.angle).ux, axis_of(o.angle).uy
    nx, ny = -uy, ux
    hw, ht = o.width / 2, T * 0.62
    pts = [(o.at[0] - ux * hw + nx * ht, o.at[1] - uy * hw + ny * ht), (o.at[0] + ux * hw + nx * ht, o.at[1] + uy * hw + ny * ht),
           (o.at[0] + ux * hw - nx * ht, o.at[1] + uy * hw - ny * ht), (o.at[0] - ux * hw - nx * ht, o.at[1] - uy * hw - ny * ht)]
    return f'<polygon points="{_pts(pts)}" fill="{PAPER}"/>'


def _door(o: Opening, T: float) -> str:
    """Drawn open: the leaf square to the wall from its hinge, and the dashed arc it sweeps from its closed position."""
    pen = pens(T)
    out = f'<g id="{o.id}" data-confidence="{o.confidence:.2f}" data-width="{_f(o.width)}">'
    ax = axis_of(o.angle)
    if o.hinge and o.swing:
        hx, hy = o.hinge
        r = math.hypot(o.swing[0] - hx, o.swing[1] - hy) or o.width
        sign = 1.0 if (o.at[0] - hx) * ax.ux + (o.at[1] - hy) * ax.uy >= 0 else -1.0
        closed = (hx + ax.ux * sign * r, hy + ax.uy * sign * r)                       # where the leaf lies when the door is shut: along the wall
        cross = (closed[0] - hx) * (o.swing[1] - hy) - (closed[1] - hy) * (o.swing[0] - hx)
        sweep = 1 if cross > 0 else 0
        dash = f"{_f(T * 0.35)} {_f(T * 0.22)}"
        out += f'<path d="M{_f(closed[0])} {_f(closed[1])} A{_f(r)} {_f(r)} 0 0 {sweep} {_f(o.swing[0])} {_f(o.swing[1])}" fill="none" stroke="{INK}" stroke-width="{_f(pen["door"])}" stroke-dasharray="{dash}"/>'
        tk = min(T * 0.35, r * 0.05)                                                   # the leaf: a thin board, square to the wall
        sx, sy = ax.ux * sign * tk, ax.uy * sign * tk
        leaf = [(hx, hy), (o.swing[0], o.swing[1]), (o.swing[0] + sx, o.swing[1] + sy), (hx + sx, hy + sy)]
        out += f'<polygon points="{_pts(leaf)}" fill="{PAPER}" stroke="{INK}" stroke-width="{_f(pen["door"])}"/>'
    for s_ in (-1, 1):                                                                # the two jambs: the frame of the opening
        c = (o.at[0] + ax.ux * s_ * o.width / 2, o.at[1] + ax.uy * s_ * o.width / 2)
        out += f'<line x1="{_f(c[0] + ax.nx * T / 2)}" y1="{_f(c[1] + ax.ny * T / 2)}" x2="{_f(c[0] - ax.nx * T / 2)}" y2="{_f(c[1] - ax.ny * T / 2)}" stroke="{INK}" stroke-width="{_f(pen["window"])}"/>'
    return out + "</g>"


def _window(o: Opening, T: float) -> str:
    """Drawn shut: the frame on both faces of the wall and at its ends in a medium line, the glass between in the finest."""
    pen = pens(T)
    ax = axis_of(o.angle)
    hw = o.width / 2
    corner = lambda t, n: (o.at[0] + ax.ux * t + ax.nx * n, o.at[1] + ax.uy * t + ax.ny * n)          # noqa: E731
    frame = [corner(-hw, T / 2), corner(hw, T / 2), corner(hw, -T / 2), corner(-hw, -T / 2)]
    out = f'<g id="{o.id}" data-confidence="{o.confidence:.2f}" data-width="{_f(o.width)}"><polygon points="{_pts(frame)}" fill="{PAPER}" stroke="{INK}" stroke-width="{_f(pen["window"])}"/>'
    for n, w_ in ((T * 0.12, pen["glass"]), (-T * 0.12, pen["glass"])):
        a, b = corner(-hw, n), corner(hw, n)
        out += f'<line x1="{_f(a[0])}" y1="{_f(a[1])}" x2="{_f(b[0])}" y2="{_f(b[1])}" stroke="{GLASS}" stroke-width="{_f(w_)}"/>'
    return out + "</g>"


def _hole(o: Opening, T: float) -> str:
    ax = axis_of(o.angle)
    hw = o.width / 2
    a, b = (o.at[0] - ax.ux * hw, o.at[1] - ax.uy * hw), (o.at[0] + ax.ux * hw, o.at[1] + ax.uy * hw)
    out = f'<g id="{o.id}" data-confidence="{o.confidence:.2f}" data-width="{_f(o.width)}">'
    pen = pens(T)
    for n in (T / 2, -T / 2):                                                         # the lintel above, seen from below: dashed projection lines along both faces
        out += f'<line x1="{_f(a[0] + ax.nx * n)}" y1="{_f(a[1] + ax.ny * n)}" x2="{_f(b[0] + ax.nx * n)}" y2="{_f(b[1] + ax.ny * n)}" stroke="{INK}" stroke-width="{_f(pen["aux"])}" stroke-dasharray="{_f(T * 0.35)} {_f(T * 0.22)}"/>'
    for p in (a, b):
        out += f'<line x1="{_f(p[0] + ax.nx * T / 2)}" y1="{_f(p[1] + ax.ny * T / 2)}" x2="{_f(p[0] - ax.nx * T / 2)}" y2="{_f(p[1] - ax.ny * T / 2)}" stroke="{INK}" stroke-width="{_f(pen["window"])}"/>'
    return out + "</g>"


def _background(prims: Primitives, limit: int) -> List[str]:
    out = [f'<line x1="{_f(l.a[0])}" y1="{_f(l.a[1])}" x2="{_f(l.b[0])}" y2="{_f(l.b[1])}" stroke-width="{_f(max(l.width, 0.5))}"/>' for l in prims.lines[:limit]]
    for a in prims.arcs[:limit]:
        p, q = arc_point(a.c, a.r, a.start), arc_point(a.c, a.r, a.end)
        large = 1 if arc_span(a.start, a.end) > 180 else 0
        out.append(f'<path d="M{_f(p[0])} {_f(p[1])} A{_f(a.r)} {_f(a.r)} 0 {large} 1 {_f(q[0])} {_f(q[1])}"/>')
    return out


def _clean_walls(arch: Architecture) -> List[Wall]:
    """The walls as they are drawn: a stub shorter than three thicknesses that meets no wall is a stroke of furniture or lettering, and a thickness within a fifth of the plan's is the plan's."""
    T = arch.wall_thickness or 1.0
    out = []
    for w in arch.walls:
        length = math.hypot(w.b[0] - w.a[0], w.b[1] - w.a[1])
        if length < 3 * T and _joined(w, arch.walls, 0.75 * w.thickness) == (False, False):
            continue
        out.append(Wall(w.id, w.a, w.b, T if abs(w.thickness - T) <= 0.2 * T else w.thickness, w.confidence, w.reason))
    return out


def _caption(arch: Architecture, walls: List[Wall]) -> str:
    c = arch.counts()
    unit = "" if not arch.units_per_metre else f" ({arch.wall_thickness / arch.units_per_metre * 100:.0f} cm)" if arch.wall_thickness else ""
    rooms = f" · {len(arch.rooms)} ambientes" if arch.rooms else ""
    total = sum(r.area_m2 for r in arch.rooms if r.area_m2)
    area = f" · {total:.1f} m² útiles".replace(".", ",") if total else ""
    return f"{len(walls)} muros{unit} · {c['doors']} puertas · {c['windows']} ventanas{rooms}{area}"


def _layer_items(arch: Architecture) -> List[List[str]]:
    """The elements of each layer, in the order of LAYERS."""
    T = arch.wall_thickness or 1.0
    walls = _clean_walls(arch)
    of = lambda kind: [o for o in arch.openings if o.kind == kind]                      # noqa: E731
    return [[_wall(w, walls) for w in walls], [_door(o, T) for o in of("door")], [_window(o, T) for o in of("window")], [_hole(o, T) for o in of("opening")]]


def _rooms(arch: Architecture, T: float) -> List[str]:
    """Each room as its floor, softly tinted, with its area (or its number when the units are unknown) written in its middle."""
    out = []
    for i, r in enumerate(arch.rooms):
        d = "".join(f"M{_f(a)} {_f(b)}H{_f(c)}V{_f(e)}H{_f(a)}Z" for a, b, c, e in r.rects)
        out.append(f'<path id="{r.id}" d="{d}" fill="{ROOM_TINTS[i % len(ROOM_TINTS)]}" data-area="{_f(r.area)}"' + (f' data-area-m2="{r.area_m2:.2f}"' if r.area_m2 else "") + "/>")
        text = f"{r.area_m2:.1f} m²".replace(".", ",") if r.area_m2 else f"A{i + 1}"
        fs = T * 1.4                                                                  # names of spaces: one size for all (2-2.5 mm at 1:100)
        out.append(f'<text x="{_f(r.at[0])}" y="{_f(r.at[1] + fs * 0.35)}" text-anchor="middle" font-family="{FONT}" font-size="{_f(fs)}" fill="{HOLE}">{text}</text>')
    return out


def _extent(arch: Architecture, walls: List[Wall]) -> Tuple[float, float, float, float]:
    """The box the building takes, door swings included: the drawing is framed on it, not on the sheet it came from."""
    xs, ys = [], []
    for w in walls:
        xs += [w.a[0], w.b[0]]
        ys += [w.a[1], w.b[1]]
    for o in arch.openings:
        for p in (o.at, o.hinge, o.swing):
            if p:
                xs.append(p[0])
                ys.append(p[1])
    for r in arch.rooms:
        for a, b, c, e in r.rects:
            xs += [a, c]
            ys += [b, e]
    if not xs:
        return 0.0, 0.0, arch.size[0], arch.size[1]
    return min(xs), min(ys), max(xs), max(ys)


def render(arch: Architecture, prims: Primitives, background: bool = True, limit: int = 60000) -> str:
    """The SVG text of the recognized plan, framed on the building with a margin and a footer (counts and, when the units are known, a scale bar). Coordinates stay those of the plan space."""
    T = arch.wall_thickness or 1.0
    walls = _clean_walls(arch)
    x0, y0, x1, y1 = _extent(arch, walls)
    side = max(x1 - x0, y1 - y0, 1.0)
    margin = max(4 * T, 0.05 * side)
    foot = 0.11 * side
    vx, vy, vw, vh = x0 - margin, y0 - margin, (x1 - x0) + 2 * margin, (y1 - y0) + 2 * margin + foot
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{_f(vw)}" height="{_f(vh)}" viewBox="{_f(vx)} {_f(vy)} {_f(vw)} {_f(vh)}" data-source="{escape(arch.source)}">',
           f'<rect x="{_f(vx)}" y="{_f(vy)}" width="{_f(vw)}" height="{_f(vh)}" fill="{PAPER}"/>']
    if background:
        out += ['<g id="ARQ-FONDO" data-layer="arq.background" fill="none" stroke="#9aa3b5" stroke-opacity="0.18">', *_background(prims, limit), "</g>"]
    walls_svg, doors, windows, holes = _layer_items(arch)
    if arch.rooms:
        out += ['<g id="ARQ-AMBIENTES" data-layer="arq.room" shape-rendering="crispEdges">', *_rooms(arch, T), "</g>"]
    out += [f'<g id="{LAYERS[0][0]}" data-layer="{LAYERS[0][1]}">', *walls_svg, "</g>"]
    out += ['<g id="ARQ-CORTES" data-layer="arq.cut">', *[_cut(o, T) for o in arch.openings], "</g>"]
    for (gid, role), items in zip(LAYERS[1:], (doors, windows, holes)):
        out += [f'<g id="{gid}" data-layer="{role}">', *items, "</g>"]
    fs = side * 0.022
    ty = y1 + margin + foot * 0.55
    out.append(f'<line x1="{_f(x0)}" y1="{_f(y1 + margin * 0.6)}" x2="{_f(x1)}" y2="{_f(y1 + margin * 0.6)}" stroke="{HOLE}" stroke-width="{_f(side * 0.0012)}"/>')
    title = "PLANTA ARQUITECTÓNICA"
    scale = f"Escala 1:{arch.drawing_scale}" if arch.drawing_scale else ("Escala gráfica" if arch.units_per_metre else "Sin escala")
    out.append(f'<g id="ARQ-ROTULO" data-layer="arq.title"><text x="{_f(x0)}" y="{_f(ty)}" font-family="{FONT}" font-size="{_f(fs * 1.25)}" font-weight="700" letter-spacing="{_f(fs * 0.08)}" fill="{INK}">{title}</text>'
               f'<text x="{_f(x0)}" y="{_f(ty + fs * 1.3)}" font-family="{FONT}" font-size="{_f(fs * 0.8)}" fill="{HOLE}">{scale}</text></g>')
    out.append(f'<text id="ARQ-LEYENDA" x="{_f(x1)}" y="{_f(ty + fs * 1.3)}" text-anchor="end" font-family="{FONT}" font-size="{_f(fs * 0.75)}" fill="{HOLE}">{escape(_caption(arch, walls))}</text>')
    if arch.units_per_metre:
        metres = min((1, 2, 5, 10, 20), key=lambda m: abs(m * arch.units_per_metre - side / 5))
        length = metres * arch.units_per_metre
        bx, by, bh = x1 - length, ty - fs * 0.9, fs * 0.3
        out.append(f'<g id="ARQ-ESCALA" data-layer="arq.scale"><rect x="{_f(bx)}" y="{_f(by)}" width="{_f(length / 2)}" height="{_f(bh)}" fill="{INK}"/>'
                   f'<rect x="{_f(bx + length / 2)}" y="{_f(by)}" width="{_f(length / 2)}" height="{_f(bh)}" fill="{PAPER}" stroke="{INK}" stroke-width="{_f(fs * 0.05)}"/>'
                   f'<text x="{_f(bx)}" y="{_f(by - fs * 0.25)}" font-family="{FONT}" font-size="{_f(fs * 0.6)}" fill="{INK}">0</text>'
                   f'<text x="{_f(x1)}" y="{_f(by - fs * 0.25)}" text-anchor="end" font-family="{FONT}" font-size="{_f(fs * 0.6)}" fill="{INK}">{metres} m</text></g>')
    return chr(10).join(out + ["</svg>", ""])
