"""The report of a study: the title block of the project, the energy against what the person set, and the plan of the sheet with the luminaires and the illuminance."""
import unittest
from unittest import mock

from epc.modules.lighting import figures, report
from tests.integration.test_lighting_api import BASE, CLASSROOM, PARAMS, SCALE, Base, body
from tests.integration.test_lighting_study import LAYOUT, PLAN, STUDY, drawing, plan

EST = lambda v, c=0.9: {"value": v, "reason": "x", "confidence": c}                  # noqa: E731


def stored():
    room = {"id": "R1", "name": "Aula", "target": EST(300), "factors": {"cu": EST(0.9), "maintenance": EST(0.8)}, "layout": {"installed": 4, "required": 4},
            "verification": {"average_lux": 378.4, "target_lux": 300, "complies": True}, "energy": {"installed_power_w": 144, "power_density_w_m2": 6.0}}
    return {"sheet": "L0", "saved_at": "t", "input": {"rooms": {}}, "result": {"rooms": [room]}, "skipped": [], "warnings": []}


class TestDocument(unittest.TestCase):
    def test_the_title_block_of_the_project_goes_after_the_project_and_only_with_what_it_has(self):
        extras = {"titleblock": {"company": "Ingenieria SA", "client": "Acme", "drawn_by": "", "checked_by": "R. Perez"}}
        rows = report.document(stored(), {"code": "P-1", "name": "Planta"}, "es", {}, False, "1.0", extras)["blocks"][0]["rows"]
        self.assertEqual([r[0] for r in rows][:4], ["Proyecto", "Emisora", "Cliente", "Revisó"])
        self.assertEqual(rows[1], ["Emisora", "Ingenieria SA"])
        plain = report.document(stored(), {}, "en", {}, False, "1.0")["blocks"][0]["rows"]
        self.assertEqual([r[0] for r in plain][:2], ["Project", "Sheet"])

    def test_the_energy_table_is_there_only_when_the_person_gave_a_limit_hours_or_a_tariff(self):
        none = {"R1": {"power_w": 144, "density_w_m2": 6.0, "limit_w_m2": None, "complies": None, "annual_kwh": None, "annual_cost": None}}
        self.assertFalse(any(b.get("text") == "Energy" for b in report.document(stored(), {}, "en", {}, False, "1.0", {"energy_checks": none})["blocks"]))
        full = {"R1": {"power_w": 144, "density_w_m2": 6.0, "limit_w_m2": 8.0, "complies": True, "annual_kwh": 288.0, "annual_cost": 43.2}}
        blocks = report.document(stored(), {}, "en", {}, False, "1.0", {"energy_checks": full})["blocks"]
        table = [b for b in blocks if b["type"] == "table"][1]
        self.assertEqual(table["rows"], [["Aula", "144", "6.0", "8.0", "within the limit", "288", "43.20"]])
        over = {"R1": {**full["R1"], "complies": False}}
        self.assertEqual([b for b in report.document(stored(), {}, "es", {}, False, "1.0", {"energy_checks": over})["blocks"] if b["type"] == "table"][1]["rows"][0][4], "excede el límite")

    def test_the_figure_carries_its_heading_and_comes_before_the_notes(self):
        figure = {"type": "figure", "caption": "c", "bounds": [0, 0, 1, 1], "shapes": []}
        blocks = report.document(stored(), {}, "en", {}, False, "1.0", {"figure": figure})["blocks"]
        placed = next(b for b in blocks if b["type"] == "figure")
        self.assertEqual(placed["title"], "Plan of the sheet with the luminaires")                  # the heading travels with it, so it never stays alone at the foot of a page
        self.assertLess(blocks.index(placed), blocks.index(next(b for b in blocks if b.get("text") == "Assumptions and estimates")))


class TestFigure(unittest.TestCase):
    ROOMS = [{"id": "R1", "name": "Aula", "points": [[0, 0], [60, 0], [60, 40], [0, 40]]}, {"id": "R2", "name": "Pasillo", "points": [[100, 0], [160, 0], [160, 40], [100, 40]]}]
    MAP = {"x0": 0, "y0": 0, "dx": 30, "dy": 20, "nx": 2, "ny": 2, "values": [100, 200, None, 300], "min": 100, "max": 300}

    def calc(self, **extra):
        return {"placements": {"R1": [{"tag": "LU-001", "x": 15, "y": 10, "z_m": 2.6}]}, "emergency_placements": {"R1": [{"tag": "LE-001", "x": 45, "y": 30, "z_m": 2.6}]}, "maps": {"R1": self.MAP}, **extra}

    def test_the_outlines_the_names_the_marks_and_the_cells_of_a_map_are_shapes_of_the_figure(self):
        fig = figures.sheet_figure(self.ROOMS, self.calc(), "Plan", "{low:.0f} to {high:.0f}")
        kinds = [s["s"] for s in fig["shapes"]]
        self.assertEqual((kinds.count("poly"), kinds.count("rect"), kinds.count("circle"), kinds.count("text")), (2, 3, 2, 2))             # the cell without a value is not drawn
        self.assertEqual(sorted(s["text"] for s in fig["shapes"] if s["s"] == "text"), ["Aula", "Pasillo"])
        self.assertEqual(fig["caption"], "Plan · 100 to 300")
        x0, y0, x1, y1 = fig["bounds"]
        self.assertTrue(x0 < 0 and y0 < 0 and x1 > 160 and y1 > 40)                                                                       # a margin around every room
        reds = [s for s in fig["shapes"] if s["s"] == "circle" and s["stroke"] == "#b91c1c"]
        self.assertEqual(len(reds), 1)                                                                                                    # the emergency luminaire is red

    def test_the_colour_goes_from_blue_to_red_over_white(self):
        low, high = figures._hex(0.0), figures._hex(1.0)
        self.assertTrue(int(low[5:7], 16) > int(low[1:3], 16))                                                                            # bluer than red
        self.assertTrue(int(high[1:3], 16) > int(high[5:7], 16))                                                                          # redder than blue
        self.assertTrue(all(int(low[i:i + 2], 16) > 100 for i in (1, 3, 5)))                                                              # washed out, as on the screen

    def test_without_rooms_there_is_no_figure_and_without_a_map_the_caption_is_plain(self):
        self.assertIsNone(figures.sheet_figure([], self.calc(), "Plan", "x"))
        fig = figures.sheet_figure(self.ROOMS, self.calc(maps={}), "Plan", "{low} {high}")
        self.assertEqual(fig["caption"], "Plan")
        self.assertEqual([s["s"] for s in fig["shapes"]].count("rect"), 0)

    def test_a_map_too_large_for_a_page_is_left_out_and_the_rest_stays(self):
        big = {**self.MAP, "values": [100.0] * (figures.MAX_CELLS + 1), "nx": figures.MAX_CELLS + 1, "ny": 1}
        fig = figures.sheet_figure(self.ROOMS, self.calc(maps={"R1": big}), "Plan", "{low} {high}")
        kinds = [s["s"] for s in fig["shapes"]]
        self.assertEqual((kinds.count("rect"), kinds.count("poly"), fig["caption"]), (0, 2, "Plan"))


class TestInTheReport(Base):
    def test_the_report_of_a_sheet_carries_the_plan_the_title_block_and_the_energy(self):
        self.with_own()
        self.assertEqual(self.c.put(PLAN, json=plan()).status_code, 200)
        self.assertEqual(self.c.put(LAYOUT, json=drawing()).status_code, 200)
        asked = body(params={"R1": PARAMS}, options={"hours_default": 2000, "kwh_price": 0.15, "power_limit_w_m2": 20})
        self.assertEqual(self.c.put(STUDY, json=asked).status_code, 200)
        seen = {}
        from epc.core import engine
        original = engine.render_report_pdf

        def spy(doc, dst, timeout=180):
            seen["doc"] = doc
            return original(doc, dst, timeout)

        with mock.patch.object(engine, "render_report_pdf", spy):
            r = self.c.post(STUDY + "/report?lang=es")
        self.assertEqual(r.status_code, 200, r.text)
        blocks = seen["doc"]["blocks"]
        self.assertTrue(any(b["type"] == "figure" and any(s["s"] == "poly" for s in b["shapes"]) for b in blocks))
        self.assertTrue(any(b.get("text") == "Energía" for b in blocks))
        self.assertTrue((self.d / r.json()["path"]).read_bytes().startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
