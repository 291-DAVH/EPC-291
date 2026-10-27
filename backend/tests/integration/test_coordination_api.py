"""Coordination between disciplines: sheets per discipline on a level, footprints, clashes, issues, threads, data exchanged, rules and who may edit what."""
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

from epc.core.config import settings
from epc.core.errors import Forbidden
from epc.main import create_app
from epc.modules.coordination import service as coordination

SCALE = {"p1": [0, 0], "p2": [100, 0], "distance_m": 10}                       # 10 view units are 1 m
ELEC = {"discipline": "electrica_BT", "scale": SCALE, "origin": [0, 0], "nodes": [{"id": "n1", "kind": "TB", "x": 0, "y": 0}, {"id": "n2", "kind": "CM", "x": 200, "y": 0}],
        "lines": [{"id": "l1", "kind": "BN", "points": [[0, 0], [200, 0]]}]}
SAN_LOW = {"discipline": "sanitaria_cloacas", "scale": SCALE, "origin": [0, 0], "nodes": [], "lines": [{"id": "l1", "kind": "CC", "points": [[100, -100], [100, 100]]}]}      # buried: no clash
SAN_HIGH = {**SAN_LOW, "lines": [{"id": "l1", "kind": "CC", "points": [[100, -100], [100, 100]], "attrs": {"z_m": 2.6}}]}                                                   # at tray height: clash


class TestCoordination(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._old = (settings.projects_dir, settings.role, settings.data_dir)
        settings.projects_dir, settings.role, settings.data_dir = self.root, "admin", self.root / "_data"
        self.c = TestClient(create_app())
        r = self.c.post("/api/projects", json={"client_name": "Acme SA", "client_code": "ACME", "project_code": "P-1", "project_name": "Planta",
                                                "jurisdiction": "AR", "methodology": "pm2", "disciplines": ["electrical"]})
        self.assertEqual(r.status_code, 201, r.text)
        self.layout = "/api/projects/ACME/P-1/layout"
        self.base = "/api/projects/ACME/P-1/coordination"

    def tearDown(self):
        settings.projects_dir, settings.role, settings.data_dir = self._old
        self.tmp.cleanup()

    def draw(self, san=SAN_HIGH):
        self.assertEqual(self.c.put(f"{self.layout}/L0", json=ELEC).status_code, 200)
        r = self.c.put(f"{self.layout}/L0@sanitaria_cloacas", json=san)
        self.assertEqual(r.status_code, 200, r.text)

    # ---------------------------------------------------------------- sheets
    def test_a_level_holds_one_drawing_per_discipline(self):
        self.draw()
        levels = self.c.get(self.layout).json()["levels"]
        self.assertEqual([(x["level"], x["base"], x["discipline"]) for x in levels], [("L0", "L0", "electrica_BT"), ("L0@sanitaria_cloacas", "L0", "sanitaria_cloacas")])
        again = self.c.put(f"{self.layout}/L0", json={**ELEC, "discipline": "sanitaria_cloacas", "nodes": [], "lines": []})
        self.assertEqual(again.status_code, 422)
        wrong = self.c.put(f"{self.layout}/L1@sanitaria_cloacas", json=ELEC)
        self.assertEqual(wrong.status_code, 422)
        self.assertEqual(self.c.put(f"{self.layout}/L0@nada", json=ELEC).status_code, 422)

    def test_a_second_sheet_is_generated_apart_from_the_first(self):
        self.draw(SAN_LOW)
        r = self.c.post(f"{self.layout}/L0@sanitaria_cloacas/generate")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertTrue(r.json()["files"]["dxf"].endswith(".dxf"))

    # ---------------------------------------------------------------- clashes
    def test_no_clash_while_the_bodies_are_at_different_heights(self):
        self.draw(SAN_LOW)
        self.assertEqual(self.c.get(f"{self.base}/clashes").json()["clashes"], [])

    def test_a_clash_is_found_named_and_can_be_accepted_with_a_reason(self):
        self.draw()
        res = self.c.get(f"{self.base}/clashes").json()
        self.assertEqual((res["counts"]["total"], res["counts"]["hard"], res["sources"]), (1, 1, {"electrica_BT": "working", "sanitaria_cloacas": "working"}))
        clash = res["clashes"][0]
        self.assertEqual((clash["type"], clash["status"], clash["a"]["discipline"] != clash["b"]["discipline"]), ("hard", "open", True))
        self.assertIn("BN", {clash["a"]["kind"], clash["b"]["kind"]})
        bad = self.c.put(f"{self.base}/clashes/{clash['id']}", json={"status": "accepted"})
        self.assertEqual(bad.status_code, 422)
        ok = self.c.put(f"{self.base}/clashes/{clash['id']}", json={"status": "accepted", "reason": "steel sleeve"})
        self.assertEqual(ok.status_code, 200)
        after = self.c.get(f"{self.base}/clashes").json()
        self.assertEqual((after["counts"]["open"], after["counts"]["accepted"], after["clashes"][0]["reason"]), (0, 1, "steel sleeve"))
        self.c.put(f"{self.base}/clashes/{clash['id']}", json={"status": "open"})
        self.assertEqual(self.c.get(f"{self.base}/clashes").json()["counts"]["open"], 1)

    def test_a_project_rule_can_ignore_a_pair_of_kinds(self):
        self.draw()
        rule = {"a": "electrica_BT", "b": "sanitaria_cloacas", "kinds_a": ["BN"], "kinds_b": ["CC"], "ignore": True}
        self.assertEqual(self.c.put(f"{self.base}/rules", json={"rules": [rule]}).status_code, 200)
        self.assertEqual(self.c.get(f"{self.base}/clashes").json()["counts"]["total"], 0)
        view = self.c.delete(f"{self.base}/rules").json()
        self.assertEqual(view["own"], [])
        self.assertEqual(self.c.get(f"{self.base}/clashes").json()["counts"]["total"], 1)
        self.assertEqual(self.c.put(f"{self.base}/rules", json={"rules": [{"a": "x y", "clearance_m": -1}]}).status_code, 422)

    # ---------------------------------------------------------------- issuing
    def test_coordination_uses_what_a_discipline_issued_not_its_drafts(self):
        self.draw(SAN_LOW)
        e = self.c.post(f"{self.base}/emit", json={"discipline": "electrica_BT", "note": "first"}).json()
        self.assertEqual((e["rev"], e["elements"], e["new_clashes"]), (1, 3, []))
        self.c.put(f"{self.layout}/L0@sanitaria_cloacas", json=SAN_HIGH)
        self.assertEqual(self.c.get(f"{self.base}/clashes").json()["sources"], {"electrica_BT": "issued", "sanitaria_cloacas": "working"})
        self.assertEqual(self.c.get(f"{self.base}/clashes?source=issued").json()["clashes"], [])               # sanitary has not issued: nothing to compare
        out = self.c.post(f"{self.base}/emit", json={"discipline": "sanitaria_cloacas"}).json()
        self.assertEqual([c["type"] for c in out["new_clashes"]], ["hard"])
        again = self.c.post(f"{self.base}/emit", json={"discipline": "sanitaria_cloacas"}).json()
        self.assertEqual((again["rev"], again["new_clashes"]), (2, []))                                           # only what is new is reported
        emissions = {e["discipline"]: e for e in self.c.get(self.base).json()["emissions"]}
        self.assertEqual((emissions["sanitaria_cloacas"]["rev"], emissions["sanitaria_cloacas"]["issues"]), (2, 2))

    def test_nothing_to_issue_without_a_calibrated_drawing(self):
        self.assertEqual(self.c.post(f"{self.base}/emit", json={"discipline": "electrica_BT"}).status_code, 422)

    def test_the_reference_layer_has_only_the_footprints_of_the_other_disciplines(self):
        self.draw()
        ref = self.c.get(f"{self.base}/reference", params={"discipline": "electrica_BT", "level": "L0"}).json()
        self.assertEqual({i["discipline"] for i in ref["items"]}, {"sanitaria_cloacas"})
        self.assertEqual(set(ref["items"][0]) & {"circuit", "circuits", "attrs"}, set())
        self.assertEqual(self.c.get(f"{self.base}/reference", params={"discipline": "electrica_BT", "level": "L1"}).json()["items"], [])

    # ---------------------------------------------------------------- threads
    def test_a_request_goes_from_one_discipline_to_another_and_is_answered_there(self):
        r = self.c.post(f"{self.base}/threads", json={"kind": "request", "from_discipline": "electrica_BT", "to_discipline": "sanitaria_cloacas", "title": "Move the chamber", "point_m": [3, 4]})
        self.assertEqual(r.status_code, 201, r.text)
        tid = r.json()["id"]
        self.assertEqual(self.c.post(f"{self.base}/threads", json={"kind": "request", "from_discipline": "electrica_BT", "to_discipline": "electrica_BT", "title": "x"}).status_code, 422)
        note = self.c.get(f"{self.base}/notifications", params={"discipline": "sanitaria_cloacas"}).json()
        self.assertEqual([t["id"] for t in note["requests"]], [tid])
        self.assertEqual(self.c.patch(f"{self.base}/threads/{tid}", json={"status": "review", "comment": "looking"}).json()["status"], "review")
        self.assertEqual(self.c.patch(f"{self.base}/threads/{tid}", json={"status": "nonsense"}).status_code, 422)
        done = self.c.patch(f"{self.base}/threads/{tid}", json={"status": "resolved", "comment": "moved"}).json()
        self.assertEqual([h["status"] for h in done["history"]], ["open", "review", "resolved"])
        self.assertEqual(self.c.get(f"{self.base}/notifications", params={"discipline": "sanitaria_cloacas"}).json()["requests"], [])

    def test_a_reserved_space_makes_the_others_keep_out_of_it(self):
        self.assertEqual(self.c.put(f"{self.layout}/L0", json=ELEC).status_code, 200)
        geom = {"points_m": [[10.0, -5.0], [10.0, 5.0]], "width_m": 0.5, "z0": 2.0, "z1": 3.0, "level": "L0"}
        bad = self.c.post(f"{self.base}/threads", json={"kind": "reservation", "from_discipline": "sanitaria_cloacas", "title": "Riser", "geom": {**geom, "z1": 1.0}})
        self.assertEqual(bad.status_code, 422)
        r = self.c.post(f"{self.base}/threads", json={"kind": "reservation", "from_discipline": "sanitaria_cloacas", "title": "Riser", "geom": geom})
        self.assertEqual(r.status_code, 201, r.text)
        res = self.c.get(f"{self.base}/clashes").json()
        self.assertEqual([(c["type"], {c["a"]["kind"], c["b"]["kind"]}) for c in res["clashes"]], [("hard", {"RES", "BN"})])
        self.c.patch(f"{self.base}/threads/{r.json()['id']}", json={"status": "released"})
        self.assertEqual(self.c.get(f"{self.base}/clashes").json()["clashes"], [])

    def test_comments_and_openings_are_validated(self):
        ok = self.c.post(f"{self.base}/threads", json={"kind": "comment", "from_discipline": "electrica_BT", "text": "check this", "sheet": "L0", "level": "L0", "point_m": [1, 2]})
        self.assertEqual(ok.status_code, 201)
        self.assertEqual(self.c.post(f"{self.base}/threads", json={"kind": "comment", "from_discipline": "electrica_BT"}).status_code, 422)
        self.assertEqual(self.c.post(f"{self.base}/threads", json={"kind": "opening", "from_discipline": "electrica_BT", "to_discipline": "civil", "title": "Hole", "geom": {"ancho_m": "wide"}}).status_code, 422)
        self.assertEqual(self.c.get(f"{self.base}/threads", params={"level": "L0"}).json()[0]["id"], ok.json()["id"])

    # ---------------------------------------------------------------- data that crosses
    def test_a_datum_has_one_owner_and_those_who_took_an_old_value_are_told(self):
        body = {"owner": "mecanica", "consumers": ["electrica_BT"], "tag": "P-101", "field": "power", "value": 15, "unit": "kW"}
        x = self.c.post(f"{self.base}/exchanges", json=body).json()
        self.assertEqual((x["version"], x["states"]), (1, {"electrica_BT": "pending"}))
        self.assertEqual(self.c.get(f"{self.base}/notifications", params={"discipline": "electrica_BT"}).json()["count"], 1)
        taken = self.c.post(f"{self.base}/exchanges/{x['id']}/take", json={"discipline": "electrica_BT"}).json()
        self.assertEqual(taken["states"], {"electrica_BT": "delivered"})
        self.assertEqual(self.c.post(f"{self.base}/exchanges/{x['id']}/take", json={"discipline": "civil"}).status_code, 422)
        changed = self.c.post(f"{self.base}/exchanges", json={**body, "value": 22}).json()
        self.assertEqual((changed["id"], changed["version"], changed["states"]), (x["id"], 2, {"electrica_BT": "outdated"}))
        same = self.c.post(f"{self.base}/exchanges", json={**body, "value": 22}).json()
        self.assertEqual(same["version"], 2)
        listing = self.c.get(f"{self.base}/exchanges").json()
        self.assertEqual(listing["matrix"], [{"owner": "mecanica", "consumer": "electrica_BT", "delivered": 0, "pending": 0, "outdated": 1, "total": 1}])
        self.assertEqual(self.c.post(f"{self.base}/exchanges", json={**body, "consumers": ["mecanica"]}).status_code, 422)

    # ---------------------------------------------------------------- who edits what
    def test_a_discipline_with_members_is_edited_only_by_them(self):
        self.assertEqual(self.c.put(f"{self.base}/members", json={"members": {"sanitaria_cloacas": ["Ana@Example.com"]}}).json(), {"sanitaria_cloacas": ["ana@example.com"]})
        d = self.root / "ACME" / "P-1"
        with mock.patch.object(coordination.identity, "is_admin", return_value=False), mock.patch.object(coordination.identity, "current_user", return_value={"email": "bob@example.com"}):
            with self.assertRaises(Forbidden):
                coordination.guard(d, "sanitaria_cloacas")
            coordination.guard(d, "electrica_BT")                                             # a discipline without members is open
        with mock.patch.object(coordination.identity, "is_admin", return_value=False), mock.patch.object(coordination.identity, "current_user", return_value={"email": "ana@example.com"}):
            coordination.guard(d, "sanitaria_cloacas")

    # ---------------------------------------------------------------- history
    def test_the_drawing_keeps_earlier_states_that_can_be_restored(self):
        self.assertEqual(self.c.put(f"{self.layout}/L0", json=ELEC).status_code, 200)
        self.assertEqual(self.c.get(f"{self.layout}/L0/history").json(), [])
        self.c.put(f"{self.layout}/L0", json={**ELEC, "nodes": ELEC["nodes"][:1]})
        hist = self.c.get(f"{self.layout}/L0/history").json()
        self.assertEqual((len(hist), hist[0]["nodes"]), (1, 2))
        self.assertEqual([n["id"] for n in self.c.get(f"{self.layout}/L0/history/{hist[0]['id']}").json()["nodes"]], ["n1", "n2"])
        back = self.c.post(f"{self.layout}/L0/history/{hist[0]['id']}/restore").json()
        self.assertEqual(len(back["drawing"]["nodes"]), 2)
        self.assertEqual(self.c.get(f"{self.layout}/L0/history/20000101T000000").status_code, 404)


if __name__ == "__main__":
    unittest.main()
