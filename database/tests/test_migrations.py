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
GLOBAL_TABLES = {"organizations", "users"}


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
        self.assertTrue({"organizations", "users", "memberships", "projects", "deliverables", "ledger_entries"} <= names)
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

    def test_downgrade_is_clean(self):
        command.upgrade(self.cfg, "head")
        command.downgrade(self.cfg, "base")
        names, e = self.tables()
        self.assertEqual(names, set())
        e.dispose()


if __name__ == "__main__":
    unittest.main()
