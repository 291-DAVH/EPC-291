"""The shapes the engine takes and gives back."""
from dataclasses import dataclass, field
from typing import Any, Dict, List

from epc_receptacles.config import VERSION

SCHEMA_VERSION = "1.0"
NORMS = ("771", "770")                       # the section of AEA 90364 that gives the mounting height: 771 offices and premises, 770 housing


class ReceptaclesError(ValueError):
    """The document cannot be used: the message says what to correct."""


@dataclass(frozen=True)
class Options:
    norm: str = "771"                        # the section whose mounting heights are checked (a room may name its own)


@dataclass
class Result:
    rooms: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {"schema_version": SCHEMA_VERSION, "engine_version": VERSION, "rooms": self.rooms, "warnings": self.warnings,
                "counts": {"rooms": len(self.rooms), "outlets": sum(r["installed"] for r in self.rooms), "required": sum(r["required"] for r in self.rooms), "warnings": len(self.warnings)}}
