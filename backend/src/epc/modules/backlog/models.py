from typing import Optional

from pydantic import BaseModel


class NewItem(BaseModel):
    title: str
    type: str = "task"
    priority: str = "P2"
    estimate_h: float = 0
    wbs_id: str = ""
    requirement_id: str = ""
    owner: str = ""


class ItemPatch(BaseModel):
    title: Optional[str] = None
    type: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    estimate_h: Optional[float] = None
    wbs_id: Optional[str] = None
    requirement_id: Optional[str] = None
    owner: Optional[str] = None
