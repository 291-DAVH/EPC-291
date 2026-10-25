# Module contract

Every module of the platform (the single-line diagram, the plan canvas, a calculation...) follows this contract, so that it can be **developed, run and tested on its own** (in another chat, on another machine) and **handed over by copying its folder**. This file is the same in every module; do not edit it there.

## 1. A module is a folder that stands alone
- It runs, tests and demos with only its own folder: `python -m unittest discover -s tests -t .` and `python -m epc_<name> --demo --out out`. No backend, no database, no network, no other folder of the repository.
- It never imports the backend (`epc`) or another module's code. What it needs from another module arrives as a **JSON document** (its schema is in `schema/`), and what it gives goes out as a JSON document or a file.
- Dependencies: the Python standard library plus **open-source** libraries only, each listed with its licence in `SPEC.md`. Prefer few. Anything with a copyleft licence (GPL, AGPL) is called as a separate program (a command), never linked into the module's code, and is flagged in `SPEC.md` for the owner to decide.

## 2. Simple by design
- One purpose, written in one sentence in `SPEC.md`, and what it deliberately does **not** do. When in doubt, leave it out.
- Pure functions in `core.py`: the same input gives the same output.
- Every number and every look-and-feel setting (line widths, colours, text sizes, limits) lives in `params.json`. **Nothing inline.** Changing how it looks is editing that file.
- Every rule taken from a book or a standard lives as **data** in `knowledge/rules.json` with its source and a status (`pending`, `approved`, `rejected`); the code reads the rules, it does not contain them. The norm reviewer approves them like the rest of the platform's norm data.

## 3. Work in the background
Anything that can take more than a moment (converting a plan, drawing, placing trays, dimensioning, producing a document) is a **job**: `jobs.start(...)` returns at once and writes `status.json` (`state`, `progress` 0..1, `message`, `started`, `finished`, `error`) that the screen reads. A reader never sees a half-written file (write to a temporary file, then rename). The person never waits looking at a frozen screen, and a failure is reported in the status, never as a crash.

## 4. What it produces
- Deliverables are **DXF and PDF** (and the documents the platform issues). **SVG is never a deliverable**: it is a working view of the screen.
- Everything it computes must be reproducible from its input document; the result states the inputs and the rules (with their ids) it used.
- A result never hides a doubt: a `warnings` list says what was assumed or could not be done.

## 5. Untrusted input
Files a client sends (PDF, DWG, DXF, images, text) are untrusted: size limits from `params.json`, never executed, never opened with a tool that runs macros or scripts, and any SVG shown on a screen is shown as an image (scripts cannot run) or after removing scripts, event handlers and external references.

## 6. Learning material and copyright
Books, standards, drawings and photos used to teach the module **never go into the repository or the module folder** (they are copyrighted or the client's). They stay in `local/dev-knowledge/` (ignored by git). What the module keeps is what was extracted from them: the rule, its value and its source (book or standard, edition, section or page).

## 7. The screen (if the module has one)
- A React component that receives its data as props and reports changes through callbacks; it does not call the backend, the integration does. Text is in Spanish and English through the platform's `t()` (a minimal one in the demo).
- The component runs alone with `web/` (`npm run dev`) on the sample of `fixtures/`.

## 8. Tests and samples
- `fixtures/` has **small, synthetic** samples and the expected results; never real client files.
- Tests cover: the sample gives the expected result, it is deterministic, outputs have the fields of their schema, nothing imports the backend, jobs report their status and end, bad input is refused with a clear message.

## 9. How it is handed over
Copy the whole folder into `incoming/<name>/` of the repository (or give it to the integration chat as it is). The integrator then:
1. moves `src/epc_<name>` to `engine/<area>/src/` (engine part) and keeps its tests;
2. writes the backend module `backend/src/epc/modules/<name>/` (api, service, repository, models, public) that calls the engine part as a job, stores results in the project (never outside it) and respects the organization of the project;
3. places `web/src/Component.tsx` under `frontend/web/src/features/<name>/` and connects it to the API;
4. adds the permission subject, the audit entries, the Spanish and English texts and, if it stores data, the migration;
5. runs the platform's gate.
A module is **ready to hand over** when: `SPEC.md` is complete, the tests pass on their own, the demo runs, `params.json` holds every setting, `knowledge/rules.json` holds every rule with its source, and `docs/` records the decisions.

## 10. Language and style
Code, identifiers, comments and the documents of the module in English; what the person reads on screen in Spanish and English through the texts. Match the surrounding code's density of comments: say why, not what.
