from typing import List

from pydantic import BaseModel


class ActivityIn(BaseModel):
    id: str
    name: str
    start: str                       # ISO date
    end: str                         # ISO date, >= start
    wbs_id: str = ""
    depends_on: List[str] = []       # finish-to-start predecessors
    milestone: bool = False
    progress: float = 0


class ScheduleIn(BaseModel):
    activities: List[ActivityIn]
