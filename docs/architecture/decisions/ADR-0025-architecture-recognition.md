# ADR-0025: Architecture recognition as an isolated engine

Status: accepted. Done: the engine (`epc_arch`) with readers for DXF, vector PDF and image, the layout endpoints and the editor's use of the walls. Date: 2026-10-27

## Context
Cables and pipes are drawn over an architectural plan that arrives as a DXF, a PDF or an image. To lay routes along the walls (and to know where the doors and windows are) the platform has to understand that plan, not only show it. The plan editor already turned a DXF into an SVG to look at (`epc_plan.underlay`, an ezdxf rendering) and a PDF into a picture; neither knows what a wall is.

## Decisions
1. **A package of its own, `epc_arch`, that imports no other package of the platform.** It has the same shape as the other engines (`engine/arch/`, tests, `params.json`, README) and sits in the engine layer of independent packages (no sibling imports; a test checks it). The backend runs it as a process with a time limit (`python -m epc_arch`), like the other exporters.
2. **One reader per source, one recognizer for all (Adapter + Registry).** `sources/` has a reader for DXF, for a vector PDF (with a fall-back to the picture of the page for a scan) and for an image. Each turns its file into the same primitives (lines with width, arcs, inserted blocks, layer names); `register` makes a reader available by kind and the kind is taken from the bytes. The recognizers (`recognizers/`) know only primitives, so a new source is a new module and nothing else changes.
3. **Everything downstream lives in one frame, the plan space** (x right, y down, origin top left): a vector source is scaled to a standard size, an image keeps its own pixels. The SVG, the JSON and the editor's view share that frame, so what is found lies over the picture with no conversion.
4. **Walls: two strategies, the surer first (Strategy).** A thick stroke (a band, a polyline with width) is a wall; two parallel strokes about a wall's thickness apart are its two faces. The thickness the candidates agree on is found per plan (`calibrate`), so no scale is needed; with a scale (the DXF units, or the person's) the ranges are real metres. The strategy of bands wins when it has enough votes, because the panes of a window are also two strokes a thickness apart. Layer names (`MUROS`, `WALL`...) restrict where walls are looked for.
5. **Openings come from the walls.** A line of wall that stops and starts again leaves a gap; what is in the gap says what it is: a leaf and its swing arc (also a Bézier quarter circle in a PDF) make a door, thin strokes across it a window, nothing an opening. A door drawn without a gap, and blocks named as doors or windows, are found too. Every element carries its confidence and the reason it was recognized.
6. **A scale guess, never applied by itself.** When the plan has no units, door leaves give a hint (0.9 m each) that the person may accept.
7. **The result is data and a drawing.** JSON (`architecture.json`) and an SVG with layers (`ARQ-FONDO`, `ARQ-MUROS`, `ARQ-PUERTAS`, `ARQ-VENTANAS`, `ARQ-HUECOS`). For a vector plan the SVG becomes the underlay (the engine drew it, so its frame is the frame of the findings); for an image the underlay stays and the editor draws the findings over it. The original file is kept apart from the converted underlay so it can be read again.
8. **One place renders a page of a PDF** (`epc_arch.pdf_to_png`): the picture the person sees as a plan and the one the raster reader reads have the same pixels. The backend's own copy was removed.
9. **In the editor** the recognized walls are something to snap to (their faces and corners) and a line drawn near a wall runs parallel to it.

## Limits (known, accepted)
- Tested on synthetic plans (a room with a door and a window in each source, in several units and angles), not yet on real plans: thresholds are in `params.json` and will need tuning.
- An image gives horizontal and vertical walls only and no door arcs (its doors are plain openings); diagonal walls in an image are not read.
- Text, dimensions, hatches, splines and curves other than arcs are ignored; the SVG the engine draws is a simplified drawing, not the faithful rendering of the DXF (a plan with a lot of detail loses it in the underlay).
- A PDF is read page 1 as the CAD program wrote it: nested forms and page rotation are not interpreted.
- The person cannot yet accept, correct or delete what was recognized one element at a time.
