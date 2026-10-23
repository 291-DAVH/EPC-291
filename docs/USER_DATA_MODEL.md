# User-facing data model (per project, inside workspace/)

What the end user sees comes only from these files; everything else stays internal.

| File | Content | Written by |
|---|---|---|
| `05-management/project-status.json` | state (active/closed), progress_pct, health (on_track/at_risk/delayed), phase, manager, location, start, due, next_milestone, milestones[] | engineer / platform |
| `05-management/deliverables.json` | list of deliverables: id, code, name, discipline, format, status (planned/in_progress/in_review/delivered), revision, due, delivered_on, file (path under `deliverables/`) | platform (publish step) |
| `01-input/intake/INT-nnnn.json` | one record per piece of information sent by the user or client: kind (voice_of_customer, user_story, document, meeting_note, report), title, text, source, author, created, status (received, analyzing, structured), attachments[] | user (web form) |
| `00-setup/requirements.json` | structured requirements derived from intake: id, statement, type, priority, discipline, acceptance[], open_questions[], source_intake[], status | Claude analysis (hidden from the user) |
| `05-management/wbs.json` | WBS (EDT): nodes with dotted id (the parent is the id without its last part), name, weight, progress (leaves only; parents are rolled up), discipline, owner | engineer / Claude (API `PUT /api/projects/{id}/wbs`); customers read it |
| `05-management/schedule.json` | activities: id, name, start, end, wbs_id, depends_on[] (finish-to-start), milestone, progress; critical path and slack are computed | engineer / Claude (`PUT .../schedule`); customers read it |
| `05-management/backlog.json` | internal backlog: id BL-nnn, title, type, priority, status, estimate_h, wbs_id, requirement_id, owner | engineer (`/api/projects/{id}/backlog`); **never shown to the customer** |
| `05-management/reports/index.json` | reports: id, title, type, date, summary, file | platform |

## Delivery package
`GET /api/app/projects/{id}/deliverables/packages` lists what was delivered grouped by issue (`<emission>/<transmittal>_Rev<NN>`, e.g. `ifa/TR-001_Rev00`); `GET .../deliverables/package[?group=...]` returns the ZIP (folder structure kept, `INDICE.csv` with SHA-256). The name uses the revision the client sees (`Rev00`); the internal revision (`00.R.C`) is recorded in the transmittal, not in the file name. A deliverable also offers other policy-deliverable formats that sit next to it with the same name (the `.pdf` of a `.dxf`); `?format=pdf` downloads it.

## Engineering workspace (engineer / admin only)
`02-engineering/<discipline>/<package>/{drawings/svg, calc, docs}` is shown in the **Engineering** tab only to the admin/engineer role (`/api/projects/{id}/engineering`, never under `/api/app`): `.svg` diagrams are previewed as images (single-line `SLD-*`, multi-line `MLD-*`, other drawings) and lists/notes (`.csv`, `.xlsx`, `.md`, `.txt`, `.json`) are shown as text or tables. **SLD data** (sub-tab *Datos del unifilar*): the form saves `02-engineering/electrical/PQ-01/src/sld-input.json` (board, titleblock, circuits with TAG, load, unit, parent, topology, phase, length, device, cable type). *Generate* writes the Excel the plugin expects (`build/sld/input_for_sld.xlsx`, sheets TABLERO and CIRCUITOS), fills the titleblock workbook (company, client, people) and runs `python -m epc_drawing.sld.sld_paginate` exactly as the `generate-sld` skill does; SVG goes to `drawings/svg`, DXF to `drawings/dxf` and the per-sheet calculation JSON to `calc`. The generator keeps its own fixed voltage-drop limits (it does not read the design criteria yet). API: `/api/projects/{id}/sld` (GET, PUT), `/example`, `/generate` (async), `/status`.

**Design criteria** (sub-tab *Criterios de diseño*): the catalog of criteria per jurisdiction and discipline lives in `engine/jurisdictions/<country>/<discipline>/design-criteria.json` (base values, flagged `validated: false` until confirmed against the standards). A project overrides any of them in `workspace/00-setup/design-criteria.json` with an origin (client requirement, standard, project decision), a note and a change history; the *design criteria report* is generated from it (`/api/projects/{id}/engineering/criteria`). Calculation and drawing plugins will read this file (not wired yet).

SVG stays internal: what the customer receives is under `deliverables/` (DXF stamped copies, PDF, XLSX).

## Intake -> data pipeline
1. The user submits free text (voice of customer, user stories, meeting notes, documents) -> `INT-nnnn.json`, status `received`.
2. Claude analyses the batch of `received` items (skill `structure-customer-input`): deduplicates, rewrites each need as one verifiable requirement in the user's language, classifies (type, priority, discipline), proposes acceptance criteria and lists open questions. Result -> `requirements.json`; the intake item moves to `structured` (or `analyzing` while questions are open).
3. The user sees status changes and the resulting requirements, never how they were produced.
