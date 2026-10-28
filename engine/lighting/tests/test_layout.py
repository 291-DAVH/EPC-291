import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE))

from epc_lighting import layout, run  # noqa: E402
from epc_lighting.model import Options  # noqa: E402
import helpers  # noqa: E402


class TestGridCounts(unittest.TestCase):
    def test_article_cases(self):
        self.assertEqual(layout.grid_counts(2, 4, 6), (1, 2))
        self.assertEqual(layout.grid_counts(5, 10, 6), (3, 2))

    def test_one_luminaire_is_one_by_one(self):
        self.assertEqual(layout.grid_counts(1, 4, 6), (1, 1))

    def test_the_grid_always_holds_at_least_n(self):
        for n in range(1, 40):
            for a, b in ((4, 6), (10, 6), (3, 20), (12, 12)):
                rows, cols = layout.grid_counts(n, a, b)
                self.assertGreaterEqual(rows * cols, n, (n, a, b))

    def test_when_rounding_falls_short_the_cheapest_grid_is_taken(self):
        self.assertEqual(layout.grid_counts(7, 4, 6), (2, 4))

    def test_a_long_narrow_room_gets_a_single_line(self):
        self.assertEqual(layout.grid_counts(4, 2, 40)[0], 1)


class TestSpacingRatio(unittest.TestCase):
    def _ratio(self, height, options=Options(), **lum):
        proj = helpers.project([helpers.room_dict(height_m=height)], [helpers.luminaire_dict(**lum)])
        return layout.spacing_ratio(proj.rooms[0], proj.luminaires["L1"], options)

    def test_by_room_height_follows_table_7(self):
        self.assertEqual([self._ratio(h).value for h in (2.6, 4.0, 4.5, 6.0, 8.0, 12.0)], [1.6, 1.6, 1.5, 1.5, 1.5, 1.2])

    def test_the_luminaire_declared_ratio_wins(self):
        est = self._ratio(2.6, spacing_ratio=1.1)
        self.assertEqual((est.value, est.confidence), (1.1, 1.0))

    def test_by_distribution_uses_the_lighting_system(self):
        est = self._ratio(2.6, Options(spacing_basis="distribution"))
        self.assertEqual(est.value, 1.2)  # direct lighting, UNAC 2.6

    def test_a_system_without_a_ratio_falls_back_to_the_height_table(self):
        est = self._ratio(2.6, Options(spacing_basis="distribution"), distribution="general_diffuse")
        self.assertEqual(est.value, 1.6)


class TestSpacingCheck(unittest.TestCase):
    def test_statuses(self):
        self.assertEqual(layout.check_axis(2, 5.0, 1.75, 1.6)["status"], "ok")
        self.assertEqual(layout.check_axis(2, 6.0, 1.75, 1.6)["status"], "within_tolerance")
        self.assertEqual(layout.check_axis(2, 8.0, 1.75, 1.6)["status"], "exceeds")

    def test_a_single_luminaire_on_an_axis_is_not_checked(self):
        self.assertFalse(layout.check_axis(1, 4.0, 1.75, 1.6)["checked"])


class TestPlan(unittest.TestCase):
    def _room(self, **kw):
        return run(helpers.document([helpers.room_dict(**kw)]), kw.pop("options", Options()))

    def test_a_long_room_warns_about_spacing(self):
        result = run(helpers.document([helpers.room_dict(length_m=12, target_lux=100)]))
        self.assertTrue(any("exceeds the maximum" in w for w in result.warnings))

    def test_enforce_spacing_adds_columns_until_it_is_respected(self):
        doc = helpers.document([helpers.room_dict(length_m=12, target_lux=100)])
        loose = run(doc).as_dict()["rooms"][0]["layout"]
        tight = run(doc, Options(enforce_spacing=True)).as_dict()["rooms"][0]["layout"]
        self.assertGreater(tight["installed"], loose["installed"])
        self.assertNotEqual(tight["spacing_check"]["along_length"]["status"], "exceeds")

    def test_positions_are_centred_in_their_cells_and_tags_are_correlative(self):
        doc = helpers.document([helpers.room_dict(id="A"), helpers.room_dict(id="B")])
        rooms = run(doc).as_dict()["rooms"]
        tags = [p["tag"] for r in rooms for p in r["layout"]["positions"]]
        self.assertEqual(tags, ["LU-001", "LU-002", "LU-003", "LU-004"])
        self.assertEqual(rooms[0]["layout"]["positions"][0]["z_m"], 2.6)

    def test_a_suspended_luminaire_sits_lower(self):
        lay = run(helpers.document([helpers.room_dict(suspension_m=0.5)])).as_dict()["rooms"][0]["layout"]
        self.assertEqual(lay["positions"][0]["z_m"], 2.1)


if __name__ == "__main__":
    unittest.main()
