"""epc_lighting: luminaire count, distribution and point illuminance for interior rooms and exterior areas. See README.md."""
from epc_lighting.config import VERSION as __version__
from epc_lighting.model import LightingError, Options, Result
from epc_lighting.pipeline import run

__all__ = ["run", "Options", "Result", "LightingError", "__version__"]
