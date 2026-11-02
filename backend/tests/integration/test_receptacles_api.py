"""Receptacles: the choices of the panel, the calculation for the rooms of a sheet, and the catalogue of outlets at its levels."""
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from epc.core.config import settings
from epc.main import create_app

BASE = "/api/projects/ACME/P-1/receptacles"
SCALE = {"p1": [0, 0], "p2": [100, 0], "distance_m": 10}                       # one unit of the view is 0.1 m
OFFICE = {"id": "R1", "name": "Oficina", "points": [[0, 0], [60, 0], [60, 40], [0, 40]]}     # 6 m x 4 m
OWN = {"name": {"es": "Mi toma", "en": "My outlet"}, "kind": "general", "power_va": 150, "height_m": 0.3}


def body(rooms=(OFFICE,), params=None, nodes=(), **extra):
    return {"sheet": {"scale": SCALE, "rooms": list(rooms), "nodes": list(nodes)}, "rooms": params if params is not None else {"R1": {"use": "office"}}, **extra}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._old = (settings.projects_dir, settings.role, settings.data_dir)
        settings.projects_dir, settings.role, settings.data_dir = self.root, "admin", self.root / "_data"
        self.c = TestClient(create_app())
        r = self.c.post("/api/projects", json={"client_name": "Acme SA", "client_code": "ACME", "project_code": "P-1", "project_name": "Planta",
                                                "jurisdiction": "AR", "methodology": "pm2", "disciplines": ["electrical"]})
        self.assertEqual(r.status_code, 201, r.text)

    def tearDown(self):
        settings.projects_dir, settings.role, settings.data_dir = self._old
        self.tmp.cleanup()


class TestOptions(Base):
    def test_the_panel_gets_the_uses_with_their_source_and_the_outlets_in_force(self):
        o = self.c.get(BASE + "/options?lang=es").json()
        office = next(u for u in o["uses"] if u["id"] == "office")
        self.assertEqual((office["basis"], office["per_m2"], office["family"], bool(office["label"]), bool(office["source"])), ("area", 9, "TUG", True, True))
        outlet = next(x for x in o["receptacles"] if x["id"] == "tug_2x10_t")
        self.assertEqual((outlet["level"], outlet["illustrative"], outlet["kind"]), ("factory", True, "general"))
        self.assertIn("Tomacorriente", outlet["name"])
        self.assertEqual(o["norms"], ["771", "770"])


class TestCalc(Base):
    def test_an_office_gets_its_outlets_along_the_walls_in_view_units(self):
        out = self.c.post(BASE + "/calc", json=body()).json()
        room = out["result"]["rooms"][0]
        self.assertEqual((room["required"], room["installed"], room["family"]), (3, 3, "TUG"))
        points = out["placements"]["R1"]
        self.assertEqual(len(points), 3)
        for p in points:
            self.assertTrue(0 <= p["x"] <= 60 and 0 <= p["y"] <= 40)
            self.assertTrue(p["x"] in (0, 60) or p["y"] in (0, 40), p)
        self.assertEqual({p["kind"] for p in points}, {"TG"})
        self.assertEqual(out["skipped"], [])

    def test_a_room_that_is_not_at_the_origin_gets_its_outlets_from_its_own_corner(self):
        far = {"id": "R1", "name": "Oficina", "points": [[100, 50], [160, 50], [160, 90], [100, 90]]}
        points = self.c.post(BASE + "/calc", json=body(rooms=(far,))).json()["placements"]["R1"]
        self.assertTrue(all(100 <= p["x"] <= 160 and 50 <= p["y"] <= 90 for p in points))

    def test_a_special_use_outlet_is_placed_as_a_te_node(self):
        out = self.c.post(BASE + "/calc", json=body(params={"R1": {"use": "general", "receptacle": "tue_2x20_t", "count": 2}})).json()
        self.assertEqual({p["kind"] for p in out["placements"]["R1"]}, {"TE"})
        self.assertEqual(out["result"]["rooms"][0]["family"], "TUE")

    def test_nothing_is_saved_by_calculating(self):
        self.c.post(BASE + "/calc", json=body())
        self.assertFalse(list(self.root.glob("**/receptacles.json")))

    def test_a_room_without_what_it_needs_is_left_out_with_the_reason_and_the_others_are_calculated(self):
        other = {"id": "R2", "name": "Otro", "points": [[0, 0], [30, 0], [30, 30], [0, 30]]}
        out = self.c.post(BASE + "/calc", json=body(rooms=(OFFICE, other), params={"R1": {"use": "office"}, "R2": {"use": "moon"}})).json()
        self.assertEqual([r["id"] for r in out["result"]["rooms"]], ["R1"])
        self.assertEqual(out["skipped"][0]["id"], "R2")
        self.assertIn("not a known use", out["skipped"][0]["reason"])

    def test_with_no_room_to_calculate_the_answer_says_so_without_an_error(self):
        out = self.c.post(BASE + "/calc", json=body(params={}))
        self.assertEqual(out.status_code, 200)
        self.assertIsNone(out.json()["result"])
        self.assertIn("no use chosen", out.json()["skipped"][0]["reason"])

    def test_a_sheet_without_scale_is_refused_and_says_so(self):
        r = self.c.post(BASE + "/calc", json={"sheet": {"rooms": [OFFICE]}, "rooms": {"R1": {"use": "office"}}})
        self.assertEqual(r.status_code, 422)
        self.assertIn("scale", str(r.json()))

    def test_a_room_that_is_not_a_rectangle_is_calculated_by_its_bounding_box_and_says_so(self):
        ell = {"id": "R1", "name": "L", "points": [[0, 0], [60, 0], [60, 20], [30, 20], [30, 40], [0, 40]]}
        out = self.c.post(BASE + "/calc", json=body(rooms=(ell,))).json()
        self.assertTrue(any("bounding box" in w for w in out["warnings"]))

    def test_the_outlets_drawn_are_checked_as_they_are_when_asked(self):
        nodes = [{"id": f"n{i}", "kind": "TG", "x": x, "y": 0, "tag": f"TG{i}"} for i, x in enumerate((10, 20))] + [{"id": "lu", "kind": "LU", "x": 5, "y": 5}]
        out = self.c.post(BASE + "/calc", json=body(nodes=nodes, options={"use_drawn": True})).json()
        room = out["result"]["rooms"][0]
        self.assertEqual((room["layout"]["mode"], room["installed"], room["required"]), ("drawn", 2, 3))        # the luminaire is not an outlet
        self.assertTrue(any("2 outlets drawn, 3 needed" in w for w in out["warnings"]))

    def test_with_use_drawn_a_room_without_outlets_is_left_out(self):
        out = self.c.post(BASE + "/calc", json=body(options={"use_drawn": True})).json()
        self.assertIn("no outlets drawn", out["skipped"][0]["reason"])

    def test_the_mounting_height_is_checked_by_the_section_of_the_norm(self):
        out = self.c.post(BASE + "/calc", json=body(params={"R1": {"use": "office", "height_m": 0.4, "norm": "770"}})).json()
        self.assertTrue(any("does not comply" in w for w in out["warnings"]))

    def test_numbers_that_are_not_finite_never_reach_the_engine(self):
        r = self.c.post(BASE + "/calc", data='{"sheet": {"scale": {"p1": [0, 0], "p2": [NaN, 0], "distance_m": 1}, "rooms": []}}', headers={"Content-Type": "application/json"})
        self.assertEqual(r.status_code, 422)


class TestCatalogue(Base):
    def test_a_project_adds_replaces_and_removes_outlets_and_the_options_say_which_level_set_each(self):
        r = self.c.put(BASE + "/catalogue", json={"receptacles": {"mine": OWN, "tug_2x10_t": {**OWN, "power_va": 120}, "tug_ip54": {"disabled": True}}})
        self.assertEqual(r.status_code, 200, r.text)
        rows = {x["id"]: x for x in self.c.get(BASE + "/options").json()["receptacles"]}
        self.assertEqual((rows["mine"]["level"], rows["tug_2x10_t"]["power_va"]), ("project", 120))
        self.assertNotIn("tug_ip54", rows)

    def test_a_calculation_uses_the_outlet_of_the_project(self):
        self.c.put(BASE + "/catalogue", json={"receptacles": {"mine": OWN}})
        room = self.c.post(BASE + "/calc", json=body(params={"R1": {"use": "office", "receptacle": "mine"}})).json()["result"]["rooms"][0]
        self.assertEqual((room["receptacle"], room["power_va_each"], room["load_va"]), ("mine", 150.0, 450.0))

    def test_an_entry_equal_to_what_is_below_is_not_a_change(self):
        factory = self.c.get(BASE + "/catalogue").json()["receptacles"]["tug_2x10_t"]
        self.c.put(BASE + "/catalogue", json={"receptacles": {"tug_2x10_t": factory}})
        self.assertEqual(self.c.get(BASE + "/catalogue").json()["own"], {})

    def test_an_invalid_entry_is_refused_with_what_to_correct_and_nothing_is_stored(self):
        r = self.c.put(BASE + "/catalogue", json={"receptacles": {"bad": {"name": {"es": "x"}, "kind": "odd", "power_va": -1}, "bad id!": OWN}})
        self.assertEqual(r.status_code, 422)
        self.assertFalse(list(self.root.glob("**/receptacles.json")))

    def test_reset_goes_back_to_what_the_level_below_gives(self):
        self.c.put(BASE + "/catalogue", json={"receptacles": {"mine": OWN}})
        self.assertEqual(self.c.delete(BASE + "/catalogue").json()["own"], {})
        self.assertNotIn("mine", self.c.get(BASE + "/catalogue").json()["receptacles"])

    def test_the_company_level_needs_an_organization_to_belong_to(self):
        self.assertEqual(self.c.get("/api/data/receptacles").status_code, 422)
