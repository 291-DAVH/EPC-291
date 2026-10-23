# ADR-0006: PostgreSQL for platform state, files for engineering artifacts

Status: Proposed. Date: 2026-10-23.

## Context
Engineering artifacts (calculation JSON, drawings, Markdown sources, deliverables) are diffable, reviewable and delivered as files, so they belong in per-project git repositories. Platform concerns (users, organizations, roles, subscriptions, project index, jobs, audit ledger, notifications) need transactions, queries and concurrency. Today there is no database: everything is files, which cannot support multiple users.

## Decision
- PostgreSQL for platform state; SQLAlchemy 2 and Alembic migrations in `database/migrations/`.
- Project files stay the system of record for engineering artifacts; the database indexes them (project, deliverable, revision, hash, state) and holds the workflow state that the web needs to query.
- SQLite for the desktop edition and tests; the repository layer hides the engine.
- Multi-tenancy by `organization_id` on every table, enforced in the repository layer and tested.

## Consequences
- (+) Concurrency, permissions and audit are solved properly; files remain portable and versioned.
- (-) Two places to keep consistent; the ledger (SHA-256 manifests) is the reconciliation point.
