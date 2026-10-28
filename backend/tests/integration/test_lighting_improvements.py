"""Lighting: a room checked as it is drawn, the luminaires compared for a room, the luminaire chosen for the rooms that have none, the energy against the person's limit and the power factor."""
import unittest

from epc.core.fsutil import read_json
from tests.integration.test_lighting_api import BASE, CLASSROOM, OWN, SCALE, Base, body

PANEL = {"activity": "education.classroom", "luminaire": "led_panel_600"}


def node(i, x, y, tag="", **attrs):
    return {"id": f"n{i}", "kind": "LU", "x": x, "y": y, "tag": tag, "attrs": attrs}


def drawn_body(nodes, **options):
    b = body(params={"R1": PANEL})
    b["sheet"]["nodes"] = nodes
    b["options"] = {"use_drawn": True, **options}
    return b


class TestCheckedAsDrawn(Base):
    def test_the_room_is_checked_with_the_luminaires_drawn_in_it_and_keeps_their_tags(self):
        nodes = [node(1, 15, 10, "LU-010"), node(2, 45, 10, "LU-011"), node(3, 15, 30), node(4, 45, 30)]
        out = self.c.post(BASE + "/calc", json=drawn_body(nodes)).json()
        room = out["result"]["rooms"][0]
        self.assertEqual((room["layout"]["drawn"], room["layout"]["installed"]), (True, 4))
        self.assertEqual([p["tag"] for p in out["placements"]["R1"]][:2], ["LU-010", "LU-011"])
        self.assertEqual([(p["x"], p["y"]) for p in out["placements"]["R1"]][0], (15.0, 10.0))               # the same place the node is

    def test_a_luminaire_outside_the_room_or_of_another_kind_does_not_count(self):
        nodes = [node(1, 15, 10), node(2, 500, 500), {"id": "t", "kind": "TG", "x": 30, "y": 20}]
        out = self.c.post(BASE + "/calc", json=drawn_body(nodes)).json()
        self.assertEqual(out["result"]["rooms"][0]["layout"]["installed"], 1)

    def test_a_room_with_nothing_drawn_is_left_out_and_says_why(self):
        out = self.c.post(BASE + "/calc", json=drawn_body([node(1, 500, 500)])).json()
        self.assertIsNone(out["result"])
        self.assertIn("no luminaires drawn", out["skipped"][0]["reason"])

    def test_fewer_luminaires_than_needed_do_not_comply_and_the_height_of_a_node_is_used(self):
        out = self.c.post(BASE + "/calc", json=drawn_body([node(1, 30, 20, "", lighting={"height_m": 2.2})])).json()
        room = out["result"]["rooms"][0]
        self.assertFalse(room["verification"]["complies"])
        self.assertEqual(room["layout"]["positions"][0]["z_m"], 2.2)

    def test_the_nodes_are_not_kept_in_the_study_and_do_not_make_it_stale(self):
        self.assertEqual(self.c.put("/api/projects/ACME/P-1/layout/L0", json={"discipline": "arquitectura", "scale": SCALE, "origin": [0, 0], "nodes": [], "lines": [], "circuits": []}).status_code, 200)
        layout = "/api/projects/ACME/P-1/layout/L0@electrica_BT"
        drawing = {"discipline": "electrica_BT", "scale": None, "origin": [0, 0], "nodes": [], "lines": [], "circuits": [], "rooms": [{**CLASSROOM, "lighting": PANEL}]}
        self.assertEqual(self.c.put(layout, json=drawing).status_code, 200)
        asked = body(params={"R1": PANEL})
        asked["sheet"]["nodes"] = [node(1, 15, 10)]
        self.assertEqual(self.c.put(BASE + "/study/L0@electrica_BT", json=asked).status_code, 200)
        self.assertFalse(self.c.get(BASE + "/study/L0@electrica_BT").json()["stale"])
        kept = read_json(self.d / "workspace" / "02-engineering" / "layout" / "L0@electrica_BT" / "src" / "lighting.json", {})
        self.assertNotIn("nodes", kept["input"]["sheet"])


class TestCompare(Base):
    def compare(self, **kw):
        return self.c.post(BASE + "/compare", json={**body(params={"R1": {"activity": "education.classroom", **kw}}), "room": "R1"})

    def test_every_interior_luminaire_is_calculated_for_the_room_best_first(self):
        r = self.compare()
        self.assertEqual(r.status_code, 200, r.text)
        out = r.json()
        ids = [o["luminaire"] for o in out["options"]]
        self.assertIn("led_panel_600", ids)
        self.assertNotIn("led_floodlight_100w", ids)                                                      # an exterior luminaire is not an option for a room
        self.assertNotIn("led_emergency_3w", ids)                                                         # nor is the one that lights the way out
        complying = [o for o in out["options"] if o["complies"]]
        self.assertEqual(out["options"][:len(complying)], complying)                                      # the ones that comply come first
        powers = [o["power_w"] for o in complying]
        self.assertEqual(powers, sorted(powers))
        self.assertEqual(out["best"], complying[0]["luminaire"])

    def test_the_figures_are_the_ones_the_panel_gets_for_that_luminaire(self):
        row = next(o for o in self.compare().json()["options"] if o["luminaire"] == "led_panel_600")
        direct = self.c.post(BASE + "/calc", json=body(params={"R1": PANEL})).json()["result"]["rooms"][0]
        self.assertEqual((row["installed"], row["average_lux"], row["power_w"]), (direct["layout"]["installed"], direct["verification"]["average_lux"], direct["energy"]["installed_power_w"]))

    def test_an_exterior_area_is_compared_among_exterior_luminaires_and_needs_its_target(self):
        r = self.c.post(BASE + "/compare", json={**body(params={"R1": {"exterior": True, "target_lux": 20}}), "room": "R1"}).json()
        self.assertEqual([o["luminaire"] for o in r["options"]], ["led_floodlight_100w"])
        no_target = self.c.post(BASE + "/compare", json={**body(params={"R1": {"exterior": True}}), "room": "R1"})
        self.assertEqual(no_target.status_code, 422)

    def test_a_room_that_is_not_there_or_has_no_parameters_is_refused(self):
        self.assertEqual(self.c.post(BASE + "/compare", json={**body(params={"R1": PANEL}), "room": "R9"}).status_code, 422)
        self.assertEqual(self.c.post(BASE + "/compare", json={**body(params={}), "room": "R1"}).status_code, 422)


class TestAutoLuminaire(Base):
    def test_a_room_with_a_target_and_no_luminaire_gets_the_best_one_and_it_is_said(self):
        asked = body(params={"R1": {"activity": "education.classroom"}})
        asked["options"] = {"auto_luminaire": True}
        out = self.c.post(BASE + "/calc", json=asked).json()
        self.assertTrue(out["result"]["rooms"][0]["verification"]["complies"])
        self.assertTrue(any("was chosen" in w for w in out["warnings"]))
        without = self.c.post(BASE + "/calc", json=body(params={"R1": {"activity": "education.classroom"}})).json()
        self.assertIn("no luminaire chosen", without["skipped"][0]["reason"])                           # not without asking for it

    def test_a_room_that_already_has_a_luminaire_keeps_it(self):
        asked = body(params={"R1": {**PANEL, "luminaire": "led_batten_2x18w"}})
        asked["options"] = {"auto_luminaire": True}
        out = self.c.post(BASE + "/calc", json=asked).json()
        self.assertEqual(out["result"]["rooms"][0]["luminaire"]["id"], "led_batten_2x18w")
        self.assertFalse(any("was chosen" in w for w in out["warnings"]))


class TestEnergy(Base):
    def calc(self, **options):
        return self.c.post(BASE + "/calc", json={**body(params={"R1": PANEL}), "options": options}).json()

    def test_without_limit_hours_or_tariff_only_the_power_is_given(self):
        check = self.calc()["energy_checks"]["R1"]
        self.assertEqual((check["complies"], check["annual_kwh"], check["annual_cost"]), (None, None, None))
        self.assertGreater(check["power_w"], 0)

    def test_the_density_is_compared_with_the_limit_of_the_person(self):
        density = self.calc()["energy_checks"]["R1"]["density_w_m2"]
        self.assertTrue(self.calc(power_limit_w_m2=density + 1)["energy_checks"]["R1"]["complies"])
        self.assertFalse(self.calc(power_limit_w_m2=density - 1)["energy_checks"]["R1"]["complies"])

    def test_the_yearly_energy_and_cost_come_from_the_hours_and_the_tariff(self):
        check = self.calc(hours_default=2000, kwh_price=0.15)["energy_checks"]["R1"]
        self.assertAlmostEqual(check["annual_kwh"], check["power_w"] * 2, places=1)                       # W x 2000 h = 2 x W kWh
        self.assertAlmostEqual(check["annual_cost"], check["annual_kwh"] * 0.15, places=2)
        own = self.c.post(BASE + "/calc", json={**body(params={"R1": {**PANEL, "operating_hours_per_year": 1000}}), "options": {"hours_default": 2000}}).json()["energy_checks"]["R1"]
        self.assertAlmostEqual(own["annual_kwh"], own["power_w"], places=1)                               # the hours of the room win over the default

    def test_the_options_are_bounded(self):
        for bad in ({"power_limit_w_m2": 0}, {"kwh_price": -1}, {"hours_default": 9000}):
            self.assertEqual(self.c.post(BASE + "/calc", json={**body(params={"R1": PANEL}), "options": bad}).status_code, 422, bad)


class TestPowerFactor(Base):
    def test_the_factor_of_a_luminaire_goes_with_the_room_and_the_catalogue_row(self):
        self.c.put(BASE + "/luminaires", json={"luminaires": {"mine": {**OWN, "power_factor": 0.9, "favorite": True, "group": "Offices"}}})
        row = next(x for x in self.c.get(BASE + "/options").json()["luminaires"] if x["id"] == "mine")
        self.assertEqual((row["power_factor"], row["favorite"], row["group"]), (0.9, True, "Offices"))
        out = self.c.post(BASE + "/calc", json=body(params={"R1": {"activity": "education.classroom", "luminaire": "mine"}})).json()
        self.assertEqual(out["rooms"][0]["power_factor"], 0.9)
        self.assertIsNone(self.c.post(BASE + "/calc", json=body(params={"R1": PANEL})).json()["rooms"][0]["power_factor"])

    def test_the_factor_of_the_emergency_luminaire_goes_with_the_room_too(self):
        self.c.put(BASE + "/luminaires", json={"luminaires": {"em": {**OWN, "power_w": 3, "power_factor": 0.6}}})
        out = self.c.post(BASE + "/calc", json=body(params={"R1": {**PANEL, "emergency_luminaire": "em"}})).json()
        self.assertEqual((out["rooms"][0]["emergency_power_factor"], out["rooms"][0]["power_factor"]), (0.6, None))

    def test_a_factor_out_of_range_is_refused_with_what_to_correct(self):
        r = self.c.put(BASE + "/luminaires", json={"luminaires": {"mine": {**OWN, "power_factor": 1.5}}})
        self.assertEqual(r.status_code, 422)
        self.assertIn("power_factor", r.text)


if __name__ == "__main__":
    unittest.main()
