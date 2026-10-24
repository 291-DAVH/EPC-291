"""Inspectors and external auditors: they see only the organizations assigned to them, the auditor cannot change anything, observations flow from them to the customer."""
import unittest

from epc.core.config import settings
from tests.integration.test_identity_api import PROJECT, PW, Base


class TestAssignments(Base):
    def world(self):
        """Two customer organizations with a project each, an inspector and an auditor with nothing assigned yet."""
        staff = self.staff()
        a, slug_a = self.new_org(staff, "Alfa SRL", seats=4, owner="a@alfa.com")
        b, slug_b = self.new_org(staff, "Beta SRL", seats=4, owner="b@beta.com")
        self.assertEqual(a.post("/api/projects", json=PROJECT).status_code, 201)                                   # ACME/P-1 belongs to Alfa
        self.assertEqual(b.post("/api/projects", json={**PROJECT, "client_code": "OTRO"}).status_code, 201)         # OTRO/P-1 belongs to Beta
        people = {}
        for key, email in (("inspector", "insp@office.com"), ("auditor", "aud@ext.com")):
            r = staff.post("/api/identity/users", json={"email": email, "name": key.title(), "password": PW, "platform_role": key})
            self.assertEqual(r.status_code, 201, r.text)
            c = self.client()
            self.assertEqual(c.post("/api/auth/login", json={"email": email, "password": PW}).status_code, 200)
            people[key] = (c, r.json()["id"])
        return staff, a, slug_a, b, slug_b, people

    def test_they_see_only_the_organizations_assigned_to_them(self):
        staff, a, slug_a, b, slug_b, people = self.world()
        insp, insp_id = people["inspector"]
        self.assertEqual(insp.get("/api/app/portfolio").json()["projects"], [])                                     # nothing assigned: nothing visible
        self.assertEqual(insp.get("/api/app/projects/ACME/P-1").status_code, 404)
        self.assertEqual(staff.put(f"/api/identity/users/{insp_id}/assignments", json={"orgs": [slug_a]}).json(), [{"slug": slug_a, "name": "Alfa SRL"}])
        self.assertEqual([p["id"] for p in insp.get("/api/app/portfolio").json()["projects"]], ["ACME/P-1"])         # immediately, without signing in again
        self.assertEqual(insp.get("/api/app/projects/ACME/P-1").status_code, 200)
        self.assertEqual(insp.get("/api/app/projects/OTRO/P-1").status_code, 404)                                   # Beta was not assigned
        self.assertEqual(insp.get("/api/me").json()["assigned"], [slug_a])
        staff.put(f"/api/identity/users/{insp_id}/assignments", json={"orgs": [slug_a, slug_b]})
        self.assertEqual(sorted(p["id"] for p in insp.get("/api/app/portfolio").json()["projects"]), ["ACME/P-1", "OTRO/P-1"])
        staff.put(f"/api/identity/users/{insp_id}/assignments", json={"orgs": [slug_b]})
        self.assertEqual(insp.get("/api/app/projects/ACME/P-1").status_code, 404)                                   # revoked
        # a suspended organization drops out of their view
        staff.patch(f"/api/identity/orgs/{slug_b}", json={"active": False})
        self.assertEqual(insp.get("/api/app/portfolio").json()["projects"], [])
        users = {u["email"]: u for u in staff.get("/api/identity/users").json()}
        self.assertEqual([x["slug"] for x in users["insp@office.com"]["assignments"]], [slug_b])
        log = [(e["action"], e["detail"].get("org")) for e in staff.get("/api/identity/audit?limit=100").json() if e["action"].startswith("assignment_")]
        self.assertEqual(set(log), {("assignment_granted", slug_a), ("assignment_granted", slug_b), ("assignment_revoked", slug_a)})

    def test_assignment_rules(self):
        staff, a, slug_a, b, slug_b, people = self.world()
        insp, insp_id = people["inspector"]
        self.assertEqual(a.put(f"/api/identity/users/{insp_id}/assignments", json={"orgs": [slug_a]}).status_code, 403)         # a customer cannot assign
        self.assertEqual(insp.put(f"/api/identity/users/{insp_id}/assignments", json={"orgs": [slug_a]}).status_code, 403)      # nor can the inspector
        self.assertEqual(staff.put(f"/api/identity/users/{insp_id}/assignments", json={"orgs": ["no-existe"]}).status_code, 422)
        owner_id = next(u["id"] for u in staff.get("/api/identity/users").json() if u["email"] == "a@alfa.com")
        self.assertEqual(staff.put(f"/api/identity/users/{owner_id}/assignments", json={"orgs": [slug_a]}).status_code, 422)   # only inspectors and auditors
        staff.put(f"/api/identity/users/{insp_id}/assignments", json={"orgs": [slug_a]})
        staff.patch(f"/api/identity/users/{insp_id}", json={"platform_role": "standards"})                                    # leaves the role: the assignments end
        users = {u["email"]: u for u in staff.get("/api/identity/users").json()}
        self.assertEqual(users["insp@office.com"]["assignments"], [])
        self.assertEqual(users["insp@office.com"]["platform_role"], "standards")
        staff.patch(f"/api/identity/users/{insp_id}", json={"platform_role": "inspector"})
        c = self.client()
        c.post("/api/auth/login", json={"email": "insp@office.com", "password": PW})
        self.assertEqual(c.get("/api/app/portfolio").json()["projects"], [])                                                 # back as inspector with nothing assigned

    def test_the_auditor_reads_but_changes_nothing(self):
        staff, a, slug_a, b, slug_b, people = self.world()
        aud, aud_id = people["auditor"]
        staff.put(f"/api/identity/users/{aud_id}/assignments", json={"orgs": [slug_a]})
        self.assertEqual(aud.get("/api/app/projects/ACME/P-1").status_code, 200)
        for method, path, body in (("post", "/api/projects", PROJECT), ("post", "/api/app/projects/ACME/P-1/inputs", {"kind": "document", "title": "t", "text": "x"}),
                                   ("put", "/api/projects/ACME/P-1/wbs", {"nodes": []}), ("post", "/api/app/org/invitations", {"email": "x@y.com"})):
            self.assertEqual(getattr(aud, method)(path, json=body).status_code, 403, path)
        self.assertEqual(aud.get("/api/norms/units").status_code, 403)
        self.assertEqual(aud.get("/api/identity/users").status_code, 403)

    def test_observations_flow_from_the_inspector_to_the_customer(self):
        staff, a, slug_a, b, slug_b, people = self.world()
        insp, insp_id = people["inspector"]
        aud, aud_id = people["auditor"]
        for uid in (insp_id, aud_id):
            staff.put(f"/api/identity/users/{uid}/assignments", json={"orgs": [slug_a]})
        base = "/api/app/projects/ACME/P-1/observations"
        self.assertEqual(a.post(base, json={"title": "El tablero no tiene rótulo"}).status_code, 403)                     # a customer does not write observations
        r = insp.post(base, json={"title": "El tablero no tiene rótulo", "severity": "major", "description": "Falta el rótulo del TGBT-02", "status": "closed", "response": "x"})
        self.assertEqual(r.status_code, 201, r.text)
        obs = r.json()
        self.assertEqual((obs["id"], obs["status"], obs["response"], obs["created_by"], obs["severity"], obs["type"]), ("OBS-001", "open", "", "Inspector", "major", "inspection"))
        self.assertEqual(insp.post(base, json={"title": "x", "severity": "gravísima"}).status_code, 422)
        self.assertEqual(aud.post(base, json={"title": "Falta evidencia de la puesta a tierra", "type": "audit"}).status_code, 201)
        # the customer reads them and answers, nothing else
        self.assertEqual([o["id"] for o in a.get(base).json()], ["OBS-001", "OBS-002"])
        self.assertEqual(a.patch(f"{base}/OBS-001", json={"title": "otro"}).status_code, 403)
        self.assertEqual(a.patch(f"{base}/OBS-001", json={"status": "closed"}).status_code, 403)
        ok = a.patch(f"{base}/OBS-001", json={"response": "Se colocó el rótulo (foto adjunta)"})
        self.assertEqual((ok.status_code, ok.json()["status"], ok.json()["response"]), (200, "answered", "Se colocó el rótulo (foto adjunta)"))
        # the inspector closes it; after that the customer cannot reopen the conversation
        closed = insp.patch(f"{base}/OBS-001", json={"status": "closed"}).json()
        self.assertEqual((closed["status"], bool(closed["closed_on"])), ("closed", True))
        self.assertEqual(a.patch(f"{base}/OBS-001", json={"response": "otra vez"}).status_code, 409)
        # a plain member of the organization can read but not answer
        inv = a.post("/api/app/org/invitations", json={"email": "m@alfa.com", "role": "member"}).json()
        m = self.client()
        m.post("/api/auth/accept-invitation", json={"token": inv["token"], "name": "Miembro", "password": PW})
        self.assertEqual(len(m.get(base).json()), 2)
        self.assertEqual(m.patch(f"{base}/OBS-002", json={"response": "yo respondo"}).status_code, 403)
        # nobody outside reaches them: another organization, an unassigned inspector
        self.assertEqual(b.get(base).status_code, 404)
        self.assertEqual(insp.get("/api/app/projects/OTRO/P-1/observations").status_code, 404)
        self.assertEqual(insp.post("/api/app/projects/OTRO/P-1/observations", json={"title": "x"}).status_code, 404)
        self.assertEqual(a.patch(f"{base}/OBS-099", json={"response": "x"}).status_code, 404)
        # the history of who wrote what
        h = staff.get(f"/api/projects/ACME/P-1/registers/observation").json()[0]["history"]
        self.assertEqual([x["action"] for x in h], ["created", "updated", "updated"])
        events = [e["action"] for e in staff.get("/api/identity/audit?limit=100").json()]
        self.assertIn("observation_created", events)
        self.assertIn("observation_updated", events)


if __name__ == "__main__":
    unittest.main()
