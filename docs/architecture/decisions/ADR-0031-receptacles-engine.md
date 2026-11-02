# ADR-0031: Receptacles engine and its place in the platform

Status: accepted. Date: 2026-11-02. Follows the pattern of ADR-0029 and ADR-0030 (lighting): an engine that calculates, a backend module that serves the editor, a catalogue with three levels.

## Context
The plan editor already draws socket outlets (kinds `TG` general use and `TE` special use) and the automatic design gives them circuits, but nothing says how many a room needs, where they go or whether their mounting height complies. The owner asked for the same treatment the luminaires have.

## Decisions
1. **A standalone engine `epc_receptacles`** (pure Python, no dependencies): the rooms are rectangles in metres; for each room it gives the outlets needed by its use, their positions along the walls, the checks of the mounting height, the load and the minimum number of circuits. Every estimate says why and how sure it is.
2. **The norm gives data; the engine gives algorithms.** The outlets per use and the mounting limits live in `data/uses.json`. They are **typical values to verify** (confidence 0.4) except the warehouse perimeter rule, which cites AEA 90364-7-771. They are loaded in the global norms review (like the typical values of the plan engine), not per project.
3. **A catalogue of outlets with three levels** (factory in the engine, company, project) in the way of the luminaires, served by a backend module `receptacles`.
4. **The editor places the outlets as nodes `TG`/`TE`** with the room and the outlet in their attributes, and a later calculation replaces the ones that came from the engine.
5. **Rooms that are not rectangles** go across as their bounding box, with a warning, as in lighting.

## Consequences
- A new engine area: gate suite, coverage floor, impact map and import-linter layer.
- The counts per use have to be confirmed by the owner once, in the norms page.
- The layout is geometric (evenly along the walls); it does not see doors or furniture.
