"""Small synthetic documents for the tests: one place, so every test builds rooms the same way."""
import copy
from typing import Any, Dict, List, Optional

from epc_lighting.document import parse_project

# The luminaire of the UPV lumen-method article: 2 lamps of 2400 lm each.
DOWNLIGHT: Dict[str, Any] = {
    "id": "L1",
    "name": "Downlight 2 x 2400 lm",
    "lamps": 2,
    "lamp_flux_lm": 2400,
    "power_w": 64,
    "photometry": {"gamma_deg": [0, 25.64, 60, 90], "intensity_cd_per_klm": [600, 525, 150, 0]},
}

FLOODLIGHT: Dict[str, Any] = {"id": "F1", "lamps": 1, "lamp_flux_lm": 36000}

# The classroom of the article: 4 x 6 x 2.6 m, 300 lux, CU as printed there (0.97).
CLASSROOM: Dict[str, Any] = {
    "id": "R1",
    "width_m": 4,
    "length_m": 6,
    "height_m": 2.6,
    "target_lux": 300,
    "luminaire": "L1",
    "coefficient_of_utilisation": 0.97,
}


def document(rooms: Optional[List[Dict[str, Any]]] = None, luminaires: Optional[List[Dict[str, Any]]] = None, areas: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """A fresh document (deep copies, so a test can edit what it gets)."""
    return {
        "schema_version": "1.0",
        "luminaires": copy.deepcopy(luminaires if luminaires is not None else [DOWNLIGHT, FLOODLIGHT]),
        "rooms": copy.deepcopy(rooms if rooms is not None else [CLASSROOM]),
        "areas": copy.deepcopy(areas if areas is not None else []),
    }


def room_dict(**changes: Any) -> Dict[str, Any]:
    room = copy.deepcopy(CLASSROOM)
    room.update(changes)
    return room


def luminaire_dict(**changes: Any) -> Dict[str, Any]:
    lum = copy.deepcopy(DOWNLIGHT)
    lum.update(changes)
    return lum


def project(rooms: Optional[List[Dict[str, Any]]] = None, luminaires: Optional[List[Dict[str, Any]]] = None):
    return parse_project(document(rooms, luminaires))


def first_room(**changes: Any):
    """(room, luminaire) objects parsed from the article classroom with the changes applied."""
    proj = project([room_dict(**changes)])
    room = proj.rooms[0]
    return room, proj.luminaires[room.luminaire_id]
