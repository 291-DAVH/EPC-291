# ADR-0028: Norm selector: generic calculation engines, norms as complete packages, one registry

Status: proposed. Nothing of this is built yet; it is the plan. Date: 2026-10-27. Builds on ADR-0012 (one source per datum), ADR-0022 (engine split), ADR-0027 (one engine per norm).

## Context
`epc_aea90364` is, at the same time, the algorithms of low-voltage electrical sizing (demand, ampacity, voltage drop, short circuit, protection coordination) and the AEA 90364 norm (its tables, constants, rules, design criteria, review state, standard solutions). The calculation can therefore only be done with this norm: there is no way to say "calculate with IEC 60364" or "with NFPA 70". `policy.py` already says it: "when a second jurisdiction exists, this module becomes a policy per norm".

The platform will grow in two directions: **more norms** for the same discipline (IEC 60364, NFPA 70, IRAM…) and **more disciplines**, each with its own norms and its own calculations (civil, mechanical, HVAC, fire protection, instrumentation, telecom). Each norm is a complete body of knowledge by itself: its own tables, rules, criteria and review. Switching from one to another must be a choice, not a code change.

## Decisions
1. **Three kinds of package, with one direction of knowledge:**
   - `epc_norms` (new, one for the whole platform): the **contract and the registry**. It knows what a norm package is (its manifest, its data folders, its review state, its policies) and how to find one by id. It knows no norm and no calculation.
   - **Generic calculation engines, one per discipline** (`epc_calc_electrical` first; later `epc_calc_hvac`, `epc_calc_civil`…): the algorithms and the sequence of a calculation. They contain **no norm number**: everything normative arrives in a **policy** (the strategy) that the caller passes in. Each defines the policy it needs as a `typing.Protocol` of its own.
   - **Norm packages** (`epc_aea90364`, later `epc_iec60364`, `epc_nfpa70`…): **complete by themselves**. Each holds its tables and constants, its rules, its design criteria, its review state, its promoted standards and the policies it offers, for the discipline(s) it covers. A norm does **not** inherit from another one: when two norms agree on a value, each keeps its own copy with its own clause and edition (the `single-source` check compares file content, and the metadata of each norm differs).
2. **Strategy + Registry (Factory), plus Template Method inside each calculation.**
   - *Strategy*: the policy of a norm, for a discipline, is a replaceable object (`ElectricalPolicy`: capacity tables, correction factors, voltage-drop limits, protection constants, minimum sections, short-circuit factors…). The calculation asks the policy; it never reads a number from a file or a constant of its own.
   - *Registry/Factory*: `epc_norms.registry.policy(norm_id, discipline)` returns the policy, importing the norm package **by name at that moment** (no static import of any norm anywhere, so a norm can be added without touching code that already exists).
   - *Template Method*: each calculation engine keeps the fixed sequence of its steps (for electrical: demand → design current → protection → ampacity → section → voltage drop → short circuit → verifications); a step asks the policy and may be overridden by a hook of the policy when a norm really differs in method, not just in numbers.
   - Not a Builder: nothing is built step by step; variants are swapped.
3. **Data first.** What differs between norms is mostly numbers; those are JSON with their clause, loaded by the package. Code in a norm package exists only for what really differs in method, and it implements the hook of the engine.
4. **The package manifest.** Every norm package has `norm.json` (next to `norm_data.py`): `id`, `family`, `name` {es,en}, `editions`, `disciplines` it covers (`electrical`, `hvac`…), `status` (`draft | verified`), the engines it feeds with their policy entry point (`"electrical": "epc_aea90364.policy:electrical_policy"`), and the paths of its data. `epc_norms` discovers packages through what jurisdictions name (`packs` in `jurisdiction.json`) and through the manifest; there is no other list.
5. **Selection.** A project chooses its norm **per discipline**: `norm` in the project's meta, defaulting to the first pack its jurisdiction names for that discipline (`packs`). The backend resolves the policy once per request and passes it to the engine; the drawing engines and the plugins receive it by parameter (default: the registry's choice for the project) and never name a norm.
5b. **Many norms in one jurisdiction are normal**: `packs: {"electrical": ["aea90364", "iec60364"]}` lists what the country accepts; the project says which one it follows.
6. **A contract test every norm package must pass** (`epc_norms.contract`): manifest valid; every declared data file exists and matches its schema; every value has a clause and an edition; the policy answers every question its engine asks (no missing key); the review state refers only to existing points; no import of another norm package (a norm is complete by itself, so they never see each other). A new norm is "done" when it passes this and the engine's own worked examples.
7. **Layers** (`engine-layers`, generated): `epc_drawing` > `epc_mld | epc_sld` > the generic calculation engines and `epc_norms` (independent of each other) > `epc_dxf`; norm packages sit **beside** the engines, not under them: they import `epc_norms` (for loaders) and nothing else of the platform, and no one imports them statically (the registry does, by name). The `engine-independent` contract (no engine imports the backend) stays.
8. **Everything the backend asks of a norm goes through the registry:** the review screen lists the packages, their points and their state; the design criteria of a project come from the pack of the discipline it follows; the ingestion pipeline promotes into the pack the jurisdiction names (already so, ADR-0027).
9. **Naming.** Norm packages are named after the norm, never after a country (`aea90364`, `iec60364`): the country is metadata of the jurisdiction. Calculation engines are named `calc_<discipline>`. No version in a name (`editions` is in the manifest).

## Plan, by phases
Every phase ends with the gate green, the characterization tests of the drawings (`engine/drawing/tests/golden`) **unchanged** and the calculation outputs byte for byte the same: nothing changes for the user until phase 5.

| Phase | What | Exit criterion |
|---|---|---|
| 0 | This ADR. Freeze the safety net: the 248 tests of `epc_aea90364`, the drawing goldens, and a table of **which module is generic and which is the norm** (see below). | The table is reviewed and agreed. |
| 1 | `epc_norms`: manifest schema (`shared/schemas/norm.schema.json`), `norm.json` for AEA 90364, the registry (find by id, list, resolve the pack of a jurisdiction and discipline), the contract test. The existing `norm_data` becomes the AEA entry point of the registry. The backend `norms` and `engineering.criteria` modules go through the registry (they work for one pack, as today). | The registry returns today's behaviour; contract test green for AEA. |
| 2 | `epc_calc_electrical`: the **policy protocol** (`ElectricalPolicy`) and the first extraction, starting with what `policy.py` already isolates (protection constants), then ampacity tables and factors, voltage-drop limits, short-circuit factors, minimum sections, demand factors. Each step: move the algorithm to the generic engine, make the AEA policy supply the numbers, goldens unchanged. | Every function of the electrical calculation reads its numbers from the policy; `epc_aea90364` holds no algorithm. |
| 3 | Move what is not AEA out of `epc_aea90364`: `hazen_williams` and `hvac_airflow` to the engines of their discipline, `lighting` to the electrical one (or its own), `make_template`/Excel pipeline to the generic engine. | `epc_aea90364` has only data, rules, criteria, review, standard solutions and the policy. |
| 4 | **Selector.** `norm` per discipline in the project; the backend resolves the policy and passes it to `sld`, `engineering` and the drawing engines; the plugins accept it; the design-criteria screen and the review screen show the norm. With one norm installed, nothing visible changes except a selector with one option. | A project can name its norm; with one pack it behaves as before. |
| 5 | **Second norm**, `iec60364`, built as a complete package with the ingestion guide (`GUIA_NORMAS.md`) and the contract test; a project switches between AEA and IEC and the same board gives two memos. | Same board, two norms, both reviewed; contract test green for both. |
| 6 | **Other disciplines** one by one, each with its generic engine and its first norm pack (civil, mechanical, HVAC, fire…), without touching `epc_norms`. | `epc_norms` unchanged by the arrival of a discipline. |

### Phase 0 table (to be confirmed module by module; this is the first reading)
- Algorithms that are physics or sequence, not a norm: `voltage_drop`, `short_circuit`, `cable_thermal`, `conductor_selection`, `current_and_loads`, `grouping`, `topology`, the pipeline sequence in `aea_pipeline`, `board_memo`/`board_figures` (the memo is the calculation's output).
- Norm: `aea_tables.json`, `rules/`, `aea_rules`, `aea_catalog`, `aea_special_locations`, `aea_demand` (demand factors), `aea_ampacity`/`aea_conductors` tables, `aea_icc_factors`, `aea_earthing`, `solutions` + `data/standard-solutions.json`, `policy.py`, the criteria and the review.
- Not electrical-norm at all: `hazen_williams`, `hvac_airflow`, `lighting`.
Several `aea_*` modules mix both (an algorithm that reads a table): phase 2 separates them one at a time.

## Consequences
- (+) Adding a norm is adding a package and one line in a jurisdiction; switching is a project setting. Adding a discipline is adding a generic engine and a pack; the registry does not change.
- (+) Each norm is reviewed, released and copied as one unit, and the review state stays with the data it approves.
- (+) The calculation engines can be tested with a fake policy, with no norm at all.
- (-) Phase 2 is a large refactor of the heart of the calculation; the goldens and the 248 tests are what make it safe, and it is done function by function.
- (-) Values that two norms share are stored twice (once per norm, each with its clause): a conscious price of "complete by itself".
- (-) A norm whose method differs (not just its numbers) needs code in its package against the hook of the engine; the policy protocol of each discipline has to be designed carefully the first time (phase 2) and is easier to change while only one norm uses it.

## Not decided here
- Inheritance between norms (a norm extending another): not wanted; every norm is complete.
- Choosing a norm per circuit or per board inside a project (the unit is the discipline of the project).
- A UI to compare the same design under two norms side by side (phase 5 makes it possible; it is not part of the plan).
- The format of the policies of other disciplines (each will be designed when its engine is).
