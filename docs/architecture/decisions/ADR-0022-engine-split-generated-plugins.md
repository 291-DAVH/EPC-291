# ADR-0022: Drawing engine split into independent packages; plugins generated from the code

Status: accepted. Date: 2026-10-26.

## Context
`epc_drawing` held symbols, title blocks, the single-line and multi-line generators and the plan engine in one package, so every plugin that wrapped drawing code shipped all of it
and none could be updated alone. The drawings also calculated on their own, apart from `epc_calc`.

## Decision
1. The drawing engine is six packages under `engine/`: `symbols`, `titleblock`, `plan`, `sld`, `mld` and `drawing` (board design and exports). Each has its own `pyproject.toml`, tests and README.
2. Direction of dependencies, enforced by the `engine-layers` import contract: `drawing` > `mld` > `sld` > (`titleblock`, `symbols`, `plan`, `calc`). Siblings never import each other.
3. The drawings only draw: numbers come from `epc_calc` (`aea_pipeline` detail, `board_figures`).
4. A plugin declares only what it owns (`owns`). `engine`, `requires` and `python` are generated from the imports and the pyproject files (`tools/build/regen_plugins.py`, checked by the gate);
   each README carries a generated dependency table. The whole map is `docs/architecture/DEPENDENCIAS.md` (`tools/build/impact_map.py`, checked by the gate).
5. A new plugin, `plan-drawing`, packages the plan engine.

## Consequences
Each package installs and can be released alone; changing one tells, by the map, what to review. Module names changed (`epc_drawing.sld` -> `epc_sld`, ...); `epc_drawing.board_design` and `epc_drawing.export.*` keep theirs.
Splitting `epc_sld.deps` (sheet and symbol glue) from `epc_sld`, so `epc_mld` would not need `epc_sld`, is open.
