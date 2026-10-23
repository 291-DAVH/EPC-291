# ADR-0004: The client sees only deliverables and data

Status: Accepted (implemented in `apps/api` and `apps/web`). Date: 2026-10-23.

## Context
The end user is an engineering office staff member who needs projects, deliverables, input data, requirements and reports. The machinery (plugins, skills, rules, workspace files, Claude analysis) must stay invisible.

## Decision
- Two API surfaces: `/api/app/*` for users and technical endpoints for the admin role only. Users receive 403 on the latter; the admin console exists only under `/admin` for `EPC_ROLE=admin`.
- Deliverables are served only from `deliverables/` with path-traversal checks; formats that are internal (`.svg`, `.json`, `.md`) are never delivered.
- Customer input enters as `received`, is analyzed outside the user's view, and returns as structured requirements. Monetary amounts are rejected from requirements (client economic data is confidential).

## Consequences
- (+) The product can be sold without exposing the way it works.
- (-) Real authentication, organizations and per-tenant isolation are still missing (planned in the `identity` module).
