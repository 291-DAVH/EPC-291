"""What the receptacles calculation is asked: the rooms of a sheet (as the editor has them, in view units, like the lighting calculation), what each room is for and the options."""
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field

from epc.modules.lighting import public as lighting

Strict, Sheet = lighting.models.Strict, lighting.models.Sheet


class RoomParams(Strict):
    """What the engine needs to know about a room that the plan does not say: what it is for, which outlet, how many (when the person fixes it) and the mounting height.
    Everything left out is estimated by the engine, which says why and how sure it is."""
    use: str = Field("", max_length=40)
    receptacle: str = Field("", max_length=64)
    count: Optional[int] = Field(None, ge=0, le=500)
    height_m: Optional[float] = Field(None, ge=0, le=5)                    # of the lower edge of the box above the floor
    norm: Optional[Literal["771", "770"]] = None                           # the section of AEA 90364 whose mounting heights are checked (the options' when left out)
    wet: Optional[bool] = None                                             # cleaned by washing or with water nearby (the use says it when left out)


class CalcOptions(Strict):
    use_drawn: bool = False                                                # check each room with the outlets drawn in it, not with the layout the engine would arrange
    norm: Literal["771", "770"] = "771"


class CalcIn(Strict):
    sheet: Sheet
    rooms: Dict[str, RoomParams] = {}                                      # by room id
    options: CalcOptions = CalcOptions()
    lang: Literal["es", "en"] = "en"


class ReceptaclesIn(BaseModel):
    """The changes a level makes to the catalogue of outlets: entries by id, or `{"disabled": true}` to remove one of a level below."""
    receptacles: Dict[str, Dict[str, Any]] = Field(max_length=200)


PlanRoomAlias = lighting.models.PlanRoom
