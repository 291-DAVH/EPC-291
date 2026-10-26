# epc-dxf

The catalog of DXF layers every drawing is delivered with: name, colour, line weight, line type and state per role (`sld.diagram`, `sld.text`, `plan.ELEC-LUM`...).
Sources, the later winning role by role: `data/layers.json` (default), the global file in `EPC_LAYERS_JSON` (the MASTER edits it in the console), files passed to `layers.load` (later: the project's).

Deliverable service: `deliverable.convert(svg)` turns an SVG in development into the DXF (symbols as blocks, strokes, colour and weight, layer by `data-layer` role); `package.deliver(sheets, out_dir, name)` does it for
several sheets and writes `<name>_entregable.json`. SVG roles: `roles.tag_iram_sheet` marks the IRAM template; generators mark their own elements. See ADR-0023.
