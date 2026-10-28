# ADR-0029: Lighting engine (`epc_lighting`)

Status: accepted. Done: the engine, handed over from `incoming/epc-lighting-engine`, integrated as `engine/lighting`. Date: 2026-10-27

## Context
The platform had one lighting calculation, `epc_aea90364.lighting` (CAL-001): lumen method, a regular grid, point-by-point with Lambertian emission, antipanic emergency lighting, and a UGR placeholder. It sat inside the AEA engine although it is not a calculation of that norm (ADR-0028, phase 3 lists it to move out), nothing in the platform used it, and it did not read the data the lighting design needs (maintenance, reflectances, zonal cavity, photometry, exterior areas).
A lighting engine was built apart (another chat, following `docs/architecture/GUIA_MOTORES.md`) and handed over in `incoming/`.

## Decisions
1. **`epc_lighting` is an engine of the platform** (`engine/lighting/`): luminaire count by the lumen method or the zonal-cavity method, coefficient of utilisation (given or read from the maker's table by room index and reflectances), a uniform layout with its spacing check, verification of the mean illuminance, point-by-point illuminance (horizontal, vertical or tilted planes, grid statistics and uniformity), exterior floodlights, power and energy. Standard library only; it imports no other package of the platform.
2. **Shape of an engine of the guide:** `run(document, Options) -> Result` (`Result.as_dict()` with `schema_version`, `counts`, `warnings`), `LightingError` for what cannot be processed, a CLI (`python -m epc_lighting INPUT --out DIR`, exit 0 / 1), JSON Schemas of input and output, thresholds and catalogues as data (`params.json`, `data/*.json` with `{es, en}` labels), every estimated value with its `reason` and `confidence`, golden test and isolation tests (no sibling import, no print outside the CLI, nothing written on import).
3. **Layer:** the independent one (`epc_titleblock | epc_symbols | epc_plan | epc_aea90364 | epc_arch | epc_lighting`). It is a pure function over a small document: the backend may call it in process (lazy import).
4. **Normative data stays pending and unused.** The first norm inside it, `D351-79` (Argentina, Decree 351/79, Annex IV: 23 rules with clause, value and unit), has every rule `pending`; `norm_data.py` returns only approved rules and the pipeline does not read it yet. The source PDF stays in `local/dev-knowledge/` (never versioned). The illuminance targets, maintenance factors and reflectances in `data/` are typical values taken from the sources named in each file, with their confidence; the engineer confirms them against the standard of the project.

## Consequences
- (+) A real lighting calculation with its worked examples (158 tests), usable from the backend, the plugins and, later, the plan editor (luminaire positions and tags come out as data).
- (-) **Overlap kept on purpose for now:** `epc_aea90364.lighting` stays because it holds what `epc_lighting` does not do yet (antipanic emergency lighting, escape-route illuminance, the UGR check). When that is ported to the new engine the old module and its test are removed (ADR-0028, phase 3).
- (-) The rules of `D351-79` keep their review state **inside** the rules file (`review: pending|approved`), unlike the norm packages, whose review state is a separate file with the fingerprint of each approved value (ADR-0011). When the norm selector of ADR-0028 is built, `D351-79` becomes a norm package of its own (named after the norm, complete by itself) and its review goes through the same screen.
- Open: no backend module, no screen and no plugin yet; interior rooms are rectangular only; no daylight, no UGR, no inter-reflections, no photometry-driven placement (see the engine's README, "Known limits").
