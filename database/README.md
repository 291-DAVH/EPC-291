# database

Platform state (ADR-0006): PostgreSQL in production, SQLite for the desktop edition and tests. Schema changes only through Alembic migrations.

## What lives where
| In the database | In project files (system of record) |
|---|---|
| organizations, users, memberships (roles), project index, deliverables index (revision, hash, state), audit ledger; later plans, subscriptions, jobs, notifications | calculations, drawings, documents, requirements, deliverables themselves, the per-project `.epc` ledger |

The database indexes the files; the SHA-256 manifest in the ledger is the reconciliation point. The application is still file-based except accounts: the `identity` module (US-0018, ADR-0009) reads and writes users, organizations, memberships, sessions and invitations (migration `0002`). A SQLite database (`local/epc.db`, or `EPC_DATABASE_URL`) is migrated automatically on first use; PostgreSQL must be migrated beforehand (the compose stack does it).

## Rules
1. Every table except `organizations` and `users` carries `organization_id` (multi-tenancy); `tests/test_migrations.py` enforces it.
2. One migration per change, reversible (`downgrade`), hand-written in `migrations/versions/NNNN_<topic>.py`.
3. No client data and no copyrighted material in `seeds/`.

## Use (from the repository root)
```
pip install -r database/requirements.txt
set EPC_DATABASE_URL=postgresql+psycopg://epc:epc@localhost:5432/epc     (default: SQLite in local/)
alembic -c database/alembic.ini upgrade head
alembic -c database/alembic.ini revision -m "add billing plans"
python -m unittest discover -s database/tests -t .
```
The compose stack in `infra/compose` starts PostgreSQL and runs `upgrade head` automatically.
