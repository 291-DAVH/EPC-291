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
