"""Synthetic plans for the tests: one small flat (a room of 6 x 4 m with walls 0.2 m thick, a door and a window), written as a DXF, as a vector PDF and as an image, so each reader can be
checked against the same expected result. Everything in metres of a y-up plan; the writers scale it."""
import io
import math
import tempfile
from pathlib import Path
from typing import List, Tuple

import ezdxf
from PIL import Image, ImageDraw

T = 0.2
W, H = 6.0, 4.0
DOOR = (2.0, 2.9)            # gap in the bottom wall, hinge at its left end
WINDOW = (3.0, 4.2)          # gap in the top wall

Segment = Tuple[Tuple[float, float], Tuple[float, float]]


def room_lines(door: bool = True, window: bool = True) -> List[Segment]:
    """The two faces of each wall as lines, with a gap where the door and the window are."""
    out: List[Segment] = []

    def face_h(y: float, gap):
        spans = [(0.0, W)] if gap is None else [(0.0, gap[0]), (gap[1], W)]
        out.extend(((x0, y), (x1, y)) for x0, x1 in spans)

    for y in (0.0, T):
        face_h(y, DOOR if door else None)
    for y in (H - T, H):
        face_h(y, WINDOW if window else None)
    for x in (0.0, T, W - T, W):
        out.append(((x, 0.0), (x, H)))
    return out


def window_lines() -> List[Segment]:
    return [((WINDOW[0], H - 0.1 - d), (WINDOW[1], H - 0.1 - d)) for d in (0.05, -0.05)]


def door_leaf() -> Segment:
    return ((DOOR[0], T / 2), (DOOR[0], T / 2 + (DOOR[1] - DOOR[0])))


def door_arc() -> Tuple[Tuple[float, float], float, float, float]:
    """Centre, radius, start and end angle (degrees, counter-clockwise, y up): the leaf swings from the closed position along the wall to the open one."""
    return (DOOR[0], T / 2), DOOR[1] - DOOR[0], 0.0, 90.0


def room_dxf(unit: float = 1.0, insunits: int = 6, layer: str = "0", door_arc_on: bool = True, extra=(), rotate: float = 0.0) -> bytes:
    doc = ezdxf.new("R2010")
    doc.units = insunits
    msp = doc.modelspace()
    if layer not in doc.layers:
        doc.layers.add(layer)
    k = unit
    cs, sn = math.cos(math.radians(rotate)), math.sin(math.radians(rotate))
    rot = lambda p: ((p[0] * cs - p[1] * sn) * k, (p[0] * sn + p[1] * cs) * k)           # noqa: E731
    for (a, b) in room_lines():
        msp.add_line(rot(a), rot(b), dxfattribs={"layer": layer})
    for (a, b) in window_lines():
        msp.add_line(rot(a), rot(b), dxfattribs={"layer": layer})
    if door_arc_on:
        (cx, cy), r, a0, a1 = door_arc()
        msp.add_arc(rot((cx, cy)), r * k, a0 + rotate, a1 + rotate)
        a, b = door_leaf()
        msp.add_line(rot(a), rot(b))
    for e in extra:
        e(msp, k)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "t.dxf"
        doc.saveas(str(path))
        return path.read_bytes()


def make_pdf(content: str, width: int = 700, height: int = 500) -> bytes:
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width} {height}] /Contents 4 0 R /Resources << >> >>".encode(),
            b"<< /Length %d >>\nstream\n" % len(content.encode()) + content.encode() + b"\nendstream"]
    out = b"%PDF-1.4\n"
    offsets = []
    for i, o in enumerate(objs, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    out += b"".join(b"%010d 00000 n \n" % o for o in offsets)
    return out + b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)


def room_pdf(scale: float = 100.0, arc: bool = True) -> bytes:
    """The room as a CAD program writes it: one stroked path per line and the door swing as a Bézier curve (a quarter circle)."""
    ox, oy = 50.0, 50.0
    ops = ["0.4 w"]
    for (a, b) in room_lines() + window_lines() + [door_leaf()]:
        ops.append(f"{ox + a[0] * scale:.3f} {oy + a[1] * scale:.3f} m {ox + b[0] * scale:.3f} {oy + b[1] * scale:.3f} l S")
    if arc:
        (cx, cy), r, _, _ = door_arc()
        c = 0.5522847498 * r
        p = lambda x, y: f"{ox + x * scale:.3f} {oy + y * scale:.3f}"                       # noqa: E731
        ops.append(f"{p(cx + r, cy)} m {p(cx + r, cy + c)} {p(cx + c, cy + r)} {p(cx, cy + r)} c S")
    return make_pdf("\n".join(ops))


def room_png(px_per_m: float = 150.0, thick: int = 12) -> bytes:
    """The room as a picture: walls as thick black bands, the door as a gap, the window as a gap with two thin lines."""
    ox, oy = 100, 100
    w, h = int(W * px_per_m) + 2 * ox, int(H * px_per_m) + 2 * oy
    img = Image.new("L", (w, h), 255)
    d = ImageDraw.Draw(img)
    X = lambda x: ox + x * px_per_m                                                          # noqa: E731
    Y = lambda y: oy + (H - y) * px_per_m                                                    # noqa: E731
    mid = T / 2

    def band(x0, y0, x1, y1):
        px, py = (thick / 2 if x0 == x1 else 0), (thick / 2 if y0 == y1 else 0)
        xs, ys = sorted((X(x0), X(x1))), sorted((Y(y0), Y(y1)))
        d.rectangle([xs[0] - px, ys[0] - py, xs[1] + px, ys[1] + py], fill=0)

    band(0, mid, DOOR[0], mid)
    band(DOOR[1], mid, W, mid)
    band(0, H - mid, WINDOW[0], H - mid)
    band(WINDOW[1], H - mid, W, H - mid)
    band(mid, 0, mid, H)
    band(W - mid, 0, W - mid, H)
    for dy in (-0.05, 0.05):
        d.line([X(WINDOW[0]), Y(H - mid + dy), X(WINDOW[1]), Y(H - mid + dy)], fill=0, width=2)
    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


def arc_angle(a: Tuple[float, float], c: Tuple[float, float]) -> float:
    return math.degrees(math.atan2(a[1] - c[1], a[0] - c[0])) % 360.0
