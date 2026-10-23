---
id: PRD-002
type: prd
title: Rules from standards and the LV engine
status: implemented-v1
epics: [EP-002, EP-003]
owner: product
---

# PRD-002: Rules from standards and the LV engine

## Problem
Applicable standards are long PDFs. Engineers re-read them for every project, and a missed clause becomes a finding at audit. The standards are copyrighted, so the product cannot ship them.

## Goals
1. Turn each standard into a `rules.json` (clause references, parameters, checks, tables) validated by the engineer.
2. Check a project's data against those rules, reporting PASS, FAIL and not-evaluated.
3. Support several countries through jurisdiction packs.
4. Never ship or commit copyrighted text; quotes stay in `local/dev-knowledge`.

## Requirements
| ID | Requirement | Status |
|---|---|---|
| FR-1 | Extract text and clause index from PDFs; render scanned pages for visual reading | done |
| FR-2 | Validation: schema, unique ids, tables, clause exists, no verbatim copy (12+ words) | done |
| FR-3 | Promotion gate: only human-verified drafts reach `jurisdictions/` | done |
| FR-4 | Engine: query by topic, standard, clause, installation type; check with conditions | done |
| FR-5 | Production sees only verified standards | done |
| FR-6 | LV calculation (AEA 90364-7-771 and others), single-line diagram, IRAM sheets | done (tables pending validation) |
| FR-7 | Field names unambiguous across rules (entity-prefixed) | open (US-0009) |
| FR-8 | Calculation engine consumes the rules engine | open |

## Success metrics
Share of rules verified per standard; findings caught by the engine before audit; zero verbatim copies.

## Risks
Wrong rule or wrong derived check gives false confidence: every check carries `source_status`, `confidence` and a `derived` flag until confirmed.
