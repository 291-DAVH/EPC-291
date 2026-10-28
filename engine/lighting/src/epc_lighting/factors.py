"""The two factors every calculation needs besides geometry: the target level and the maintenance factor."""
from typing import Any, Dict, List, Optional, Tuple

from epc_lighting import norm_data
from epc_lighting.config import data
from epc_lighting.model import Estimate


def resolve_target(item: Any, warnings: List[str]) -> Tuple[Estimate, Dict[str, Any]]:
    """The maintained illuminance to reach, and the quality figures of the activity when known.

    An explicit target_lux wins over the activity; the activity still reports its glare and colour limits.
    """
    activity = _activity(item.activity) if item.activity else None
    extras: Dict[str, Any] = {}
    if activity:
        extras = {"activity": activity["id"], "ugr_l_max": activity["ugr_l"], "ra_min": activity["ra"]}
    if item.target_lux is None and item.target_rule:
        rule = norm_data.illuminance_rule(item.target_rule)
        return Estimate(rule["value"], f"rule {rule['id']} of {rule['norm']} ({rule['clause']}), approved in the norms review", 1.0), {**extras, "norm_rule": rule["id"], "norm": rule["norm"], "clause": rule["clause"]}
    if item.target_lux is not None:
        reason = "given in the document"
        if activity and activity["em_lux"] != item.target_lux:
            reason += f" (the activity '{activity['id']}' suggests {activity['em_lux']} lux)"
        return Estimate(item.target_lux, reason, 1.0), extras
    return Estimate(activity["em_lux"], f"activity '{activity['id']}': {activity['source']}", 0.9), extras


def _activity(activity_id: str) -> Dict[str, Any]:
    return next(a for a in data("levels")["activities"] if a["id"] == activity_id)


def interior_maintenance(environment: str, given: Optional[float]) -> Estimate:
    if given is not None:
        return Estimate(given, "given in the document", 1.0)
    entry = data("maintenance")["interior"][environment]
    return Estimate(entry["value"], f"{entry['label']['en']}: {entry['source']}", 0.8)


def exterior_maintenance(enclosure: str, given: Optional[float]) -> Estimate:
    if given is not None:
        return Estimate(given, "given in the document", 1.0)
    entry = data("maintenance")["exterior"][enclosure]
    return Estimate(entry["value"], f"{entry['label']['en']}: {entry['source']}", 0.8)
