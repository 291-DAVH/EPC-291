"""An organization (a company, or an independent professional who is an organization of one person) does its own engineering:
its projects, clients, issuing companies and personnel are its own, and nothing of another organization is ever visible."""
import unittest

from tests.integration.test_identity_api import PROJECT, PW, Base

SLD_CIRCUIT = {"tag": "C-01", "description": "ALIMENTADOR", "load": 20, "unit": "A", "destination": "TD-1", "topology": "single", "phase": "3F", "length_m": 20, "kind": "mccb"}
OTHER = {**PROJECT, "client_name": "Beta SA", "client_code": "BETA", "project_code": "B-1"}
PROJECT_ROUTES = ("engineering", "sld", "sld/boards", "sld/memo", "parties", "registers", "reporting", "issuing", "backlog")


class TestOrganizationWorkspace(Base):
    def two_orgs(self):
        staff = self.staff()
        a, a_slug = self.new_org(staff, "Metal SRL", seats=3, owner="a@metal.com")
        b, b_slug = self.new_org(staff, "Electro SA", seats=2, owner="b@electro.com")
        self.assertEqual(a.post("/api/projects", json=PROJECT).status_code, 201)
        self.assertEqual(b.post("/api/projects", json=OTHER).status_code, 201)
        return staff, a, b, a_slug, b_slug

    def test_each_organization_works_only_its_own_projects(self):
        _, a, b, _, _ = self.two_orgs()
        self.assertEqual([p["project_code"] for p in a.get("/api/projects").json()], ["P-1"])
        self.assertEqual([p["project_code"] for p in b.get("/api/projects").json()], ["B-1"])
        for route in PROJECT_ROUTES:
            self.assertNotIn(a.get(f"/api/projects/ACME/P-1/{route}").status_code, (403, 404), route)                    # its own: reachable
            self.assertEqual(b.get(f"/api/projects/ACME/P-1/{route}").status_code, 404, f"another organization's project: {route}")
        self.assertEqual(b.put("/api/projects/ACME/P-1/parties", json={"issuer": ""}).status_code, 404)
        self.assertEqual(b.put("/api/projects/ACME/P-1/sld", json={"board": {"name": "X"}, "circuits": [SLD_CIRCUIT]}).status_code, 404)
        self.assertEqual(b.put("/api/projects/ACME/P-1/wbs", json={"nodes": []}).status_code, 404)
        self.assertEqual(b.put("/api/projects/ACME/P-1/schedule", json={"activities": []}).status_code, 404)
        self.assertEqual(b.put("/api/projects/ACME/P-1/org", json={"org": "electro-sa"}).status_code, 403)            # giving a project to an organization is the platform team's

    def test_clients_issuers_and_personnel_belong_to_the_organization(self):
        staff, a, b, _, _ = self.two_orgs()
        self.assertEqual(a.post("/api/data/clients", json={"id": "ACME", "name": "Acme SA", "tax_id": "30-9-9"}).status_code, 201)
        self.assertEqual(a.post("/api/data/people", json={"name": "D. Villena", "roles": ["designer", "approver"]}).status_code, 201)
        self.assertEqual(b.get("/api/data/clients").json(), [])                                                       # the other organization sees none of them
        self.assertEqual(b.get("/api/data/people").json(), [])
        self.assertEqual(b.post("/api/data/clients", json={"id": "ACME", "name": "Otro Acme"}).status_code, 201)       # the same code is free in another organization
        self.assertEqual([c["name"] for c in a.get("/api/data/clients").json()], ["Acme SA"])
        # a new organization starts with itself as its first issuing company
        self.assertEqual([i["legal_name"] for i in a.get("/api/data/issuers").json()], ["Metal SRL"])
        self.assertEqual([i["legal_name"] for i in b.get("/api/data/issuers").json()], ["Electro SA"])
        # the project resolves its issuer, client and team in the data of the organization that owns it, whoever looks at it
        for who in (a, staff):
            v = who.get("/api/projects/ACME/P-1/parties").json()
            self.assertEqual((v["issuer"]["legal_name"], v["client"]["name"], v["client"]["in_directory"]), ("Metal SRL", "Acme SA", True), who)
        self.assertEqual([p["name"] for p in a.get("/api/projects/ACME/P-1/parties").json()["people"]], ["D. Villena"])
        self.assertEqual(b.get("/api/projects/BETA/B-1/parties").json()["issuer"]["legal_name"], "Electro SA")
        self.assertEqual(b.get("/api/data/logos/organization").status_code, 404)

    def test_the_title_block_uses_the_data_of_the_projects_organization(self):
        _, a, b, _, _ = self.two_orgs()
        a.post("/api/data/clients", json={"id": "ACME", "name": "Acme SA", "tax_id": "30-9-9"})
        a.put("/api/projects/ACME/P-1/parties", json={"team": {"electrical": {"drawn_by": "D. Villena", "checked_by": "M. Sosa", "approved_by": "R. Paz"}}})
        tb = a.get("/api/projects/ACME/P-1/sld").json()["input"]["titleblock"]
        self.assertEqual((tb["company"], tb["client"], tb["client_cuit"], tb["drawn_by"], tb["approved_by"]), ("Metal SRL", "Acme SA", "30-9-9", "D. Villena", "R. Paz"))
        tb_b = b.get("/api/projects/BETA/B-1/sld").json()["input"]["titleblock"]
        self.assertEqual((tb_b["company"], tb_b["drawn_by"]), ("Electro SA", ""))

    def test_the_owner_manages_the_data_and_a_member_only_reads_it(self):
        staff = self.staff()
        owner, _ = self.new_org(staff, "Metal SRL", seats=3, owner="a@metal.com")
        inv = owner.post("/api/app/org/invitations", json={"email": "m@metal.com", "role": "member"}).json()
        member = self.client()
        self.assertEqual(member.post("/api/auth/accept-invitation", json={"token": inv["token"], "name": "Miembro", "password": PW}).status_code, 200)
        self.assertEqual(owner.post("/api/data/clients", json={"id": "ACME", "name": "Acme SA"}).status_code, 201)
        self.assertEqual([c["id"] for c in member.get("/api/data/clients").json()], ["ACME"])
        self.assertEqual(member.post("/api/data/clients", json={"id": "NUEVO", "name": "Nuevo"}).status_code, 403)
        self.assertEqual(member.post("/api/data/people", json={"name": "X"}).status_code, 403)
        self.assertEqual(member.post("/api/projects", json=PROJECT).status_code, 201)                                   # but members do the engineering
        self.assertEqual(member.put("/api/projects/ACME/P-1/parties", json={"team": {"electrical": {"drawn_by": "Miembro"}}}).status_code, 200)

    def test_an_independent_professional_is_an_organization_of_one(self):
        self.staff()
        settings_signup(self)
        solo = self.client()
        r = solo.post("/api/auth/signup", json={"kind": "individual", "name": "Ana Díaz", "email": "ana@x.com", "password": PW})
        self.assertEqual(r.status_code, 201, r.text)
        self.assertEqual(solo.post("/api/projects", json=PROJECT).status_code, 201)
        self.assertEqual([i["legal_name"] for i in solo.get("/api/data/issuers").json()], ["Ana Díaz"])                  # she issues in her own name until she adds companies
        self.assertEqual(solo.post("/api/data/issuers", json={"legal_name": "Empresa X S.A.", "tax_id": "30-1-1"}).status_code, 201)
        self.assertEqual(solo.post("/api/data/issuers", json={"legal_name": "Empresa Y S.R.L."}).status_code, 201)
        v = solo.get("/api/projects/ACME/P-1/parties").json()
        self.assertEqual(sorted(i["legal_name"] for i in v["issuers"]), ["Ana Díaz", "Empresa X S.A.", "Empresa Y S.R.L."])
        iid = next(i["id"] for i in v["issuers"] if i["legal_name"] == "Empresa Y S.R.L.")
        self.assertEqual(solo.put("/api/projects/ACME/P-1/parties", json={"issuer": iid}).json()["issuer"]["legal_name"], "Empresa Y S.R.L.")

    def test_the_raw_file_tree_is_not_for_organizations(self):
        staff, a, b, _, _ = self.two_orgs()
        self.assertEqual(staff.get("/api/projects/ACME/P-1/tree").status_code, 200)
        for who in (a, b):
            self.assertEqual(who.get("/api/projects/ACME/P-1/tree").status_code, 403)

    def test_inspectors_and_auditors_do_not_enter_the_engineering(self):
        staff, a, _, _, slug = self.two_orgs()
        for role in ("inspector", "auditor"):
            self.assertEqual(staff.post("/api/identity/users", json={"email": f"{role}@x.com", "name": role, "password": PW, "platform_role": role}).status_code, 201)
            c = self.client()
            self.assertEqual(c.post("/api/auth/login", json={"email": f"{role}@x.com", "password": PW}).status_code, 200)
            for path in ("/api/projects", "/api/projects/ACME/P-1/engineering", "/api/data/clients"):
                self.assertEqual(c.get(path).status_code, 403, (role, path))


def settings_signup(case):
    from epc.core.config import settings
    settings.signup = "open"


if __name__ == "__main__":
    unittest.main()
