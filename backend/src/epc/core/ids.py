"""Sequential record ids such as `BL-007`, `ENT-012`, `RIE-003`."""
from typing import Iterable, Optional


def max_seq(items: Iterable[dict], prefix: Optional[str] = None) -> int:
    """The highest number among the ids `PREFIX-nnn` (0 when there are none). With a prefix, ids that do not start with it are ignored."""
    return max((int(i["id"].split("-")[1]) for i in items if prefix is None or str(i.get("id", "")).startswith(prefix)), default=0)
