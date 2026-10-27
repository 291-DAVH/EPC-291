"""epc_arch: architecture recognition (walls, doors and windows) from a DXF, a vector PDF or an image. See README.md."""
from epc_arch.model import Architecture, ArchError, Opening, Options, Wall
from epc_arch.pipeline import Result, recognize
from epc_arch.sources import kinds
from epc_arch.sources.render import pdf_to_png

__version__ = "0.1.0"
__all__ = ["recognize", "Result", "Options", "Architecture", "Wall", "Opening", "ArchError", "kinds", "pdf_to_png"]
