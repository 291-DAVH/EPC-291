"""What a board may contain: the allowed values and the checks of a board and its circuits."""

import re
from typing import Dict

from epc.modules.sld import lengths, repository


UNITS = ("A", "W", "kW", "MW", "VA", "kVA", "MVA", "HP")


TOPOLOGIES = ("single", "dol", "dol_ol", "star_delta", "softstarter", "vfd", "dol_rcd", "manual")


PHASES = ("3F", "1F", "3F+N")


KINDS = ("auto", "mcb", "mccb", "mccb_motorized", "rcbo", "rccb")


CABLE_TYPES = ("tetra_sep", "tetra_inc", "unifilar")
LENGTH_SOURCES = lengths.SOURCES


SYSTEMS = ("TN-S", "TN-C-S", "IT")


OPTIONS = {"units": UNITS, "topologies": TOPOLOGIES, "phases": PHASES, "kinds": KINDS, "cable_types": CABLE_TYPES, "systems": SYSTEMS, "length_sources": LENGTH_SOURCES}


def options() -> dict:
    return {**OPTIONS, "route_kinds": repository.route_kinds()}


MAX_CIRCUITS = 150


def _validate_board(b: dict, e: Dict[str, str]) -> None:
    if not b["name"].strip():
        e["board.name"] = "required"
    if not 50 <= b["voltage_v"] <= 1000:
        e["board.voltage_v"] = "between 50 and 1000 V"
    if b["system"] not in SYSTEMS:
        e["board.system"] = "one of " + ", ".join(SYSTEMS)
    if not 0.1 <= b["icc_ka"] <= 100:
        e["board.icc_ka"] = "between 0.1 and 100 kA"
    if not 0.1 <= b["fp_default"] <= 1:
        e["board.fp_default"] = "between 0.1 and 1"
    if b["frequency_hz"] not in (50, 60):
        e["board.frequency_hz"] = "50 or 60"
    if b["feeder_length_m"] < 0:
        e["board.feeder_length_m"] = "must be >= 0"


def _validate_circuit(i: int, c: dict, tags: list, parents: set, e: Dict[str, str]) -> None:
    t = c["tag"].strip()
    k = f"circuit:{t or i + 1}"
    if not t or "," in t:
        e[f"{k}.tag"] = "required, without commas"
    elif tags.count(t) > 1:
        e[f"{k}.tag"] = "duplicated"
    for field, allowed, message in (("unit", UNITS, "one of " + ", ".join(UNITS)), ("topology", TOPOLOGIES, "invalid"),
                                    ("phase", PHASES, "one of " + ", ".join(PHASES)), ("kind", KINDS, "invalid"), ("cable_type", CABLE_TYPES, "invalid"),
                                    ("length_source", LENGTH_SOURCES, "one of " + ", ".join(LENGTH_SOURCES))):
        if c[field] not in allowed:
            e[f"{k}.{field}"] = message
    if c["load"] is None and t not in parents:
        e[f"{k}.load"] = "required (a parent device may leave it empty)"
    if c["load"] is not None and c["load"] <= 0:
        e[f"{k}.load"] = "must be > 0"
    if c["length_m"] < 0:
        e[f"{k}.length_m"] = "must be >= 0"
    for fld, msg in repository.route_errors(c.get("route") or []).items():
        e[f"{k}.route.{fld}"] = msg
    for fld in ("fp", "efficiency"):
        if c[fld] is not None and not 0 < c[fld] <= 1:
            e[f"{k}.{fld}"] = "between 0 and 1"
    p = c["parent_tag"].strip()
    if p and (p == t or p not in tags):
        e[f"{k}.parent_tag"] = "unknown or self parent"


def _validate_parent_cycles(cs: list, e: Dict[str, str]) -> None:
    par = {c["tag"].strip(): c["parent_tag"].strip() for c in cs}
    for t in par:
        seen, cur = set(), t
        while cur and cur in par:
            if cur in seen:
                e["circuits"] = f"parent cycle at {t}"
                break
            seen.add(cur)
            cur = par[cur]


def validate(data: dict) -> Dict[str, str]:
    e: Dict[str, str] = {}
    _validate_board(data["board"], e)
    cs = data["circuits"]
    if not cs:
        e["circuits"] = "at least one circuit"
    if len(cs) > MAX_CIRCUITS:
        e["circuits"] = f"up to {MAX_CIRCUITS} circuits"
    tags = [c["tag"].strip() for c in cs]
    parents = {c["parent_tag"].strip() for c in cs if c["parent_tag"].strip()}
    for i, c in enumerate(cs):
        _validate_circuit(i, c, tags, parents, e)
    if not e:                                                         # cycles
        _validate_parent_cycles(cs, e)
    return e


def _name(board_name: str) -> str:
    """Base name of the outputs: SLD_<base>.*, MLD_<base>.* and <base>_dimensionado*.json."""
    return re.sub(r"[^A-Za-z0-9]+", "-", board_name).strip("-")[:30] or "TABLERO"
