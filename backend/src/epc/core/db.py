"""Database access shared by modules: one SQLAlchemy engine per URL (PostgreSQL in production, SQLite for development and tests).

The schema belongs to the Alembic migrations in `database/`. A SQLite database is brought to the latest revision automatically the first
time it is used; any other database must be migrated beforehand (`alembic -c database/alembic.ini upgrade head`, done by the compose stack).
"""
import os
import threading
from pathlib import Path
from typing import Dict

import sqlalchemy as sa

from epc.core.config import settings
from epc.core.errors import Failure

_engines: Dict[str, sa.Engine] = {}
_lock = threading.Lock()


def url() -> str:
    if settings.database_url:
        return settings.database_url
    local = settings.repo / "local"
    local.mkdir(parents=True, exist_ok=True)
    return "sqlite:///" + (local / "epc.db").as_posix()


def _migrate(db_url: str) -> None:
    ini = settings.repo / "database" / "alembic.ini"
    if not ini.exists():
        raise Failure("database/alembic.ini not found: run the migrations before starting the backend")
    from alembic import command
    from alembic.config import Config
    old = os.environ.get("EPC_DATABASE_URL")
    os.environ["EPC_DATABASE_URL"] = db_url                   # read by database/migrations/env.py
    try:
        command.upgrade(Config(str(ini)), "head")
    finally:
        if old is None:
            os.environ.pop("EPC_DATABASE_URL", None)
        else:
            os.environ["EPC_DATABASE_URL"] = old


def engine() -> sa.Engine:
    u = url()
    with _lock:
        eng = _engines.get(u)
        if eng is None:
            if u.startswith("sqlite"):
                path = u.split("///", 1)[-1]
                if path and path != ":memory:":
                    Path(path).parent.mkdir(parents=True, exist_ok=True)
                _migrate(u)
                eng = sa.create_engine(u, connect_args={"check_same_thread": False})
                sa.event.listen(eng, "connect", lambda c, _: c.execute("PRAGMA foreign_keys=ON"))
            else:
                eng = sa.create_engine(u, pool_pre_ping=True)
            _engines[u] = eng
        return eng


def dispose() -> None:
    """Close every engine (tests that delete their temporary database)."""
    with _lock:
        for e in _engines.values():
            e.dispose()
        _engines.clear()
