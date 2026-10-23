---
id: PRD-001
type: prd
title: Client portal
status: implemented-v1
epics: [EP-004]
owner: product
---

# PRD-001: Client portal

## Problem
The end user (an engineering office) cannot see the state of many projects at once, receive deliverables in a controlled way, or send the client's information in a form that becomes usable data. Showing them the platform's machinery would confuse them and expose our method.

## Users
Engineering office staff. Secondary: administrators.

## Goals
1. One dashboard with every project, its health, progress, next milestone and pending items.
2. Per project: deliverables (downloadable), input data, requirements, reports.
3. Customer input can be sent in free form (voice of customer, user stories, meeting notes, documents).
4. Nothing technical is visible to users.

## Non-goals
Editing engineering files in the browser; billing screens (see PRD-005).

## Functional requirements
| ID | Requirement | Status |
|---|---|---|
| FR-1 | Dashboard with KPIs, filters (status, phase, discipline, situation), sorting, cards and table views | done |
| FR-2 | Project page with Overview, Deliverables, Input data, Requirements, Reports | done |
| FR-3 | Safe download of delivered files; internal formats never offered | done |
| FR-4 | Upload of input data with attachments; status received -> analyzing -> structured | done |
| FR-5 | Create a project from the template | done |
| FR-6 | Spanish and English; light and dark | done |
| FR-7 | Technical console only for the admin role | done |
| FR-8 | Authentication and per-organization data | open (PRD-005) |

## Non-functional requirements
Responsive from phone width; no technical vocabulary in the UI; downloads protected against path traversal; works with 100+ projects.

## Success metrics
A new user finds a deliverable or sends information without help; zero technical terms in the user UI (checked by test).

## Open questions
Who receives notifications when a deliverable is published? Which formats may a user upload besides the current list?
