from typing import List, Optional

from pydantic import BaseModel


class NewProject(BaseModel):
    client_name: str
    client_code: str
    project_code: str
    project_name: str = ""
    jurisdiction: str = "AR"
    methodology: str = "pm2"
    locale: Optional[str] = None
    disciplines: List[str] = ["electrical"]
    phase: str = "IC"
    end_phase: str = "ASB"           # the last phase this project goes through (it may end at basic, detail or execution engineering, with no as-built)
    org: str = ""                    # staff only: organization (slug) that owns the project; customers always create in their own
