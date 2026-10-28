"""Lighting: the study kept with a sheet, when it goes stale, and its report as a document that is issued."""
import unittest

from epc.core.fsutil import read_json
from tests.integration.test_lighting_api import BASE, CLASSROOM, OWN, PARAMS, SCALE, Base, body

LAYOUT = "/api/projects/ACME/P-1/layout/L0@electrica_BT"
PLAN = "/api/projects/ACME/P-1/layout/L0"                                                          # the Architecture sheet of the level: the only one that sets the scale
STUDY = BASE + "/study/L0@electrica_BT"


def plan(scale=SCALE):
    return {"discipline": "arquitectura", "scale": scale, "origin": [0, 0], "nodes": [], "lines": [], "circuits": []}


def drawing(params=PARAMS, scale=None):
    return {"discipline": "electrica_BT", "scale": scale, "origin": [0, 0], "nodes": [], "lines": [], "circuits": [], "rooms": [{**CLASSROOM, "lighting": params}]}


class Study(Base):
    def setUp(self):
        super().setUp()
        self.with_own()
        self.assertEqual(self.c.put(PLAN, json=plan()).status_code, 200)
        self.assertEqual(self.c.put(LAYOUT, json=drawing()).status_code, 200)

    def save(self):
        return self.c.put(STUDY, json=body())


class TestKeeping(Study):
    def test_a_sheet_without_study_says_so(self):
        self.assertEqual(self.c.get(STUDY).json(), {"exists": False})

    def test_the_study_is_kept_with_the_sheet_and_is_good_for_the_rooms_as_they_are(self):
        r = self.save()
        self.assertEqual(r.status_code, 200, r.text)
        s = r.json()
        self.assertTrue(s["exists"] and not s["stale"] and s["report"])                                      # the report is made with the study
        self.assertEqual((s["report_file"], s["report_error"]), ("LIGHTING_L0_electrica_BT.pdf", ""))
        self.assertEqual(s["result"]["rooms"][0]["id"], "R1")
        self.assertTrue(s["placements"]["R1"])
        kept = read_json(self.d / "workspace" / "02-engineering" / "layout" / "L0@electrica_BT" / "src" / "lighting.json", None)
        self.assertEqual(kept["fingerprint"], s["fingerprint"])
        self.assertEqual(self.c.get(STUDY).json()["fingerprint"], s["fingerprint"])                      # it survives a reload

    def test_a_sheet_that_does_not_exist_and_a_request_with_nothing_to_calculate_are_refused(self):
        self.assertEqual(self.c.put(BASE + "/study/L9", json=body()).status_code, 404)
        self.assertEqual(self.c.put(STUDY, json=body(params={})).status_code, 422)
        self.assertEqual(self.c.get(STUDY).json(), {"exists": False})                                     # nothing was kept

    def test_a_second_study_replaces_the_first(self):
        first = self.save().json()
        second = self.c.put(STUDY, json=body(params={"R1": {**PARAMS, "height_m": 3.2}})).json()
        self.assertNotEqual(first["fingerprint"], second["fingerprint"])
        self.assertEqual(self.c.get(STUDY).json()["fingerprint"], second["fingerprint"])


class TestReportWithTheStudy(Study):
    def test_the_report_is_among_the_files_of_engineering_as_a_pdf_the_moment_the_study_is_kept(self):
        self.save()
        eng = "/api/projects/ACME/P-1/engineering"
        docs = [x for x in self.c.get(eng).json()["documents"] if x["name"].startswith("LIGHTING_")]
        self.assertEqual([(x["kind"], x["ext"], x["discipline"]) for x in docs], [("pdf", ".pdf", "electrical")])
        shown = self.c.get(eng + "/pdf", params={"path": docs[0]["path"]})
        self.assertEqual((shown.status_code, shown.headers["content-type"]), (200, "application/pdf"))
        self.assertTrue(shown.content.startswith(b"%PDF"))

    def test_the_pdf_endpoint_only_serves_pdfs_the_workspace_lists(self):
        eng = "/api/projects/ACME/P-1/engineering/pdf"
        self.assertEqual(self.c.get(eng, params={"path": "../../project.json"}).status_code, 422)
        self.assertEqual(self.c.get(eng, params={"path": "electrical/PQ-01/docs/nope.pdf"}).status_code, 404)
        self.assertEqual(self.c.get(eng, params={"path": "electrical/PQ-01/docs/x.md"}).status_code, 422)

    def test_a_report_that_cannot_be_made_does_not_undo_the_study_and_says_why(self):
        self.c.put(LAYOUT, json=drawing({**PARAMS, "height_m": 3.4}))                                           # the saved sheet no longer says what the request says
        out = self.save().json()
        self.assertTrue(out["exists"])
        self.assertEqual(out["report_file"], "")
        self.assertIn("changed since the study was made", out["report_error"])
        self.assertTrue(self.c.get(STUDY).json()["exists"])


class TestStale(Study):
    def test_it_goes_stale_when_what_a_room_says_changes_and_is_good_again_when_the_study_is_remade(self):
        self.save()
        self.c.put(LAYOUT, json=drawing({**PARAMS, "height_m": 3.4}))
        self.assertTrue(self.c.get(STUDY).json()["stale"])
        self.c.put(STUDY, json=body(params={"R1": {**PARAMS, "height_m": 3.4}}))
        self.assertFalse(self.c.get(STUDY).json()["stale"])

    def test_it_goes_stale_when_the_scale_changes(self):
        self.save()
        self.c.put(PLAN, json=plan({"p1": [0, 0], "p2": [100, 0], "distance_m": 12}))                   # calibrating the plan again
        self.assertTrue(self.c.get(STUDY).json()["stale"])

    def test_it_goes_stale_when_a_luminaire_of_the_catalogue_it_used_changes(self):
        self.save()
        self.c.put(BASE + "/luminaires", json={"luminaires": {"mine": {**OWN, "lamp_flux_lm": 3000}}})
        self.assertTrue(self.c.get(STUDY).json()["stale"])

    def test_it_stays_good_when_the_sheet_changes_in_what_the_study_does_not_read(self):
        self.save()
        self.c.put(LAYOUT, json={**drawing(), "nodes": [{"id": "n1", "kind": "LU", "x": 10, "y": 10}]})
        self.assertFalse(self.c.get(STUDY).json()["stale"])

    def test_a_room_with_something_the_study_cannot_read_makes_it_stale_instead_of_failing(self):
        self.save()
        self.c.put(LAYOUT, json=drawing({**PARAMS, "height_m": -1}))
        self.assertTrue(self.c.get(STUDY).json()["stale"])


class TestReport(Study):
    def test_the_report_of_a_study_is_a_pdf_among_the_documents_and_is_offered_for_issue(self):
        self.save()
        r = self.c.post(STUDY + "/report?lang=es")
        self.assertEqual(r.status_code, 200, r.text)
        pdf = self.d / r.json()["path"]
        self.assertTrue(pdf.read_bytes().startswith(b"%PDF"))
        self.assertTrue(self.c.get(STUDY).json()["report"])
        offered = [c for c in self.c.get("/api/projects/ACME/P-1/issuing").json()["candidates"] if c["name"].startswith("LIGHTING_")]
        self.assertEqual([(c["kind"], c["formats"]) for c in offered], [("document", ["pdf"])])

    def test_a_stale_study_has_no_report_and_a_sheet_without_study_neither(self):
        self.assertEqual(self.c.post(STUDY + "/report").status_code, 404)
        self.save()
        self.c.put(LAYOUT, json=drawing({**PARAMS, "height_m": 3.4}))
        r = self.c.post(STUDY + "/report")
        self.assertEqual(r.status_code, 409, r.text)


class TestExterior(Study):
    FLOOD = {"exterior": True, "luminaire": "led_floodlight_100w", "target_lux": 20}

    def test_a_study_of_an_exterior_area_is_kept_and_its_report_has_the_floodlights(self):
        self.c.put(LAYOUT, json=drawing(self.FLOOD))
        s = self.c.put(STUDY, json=body(params={"R1": self.FLOOD})).json()
        self.assertEqual([a["id"] for a in s["result"]["areas"]], ["R1"])
        self.assertEqual(s["areas"][0]["area_m2"], 24.0)
        self.assertFalse(self.c.get(STUDY).json()["stale"])
        r = self.c.post(STUDY + "/report?lang=en")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertTrue((self.d / r.json()["path"]).read_bytes().startswith(b"%PDF"))


class TestEmergencyReport(Study):
    def test_the_emergency_lighting_of_a_room_is_kept_in_the_study_and_listed_in_the_report(self):
        params = {**PARAMS, "emergency_luminaire": "led_emergency_3w"}
        self.c.put(LAYOUT, json=drawing(params))
        s = self.c.put(STUDY, json=body(params={"R1": params})).json()
        self.assertEqual([e["id"] for e in s["result"]["emergency"]], ["R1"])
        self.assertFalse(self.c.get(STUDY).json()["stale"])
        r = self.c.post(STUDY + "/report?lang=es")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertTrue((self.d / r.json()["path"]).read_bytes().startswith(b"%PDF"))

    def test_the_report_document_lists_the_emergency_rooms_and_marks_the_criteria_that_were_assumed(self):
        from epc_lighting.config import PARAMS as ENGINE
        from epc.modules.lighting import report
        est = lambda v, c: {"value": v, "reason": "x", "confidence": c}                                      # noqa: E731
        room = {"id": "R1", "name": "Aula", "target": est(300, 0.9), "factors": {"cu": est(0.9, 0.9), "maintenance": est(0.8, 0.9)},
                "layout": {"installed": 4, "required": 4}, "verification": {"average_lux": 378.4, "target_lux": 300, "complies": True}, "energy": {"installed_power_w": 144, "power_density_w_m2": 6.0}}
        em = {"id": "R1", "name": "Aula", "luminaire": {"name": "LED emergency"}, "layout": {"installed": 2}, "criteria": {"min_lux": est(ENGINE["emergency"]["antipanic_e_min_lux"], 0.5), "max_over_min": est(40, 0.5)},
              "verification": {"min_lux": 0.6, "max_over_min": 12.0, "complies": True}, "routes": [{"complies": True}, {"complies": False}]}
        stored = {"sheet": "L0", "saved_at": "t", "input": {"rooms": {"R1": {"emergency_luminaire": "mine"}}}, "result": {"rooms": [room], "emergency": [em]}, "skipped": [], "warnings": []}
        doc = report.document(stored, {}, "en", {"mine": "Own 3 W"}, False, "1.0")
        table = [b for b in doc["blocks"] if b["type"] == "table"][1]
        self.assertEqual(table["rows"][0], ["Aula", "Own 3 W", "2", "0.60", "12.0", "meets", "1 / 2"])
        notes = [line for b in doc["blocks"] if b["type"] == "bullets" for line in b["items"]]
        self.assertEqual(sum("[confirm]" in line for line in notes), 2)                                      # the minimum illuminance and the ratio were not given


class TestDocument(unittest.TestCase):
    def test_the_texts_are_in_the_language_asked_and_what_was_estimated_with_little_confidence_is_marked(self):
        from epc.modules.lighting import report
        est = lambda v, c: {"value": v, "reason": "x", "confidence": c}                                      # noqa: E731
        room = {"id": "R1", "name": "Aula", "target": est(300, 0.9), "factors": {"cu": est(0.5, 0.3), "maintenance": est(0.8, 0.9)},
                "layout": {"installed": 4, "required": 4}, "verification": {"average_lux": 378.4, "target_lux": 300, "complies": True}, "energy": {"installed_power_w": 144, "power_density_w_m2": 6.0}}
        stored = {"sheet": "L0", "saved_at": "2026-01-01 10:00", "saved_by": "a@b.c", "input": {"rooms": {"R1": {"activity": "education.classroom", "luminaire": "mine"}}},
                  "result": {"rooms": [room]}, "skipped": [{"id": "R2", "name": "Pasillo", "reason": "no luminaire chosen"}], "warnings": ["w1"]}
        es = report.document(stored, {"code": "P-1", "name": "Planta"}, "es", {"mine": "Doble 2400"}, True, "1.0")
        self.assertEqual(es["title"], "Memoria de cálculo de iluminación")
        table = next(b for b in es["blocks"] if b["type"] == "table")
        self.assertEqual(table["rows"][0], ["Aula", "education.classroom", "Doble 2400", "4 / 4", "378", "300", "cumple", "6.0"])
        bullets = next(b for b in es["blocks"] if b["type"] == "bullets")["items"]
        self.assertEqual(len(bullets), 2)                                                                     # the target, and the factor that was not sure
        self.assertIn("[confirmar]", bullets[1])
        self.assertTrue(any("valores típicos" in b.get("text", "") for b in es["blocks"]))
        self.assertEqual(report.document(stored, {}, "en", {}, False, "1.0")["title"], "Lighting calculation report")
        stored["result"]["areas"] = [{"id": "A1", "name": "Patio", "area_m2": 40.0, "target": est(20, 0.9), "factors": {"beam_utilisation": est(0.75, 0.4)}, "flux": {"luminaires_required": 3},
                                      "verification": {"average_lux": 24.0, "target_lux": 20, "complies": True}, "energy": {"installed_power_w": 300}}]
        with_area = report.document(stored, {}, "en", {}, False, "1.0")
        areas = [b for b in with_area["blocks"] if b["type"] == "table"][1]
        self.assertEqual(areas["rows"][0], ["Patio", "–", "40", "3", "24", "20", "meets", "300"])
        self.assertTrue(any("beam utilisation" in line and "[confirm]" in line for b in with_area["blocks"] if b["type"] == "bullets" for line in b["items"]))


if __name__ == "__main__":
    unittest.main()
