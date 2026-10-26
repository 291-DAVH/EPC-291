"""The project-management methodology of a project; its registers and report catalog are data under `management/methodologies/<id>`."""
from typing import Optional

DEFAULT = "pm2"


def of(meta: Optional[dict]) -> str:
    """The methodology id written in the project's metadata, PM² when none."""
    return (meta or {}).get("methodology") or DEFAULT
