# Roadmap

Reviewed at every sprint planning. Dates are targets, not commitments.

## Now (SPRINT-01, 2026-10-26 to 2026-11-06)
- Target structure applied (phases 2 and 3): `local/`, `shared/`, `claude/`, marketplace and plugin validation.
- First standard promoted to verified (AEA 90364-7-771).
- CI pipeline.

## Next (Q4 2026)
- Engine extraction and backend modules with import-linter (phases 4 and 5).
- Automated analysis of customer input through the Claude API.
- Portal and console split; WBS/EDT module MVP.
- PostgreSQL baseline.

## Later (2027)
- Authentication, organizations, subscriptions, white-label.
- Complete MLD generator; medium voltage; fire protection; HVAC; civil.
- Procurement and construction modules; PMI methodology pack.
- Drawing engine growth in 2D with ezdxf and shapely (ADR-0008).
- Second jurisdiction (another country).

## Deferred (no date)
- Desktop edition with Rust/Tauri (EP-012, ADR-0007).
- 3D and FreeCAD integration (not planned; see ADR-0008).

## Milestones
| Milestone | Target | Exit criteria |
|---|---|---|
| M0 Foundation | 2026-10-23 (done) | Hub, rules engine, portal, git workflow |
| M1 Architecture applied | 2026-11-06 | Repository matches `docs/architecture`; CI green |
| M2 Verified LV rules | 2026-11-30 | LV standards verified by the engineer; checks used by the calc engine |
| M3 Pilot | 2027-Q1 | Authentication, one organization, one real project end to end |
| M4 Commercial | 2027-Q2 | Subscriptions, on-prem package, second country pack |
