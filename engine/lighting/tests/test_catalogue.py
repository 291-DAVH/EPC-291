"""The catalogue of luminaires: the factory list, the levels on top of it, validation and the conversion to the engine's document."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from epc_lighting import catalogue, run   # noqa: E402


class TestFactory(unittest.TestCase):
    def test_every_factory_luminaire_is_valid_named_in_both_languages_and_marked_illustrative(self):
        found = catalogue.defaults()
        self.assertGreaterEqual(len(found), 5)
        for lid, entry in found.items():
            self.assertEqual(catalogue.check(lid, entry), [], lid)
            self.assertTrue(entry["illustrative"], lid)                       # typical numbers, never presented as a maker's

    def test_the_interior_ones_have_an_intensity_curve_that_emits_the_lamp_flux_and_the_exterior_ones_none(self):
        from epc_lighting import photometry
        from epc_lighting.tables import parse_photometry
        for lid, entry in catalogue.defaults().items():
            if entry["kind"] == "exterior":
                self.assertNotIn("photometry", entry, lid)
                continue
            curve = parse_photometry(entry["photometry"], lid)
            self.assertAlmostEqual(photometry.emitted_fraction(curve), 1.0, delta=0.02, msg=lid)          # an analytic curve: all the flux, no loss to invent

    def test_the_factory_has_interior_and_exterior_luminaires(self):
        self.assertEqual({e["kind"] for e in catalogue.defaults().values()}, {"interior", "exterior"})

    def test_what_a_caller_changes_in_the_copy_does_not_reach_the_catalogue(self):
        catalogue.defaults()["led_panel_600"]["lamps"] = 99
        self.assertEqual(catalogue.defaults()["led_panel_600"]["lamps"], 1)


class TestLevels(unittest.TestCase):
    ENTRY = {"name": {"es": "Propia", "en": "Own"}, "kind": "interior", "lamps": 2, "lamp_flux_lm": 2500, "power_w": 40}

    def test_a_level_adds_and_replaces_by_id_and_the_later_one_wins(self):
        merged = catalogue.merge([{"mine": self.ENTRY, "led_panel_600": {**self.ENTRY, "lamps": 3}}, {"mine": {**self.ENTRY, "lamps": 4}}])
        self.assertEqual(merged["mine"]["lamps"], 4)
        self.assertEqual(merged["led_panel_600"]["lamps"], 3)
        self.assertIn("led_downlight_20w", merged)                            # what nobody touched is still the factory's

    def test_a_disabled_entry_is_removed(self):
        self.assertNotIn("led_panel_600", catalogue.merge([{"led_panel_600": {"disabled": True}}]))

    def test_no_level_changes_nothing(self):
        self.assertEqual(catalogue.merge([]), catalogue.defaults())
        self.assertEqual(catalogue.merge([{}, None]), catalogue.defaults())


class TestCheck(unittest.TestCase):
    def test_what_is_wrong_is_said_where_it_is(self):
        good = {"name": {"es": "a", "en": "b"}, "lamps": 1, "lamp_flux_lm": 1000}
        self.assertEqual(catalogue.check("x", good), [])
        self.assertTrue(any("both languages" in p for p in catalogue.check("x", {**good, "name": {"es": "solo"}})))
        self.assertTrue(any("both languages" in p for p in catalogue.check("x", {**good, "name": "texto"})))
        self.assertTrue(any("kind" in p for p in catalogue.check("x", {**good, "kind": "subterraneo"})))
        self.assertTrue(any("lamp_flux_lm" in p for p in catalogue.check("x", {k: v for k, v in good.items() if k != "lamp_flux_lm"})))
        self.assertTrue(any("lamps" in p for p in catalogue.check("x", {**good, "lamps": 1.5})))
        self.assertEqual(catalogue.check("x", "no es un objeto"), ["x: must be an object"])


class TestAsDocument(unittest.TestCase):
    def test_the_name_comes_in_the_language_asked_and_the_catalogue_keys_stay_out(self):
        entry = catalogue.defaults()["led_panel_600"]
        doc = catalogue.as_document("led_panel_600", entry, "es")
        self.assertEqual(doc["name"], entry["name"]["es"])
        self.assertEqual(catalogue.as_document("led_panel_600", entry, "xx")["name"], entry["name"]["en"])
        for key in ("kind", "illustrative"):
            self.assertNotIn(key, doc)

    def test_the_key_of_the_catalogue_is_the_id_whatever_the_entry_says(self):
        entry = {**catalogue.defaults()["led_panel_600"], "id": "other"}
        self.assertEqual(catalogue.as_document("led_panel_600", entry)["id"], "led_panel_600")

    def test_a_factory_luminaire_runs_in_the_engine(self):
        entry = catalogue.defaults()["led_panel_600"]
        document = {"schema_version": "1.0", "luminaires": [catalogue.as_document("led_panel_600", entry)],
                    "rooms": [{"id": "R1", "width_m": 4, "length_m": 6, "height_m": 2.6, "target_lux": 300, "luminaire": "led_panel_600", "coefficient_of_utilisation": 0.6}]}
        counts = run(document).as_dict()["counts"]
        self.assertEqual((counts["rooms"], counts["luminaires"] > 0), (1, True))


if __name__ == "__main__":
    unittest.main()
