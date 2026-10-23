---
id: RISKS
type: risk-register
title: Risk register
status: active
---

# Risk register

Scale: probability and impact 1 (low) to 5 (high); score = probability x impact (green <= 6, amber 8 to 12, red >= 15).

| ID | Risk | P | I | Score | Response | Owner | Status |
|---|---|---|---|---|---|---|---|
| R-001 | Copyrighted standards leak into the repository or the product | 2 | 5 | 10 | `local/` ignore, pre-commit hook, CI check, verbatim guard on rules | owner | open |
| R-002 | Calculation tables or rules not validated against the official standards give wrong results | 3 | 5 | 15 | `source_status`, human validation gate, verified-only in production | owner | open |
| R-003 | Large restructuring breaks code and paths | 3 | 3 | 9 | One phase per branch, test gate after each | owner | open |
| R-004 | Scope creep across disciplines | 4 | 3 | 12 | Roadmap by epic, one discipline at a time, PRD before work | owner | open |
| R-005 | No authentication before a pilot exposes client data | 3 | 5 | 15 | EP-007 before M3; role guard meanwhile | owner | open |
| R-006 | Claude API cost per analysis grows with volume | 3 | 3 | 9 | Record cost per job, batch analysis, caching | owner | open |
| R-007 | Plugin layout drifts from Claude Code's official format | 2 | 3 | 6 | `claude plugin validate --strict` in CI | owner | open |
| R-008 | Single-person bus factor | 4 | 4 | 16 | Docs-as-code, ADRs, planning in repo, clear modules | owner | open |
| R-009 | (deferred with EP-012) Desktop packaging (Python sidecar, signing on three platforms) is heavier than expected | 3 | 3 | 9 | Spike first (US-0023/0024), CI matrix, keep Rust code small | owner | open |
