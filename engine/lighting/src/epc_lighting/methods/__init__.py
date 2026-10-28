"""Registry of flux methods (Strategy). A new method is a new module and nothing else changes.

A method is a function (room, luminaire, context) -> FluxPlan: it says how much
flux the room needs and which coefficient of utilisation it used.
"""
from typing import Callable, Dict, List

from epc_lighting.model import Context, FluxPlan, LightingError, Luminaire, Room

Method = Callable[[Room, Luminaire, Context], FluxPlan]

REGISTRY: Dict[str, Method] = {}


def register(kind: str) -> Callable[[Method], Method]:
    def decorator(fn: Method) -> Method:
        REGISTRY[kind] = fn
        return fn

    return decorator


def names() -> List[str]:
    return sorted(REGISTRY)


def get(kind: str) -> Method:
    if kind not in REGISTRY:
        raise LightingError(f"method '{kind}' is not available: choose one of {names()}")
    return REGISTRY[kind]


from epc_lighting.methods import lumen, zonal  # noqa: E402,F401  (importing registers them)
