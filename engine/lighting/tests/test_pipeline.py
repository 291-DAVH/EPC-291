import json
import re
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE))

from epc_lighting import LightingError, Options, Result, __version__, run  # noqa: E402
import helpers  # noqa: E402

EXAMPLE = HERE.parent / "examples" / "classroom.json"
GOLDEN = HERE / "fixtures" / "classroom.expected.json"


class TestOutputContract(unittest.TestCase):
    def setUp(self):
        self.out = run(helpers.document(areas=[{"id": "A1", "area_m2": 100, "target_lux": 20, "luminaire": "F1"}])).as_dict()

    def test_stable_top_level_keys(self):
        self.assertEqual(list(self.out), ["schema_version", "engine", "counts", "rooms", "areas", "warnings"])
        self.assertEqual(self.out["schema_version"], "1.0")
        self.assertEqual(self.out["engine"], {"name": "epc_lighting", "version": __version__})

    def test_counts_match_the_content(self):
        counts = self.out["counts"]
        self.assertEqual(counts["rooms"], len(self.out["rooms"]))
        self.assertEqual(counts["areas"], len(self.out["areas"]))
        self.assertEqual(counts["warnings"], len(self.out["warnings"]))
        self.assertEqual(counts["luminaires"], self.out["rooms"][0]["layout"]["installed"] + self.out["areas"][0]["flux"]["luminaires_required"])

    def test_estimates_carry_reason_and_confidence(self):
        room = self.out["rooms"][0]
        for est in (room["target"], room["factors"]["cu"], room["factors"]["maintenance"], room["geometry"]["mounting_height_m"]):
            self.assertTrue(est["reason"])
            self.assertTrue(0 <= est["confidence"] <= 1)

    def test_it_is_json_without_nan_and_numbers_are_rounded(self):
        text = json.dumps(self.out, allow_nan=False)
        self.assertIsNone(re.search(r"\d[eE][-+]?\d", text))  # no exponent notation: nothing like 1e-07 float noise
        for room in self.out["rooms"]:
            self.assertEqual(room["verification"]["average_lux"], round(room["verification"]["average_lux"], 3))

    def test_no_dates_paths_or_random_ids(self):
        text = json.dumps(self.out)
        self.assertNotIn("/home", text)
        self.assertIsNone(re.search(r"\d{4}-\d{2}-\d{2}", text))
        self.assertIsNone(re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-", text))

    def test_the_same_input_gives_the_same_output(self):
        doc = helpers.document()
        first = json.dumps(run(doc).as_dict(), sort_keys=False)
        second = json.dumps(run(doc).as_dict(), sort_keys=False)
        self.assertEqual(first, second)

    def test_the_input_is_not_modified(self):
        doc = helpers.document()
        before = json.dumps(doc, sort_keys=True)
        run(doc)
        self.assertEqual(json.dumps(doc, sort_keys=True), before)

    def test_result_is_a_result_object(self):
        self.assertIsInstance(run(helpers.document()), Result)


class TestBehaviour(unittest.TestCase):
    def test_efficiency_is_accounted_for_in_the_installed_flux(self):
        lum = helpers.luminaire_dict(efficiency=0.5)
        res = run(helpers.document([helpers.room_dict()], [lum])).as_dict()["rooms"][0]
        self.assertTrue(res["verification"]["complies"])  # the count accounts for the efficiency
        self.assertGreater(res["flux"]["required_installed_lm"], res["flux"]["required_lm"])

    def test_efficiency_raises_the_count(self):
        base = run(helpers.document()).as_dict()["rooms"][0]["flux"]["luminaires_exact"]
        lum = helpers.luminaire_dict(efficiency=0.5)
        low = run(helpers.document([helpers.room_dict()], [lum])).as_dict()["rooms"][0]["flux"]["luminaires_exact"]
        self.assertAlmostEqual(low, base * 2, places=2)

    def test_a_higher_target_needs_more_luminaires(self):
        counts = [run(helpers.document([helpers.room_dict(target_lux=t)])).as_dict()["rooms"][0]["layout"]["installed"] for t in (100, 300, 750)]
        self.assertEqual(counts, sorted(counts))
        self.assertLess(counts[0], counts[-1])

    def test_the_average_always_reaches_the_target_by_construction(self):
        for width in (3, 4, 7, 12):
            for target in (100, 300, 500):
                room = helpers.room_dict(width_m=width, target_lux=target)
                self.assertTrue(run(helpers.document([room])).as_dict()["rooms"][0]["verification"]["complies"], (width, target))

    def test_energy_block(self):
        room = helpers.room_dict(operating_hours_per_year=1000)
        energy = run(helpers.document([room])).as_dict()["rooms"][0]["energy"]
        self.assertEqual(energy["installed_power_w"], 128.0)
        self.assertEqual(energy["annual_energy_kwh"], 128.0)
        self.assertAlmostEqual(energy["power_density_w_m2"], 128 / 24, places=3)

    def test_several_rooms_share_the_tag_sequence(self):
        out = run(helpers.document([helpers.room_dict(id="A"), helpers.room_dict(id="B")])).as_dict()
        tags = [p["tag"] for r in out["rooms"] for p in r["layout"]["positions"]]
        self.assertEqual(len(tags), len(set(tags)))

    def test_options_are_a_frozen_value(self):
        with self.assertRaises(Exception):
            Options().enforce_spacing = True  # type: ignore[misc]

    def test_warnings_are_prefixed_with_the_room(self):
        out = run(helpers.document([helpers.room_dict(length_m=12)]))
        self.assertTrue(all(w.startswith("room 'R1': ") for w in out.warnings))

    def test_geometry_that_cannot_work_is_a_domain_error(self):
        with self.assertRaises(LightingError):
            run(helpers.document([helpers.room_dict(suspension_m=1.9)]))


class TestGolden(unittest.TestCase):
    """The example document and its fixed result: a change in behaviour shows up as a diff to review."""

    def test_example_matches_the_golden_file_byte_for_byte(self):
        got = json.dumps(run(EXAMPLE.read_bytes()).as_dict(), indent=1, ensure_ascii=False) + "\n"
        self.assertEqual(got, GOLDEN.read_text(encoding="utf-8"))

    def test_the_example_reproduces_the_article(self):
        room = run(EXAMPLE.read_bytes()).as_dict()["rooms"][0]
        self.assertAlmostEqual(room["flux"]["required_lm"], 9278.35, delta=0.01)
        self.assertEqual(room["layout"]["installed"], 2)


if __name__ == "__main__":
    unittest.main()
