"""Which thickness is the wall's: a filled wall has thick outlines, and the thickness is the distance between them, not the width of the stroke."""
import sys
import tempfile
import unittest
from pathlib import Path

import ezdxf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE))

from epc_arch import recognize                                             # noqa: E402
import helpers                                                             # noqa: E402


def _flat(stroke: float) -> bytes:
    """The flat of the helpers with each face of each wall drawn as a polyline of width `stroke` (how a filled wall is outlined)."""
    doc = ezdxf.new("R2010")
    doc.units = 6
    msp = doc.modelspace()
    for a, b in helpers.room_lines():
        msp.add_lwpolyline([a, b], dxfattribs={"const_width": stroke})
    for a, b in helpers.window_lines():
        msp.add_line(a, b)
    (cx, cy), r, a0, a1 = helpers.door_arc()
    msp.add_arc((cx, cy), r, a0, a1)
    a, b = helpers.door_leaf()
    msp.add_line(a, b)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "t.dxf"
        doc.saveas(str(path))
        return path.read_bytes()


class TestWallThickness(unittest.TestCase):
    def test_the_outlines_of_filled_walls_do_not_set_the_thickness(self):
        a = recognize(_flat(0.06), "flat.dxf").architecture                  # strokes 6 cm wide, faces 20 cm apart
        self.assertAlmostEqual(a.wall_thickness / a.units_per_metre, helpers.T, delta=0.03)
        self.assertEqual(a.counts()["doors"], 1)

    def test_a_wall_drawn_as_a_thick_band_is_still_a_band(self):
        doc = ezdxf.new("R2010")
        doc.units = 6
        msp = doc.modelspace()
        for a, b in (((0, 0.1), (6, 0.1)), ((0, 3.9), (6, 3.9)), ((0.1, 0), (0.1, 4)), ((5.9, 0), (5.9, 4))):
            msp.add_lwpolyline([a, b], dxfattribs={"const_width": 0.2})
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.dxf"
            doc.saveas(str(path))
            a = recognize(path.read_bytes(), "bands.dxf").architecture
        self.assertAlmostEqual(a.wall_thickness / a.units_per_metre, 0.2, delta=0.03)


if __name__ == "__main__":
    unittest.main()
