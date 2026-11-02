"""The recognition end to end, always in the same order: read the source, bring it to the plan space, find the walls, find the openings in them, guess the scale, say it as data and as an SVG.
Each step is a function of its own that knows nothing of the others' inner workings, so a step can be replaced (another reader, another strategy) without touching the rest."""
import math
import statistics
from dataclasses import dataclass
from typing import Any, Dict, Optional

from epc_arch import normalize as plan_space
from epc_arch import sources, svgout
from epc_arch.config import PARAMS, Hints, scale_for
from epc_arch.model import Architecture, Line, Options, Primitives
from epc_arch.recognizers import Context
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


def recognize(data: bytes, name: str = "", options: Options = Options()) -> Result:
    """The architecture of a plan given as a DXF, a vector PDF or an image, and the SVG of it. Raises ArchError when the file cannot be read."""
    raw = sources.read(data, name, options)
    prims, size = plan_space.normalize(raw)
    units = options.units_per_metre or prims.units_per_metre
    ctx = Context(size=size, scale=scale_for(size, units), hints=Hints())
    walls, T, openings, rooms = _read(prims, size, units, ctx)
    if prims.ink is not None:
        # A picture can be read in several ways: by its thick strokes, by its lines, or with walls drawn as pairs of lines shut into bands. The reading that closes more of the plan into
        # rooms is the one that found the walls, unless it has far more walls than the first: hatching closes many small cells too.
        candidates = [(prims, (walls, T, openings, rooms))]
        variants = [Primitives(**{**prims.__dict__, "lines": alt, "alternatives": []}) for alt in prims.alternatives]
        if any(l.layer == "wall" for l in prims.lines):
            variants.append(Primitives(**{**prims.__dict__, "lines": [Line(l.a, l.b, l.width) for l in prims.lines], "alternatives": []}))
        candidates += [(v, _read(v, size, units, ctx)) for v in variants]
        readable = [c for c in candidates if c[1][0]]
        if readable:
            base = len(walls) if _closed(candidates[0][1], size) >= 0.05 else None       # when the first reading closed little, it is no measure of how many walls a plan has
            fair = [c for c in readable if base is None or len(c[1][0]) <= 2 * base + 10] or readable
            best = max(fair, key=lambda c: _closed(c[1], size))
            if _closed(best[1], size) > 1.3 * _closed(candidates[0][1], size) or not walls:
                prims, (walls, T, openings, rooms) = best
    left_out = 0
    if T:
        walls, openings, rooms, left_out = keep_the_plan(walls, openings, rooms, T, ctx)
    arch = Architecture(source=prims.source, size=size, units_per_metre=units, scale_hint=None, wall_thickness=T, walls=walls, openings=openings, warnings=list(prims.warnings))
    arch.rooms = rooms
    if left_out:
        arch.warnings.append(f"the sheet has several views: {left_out} without rooms or doors (sections, elevations, details) were left out and the plan kept")
    arch.drawing_scale = prims.scale
    arch.scale_hint = scale_hint(arch, bool(units))
    _empty_warnings(arch, T is not None)
    return Result(arch, svgout.render(arch, prims, options.background))


__all__ = ["recognize", "Result", "Primitives"]
