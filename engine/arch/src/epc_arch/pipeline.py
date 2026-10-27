"""The recognition end to end, always in the same order: read the source, bring it to the plan space, find the walls, find the openings in them, guess the scale, say it as data and as an SVG.
Each step is a function of its own that knows nothing of the others' inner workings, so a step can be replaced (another reader, another strategy) without touching the rest."""
import statistics
from dataclasses import dataclass
from typing import Any, Dict, Optional

from epc_arch import normalize as plan_space
from epc_arch import sources, svgout
from epc_arch.config import PARAMS, Hints, scale_for
from epc_arch.model import Architecture, Options, Primitives
from epc_arch.recognizers import Context
from epc_arch.recognizers.openings import recognize_openings
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


def recognize(data: bytes, name: str = "", options: Options = Options()) -> Result:
    """The architecture of a plan given as a DXF, a vector PDF or an image, and the SVG of it. Raises ArchError when the file cannot be read."""
    raw = sources.read(data, name, options)
    prims, size = plan_space.normalize(raw)
    units = options.units_per_metre or prims.units_per_metre
    ctx = Context(size=size, scale=scale_for(size, units), hints=Hints())
    walls, T, _ = recognize_walls(prims, ctx)
    openings = recognize_openings(prims, walls, T, ctx) if T else []
    arch = Architecture(source=prims.source, size=size, units_per_metre=units, scale_hint=None, wall_thickness=T, walls=walls, openings=openings, warnings=list(prims.warnings))
    arch.scale_hint = scale_hint(arch, bool(units))
    _empty_warnings(arch, T is not None)
    return Result(arch, svgout.render(arch, prims, options.background))


__all__ = ["recognize", "Result", "Primitives"]
