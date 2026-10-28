import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE))

from epc_lighting import geometry, methods  # noqa: E402
from epc_lighting.config import data  # noqa: E402
from epc_lighting.model import LightingError  # noqa: E402
import helpers  # noqa: E402

SYSTEMS = data("lighting_systems")["systems"]


class TestRoomIndex(unittest.TestCase):
    def test_direct_formula(self):
        room, _ = helpers.first_room()
        self.assertAlmostEqual(geometry.room_index("direct", room, 1.75), 24 / (1.75 * 10))

    def test_indirect_formula_uses_the_luminaire_plane_over_the_floor(self):
        room, _ = helpers.first_room()
        self.assertAlmostEqual(geometry.room_index("indirect", room, 1.75), 3 * 24 / (2 * 2.6 * 10))

    def test_cavity_ratio_is_five_over_k_for_the_same_height(self):
        room, _ = helpers.first_room()
        k = geometry.room_index("direct", room, 1.75)
        self.assertAlmostEqual(geometry.cavity_ratio(1.75, 4, 6), 5 / k)


class TestEffectiveReflectance(unittest.TestCase):
    def test_zero_depth_is_the_base_itself(self):
        self.assertEqual(geometry.effective_reflectance(0.7, 0.5, 4, 6, 0), 0.7)

    def test_it_falls_as_the_cavity_gets_deeper(self):
        values = [geometry.effective_reflectance(0.7, 0.5, 4, 6, d) for d in (0.1, 0.5, 1.0, 3.0)]
        self.assertEqual(values, sorted(values, reverse=True))
        self.assertLess(values[-1], 0.55)

    def test_equal_base_and_walls_give_a_value_between_zero_and_that_reflectance(self):
        value = geometry.effective_reflectance(0.5, 0.5, 4, 6, 1.0)
        self.assertTrue(0 < value < 0.5)


class TestMountingHeight(unittest.TestCase):
    def test_flush_is_as_high_as_possible(self):
        room, _ = helpers.first_room()
        self.assertAlmostEqual(geometry.mounting_height(room, SYSTEMS["direct"], []).value, 1.75)

    def test_a_suspension_lowers_the_luminaires(self):
        room, _ = helpers.first_room(suspension_m=0.5)
        self.assertAlmostEqual(geometry.mounting_height(room, SYSTEMS["direct"], []).value, 1.25)

    def test_table_2_minimum_for_direct_lighting(self):
        room, _ = helpers.first_room(suspension_mode="auto_min")
        self.assertAlmostEqual(geometry.mounting_height(room, SYSTEMS["direct"], []).value, 1.75 * 2 / 3, places=6)

    def test_table_2_optimum_for_indirect_lighting(self):
        room, _ = helpers.first_room(suspension_mode="auto_optimal", lighting_system="indirect")
        self.assertAlmostEqual(geometry.mounting_height(room, SYSTEMS["indirect"], []).value, 1.75 * 0.75)

    def test_auto_mode_for_a_system_table_2_does_not_cover_is_refused_with_the_way_out(self):
        room, _ = helpers.first_room(suspension_mode="auto_min", lighting_system="semi_indirect")
        with self.assertRaisesRegex(LightingError, "give suspension_m instead"):
            geometry.mounting_height(room, SYSTEMS["semi_indirect"], [])

    def test_a_suspension_that_reaches_the_work_plane_is_refused(self):
        room, _ = helpers.first_room(suspension_m=1.9)
        with self.assertRaisesRegex(LightingError, "no height between"):
            geometry.mounting_height(room, SYSTEMS["direct"], [])

    def test_a_work_plane_above_the_ceiling_is_refused(self):
        room, _ = helpers.first_room(work_plane_height_m=3.0)
        with self.assertRaisesRegex(LightingError, "must be lower than height_m"):
            geometry.mounting_height(room, SYSTEMS["direct"], [])


class TestMethods(unittest.TestCase):
    def test_both_methods_are_registered(self):
        self.assertEqual(methods.names(), ["lumen", "zonal"])

    def test_an_unknown_method_names_the_choices(self):
        with self.assertRaisesRegex(LightingError, r"choose one of \['lumen', 'zonal'\]"):
            methods.get("point")

    def test_zonal_with_a_fixed_cu_needs_the_same_flux_as_lumen(self):
        from epc_lighting import run
        flux = {}
        for method in ("lumen", "zonal"):
            room = helpers.room_dict(method=method)
            flux[method] = run(helpers.document([room])).as_dict()["rooms"][0]["flux"]["required_lm"]
        self.assertAlmostEqual(flux["lumen"], flux["zonal"])

    def test_zonal_reports_its_cavities(self):
        from epc_lighting import run
        geo = run(helpers.document([helpers.room_dict(method="zonal", suspension_m=0.3)])).as_dict()["rooms"][0]["geometry"]
        self.assertGreater(geo["ceiling_cavity_ratio"], 0)
        self.assertLess(geo["effective_ceiling_reflectance"], 0.5)
        self.assertAlmostEqual(geo["room_cavity_ratio"], geometry.cavity_ratio(1.45, 4, 6), places=3)


if __name__ == "__main__":
    unittest.main()
