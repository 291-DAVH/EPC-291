"""Alembic baseline on SQLite: upgrade, tenancy invariant, downgrade."""
import os
import tempfile
import unittest
from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

DB = Path(__file__).resolve().parents[1]
GLOBAL_TABLES = {"organizations", "users", "identities", "registrations"}      # identities belong to a person, a registration to a company that is not an organization yet: not to a tenant


class TestMigrations(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.url = "sqlite:///" + str(Path(self.tmp.name) / "t.db").replace("\\", "/")
        self._old = os.environ.get("EPC_DATABASE_URL")
        os.environ["EPC_DATABASE_URL"] = self.url
        self.cfg = Config(str(DB / "alembic.ini"))

    def tearDown(self):
        if self._old is None:
            os.environ.pop("EPC_DATABASE_URL", None)
        else:
            os.environ["EPC_DATABASE_URL"] = self._old
        self.tmp.cleanup()

    def tables(self):
        e = sa.create_engine(self.url)
        try:
            return set(sa.inspect(e).get_table_names()) - {"alembic_version"}, e
        except Exception:
            e.dispose()
            raise

    def test_single_head(self):
        self.assertEqual(len(ScriptDirectory.from_config(self.cfg).get_heads()), 1)

    def test_upgrade_creates_tables_and_every_tenant_table_has_organization_id(self):
        command.upgrade(self.cfg, "head")
        names, e = self.tables()
        self.assertTrue({"organizations", "users", "memberships", "projects", "deliverables", "ledger_entries", "sessions", "invitations", "audit_log", "user_assignments", "identities"} <= names)
        insp = sa.inspect(e)
        for t in names - GLOBAL_TABLES:
            self.assertIn("organization_id", [c["name"] for c in insp.get_columns(t)], t)
        e.dispose()

    def test_constraints_reject_duplicates(self):
        command.upgrade(self.cfg, "head")
        _, e = self.tables()
        with e.begin() as c:
            c.execute(sa.text("INSERT INTO organizations (id, slug, name) VALUES ('a', 'acme', 'Acme')"))
        with self.assertRaises(sa.exc.IntegrityError):
            with e.begin() as c:
                c.execute(sa.text("INSERT INTO organizations (id, slug, name) VALUES ('b', 'acme', 'Other')"))
        e.dispose()

    def test_identity_migration_converts_existing_roles_and_downgrades(self):
        command.upgrade(self.cfg, "0001")
        _, e = self.tables()
        with e.begin() as c:
            c.execute(sa.text("INSERT INTO organizations (id, slug, name) VALUES ('o1', 'acme', 'Acme')"))
            for uid, email in (("u1", "a@x.com"), ("u2", "b@x.com")):
                c.execute(sa.text(f"INSERT INTO users (id, email, display_name) VALUES ('{uid}', '{email}', '{uid}')"))
            c.execute(sa.text("INSERT INTO memberships (id, organization_id, user_id, role) VALUES ('m1', 'o1', 'u1', 'admin'), ('m2', 'o1', 'u2', 'user')"))
        command.upgrade(self.cfg, "head")
        with e.connect() as c:
            roles = dict(c.execute(sa.text("SELECT user_id, role FROM memberships")).all())
            org = c.execute(sa.text("SELECT seats, active FROM organizations")).one()
            usr = c.execute(sa.text("SELECT platform_role, password_hash FROM users WHERE id = 'u1'")).one()
        self.assertEqual(roles, {"u1": "owner", "u2": "member"})
        self.assertEqual((org[0], bool(org[1])), (1, True))
        self.assertEqual(tuple(usr), ("user", None))
        command.downgrade(self.cfg, "0001")
        with e.connect() as c:
            self.assertEqual(dict(c.execute(sa.text("SELECT user_id, role FROM memberships")).all()), {"u1": "admin", "u2": "user"})
        e.dispose()

    def test_downgrade_is_clean(self):
        command.upgrade(self.cfg, "head")
        command.downgrade(self.cfg, "base")
        names, e = self.tables()
        self.assertEqual(names, set())
        e.dispose()


if __name__ == "__main__":
    unittest.main()
