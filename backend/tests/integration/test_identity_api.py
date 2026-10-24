"""Accounts, sessions, organizations (individual and company subscriptions) and tenant isolation (US-0018) with EPC_AUTH=required."""
import json
import os
import tempfile
import unittest
from pathlib import Path

import sqlalchemy as sa
from fastapi.testclient import TestClient

from epc.core import db
from epc.core.config import settings
from epc.main import create_app
from epc.modules.identity import cli, models, service

PW = "correct-horse-1"
PROJECT = {"client_name": "Acme SA", "client_code": "ACME", "project_code": "P-1", "project_name": "Planta", "jurisdiction": "AR",
           "methodology": "pm2", "disciplines": ["electrical"]}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._old = (settings.projects_dir, settings.role, settings.auth, settings.database_url, settings.signup, settings.data_dir)
        settings.projects_dir, settings.role, settings.auth, settings.signup = self.root / "projects", "user", "required", "closed"
        # EPC_TEST_DATABASE_URL runs the same tests on another engine (CI uses PostgreSQL); its account tables are emptied first
        settings.database_url = os.environ.get("EPC_TEST_DATABASE_URL") or "sqlite:///" + (self.root / "epc.db").as_posix()
        settings.data_dir = self.root / "data"
        db.dispose()
        if os.environ.get("EPC_TEST_DATABASE_URL"):
            db._migrate(settings.database_url)                    # only SQLite is migrated automatically
            with db.engine().begin() as cx:
                for table in ("sessions", "invitations", "user_assignments", "audit_log", "identities", "memberships", "users", "organizations"):
                    cx.execute(sa.text(f"DELETE FROM {table}"))
        service.reset_throttle()
        self.app = create_app()
        self.clients = []

    def tearDown(self):
        for c in self.clients:
            c.close()
        db.dispose()
        settings.projects_dir, settings.role, settings.auth, settings.database_url, settings.signup, settings.data_dir = self._old
        self.tmp.cleanup()

    def client(self):
        c = TestClient(self.app)
        self.clients.append(c)
        return c

    def staff(self):
        service.bootstrap_admin("staff@office.com", "Office Staff", PW)
        c = self.client()
        self.assertEqual(c.post("/api/auth/login", json={"email": "staff@office.com", "password": PW}).status_code, 200)
        return c

    def new_org(self, staff, name, kind="company", seats=3, owner="owner@x.com", owner_name="Owner"):
        """Staff creates the organization; its owner accepts the invitation. Returns (client of the owner, slug)."""
        r = staff.post("/api/identity/orgs", json={"name": name, "kind": kind, "seats": seats, "owner_email": owner})
        self.assertEqual(r.status_code, 201, r.text)
        c = self.client()
        a = c.post("/api/auth/accept-invitation", json={"token": r.json()["invitation"]["token"], "name": owner_name, "password": PW})
        self.assertEqual(a.status_code, 200, a.text)
        return c, r.json()["org"]["slug"]


class TestAccess(Base):
    def test_anonymous_reaches_only_the_sign_in_surface(self):
        c = self.client()
        self.assertEqual(c.get("/api/health").status_code, 200)
        me = c.get("/api/me").json()
        self.assertEqual((me["auth"], me["authenticated"], me["role"]), ("required", False, "user"))
        for path in ("/api/app/portfolio", "/api/projects/options", "/api/plugins", "/api/app/org"):
            self.assertEqual(c.get(path).status_code, 401, path)
        self.assertEqual(c.post("/api/projects", json=PROJECT).status_code, 401)
        self.assertEqual(c.post("/api/auth/logout").status_code, 401)

    def test_login_logout_and_bearer(self):
        staff = self.staff()
        me = staff.get("/api/me").json()
        self.assertEqual((me["authenticated"], me["role"], me["email"]), (True, "admin", "staff@office.com"))
        self.assertEqual(staff.get("/api/plugins").status_code, 200)
        token = staff.cookies.get("epc_session")
        self.assertTrue(token)
        bare = self.client()
        self.assertEqual(bare.get("/api/me", headers={"Authorization": f"Bearer {token}"}).json()["authenticated"], True)
        self.assertEqual(staff.post("/api/auth/logout").status_code, 200)
        self.assertEqual(bare.get("/api/me", headers={"Authorization": f"Bearer {token}"}).json()["authenticated"], False)     # revoked on the server
        self.assertEqual(self.client().get("/api/plugins", headers={"Authorization": f"Bearer {token}"}).status_code, 401)

    def test_wrong_credentials_and_throttle(self):
        service.bootstrap_admin("staff@office.com", "S", PW)
        c = self.client()
        for _ in range(5):
            r = c.post("/api/auth/login", json={"email": "staff@office.com", "password": "nope-nope-nope"})
            self.assertEqual(r.status_code, 401)
        self.assertEqual(c.post("/api/auth/login", json={"email": "staff@office.com", "password": PW}).status_code, 429)      # locked even with the right one
        service.reset_throttle()
        self.assertEqual(c.post("/api/auth/login", json={"email": "nobody@office.com", "password": PW}).status_code, 401)       # unknown = same answer
        self.assertEqual(c.post("/api/auth/login", json={"email": "staff@office.com", "password": PW}).status_code, 200)

    def test_passwords_are_hashed_and_sessions_stored_as_hashes(self):
        c = self.staff()
        token = c.cookies.get("epc_session")
        with db.engine().connect() as cx:
            ph = cx.execute(sa.select(models.users.c.password_hash)).scalar()
            th = cx.execute(sa.select(models.sessions.c.token_hash)).scalar()
        self.assertTrue(ph.startswith("scrypt$"))
        self.assertNotIn(PW, ph)
        self.assertNotEqual(th, token)
        self.assertEqual(th, service.token_hash(token))

    def test_expired_session_is_refused(self):
        c = self.staff()
        with db.engine().begin() as cx:
            cx.execute(sa.update(models.sessions).values(expires_at=service.repo.now() - service.dt.timedelta(minutes=1)))
        self.assertEqual(c.get("/api/me").json()["authenticated"], False)

    def test_simulated_mode_is_unchanged(self):
        settings.auth = "simulated"
        c = self.client()
        self.assertEqual(c.get("/api/me").json(), {**c.get("/api/me").json(), "auth": "simulated", "authenticated": True, "role": "user"})
        self.assertEqual(c.get("/api/plugins").status_code, 403)
        settings.role = "admin"
        self.assertEqual(c.get("/api/plugins").status_code, 200)

    def test_cli_creates_and_resets_a_staff_account(self):
        import os
        os.environ["EPC_TEST_PW"] = PW
        try:
            self.assertEqual(cli.main(["create-admin", "--email", "boss@office.com", "--name", "Boss", "--password-env", "EPC_TEST_PW"]), 0)
            os.environ["EPC_TEST_PW"] = "short"
            self.assertEqual(cli.main(["create-admin", "--email", "boss@office.com", "--password-env", "EPC_TEST_PW"]), 1)
        finally:
            os.environ.pop("EPC_TEST_PW", None)
        self.assertEqual(self.client().post("/api/auth/login", json={"email": "boss@office.com", "password": PW}).status_code, 200)

    def test_models_match_the_migrations(self):
        db.engine()
        insp = sa.inspect(db.engine())
        for t in models.metadata.sorted_tables:
            self.assertEqual({c["name"] for c in insp.get_columns(t.name)}, {c.name for c in t.columns}, t.name)


class TestSignup(Base):
    def test_closed_by_default(self):
        r = self.client().post("/api/auth/signup", json={"kind": "individual", "name": "Ana", "email": "ana@x.com", "password": PW})
        self.assertEqual(r.status_code, 403)

    def test_individual_and_company_accounts(self):
        settings.signup = "open"
        self.assertTrue(self.client().get("/api/me").json()["signup"])
        ana = self.client()
        r = ana.post("/api/auth/signup", json={"kind": "individual", "name": "Ana Díaz", "email": "Ana@X.com", "password": PW})
        self.assertEqual(r.status_code, 201, r.text)
        me = ana.get("/api/me").json()
        self.assertEqual((me["org_kind"], me["org_role"], me["org"], me["role"], me["email"]), ("individual", "owner", "Ana Díaz", "user", "ana@x.com"))
        self.assertEqual(ana.get("/api/app/org").json()["seats"], 1)
        self.assertEqual(ana.post("/api/app/org/invitations", json={"email": "b@x.com"}).status_code, 409)       # one seat: no group
        corp = self.client()
        r = corp.post("/api/auth/signup", json={"kind": "company", "org_name": "Metal SRL", "name": "Raúl", "email": "raul@metal.com", "password": PW})
        self.assertEqual(r.status_code, 201, r.text)
        self.assertEqual((corp.get("/api/me").json()["org_kind"], corp.get("/api/app/org").json()["seats"]), ("company", service.COMPANY_SEATS))

    def test_validation(self):
        settings.signup = "open"
        c = self.client()
        base = {"kind": "individual", "name": "Ana", "email": "ana@x.com", "password": PW}
        for patch, field in (({"password": "short"}, "password"), ({"email": "nope"}, "email"), ({"kind": "group"}, "kind"), ({"name": " "}, "name"),
                             ({"kind": "company", "org_name": ""}, "org_name")):
            r = c.post("/api/auth/signup", json={**base, **patch})
            self.assertEqual(r.status_code, 422, patch)
            self.assertIn(field, r.json()["detail"]["errors"])
        self.assertEqual(c.post("/api/auth/signup", json=base).status_code, 201)
        self.assertEqual(self.client().post("/api/auth/signup", json=base).status_code, 409)                      # email already registered


class TestOrganizations(Base):
    def test_company_is_a_group_with_seats(self):
        staff = self.staff()
        owner, slug = self.new_org(staff, "Metal SRL", seats=2)
        me = owner.get("/api/me").json()
        self.assertEqual((me["org"], me["org_kind"], me["org_role"], me["role"]), ("Metal SRL", "company", "owner", "user"))
        org = owner.get("/api/app/org").json()
        self.assertEqual((org["seats"], org["seats_used"], [m["email"] for m in org["members"]]), (2, 1, ["owner@x.com"]))

        inv = owner.post("/api/app/org/invitations", json={"email": "ana@x.com", "role": "member"})
        self.assertEqual(inv.status_code, 201, inv.text)
        self.assertEqual(owner.get("/api/app/org").json()["seats_pending"], 1)
        self.assertEqual(owner.post("/api/app/org/invitations", json={"email": "bob@x.com"}).status_code, 409)       # the pending invitation holds the seat
        self.assertEqual(owner.post("/api/app/org/invitations", json={"email": "bad"}).status_code, 422)

        ana = self.client()
        info = ana.post("/api/auth/invitation", json={"token": inv.json()["token"]}).json()
        self.assertEqual((info["email"], info["org"], info["existing_account"]), ("ana@x.com", "Metal SRL", False))
        r = ana.post("/api/auth/accept-invitation", json={"token": inv.json()["token"], "name": "Ana", "password": PW})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(ana.get("/api/me").json()["org_role"], "member")
        self.assertEqual(ana.get("/api/app/org").status_code, 403)                                               # members do not manage people
        self.assertEqual(ana.post("/api/app/org/invitations", json={"email": "z@x.com"}).status_code, 403)
        self.assertEqual(self.client().post("/api/auth/accept-invitation", json={"token": inv.json()["token"], "name": "Ana", "password": PW}).status_code, 404)   # single use

    def test_a_group_shares_its_projects(self):
        staff = self.staff()
        owner, _ = self.new_org(staff, "Metal SRL", seats=2)
        self.assertEqual(owner.post("/api/projects", json=PROJECT).status_code, 201)
        inv = owner.post("/api/app/org/invitations", json={"email": "ana@x.com"}).json()
        ana = self.client()
        ana.post("/api/auth/accept-invitation", json={"token": inv["token"], "name": "Ana", "password": PW})
        self.assertEqual([p["name"] for p in ana.get("/api/app/portfolio").json()["projects"]], ["Planta"])
        self.assertEqual(ana.get("/api/app/projects/ACME/P-1").status_code, 200)

    def test_manage_members(self):
        staff = self.staff()
        owner, _ = self.new_org(staff, "Metal SRL", seats=3)
        tokens = [owner.post("/api/app/org/invitations", json={"email": e}).json()["token"] for e in ("a@x.com", "b@x.com")]
        a, b = self.client(), self.client()
        a.post("/api/auth/accept-invitation", json={"token": tokens[0], "name": "A", "password": PW})
        b.post("/api/auth/accept-invitation", json={"token": tokens[1], "name": "B", "password": PW})
        members = {m["email"]: m for m in owner.get("/api/app/org").json()["members"]}
        self.assertEqual(len(members), 3)
        # deactivating cuts the live session at once, and the seat is freed
        self.assertEqual(owner.patch(f"/api/app/org/members/{members['a@x.com']['user_id']}", json={"active": False}).status_code, 200)
        self.assertEqual(a.get("/api/me").json()["authenticated"], False)
        self.assertEqual(self.client().post("/api/auth/login", json={"email": "a@x.com", "password": PW}).status_code, 403)
        # promote b, then the first owner can step down; the last owner cannot
        self.assertEqual(owner.patch(f"/api/app/org/members/{members['b@x.com']['user_id']}", json={"role": "owner"}).status_code, 200)
        oid = members["owner@x.com"]["user_id"]
        self.assertEqual(owner.patch(f"/api/app/org/members/{oid}", json={"role": "member"}).status_code, 200)
        b.cookies.clear()
        self.assertEqual(b.post("/api/auth/login", json={"email": "b@x.com", "password": PW}).status_code, 200)
        self.assertEqual(b.patch(f"/api/app/org/members/{members['b@x.com']['user_id']}", json={"role": "member"}).status_code, 409)
        self.assertEqual(b.delete(f"/api/app/org/members/{members['b@x.com']['user_id']}").status_code, 409)
        self.assertEqual(b.delete(f"/api/app/org/members/{members['a@x.com']['user_id']}").status_code, 200)
        self.assertEqual(b.patch("/api/app/org/members/00000000-0000-0000-0000-000000000000", json={"active": False}).status_code, 404)
        self.assertEqual(len(b.get("/api/app/org").json()["members"]), 2)

    def test_cancel_invitation_and_expiry(self):
        staff = self.staff()
        owner, _ = self.new_org(staff, "Metal SRL", seats=2)
        inv = owner.post("/api/app/org/invitations", json={"email": "ana@x.com"}).json()
        self.assertEqual(owner.delete(f"/api/app/org/invitations/{inv['id']}").status_code, 200)
        self.assertEqual(self.client().post("/api/auth/invitation", json={"token": inv["token"]}).status_code, 404)
        inv = owner.post("/api/app/org/invitations", json={"email": "ana@x.com"}).json()
        with db.engine().begin() as cx:
            cx.execute(sa.update(models.invitations).values(expires_at=service.repo.now() - service.dt.timedelta(days=1)))
        self.assertEqual(self.client().post("/api/auth/accept-invitation", json={"token": inv["token"], "name": "A", "password": PW}).status_code, 404)

    def test_existing_account_joins_a_second_organization(self):
        staff = self.staff()
        o1, _ = self.new_org(staff, "Alfa SRL", seats=2, owner="o1@x.com")
        o2, _ = self.new_org(staff, "Beta SRL", seats=2, owner="o2@x.com")
        inv = o2.post("/api/app/org/invitations", json={"email": "o1@x.com"}).json()
        c = self.client()
        self.assertEqual(c.post("/api/auth/invitation", json={"token": inv["token"]}).json()["existing_account"], True)
        self.assertEqual(c.post("/api/auth/accept-invitation", json={"token": inv["token"], "password": "wrong-wrong-1"}).status_code, 401)
        self.assertEqual(c.post("/api/auth/accept-invitation", json={"token": inv["token"], "password": PW}).status_code, 200)
        self.assertEqual(c.get("/api/me").json()["org"], "Beta SRL")
        other = self.client()
        self.assertEqual(other.post("/api/auth/login", json={"email": "o1@x.com", "password": PW}).status_code, 200)
        self.assertEqual(other.get("/api/me").json()["org"], "Alfa SRL")                                           # first membership by default
        pick = self.client()
        pick.post("/api/auth/login", json={"email": "o1@x.com", "password": PW, "org": "beta-srl"})
        self.assertEqual(pick.get("/api/me").json()["org"], "Beta SRL")

    def test_the_account_type_is_recognized_from_email_and_password_alone(self):
        staff = self.staff()
        self.assertEqual(self.client().get("/api/me").json()["account_type"], "")
        me = staff.get("/api/me").json()
        self.assertEqual((me["account_type"], me["landing"]), ("staff", "/"))
        admin, _ = self.new_org(staff, "Metal SRL", seats=3, owner="boss@metal.com")
        self.assertEqual(admin.get("/api/me").json()["account_type"], "corporate_owner")
        inv = admin.post("/api/app/org/invitations", json={"email": "ana@metal.com"}).json()
        member = self.client()
        member.post("/api/auth/accept-invitation", json={"token": inv["token"], "name": "Ana", "password": PW})
        self.assertEqual(member.get("/api/me").json()["account_type"], "corporate_member")
        settings.signup = "open"
        solo = self.client()
        solo.post("/api/auth/signup", json={"kind": "individual", "name": "Luis", "email": "luis@x.com", "password": PW})
        self.assertEqual(solo.get("/api/me").json()["account_type"], "individual")
        staff.post("/api/identity/users", json={"email": "rev@x.com", "name": "Rev", "password": PW, "platform_role": "standards"})
        rev = self.client()
        r = rev.post("/api/auth/login", json={"email": "rev@x.com", "password": PW})           # the same form for everyone: nothing else is asked
        self.assertEqual((r.json()["account_type"], r.json()["landing"]), ("reviewer", "/norms"))
        # the sign-in answer already says where the person goes, and the owner link for the customer app is included
        self.assertEqual(solo.post("/api/auth/login", json={"email": "luis@x.com", "password": PW}).json()["landing"], "/")
        self.assertEqual(solo.get("/api/me").json()["app_url"], settings.public_url)

    def test_a_person_in_several_organizations_switches_without_signing_in_again(self):
        staff = self.staff()
        o1, _ = self.new_org(staff, "Alfa SRL", seats=2, owner="p@x.com")
        o2, slug2 = self.new_org(staff, "Beta SRL", seats=2, owner="q@x.com")
        self.assertEqual(o1.post("/api/projects", json=PROJECT).status_code, 201)
        inv = o2.post("/api/app/org/invitations", json={"email": "p@x.com"}).json()
        c = self.client()
        c.post("/api/auth/accept-invitation", json={"token": inv["token"], "password": PW})
        c.cookies.clear()
        c.post("/api/auth/login", json={"email": "p@x.com", "password": PW})
        me = c.get("/api/me").json()
        self.assertEqual((me["org"], [(o["slug"], o["role"], o["current"]) for o in me["organizations"]]), ("Alfa SRL", [("alfa-srl", "owner", True), ("beta-srl", "member", False)]))
        self.assertEqual(len(c.get("/api/app/portfolio").json()["projects"]), 1)
        r = c.post("/api/auth/switch-org", json={"org": "beta-srl"})
        self.assertEqual((r.status_code, r.json()["org"], r.json()["account_type"]), (200, "Beta SRL", "corporate_member"))
        self.assertEqual(c.get("/api/app/portfolio").json()["projects"], [])                        # Beta's projects, not Alfa's
        self.assertEqual(c.get("/api/app/org").status_code, 403)                                      # only a member there
        self.assertEqual(c.post("/api/auth/switch-org", json={"org": "alfa-srl"}).json()["account_type"], "corporate_owner")
        self.assertEqual(c.post("/api/auth/switch-org", json={"org": "no-existe"}).status_code, 404)
        self.assertEqual(o2.post("/api/auth/switch-org", json={"org": "alfa-srl"}).status_code, 404)   # not a member of that one
        self.assertEqual(staff.post("/api/auth/switch-org", json={"org": "alfa-srl"}).status_code, 200)       # the engineering team may enter any organization (TestExpertStaff)
        staff.patch("/api/identity/orgs/beta-srl", json={"active": False})
        self.assertEqual(c.post("/api/auth/switch-org", json={"org": "beta-srl"}).status_code, 404)    # a suspended organization is not selectable
        self.assertEqual([o["slug"] for o in c.get("/api/me").json()["organizations"]], ["alfa-srl"])

    def test_password_change_revokes_other_sessions(self):
        staff = self.staff()
        owner, _ = self.new_org(staff, "Metal SRL")
        second = self.client()
        second.post("/api/auth/login", json={"email": "owner@x.com", "password": PW})
        self.assertEqual(owner.post("/api/auth/password", json={"current_password": "bad-bad-bad-1", "new_password": "another-pass-22"}).status_code, 422)
        self.assertEqual(owner.post("/api/auth/password", json={"current_password": PW, "new_password": "short"}).status_code, 422)
        self.assertEqual(owner.post("/api/auth/password", json={"current_password": PW, "new_password": "another-pass-22"}).status_code, 200)
        self.assertTrue(owner.get("/api/me").json()["authenticated"])
        self.assertFalse(second.get("/api/me").json()["authenticated"])
        self.assertEqual(self.client().post("/api/auth/login", json={"email": "owner@x.com", "password": PW}).status_code, 401)
        self.assertEqual(self.client().post("/api/auth/login", json={"email": "owner@x.com", "password": "another-pass-22"}).status_code, 200)


class TestPermissionMatrix(Base):
    """Every kind of account against the same list of requests: what is allowed and what is not is data (permissions.py), and the server enforces it."""

    def accounts(self):
        staff = self.staff()
        owner, slug = self.new_org(staff, "Metal SRL", seats=5, owner="owner@m.com")
        out = {"staff": staff, "corporate_owner": owner}
        for email, role, key in (("admin@m.com", "admin", "corporate_admin"), ("member@m.com", "member", "corporate_member")):
            inv = owner.post("/api/app/org/invitations", json={"email": email, "role": role}).json()
            c = self.client()
            self.assertEqual(c.post("/api/auth/accept-invitation", json={"token": inv["token"], "name": role.title(), "password": PW}).status_code, 200)
            out[key] = c
        settings.signup = "open"
        solo = self.client()
        solo.post("/api/auth/signup", json={"kind": "individual", "name": "Solo", "email": "solo@x.com", "password": PW})
        out["individual"] = solo
        for email, role in (("rev@x.com", "standards"), ("insp@x.com", "inspector"), ("aud@x.com", "auditor")):
            self.assertEqual(staff.post("/api/identity/users", json={"email": email, "name": role, "password": PW, "platform_role": role}).status_code, 201)
            c = self.client()
            self.assertEqual(c.post("/api/auth/login", json={"email": email, "password": PW}).status_code, 200)
            out[{"standards": "reviewer"}.get(role, role)] = c
        return out

    def test_each_kind_of_account_reaches_exactly_what_the_matrix_says(self):
        accs = self.accounts()
        everyone_in_the_app = {"staff", "individual", "corporate_owner", "corporate_admin", "corporate_member", "inspector", "auditor"}
        customers = {"staff", "individual", "corporate_owner", "corporate_admin", "corporate_member"}
        managers = {"staff", "individual", "corporate_owner", "corporate_admin"}
        workers = customers                                                     # an organization does its own engineering (inspectors and auditors only review)
        cases = [("get", "/api/projects", workers), ("get", "/api/data/clients", workers), ("post", "/api/data/clients", managers), ("put", "/api/data/people/x", managers),
                 ("get", "/api/data/issuers", workers),
                 ("get", "/api/app/portfolio", everyone_in_the_app), ("get", "/api/projects/options", everyone_in_the_app), ("post", "/api/projects", customers),
                 ("get", "/api/app/org", managers), ("post", "/api/app/org/invitations", managers),
                 ("get", "/api/norms/units", {"staff", "reviewer"}), ("get", "/api/identity/orgs", {"staff"}), ("get", "/api/identity/audit", {"staff"}),
                 ("get", "/api/plugins", {"staff"}), ("get", "/api/rules/standards", {"staff"})]
        for method, path, allowed in cases:
            for kind, c in accs.items():
                if kind == "staff" and path.startswith("/api/app/org"):
                    continue                                                    # the matrix lets staff through, but they belong to no organization to manage
                r = getattr(c, method)(path, json={}) if method in ("post", "put") else c.get(path)
                self.assertEqual(r.status_code != 403, kind in allowed, f"{kind} {method.upper()} {path} -> {r.status_code}")

    def test_me_tells_the_screens_what_to_show(self):
        accs = self.accounts()
        for kind, c in accs.items():
            self.assertEqual(c.get("/api/me").json()["account_type"], kind)
        self.assertEqual(accs["auditor"].get("/api/me").json()["abilities"], {"app": ["read"], "observation": ["read", "write"]})
        self.assertEqual(accs["corporate_member"].get("/api/me").json()["abilities"], {"app": ["read", "write"], "observation": ["read"], "workspace": ["read", "write"], "orgdata": ["read"]})
        self.assertEqual(accs["individual"].get("/api/me").json()["abilities"]["orgdata"], ["read", "write"])
        self.assertIn("norms", accs["reviewer"].get("/api/me").json()["abilities"])
        self.assertEqual(sorted(accs["staff"].get("/api/me").json()["abilities"]), ["app", "console", "identity", "norms", "observation", "org", "orgdata", "workspace"])

    def test_security_headers(self):
        r = self.client().get("/api/health")
        self.assertEqual((r.headers["x-content-type-options"], r.headers["x-frame-options"], r.headers["referrer-policy"]), ("nosniff", "DENY", "same-origin"))
        self.assertEqual(self.client().get("/api/me").headers["cache-control"], "no-store")
        settings.cookie_secure = True
        try:
            self.assertIn("max-age", self.client().get("/api/health").headers["strict-transport-security"])
        finally:
            settings.cookie_secure = False


class TestAuditLog(Base):
    def test_sensitive_actions_are_recorded_without_secrets(self):
        staff = self.staff()
        c = self.client()
        c.post("/api/auth/login", json={"email": "staff@office.com", "password": "wrong-password-1"})
        owner, slug = self.new_org(staff, "Metal SRL", seats=3, owner="o@m.com")
        inv = owner.post("/api/app/org/invitations", json={"email": "a@m.com", "role": "member"}).json()
        a = self.client()
        a.post("/api/auth/accept-invitation", json={"token": inv["token"], "name": "A", "password": PW})
        mid = next(m["user_id"] for m in owner.get("/api/app/org").json()["members"] if m["email"] == "a@m.com")
        owner.patch(f"/api/app/org/members/{mid}", json={"role": "admin"})
        owner.post("/api/auth/password", json={"current_password": PW, "new_password": "another-pass-22"})
        staff.patch(f"/api/identity/orgs/{slug}", json={"seats": 6})
        log = staff.get("/api/identity/audit?limit=200").json()
        actions = [e["action"] for e in log]
        for want in ("login", "login_failed", "organization_created", "invitation_accepted", "invitation_created", "member_updated", "password_changed", "organization_updated"):
            self.assertIn(want, actions)
        failed = next(e for e in log if e["action"] == "login_failed")
        self.assertEqual((failed["target"], failed["actor"]), ("staff@office.com", "staff@office.com"))
        upd = next(e for e in log if e["action"] == "member_updated")
        self.assertEqual((upd["actor"], upd["target"], upd["org"], upd["detail"]["to"]), ("o@m.com", "a@m.com", slug, {"role": "admin"}))
        blob = json.dumps(log)
        for secret in (PW, "another-pass-22", "wrong-password-1", inv["token"]):
            self.assertNotIn(secret, blob)
        self.assertEqual([e["action"] for e in staff.get("/api/identity/audit?action=login_failed").json()], ["login_failed"])
        self.assertTrue(all(e["org"] == slug for e in staff.get(f"/api/identity/audit?org={slug}").json()))
        self.assertEqual(owner.get("/api/identity/audit").status_code, 403)                   # only the platform staff read it


class TestCompanyAdministrator(Base):
    def test_an_administrator_manages_people_but_not_the_owners(self):
        staff = self.staff()
        owner, _ = self.new_org(staff, "Metal SRL", seats=6, owner="o@m.com")
        tok = lambda email, role: owner.post("/api/app/org/invitations", json={"email": email, "role": role}).json()["token"]
        admin, member = self.client(), self.client()
        admin.post("/api/auth/accept-invitation", json={"token": tok("adm@m.com", "admin"), "name": "Adm", "password": PW})
        member.post("/api/auth/accept-invitation", json={"token": tok("mem@m.com", "member"), "name": "Mem", "password": PW})
        self.assertEqual(admin.get("/api/me").json()["account_type"], "corporate_admin")
        people = {m["email"]: m["user_id"] for m in admin.get("/api/app/org").json()["members"]}
        self.assertEqual(len(people), 3)
        self.assertEqual(admin.post("/api/app/org/invitations", json={"email": "x@m.com", "role": "member"}).status_code, 201)
        self.assertEqual(admin.post("/api/app/org/invitations", json={"email": "y@m.com", "role": "admin"}).status_code, 201)
        self.assertEqual(admin.patch(f"/api/app/org/members/{people['mem@m.com']}", json={"role": "admin"}).status_code, 200)
        self.assertEqual(admin.patch(f"/api/app/org/members/{people['mem@m.com']}", json={"role": "member"}).status_code, 200)
        self.assertEqual(admin.post("/api/app/org/invitations", json={"email": "z@m.com", "role": "owner"}).status_code, 403)
        self.assertEqual(admin.patch(f"/api/app/org/members/{people['mem@m.com']}", json={"role": "owner"}).status_code, 403)
        self.assertEqual(admin.patch(f"/api/app/org/members/{people['o@m.com']}", json={"active": False}).status_code, 403)
        self.assertEqual(admin.patch(f"/api/app/org/members/{people['o@m.com']}", json={"role": "member"}).status_code, 403)
        self.assertEqual(admin.delete(f"/api/app/org/members/{people['o@m.com']}").status_code, 403)
        self.assertEqual(member.get("/api/app/org").status_code, 403)
        self.assertEqual(owner.patch(f"/api/app/org/members/{people['adm@m.com']}", json={"role": "owner"}).status_code, 200)
        self.assertEqual(owner.patch(f"/api/app/org/members/{people['o@m.com']}", json={"role": "admin"}).status_code, 200)
        self.assertEqual(owner.patch(f"/api/app/org/members/{people['adm@m.com']}", json={"role": "member"}).status_code, 403)         # the first owner is an administrator now


class TestExpertStaff(Base):
    """One account of the engineering team sees everything and can work inside any organization, without a second login."""

    def test_staff_enters_any_organization_and_leaves_it(self):
        staff = self.staff()
        a, slug_a = self.new_org(staff, "Alfa SRL", seats=3, owner="a@alfa.com")
        b, slug_b = self.new_org(staff, "Beta SRL", seats=3, owner="b@beta.com")
        a.post("/api/projects", json=PROJECT)
        b.post("/api/projects", json={**PROJECT, "client_code": "OTRO"})
        me = staff.get("/api/me").json()
        self.assertEqual((me["account_type"], me["org"], [o["slug"] for o in me["organizations"]]), ("staff", "", [slug_a, slug_b]))
        self.assertEqual(me["console_url"], settings.console_url)
        self.assertEqual(staff.get("/api/app/org").status_code, 403)                                          # outside an organization there is no people page
        self.assertEqual(sorted(p["id"] for p in staff.get("/api/app/portfolio").json()["projects"]), ["ACME/P-1", "OTRO/P-1"])       # but every project is visible
        r = staff.post("/api/auth/switch-org", json={"org": slug_b})
        self.assertEqual((r.status_code, r.json()["org"], r.json()["account_type"]), (200, "Beta SRL", "staff"))
        org = staff.get("/api/app/org").json()                                                                # the people of that organization
        self.assertEqual((org["name"], [m["email"] for m in org["members"]]), ("Beta SRL", ["b@beta.com"]))
        inv = staff.post("/api/app/org/invitations", json={"email": "nuevo@beta.com", "role": "member"})
        self.assertEqual(inv.status_code, 201, inv.text)
        self.assertEqual(len(staff.get("/api/app/portfolio").json()["projects"]), 2)                          # still sees all projects
        self.assertEqual(staff.post("/api/projects", json={**PROJECT, "client_code": "NUEVO"}).status_code, 201)
        self.assertEqual(self.d_org("NUEVO"), slug_b)                                                         # created inside Beta: it belongs to Beta
        staff.post("/api/auth/switch-org", json={"org": slug_a})
        self.assertEqual(staff.get("/api/app/org").json()["name"], "Alfa SRL")
        self.assertEqual(staff.post("/api/auth/switch-org", json={"org": "no-existe"}).status_code, 404)
        left = staff.post("/api/auth/switch-org", json={"org": ""})
        self.assertEqual((left.status_code, left.json()["org"]), (200, ""))
        self.assertEqual(staff.get("/api/app/org").status_code, 403)
        events = [(e["action"], e["actor"], e["target"]) for e in staff.get("/api/identity/audit?limit=100").json() if e["action"].startswith(("organization_entered", "organization_left", "invitation_created"))]
        self.assertIn(("organization_entered", "staff@office.com", slug_b), events)
        self.assertIn(("organization_left", "staff@office.com", ""), events)
        self.assertIn(("invitation_created", "staff@office.com", "nuevo@beta.com"), events)                   # what the expert does is recorded as theirs
        # nobody else gets this power
        self.assertEqual(a.post("/api/auth/switch-org", json={"org": slug_b}).status_code, 404)
        rev = self.client()
        staff.post("/api/identity/users", json={"email": "rev@x.com", "name": "Rev", "password": PW, "platform_role": "standards"})
        rev.post("/api/auth/login", json={"email": "rev@x.com", "password": PW})
        self.assertEqual(rev.post("/api/auth/switch-org", json={"org": slug_a}).status_code, 403)

    def d_org(self, client_code):
        import json
        return json.loads((settings.projects_dir / client_code / "P-1" / ".epc" / "project.json").read_text(encoding="utf-8")).get("org")

    def test_staff_reaches_every_area_with_one_account(self):
        staff = self.staff()
        for path in ("/api/app/portfolio", "/api/norms/units", "/api/identity/orgs", "/api/identity/audit", "/api/plugins", "/api/projects", "/api/rules/standards"):
            self.assertEqual(staff.get(path).status_code, 200, path)
        self.assertEqual(sorted(staff.get("/api/me").json()["abilities"]), ["app", "console", "identity", "norms", "observation", "org", "orgdata", "workspace"])


class TestStaff(Base):
    def test_customers_cannot_reach_staff_endpoints(self):
        staff = self.staff()
        owner, _ = self.new_org(staff, "Metal SRL")
        for method, path in (("get", "/api/identity/orgs"), ("get", "/api/identity/users"), ("post", "/api/identity/orgs"), ("get", "/api/plugins"), ("get", "/api/overview")):
            self.assertEqual(getattr(owner, method)(path).status_code, 403, path)
        self.assertEqual(owner.put("/api/projects/ACME/P-1/org", json={"org": "metal-srl"}).status_code, 403)

    def test_org_administration(self):
        staff = self.staff()
        owner, slug = self.new_org(staff, "Metal SRL", seats=3)
        orgs = {o["slug"]: o for o in staff.get("/api/identity/orgs").json()}
        self.assertEqual((orgs[slug]["members"], orgs[slug]["seats"], orgs[slug]["active"]), (1, 3, True))
        self.assertEqual(staff.patch(f"/api/identity/orgs/{slug}", json={"seats": 10}).json()["seats"], 10)
        self.assertEqual(staff.patch(f"/api/identity/orgs/{slug}", json={"kind": "individual"}).json()["seats"], 1)    # one person: allowed
        self.assertEqual(staff.patch(f"/api/identity/orgs/{slug}", json={"kind": "company", "seats": 0}).status_code, 409)
        self.assertEqual(staff.patch("/api/identity/orgs/nope", json={"seats": 2}).status_code, 404)
        self.assertEqual(staff.post("/api/identity/orgs", json={"name": "X", "kind": "weird", "owner_email": "a@x.com"}).status_code, 422)
        # suspend: live sessions die and nobody can log in
        self.assertEqual(staff.patch(f"/api/identity/orgs/{slug}", json={"active": False}).json()["active"], False)
        self.assertFalse(owner.get("/api/me").json()["authenticated"])
        self.assertEqual(self.client().post("/api/auth/login", json={"email": "owner@x.com", "password": PW}).status_code, 403)
        staff.patch(f"/api/identity/orgs/{slug}", json={"active": True})
        self.assertEqual(self.client().post("/api/auth/login", json={"email": "owner@x.com", "password": PW}).status_code, 200)

    def test_users_and_support_password(self):
        staff = self.staff()
        owner, _ = self.new_org(staff, "Metal SRL")
        users = {u["email"]: u for u in staff.get("/api/identity/users").json()}
        self.assertEqual(users["owner@x.com"]["organizations"], [{"slug": "metal-srl", "name": "Metal SRL", "role": "owner"}])
        uid = users["owner@x.com"]["id"]
        self.assertEqual(staff.put(f"/api/identity/users/{uid}/password", json={"password": "short"}).status_code, 422)
        self.assertEqual(staff.put(f"/api/identity/users/{uid}/password", json={"password": "support-set-99"}).status_code, 200)
        self.assertFalse(owner.get("/api/me").json()["authenticated"])
        self.assertEqual(self.client().post("/api/auth/login", json={"email": "owner@x.com", "password": "support-set-99"}).status_code, 200)
        self.assertEqual(staff.patch(f"/api/identity/users/{uid}", json={"active": False}).status_code, 200)
        self.assertEqual(self.client().post("/api/auth/login", json={"email": "owner@x.com", "password": "support-set-99"}).status_code, 401)
        # the last staff account cannot be removed
        sid = users["staff@office.com"]["id"]
        self.assertEqual(staff.patch(f"/api/identity/users/{sid}", json={"active": False}).status_code, 409)
        self.assertEqual(staff.patch(f"/api/identity/users/{sid}", json={"platform_role": "user"}).status_code, 409)
        self.assertEqual(staff.patch(f"/api/identity/users/{sid}", json={"platform_role": "boss"}).status_code, 422)

    def test_norm_reviewer_account_sees_only_the_norms_area(self):
        staff = self.staff()
        owner, _ = self.new_org(staff, "Metal SRL")
        body = {"email": "Rev@Office.com", "name": "Ing. Revisor", "password": PW, "platform_role": "standards"}
        r = staff.post("/api/identity/users", json=body)
        self.assertEqual((r.status_code, r.json()["platform_role"], r.json()["email"]), (201, "standards", "rev@office.com"))
        self.assertEqual(staff.post("/api/identity/users", json=body).status_code, 409)
        self.assertEqual(staff.post("/api/identity/users", json={**body, "email": "x@office.com", "platform_role": "user"}).status_code, 422)
        self.assertEqual(staff.post("/api/identity/users", json={**body, "email": "y@office.com", "password": "short"}).status_code, 422)
        self.assertEqual(owner.post("/api/identity/users", json={**body, "email": "z@office.com"}).status_code, 403)       # customers cannot create accounts
        rev = self.client()
        self.assertEqual(rev.post("/api/auth/login", json={"email": "rev@office.com", "password": PW}).status_code, 200)
        me = rev.get("/api/me").json()
        self.assertEqual((me["role"], me["org"], me["org_role"]), ("standards", "", ""))
        self.assertEqual(rev.get("/api/norms/units").status_code, 200)
        for path in ("/api/app/portfolio", "/api/projects/options", "/api/plugins", "/api/projects", "/api/identity/orgs", "/api/identity/users", "/api/app/org", "/api/rules/standards"):
            self.assertEqual(rev.get(path).status_code, 403, path)
        self.assertEqual(rev.post("/api/auth/password", json={"current_password": PW, "new_password": "another-pass-22"}).status_code, 200)     # can change their own password
        self.assertEqual(owner.get("/api/norms/units").status_code, 403)                                                   # a customer cannot see the norms area
        uid = next(u["id"] for u in staff.get("/api/identity/users").json() if u["email"] == "rev@office.com")
        self.assertEqual(staff.patch(f"/api/identity/users/{uid}", json={"active": False}).status_code, 200)
        self.assertFalse(rev.get("/api/me").json()["authenticated"])


class TestTenantIsolation(Base):
    def test_a_customer_sees_only_their_own_organization(self):
        staff = self.staff()
        a, slug_a = self.new_org(staff, "Alfa SRL", owner="a@x.com")
        b, _ = self.new_org(staff, "Beta SRL", owner="b@x.com")
        self.assertEqual(a.post("/api/projects", json=PROJECT).status_code, 201)
        self.assertEqual(a.post("/api/app/projects/ACME/P-1/inputs", data={"kind": "document", "title": "t", "text": "x"}).status_code, 201)
        # B cannot see, read, write or guess A's project
        self.assertEqual(b.get("/api/app/portfolio").json()["projects"], [])
        for method, path in (("get", "/api/app/projects/ACME/P-1"), ("get", "/api/app/projects/ACME/P-1/inputs"), ("get", "/api/app/projects/ACME/P-1/requirements"),
                             ("get", "/api/app/projects/ACME/P-1/deliverables"), ("get", "/api/app/projects/ACME/P-1/reports"), ("get", "/api/app/projects/ACME/P-1/plan/wbs")):
            self.assertEqual(getattr(b, method)(path).status_code, 404, path)
        self.assertEqual(b.post("/api/app/projects/ACME/P-1/inputs", data={"kind": "document", "title": "t", "text": "x"}).status_code, 404)
        # B creating the same code does not get A's project (and learns nothing but that the code is taken)
        self.assertEqual(b.post("/api/projects", json=PROJECT).status_code, 409)
        self.assertEqual(b.post("/api/projects", json={**PROJECT, "client_code": "OTRO"}).status_code, 201)
        self.assertEqual([p["id"] for p in b.get("/api/app/portfolio").json()["projects"]], ["OTRO/P-1"])
        self.assertEqual([p["id"] for p in a.get("/api/app/portfolio").json()["projects"]], ["ACME/P-1"])
        # staff see both; the project carries its owner
        ids = sorted(p["id"] for p in staff.get("/api/projects").json())
        self.assertEqual(ids, ["ACME/P-1", "OTRO/P-1"])
        meta = json.loads((settings.projects_dir / "ACME" / "P-1" / ".epc" / "project.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["org"], slug_a)
        # a customer cannot choose another owner
        self.assertEqual(json.loads((settings.projects_dir / "OTRO" / "P-1" / ".epc" / "project.json").read_text(encoding="utf-8"))["org"], "beta-srl")
        c = b.post("/api/projects", json={**PROJECT, "client_code": "TRAMPA", "org": slug_a})
        self.assertEqual(json.loads((settings.projects_dir / "TRAMPA" / "P-1" / ".epc" / "project.json").read_text(encoding="utf-8"))["org"], "beta-srl")
        self.assertEqual(c.status_code, 201)

    def test_projects_without_owner_are_staff_only_until_assigned(self):
        staff = self.staff()
        owner, slug = self.new_org(staff, "Metal SRL")
        self.assertEqual(staff.post("/api/projects", json=PROJECT).status_code, 201)              # staff create with no owner (legacy / office project)
        self.assertEqual(owner.get("/api/app/portfolio").json()["projects"], [])
        self.assertEqual(owner.get("/api/app/projects/ACME/P-1").status_code, 404)
        self.assertEqual(staff.put("/api/projects/ACME/P-1/org", json={"org": "does-not-exist"}).status_code, 422)
        self.assertEqual(staff.put("/api/projects/ACME/P-1/org", json={"org": slug}).status_code, 200)
        self.assertEqual(owner.get("/api/app/projects/ACME/P-1").status_code, 200)
        self.assertEqual(staff.put("/api/projects/ACME/P-1/org", json={"org": ""}).status_code, 200)
        self.assertEqual(owner.get("/api/app/projects/ACME/P-1").status_code, 404)

    def test_staff_can_create_a_project_for_an_organization(self):
        staff = self.staff()
        owner, slug = self.new_org(staff, "Metal SRL")
        self.assertEqual(staff.post("/api/projects", json={**PROJECT, "org": slug}).status_code, 201)
        self.assertEqual(owner.get("/api/app/projects/ACME/P-1").status_code, 200)
        self.assertEqual(staff.post("/api/projects", json={**PROJECT, "client_code": "B", "org": "nope"}).status_code, 422)


if __name__ == "__main__":
    unittest.main()
