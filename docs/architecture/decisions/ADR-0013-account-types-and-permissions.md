# ADR-0013: Account types, a permission matrix and an audit log

Status: Accepted. Date: 2026-10-24. Extends ADR-0009 (accounts and organizations) and ADR-0011 (norm review).

## Context
The platform has customers (independent professionals and companies), its own team and, now, people who inspect or audit customers. Each kind of person must see exactly what corresponds to them from the moment they sign in, and what is allowed was spread between the route filter and several services.

## Decision
- **Sign-in stays one form** (email and password). The kind of account is worked out from the account itself and reported by `/api/me` (`account_type`, `abilities`, `landing`):

| Kind | Who | Sees |
|---|---|---|
| `individual` | independent professional (an organization of one person) | their own projects |
| `corporate_owner` | owner of a company subscription | the organization's projects and people |
| `corporate_admin` | administrator of a company subscription | the same; manages members but never touches an owner |
| `corporate_member` | member of a company subscription | the organization's projects, no people management |
| `inspector` | internal inspector | only the organizations assigned to them; read, plus recording observations |
| `auditor` | external auditor | only the organizations assigned to them; read-only, plus recording observations |
| `reviewer` | norm reviewer | only the norm review |
| `staff` | platform administrator | everything; everything they do is recorded |

  One person can belong to several organizations (one account, several memberships) and switches between them; becoming a member of a company never changes the type of an existing account. The independent professional stays an organization of one so that every datum belongs to an organization and isolation is solved in one place.
- **Permission matrix as data** (`identity/permissions.py`): each kind has abilities (`read`, `write`, `respond`) over subjects (`app`, `org`, `observation`, `norms`, `identity`, `console`). The guard maps every request to a subject and a method to an action and refuses what the matrix does not give; the screens use `abilities` only to hide what would be refused. Services still check what depends on the data (who may touch an owner, which organization).
- **Assignments** (`user_assignments`): an inspector or auditor reaches a project only when its organization is assigned to them by staff; with no assignment they see nothing. The filter lives where projects are resolved, so every module is covered.
- **Observations**: a register of the methodology (`registers.json`, `observation`) on the customer surface. Inspectors, auditors and staff record them; the customer's owner or administrators answer (only the response); whoever recorded it closes it.
- **Audit log** (`audit_log`, staff only): sign-ins and failed sign-ins, accounts, roles, organizations, invitations, assignments, password changes, organization switches and observations: who, what, on what, which organization, when. It never stores passwords, tokens or invitation links.
- **HTTP hardening**: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, `Cache-Control: no-store` on account data, and HSTS when cookies are secure.

## Consequences
- (+) Adding a kind of account is a row in the matrix and a test, not a new set of `if`s; the matrix test (every kind against the same list of requests) fails if access drifts.
- (+) Inspectors and auditors are possible without a second isolation mechanism.
- (-) Not done yet: sending invitations by email (links are still shown to the sender), invitation-based creation of internal accounts (staff set an initial password), two-factor authentication, and finer permissions inside an organization (a member currently shares the organization's projects).
