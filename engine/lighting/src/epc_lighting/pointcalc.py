"""Point-by-point illuminance: E = I * cos(theta) / r^2 summed over the luminaires.

For a horizontal plane this is the UPV article's E_H = I cos^3(alpha) / H^2 and
for a vertical one E_V = I cos^2(alpha) sin(alpha) / H^2; the vector form here
gives both (and any tilt) from the angle between the ray and the surface normal.
Only the direct component is computed: light reflected by walls and ceiling is
not included, so the figures are a lower bound of the lumen-method average.
"""
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Sequence, Tuple

from epc_lighting.config import PARAMS
from epc_lighting.model import LightingError, Photometry, PointSpec, rnd
from epc_lighting.photometry import intensity_cd

Normal = Tuple[float, float, float]
HORIZONTAL: Normal = (0.0, 0.0, 1.0)


@dataclass(frozen=True)
class Source:
    """A luminaire placed in the room, aimed straight down."""
    x: float
    y: float
    z: float
    photometry: Photometry
    lamp_flux_lm: float


def _contribution(src: Source, point: Tuple[float, float, float], normal: Normal) -> float:
    dx, dy, dz = src.x - point[0], src.y - point[1], src.z - point[2]
    r2 = dx * dx + dy * dy + dz * dz
    if r2 <= 0:
        return 0.0
    r = math.sqrt(r2)
    cos_incidence = (dx * normal[0] + dy * normal[1] + dz * normal[2]) / r
    if cos_incidence <= 0:
        return 0.0
    gamma = math.degrees(math.acos(max(-1.0, min(1.0, dz / r))))
    c_plane = math.degrees(math.atan2(-dy, -dx))
    return intensity_cd(src.photometry, gamma, c_plane, src.lamp_flux_lm) * cos_incidence / r2


def illuminance_at(sources: Sequence[Source], point: Tuple[float, float, float], normal: Normal = HORIZONTAL) -> float:
    """Direct illuminance in lux at a point on a surface with the given unit normal."""
    return sum(_contribution(s, point, normal) for s in sources)


def grid_points(width_m: float, length_m: float, step_m: float) -> List[Tuple[float, float]]:
    """Cell-centre points, x along the length and y along the width, never coarser than step_m."""
    limit = PARAMS["point_grid"]["max_points"]
    step = step_m
    while True:
        nx, ny = math.ceil(length_m / step - 1e-9), math.ceil(width_m / step - 1e-9)
        if nx * ny <= limit:
            break
        step *= 1.1
    dx, dy = length_m / nx, width_m / ny
    return [((i + 0.5) * dx, (j + 0.5) * dy) for j in range(ny) for i in range(nx)]


def _stats(values: List[float], maintenance: float) -> Dict[str, Any]:
    low, high, avg = min(values), max(values), sum(values) / len(values)
    return {
        "min_lux": rnd(low * maintenance),
        "avg_lux": rnd(avg * maintenance),
        "max_lux": rnd(high * maintenance),
        "min_over_avg": rnd(low / avg) if avg > 0 else 0.0,
        "max_over_avg": rnd(high / avg) if avg > 0 else 0.0,
        "max_over_min": rnd(high / low) if low > 0 else None,
    }


def _uniformity_warnings(stats: Dict[str, Any]) -> List[str]:
    limits = PARAMS["uniformity_limits"]
    found = []
    if stats["min_over_avg"] < limits["min_over_avg"]:
        found.append(f"min/avg illuminance {stats['min_over_avg']} is below {round(limits['min_over_avg'], 3)}: the darkest zone is too dark")
    if stats["max_over_avg"] > limits["max_over_avg"]:
        found.append(f"max/avg illuminance {stats['max_over_avg']} is above {limits['max_over_avg']}: bright spots, consider less reflective surfaces")
    if stats["max_over_min"] is None or stats["max_over_min"] > limits["max_over_min"]:
        found.append(f"max/min illuminance is above {limits['max_over_min']}: strong contrast between zones")
    return found


def _points_report(sources: Sequence[Source], points: Sequence[PointSpec], plane_m: float, maintenance: float) -> List[Dict[str, Any]]:
    report = []
    for p in points:
        e = illuminance_at(sources, (p.x_m, p.y_m, plane_m), p.normal)
        report.append({"id": p.id, "x_m": rnd(p.x_m), "y_m": rnd(p.y_m), "initial_lux": rnd(e), "maintained_lux": rnd(e * maintenance)})
    return report


def calculate(
    sources: Sequence[Source],
    width_m: float,
    length_m: float,
    plane_m: float,
    step_m: float,
    maintenance: float,
    points: Sequence[PointSpec] = (),
) -> Tuple[Dict[str, Any], List[str]]:
    """Grid statistics (maintained lux) plus any requested points; returns (report, warnings)."""
    if step_m <= 0:
        raise LightingError("point step must be greater than 0 m")
    grid = grid_points(width_m, length_m, step_m)
    values = [illuminance_at(sources, (x, y, plane_m)) for x, y in grid]
    stats = _stats(values, maintenance)
    report = {
        "computed": True,
        "component": "direct only (inter-reflections not included)",
        "plane_height_m": rnd(plane_m),
        "grid_points": len(grid),
        "maintenance_factor": rnd(maintenance),
        **stats,
        "points": _points_report(sources, points, plane_m, maintenance),
    }
    return report, _uniformity_warnings(stats)
