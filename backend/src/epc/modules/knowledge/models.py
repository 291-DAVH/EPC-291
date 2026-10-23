from typing import Any, Dict, Optional

from pydantic import BaseModel


class CheckRequest(BaseModel):
    context: Dict[str, Any] = {}
    installation_type: Optional[str] = None
    topic: Optional[str] = None
    standard: Optional[str] = None
