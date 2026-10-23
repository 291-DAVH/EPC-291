from typing import List

from pydantic import BaseModel


class WbsNodeIn(BaseModel):
    id: str
    name: str
    discipline: str = ""
    deliverable_id: str = ""
    owner: str = ""
    weight: float = 1
    progress: float = 0          # only leaves carry progress; parents are rolled up


class WbsIn(BaseModel):
    nodes: List[WbsNodeIn]
