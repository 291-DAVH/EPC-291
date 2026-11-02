# epc-arch

Architecture recognition: a plan that arrives as a DXF, a vector PDF or an image becomes walls (with their own thickness), doors, windows, openings and rooms, and a clean SVG with layers to work on.
One reader per source (`epc_arch.sources`: DXF, vector PDF, raster image) turns the file into the same primitives (lines, arcs, blocks); the recognizers (`epc_arch.recognizers`) only know primitives, so a new source is a new reader and nothing else changes.
`epc_arch.recognize(data, name)` returns an `Architecture` (JSON-able) and the SVG. Thresholds are data (`params.json`). Depends on `ezdxf`, `numpy`, `pillow` and `pypdfium2`; on no other engine package.
Run: `python -m epc_arch plan.dxf --out DIR` (`--background` draws the original linework faintly underneath).

How a plan is read:
- Walls by their shape: a long box of about one width with straight unbroken faces, whatever its colour or fill (solid, hatched or a bare outline). A picture is read several ways (thick strokes, lines, outlines and hatching shut into bands, neutral or dark ink only, every mark on the paper, walls at 45 degrees) and the reading that closes the plan into the most rooms is kept. Each wall keeps its own thickness; on a DXF wall layer, partitions thinner than the main walls are walls too.
- Walls are tidied into a network: two directions, shared axes, corners and T joins closed. Structural axes (long thin lines crossing each other) and the sheet frame are left out.
- Doors by their shape: a leaf square to the wall from a jamb and the quarter circle it sweeps, looked for at every wall end and every door width; the arc reaches both ends, the space it sweeps is empty, the doorway is not wall, and the doors of one plan are of similar widths. Windows: thin lines across a gap in an outside wall.
- Rooms: what the walls, with their doors and windows shut, close. Sheets with several views keep the view with rooms and doors (the plan). A PDF's written scale ("ESCALA 1:50") gives metres.

The SVG follows architectural drawing conventions: cut walls solid with closed corners, windows shut (frame and glass), doors open with a dashed swing, plain openings dashed, rooms tinted with their area, and a footer with title, scale, graphic scale and counts. Layers: `ARQ-AMBIENTES`, `ARQ-MUROS`, `ARQ-CORTES`, `ARQ-PUERTAS`, `ARQ-VENTANAS`, `ARQ-HUECOS`, `ARQ-ROTULO`.

Limits: renders and photos are refused; a raster image reads horizontal, vertical and 45-degree walls only; text, dimension lines and hatching are ignored, not read; sizes are in plan units unless the source gives its units or scale.

Training tools (in `scripts/`): `registrar_muestras.py` (sample registry by SHA-256, samples never go to git), `generar_salidas.py` (`out/out_NN.svg` per sample), `informe_aprendizaje.py` (`out/aprendizaje.html`), `planta_prueba.py` (a designed house with known truth, as SVG, DXF and PNG), `generar_biblioteca.py` (`biblioteca/` furniture symbols). What was learned from the samples and books: `biblioteca/REPERTORIO.md`.
