# Prompt to start a focused chat for the module "plan"

Paste everything below the line in a new chat, with this folder open as the working directory.

---

You are going to build the module **plan** of the EPC platform (automated electrical and civil engineering) **in isolation**. This folder is the whole world: do not look for, import or modify anything outside it.

1. Read `MODULE.md` (the contract) and `SPEC.md` (what this module does). Follow the contract strictly; if something in `SPEC.md` contradicts it, tell me before deciding.
2. Work in this order: complete `SPEC.md` with me (ask me what is missing, one decision at a time) -> schemas in `schema/` -> small synthetic samples in `fixtures/` -> tests -> `core.py` and `jobs.py` -> `params.json` -> the screen in `web/` (if the module has one) -> `docs/` with the decisions.
3. Keep it **as simple as possible**: do the minimum that meets `SPEC.md`, leave out anything it does not ask for, and tell me what you left out.
4. Everything that takes time is a background job with a status file (contract, section 3). The person never waits on a frozen screen.
5. Open-source libraries only, each with its licence written in `SPEC.md`; a library with a copyleft licence (GPL, AGPL) is called as a separate command, never linked, and you flag it for me.
6. I will give you books, PDFs, photos and text to teach you the subject. Never copy those into this folder. Extract from them **rules as data** into `knowledge/rules.json`, each with its source (book or standard, edition, page or section) and `"status": "pending"`; I will review them.
7. SVG is only a working view on the screen, never a deliverable; deliverables are DXF and PDF.
8. Code and documents in English; text on screen in Spanish and English.
9. Every number or look-and-feel setting goes in `params.json`, never inline.
10. When you finish, run the tests and the demo on their own and report what passes, what you assumed, what you left out and what the integrator must know. Do not claim something works unless you ran it.

Start by reading `MODULE.md` and `SPEC.md` and asking me the first question.
