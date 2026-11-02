"""Sheets with several views. A sheet often carries the plan together with sections and elevations: each view is a group of walls of its own, apart from the others. A plan is the view with
rooms and doors (a section cuts slabs and walls into long bands, an elevation has no doors drawn open), so the groups that score far below the best are left out."""
from typing import List, Tuple

from epc_arch.model import Opening, Room, Wall
from epc_arch.recognizers import Context
from epc_arch.recognizers.walls import _components

Box = Tuple[float, float, float, float]


def _box(walls: List[Wall], pad: float) -> Box:
    xs = [c for w in walls for c in (w.a[0], w.b[0])]
    ys = [c for w in walls for c in (w.a[1], w.b[1])]
    return min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad


def _inside(p, box: Box) -> bool:
    return box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3]


def keep_the_plan(walls: List[Wall], openings: List[Opening], rooms: List[Room], T: float, ctx: Context) -> Tuple[List[Wall], List[Opening], List[Room], int]:
    """The walls, openings and rooms of the views that are plans, and how many views were left out."""
    cfg = ctx.params["views"]
    groups = _components(walls, 3 * T, ctx.params["relative"]["opening_width_in_walls"][1] * T, ctx.params["walls"]["angle_tolerance_deg"])
    if len(groups) < 2:
        return walls, openings, rooms, 0
    scored = []
    for g in groups:
        box = _box([walls[i] for i in g], T)
        score = sum(1 for r in rooms if _inside(r.at, box)) + cfg["door_weight"] * sum(1 for o in openings if o.kind == "door" and _inside(o.at, box))
        scored.append((score, g, box))
    best = max(s for s, _, _ in scored)
    if best <= 0:
        return walls, openings, rooms, 0
    kept = [(g, box) for s, g, box in scored if s >= cfg["keep_share"] * best]
    keep_ids = {i for g, _ in kept for i in g}
    boxes = [box for _, box in kept]
    inside = lambda p: any(_inside(p, b) for b in boxes)                      # noqa: E731
    return ([w for i, w in enumerate(walls) if i in keep_ids], [o for o in openings if inside(o.at)], [r for r in rooms if inside(r.at)], len(scored) - len(kept))
