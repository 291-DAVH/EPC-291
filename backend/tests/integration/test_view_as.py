"""The engineering team can look at the platform as an organization, a member of it or an independent professional: the server applies exactly what that account may do and see."""
import unittest

from tests.integration.test_identity_api import PROJECT, PW, Base

OTHER = {**PROJECT, "client_name": "Beta SA", "client_code": "BETA", "project_code": "B-1"}


class TestViewAs(Base):
    def setup_orgs(self):
        staff = self.staff()
        a, a_slug = self.new_org(staff, "Metal SRL", seats=3, owner="a@metal.com")
        b, b_slug = self.new_org(staff, "Electro SA", seats=2, owner="b@electro.com")
        solo, solo_slug = self.new_org(staff, "Ana Díaz", kind="individual", seats=1, owner="ana@x.com", owner_name="Ana Díaz")
        for c, p in ((a, PROJECT), (b, OTHER)):
            self.assertEqual(c.post("/api/projects", json=p).status_code, 201)
        return staff, a_slug, b_slug, solo_slug

    def view(self, staff, org, role):
        r = staff.post("/api/auth/view-as", json={"org": org, "role": role})
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def test_as_the_owner_of_an_organization(self):
        staff, a, _, _ = self.setup_orgs()
        me = self.view(staff, a, "owner")
        self.assertEqual((me["account_type"], me["org"], me["viewing_as"], me["can_view_as"]), ("corporate_owner", "Metal SRL", "owner", True))
        self.assertEqual([p["project_code"] for p in staff.get("/api/projects").json()], ["P-1"])                       # only that organization's projects
        self.assertEqual(staff.get("/api/projects/BETA/B-1/engineering").status_code, 404)                              # nothing of the other one
        self.assertEqual(staff.get("/api/plugins").status_code, 403)                                                   # nor the platform's internals
        self.assertEqual(staff.get("/api/identity/orgs").status_code, 403)
        self.assertEqual(staff.post("/api/data/clients", json={"id": "ACME", "name": "Acme SA"}).status_code, 201)       # it manages its own data
        self.assertTrue(len(me["organizations"]) >= 3)                                                                 # the selector keeps working while looking as someone else

    def test_as_a_member_of_an_organization(self):
        staff, a, _, _ = self.setup_orgs()
        me = self.view(staff, a, "member")
        self.assertEqual(me["account_type"], "corporate_member")
        self.assertEqual(staff.get("/api/data/clients").status_code, 200)
        self.assertEqual(staff.post("/api/data/clients", json={"id": "X", "name": "X"}).status_code, 403)               # members read the organization's data, they do not manage it
        self.assertEqual(staff.get("/api/app/org").status_code, 403)
        admin = self.view(staff, a, "admin")
        self.assertEqual(admin["account_type"], "corporate_admin")
        self.assertEqual(staff.get("/api/app/org").status_code, 200)

    def test_as_an_independent_professional(self):
        staff, _, _, solo = self.setup_orgs()
        me = self.view(staff, solo, "owner")
        self.assertEqual((me["account_type"], me["org_kind"], me["org"]), ("individual", "individual", "Ana Díaz"))
        self.assertEqual(staff.post("/api/projects", json={**PROJECT, "client_code": "SOLO", "project_code": "S-1"}).status_code, 201)
        self.assertEqual([p["project_code"] for p in staff.get("/api/projects").json()], ["S-1"])
        r = staff.post("/api/auth/view-as", json={"org": solo, "role": "member"})
        self.assertEqual(r.status_code, 422)                                                                           # an organization of one person has no members

    def test_going_back_to_the_team(self):
        staff, a, b, _ = self.setup_orgs()
        self.view(staff, a, "member")
        me = self.view(staff, a, "")
        self.assertEqual((me["account_type"], me["viewing_as"], me["org"]), ("staff", "", "Metal SRL"))                   # still inside the organization, with the team's rights
        self.assertEqual(staff.get("/api/plugins").status_code, 200)
        self.view(staff, a, "member")
        me = staff.post("/api/auth/switch-org", json={"org": b}).json()                                                # choosing another organization ends the look-as
        self.assertEqual((me["account_type"], me["viewing_as"], me["org"]), ("staff", "", "Electro SA"))

    def test_only_the_team_can_do_it_and_every_use_is_recorded(self):
        staff, a_slug, _, _ = self.setup_orgs()
        owner = self.client()
        owner.post("/api/auth/login", json={"email": "a@metal.com", "password": PW})
        for role in ("owner", "member"):
            self.assertEqual(owner.post("/api/auth/view-as", json={"org": a_slug, "role": role}).status_code, 403)
        self.assertEqual(self.client().post("/api/auth/view-as", json={"org": a_slug, "role": "owner"}).status_code, 401)
        self.view(staff, a_slug, "member")
        self.view(staff, a_slug, "")
        staff.post("/api/auth/view-as", json={"org": "nope", "role": "owner"})
        back = self.view(staff, a_slug, "")                                                                             # the team's view again, to read the audit log
        self.assertEqual(back["account_type"], "staff")
        actions = [e["action"] for e in staff.get("/api/identity/audit?limit=100").json()]
        self.assertIn("view_as_started", actions)
        self.assertIn("view_as_ended", actions)
        self.assertEqual(staff.post("/api/auth/view-as", json={"org": "nope", "role": "owner"}).status_code, 404)


if __name__ == "__main__":
    unittest.main()
