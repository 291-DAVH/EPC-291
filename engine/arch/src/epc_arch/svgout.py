"""The recognized plan as an SVG with layers: the original linework faint underneath and, over it, one group per kind of element (`ARQ-MUROS`, `ARQ-PUERTAS`, `ARQ-VENTANAS`, `ARQ-HUECOS`),
each element with its id and confidence. The SVG is the frame of the plan space (see `model`): one unit of the SVG is one unit of the coordinates in the result."""
import math
from typing import List
from xml.sax.saxutils import escape

from epc_arch.geometry import arc_point, arc_span, axis_of
from epc_arch.model import Architecture, Opening, Primitives, Wall

LAYERS = (("ARQ-MUROS", "arq.wall"), ("ARQ-PUERTAS", "arq.door"), ("ARQ-VENTANAS", "arq.window"), ("ARQ-HUECOS", "arq.opening"))


def _f(v: float) -> str:
    return f"{v:.2f}".rstrip("0").rstrip(".")


def _quad(w: Wall) -> str:
    dx, dy = w.b[0] - w.a[0], w.b[1] - w.a[1]
    n = math.hypot(dx, dy) or 1.0
    ox, oy = -dy / n * w.thickness / 2, dx / n * w.thickness / 2
    pts = [(w.a[0] + ox, w.a[1] + oy), (w.b[0] + ox, w.b[1] + oy), (w.b[0] - ox, w.b[1] - oy), (w.a[0] - ox, w.a[1] - oy)]
    return " ".join(f"{_f(x)},{_f(y)}" for x, y in pts)


def _wall(w: Wall) -> str:
    return f'<polygon id="{w.id}" data-confidence="{w.confidence:.2f}" data-thickness="{_f(w.thickness)}" points="{_quad(w)}" fill="#6b7280" fill-opacity="0.55" stroke="#374151" stroke-width="1"/>'


def _door(o: Opening) -> str:
    out = f'<g id="{o.id}" data-confidence="{o.confidence:.2f}" data-width="{_f(o.width)}">'
    if o.hinge and o.swing:
        r = math.hypot(o.swing[0] - o.hinge[0], o.swing[1] - o.hinge[1])
        out += f'<line x1="{_f(o.hinge[0])}" y1="{_f(o.hinge[1])}" x2="{_f(o.swing[0])}" y2="{_f(o.swing[1])}" stroke="#b45309" stroke-width="1.5"/>'
        out += f'<circle cx="{_f(o.hinge[0])}" cy="{_f(o.hinge[1])}" r="{_f(max(2.0, r / 12))}" fill="#b45309"/>'
    return out + f'<circle cx="{_f(o.at[0])}" cy="{_f(o.at[1])}" r="{_f(o.width / 2)}" fill="none" stroke="#b45309" stroke-width="1.5" stroke-dasharray="6 4"/></g>'


def _span_line(o: Opening, color: str) -> str:
    ax = axis_of(o.angle)
    a = (o.at[0] - ax.ux * o.width / 2, o.at[1] - ax.uy * o.width / 2)
    b = (o.at[0] + ax.ux * o.width / 2, o.at[1] + ax.uy * o.width / 2)
    return (f'<line id="{o.id}" data-confidence="{o.confidence:.2f}" data-width="{_f(o.width)}" x1="{_f(a[0])}" y1="{_f(a[1])}" x2="{_f(b[0])}" y2="{_f(b[1])}" '
            f'stroke="{color}" stroke-width="3" stroke-linecap="butt"/>')


def _background(prims: Primitives, limit: int) -> List[str]:
    out = [f'<line x1="{_f(l.a[0])}" y1="{_f(l.a[1])}" x2="{_f(l.b[0])}" y2="{_f(l.b[1])}" stroke-width="{_f(max(l.width, 0.5))}"/>' for l in prims.lines[:limit]]
    for a in prims.arcs[:limit]:
        p, q = arc_point(a.c, a.r, a.start), arc_point(a.c, a.r, a.end)
        large = 1 if arc_span(a.start, a.end) > 180 else 0
        out.append(f'<path d="M{_f(p[0])} {_f(p[1])} A{_f(a.r)} {_f(a.r)} 0 {large} 1 {_f(q[0])} {_f(q[1])}"/>')
    return out


def render(arch: Architecture, prims: Primitives, background: bool = True, limit: int = 60000) -> str:
    """The SVG text of the recognized plan."""
    w, h = arch.size
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{_f(w)}" height="{_f(h)}" viewBox="0 0 {_f(w)} {_f(h)}" data-source="{escape(arch.source)}">',
           f'<rect width="{_f(w)}" height="{_f(h)}" fill="#ffffff"/>']
    if background:
        out += ['<g id="ARQ-FONDO" data-layer="arq.background" fill="none" stroke="#9aa3b5" stroke-opacity="0.7">', *_background(prims, limit), "</g>"]
    by_kind = {"door": [o for o in arch.openings if o.kind == "door"], "window": [o for o in arch.openings if o.kind == "window"], "opening": [o for o in arch.openings if o.kind == "opening"]}
    body = [[_wall(x) for x in arch.walls], [_door(o) for o in by_kind["door"]], [_span_line(o, "#2563eb") for o in by_kind["window"]], [_span_line(o, "#9ca3af") for o in by_kind["opening"]]]
    for (gid, role), items in zip(LAYERS, body):
        out += [f'<g id="{gid}" data-layer="{role}">', *items, "</g>"]
    return "\n".join(out + ["</svg>", ""])
