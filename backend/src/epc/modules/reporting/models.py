from typing import Optional

from pydantic import BaseModel


class GenerateIn(BaseModel):
    type: str                               # id from the methodology catalog (status, progress, risks, effort, changes)
    period_start: Optional[str] = None      # ISO date; default: the day after the previous report of the same type, else the project start
    period_end: Optional[str] = None        # ISO date; default: today
    lang: Optional[str] = None              # es | en; default: the project's language
