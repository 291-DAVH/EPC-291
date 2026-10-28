# ADR-0030: Lighting in the platform: backend module and plan-editor integration

Status: accepted and built in seven phases (2026-10-27/28; the defaults of "Decisions I need from the owner" were confirmed). Date: 2026-10-27. Builds on ADR-0029 (the `epc_lighting` engine), ADR-0021 (plan editor), ADR-0026 (automatic design of circuits and runs) and ADR-0028 (norm selector).

## Context
`epc_lighting` calculates, from a small JSON document (luminaires, rectangular interior rooms, exterior areas), how many luminaires a room needs, where they go, whether the room reaches its target illuminance and what the light looks like on the work plane. It is pure, in-process callable and has no connection to the platform yet.
The plan editor already has what it needs around it: rooms drawn as polygons (ADR-0026), the electrical discipline with the subdiscipline *Lighting* (kinds `LU`, `IN`, `CP`, `TB`…), the scale of each sheet, a Design panel that proposes the runs and the wiring of the luminaires it finds, and the pattern "propose as a preview, accept to apply" used by that panel.
The goal: a person marks the rooms, says what each one is for and which luminaire to use, and the platform **places the luminaires on the plan with the calculation behind them**; the existing design then runs the trunks and the circuits.

## What the engine needs and what the editor has
| The engine asks (per room) | Where it comes from |
|---|---|
| `width_m`, `length_m` (rectangle; `x` along the length) | the room polygon of the drawing, in view units, times the metres per unit of the sheet |
| `height_m` | room parameter (default: the story height of the project settings, 2.6 m if none) |
| `activity` → target illuminance, `ugr`, `ra` | room parameter, chosen from the engine's activities (typical values: they carry their source and confidence) |
| `luminaire` (lamps, flux, power, optional CU table and photometry) | a **catalogue of luminaires** (global / company / project, like the layers and the standard solutions) |
| reflectances, `method` (lumen or zonal), `target_lux` override, `coefficient_of_utilisation`, work-plane height, hours per year | room parameters (all optional: the engine estimates what is missing and says how sure it is) |
The engine returns positions in metres from the room corner (`x_m`, `y_m`, `z_m`), the count needed and installed, the mean illuminance against the target, the spacing check, the point-by-point statistics, the power and the energy, and a list of warnings. Every estimated number carries its `reason` and `confidence`.

## Decisions
1. **A backend module `lighting`** (`api`, `service`, `repository`, `models`, `public`; the layers and the public-interface rule of ADR-0001 apply). It calls `epc_lighting` **in process** (lazy import), takes the drawing in the request body as the design endpoints do (so it never reads or writes the drawing) and returns a **proposal**: nothing is saved by calculating. Endpoints under `/api/projects/{client}/{code}/lighting`:
   - `GET options`: the activities, materials, lighting systems, methods and the catalogue of luminaires in force (labels `{es, en}`).
   - `POST calc`: `{drawing (rooms, scale, origin), rooms: {room id: lighting parameters}, options}` → `{result (the engine's), placements (positions in view units, by room), warnings, stale-free fingerprint}`.
   - `GET/PUT/DELETE` of the luminaire catalogue at each level, in the catalogs module's pattern.
2. **The geometry between editor and engine is one pure, tested function** (`lighting/geometry.py`): a room polygon that is an axis-aligned rectangle (within 1 %) becomes `width_m`/`length_m` and a corner; any other polygon uses its **bounding box and says so in a warning** (the engine has rectangular rooms only); positions come back as `corner + (x_m, y_m) / metres_per_unit`. Without a calibrated scale the calculation is refused with the reason (the same rule as the plan engine).
3. **Room parameters live with the room in the drawing** (`RoomIn.lighting`, optional, ignored by the plan engine like the rest of the room), so they are saved with the sheet, versioned in its history and visible to coordination only as the luminaires they produce. The result is **not** stored in the drawing.
4. **The editor gets a panel "Lighting"** in the right-hand rail (the electrical discipline; open by default in a plan of the *Lighting* subdiscipline), in two steps like Design:
   - *Rooms*: a table with one row per room (name, activity, height, luminaire, method, optional target) and **Calculate**. The proposal shows on the plan as dashed circles with the number of luminaires and, per room, a card: needed, installed, `E_m` against the target (met / not met with the margin), spacing, uniformity, and the warnings with their confidence badges.
   - *Apply*: places one `LU` node per position (kind chosen by the subdiscipline), with `attrs.lighting = {room, luminaire, flux_lm, power_w}`. A later calculation **replaces the luminaires of that room that came from the calculation** (asked first) and never touches the ones the person drew.
   - Then the existing Design steps run on those loads (runs preview, then wiring). The Design panel reads the power of each luminaire from `attrs.lighting.power_w` when present instead of the typical value per outlet.
5. **The engine's tags are not pushed into the drawing.** The plan engine numbers the nodes (`LU-001…`) when it processes the sheet; the lighting result is tied to the nodes by `attrs.lighting.room`, not by tag.
6. **Targets are typical values until reviewed.** The activities come from the engine's data (their source and confidence shown). A room may override the target; the rules of `D351-79` stay pending and unused until ADR-0028 makes them a norm package and a person approves them (then the target of an activity can be taken from the approved rule and marked so).
7. **Audit and permissions:** calculating needs the workspace-read permission; applying is a normal save of the sheet (the edit guard of the discipline already applies); catalogue edits follow the catalogs module's rules per level; every apply is audited with the number of luminaires.

## Plan, by phases
Each phase ends with the gate green; nothing changes for the user before phase 3.

| Phase | What | Exit criterion |
|---|---|---|
| 1 | Backend module `lighting`: options, calc, `geometry.py` with its tests (rectangles, rotated and L-shaped rooms, orientation, units, missing scale), global luminaire catalogue with a few generic entries (flagged *illustrative*), integration tests with `TestClient` | `POST calc` over the demo plan returns placements inside each room |
| 2 | `RoomIn.lighting` and the **Lighting panel with the preview only** (no apply); i18n es/en; Vitest tests of the pure parts (parameters → request, result → cards, placements → overlay) | The preview matches the engine's numbers on the worked classroom example |
| 3 | **Apply** to the plan (nodes with `attrs.lighting`), replace-on-recalculation, and Design using the power of each luminaire | Mark rooms → calculate → apply → runs → wiring, on the demo plan |
| 4 | **Study kept and checked for staleness** per sheet (`workspace/02-engineering/layout/<sheet>/src/lighting.json`, with the fingerprint of rooms and parameters), "the rooms changed: recalculate" notice (as the board memo has), the **luminaire catalogue screens** for company and project in the console, and the **lighting calculation report** as a deliverable (PDF) through the issuing flow | A study survives a reload and warns when stale; the report is issued with the project's title block |
| 5 | Exterior areas (a polygon with the `exterior` flag), point-by-point result as an **illuminance map** overlay (a toggle of the panel), spacing and uniformity marks | The map matches the engine's grid statistics |
| 6 | Port **emergency lighting** (antipanic, escape routes) and the UGR check from `epc_aea90364.lighting` into `epc_lighting` and remove the old module (ADR-0028, phase 3) | The old module and its test are gone; the same worked cases pass in the new engine |
| 7 | `D351-79` as a norm package with its review through the norms screen; approved rules feed the targets | A target read from an approved rule is shown as such |

## Risks and how they are met
- **Non-rectangular rooms** are the first limit people will hit: bounding box with a warning now; a polygon-capable layout in the engine is an engine change (its own phase and ADR when wanted).
- **Heights and the work plane** are easy to leave at defaults: the panel shows them in the table and the card says which default was used.
- **Luminaire data** decides the quality of the result (flux, CU, photometry). The catalogue starts illustrative and says so; importing manufacturer files (IES/LDT) is not in this plan.
- **Replacing luminaires** must never destroy what the person drew: only nodes marked as coming from the calculation are replaced, and the person is asked.
- **A large number of rooms** with point-by-point on: the grid step is an option of the panel and the calculation runs per request (bounded by the size of the document).

## Decisions I need from the owner (defaults in brackets)
1. Is the **bounding box** of a non-rectangular room acceptable at first, with a warning? [yes]
2. Should the **report** (phase 4) be issued as a PDF through the normal deliverables flow? [yes]
3. Luminaire catalogue: a **generic list edited by the company** is enough at first; **manufacturer files** later? [yes]
4. **Emergency lighting** (phase 6) before or after exterior areas and the illuminance map (phase 5)? [after: normal lighting first]

## Consequences
- (+) A closed loop in the editor: rooms → luminaires with their calculation → runs → circuits, using the pieces that already exist.
- (+) The engine stays pure and testable; the platform owns the geometry glue, the catalogue and the screens.
- (-) Room parameters add fields to the drawing model (optional, ignored by the plan engine).
- (-) The targets of the activities are the typical ones quoted in the engine's material, which the screen says on each card; the ones of the Decreto 351/79 reach the panel only when a person approves them in the norms review (phase 7). Until then the rooms use the activity or a target given by hand.
- (-) The review state of the lighting rules is kept with the others in the AEA norm package (`epc_aea90364/data/review.json`), because the norms review has one file for it; the engine reads the `review` flag of each rule, which the review keeps in step.
- (-) Emergency luminaires are previewed and reported but not drawn as nodes of the plan: the electrical profile has no kind for them (a later profile change).
