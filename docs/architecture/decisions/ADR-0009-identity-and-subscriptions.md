# ADR-0009: Accounts, organizations (individual and corporate) and tenant isolation

Status: Accepted (US-0018). Date: 2026-10-23. Builds on ADR-0004 (the client sees only deliverables) and ADR-0006 (database strategy).

## Context
Until now the role (`user` or `admin`) came from an environment variable: nobody logged in, so the platform could not be used with real customer data, nor piloted, nor sold as subscriptions. Two kinds of subscription must exist: **individual** (one person) and **corporate** (a group of people who share the same projects).

## Decision
**Account model** (database, migration `0002_identity`): `organizations` (`kind` = `individual` | `company`, `seats`, `active`), `users` (email, password hash, `platform_role`), `memberships` (user in organization, role `owner` | `member`), `sessions`, `invitations`. A subscription is an organization: an individual one has one seat; a corporate one is a group of people limited by `seats`.

**Two kinds of people.** *Staff* (`platform_role = admin`: the engineering office) are not tied to an organization and see every project and the technical console. *Customers* belong to an organization and see only its projects, through the end-user surface (`/api/app/*`). Inside an organization the `owner` manages the people (invite, change role, deactivate, remove) and a `member` only uses the projects. The organization always keeps at least one owner.

**Two modes** (`EPC_AUTH`): `simulated` (development default: the role comes from `EPC_ROLE`, no login, no database; every earlier workflow and test is unchanged) and `required` (production default: sessions and accounts).

**Sessions.** Opaque random token (256 bits) in an `HttpOnly`, `SameSite=Lax` cookie (`Secure` behind HTTPS) or `Authorization: Bearer`; only its SHA-256 is stored, so a database leak does not give sessions. Fixed lifetime (`EPC_SESSION_HOURS`, 12). Deactivating a person, suspending an organization, changing a password or removing a member revokes the affected sessions at once; the role and the membership are read on every request, so permission changes apply immediately.

**Passwords.** `scrypt` (standard library, per-password salt), minimum 10 characters, never the email. Unknown account and wrong password answer alike and cost the same time; five failures per email (or thirty per address) in 15 minutes answer 429.

**Access to accounts.** Self-registration is closed by default (`EPC_SIGNUP=open` enables individual and company sign-up). Normally the staff create an organization and send its owner an invitation link; the owner invites the group. Invitations are single-use, expire in 7 days, hold a seat while pending, and an existing account can join a second organization with its password. A person may belong to several organizations; a session works in one (the first, or the one named at sign-in).

**Tenant isolation.** Each project records its owner organization (`org` in `.epc/project.json`). The projects repository filters by the organization of the request in both listing and lookup, so every module that resolves a project through `projects.get_project_dir` is covered, and another organization's project answers 404 (it does not exist for them). Projects created before accounts have no owner and are visible only to staff until assigned (`PUT /api/projects/{client}/{code}/org`). Code outside a request (background jobs) is trusted and not filtered. Tests cover cross-organization reads, writes, creation and listing.

**Boundaries.** The guard (`identity.guard`) resolves the principal for every request, returns 401 to anonymous callers (except health, `/api/me`, sign-in, sign-up and invitation endpoints), 403 to customers outside the public surface, and lets staff through. The owner endpoints live under `/api/app/org` (customer surface) and check the owner role in the service; the staff endpoints under `/api/identity/*` and are unreachable by customers.

## Consequences
- (+) Real multi-user use, groups with seats, a clean base for billing (the seat count is the limit that a plan will set) and white label (an organization is the unit to brand).
- (+) No new dependency for security: hashing and tokens use the standard library; the database layer is SQLAlchemy Core over the existing Alembic schema (SQLite is migrated automatically for development; PostgreSQL by the compose `migrate` service).
- (-) Known limits, deliberate for this stage: no email delivery (the invitation link is shown to the sender), no password reset by email (staff can set a temporary one), no MFA or SSO, a fixed session lifetime, in-memory sign-in throttling (per process), and two organizations cannot both use the same client code in the project path (the second gets "already exists"; a per-organization path is the fix when it matters). The subscription plan (price, billing) is not modeled: only `kind` and `seats`.
