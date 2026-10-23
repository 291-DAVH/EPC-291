# User-facing data model (per project, inside workspace/)

What the end user sees comes only from these files; everything else stays internal.

| File | Content | Written by |
|---|---|---|
| `05-management/project-status.json` | state (active/closed), progress_pct, health (on_track/at_risk/delayed), phase, manager, location, start, due, next_milestone, milestones[] | engineer / platform |
| `05-management/deliverables.json` | list of deliverables: id, code, name, discipline, format, status (planned/in_progress/in_review/delivered), revision, due, delivered_on, file (path under `deliverables/`) | platform (publish step) |
| `01-input/intake/INT-nnnn.json` | one record per piece of information sent by the user or client: kind (voice_of_customer, user_story, document, meeting_note, report), title, text, source, author, created, status (received, analyzing, structured), attachments[] | user (web form) |
| `00-setup/requirements.json` | structured requirements derived from intake: id, statement, type, priority, discipline, acceptance[], open_questions[], source_intake[], status | Claude analysis (hidden from the user) |
| `05-management/reports/index.json` | reports: id, title, type, date, summary, file | platform |

## Intake -> data pipeline
1. The user submits free text (voice of customer, user stories, meeting notes, documents) -> `INT-nnnn.json`, status `received`.
2. Claude analyses the batch of `received` items (skill `structure-customer-input`): deduplicates, rewrites each need as one verifiable requirement in the user's language, classifies (type, priority, discipline), proposes acceptance criteria and lists open questions. Result -> `requirements.json`; the intake item moves to `structured` (or `analyzing` while questions are open).
3. The user sees status changes and the resulting requirements, never how they were produced.
