# ADR-0020: Drawing the routes over the architectural plan

Status: Accepted (direction; to be built in phases). Date: 2026-10-25. Extends ADR-0019 and the real route of a cable.

## Context
The engineer receives the architectural plan of the building and must decide where the pass chambers are, how the cables run, and what trays, conduits, fire-protection pipes or drains result. Today the route of a cable is typed stretch by stretch. The plan should be a canvas on which the engineer draws simply (points or squares for chambers, lines for routes) and the system turns what was drawn into the engineering.

## Decision
- **The plan is an underlay, not something the program tries to understand.** The program accepts the plan in the formats it can bring to a vector or image view with open tools: PDF (vector), DXF, DWG (converted to DXF) and, later, IFC; a scanned image is accepted as a plain underlay. It is converted to an SVG **for display only**. That SVG is a working view: **it is never a deliverable** (deliverables stay DXF and PDF, as always). Uploaded files are untrusted: the view is shown as an image (no scripts can run) and the original is kept in the project, never in git.
- **Calibration.** Every plan is scaled by the engineer: two points and the real distance between them. A project has several plans (one per level), each with its scale and level; vertical risers join levels.
- **A light drawing layer, not a CAD.** Nodes (pass chamber, board, riser, sprinkler, hydrant, drain...) placed as points or squares; lines (routes) drawn as polylines with the kind of installation (tray, buried duct, direct burial, road crossing...); layers per discipline (electrical, fire protection, drainage, storm water) that can be shown or hidden. Pan, zoom and snapping; no more than that at the start.
- **What is drawn becomes data.** A route drawn over the plan generates the stretches of the cable's real route with their kind and **length measured from the scale**, replacing the typed ones. Where several cables share a drawn line, the number of circuits per stretch (grouping) follows from it.
- **What the system derives.**
  - Electrical: the cable schedule, and trays and conduits sized from the cables that run through each stretch (fill, weight, grouping, thermal derating).
  - Fire protection: the pipe network (nodes and lengths from the plan) calculated with the engine's hydraulics.
  - Drainage and storm water: pipe diameters and slopes from flow and level.
  Each discipline has its own calculation but they share the same drawing and network.
- **Outputs** are DXF and PDF of the plan with the routes over it, and the schedules; never the SVG.

## Phases
1. Upload, convert to a view, calibrate, levels.
2. Draw nodes and routes; lengths and the real route of the cable are generated.
3. Trays and conduits: grouping, fill and derating; schedules and DXF/PDF output.
4. Fire-protection and drainage networks with their calculations.
5. Assistance: route suggestions and clash detection. Automatic recognition of walls and rooms is **not** planned; it is hard and unreliable.

## Open-source tools to evaluate (licences to check before adopting)
`ezdxf` (reads DXF, can render to SVG), LibreDWG (DWG to DXF; GPL), `pdftocairo` from poppler or MuPDF (PDF to SVG; GPL / AGPL), IfcOpenShell (IFC; LGPL), and a pan-and-zoom layer in the web app (SVG with d3-zoom, or a canvas library under MIT).

## Consequences
- (+) The route stops being typed: it is drawn once and feeds the calculation, the cable schedule and the trays.
- (-) It is the largest piece of the engineering area: a drawing editor inside the web app. Keeping its scope small (points, lines, layers, scale) is what makes it feasible.
- (-) Conversion quality depends on the file the client sends; the fallback is always an image underlay.
