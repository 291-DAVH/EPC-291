"""epc_receptacles: how many socket outlets a room needs, where they go and whether their mounting height complies. See README.md."""
from epc_receptacles.config import VERSION as __version__
from epc_receptacles.model import Options, ReceptaclesError, Result
from epc_receptacles.pipeline import run

__all__ = ["run", "Options", "Result", "ReceptaclesError", "__version__"]
