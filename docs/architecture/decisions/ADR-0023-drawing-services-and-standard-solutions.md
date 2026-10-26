# ADR-0023: Drawings as services; DXF layer catalog; standard solutions

Status: accepted. Done: the DXF layer catalog, the deliverable service with semantic roles, the title block service and the standard solutions. Date: 2026-10-26.

## Context
After ADR-0022 the drawing engine is a set of packages, but three things still tie the diagrams to each other and to the way they were first built:
the single-line (`epc_sld`) and multi-line (`epc_mld`) each decide which protection devices a circuit has; the title block is made through an Excel and subprocesses (`epc_sld.deps`);
and the layers of the DXF were names written in the code, assigned by where an entity sits on the sheet.

## Decisions
1. **Standard solutions, a document the MASTER maintains (done).** The rule "a lighting circuit takes a differential plus a thermal-magnetic breaker, in the quantity needed" is a design decision, not drawing. It lives in the
   calculation: `epc_calc.solutions` reads a document (`data/standard-solutions.json`) of solutions, each with the conditions it applies under (topology, kind, phase, type, group, motor, In range, text), its priority and the chain of
   symbols that builds the circuit. Placeholders take the facts of the circuit and the project's criteria (`{in_a:g}`, `{icu_ka:g}`, `{rcd_ma:g}`, `{tag}`), so the differential sensitivity is no longer fixed at 30 mA in the drawings.
   Sources, the later winning solution by solution: the default document, the global file the MASTER edits (console tab "Soluciones estándar", `<data>/global/standard-solutions.json`, passed in `EPC_SOLUTIONS_JSON`), and later the
   company's and the project's own files (`load` already takes extra files; a solution can be replaced, added, switched off or removed with `null`). A document must keep one solution with an empty `when` for any circuit.
   The default document reproduces what the diagrams drew, plus a ready-made, switched-off solution "lighting: differential + breaker" the MASTER can turn on.
2. **Symbol assembler (done).** The assembler does not make symbols (the library does): it names which symbols build each circuit, in order, with their poles and slot texts. It is the same resolution step in the calculation:
   the detail of every circuit carries `cadena` (the chain) and `solucion` (which one won), and the table text (`disp`) comes from it. The single-line and the multi-line only read `cadena` and lay it out. The three copies of the
   protection chain (`aea_pipeline._dispositivo`, `sld_generator.chain`, `mld_generator.device_chain`) became one. The differential check of the board follows the chain (a circuit is protected when its own devices or a group above include one).
3. **Title block as a service (done).** A diagram asks `epc_titleblock.service.render` for its sheets with a JSON request (formats, name and fields of each sheet, the project's common fields, logos) and receives the filled sheets;
   `project_request` turns the platform's title block data into the common part. No Excel, no subprocess; the single-line and the multi-line get the project's request in `EPC_TITLEBLOCK_JSON`. `epc_sld.deps`, the Excel template
   and `titleblocks_generator` are gone, and `epc_mld` no longer imports `epc_sld` (the layers contract puts them side by side). Visible result: the three fields the Excel template carried as demo data (type of drawing,
   "replaces" code and internal code) are no longer printed in every title block: they stay blank until the project gives them.
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
6. Layers of the packages, top down: `epc_drawing` > (`epc_mld`, `epc_sld`) > (`epc_titleblock`, `epc_symbols`, `epc_plan`, `epc_calc`) > `epc_dxf`.

## Consequences
Each piece installs and changes alone; the map `docs/architecture/DEPENDENCIAS.md` says what a change touches. Defaults are identical to what was delivered before (golden outputs unchanged);
only what the MASTER edits changes a drawing. All steps are done; what remains is the project's and the company's own copies of the two documents (layer catalog and standard solutions), which the loaders already accept.
When the catalog sets a weight for a layer, the layer governs: the entities of that layer are left "by layer" instead of carrying the stroke width of the SVG; a layer without a weight keeps the strokes (the default).
The plan editor no longer writes its layers itself: it makes a DXF draft whose layers are roles (`plan.ELEC-LUM`) and hands it to `epc_dxf.deliverable.finish_draft`, which gives every role its name and look from the catalog; its delivery
package gets the same index as the diagrams (`package.describe_dxf`).
**Automatic groups of differentials:** the document of standard solutions has a third part, `groups`: rules that put circuits without a differential of their own behind one. A rule says which circuits it takes (the same conditions as a
solution), how they are split (`by`: type, phase, kind, topology), how many circuits and how much current one differential serves (`max_circuits`, `max_ib_a`) and how the group is named. `epc_calc.grouping` plans the groups,
`epc_drawing.board_design` adds them to the board data before the calculation, so the memo, the single-line and the multi-line see them as any group. They are switched off by default (lighting and sockets); a circuit with a kind chosen by hand, one that
already has a differential, or one in a group written by hand is left alone. A change in the document makes the memo of the boards stale.
