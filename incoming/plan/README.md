> **Integrated (ADR-0021).** The engine part now lives in `engine/drawing/src/epc_plan` (tests in `engine/drawing/tests/test_plan.py`, samples in `engine/drawing/tests/fixtures/plan`), the backend module in `backend/src/epc/modules/layout` and the screen in `frontend/web/src/features/project/{Layout,PlanEditor}.tsx` (tab "Trazado"). What stays here is the module's specification (`SPEC.md`), its documents (`docs/`) and the old demo screen.

# plan (module)

What it is: one sentence, written when the module is born. **Read MODULE.md first**: it is the contract this folder follows.

## Run it on its own
```
python -m unittest discover -s tests -t .          # tests, no backend, no network
python -m epc_plan --demo --out out               # demo with the sample in fixtures/
```

Screen on its own (needs Node):
```
cd web && npm install && npm run dev        # http://localhost:5190
```

## Layout
```
MODULE.md            the contract (do not edit; it is the same for every module)
SPEC.md              what THIS module does: inputs, outputs, rules, non-goals (edit)
src/epc_plan/       the code (pure Python; no import of the backend)
  core.py            the functions that do the work; deterministic
  jobs.py            long operations as background jobs with a status file
  cli.py             python -m epc_plan ...
  params.json        every number and every look-and-feel setting (never inline)
schema/              JSON Schemas of what goes in and what comes out
fixtures/            small, synthetic samples and their expected results
tests/               unittest
knowledge/           what the module learned (rules as data, with their source); NO copyrighted files
docs/                decisions taken while building it
```
