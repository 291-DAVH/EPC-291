"""Lighting: the choices of the panel, the calculation for the rooms of a sheet, and the catalogue of luminaires at its levels."""
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

from epc.core.config import settings
from epc.core.fsutil import read_json, write_json
from epc.main import create_app
from epc.modules.identity import public as identity
from epc.modules.projects import public as projects

BASE = "/api/projects/ACME/P-1/lighting"
SCALE = {"p1": [0, 0], "p2": [100, 0], "distance_m": 10}                       # one unit of the view is 0.1 m
CLASSROOM = {"id": "R1", "name": "Aula", "points": [[0, 0], [60, 0], [60, 40], [0, 40]]}     # 6 m x 4 m
OWN = {"name": {"es": "Doble 2400", "en": "Double 2400"}, "kind": "interior", "lamps": 2, "lamp_flux_lm": 2400, "power_w": 64}
PARAMS = {"activity": "education.classroom", "luminaire": "mine", "coefficient_of_utilisation": 0.97}


def body(rooms=(CLASSROOM,), params=None, **extra):
    return {"sheet": {"scale": SCALE, "rooms": list(rooms)}, "rooms": params if params is not None else {"R1": PARAMS}, **extra}


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
        self.d = projects.get_project_dir("ACME", "P-1")

    def tearDown(self):
        settings.projects_dir, settings.role, settings.data_dir = self._old
        self.tmp.cleanup()

    def with_own(self):
        self.assertEqual(self.c.put(BASE + "/luminaires", json={"luminaires": {"mine": OWN}}).status_code, 200)


class TestOptions(Base):
    def test_the_panel_gets_activities_materials_systems_methods_and_the_luminaires_in_force(self):
        o = self.c.get(BASE + "/options?lang=es").json()
        self.assertIn("education.classroom", [a["id"] for a in o["activities"]])
        classroom = next(a for a in o["activities"] if a["id"] == "education.classroom")
        self.assertEqual((classroom["em_lux"], bool(classroom["source"]), bool(classroom["label"])), (300, True, True))          # the target says where it comes from
        self.assertTrue(o["materials"] and o["systems"])
        self.assertEqual(o["methods"], ["lumen", "zonal"])
        panel = next(x for x in o["luminaires"] if x["id"] == "led_panel_600")
        self.assertEqual((panel["level"], panel["illustrative"], panel["kind"]), ("factory", True, "interior"))
        self.assertIn("Panel", panel["name"])                                                                                  # in the language asked
        self.assertIn("LED panel", next(x for x in self.c.get(BASE + "/options").json()["luminaires"] if x["id"] == "led_panel_600")["name"])


class TestCalc(Base):
    def test_the_article_classroom_gets_its_two_luminaires_in_one_row_inside_the_room(self):
        self.with_own()
        r = self.c.post(BASE + "/calc", json=body())
        self.assertEqual(r.status_code, 200, r.text)
        out = r.json()
        room = out["result"]["rooms"][0]
        self.assertEqual(room["layout"]["installed"], 2)
        self.assertAlmostEqual(room["verification"]["average_lux"], 310.4, places=1)           # the worked example of the article
        self.assertTrue(room["verification"]["complies"])
        self.assertEqual([(p["x"], p["y"]) for p in out["placements"]["R1"]], [(15.0, 20.0), (45.0, 20.0)])      # 1.5 m and 4.5 m along the length, 2 m across, in view units
        self.assertEqual(out["rooms"][0], {"id": "R1", "name": "Aula", "length_m": 6.0, "width_m": 4.0, "exact": True, "corner": [0, 0]})
        self.assertEqual(out["skipped"], [])

    def test_a_room_that_is_not_at_the_origin_gets_its_luminaires_from_its_own_corner(self):
        self.with_own()
        moved = {**CLASSROOM, "points": [[100, 50], [160, 50], [160, 90], [100, 90]]}
        out = self.c.post(BASE + "/calc", json=body(rooms=(moved,))).json()
        self.assertEqual([(p["x"], p["y"]) for p in out["placements"]["R1"]], [(115.0, 70.0), (145.0, 70.0)])

    def test_nothing_is_saved_by_calculating(self):
        self.with_own()
        before = sorted(p.name for p in (self.d / "workspace" / "00-setup").iterdir())
        self.assertEqual(self.c.post(BASE + "/calc", json=body()).status_code, 200)
        self.assertEqual(sorted(p.name for p in (self.d / "workspace" / "00-setup").iterdir()), before)

    def test_a_room_without_what_it_needs_is_left_out_with_the_reason_and_the_others_are_calculated(self):
        self.with_own()
        second = {"id": "R2", "name": "Pasillo", "points": [[0, 50], [60, 50], [60, 70], [0, 70]]}
        third = {"id": "R3", "name": "Sala", "points": [[70, 0], [130, 0], [130, 40], [70, 40]]}
        fourth = {"id": "R4", "name": "Otra", "points": [[70, 50], [130, 50], [130, 90], [70, 90]]}
        params = {"R1": PARAMS, "R3": {"luminaire": "mine"}, "R4": {"activity": "education.classroom", "luminaire": "no_such"}}
        out = self.c.post(BASE + "/calc", json=body(rooms=(CLASSROOM, second, third, fourth), params=params)).json()
        reasons = {s["id"]: s["reason"] for s in out["skipped"]}
        self.assertEqual(set(reasons), {"R2", "R3", "R4"})
        self.assertIn("no luminaire", reasons["R2"])
        self.assertIn("no activity or target", reasons["R3"])
        self.assertIn("not in the catalogue", reasons["R4"])
        self.assertEqual([r["id"] for r in out["result"]["rooms"]], ["R1"])

    def test_with_no_room_to_calculate_the_answer_says_so_without_an_error(self):
        out = self.c.post(BASE + "/calc", json=body(params={})).json()
        self.assertIsNone(out["result"])
        self.assertEqual(len(out["skipped"]), 1)
        self.assertTrue(any("nothing could be calculated" in w for w in out["warnings"]))

    def test_a_room_that_is_not_a_rectangle_is_calculated_by_its_bounding_box_and_says_so(self):
        self.with_own()
        l_shape = {"id": "R1", "name": "En L", "points": [[0, 0], [60, 0], [60, 20], [20, 20], [20, 40], [0, 40]]}
        out = self.c.post(BASE + "/calc", json=body(rooms=(l_shape,))).json()
        self.assertFalse(out["rooms"][0]["exact"])
        self.assertTrue(any("bounding box" in w for w in out["warnings"]))
        self.assertEqual(out["rooms"][0]["length_m"], 6.0)

    def test_the_luminaires_that_fall_outside_the_outline_of_an_l_shaped_room_are_not_placed_and_it_is_said(self):
        self.with_own()
        l_shape = {"id": "R1", "name": "En L", "points": [[0, 0], [120, 0], [120, 20], [20, 20], [20, 80], [0, 80]]}
        out = self.c.post(BASE + "/calc", json=body(rooms=(l_shape,))).json()
        placed = out["placements"]["R1"]
        every = out["result"]["rooms"][0]["layout"]["installed"]
        self.assertTrue(0 < len(placed) < every, (len(placed), every))
        self.assertTrue(all(0 <= p["x"] <= 120 and 0 <= p["y"] <= 80 and (p["x"] <= 20 or p["y"] <= 20) for p in placed), placed)
        self.assertTrue(any("fall outside its outline" in w for w in out["warnings"]), out["warnings"])

    def test_a_sheet_without_scale_is_refused_and_a_polygon_without_area_is_left_out(self):
        self.with_own()
        no_scale = {"sheet": {"rooms": [CLASSROOM]}, "rooms": {"R1": PARAMS}}
        r = self.c.post(BASE + "/calc", json=no_scale)
        self.assertEqual(r.status_code, 422)
        self.assertIn("scale", r.json()["detail"]["errors"])
        flat = {"id": "R1", "name": "Plano", "points": [[0, 0], [10, 0], [20, 0]]}
        out = self.c.post(BASE + "/calc", json=body(rooms=(flat,))).json()
        self.assertIn("no area", out["skipped"][0]["reason"])

    def test_what_the_engine_refuses_comes_back_as_a_message_that_says_what_to_fix(self):
        self.with_own()
        r = self.c.post(BASE + "/calc", json=body(params={"R1": {**PARAMS, "activity": "no.such.activity"}}))
        self.assertEqual(r.status_code, 422, r.text)
        self.assertIn("lighting", r.json()["detail"]["errors"])
        self.assertEqual(self.c.post(BASE + "/calc", json=body(params={"R1": {**PARAMS, "height_m": -1}})).status_code, 422)      # refused before it reaches the engine

    def test_numbers_that_are_not_finite_and_rooms_of_absurd_size_never_reach_the_engine(self):
        self.with_own()
        raw = '{"sheet": {"scale": {"p1": [0, 0], "p2": [100, 0], "distance_m": Infinity}, "rooms": []}}'
        self.assertEqual(self.c.post(BASE + "/calc", content=raw, headers={"content-type": "application/json"}).status_code, 422)
        wrong_scale = {"sheet": {"scale": {"p1": [0, 0], "p2": [1, 0], "distance_m": 10000}, "rooms": [CLASSROOM]}, "rooms": {"R1": PARAMS}}
        out = self.c.post(BASE + "/calc", json=wrong_scale).json()
        self.assertIsNone(out["result"])
        self.assertIn("check the scale", out["skipped"][0]["reason"])

    def test_the_fingerprint_follows_what_the_calculation_was_made_from(self):
        self.with_own()
        first = self.c.post(BASE + "/calc", json=body()).json()["fingerprint"]
        self.assertEqual(self.c.post(BASE + "/calc", json=body()).json()["fingerprint"], first)                    # the same input, the same fingerprint
        self.assertNotEqual(self.c.post(BASE + "/calc", json=body(params={"R1": {**PARAMS, "target_lux": 500}})).json()["fingerprint"], first)
        self.c.put(BASE + "/luminaires", json={"luminaires": {"mine": {**OWN, "lamps": 3}}})
        self.assertNotEqual(self.c.post(BASE + "/calc", json=body()).json()["fingerprint"], first)                 # a change of the luminaire makes it stale

    def test_the_options_of_the_calculation_reach_the_engine(self):
        self.with_own()
        without = self.c.post(BASE + "/calc", json=body(options={"compute_points": False})).json()["result"]["rooms"][0]["points"]
        self.assertFalse(without["computed"])
        zonal = self.c.post(BASE + "/calc", json=body(params={"R1": {**PARAMS, "method": "zonal", "coefficient_of_utilisation": None}})).json()
        self.assertEqual(zonal["result"]["rooms"][0]["method"], "zonal")


class TestCatalogue(Base):
    def test_a_project_adds_replaces_and_removes_luminaires_and_the_options_say_which_level_set_each(self):
        self.with_own()
        panel = {**OWN, "name": {"es": "Mi panel", "en": "My panel"}, "lamps": 1, "lamp_flux_lm": 4000}
        self.assertEqual(self.c.put(BASE + "/luminaires", json={"luminaires": {"led_panel_600": panel, "led_batten_2x18w": {"disabled": True}}}).status_code, 200)
        rows = {x["id"]: x for x in self.c.get(BASE + "/options").json()["luminaires"]}
        self.assertEqual((rows["mine"]["level"], rows["led_panel_600"]["level"], rows["led_downlight_20w"]["level"]), ("project", "project", "factory"))
        self.assertEqual(rows["led_panel_600"]["lamp_flux_lm"], 4000)
        self.assertNotIn("led_batten_2x18w", rows)
        view = self.c.get(BASE + "/luminaires").json()
        self.assertEqual(sorted(view["own"]), ["led_batten_2x18w", "led_panel_600", "mine"])
        self.assertEqual(view["inherits"], "company")

    def test_an_entry_equal_to_what_is_below_is_not_a_change_and_removing_what_is_not_there_is_nothing(self):
        factory = {k: v for k, v in self.c.get(BASE + "/luminaires").json()["luminaires"]["led_panel_600"].items()}
        self.c.put(BASE + "/luminaires", json={"luminaires": {"led_panel_600": factory, "nobody": {"disabled": True}}})
        self.assertEqual(self.c.get(BASE + "/luminaires").json()["own"], {})
        self.assertFalse((self.d / "workspace" / "00-setup" / "luminaires.json").exists())

    def test_an_invalid_entry_is_refused_with_what_to_correct_and_nothing_is_stored(self):
        r = self.c.put(BASE + "/luminaires", json={"luminaires": {"bad": {"name": {"es": "solo"}, "lamps": 1.5}}})
        self.assertEqual(r.status_code, 422)
        problems = r.json()["detail"]["errors"]["luminaires"]
        self.assertTrue(any("both languages" in p for p in problems) and any("lamps" in p and "whole number" in p for p in problems))
        self.assertFalse((self.d / "workspace" / "00-setup" / "luminaires.json").exists())

    def test_the_ids_of_the_catalogue_and_the_size_of_a_change_are_bounded(self):
        r = self.c.put(BASE + "/luminaires", json={"luminaires": {"con espacios y / barra": OWN}})
        self.assertEqual(r.status_code, 422)
        self.assertIn("up to 64", r.json()["detail"]["errors"]["luminaires"][0])
        many = {f"l{i}": OWN for i in range(201)}
        self.assertEqual(self.c.put(BASE + "/luminaires", json={"luminaires": many}).status_code, 422)

    def test_an_id_written_inside_an_entry_does_not_rename_it(self):
        self.assertEqual(self.c.put(BASE + "/luminaires", json={"luminaires": {"mine": {**OWN, "id": "other"}}}).status_code, 200)
        out = self.c.post(BASE + "/calc", json=body()).json()
        self.assertEqual(out["result"]["rooms"][0]["luminaire"]["id"], "mine")

    def test_reset_goes_back_to_what_the_level_below_gives(self):
        self.with_own()
        self.assertIn("mine", [x["id"] for x in self.c.get(BASE + "/options").json()["luminaires"]])
        self.assertEqual(self.c.delete(BASE + "/luminaires").status_code, 200)
        self.assertNotIn("mine", [x["id"] for x in self.c.get(BASE + "/options").json()["luminaires"]])


FLOOD = {"exterior": True, "luminaire": "led_floodlight_100w", "target_lux": 20}
PANEL = {"activity": "education.classroom", "luminaire": "led_panel_600"}
L_SHAPE = {"id": "R1", "name": "En L", "points": [[0, 0], [120, 0], [120, 20], [20, 20], [20, 80], [0, 80]]}


class TestExteriorAndMap(Base):
    def test_an_exterior_area_gets_floodlights_from_its_area_and_target_and_no_positions(self):
        out = self.c.post(BASE + "/calc", json=body(params={"R1": FLOOD})).json()
        area = out["result"]["areas"][0]
        self.assertEqual((area["id"], area["area_m2"], area["method"]), ("R1", 24.0, "floodlight"))
        self.assertGreaterEqual(area["flux"]["luminaires_required"], 1)
        self.assertEqual((out["result"]["rooms"], out["placements"], out["rooms"]), ([], {}, []))
        self.assertEqual(out["areas"], [{"id": "R1", "name": "Aula", "area_m2": 24.0}])
        self.assertTrue(area["verification"]["complies"])

    def test_the_area_of_an_exterior_outline_is_the_real_one_not_the_bounding_box(self):
        out = self.c.post(BASE + "/calc", json=body(rooms=(L_SHAPE,), params={"R1": FLOOD})).json()
        self.assertEqual(out["areas"][0]["area_m2"], 36.0)                                          # 12 x 2 m plus 2 x 6 m of the leg of the L; the bounding box would be 96 m²
        self.assertFalse(any("bounding box" in w for w in out["warnings"]))

    def test_an_exterior_area_needs_a_target_and_the_luminaire_has_to_be_of_its_kind(self):
        no_target = self.c.post(BASE + "/calc", json=body(params={"R1": {**FLOOD, "target_lux": None}})).json()
        self.assertIn("needs its target", no_target["skipped"][0]["reason"])
        interior_in_area = self.c.post(BASE + "/calc", json=body(params={"R1": {**FLOOD, "luminaire": "led_panel_600"}})).json()
        self.assertIn("for interior use", interior_in_area["skipped"][0]["reason"])
        exterior_in_room = self.c.post(BASE + "/calc", json=body(params={"R1": {**PANEL, "luminaire": "led_floodlight_100w"}})).json()
        self.assertIn("for exterior use", exterior_in_room["skipped"][0]["reason"])

    def test_rooms_and_areas_are_calculated_together_and_an_outline_too_large_is_left_out(self):
        pool = {"id": "R2", "name": "Patio", "points": [[0, 100], [60, 100], [60, 160], [0, 160]]}
        both = self.c.post(BASE + "/calc", json=body(rooms=(CLASSROOM, pool), params={"R1": PANEL, "R2": FLOOD})).json()
        self.assertEqual(([r["id"] for r in both["result"]["rooms"]], [a["id"] for a in both["result"]["areas"]]), (["R1"], ["R2"]))
        huge = {"id": "R3", "name": "Enorme", "points": [[0, 0], [100000, 0], [100000, 100000], [0, 100000]]}
        out = self.c.post(BASE + "/calc", json=body(rooms=(huge,), params={"R3": FLOOD})).json()
        self.assertIn("larger than", out["skipped"][0]["reason"])

    def test_the_illuminance_map_is_given_only_when_asked_one_value_per_cell(self):
        plain = self.c.post(BASE + "/calc", json=body(params={"R1": PANEL})).json()
        self.assertEqual(plain["maps"], {})
        out = self.c.post(BASE + "/calc", json=body(params={"R1": PANEL}, options={"map": True})).json()
        m = out["maps"]["R1"]
        self.assertEqual(len(m["values"]), m["nx"] * m["ny"])
        self.assertEqual((m["x0"], m["y0"]), (0.0, 0.0))
        self.assertAlmostEqual(m["nx"] * m["dx"], 60.0, places=2)                                       # the cells cover the room, in view units
        self.assertLess(m["min"], m["max"])

    def test_the_map_of_an_l_shaped_room_leaves_out_the_cells_outside_its_outline(self):
        out = self.c.post(BASE + "/calc", json=body(rooms=(L_SHAPE,), params={"R1": PANEL}, options={"map": True})).json()
        m = out["maps"]["R1"]
        self.assertIn(None, m["values"])
        self.assertTrue(any(v is not None for v in m["values"]))
        last_row = m["values"][-m["nx"]:]                                                               # the bottom of the L is the leg: its right side is outside
        self.assertIsNone(last_row[-1])
        self.assertIsNotNone(last_row[0])

    def test_a_luminaire_without_curve_gives_no_map_and_says_why_in_the_statistics(self):
        self.with_own()
        out = self.c.post(BASE + "/calc", json=body(params={"R1": PARAMS}, options={"map": True})).json()
        self.assertEqual(out["maps"], {})
        self.assertFalse(out["result"]["rooms"][0]["points"]["computed"])


class TestCompanyLevel(Base):
    def setUp(self):
        super().setUp()
        meta = self.d / ".epc" / "project.json"
        write_json(meta, {**read_json(meta, {}), "org": "acme-co"})                   # the project belongs to a company
        patcher = mock.patch.object(identity, "active_org_slug", return_value="acme-co")
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_the_company_level_sits_under_the_project_and_the_nearest_level_wins(self):
        self.assertEqual(self.c.put("/api/data/luminaires", json={"luminaires": {"mine": OWN}}).status_code, 200)
        self.assertEqual(next(x for x in self.c.get(BASE + "/options").json()["luminaires"] if x["id"] == "mine")["level"], "company")
        self.c.put(BASE + "/luminaires", json={"luminaires": {"mine": {**OWN, "lamp_flux_lm": 3000}}})
        mine = next(x for x in self.c.get(BASE + "/options").json()["luminaires"] if x["id"] == "mine")
        self.assertEqual((mine["level"], mine["lamp_flux_lm"]), ("project", 3000))
        view = self.c.get(BASE + "/luminaires").json()
        self.assertEqual(view["inherits"], "company")
        self.assertEqual(view["default"]["mine"]["lamp_flux_lm"], 2400)                                  # what the project sees without its own change
        self.assertEqual(self.c.get("/api/data/luminaires").json()["inherits"], "factory")
        self.assertEqual(self.c.delete("/api/data/luminaires").status_code, 200)
        self.assertEqual(next(x for x in self.c.get(BASE + "/options").json()["luminaires"] if x["id"] == "mine")["lamp_flux_lm"], 3000)       # the project keeps its own


if __name__ == "__main__":
    unittest.main()
