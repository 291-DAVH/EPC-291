# ADR-0011: Norm review by a dedicated reviewer role

Status: Accepted. Date: 2026-10-24. Builds on ADR-0009 (accounts) and the knowledge concept in `docs/explanation/knowledge.md`.

## Context
The norm data that drives every calculation (the 177 rules, the 29 calculation tables and constants of the AEA engine, the 15 base design criteria) is marked as draft until a person validates it point by point against the standard. That validation is a product task done by one person (the maintainer of the platform), not by engineers or customers, and it must be traceable.

## Decision
- New platform role `standards` (the *norm reviewer*): an account that belongs to no organization and reaches only `/api/norms/*` and its own account. Customers and engineering staff accounts do not need it; staff (`admin`) can also open the review. Staff create the account (console, *Organizaciones*, or `python -m epc.modules.identity.cli create-admin --role standards`).
- Module `norms`: lists the norms (one unit per standard and edition for the rules, one for the calculation tables, one for the design criteria) and their points; a reviewer can **correct** a point (the value is rewritten in the engine's data file with the file's own formatting, so git shows only that change) and **approve** or **flag** it with a note.
- A point is *pending* until approved. Approval stores who, when, a note and the fingerprint of the approved value in `jurisdictions/AR/review.json`; every action is appended to `jurisdictions/AR/review-log.jsonl`. A corrected point returns to pending unless it is saved with approval; a value that changes by any other means after approval shows as *stale*.
- The reviewer corrects values, not structure: rules keep their fields and types, tables and constants keep their keys and sizes (checked), a criterion's default must stay within its options or limits. The data files keep no review fields, so the engine reads them unchanged.
- The design-criteria catalog is marked `validated: true` only while every criterion is approved; the design pipeline reads the catalog (not a copy) so a correction takes effect at once, and the calculation engine drops its in-memory copy of the tables and rules after a correction.

## Consequences
- (+) The pending item "validate the norm data" becomes a visible, auditable work list, and the platform can show what is validated.
- (-) Corrections are made in the data files of the installation: on the read-only container image the review must be done on the development copy and committed (the API says so). A multi-reviewer workflow (two approvals) and the validation of the standards ingested by `epc_standards` are not covered yet.
