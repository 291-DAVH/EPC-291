"""The geometry between the plan editor and the lighting engine: scale, rectangles, and the round trip of a position."""
import unittest

from epc.modules.lighting import geometry
from epc.modules.lighting.models import Scale

SCALE = Scale(p1=[0, 0], p2=[100, 0], distance_m=10)             # one unit of the view is 0.1 m


class TestScale(unittest.TestCase):
    def test_metres_per_unit_comes_from_the_two_points_whatever_their_direction(self):
        self.assertAlmostEqual(geometry.metres_per_unit(SCALE), 0.1)
        self.assertAlmostEqual(geometry.metres_per_unit(Scale(p1=[0, 0], p2=[30, 40], distance_m=5)), 0.1)      # a diagonal: 50 units for 5 m

    def test_no_scale_or_a_scale_of_one_point_is_refused_with_the_reason(self):
        with self.assertRaisesRegex(geometry.GeometryError, "no scale"):
            geometry.metres_per_unit(None)
        with self.assertRaisesRegex(geometry.GeometryError, "same point"):
            geometry.metres_per_unit(Scale(p1=[5, 5], p2=[5, 5], distance_m=1))


class TestRectangle(unittest.TestCase):
    def test_a_rectangle_along_the_axes_is_exact_in_any_vertex_order_or_orientation(self):
        for points in ([[10, 20], [70, 20], [70, 60], [10, 60]], [[70, 60], [10, 60], [10, 20], [70, 20]], [[10, 20], [40, 20], [70, 20], [70, 60], [10, 60]]):
            rect = geometry.rectangle(points)
            self.assertTrue(rect.exact)
            self.assertEqual((rect.x0, rect.y0, rect.x1, rect.y1), (10, 20, 70, 60))

    def test_an_l_shape_or_a_rotated_room_is_not_exact_but_still_has_its_bounding_box(self):
        l_shape = geometry.rectangle([[0, 0], [60, 0], [60, 20], [20, 20], [20, 40], [0, 40]])
        self.assertFalse(l_shape.exact)
        self.assertEqual((l_shape.width_u, l_shape.height_u), (60, 40))
        rotated = geometry.rectangle([[20, 0], [40, 20], [20, 40], [0, 20]])
        self.assertFalse(rotated.exact)

    def test_a_polygon_without_area_is_refused(self):
        with self.assertRaisesRegex(geometry.GeometryError, "no area"):
            geometry.rectangle([[0, 0], [10, 0], [20, 0]])

    def test_a_small_wobble_in_the_drawing_is_still_a_rectangle(self):
        self.assertTrue(geometry.rectangle([[0, 0], [100, 0.3], [100, 60], [0, 60]]).exact)


class TestAcross(unittest.TestCase):
    def test_the_engine_gets_the_extent_along_x_as_length_and_along_y_as_width_in_metres(self):
        rect = geometry.rectangle([[0, 0], [60, 0], [60, 40], [0, 40]])
        self.assertEqual(geometry.to_engine(rect, 0.1), (6.0, 4.0))

    def test_a_position_of_the_engine_comes_back_to_the_view_from_the_corner_of_the_room(self):
        rect = geometry.rectangle([[100, 50], [160, 50], [160, 90], [100, 90]])
        x, y = geometry.to_view(rect, 0.1, 1.5, 2.0)
        self.assertEqual((x, y), (115.0, 70.0))
        self.assertTrue(rect.x0 <= x <= rect.x1 and rect.y0 <= y <= rect.y1)

    def test_the_round_trip_loses_nothing_that_matters(self):
        rect = geometry.rectangle([[0, 0], [123.4, 0], [123.4, 77.7], [0, 77.7]])
        k = 0.0371
        length, width = geometry.to_engine(rect, k)
        x, y = geometry.to_view(rect, k, length, width)             # the far corner of the room
        self.assertAlmostEqual(x, rect.x1, delta=0.05)
        self.assertAlmostEqual(y, rect.y1, delta=0.05)


if __name__ == "__main__":
    unittest.main()
