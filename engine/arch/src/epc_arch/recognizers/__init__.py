"""The recognizers know primitives and nothing about files: whatever the source, they look for the same things. `Context` carries what they share."""
from dataclasses import dataclass, field
from typing import Any, Dict, Tuple

from epc_arch.config import PARAMS, Hints, Scale


@dataclass(frozen=True)
class Context:
    size: Tuple[float, float]
    scale: Scale
    hints: Hints
    params: Dict[str, Any] = field(default_factory=lambda: PARAMS)
