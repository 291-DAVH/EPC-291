"""Public interface of the receptacles module (the only thing other modules may import)."""
from epc.modules.receptacles.service import calc, effective, options

__all__ = ["calc", "effective", "options"]
