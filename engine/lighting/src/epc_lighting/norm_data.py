"""Access to normative data (rules/ and standards/).

Only rules whose ``review`` is ``"approved"`` are returned unless
``include_pending`` is true: a value read from a norm must have been checked by a
person first. The pipeline does not use this module yet.
"""
from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources

from .model import LightingError

_PACKAGE = "epc_lighting"


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
