"""DXF -> PDF rendering: valid PDF whose page has the size of the drawing (mm)."""
import tempfile
import unittest
from pathlib import Path

import ezdxf


class TestPdfExport(unittest.TestCase):
    def test_page_follows_the_drawing_extents(self):
        from epc_drawing.export.pdf import dxf_to_pdf
        with tempfile.TemporaryDirectory() as tmp:
            src, dst = Path(tmp) / "d.dxf", Path(tmp) / "d.pdf"
            doc = ezdxf.new("R2010")
            msp = doc.modelspace()
            msp.add_lwpolyline([(0, 0), (420, 0), (420, 297), (0, 297)], close=True)
            msp.add_text("TEST", dxfattribs={"height": 8}).set_placement((20, 20))
            doc.saveas(src)
            dxf_to_pdf(src, dst)
            raw = dst.read_bytes()
            self.assertTrue(raw.startswith(b"%PDF"))
            import pypdfium2 as pdfium
            w, h = pdfium.PdfDocument(str(dst))[0].get_size()
            self.assertAlmostEqual(w / 72 * 25.4, 420, delta=3)         # A3 landscape, in mm
            self.assertAlmostEqual(h / 72 * 25.4, 297, delta=3)


if __name__ == "__main__":
    unittest.main()
