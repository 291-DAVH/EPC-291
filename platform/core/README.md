# core

The rules engine moved to `engine/rules` (phase 4). `workflow/` holds the seed of the workflow engine migrated from the legacy template: state rules (`rules/`), transition scripts (`scripts/`, with `states.json`, `workflow.py`, `fwlib.py`) and fixed-phrase commands (`commands/`). Next step: turn `states.json` + `workflow.py` into the engine described in docs/plan section 2.4.
