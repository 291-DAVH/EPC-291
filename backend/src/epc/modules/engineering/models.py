from typing import Any

from pydantic import BaseModel


class CriterionIn(BaseModel):
    value: Any
    source: str = "project"          # client | standard | project
    note: str = ""
