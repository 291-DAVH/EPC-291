# ADR-0015: A MASTER account for development only

Status: Accepted. Date: 2026-10-24. Extends ADR-0013.

## Context
The maintainer needs to open every screen of the platform on a development machine, including right after the accounts were deleted, without creating and juggling users. That convenience must not exist for the people who use the platform.

## Decision
- A fixed internal account (`master`, email `master@dev.invalid`) with the rights of the engineering team, available only when **all** of these hold: `EPC_ENV` is exactly `dev`, accounts are required (`EPC_AUTH=required`), and `EPC_DEV_MASTER_PASSWORD` is set in the environment. **Nothing is shipped**: the repository carries no password and no default; the value lives only in the developer's own `local/dev.ps1` (the `local/` folder is ignored by git), so the account cannot reach `main`. The gate check `dev-credentials` fails if any versioned file gives the MASTER variables a value or if the deployment files (`infra/`, `.github/`) mention them, and if `local/` stops being ignored.
- It signs in only from the machine itself (loopback addresses) and with the environment's password, through the normal sign-in box; the database row is created on first use and has **no password of its own**, so the account cannot be used by any other path.
- It is **transparent**: it does not appear in the lists of accounts, in the audit log nor in the count of staff accounts (it never counts as "the last administrator"); the domain `dev.invalid` is reserved, so nobody can register or create it. In production or staging it is inert even if the variable were set, and the container image runs with `EPC_ENV=production`.
- `python -m epc.modules.identity.cli reset-accounts --yes [--audit]` (and `.\local\dev.ps1 reset-users`, which asks for confirmation) deletes every account, organization, session, invitation, assignment and linked identity; it refuses in production, keeps the projects on disk and records itself in the audit log unless the log is deleted too. After a reset the MASTER is the way back in.

## Consequences
- (+) Fast development loop; a fresh start is one command.
- (-) A development machine that sets the variable and exposes the API beyond loopback still refuses the MASTER (loopback check), but it should not be exposed anyway.
