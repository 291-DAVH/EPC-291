"""What the lighting calculation is asked: the rooms of a sheet (as the editor has them, in view units), the parameters of each one and the options of the calculation."""
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    """Numbers of a request are finite: JSON allows the literals NaN and Infinity, a calculation cannot use them."""
    model_config = ConfigDict(allow_inf_nan=False)


class Scale(Strict):
    """The calibration of a sheet: two points of the view that are `distance_m` metres apart."""
    p1: List[float] = Field(min_length=2, max_length=2)
    p2: List[float] = Field(min_length=2, max_length=2)
    distance_m: float = Field(gt=0)


class PlanRoom(Strict):
    """A room marked on the plan: its outline in view units."""
    id: str = Field(min_length=1, max_length=64)
    name: str = Field("", max_length=120)
    points: List[List[float]] = Field(min_length=3, max_length=500)


class PlanNode(Strict):
    """An element of the drawing that may be a luminaire (`LU`): where it is and what the calculation said of it when it was placed."""
    id: str = Field(min_length=1, max_length=64)
    kind: str = Field(max_length=16)
    x: float
    y: float
    tag: str = Field("", max_length=40)
    attrs: Dict[str, Any] = {}


class Sheet(Strict):
    scale: Optional[Scale] = None
    rooms: List[PlanRoom] = Field([], max_length=500)
    nodes: List[PlanNode] = Field([], max_length=5000)                      # only read to check the room as it is drawn (`use_drawn`)


class RoomParams(Strict):
    """What the engine needs to know about a room that the plan does not say: what it is for, which luminaire, the method and what the person wants to fix by hand.
    Everything left out is estimated by the engine, which says how sure it is."""
    activity: str = Field("", max_length=80)
    luminaire: str = Field("", max_length=64)
    method: Literal["lumen", "zonal"] = "lumen"
    height_m: Optional[float] = Field(None, gt=0, le=60)
    target_lux: Optional[float] = Field(None, gt=0, le=100000)
    coefficient_of_utilisation: Optional[float] = Field(None, gt=0, le=1.5)
    work_plane_height_m: Optional[float] = Field(None, ge=0, le=60)
    operating_hours_per_year: Optional[float] = Field(None, ge=0, le=8760)
    reflectances: Optional[Dict[str, Any]] = None
    exterior: bool = False                                               # an exterior area: floodlights by the beam method, from the area and the target (nothing about its walls or its height)
    beam_utilisation: Optional[float] = Field(None, gt=0, le=1)
    enclosure: Literal["open", "closed"] = "open"
    maintenance_factor: Optional[float] = Field(None, gt=0, le=1)
    norm_rule: str = Field("", max_length=80)                              # the id of a rule of a norm (approved in the norms review) that gives the target in lux
    emergency_luminaire: str = Field("", max_length=64)                    # an interior luminaire for the antipanic emergency lighting of the room: the grid that keeps the minimum illuminance on the floor
    emergency_e_min_lux: Optional[float] = Field(None, gt=0, le=1000)
    ugr_calculated: Optional[float] = Field(None, ge=0, le=100)           # the UGR of the room calculated outside: it is compared with the limit of the activity


class CalcOptions(Strict):
    enforce_spacing: bool = False
    spacing_basis: Literal["height", "distribution"] = "height"
    compute_points: bool = True
    use_drawn: bool = False                                              # check each room with the luminaires drawn in it, not with the grid the engine would arrange
    auto_luminaire: bool = False                                         # choose the luminaire of a room that has a target but no luminaire: the one that complies with the least power
    power_limit_w_m2: Optional[float] = Field(None, gt=0, le=1000)       # installed power density that a room should not exceed (the person's, the engine has none)
    kwh_price: Optional[float] = Field(None, ge=0, le=100000)
    hours_default: Optional[float] = Field(None, ge=0, le=8760)          # operating hours per year of the rooms that do not say their own
    map: bool = False                                                    # also give the illuminance of every cell of the grid, to draw it over the plan
    point_step_m: float = Field(0.5, gt=0, le=5)
    default_height_m: float = Field(2.6, gt=0, le=60)                    # for a room whose height was not given


class CalcIn(Strict):
    sheet: Sheet
    rooms: Dict[str, RoomParams] = {}                                    # by room id
    options: CalcOptions = CalcOptions()
    lang: Literal["es", "en"] = "en"


class CompareIn(CalcIn):
    """The calculation of one room with each luminaire of the catalogue in turn."""
    room: str = Field(min_length=1, max_length=64)


class LuminairesIn(BaseModel):
    """The changes a level makes to the catalogue of luminaires: entries by id, or `{"disabled": true}` to remove one of a level below."""
    luminaires: Dict[str, Dict[str, Any]] = Field(max_length=200)
