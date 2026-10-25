# plan - what this module does

> Starting point taken from ADR-0020 (docs/architecture/decisions). Complete it with the owner before writing code: the questions are at the end.

## Purpose
Turn an architectural plan into a canvas on which the engineer draws a few points and lines, and let the system derive from them, in the background, the electrical trays and conduits with their cables, the fire-protection pipes and the drains, with dimensions and comments.

## Not in scope (to keep it small)
- It does **not** recognise walls, rooms or doors in the plan; the plan is only an underlay.
- It is **not** a CAD: points, polylines, layers, scale and measuring, nothing more at the start.
- It does not do the electrical calculation itself (section, voltage drop, protections): that is `epc_calc`. It receives the cables of a route as data and returns lengths, grouping, fill and so on.
- Automatic route suggestion and clash detection come later (phase 5).

## Input
- `plan` document: the underlay (a reference to a converted view: image or SVG for display), its `level`, and its **scale** (two calibration points in drawing units and the real distance between them).
- `drawing` document: nodes (kind, position, level, label) and routes (polylines with a layer / discipline and a kind of installation: tray, buried duct, direct burial, road crossing, conduit...), in plan coordinates.
- `cables` document (from the platform): the cables that run through each route, each with its id, outer diameter, weight and circuit group.
- Schemas in `schema/`.

## Output
- `routes` document: for every route its real **length** (from the scale) and its stretches by kind, ready to become the platform's "real route of a cable".
- `trays` document: per stretch, the cables it carries, grouping count, fill %, weight, and the tray or conduit size chosen from a catalog in `params.json`.
- `networks` document (later): pipe networks for fire protection and drainage with lengths, nodes and levels, for their calculation.
- `annotations`: dimensions (cotas) and comments placed on the drawing.
- Files: **DXF and PDF** of the plan with the routes drawn over it. **Never SVG as a deliverable**: SVG is the on-screen view only.

## Conversions (open-source tools to evaluate; licences to confirm)
- PDF (vector) to a view: `pdftocairo` (poppler, GPL) or MuPDF (AGPL), **called as a separate command, not linked**.
- DXF: `ezdxf` (MIT) reads it and can render it to SVG.
- DWG to DXF: LibreDWG (GPL), as a separate command.
- IFC (later): IfcOpenShell (LGPL).
- Images: kept as they are; the underlay is just the image.
- Every conversion is a **background job** with a status file; a failed conversion leaves the image as underlay and says so in `warnings`.

## Rules it applies (as data in `knowledge/rules.json`)
Distances between trays, bending radii, support spacing, fill limits, separation between power and signal, cover depth of buried conduits, slopes of drains, pipe velocities... Each one with its source and `pending` until the reviewer approves it. The owner will provide books, PDFs and photos; extract from them, never copy them here.

## Screen (`web/`)
A canvas with pan, zoom, snapping, layers that can be shown or hidden, a calibrate-scale tool, point and polyline tools, a measuring tool and a panel that lists what was derived. Simple first; every setting in `params.json`.

## Phases
1. Upload, convert to a view, calibrate, levels.
2. Draw nodes and routes; lengths and the stretches of the real route are generated.
3. Trays and conduits: grouping, fill and derating; schedules and DXF/PDF output.
4. Fire-protection and drainage networks.
5. Route suggestions and clash detection.

## Open questions for the owner
1. Which formats will the architectural plans usually arrive in (PDF, DWG, DXF, images)? In what proportion?
2. What are the tray and conduit catalogs to use (widths, depths, weights, manufacturer)?
3. Which standards and books will be the sources of the rules?
4. Which layers and symbols does the engineer expect on the canvas (a first list)?
5. Is one plan per level enough, or are sections and elevations also needed?
