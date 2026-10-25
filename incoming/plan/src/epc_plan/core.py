"""The work of the module as pure functions: the same input gives the same output; nothing here reads the network, the environment or the backend."""
import json
from pathlib import Path
from typing import Any, Dict

PARAMS = json.loads((Path(__file__).with_name("params.json")).read_text(encoding="utf-8"))


def process(document: Dict[str, Any], params: Dict[str, Any] = PARAMS) -> Dict[str, Any]:
    """Replace this body. Takes the input document (see schema/input.schema.json) and returns the output document (schema/output.schema.json)."""
    return {"schema_version": "1.0", "items": len(document.get("items", [])), "warnings": []}
