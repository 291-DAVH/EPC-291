"""Receptacles: the study kept with a sheet, when it goes stale, and its report as a document that is offered to be issued."""
import unittest

from epc.core.fsutil import read_json
from epc.modules.engineering import public as engineering
from tests.integration.test_receptacles_api import BASE, OFFICE, SCALE, Base, body

LAYOUT = "/api/projects/ACME/P-1/layout/L0@electrica_BT"
PLAN = "/api/projects/ACME/P-1/layout/L0"                                                          # the Architecture sheet of the level: the only one that sets the scale
STUDY = BASE + "/study/L0@electrica_BT"
PARAMS = {"use": "office", "receptacle": "tug_2x10_t"}


def plan(scale=SCALE):
    return {"discipline": "arquitectura", "scale": scale, "origin": [0, 0], "nodes": [], "lines": [], "circuits": []}


def drawing(params=PARAMS):
    return {"discipline": "electrica_BT", "scale": None, "origin": [0, 0], "nodes": [], "lines": [], "circuits": [], "rooms": [{**OFFICE, "receptacles": params}]}


class Study(Base):
    def setUp(self):
        super().setUp()
        self.d = self.root / "ACME" / "P-1"
        self.assertEqual(self.c.put(PLAN, json=plan()).status_code, 200)
        self.assertEqual(self.c.put(LAYOUT, json=drawing()).status_code, 200)

    def save(self, params=None):
        return self.c.put(STUDY, json=body(params={"R1": params or PARAMS}))


class TestKeeping(Study):
    def test_a_sheet_without_study_says_so(self):
        self.assertEqual(self.c.get(STUDY).json(), {"exists": False})

    def test_the_study_is_kept_with_the_sheet_and_is_good_for_the_rooms_as_they_are(self):
        r = self.save()
        self.assertEqual(r.status_code, 200, r.text)
        s = r.json()
        self.assertTrue(s["exists"] and not s["stale"] and s["report"])
        self.assertEqual((s["report_file"], s["report_error"]), ("RECEPTACLES_L0_electrica_BT.md", ""))
        self.assertEqual(s["result"]["rooms"][0]["required"], 3)
        kept = read_json(self.d / "workspace" / "02-engineering" / "layout" / "L0@electrica_BT" / "src" / "receptacles.json", None)
        self.assertEqual(kept["fingerprint"], s["fingerprint"])
        self.assertEqual(self.c.get(STUDY).json()["fingerprint"], s["fingerprint"])                      # it survives a reload

    def test_a_sheet_that_does_not_exist_and_a_request_with_nothing_to_calculate_are_refused(self):
        self.assertEqual(self.c.put(BASE + "/study/L9", json=body()).status_code, 404)
        self.assertEqual(self.c.put(STUDY, json=body(params={})).status_code, 422)
        self.assertEqual(self.c.get(STUDY).json(), {"exists": False})

    def test_a_second_study_replaces_the_first(self):
        first = self.save().json()
        second = self.save({**PARAMS, "count": 5}).json()
        self.assertNotEqual(first["fingerprint"], second["fingerprint"])
        self.assertEqual(self.c.get(STUDY).json()["result"]["rooms"][0]["required"], 5)


class TestReport(Study):
    def test_the_report_is_a_text_among_the_documents_of_the_project(self):
        self.save()
        text = (self.d / "workspace" / "02-engineering" / "electrical" / "PQ-01" / "docs" / "RECEPTACLES_L0_electrica_BT.md").read_text(encoding="utf-8")
        self.assertIn("Oficina", text)
        self.assertIn("3 / 3", text)
        self.assertIn("typical value, to verify", text)                                                   # what rests on a typical value says so

    def test_it_goes_stale_when_what_a_room_says_changes_and_is_good_again_when_the_study_is_remade(self):
        self.save()
        self.assertEqual(self.c.put(LAYOUT, json=drawing({**PARAMS, "count": 7})).status_code, 200)
        self.assertTrue(self.c.get(STUDY).json()["stale"])
        self.assertEqual(self.c.post(STUDY + "/report").status_code, 409)                                 # a stale study makes no report
        again = self.c.post(STUDY + "/remake?lang=es")
        self.assertEqual(again.status_code, 200, again.text)
        self.assertFalse(again.json()["stale"])
        self.assertEqual(again.json()["result"]["rooms"][0]["required"], 7)

    def test_a_good_study_is_offered_to_be_issued_and_a_stale_one_is_not(self):
        self.save()
        offered = [c["id"] for c in engineering.issuable(self.d)]
        self.assertIn("electrical/PQ-01/docs/RECEPTACLES_L0_electrica_BT.pdf", offered)
        self.c.put(LAYOUT, json=drawing({**PARAMS, "count": 9}))
        self.assertNotIn("electrical/PQ-01/docs/RECEPTACLES_L0_electrica_BT.pdf", [c["id"] for c in engineering.issuable(self.d)])

    def test_the_document_of_a_deliverable_is_named_by_its_kind(self):
        from epc.core.documents import document_of
        got = document_of("RECEPTACLES_L0_electrica_BT", "electrical")
        self.assertEqual((got["doc_type"], got["subject"]), ("receptacles", "L0_electrica_BT"))


if __name__ == "__main__":
    unittest.main()
