"""The values the engine passes around. Immutable but the containers."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from epc_lighting.config import PARAMS, VERSION


class LightingError(Exception):
    """The input cannot be processed: the message says what to fix."""


def rnd(x: float) -> float:
    """Round for output; refuses NaN/inf so a bad number never reaches the JSON."""
    if not math.isfinite(x):
        raise LightingError("a non-finite number was produced: check the dimensions and factors in the input")
    value = round(float(x), PARAMS["rounding_digits"])
    return 0.0 if value == 0 else value


@dataclass(frozen=True)
class Estimate:
    """A number with the reason it has that value and how far to trust it (0-1)."""
    value: float
    reason: str
    confidence: float = 1.0

    def as_dict(self) -> Dict[str, Any]:
        return {"value": rnd(self.value), "reason": self.reason, "confidence": round(self.confidence, 2)}


@dataclass(frozen=True)
class CuTable:
    """Coefficient-of-utilisation table: values[i][j] for axis value i and reflectance column j.

    Each column is (ceiling, walls, floor). Values are fractions (percent already divided by 100).
    """
    axis: str
    axis_values: Tuple[float, ...]
    columns: Tuple[Tuple[float, float, float], ...]
    values: Tuple[Tuple[float, ...], ...]


@dataclass(frozen=True)
class Photometry:
    """Intensity distribution in cd per klm of lamp flux.

    gamma_deg is the angle from the downward vertical; c_deg lists the C planes
    (a single plane means rotational symmetry); values[c][gamma].
    """
    gamma_deg: Tuple[float, ...]
    c_deg: Tuple[float, ...]
    values: Tuple[Tuple[float, ...], ...]


@dataclass(frozen=True)
class Luminaire:
    id: str
    name: str
    lamps: int
    lamp_flux_lm: float
    efficiency: float
    power_w: Optional[float] = None
    cu: Optional[float] = None
    cu_table: Optional[CuTable] = None
    photometry: Optional[Photometry] = None
    distribution: Optional[str] = None
    spacing_ratio: Optional[float] = None

    @property
    def flux_lm(self) -> float:
        return self.lamps * self.lamp_flux_lm


@dataclass(frozen=True)
class PointSpec:
    id: str
    x_m: float
    y_m: float
    normal: Tuple[float, float, float]


@dataclass(frozen=True)
class Room:
    id: str
    name: str
    width_m: float
    length_m: float
    height_m: float
    work_plane_m: float
    suspension_m: float
    suspension_mode: Optional[str]
    luminaire_id: str
    method: str
    system: str
    target_lux: Optional[float]
    activity: Optional[str]
    reflectances: Tuple[Estimate, Estimate, Estimate]
    environment: str
    maintenance: Optional[float]
    cu: Optional[float]
    points: Tuple[PointSpec, ...] = ()
    point_step_m: Optional[float] = None
    operating_hours: Optional[float] = None
    ugr_calculated: Optional[float] = None
    target_rule: Optional[str] = None
    positions: Tuple[Tuple[float, float, Optional[float], Optional[str]], ...] = ()          # luminaires already drawn: (x_m, y_m, z_m, tag)

    @property
    def area_m2(self) -> float:
        return self.width_m * self.length_m


@dataclass(frozen=True)
class Area:
    id: str
    name: str
    area_m2: float
    luminaire_id: str
    target_lux: Optional[float]
    activity: Optional[str]
    beam_utilisation: Optional[float]
    enclosure: str
    maintenance: Optional[float]
    operating_hours: Optional[float] = None
    target_rule: Optional[str] = None


@dataclass(frozen=True)
class Route:
    """An escape route: the axis along which the emergency illuminance is checked (metres from the corner of the room)."""
    id: str
    start: Tuple[float, float]
    end: Tuple[float, float]
    e_min_lux: Optional[float] = None


@dataclass(frozen=True)
class Emergency:
    """A room with antipanic emergency lighting: the grid of luminaires is sized so that the floor keeps the minimum illuminance."""
    id: str
    name: str
    width_m: float
    length_m: float
    height_m: float
    luminaire_id: str
    e_min_lux: Optional[float] = None
    ratio_max: Optional[float] = None
    maintenance: Optional[float] = None
    band_m: Optional[float] = None
    step_m: Optional[float] = None
    routes: Tuple[Route, ...] = ()


@dataclass(frozen=True)
class Project:
    luminaires: Dict[str, Luminaire]
    rooms: Tuple[Room, ...]
    areas: Tuple[Area, ...]
    emergency: Tuple[Emergency, ...] = ()


@dataclass(frozen=True)
class Options:
    """Everything the caller may want to change. No environment variables."""
    enforce_spacing: bool = False
    spacing_basis: str = "height"
    compute_points: bool = True
    point_step_m: float = PARAMS["point_grid"]["step_m"]
    return_grid: bool = False                         # also give the illuminance of every cell of the grid (for a map), not only its statistics


@dataclass
class Context:
    """What a flux method needs besides the room and the luminaire."""
    target: Estimate
    maintenance: Estimate
    mounting: Estimate
    system: Dict[str, Any]
    warnings: List[str]


@dataclass(frozen=True)
class FluxPlan:
    """What a flux method answers: the flux the room needs and how it got there."""
    required_flux_lm: float
    cu: Estimate
    geometry: Dict[str, Any]


@dataclass
class Result:
    rooms: List[Dict[str, Any]] = field(default_factory=list)
    areas: List[Dict[str, Any]] = field(default_factory=list)
    emergency: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def luminaire_count(self) -> int:
        total = sum(r["layout"]["installed"] for r in self.rooms)
        return total + sum(a["flux"]["luminaires_required"] for a in self.areas)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": "1.0",
            "engine": {"name": "epc_lighting", "version": VERSION},
            "counts": {
                "rooms": len(self.rooms),
                "areas": len(self.areas),
                "emergency": len(self.emergency),
                "luminaires": self.luminaire_count(),
                "warnings": len(self.warnings),
            },
            "rooms": self.rooms,
            "areas": self.areas,
            "emergency": self.emergency,
            "warnings": list(self.warnings),
        }
