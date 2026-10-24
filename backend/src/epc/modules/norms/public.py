"""Public interface of the norms module."""
from typing import List

from epc.modules.norms import service


def review_summary() -> List[dict]:
    """Per norm (and per table set and criteria catalog): total, approved, rejected, pending and stale points."""
    return service.units()


__all__ = ["review_summary"]
