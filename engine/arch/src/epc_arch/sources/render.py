"""A page of a PDF as an image: the one place that does it, so that the picture the person sees as the plan and the picture the raster reader reads have the same pixels."""
import io
from typing import Optional

import pypdfium2

from epc_arch.model import ArchError


def pdf_to_png(data: bytes, page: int = 0, max_side: int = 3000, max_scale: float = 2.5) -> Optional[bytes]:
    """The page as a PNG at most `max_side` pixels on its longest side, or None when the file cannot be read (damaged or protected)."""
    try:
        doc = pypdfium2.PdfDocument(data)
        pg = doc[page]
        width, height = pg.get_size()
        image = pg.render(scale=min(max_scale, max_side / max(width, height, 1))).to_pil()
        out = io.BytesIO()
        image.save(out, format="PNG")
        return out.getvalue()
    except Exception:                                         # noqa: BLE001 - a broken or protected PDF is reported by the caller as "cannot open"
        return None


def render_or_fail(data: bytes, page: int, max_side: int) -> bytes:
    png = pdf_to_png(data, page, max_side)
    if png is None:
        raise ArchError("the PDF cannot be read: it may be damaged or protected")
    return png
