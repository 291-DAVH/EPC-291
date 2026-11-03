"""How the plan is drawn: every line is the same fine line (0.05 mm of paper), and a wall is a rectangle of its real thickness filled with colour."""
import re
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE))

from epc_arch import recognize                                             # noqa: E402
from epc_arch.config import PARAMS                                         # noqa: E402
import helpers                                                             # noqa: E402
from test_annotations import _flat_with_notes                              # noqa: E402


class TestRender(unittest.TestCase):
    def setUp(self):
        self.r = recognize(_flat_with_notes(), "flat.dxf")
        self.a = self.r.architecture

    def test_every_line_has_the_width_of_005_mm_of_paper(self):
        widths = {float(w) for w in re.findall(r'stroke-width="([^"]+)"', self.r.svg)}
        expected = PARAMS["render"]["line_mm"] / 1000.0 * PARAMS["render"]["default_scale"] * self.a.units_per_metre      # no scale written: 1:100
        self.assertEqual(len(widths), 1)
        self.assertAlmostEqual(widths.pop(), expected, delta=0.01)

    def test_a_wall_is_a_filled_rectangle_of_its_real_thickness(self):
        polygons = re.findall(r'<polygon id="w\d+"[^>]*points="([^"]+)"[^>]*fill="([^"]+)"', self.r.svg)
        self.assertEqual(len(polygons), len(self.a.walls))
        for points, fill in polygons:
            self.assertEqual(fill, PARAMS["render"]["wall_fill"])
            xs = sorted({round(float(p.split(",")[0]), 1) for p in points.split()})
            ys = sorted({round(float(p.split(",")[1]), 1) for p in points.split()})
            self.assertAlmostEqual(min(xs[-1] - xs[0], ys[-1] - ys[0]), self.a.wall_thickness, delta=0.2)      # the short side of the rectangle is the thickness: no outline adds to it

    def test_the_scale_the_sheet_says_sets_the_width(self):
        self.a.drawing_scale = 50
        from epc_arch import svgout
        self.assertAlmostEqual(svgout.hairline(self.a), 0.00005 * 50 * self.a.units_per_metre, places=6)


if __name__ == "__main__":
    unittest.main()
