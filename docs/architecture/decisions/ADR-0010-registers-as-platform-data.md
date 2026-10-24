# ADR-0010: Management registers are platform data, defined by the methodology

Status: Accepted. Date: 2026-10-23. Builds on ADR-0002 (three kinds of management) and ADR-0009.

## Context
The management pack inherited from the previous framework kept risks, changes, issues, decisions and stakeholders as Markdown guides that Claude filled in during work sessions (commands such as "registrar incidencia", states such as `FOR_REVIEW`, folders such as `90-management`). A platform with several users, permissions and reports cannot build reports from free-form Markdown tables, and those files do not match its structure (project workspace, deliverables, modules).

## Decision
- Each register is a set of records stored as JSON in `workspace/05-management/registers/<kind>.json`, managed by the `registers` module through an API and a screen.
- The methodology pack defines them: `management/methodologies/<id>/registers.json` lists the registers (id, prefix, fields with type, limits and options in each language, closing statuses, derived values). Another methodology brings its own file; no code change.
- Records are never deleted; they change status and keep a history of who changed what and when (PM² keeps the trail). Required data is enforced at entry (an issue has an owner and a date; a risk has probability and impact).
- Reports (`reports.json`, D11 to D15 for PM²) read the registers through the module's public interface and the rest of the project's data; what the platform does not hold is shown as not available, never invented.

## Consequences
- (+) Reports, the console and a future client portal share one source of truth; history and permissions come for free.
- (-) The Markdown guides of the old framework (charter, scope, starting data, review sheet, audit...) and `management/workflow` still describe the previous way of working; they are adapted one by one when each becomes a platform feature.
