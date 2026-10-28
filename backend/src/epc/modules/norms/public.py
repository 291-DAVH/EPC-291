"""Public interface of the norms module."""
from typing import List, Optional

from epc.modules.norms import service


def review_summary() -> List[dict]:
    """Per norm (and per table set and criteria catalog): total, approved, rejected, pending and stale points."""
    return service.units()


def lighting_rule(rule_id: str) -> Optional[dict]:
    """A rule of the lighting norms with its review status, or None."""
    return service.lighting_rule(rule_id)


def lighting_rules() -> List[dict]:
    """The rules of the lighting norms that give a level in lux, each with its review status."""
    return service.lighting_rules()


__all__ = ["review_summary", "lighting_rule", "lighting_rules"]
