import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

import epc_receptacles  # noqa: E402
from epc_receptacles import Options, ReceptaclesError, layout  # noqa: E402

TUG = {"id": "tug", "kind": "general", "power_va": 100, "height_m": 0.3}
TUE = {"id": "tue", "kind": "special", "power_va": 2200, "height_m": 1.2}


def run(rooms, outlets=None, **opts):
    return epc_receptacles.run({"receptacles": outlets if outlets is not None else [TUG, TUE], "rooms": rooms}, Options(**opts)).as_dict()


def room(**kw):
    return {"id": "R1", "length_m": 6, "width_m": 4, "receptacle": "tug", **kw}


class TestCount(unittest.TestCase):
    def test_area_basis_rounds_up_and_keeps_the_minimum_of_the_use(self):
        r = run([room(use="office")])["rooms"][0]                           # 24 m² at one per 9 m² = 3 outlets (the minimum of an office is 3)
        self.assertEqual((r["required"], r["installed"], r["basis"]), (3, 3, "area"))
        small = run([room(use="office", length_m=2, width_m=2)])["rooms"][0]
        self.assertEqual(small["required"], 3)                                # 4 m² would be 1: the minimum wins

    def test_perimeter_basis_follows_the_walls(self):
        r = run([room(use="warehouse", length_m=20, width_m=12)])["rooms"][0]       # perimeter 64 m at one per 9 m = 8 outlets
        self.assertEqual((r["required"], r["basis"]), (8, "perimeter"))
        self.assertEqual(r["estimate"]["confidence"], 0.7)                    # this one comes from a clause of the norm

    def test_a_number_chosen_by_the_person_replaces_the_rule_and_says_so(self):
        r = run([room(use="office", count=5)])["rooms"][0]
        self.assertEqual((r["required"], r["installed"]), (5, 5))
        self.assertIn("chosen by the person", r["estimate"]["reason"])

    def test_every_estimate_says_why_and_how_sure_it_is(self):
        e = run([room(use="classroom")])["rooms"][0]["estimate"]
        self.assertTrue(e["reason"] and e["source"])
        self.assertLess(e["confidence"], 1)


class TestLoadAndCircuits(unittest.TestCase):
    def test_load_is_outlets_times_power_and_circuits_follow_the_limit_of_the_family(self):
        r = run([room(use="warehouse", length_m=40, width_m=30)])["rooms"][0]       # 140 m of perimeter: 16 outlets, more than 15 per circuit
        self.assertEqual((r["required"], r["load_va"], r["circuits_min"]), (16, 1600.0, 2))

    def test_a_special_outlet_makes_the_room_a_special_use_family(self):
        r = run([room(receptacle="tue", count=2)])["rooms"][0]
        self.assertEqual((r["family"], r["load_va"], r["circuits_min"]), ("TUE", 4400.0, 2))

    def test_without_a_receptacle_named_the_first_of_the_family_is_used(self):
        r = run([{"id": "R1", "length_m": 6, "width_m": 4}])["rooms"][0]
        self.assertEqual(r["receptacle"], "tug")

    def test_no_outlet_for_the_family_is_a_warning_not_a_crash(self):
        out = run([{"id": "R1", "length_m": 6, "width_m": 4}], outlets=[TUE])
        self.assertEqual(out["rooms"][0]["load_va"], 0.0)
        self.assertTrue(any("no outlet" in w for w in out["warnings"]))


class TestChecks(unittest.TestCase):
    def test_mounting_height_by_section_of_the_norm(self):
        low = run([room(height_m=0.1)])["rooms"][0]["checks"][0]
        self.assertFalse(low["ok"])
        housing = run([room(height_m=0.4, norm="770")])["rooms"][0]["checks"][0]          # housing: between 0.2 and 0.3 m
        self.assertFalse(housing["ok"])
        self.assertTrue(run([room(height_m=0.25, norm="770")])["rooms"][0]["checks"][0]["ok"])
        self.assertTrue(run([room(height_m=0.4)], norm="771")["rooms"][0]["checks"][0]["ok"])

    def test_a_wet_room_has_its_own_height_check(self):
        r = run([room(use="bathroom", height_m=0.16)])["rooms"][0]
        self.assertEqual([c["id"] for c in r["checks"]], ["mounting_height", "wet_room_height"])
        self.assertFalse(r["checks"][1]["ok"])

    def test_drawn_outlets_are_counted_and_compared_with_what_is_needed(self):
        pts = [{"x_m": 1, "y_m": 0}, {"x_m": 2, "y_m": 0}]
        r = run([room(use="office", positions=pts)])["rooms"][0]
        self.assertEqual((r["layout"]["mode"], r["installed"], r["required"]), ("drawn", 2, 3))
        self.assertFalse(next(c for c in r["checks"] if c["id"] == "enough_outlets")["ok"])

    def test_failed_checks_come_up_as_warnings_of_the_room(self):
        out = run([room(height_m=0.1)])
        self.assertTrue(any("does not comply" in w for w in out["warnings"]))


class TestLayout(unittest.TestCase):
    def test_every_outlet_is_on_a_wall_inside_the_room(self):
        for n in (1, 3, 8, 20):
            for p in layout.positions(6, 4, n, 0.3):
                self.assertTrue(0 <= p["x_m"] <= 6 and 0 <= p["y_m"] <= 4)
                self.assertTrue(p["x_m"] in (0, 6) or p["y_m"] in (0, 4), p)

    def test_no_outlet_sits_in_a_corner(self):
        for p in layout.positions(6, 4, 12, 0.3):
            on_x_wall, on_y_wall = p["x_m"] in (0, 6), p["y_m"] in (0, 4)
            self.assertFalse(on_x_wall and on_y_wall, p)

    def test_positions_are_the_same_every_time(self):
        self.assertEqual(layout.positions(5, 3, 7, 0.3), layout.positions(5, 3, 7, 0.3))

    def test_a_wall_too_short_for_the_clearance_takes_the_middle(self):
        p = layout.positions(0.5, 0.5, 1, 0.3)[0]
        self.assertTrue(p["x_m"] in (0, 0.5, 0.25) or p["y_m"] in (0, 0.5, 0.25))


class TestErrors(unittest.TestCase):
    def test_what_is_wrong_is_said(self):
        for doc, text in (({"rooms": [{"length_m": 1, "width_m": 1}]}, "needs an `id`"), ({"rooms": [{"id": "a", "length_m": 0, "width_m": 1}]}, "length_m"),
                          ({"rooms": [{"id": "a", "length_m": 1, "width_m": 1, "use": "moon"}]}, "not a known use"), ({"rooms": [{"id": "a", "length_m": 1, "width_m": 1, "receptacle": "x"}]}, "not among the outlets"),
                          ({"rooms": [{"id": "a", "length_m": 1, "width_m": 1, "count": -1}]}, "count"), ("not json", "not valid JSON")):
            with self.assertRaises(ReceptaclesError) as ctx:
                epc_receptacles.run(doc)
            self.assertIn(text, str(ctx.exception))

    def test_a_repeated_id_is_refused(self):
        with self.assertRaises(ReceptaclesError):
            run([room(), room()])


if __name__ == "__main__":
    unittest.main()
