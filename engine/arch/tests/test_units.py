"""The small pieces of the engine on their own: geometry, the arc fitted to a curve, the plan space, the calibration and the raster steps."""
import math
import sys
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from epc_arch import geometry as g   # noqa: E402
from epc_arch.config import Hints, scale_for   # noqa: E402
from epc_arch.model import Arc, ArchError, Line, Primitives   # noqa: E402
from epc_arch.normalize import normalize   # noqa: E402
from epc_arch.recognizers import Context   # noqa: E402
from epc_arch.recognizers.walls import Candidate, calibrate   # noqa: E402
from epc_arch.sources.pdf import arc_from_bezier   # noqa: E402
from epc_arch.sources.raster import merge_rows, otsu, prune, runs   # noqa: E402


class TestGeometry(unittest.TestCase):
    def test_directions_are_undirected_and_wrap_around(self):
        self.assertAlmostEqual(g.seg_angle((0, 0), (1, 0)), 0.0)
        self.assertAlmostEqual(g.seg_angle((1, 0), (0, 0)), 0.0)
        self.assertAlmostEqual(g.seg_angle((0, 0), (0, 1)), 90.0)
        self.assertAlmostEqual(g.angle_gap(179.0, 1.0), 2.0)

    def test_an_axis_puts_points_along_and_across(self):
        ax = g.axis_of(90.0)
        self.assertAlmostEqual(ax.t((0, 5)), 5.0)
        self.assertAlmostEqual(abs(ax.o((3, 0))), 3.0)
        p = ax.at(5.0, 3.0)
        self.assertAlmostEqual(ax.t(p), 5.0)
        self.assertAlmostEqual(ax.o(p), 3.0)

    def test_distances_to_a_segment_and_to_its_line(self):
        self.assertAlmostEqual(g.dist_point_segment((5, 3), (0, 0), (2, 0)), math.hypot(3, 3))
        self.assertAlmostEqual(g.dist_point_line((5, 3), (0, 0), (2, 0)), 3.0)

    def test_the_circle_through_three_points_and_the_span_of_an_arc(self):
        c, r = g.circle_through((1, 0), (0, 1), (-1, 0))
        self.assertAlmostEqual(r, 1.0)
        self.assertAlmostEqual(c[0], 0.0)
        self.assertIsNone(g.circle_through((0, 0), (1, 1), (2, 2)))
        self.assertAlmostEqual(g.arc_span(350.0, 10.0), 20.0)


class TestPdfArc(unittest.TestCase):
    K = 0.5522847498

    def test_a_quarter_circle_drawn_as_a_curve_is_an_arc(self):
        a = arc_from_bezier((1, 0), (1, self.K), (self.K, 1), (0, 1))
        self.assertIsNotNone(a)
        self.assertAlmostEqual(a.r, 1.0, places=2)
        self.assertAlmostEqual(g.arc_span(a.start, a.end), 90.0, delta=0.5)

    def test_any_other_curve_is_not(self):
        self.assertIsNone(arc_from_bezier((0, 0), (0, 5), (1, -5), (1, 0)))


class TestPlanSpace(unittest.TestCase):
    def test_a_vector_source_is_flipped_and_brought_to_the_standard_size(self):
        p = Primitives("dxf", lines=[Line((0, 0), (10, 0)), Line((0, 5), (10, 5))], arcs=[Arc((2, 1), 1.0, 0.0, 90.0)], y_up=True, fit=True, units_per_metre=10.0)
        out, size = normalize(p)
        self.assertAlmostEqual(size[0], 3000.0)
        self.assertAlmostEqual(out.lines[0].a[1], 1500.0)                       # the bottom line of the drawing is now at the bottom
        self.assertAlmostEqual(out.units_per_metre, 3000.0)
        self.assertAlmostEqual(g.arc_span(out.arcs[0].start, out.arcs[0].end), 90.0)
        self.assertAlmostEqual(out.arcs[0].start, 270.0)

    def test_an_image_is_left_as_it_is_and_an_empty_drawing_is_refused(self):
        p = Primitives("image", lines=[Line((1, 1), (9, 1))], extent=(100.0, 50.0))
        out, size = normalize(p)
        self.assertEqual((size, out.lines[0].a), ((100.0, 50.0), (1, 1)))
        with self.assertRaises(ArchError):
            normalize(Primitives("dxf", y_up=True, fit=True))


class TestCalibration(unittest.TestCase):
    ctx = Context(size=(3000.0, 2000.0), scale=scale_for((3000.0, 2000.0), None), hints=Hints())

    def test_the_thickness_most_candidates_agree_on_is_the_one_of_the_walls(self):
        cands = [Candidate(0, i * 100.0, 0, 500, 20.0 + (i % 3) * 0.5, 500, "pair") for i in range(8)] + [Candidate(0, 900, 0, 50, 90.0, 50, "pair")]
        self.assertAlmostEqual(calibrate(cands, self.ctx), 20.5, delta=1.0)

    def test_nothing_stands_out_without_votes(self):
        self.assertIsNone(calibrate([], self.ctx))
        self.assertIsNone(calibrate([Candidate(0, 0, 0, 500, 20.0, 500, "pair")], self.ctx))

    def test_ranges_are_real_sizes_when_the_scale_is_known(self):
        known = scale_for((3000.0, 2000.0), 500.0)
        self.assertTrue(known.known)
        self.assertAlmostEqual(known.wall_thickness[0], 25.0)
        self.assertFalse(self.ctx.scale.known)


class TestRaster(unittest.TestCase):
    def test_otsu_separates_ink_from_paper_and_runs_find_the_strokes(self):
        img = np.full((20, 40), 255, dtype=np.uint8)
        img[5:8, 2:30] = 0
        ink = img <= otsu(img)
        rows, starts, ends = runs(ink, 10)
        self.assertEqual((rows.tolist(), starts.tolist(), ends.tolist()), ([5, 6, 7], [2, 2, 2], [30, 30, 30]))
        self.assertEqual(merge_rows(rows, starts, ends, 2), [(2, 30, 5, 7)])          # three rows, one band of thickness 3

    def test_thin_strokes_inside_a_thick_band_are_its_edges_and_go(self):
        thick = Line((0, 10), (100, 10), 12.0)
        edge = Line((50, 5), (50, 15), 1.0)
        outside = Line((50, 40), (50, 60), 1.0)
        self.assertEqual(prune([thick, edge, outside]), [thick, outside])


class TestHints(unittest.TestCase):
    def test_names_of_layers_say_what_is_in_them(self):
        h = Hints()
        self.assertEqual([h.of(n) for n in ("MUROS", "A-WALL-FULL", "Puerta-1", "WINDOW", "MOBILIARIO", "")], ["wall", "wall", "door", "window", "", ""])


if __name__ == "__main__":
    unittest.main()
