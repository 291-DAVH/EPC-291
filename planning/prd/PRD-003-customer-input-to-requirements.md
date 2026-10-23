---
id: PRD-003
type: prd
title: Customer input to requirements
status: implemented-v1
epics: [EP-005]
owner: product
---

# PRD-003: Customer input to requirements

## Problem
Clients give needs as stories, complaints, meeting notes and documents. Manually turning them into verifiable requirements is slow and loses traceability.

## Goals
1. Accept input in any free form.
2. Analyze, deduplicate and rewrite it as one verifiable statement per requirement, with type, priority, discipline, acceptance criteria and open questions.
3. Keep traceability from requirement to source and to deliverable.
4. Keep the analysis invisible to the user; they see status and result.
5. Never store the client's monetary information.

## Requirements
| ID | Requirement | Status |
|---|---|---|
| FR-1 | Upload form with attachments (allowed types, size limit, safe names) | done |
| FR-2 | `received` -> `analyzing` -> `structured` status | done |
| FR-3 | Validated storage of analysis (closed vocabularies, traceability, atomic, rejects amounts) | done |
| FR-4 | Merge into existing requirement instead of duplicating | done |
| FR-5 | Automatic trigger of the analysis through the Claude API | open (US-0016) |
| FR-6 | Notify the project engineer of open questions | open |
| FR-7 | Link requirements to deliverables (traceability matrix) | open |

## Success metrics
Time from submission to structured requirement; share of requirements with acceptance criteria; open questions answered before the next phase.
