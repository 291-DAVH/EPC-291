# ADR-0023: Drawings as services; DXF layer catalog; standard solutions

Status: accepted (direction). First step done: the DXF layer catalog. Date: 2026-10-26.

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
4. **Deliverable as a service.** Any drawing (single-line, multi-line, plan) hands over an SVG in development and asks `epc_dxf` to turn it into a DELIVERABLE: DXF with the layer catalog, and the package.
   The SVG-to-DXF converters (`svg_to_dxf`, `capas_dxf`, `bloques_dxf`) move there from `epc_titleblock` and `epc_sld`; with that `epc_mld` stops needing `epc_sld`. SVG elements will carry a semantic role (`data-layer`)
   instead of being assigned to a layer by their position on the sheet.
5. **Layer catalog (done).** `epc_dxf.layers`: a drawing asks for a layer by role (`sld.diagram`, `sld.text`, `sld.titleblock`, `sld.sheet`, `plan.<layer>`); the catalog gives name, colour (AutoCAD index), line weight (empty = standard),
   line type and state (on, frozen, locked, plots). Sources, the later winning role by role: the default (`data/layers.json`), the global file (`<data>/global/drawing-layers.json`, edited by the MASTER in the console tab "Capas de dibujo",
   passed to engine runs in `EPC_LAYERS_JSON`), and later the project's own file so the user can adapt it.
6. Layers of the packages, top down: `epc_drawing` > `epc_mld` > `epc_sld` > (`epc_titleblock`, `epc_symbols`, `epc_plan`, `epc_calc`) > `epc_dxf`.

## Consequences
Each piece installs and changes alone; the map `docs/architecture/DEPENDENCIAS.md` says what a change touches. Defaults are identical to what was delivered before (golden outputs unchanged);
only what the MASTER edits changes a drawing. Steps 1-4 are future work, in this order: deliverable service, title block service, assembler with the standard-solutions document.
The entity-level line weights the single-line takes from its SVG still win over the layer's weight; making the layer govern needs the semantic roles of step 4.
