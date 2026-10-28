"""Access to normative data (rules/ and standards/).

Only rules whose ``review`` is ``"approved"`` are returned unless
``include_pending`` is true: a value read from a norm must have been checked by a
person first. A room can take its target from an approved rule (`target_rule` in the document): see `illuminance_rule`.
"""
from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources
from pathlib import Path

from .model import LightingError

_PACKAGE = "epc_lighting"
RULES_DIR = Path(__file__).resolve().parent / "rules"          # where a reviewer's correction is written (the reading above also works from a zip)


def _read(folder: str, name: str) -> dict:
    try:
        text = resources.files(_PACKAGE).joinpath(folder, name).read_text("utf-8")
    except FileNotFoundError as exc:
        raise LightingError(f"unknown norm file {folder}/{name}") from exc
    return json.loads(text)


@lru_cache(maxsize=None)
def standard(norm_id: str) -> dict:
    """Metadata of a norm (title, jurisdiction, edition, review status)."""
    return _read("standards", f"{norm_id}.json")


@lru_cache(maxsize=None)
def _rules(norm_id: str) -> tuple:
    return tuple(_read("rules", f"{norm_id}.rules.json")["rules"])


def norms() -> list[str]:
    """Ids of the norms whose rules ship with the engine."""
    folder = resources.files(_PACKAGE).joinpath("rules")
    return sorted(p.name[: -len(".rules.json")] for p in folder.iterdir() if p.name.endswith(".rules.json"))


def clear_cache() -> None:
    """Read the rule files again (after a reviewer corrected or approved a rule)."""
    _rules.cache_clear()


def rules(norm_id: str, include_pending: bool = False) -> list[dict]:
    """Rules of a norm; by default only the approved ones."""
    found = [r for r in _rules(norm_id) if include_pending or r.get("review") == "approved"]
    return [dict(r) for r in found]


def rule(norm_id: str, rule_id: str, include_pending: bool = False) -> dict:
    """One rule by id; raises ``LightingError`` if absent or not approved."""
    for item in rules(norm_id, include_pending):
        if item["id"] == rule_id:
            return item
    raise LightingError(f"rule {rule_id} of {norm_id} not found or not approved")


def illuminance_rule(rule_id: str) -> dict:
    """An approved rule that gives a maintained illuminance in lux, from whichever norm holds it. Raises ``LightingError`` with what to do when it does not exist, is not approved or is not a level in lux."""
    for norm_id in norms():
        for item in _rules(norm_id):
            if item["id"] != rule_id:
                continue
            if item.get("review") != "approved":
                raise LightingError(f"rule {rule_id} of {norm_id} is not approved: approve it in the norms review, or give 'target_lux'")
            if item.get("unit") != "lx" or not isinstance(item.get("value"), (int, float)) or isinstance(item.get("value"), bool) or item["value"] <= 0:
                raise LightingError(f"rule {rule_id} of {norm_id} is not an illuminance level in lux: choose a rule that is, or give 'target_lux'")
            return {**item, "norm": norm_id}
    raise LightingError(f"rule {rule_id} is not in any norm of the engine ({', '.join(norms())})")
