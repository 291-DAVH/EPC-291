"""The development-only MASTER account and the command that deletes every account."""
import unittest

from epc.core.config import settings
from epc.core.errors import Unauthorized
from epc.modules.identity import cli, service
from epc.modules.identity.models import MASTER_EMAIL
from tests.integration.test_identity_api import PW, Base

MASTER_PW = "dev-master-pass-123"


class Master(Base):
    def setUp(self):
        super().setUp()
        self._old_master = (settings.dev_master_user, settings.dev_master_password, settings.env)
        settings.dev_master_user, settings.dev_master_password, settings.env = "master", MASTER_PW, "dev"

    def tearDown(self):
        settings.dev_master_user, settings.dev_master_password, settings.env = self._old_master
        super().tearDown()

    def master(self, who="master", password=MASTER_PW):
        c = self.client()
        return c, c.post("/api/auth/login", json={"login": who, "password": password})


class TestMasterAccount(Master):
    def test_the_master_reaches_everything_in_development(self):
        for who in ("master", "MASTER", MASTER_EMAIL):
            c, r = self.master(who)
            self.assertEqual((r.status_code, r.json()["account_type"]), (200, "staff"), who)
        c, _ = self.master()
        for path in ("/api/app/portfolio", "/api/norms/units", "/api/identity/orgs", "/api/identity/audit", "/api/plugins", "/api/projects"):
            self.assertEqual(c.get(path).status_code, 200, path)
        # it works inside an organization like any expert staff account
        staff = self.staff()
        staff.post("/api/identity/orgs", json={"name": "Alfa SRL", "kind": "company", "seats": 2, "owner_email": "a@alfa.com"})
        self.assertEqual(c.post("/api/auth/switch-org", json={"org": "alfa-srl"}).json()["org"], "Alfa SRL")

    def test_it_needs_the_password_and_this_machine(self):
        self.assertEqual(self.master(password="wrong-password-1")[1].status_code, 401)
        self.assertEqual(self.master(password="")[1].status_code, 401)
        self.assertEqual(self.master(who="otro")[1].status_code, 401)
        service.reset_throttle()
        with self.assertRaises(Unauthorized):
            service.login("master", MASTER_PW, "", "203.0.113.9")                                         # not from another machine
        service.login("master", MASTER_PW, "", "127.0.0.1")
        settings.dev_master_password = ""                                                                   # without a password in the environment it does not exist
        service.reset_throttle()
        self.assertEqual(self.master()[1].status_code, 401)

    def test_it_is_inert_in_production(self):
        self.assertEqual(self.master()[1].status_code, 200)                                                 # the row exists now
        for env in ("production", "staging", ""):                                                          # only the explicit `dev` environment enables it
            settings.env = env
            service.reset_throttle()
            self.assertEqual(self.master()[1].status_code, 401, env)
            self.assertEqual(self.master(who=MASTER_EMAIL)[1].status_code, 401, env)
            self.assertFalse(service.master_enabled(), env)
        settings.env = "dev"
        settings.dev_master_password = ""
        service.reset_throttle()
        self.assertEqual(self.client().post("/api/auth/login", json={"login": MASTER_EMAIL, "password": ""}).status_code, 401)   # it has no password of its own

    def test_nobody_else_sees_it_and_nobody_can_register_it(self):
        staff = self.staff()
        self.master()
        self.assertEqual([u["email"] for u in staff.get("/api/identity/users").json()], ["staff@office.com"])
        actors = {e["actor"] for e in staff.get("/api/identity/audit?limit=200").json()}
        self.assertNotIn(MASTER_EMAIL, actors)
        settings.signup = "open"
        self.assertEqual(self.client().post("/api/auth/signup", json={"kind": "individual", "name": "X", "email": MASTER_EMAIL, "password": PW}).status_code, 422)
        self.assertEqual(staff.post("/api/identity/users", json={"email": MASTER_EMAIL, "name": "X", "password": PW, "platform_role": "admin"}).status_code, 422)

    def test_it_does_not_count_as_the_last_staff_account(self):
        staff = self.staff()
        self.master()
        uid = next(u["id"] for u in staff.get("/api/identity/users").json() if u["email"] == "staff@office.com")
        self.assertEqual(staff.patch(f"/api/identity/users/{uid}", json={"active": False}).status_code, 409)       # the master does not replace a real administrator


class TestResetAccounts(Master):
    def test_it_deletes_every_account_and_keeps_the_master_usable(self):
        staff = self.staff()
        owner, slug = self.new_org(staff, "Alfa SRL", seats=3, owner="a@alfa.com")
        owner.post("/api/projects", json={"client_name": "Acme SA", "client_code": "ACME", "project_code": "P-1", "project_name": "Planta", "jurisdiction": "AR",
                                           "methodology": "pm2", "disciplines": ["electrical"]})
        self.assertEqual(cli.main(["reset-accounts"]), 1)                                                   # without --yes nothing happens
        self.assertTrue(staff.get("/api/me").json()["authenticated"])
        self.assertEqual(cli.main(["reset-accounts", "--yes"]), 0)
        for who in ("staff@office.com", "a@alfa.com"):
            self.assertEqual(self.client().post("/api/auth/login", json={"login": who, "password": PW}).status_code, 401, who)
        self.assertFalse(staff.get("/api/me").json()["authenticated"])                                      # open sessions are gone too
        self.assertTrue((settings.projects_dir / "ACME" / "P-1" / ".epc" / "project.json").exists())         # the projects on disk are not touched
        c, r = self.master()                                                                                # the way back in after a reset
        self.assertEqual(r.status_code, 200)
        self.assertEqual(c.get("/api/identity/orgs").json(), [])
        self.assertIn("accounts_reset", [e["action"] for e in c.get("/api/identity/audit").json()])        # the reset itself stays in the audit log

    def test_the_audit_log_goes_too_only_when_asked(self):
        staff = self.staff()
        self.assertEqual(cli.main(["reset-accounts", "--yes", "--audit"]), 0)
        c, _ = self.master()
        self.assertEqual([e["action"] for e in c.get("/api/identity/audit").json()], [])

    def test_it_is_refused_in_production(self):
        self.staff()
        settings.env = "production"
        self.assertEqual(cli.main(["reset-accounts", "--yes"]), 1)
        with self.assertRaises(Exception):
            service.reset_accounts()
        settings.env = "dev"
        self.assertTrue(self.client().post("/api/auth/login", json={"login": "staff@office.com", "password": PW}).status_code == 200)       # nothing was deleted


if __name__ == "__main__":
    unittest.main()
