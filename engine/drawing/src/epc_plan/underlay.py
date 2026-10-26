"""The plan the person uploads is only an underlay: here a DXF is turned into an SVG view for the screen. That SVG is never a deliverable."""
import tempfile
from pathlib import Path

import ezdxf
from ezdxf.addons.drawing import Frontend, RenderContext, layout, svg
from ezdxf.addons.drawing.config import BackgroundPolicy, ColorPolicy, Configuration


def dxf_to_svg(data: bytes) -> str:
    """The modelspace of a DXF as an SVG (for display only). Raises ValueError with a clear message when the file cannot be read."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "underlay.dxf"
        path.write_bytes(data)
        try:
            doc = ezdxf.readfile(str(path))
        except (ezdxf.DXFError, OSError, UnicodeDecodeError):
            raise ValueError("the DXF cannot be read: it is not a valid DXF file")
        backend = svg.SVGBackend()
        Frontend(RenderContext(doc), backend, config=Configuration(color_policy=ColorPolicy.BLACK, background_policy=BackgroundPolicy.WHITE)).draw_layout(doc.modelspace())
        return backend.get_string(layout.Page(0, 0))
