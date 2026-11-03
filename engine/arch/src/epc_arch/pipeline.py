"""The recognition end to end, always in the same order: read the source, bring it to the plan space, find the walls, find the openings in them, guess the scale, say it as data and as an SVG.
Each step is a function of its own that knows nothing of the others' inner workings, so a step can be replaced (another reader, another strategy) without touching the rest."""
import math
import statistics
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from epc_arch import normalize as plan_space
from epc_arch import sources, svgout
from epc_arch.config import PARAMS, Hints, scale_for
from epc_arch.model import Architecture, Line, Options, Primitives
from epc_arch.recognizers import Context
from epc_arch.recognizers import annotations
from epc_arch.recognizers import align as sheet_align
from epc_arch.recognizers import levels as sheet_levels
from epc_arch.recognizers import sheet as sheet_views
from epc_arch.recognizers.openings import recognize_openings
from epc_arch.recognizers.rooms import recognize_rooms
from epc_arch.recognizers.views import keep_the_plan
from epc_arch.recognizers.walls import recognize_walls


@dataclass
class Result:
    architecture: Architecture
    svg: str

    def as_dict(self) -> Dict[str, Any]:
        return self.architecture.as_dict()


def scale_hint(arch: Architecture, units_known: bool) -> Optional[Dict[str, Any]]:
    """A guess of the units per metre from what a plan nearly always has: a door leaf about 0.9 m wide. Only a hint, never applied by itself."""
    if units_known:
        return None
    radii = [o.width for o in arch.openings if o.kind == "door" and "arc" in o.reason]
    if not radii:
        return None
    leaf = PARAMS["metres"]["typical_door_leaf"]
    return {"units_per_metre": round(statistics.median(radii) / leaf, 3), "basis": f"{len(radii)} door leaves taken as {leaf} m", "confidence": round(min(0.7, 0.3 + 0.05 * len(radii)), 2)}


def _empty_warnings(arch: Architecture, calibrated: bool) -> None:
    if not calibrated:
        arch.warnings.append("no walls were recognized: no thickness stood out among the strokes (walls drawn as two parallel lines or as a thick band are the ones read)")
    elif not arch.openings:
        arch.warnings.append("no doors, windows or openings were recognized")


def _read(prims: Primitives, size, units, ctx: Context):
    """Walls, their thickness, the openings and the rooms of one reading of the primitives."""
    walls, T, _ = recognize_walls(prims, ctx)
    openings = recognize_openings(prims, walls, T, ctx) if T else []
    rooms = recognize_rooms(walls, openings, T, size, units, ctx) if T else []
    return walls, T, openings, rooms


def _closed(reading, size) -> float:
    """How well a reading closes the plan into rooms: the share of the sheet it closes, weighed by how many rooms (a reading that only finds the outline closes one big box)
    and by the doors it found (rooms closed by shutting wide gaps, with no door in any wall, are not a plan read well)."""
    _, T, openings, rooms = reading
    doors = sum(1 for o in openings if o.kind == "door")
    return sum(r.area for r in rooms) / (size[0] * size[1]) * math.sqrt(len(rooms)) * (1 + 0.15 * doors) if T else 0.0


def _architecture(prims: Primitives, size, options: Options) -> Tuple[Architecture, Primitives]:
    """The architecture of one drawing (a plan, or one view of a sheet) and the primitives of the reading that found it."""
    units = options.units_per_metre or prims.units_per_metre
    ctx = Context(size=size, scale=scale_for(size, units), hints=Hints())
    prims, marks = annotations.split(prims, size)
    walls, T, openings, rooms = _read(prims, size, units, ctx)
    if prims.ink is not None:
        prims, (walls, T, openings, rooms) = _best_reading(prims, (walls, T, openings, rooms), size, units, ctx)
    left_out = 0
    if T:
        walls, openings, rooms, left_out = keep_the_plan(walls, openings, rooms, T, ctx)
    arch = Architecture(source=prims.source, size=size, units_per_metre=units, scale_hint=None, wall_thickness=T, walls=walls, openings=openings, warnings=list(prims.warnings))
    arch.rooms = rooms
    arch.annotations = marks
    if left_out:
        arch.warnings.append(f"the sheet has several views: {left_out} without rooms or doors (sections, elevations, details) were left out and the plan kept")
    arch.drawing_scale = prims.scale
    arch.scale_hint = scale_hint(arch, bool(units))
    _empty_warnings(arch, T is not None)
    return arch, prims


def _readings(prims: Primitives, first, size, units, ctx: Context):
    """The first reading of a picture and the others it allows: its alternatives, and the plain lines when some were taken as walls by their layer."""
    variants = [Primitives(**{**prims.__dict__, "lines": alt, "alternatives": []}) for alt in prims.alternatives]
    if any(l.layer == "wall" for l in prims.lines):
        variants.append(Primitives(**{**prims.__dict__, "lines": [Line(l.a, l.b, l.width) for l in prims.lines], "alternatives": []}))
    return [(prims, first)] + [(v, _read(v, size, units, ctx)) for v in variants]


def _fair(readable, first, size):
    """The readings that do not have far more walls than the first (hatching closes many small cells too); when the first closed little it is no measure of how many walls a plan has."""
    base = len(first[0]) if _closed(first, size) >= 0.05 else None
    return [c for c in readable if base is None or len(c[1][0]) <= 2 * base + 10] or readable


def _best_reading(prims: Primitives, first, size, units, ctx: Context):
    """A picture can be read in several ways: by its thick strokes, by its lines, or with walls drawn as pairs of lines shut into bands. The reading that closes more of the plan into
    rooms is the one that found the walls."""
    readable = [c for c in _readings(prims, first, size, units, ctx) if c[1][0]]
    if not readable:
        return prims, first
    best = max(_fair(readable, first, size), key=lambda c: _closed(c[1], size))
    return best if _closed(best[1], size) > 1.3 * _closed(first, size) or not first[0] else (prims, first)


@dataclass
class Sheet:
    """What a file holds: one plan, or the plans of a sheet (one per floor, from the lowest up) laid in a frame they share."""
    levels: List[Result]
    warnings: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {"schema_version": "1.0", "plans": len(self.levels), "warnings": self.warnings,
                "levels": [{"level": r.as_dict()["level"], "counts": r.architecture.counts(), "reference": r.as_dict()["reference"], "size": r.as_dict()["size"]} for r in self.levels]}


def _score(arch: Architecture, cfg) -> int:
    return len(arch.rooms) + cfg["door_weight"] * sum(1 for o in arch.openings if o.kind == "door")


def _plans(parts, cfg):
    """The views that are plans: those with walls whose rooms and doors are not far below the best (a section or an elevation has none)."""
    scores = [_score(a, cfg) if a.walls else 0 for _, a, _ in parts]
    best = max(scores, default=0)
    return [p for p, s in zip(parts, scores) if best > 0 and s >= cfg["keep_share"] * best]


def _frame(plans, ranked, shifts, T: float):
    """The size of the frame the floors share and the shift of each into it: the frame starts at the corner of what the floors cover, with a margin."""
    boxes = {i: sheet_align._bounds(plans[i][1].walls) for i in ranked}
    x0 = min(boxes[i][0] + shifts[i][0] for i in ranked)
    y0 = min(boxes[i][1] + shifts[i][1] for i in ranked)
    x1 = max(boxes[i][2] + shifts[i][0] for i in ranked)
    y1 = max(boxes[i][3] + shifts[i][1] for i in ranked)
    pad = 2 * T
    return (x1 - x0 + 2 * pad, y1 - y0 + 2 * pad), {i: (shifts[i][0] - x0 + pad, shifts[i][1] - y0 + pad) for i in ranked}, pad


def _lay_over(plans, options: Options) -> List[Result]:
    """The plans from the lowest floor up, in one frame: the walls of each laid over those of the lowest."""
    levels = sheet_levels.assign([v.box for v, _, _ in plans], [v.texts for v, _, _ in plans])
    ranked = sheet_levels.order(levels)
    ref = plans[ranked[0]][1]
    T = ref.wall_thickness or 1.0
    shifts, agreed = {}, {}
    for i in ranked:
        shifts[i], agreed[i] = ((0.0, 0.0), True) if i == ranked[0] else sheet_align.shift_onto(ref, plans[i][1], T)
    size, moves, pad = _frame(plans, ranked, shifts, T)
    out = []
    for i in ranked:
        dx, dy = moves[i]
        arch = sheet_align.move(plans[i][1], dx, dy, size, (pad, pad))
        arch.level = levels[i]
        if not agreed[i]:
            arch.warnings.append("the walls of this floor do not match those of the lowest one: the floors were put corner to corner, check that they line up")
        if levels[i].source == "order":
            arch.warnings.append("the sheet does not name this plan's floor: plans were numbered in reading order")
        out.append(Result(arch, svgout.render(arch, sheet_align.move_prims(plans[i][2], dx, dy), options.background)))
    return out


def recognize_sheet(data: bytes, name: str = "", options: Options = Options()) -> Sheet:
    """The plans of a file: a sheet with several plans gives one architecture per plan (its floor, in a frame the floors share), without its frame, title block, sections and elevations;
    any other file gives its one plan. Raises ArchError when the file cannot be read."""
    raw = sources.read(data, name, options)
    prims, size = plan_space.normalize(raw)
    views = sheet_views.split(prims, size)
    if views:
        parts = [(v, *_architecture(v.prims, v.size, options)) for v in views]
        plans = _plans(parts, PARAMS["views"])
        if plans:
            sheet = Sheet(_lay_over(plans, options))
            if len(views) > len(plans):
                sheet.warnings.append(f"the sheet has {len(views)} views: {len(views) - len(plans)} that are not plans (sections, elevations, tables) were left out")
            return sheet
    arch, used = _architecture(prims, size, options)
    return Sheet([Result(arch, svgout.render(arch, used, options.background))])


def recognize(data: bytes, name: str = "", options: Options = Options()) -> Result:
    """The architecture of a plan given as a DXF, a vector PDF or an image, and the SVG of it. A sheet with several plans gives the lowest floor (use `recognize_sheet` for all of them).
    Raises ArchError when the file cannot be read."""
    sheet = recognize_sheet(data, name, options)
    first = sheet.levels[0]
    if len(sheet.levels) > 1:
        first.architecture.warnings.append(f"the file is a sheet with {len(sheet.levels)} plans: this is the lowest; the others are in `recognize_sheet`")
    return first
