# epc-arch

Architecture recognition: a plan that arrives as a DXF, a vector PDF or an image becomes walls, doors and windows, and an SVG with layers (`ARQ-MUROS`, `ARQ-PUERTAS`, `ARQ-VENTANAS`, `ARQ-HUECOS`) to work on.
One reader per source (`epc_arch.sources`: DXF, vector PDF, raster image) turns the file into the same primitives (lines, arcs, blocks); the recognizers (`epc_arch.recognizers`) only know primitives, so a new source is a new reader and nothing else changes.
`epc_arch.recognize(data, name)` returns an `Architecture` (JSON-able) and the SVG. Thresholds are data (`params.json`). Depends on `ezdxf`, `numpy`, `pillow` and `pypdfium2`; on no other engine package.
Run: `python -m epc_arch plan.dxf --out DIR`.
Limits: a raster image gives orthogonal walls only and no door arcs; text, hatches and curves other than arcs are ignored; sizes are in plan units (metres only when the source says its units or a scale is given).
