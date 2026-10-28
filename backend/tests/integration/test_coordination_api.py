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

    def with_plan(self):
        """The Architecture sheet of the level carries the scale: the other disciplines work with the scale of the plan."""
        arch = {"discipline": "arquitectura", "scale": SCALE, "origin": [0, 0], "nodes": [], "lines": [], "circuits": []}
        self.assertEqual(self.c.put(f"{self.layout}/L0@arquitectura", json=arch).status_code, 200)
        self.assertEqual(self.c.put(f"{self.layout}/L1@arquitectura", json=arch).status_code, 200)

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
        self.with_plan()
        self.draw(SAN_LOW)
        r = self.c.post(f"{self.layout}/L0@sanitaria_cloacas/generate")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertTrue(r.json()["files"]["dxf"].endswith(".dxf"))

    # ---------------------------------------------------------------- clashes
    def test_no_clash_while_the_bodies_are_at_different_heights(self):
        self.draw(SAN_LOW)
        self.assertEqual(self.c.get(f"{self.base}/clashes").json()["clashes"], [])

    def test_a_clash_is_found_named_and_can_be_accepted_with_a_reason(self):
        self.with_plan()
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
        self.with_plan()
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
        self.with_plan()
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
        self.with_plan()
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
        self.with_plan()
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

    # ---------------------------------------------------------------- the disciplines seen together, and what changed
    def test_the_overlay_shows_every_discipline_of_a_level_with_its_clashes(self):
        self.with_plan()
        self.draw()
        o = self.c.get(f"{self.base}/overlay", params={"level": "L0"}).json()
        self.assertEqual({i["discipline"] for i in o["items"]}, {"electrica_BT", "sanitaria_cloacas"})
        self.assertEqual(len(o["clashes"]), 1)
        self.assertEqual(self.c.get(f"{self.base}/overlay", params={"level": "L2"}).json()["items"], [])

    def test_what_changed_since_the_files_were_made_is_listed(self):
        self.with_plan()
        self.assertEqual(self.c.put(f"{self.layout}/L0", json=ELEC).status_code, 200)
        self.assertEqual(self.c.get(f"{self.layout}/L0/changes").json(), {"has_snapshot": False})
        self.assertEqual(self.c.post(f"{self.layout}/L0/generate").status_code, 200)
        self.assertEqual(self.c.get(f"{self.layout}/L0/changes").json()["count"], 0)
        moved = {**ELEC, "nodes": [{**ELEC["nodes"][0], "x": 50}, {"id": "n9", "kind": "LU", "x": 10, "y": 10}], "lines": []}
        self.c.put(f"{self.layout}/L0", json=moved)
        ch = self.c.get(f"{self.layout}/L0/changes").json()
        self.assertEqual([n["id"] for n in ch["nodes"]["added"]], ["n9"])
        self.assertEqual([n["id"] for n in ch["nodes"]["removed"]], ["n2"])
        self.assertEqual([n["id"] for n in ch["nodes"]["changed"]], ["n1"])
        self.assertEqual([n["id"] for n in ch["lines"]["removed"]], ["l1"])
        self.assertEqual((ch["count"], ch["scale_changed"]), (4, False))

    # ---------------------------------------------------------------- the rest of the surface
    def test_settings_members_threads_and_data_can_be_read_changed_and_removed(self):
        self.assertEqual(self.c.get(f"{self.base}/settings").json()["story_height_m"], 3.0)
        self.assertEqual(self.c.put(f"{self.base}/settings", json={"story_height_m": 3.5}).json()["story_height_m"], 3.5)
        self.assertEqual(self.c.put(f"{self.base}/settings", json={"story_height_m": 99}).status_code, 422)
        self.assertEqual(self.c.get(f"{self.base}/members").json(), {})
        self.assertEqual(self.c.post(f"{self.base}/emit", json={"discipline": "a b"}).status_code, 422)
        t = self.c.post(f"{self.base}/threads", json={"kind": "comment", "from_discipline": "electrica_BT", "text": "x"}).json()["id"]
        self.assertEqual(self.c.patch(f"{self.base}/threads/{t}", json={"status": "open"}).status_code, 422)             # nothing changes: say something
        self.assertEqual(self.c.patch(f"{self.base}/threads/T-999", json={"comment": "hi"}).status_code, 404)
        self.assertEqual(self.c.delete(f"{self.base}/threads/{t}").status_code, 204)
        self.assertEqual(self.c.delete(f"{self.base}/threads/{t}").status_code, 404)
        body = {"owner": "mecanica", "consumers": ["electrica_BT"], "tag": "P-1", "field": "power", "value": 5}
        self.assertEqual(self.c.post(f"{self.base}/exchanges", json={**body, "tag": ""}).status_code, 422)
        self.assertEqual(self.c.post(f"{self.base}/exchanges", json={**body, "value": ""}).status_code, 422)
        x = self.c.post(f"{self.base}/exchanges", json=body).json()["id"]
        self.assertEqual(self.c.post(f"{self.base}/exchanges/X-999/take", json={"discipline": "electrica_BT"}).status_code, 404)
        self.assertEqual(self.c.delete(f"{self.base}/exchanges/{x}").status_code, 204)
        self.assertEqual(self.c.delete(f"{self.base}/exchanges/{x}").status_code, 404)

    def test_the_company_rules_belong_to_an_organization(self):
        self.assertEqual(self.c.get("/api/data/clash-rules").status_code, 422)                       # this session works in no organization
        self.assertEqual(self.c.put("/api/data/clash-rules", json={"rules": []}).status_code, 422)

    def test_a_clash_needs_a_known_source_and_a_valid_state(self):
        self.assertEqual(self.c.get(f"{self.base}/clashes?source=nope").status_code, 422)
        self.assertEqual(self.c.put(f"{self.base}/clashes/abc", json={"status": "maybe"}).status_code, 422)
        self.assertEqual(self.c.get(f"{self.layout}/L0/history/zzz").status_code, 404)

    # ---------------------------------------------------------------- the layers of each discipline
    def test_the_layers_in_force_come_grouped_by_discipline_with_what_the_editor_draws_in_them(self):
        url = "/api/projects/ACME/P-1/layout-layers"
        groups = {g["id"]: g for g in self.c.get(url).json()["disciplines"]}
        self.assertEqual([g for g in groups][:4], ["arquitectura", "civil", "mecanica", "electrica"])           # in the order a project is worked
        cable = next(x for x in groups["electrica"]["layers"] if x["name"] == "ELEC-CABLE")
        self.assertEqual((cable["hex"], cable["kinds"][0]["id"], cable["kinds"][0]["type"]), ("#ff0000", "CA", "line"))
        self.assertEqual((groups["hvac"]["profile"], groups["arquitectura"]["profile"]), ("hvac", "arquitectura"))
        self.assertFalse(groups["electrica"]["drawn"])
        self.c.put(f"{self.layout}/L0", json=ELEC)
        self.assertTrue({g["id"]: g for g in self.c.get(url).json()["disciplines"]}["electrica"]["drawn"])
        self.c.put(f"/api/projects/ACME/P-1/drawing-layers", json={"layers": {"plan.HVAC-DUCTO": {"color": 3}}})
        hv = {g["id"]: g for g in self.c.get(url).json()["disciplines"]}["hvac"]
        self.assertEqual(next(x for x in hv["layers"] if x["name"] == "HVAC-DUCTO")["color"], 3)             # the project's own catalog wins

    # ---------------------------------------------------------------- templates
    def test_a_template_is_saved_listed_and_deleted(self):
        url = "/api/projects/ACME/P-1/layout-templates"
        group = {"discipline": "electrica_BT", "nodes": [{"id": "n1", "kind": "LU", "x": 0, "y": 0}], "lines": [{"id": "l1", "kind": "CA", "points": [[0, 0], [10, 0]]}]}
        self.assertEqual(self.c.put(f"{url}/Office tipo", json=group).status_code, 200)
        self.assertEqual([t["name"] for t in self.c.get(url).json()], ["Office tipo"])
        self.assertEqual(self.c.put(f"{url}/empty", json={"discipline": "electrica_BT"}).status_code, 422)
        self.assertEqual(self.c.put(f"{url}/..bad", json=group).status_code, 422)
        self.assertEqual(self.c.delete(f"{url}/Office tipo").status_code, 204)
        self.assertEqual(self.c.get(url).json(), [])
        self.assertEqual(self.c.delete(f"{url}/Office tipo").status_code, 404)


if __name__ == "__main__":
    unittest.main()
