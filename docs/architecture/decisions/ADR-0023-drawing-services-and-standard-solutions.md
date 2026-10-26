# ADR-0023: Drawings as services; DXF layer catalog; standard solutions

Status: accepted (direction). Done: the DXF layer catalog and the deliverable service with semantic roles. Date: 2026-10-26.

## Context
After ADR-0022 the drawing engine is a set of packages, but three things still tie the diagrams to each other and to the way they were first built:
the single-line (`epc_sld`) and multi-line (`epc_mld`) each decide which protection devices a circuit has; the title block is made through an Excel and subprocesses (`epc_sld.deps`);
and the layers of the DXF were names written in the code, assigned by where an entity sits on the sheet.

## Decisions
1. **Standard solutions, a document the MASTER maintains.** The rule "a lighting circuit takes a differential plus a thermal-magnetic breaker, in the quantity needed" is a design decision, not drawing.
   It lives in the calculation, driven by the project's criteria (for example the differential sensitivity), as a catalog of standard solutions (type of load or circuit -> devices, ratings rule, quantity rule)
   in a global JSON the MASTER edits in the console; later a project may override it. The calculation result lists the devices of each circuit.
2. **Symbol assembler.** A step between the calculation and the diagrams turns those devices into a neutral JSON of symbols (ids, poles, slots, texts). The single-line and the multi-line only read it and know how to lay it out.
   The three copies of the protection chain (`aea_pipeline._dispositivo`, `sld_generator.chain`, `mld_generator.device_chain`) become one.
3. **Title block as a service.** A diagram asks `epc_titleblock` for its sheets with a JSON request (formats, how many, the fields of the project) and receives the SVG and DXF of each. No Excel, no subprocess, no `SLD_*` variables;
   the data comes from the project (issuer, client, team, description).
4. **Deliverable as a service (done).** A drawing hands over its SVG in development and `epc_dxf.deliverable.convert` returns the DXF: symbols that have a DXF block become INSERTs, strokes are converted, colour and line
   weight follow the SVG and every entity goes to the layer of its ROLE. `epc_dxf.package` converts several sheets and writes the index of the package (`<name>_entregable.json`: per sheet its SVG with hash, its DXF, the layers it uses
   with entity counts and roles; no dates and no DXF hash, so the same drawing gives the same index). The converters (`svg_to_dxf`, `capas_dxf`, `bloques_dxf`) moved from `epc_titleblock` and `epc_sld` to `epc_dxf`.
   **Semantic roles:** SVG elements say what they are with `data-layer="<role>"` (`sld.diagram`, `sld.text`, `sld.titleblock`, `sld.sheet`); the converter reads it from the element or its closest ancestor. The IRAM template is marked by
   `epc_dxf.roles.tag_iram_sheet` (frame groups -> `sld.sheet`, title block -> `sld.titleblock`). An element without a role still falls back to the old position-on-the-sheet rule. Visible result: the whole title block now sits in
   its layer (before only part of it did), the coordinate letters of the frame in the sheet layer, and the table and reference column are annotation (`sld.text`) instead of diagram. The plan editor writes its DXF natively
   (one layer per kind, from the same catalog) and does not go through SVG.
5. **Layer catalog (done).** `epc_dxf.layers`: a drawing asks for a layer by role (`sld.diagram`, `sld.text`, `sld.titleblock`, `sld.sheet`, `plan.<layer>`); the catalog gives name, colour (AutoCAD index), line weight (empty = standard),
   line type and state (on, frozen, locked, plots). Sources, the later winning role by role: the default (`data/layers.json`), the global file (`<data>/global/drawing-layers.json`, edited by the MASTER in the console tab "Capas de dibujo",
   passed to engine runs in `EPC_LAYERS_JSON`), and later the project's own file so the user can adapt it.
6. Layers of the packages, top down: `epc_drawing` > `epc_mld` > `epc_sld` > (`epc_titleblock`, `epc_symbols`, `epc_plan`, `epc_calc`) > `epc_dxf`.

## Consequences
Each piece installs and changes alone; the map `docs/architecture/DEPENDENCIAS.md` says what a change touches. Defaults are identical to what was delivered before (golden outputs unchanged);
only what the MASTER edits changes a drawing. Steps 1-3 are future work, in this order: title block service, assembler with the standard-solutions document (step 4 is done). `epc_mld` still needs `epc_sld` for the title-block glue (`deps`) until step 3 is done.
The entity-level line weights the single-line takes from its SVG still win over the layer's weight; letting the layer govern is a decision for a later step now that every element has a role.
