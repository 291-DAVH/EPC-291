"""Sign in and sign up with an alias, and with Google, GitHub, Facebook and LinkedIn (the providers are simulated: no network)."""
import unittest
import urllib.parse

from epc.core.config import settings
from epc.modules.identity import oauth
from tests.integration.test_identity_api import PW, Base

PROVIDERS = ("google", "github", "facebook", "linkedin")


class TestAlias(Base):
    def test_sign_in_with_email_or_alias(self):
        settings.signup = "open"
        c = self.client()
        r = c.post("/api/auth/signup", json={"kind": "individual", "name": "Ana Díaz", "email": "ana@x.com", "password": PW, "username": "Ana.Diaz"})
        self.assertEqual(r.status_code, 201, r.text)
        self.assertEqual(r.json()["username"], "ana.diaz")                                                     # stored lowercase
        for login in ("ana@x.com", "ANA@x.com", "ana.diaz", "Ana.Diaz"):
            c2 = self.client()
            r = c2.post("/api/auth/login", json={"login": login, "password": PW})
            self.assertEqual((r.status_code, r.json()["email"]), (200, "ana@x.com"), login)
        self.assertEqual(self.client().post("/api/auth/login", json={"email": "ana.diaz", "password": PW}).status_code, 200)       # the older field still works
        self.assertEqual(self.client().post("/api/auth/login", json={"login": "ana.diaz", "password": "wrong-wrong-1"}).status_code, 401)
        self.assertEqual(self.client().post("/api/auth/login", json={"login": "nadie", "password": PW}).status_code, 401)

    def test_alias_rules_and_change(self):
        settings.signup = "open"
        base = {"kind": "individual", "name": "Ana", "email": "ana@x.com", "password": PW}
        for bad in ("a", "ab", "con espacio", "tiene@arroba", "-empieza", "admin", "x" * 31, "ñandú"):
            r = self.client().post("/api/auth/signup", json={**base, "username": bad})
            self.assertEqual(r.status_code, 422, bad)
            self.assertIn("username", r.json()["detail"]["errors"])
        ana = self.client()
        self.assertEqual(ana.post("/api/auth/signup", json={**base, "username": "ana"}).status_code, 201)
        luis = self.client()
        luis.post("/api/auth/signup", json={"kind": "individual", "name": "Luis", "email": "luis@x.com", "password": PW})
        self.assertEqual(luis.get("/api/me").json()["username"], "")                                         # the alias is optional
        self.assertEqual(luis.put("/api/auth/username", json={"username": "ANA"}).status_code, 409)         # taken (case-insensitive)
        self.assertEqual(luis.put("/api/auth/username", json={"username": "luis_p"}).json()["username"], "luis_p")
        self.assertEqual(self.client().post("/api/auth/login", json={"login": "luis_p", "password": PW}).status_code, 200)
        self.assertEqual(luis.put("/api/auth/username", json={"username": ""}).json()["username"], "")        # cleared
        self.assertEqual(self.client().post("/api/auth/login", json={"login": "luis_p", "password": PW}).status_code, 401)
        self.assertEqual(ana.put("/api/auth/username", json={"username": "ana"}).status_code, 200)            # keeping your own is fine
        self.assertEqual(self.client().put("/api/auth/username", json={"username": "x1x"}).status_code, 401)

    def test_aliases_for_invitations_and_internal_accounts(self):
        staff = self.staff()
        owner, _ = self.new_org(staff, "Metal SRL", seats=3, owner="o@m.com")
        inv = owner.post("/api/app/org/invitations", json={"email": "m@m.com"}).json()
        m = self.client()
        self.assertEqual(m.post("/api/auth/accept-invitation", json={"token": inv["token"], "name": "M", "password": PW, "username": "mi.alias"}).status_code, 200)
        self.assertEqual(self.client().post("/api/auth/login", json={"login": "mi.alias", "password": PW}).status_code, 200)
        r = staff.post("/api/identity/users", json={"email": "rev@x.com", "name": "Rev", "password": PW, "platform_role": "standards", "username": "revisor"})
        self.assertEqual(r.status_code, 201, r.text)
        rev = self.client()
        self.assertEqual(rev.post("/api/auth/login", json={"login": "revisor", "password": PW}).json()["account_type"], "reviewer")
        users = {u["email"]: u for u in staff.get("/api/identity/users").json()}
        self.assertEqual((users["rev@x.com"]["username"], users["m@m.com"]["username"]), ("revisor", "mi.alias"))
        self.assertEqual(staff.post("/api/identity/users", json={"email": "z@x.com", "name": "Z", "password": PW, "platform_role": "auditor", "username": "revisor"}).status_code, 409)

    def test_failed_sign_ins_by_alias_are_throttled_and_logged(self):
        staff = self.staff()
        c = self.client()
        for _ in range(5):
            c.post("/api/auth/login", json={"login": "nobody.here", "password": "wrong-wrong-1"})
        self.assertEqual(c.post("/api/auth/login", json={"login": "nobody.here", "password": PW}).status_code, 429)
        log = staff.get("/api/identity/audit?action=login_failed").json()
        self.assertEqual({e["target"] for e in log}, {"nobody.here"})


class Social(Base):
    """Fake providers: the code is accepted and the person is whoever `self.who[provider]` says."""

    def setUp(self):
        super().setUp()
        self._old_oauth = (settings.oauth, settings.secret_key, settings.public_url)
        settings.oauth = {p: {"client_id": f"id-{p}", "client_secret": f"secret-{p}"} for p in PROVIDERS}
        settings.secret_key, settings.public_url = "test-secret-key", "http://localhost:5173"
        settings.signup = "open"
        self.sent = []
        self.who = {"google": {"sub": "g-1", "email": "ana@gmail.com", "email_verified": True, "name": "Ana Gómez"},
                    "github": {"id": 77, "login": "anagh", "name": "Ana GH", "_emails": [{"email": "ana@gmail.com", "primary": True, "verified": True}]},
                    "facebook": {"id": "f-1", "name": "Ana FB", "email": "ana@gmail.com"},
                    "linkedin": {"sub": "l-1", "email": "ana@gmail.com", "email_verified": "true", "name": "Ana LI"}}
        oauth.set_http(self.fake)

    def tearDown(self):
        oauth.set_http(None)
        settings.oauth, settings.secret_key, settings.public_url = self._old_oauth
        super().tearDown()

    def fake(self, url, data=None, headers=None):
        self.sent.append((url, data, headers))
        for pid, p in oauth.PROVIDERS.items():
            if url == p["token"]:
                if getattr(self, "provider_down", False):
                    raise oauth.OAuthError("provider_error")
                return {"access_token": f"token-{pid}"}
            if url == p["userinfo"]:
                return {k: v for k, v in self.who[pid].items() if not k.startswith("_")}
            if url == p.get("emails"):
                return self.who[pid]["_emails"]
        raise AssertionError(f"unexpected call {url}")

    def go(self, client, provider, mode="login", invite="", code="the-code", state=None, tamper=False):
        """The two redirects of the browser: start, then the provider sends the person back."""
        r = client.get(f"/api/auth/oauth/{provider}/start", params={"mode": mode, "invite": invite}, follow_redirects=False)
        self.assertEqual(r.status_code, 302, r.text)
        loc = r.headers["location"]
        if "auth_error" in loc:
            return r
        q = urllib.parse.parse_qs(urllib.parse.urlparse(loc).query)
        if tamper:
            for ck in client.cookies.jar:
                if ck.name == oauth.COOKIE:
                    ck.value = ck.value[:-3] + "AAA"
        return client.get(f"/api/auth/oauth/{provider}/callback", params={"code": code, "state": state or q["state"][0]}, follow_redirects=False)

    def error_of(self, r):
        self.assertEqual(r.status_code, 302)
        loc = r.headers["location"]
        return urllib.parse.parse_qs(urllib.parse.urlparse(loc).query).get("auth_error", [None])[0]


class TestProviders(Social):
    def test_only_configured_providers_are_offered(self):
        self.assertEqual([p["id"] for p in self.client().get("/api/auth/providers").json()], list(PROVIDERS))
        settings.oauth = {"google": settings.oauth["google"], "github": settings.oauth["github"]}
        self.assertEqual([p["name"] for p in self.client().get("/api/auth/providers").json()], ["Google", "GitHub"])
        settings.oauth = {}
        self.assertEqual(self.client().get("/api/auth/providers").json(), [])
        self.assertEqual(self.error_of(self.client().get("/api/auth/oauth/google/start", follow_redirects=False)), "provider_unavailable")

    def test_start_sends_the_person_to_the_provider_with_a_signed_state(self):
        for pid in PROVIDERS:
            c = self.client()
            r = c.get(f"/api/auth/oauth/{pid}/start", follow_redirects=False)
            self.assertEqual(r.status_code, 302)
            u = urllib.parse.urlparse(r.headers["location"])
            q = urllib.parse.parse_qs(u.query)
            self.assertEqual(f"{u.scheme}://{u.netloc}{u.path}", oauth.PROVIDERS[pid]["authorize"])
            self.assertEqual((q["client_id"], q["response_type"]), ([f"id-{pid}"], ["code"]))
            self.assertEqual(q["redirect_uri"], [f"http://localhost:5173/api/auth/oauth/{pid}/callback"])
            self.assertEqual("code_challenge" in q, oauth.PROVIDERS[pid]["pkce"])
            self.assertEqual(q["scope"], [oauth.PROVIDERS[pid]["scope"]])
            self.assertIn("httponly", r.headers["set-cookie"].lower())
            self.assertIn(oauth.COOKIE, r.headers["set-cookie"])
        self.assertEqual(self.client().get("/api/auth/oauth/google/start", params={"mode": "link"}, follow_redirects=False).status_code, 401)       # linking needs a session

    def test_a_broken_flow_never_signs_anyone_in(self):
        c = self.client()
        self.assertEqual(self.error_of(self.go(c, "google", state="otra-cosa")), "invalid_state")
        self.assertEqual(self.error_of(self.go(self.client(), "google", tamper=True)), "invalid_state")                    # cookie altered
        self.assertEqual(self.error_of(self.client().get("/api/auth/oauth/google/callback", params={"code": "x", "state": "y"}, follow_redirects=False)), "invalid_state")
        self.assertEqual(self.error_of(self.go(self.client(), "google", code="")), "cancelled")
        self.provider_down = True
        self.assertEqual(self.error_of(self.go(self.client(), "google")), "provider_error")
        self.assertFalse(self.client().get("/api/me").json()["authenticated"])
        # a flow started with one provider cannot be finished with another
        c = self.client()
        r = c.get("/api/auth/oauth/google/start", follow_redirects=False)
        state = urllib.parse.parse_qs(urllib.parse.urlparse(r.headers["location"]).query)["state"][0]
        self.assertEqual(self.error_of(c.get("/api/auth/oauth/github/callback", params={"code": "x", "state": state}, follow_redirects=False)), "invalid_state")


class TestSocialSignUpAndIn(Social):
    def test_a_new_person_registers_with_a_provider_and_signs_in_again(self):
        c = self.client()
        r = self.go(c, "google")
        self.assertEqual((r.status_code, r.headers["location"]), (302, "/?social=pending"))
        self.assertFalse(c.get("/api/me").json()["authenticated"])                                 # nothing is created before the person chooses
        self.assertEqual(c.get("/api/auth/oauth/pending").json(), {"provider": "google", "email": "ana@gmail.com", "name": "Ana Gómez"})
        self.assertEqual(c.post("/api/auth/oauth/complete", json={"kind": "bogus"}).status_code, 422)
        self.assertEqual(c.post("/api/auth/oauth/complete", json={"kind": "company", "org_name": ""}).status_code, 422)
        r = c.post("/api/auth/oauth/complete", json={"kind": "company", "org_name": "Gómez Hnos", "username": "ana.g"})
        self.assertEqual(r.status_code, 201, r.text)
        me = c.get("/api/me").json()
        self.assertEqual((me["account_type"], me["org"], me["email"], me["username"], me["has_password"]), ("corporate_owner", "Gómez Hnos", "ana@gmail.com", "ana.g", False))
        self.assertEqual(c.get("/api/auth/oauth/pending").status_code, 404)                        # used once
        ids = c.get("/api/auth/identities").json()
        self.assertEqual((ids["has_password"], [i["provider"] for i in ids["identities"]]), (False, ["google"]))
        # the next time one click is enough
        again = self.client()
        r = self.go(again, "google")
        self.assertEqual((r.status_code, r.headers["location"]), (302, "/"))
        self.assertEqual(again.get("/api/me").json()["email"], "ana@gmail.com")
        # without a password nobody can guess their way in by email or alias
        self.assertEqual(self.client().post("/api/auth/login", json={"login": "ana.g", "password": PW}).status_code, 401)
        self.assertEqual(self.client().post("/api/auth/login", json={"login": "ana@gmail.com", "password": ""}).status_code, 401)
        staff = self.staff()
        actions = [e["action"] for e in staff.get("/api/identity/audit?limit=50").json()]
        self.assertIn("social_signup", actions)
        self.assertIn("social_login", actions)

    def test_every_provider_registers_an_independent(self):
        for n, pid in enumerate(PROVIDERS):
            for who in self.who.values():
                who["email"] = f"p{n}@x.com"
            self.who["github"]["_emails"] = [{"email": f"p{n}@x.com", "primary": True, "verified": True}]
            c = self.client()
            self.assertEqual(self.go(c, pid).headers["location"], "/?social=pending", pid)
            self.assertEqual(c.post("/api/auth/oauth/complete", json={"kind": "individual"}).status_code, 201, pid)
            self.assertEqual(c.get("/api/me").json()["account_type"], "individual")

    def test_registering_needs_open_sign_up_and_an_email(self):
        settings.signup = "closed"
        c = self.client()
        self.assertEqual(self.error_of(self.go(c, "google")), "signup_closed")
        self.assertIsNone(c.cookies.get(oauth.PENDING_COOKIE))
        settings.signup = "open"
        self.who["facebook"]["email"] = ""
        self.assertEqual(self.error_of(self.go(self.client(), "facebook")), "no_email")
        # a pending sign-up that expired or was never started creates nothing
        self.assertEqual(self.client().post("/api/auth/oauth/complete", json={"kind": "individual"}).status_code, 422)

    def test_an_existing_account_is_linked_only_when_the_provider_vouches_for_the_email(self):
        solo = self.client()
        solo.post("/api/auth/signup", json={"kind": "individual", "name": "Ana", "email": "ana@gmail.com", "password": PW})
        # Google vouches for the email: linked and signed in
        c = self.client()
        r = self.go(c, "google")
        self.assertEqual((r.status_code, r.headers["location"]), (302, "/"))
        self.assertEqual(c.get("/api/me").json()["email"], "ana@gmail.com")
        self.assertEqual([i["provider"] for i in solo.get("/api/auth/identities").json()["identities"]], ["google"])
        # Facebook does not: whoever controls that Facebook account must not take the account over
        self.assertEqual(self.error_of(self.go(self.client(), "facebook")), "email_exists_login_first")
        # ... but the owner, signed in with the password, can link it on purpose
        r = self.go(solo, "facebook", mode="link")
        self.assertEqual(r.headers["location"], "/account?linked=facebook")
        fb = self.client()
        self.assertEqual(self.go(fb, "facebook").headers["location"], "/")
        self.assertEqual(fb.get("/api/me").json()["email"], "ana@gmail.com")

    def test_internal_accounts_never_sign_in_through_a_provider(self):
        staff = self.staff()
        for who in self.who.values():
            who["email"] = "staff@office.com"
        self.who["github"]["_emails"] = [{"email": "staff@office.com", "primary": True, "verified": True}]
        for pid in PROVIDERS:
            c = self.client()
            self.assertEqual(self.error_of(self.go(c, pid)), "internal_account_password_only", pid)
            self.assertFalse(c.get("/api/me").json()["authenticated"])
        # not even once linked by someone with access to the database row
        uid = next(u["id"] for u in staff.get("/api/identity/users").json() if u["email"] == "staff@office.com")
        from epc.modules.identity import repository as repo
        repo.insert_identity(uid, "google", "g-1", "staff@office.com")
        self.assertEqual(self.error_of(self.go(self.client(), "google")), "internal_account_password_only")

    def test_a_disabled_account_or_one_without_organization_cannot_sign_in(self):
        staff = self.staff()
        owner, slug = self.new_org(staff, "Metal SRL", seats=3, owner="ana@gmail.com")
        c = self.client()
        self.assertEqual(self.go(c, "google").headers["location"], "/")                                      # linked by the verified email
        staff.patch(f"/api/identity/orgs/{slug}", json={"active": False})
        self.assertEqual(self.error_of(self.go(self.client(), "google")), "no_organization")


class TestSocialInvitation(Social):
    def test_an_invitation_can_be_accepted_with_a_provider_that_vouches_for_the_email(self):
        staff = self.staff()
        owner, _ = self.new_org(staff, "Metal SRL", seats=3, owner="o@m.com")
        inv = owner.post("/api/app/org/invitations", json={"email": "ana@gmail.com", "role": "admin"}).json()
        self.assertEqual(self.error_of(self.client().get("/api/auth/oauth/google/start", params={"invite": "no-es-valida"}, follow_redirects=False)), "invalid_invitation")
        c = self.client()
        r = self.go(c, "facebook", invite=inv["token"])                                                       # Facebook does not vouch: refused
        self.assertEqual(self.error_of(r), "invitation_email_mismatch")
        self.who["google"]["email"] = "otra@gmail.com"
        self.assertEqual(self.error_of(self.go(self.client(), "google", invite=inv["token"])), "invitation_email_mismatch")
        self.who["google"]["email"] = "ana@gmail.com"
        c = self.client()
        r = self.go(c, "google", invite=inv["token"])
        self.assertEqual((r.status_code, r.headers["location"]), (302, "/"))
        me = c.get("/api/me").json()
        self.assertEqual((me["account_type"], me["org"], me["has_password"]), ("corporate_admin", "Metal SRL", False))
        self.assertEqual(self.error_of(self.go(self.client(), "google", invite=inv["token"])), "invalid_invitation")        # single use
        self.assertEqual(len(owner.get("/api/app/org").json()["members"]), 2)


class TestIdentitiesOfAnAccount(Social):
    def test_link_unlink_and_the_last_way_to_sign_in(self):
        c = self.client()
        self.go(c, "github")
        c.post("/api/auth/oauth/complete", json={"kind": "individual"})                                       # created through GitHub: no password
        self.assertEqual(c.delete("/api/auth/identities/github").status_code, 409)                           # its only way in
        self.go(c, "linkedin", mode="link")
        self.assertEqual(sorted(i["provider"] for i in c.get("/api/auth/identities").json()["identities"]), ["github", "linkedin"])
        self.assertEqual(c.delete("/api/auth/identities/github").status_code, 200)                           # LinkedIn remains
        self.assertEqual(c.delete("/api/auth/identities/github").status_code, 404)
        self.assertEqual(c.delete("/api/auth/identities/linkedin").status_code, 409)
        # setting a password needs no current one for such an account, and frees the last provider
        self.assertEqual(c.post("/api/auth/password", json={"current_password": "", "new_password": "short"}).status_code, 422)
        self.assertEqual(c.post("/api/auth/password", json={"current_password": "", "new_password": "a-new-password-1"}).status_code, 200)
        self.assertTrue(c.get("/api/me").json()["has_password"])
        self.assertEqual(c.delete("/api/auth/identities/linkedin").status_code, 200)
        self.assertEqual(self.client().post("/api/auth/login", json={"login": "ana@gmail.com", "password": "a-new-password-1"}).status_code, 200)
        # from now on the current password is required
        self.assertEqual(c.post("/api/auth/password", json={"current_password": "", "new_password": "another-pass-22"}).status_code, 422)

    def test_a_provider_account_belongs_to_one_person(self):
        a = self.client()
        self.go(a, "google")
        a.post("/api/auth/oauth/complete", json={"kind": "individual"})
        self.who["github"]["_emails"] = [{"email": "luis@x.com", "primary": True, "verified": True}]
        self.who["github"]["id"] = 5
        b = self.client()
        b.post("/api/auth/signup", json={"kind": "individual", "name": "Luis", "email": "luis@x.com", "password": PW})
        self.assertEqual(self.go(b, "github", mode="link").headers["location"], "/account?linked=github")
        # the same Google account cannot be linked to a second person
        self.assertEqual(self.error_of(self.go(b, "google", mode="link")), "identity_in_use")
        self.assertEqual([i["provider"] for i in b.get("/api/auth/identities").json()["identities"]], ["github"])


if __name__ == "__main__":
    unittest.main()
