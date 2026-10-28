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


class Sheet(Strict):
    scale: Optional[Scale] = None
    rooms: List[PlanRoom] = Field([], max_length=500)


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
    emergency_luminaire: str = Field("", max_length=64)                    # an interior luminaire for the antipanic emergency lighting of the room: the grid that keeps the minimum illuminance on the floor
    emergency_e_min_lux: Optional[float] = Field(None, gt=0, le=1000)
    ugr_calculated: Optional[float] = Field(None, ge=0, le=100)           # the UGR of the room calculated outside: it is compared with the limit of the activity


class CalcOptions(Strict):
    enforce_spacing: bool = False
    spacing_basis: Literal["height", "distribution"] = "height"
    compute_points: bool = True
    map: bool = False                                                    # also give the illuminance of every cell of the grid, to draw it over the plan
    point_step_m: float = Field(0.5, gt=0, le=5)
    default_height_m: float = Field(2.6, gt=0, le=60)                    # for a room whose height was not given


class CalcIn(Strict):
    sheet: Sheet
    rooms: Dict[str, RoomParams] = {}                                    # by room id
    options: CalcOptions = CalcOptions()
    lang: Literal["es", "en"] = "en"


class LuminairesIn(BaseModel):
    """The changes a level makes to the catalogue of luminaires: entries by id, or `{"disabled": true}` to remove one of a level below."""
    luminaires: Dict[str, Dict[str, Any]] = Field(max_length=200)
