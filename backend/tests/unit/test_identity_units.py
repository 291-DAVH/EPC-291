"""Pure logic of the identity service, without HTTP or a database: password hashing, input checks, the kind of account a principal is, the login throttle and the
organization slug. Pinned as it behaves today."""
import unittest
from unittest import mock

from epc.core.errors import Conflict, Invalid
from epc.modules.identity import service as ids
from epc.modules.identity.models import Principal


class TestPasswords(unittest.TestCase):
    def test_hash_and_verify(self):
        h = ids.hash_password("correct horse battery")
        self.assertTrue(h.startswith("scrypt$16384$8$1$"))
        self.assertTrue(ids.verify_password("correct horse battery", h))
        self.assertFalse(ids.verify_password("wrong", h))
        self.assertNotEqual(h, ids.hash_password("correct horse battery"))           # a new salt every time

    def test_unknown_or_malformed_hashes_never_verify(self):
        self.assertFalse(ids.verify_password("x", None))
        self.assertFalse(ids.verify_password("x", ""))
        self.assertFalse(ids.verify_password("x", "not-a-hash"))
        self.assertFalse(ids.verify_password("x", "scrypt$a$b$c$d$e"))

    def test_token_hash_is_sha256_hex(self):
        self.assertEqual(ids.token_hash("abc"), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")

    def test_password_rules(self):
        ids._check_password("0123456789")
        with self.assertRaises(Invalid) as cm:
            ids._check_password("short")
        self.assertEqual(cm.exception.detail["errors"], {"password": f"at least {ids.MIN_PASSWORD} characters"})
        with self.assertRaises(Invalid) as cm:
            ids._check_password("Ana@Example.com", "ana@example.com")
        self.assertEqual(cm.exception.detail["errors"], {"password": "must not be the email"})


class TestInputChecks(unittest.TestCase):
    def test_email(self):
        self.assertEqual(ids._check_email("  Ana@Example.COM "), "ana@example.com")
        for bad in ("", None, "ana", "ana@x", "a b@x.com", "a@" + "x" * 250 + ".com"):
            with self.assertRaises(Invalid, msg=bad):
                ids._check_email(bad)
        with self.assertRaises(Invalid) as cm:
            ids._check_email("master@dev.invalid")
        self.assertEqual(cm.exception.detail["errors"], {"email": "this address is reserved"})

    def test_username(self):
        with mock.patch.object(ids.repo, "user_by_username", return_value=None):
            self.assertIsNone(ids._check_username(None))
            self.assertIsNone(ids._check_username("  "))
            self.assertEqual(ids._check_username(" Ana.Perez "), "ana.perez")
            for bad in ("ab", "a@b", "-ab", "x" * 31, "admin", "ROOT", "con espacio"):
                with self.assertRaises(Invalid, msg=bad):
                    ids._check_username(bad)
        with mock.patch.object(ids.repo, "user_by_username", return_value={"id": "u1"}):
            with self.assertRaises(Conflict):
                ids._check_username("ana")
            self.assertEqual(ids._check_username("ana", exclude="u1"), "ana")

    def test_token_from_cookie_or_bearer(self):
        self.assertEqual(ids.token_from("cookie", "Bearer abc"), "cookie")
        self.assertEqual(ids.token_from(None, "Bearer abc"), "abc")
        self.assertEqual(ids.token_from("", "bearer  xyz "), "xyz")
        self.assertIsNone(ids.token_from(None, "Basic abc"))
        self.assertIsNone(ids.token_from(None, None))


class TestAccountType(unittest.TestCase):
    def test_every_kind_of_account(self):
        P = lambda **kw: Principal(authenticated=True, **kw)      # noqa: E731
        self.assertEqual(ids.account_type(Principal()), "")
        self.assertEqual(ids.account_type(P(role="admin")), "staff")
        self.assertEqual(ids.account_type(P(role="standards")), "reviewer")
        self.assertEqual(ids.account_type(P(role="inspector")), "inspector")
        self.assertEqual(ids.account_type(P(role="auditor")), "auditor")
        self.assertEqual(ids.account_type(P(org_kind="company", org_role="owner")), "corporate_owner")
        self.assertEqual(ids.account_type(P(org_kind="company", org_role="admin")), "corporate_admin")
        self.assertEqual(ids.account_type(P(org_kind="company", org_role="member")), "corporate_member")
        self.assertEqual(ids.account_type(P(org_kind="company", org_role="")), "corporate_member")
        self.assertEqual(ids.account_type(P(org_kind="individual", org_role="owner")), "individual")
        self.assertEqual(ids.account_type(P()), "individual")


class TestThrottle(unittest.TestCase):
    def setUp(self):
        ids.reset_throttle()
        self.addCleanup(ids.reset_throttle)

    def test_it_blocks_after_the_limit_and_only_for_that_key(self):
        for _ in range(3):
            ids._throttle("k", 3)
            ids._throttle("k", 3, add=True)
        with self.assertRaises(Exception) as cm:
            ids._throttle("k", 3)
        self.assertEqual(cm.exception.detail, {"errors": {"login": "too many attempts, try again in a few minutes"}})
        ids._throttle("other", 3)

    def test_attempts_expire_after_fifteen_minutes(self):
        with mock.patch.object(ids.time, "time", return_value=1000.0):
            for _ in range(3):
                ids._throttle("k", 3, add=True)
        with mock.patch.object(ids.time, "time", return_value=1000.0 + 899):
            with self.assertRaises(Exception):
                ids._throttle("k", 3)
        with mock.patch.object(ids.time, "time", return_value=1000.0 + 900):
            ids._throttle("k", 3)

    def test_reset_clears_everything(self):
        for _ in range(3):
            ids._throttle("k", 3, add=True)
        ids.reset_throttle()
        ids._throttle("k", 3)


class TestSlug(unittest.TestCase):
    def test_slug_is_lowercase_dashed_and_unique(self):
        taken = set()
        with mock.patch.object(ids.repo, "org_by_slug", side_effect=lambda s: {"slug": s} if s in taken else None):
            self.assertEqual(ids._slug("Acme S.A. — Ingeniería"), "acme-s-a-ingenier-a")
            taken.add("acme")
            self.assertEqual(ids._slug("ACME"), "acme-2")
            taken.add("acme-2")
            self.assertEqual(ids._slug("Acme"), "acme-3")
            self.assertEqual(ids._slug("!!!"), "org")
            self.assertEqual(len(ids._slug("x" * 100)), 40)


if __name__ == "__main__":
    unittest.main()
