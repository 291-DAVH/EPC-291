# epc_lighting

Lighting engine of EPC-291. From a JSON document with luminaires, interior rooms and exterior areas it calculates how many luminaires are needed, where they go, whether the room reaches its target illuminance, and what the light looks like at points of the work plane. Pure Python, no third-party dependencies, no web, no database.

## What it does

| Step | Method | Source |
|---|---|---|
| Luminaire count, interior | **Lumen method** `Phi_T = Em·S / (Cu·Cm)`, `NL = Phi_T / (n·Phi_L)` | UPV lumen-method article, eq. 1-2; UNAC ch. III §1 |
| Luminaire count, interior (alternative) | **Zonal cavity**: cavity ratio `RCR = 5h(l+w)/(lw)`, effective ceiling/floor reflectances, then the same flux equation | UNAC ch. III §2 |
| Coefficient of utilisation | Given, or read from the manufacturer's table by room index `k` (or `RCR`) and reflectances, with interpolation | UPV table 5 |
| Distribution | Uniform grid: `N_w = sqrt(N·a/b)`, `N_l = N_w·b/a`, wall distance `e/2`, spacing `e <= ratio·h` | UPV eq. 3-4, table 7; UNAC §2.5-2.6 |
| Verification | `Em = N·n·Phi_L·Cu·Cm / S >= target` | UPV eq. 5 |
| Point-by-point | `E = I·cos(theta)/r²` for horizontal, vertical or tilted surfaces; grid statistics and uniformity | point-by-point article; UNAC ch. III §6 |
| Exterior floodlights | `N = Em·S / (Phi·CBU·fm)` | UNAC ch. III §5 |
| Power and energy | installed W, W/m², W/m² per 100 lx, kWh/year | UNAC ch. III §7 |

Every estimated number (target, CU, maintenance factor, reflectances, mounting height, spacing limit) comes with a `reason` and a `confidence`. `docs/formulas.md` maps each formula to its source and module.

## How it is used

```python
import epc_lighting

result = epc_lighting.run(document)          # dict, JSON str or bytes
data = result.as_dict()                      # stable JSON-serialisable dict
```

```
python -m epc_lighting INPUT.json --out DIR
    [--enforce-spacing] [--spacing-basis height|distribution] [--point-step M] [--no-points]
```

Exit code 0 = ok (writes `DIR/<stem>.lighting.json`), 1 = `ERROR …` on stderr, anything else = unexpected failure. It writes only inside `--out`.

A minimal document (the classroom of the UPV article); see `examples/classroom.json` for rooms with photometry, the zonal method and an exterior area:

```json
{
  "schema_version": "1.0",
  "luminaires": [{"id": "L1", "lamps": 2, "lamp_flux_lm": 2400}],
  "rooms": [{
    "id": "R1", "width_m": 4, "length_m": 6, "height_m": 2.6,
    "activity": "education.classroom", "luminaire": "L1",
    "coefficient_of_utilisation": 0.97
  }]
}
```

Input schema: `src/epc_lighting/schema/input.schema.json`; output schema: `output.schema.json`. Validation messages say what to correct. Units: metres, lumens, lux, degrees. Plan axes: `x` along `length_m`, `y` along `width_m`; luminaire positions are in metres with `z` above the floor; tags are `LU-001`, `LU-002`… across the whole document.

Lumen method result for the article classroom: `k = 1.371`, `Phi_T = 9278.35 lm`, 1.93 → 2 luminaires in one row, 1.5 / 3 / 1.5 m, `Em = 310.4 lux`.

### Options

`Options(enforce_spacing=False, spacing_basis="height", compute_points=True, point_step_m=0.5)`. `enforce_spacing` adds rows/columns until the maximum spacing is respected (beyond a 10 % tolerance, which is how the article accepts 3 m against 2.8 m). `spacing_basis="distribution"` uses the ratio of the lighting system (UNAC §2.6) instead of the room-height table (UPV table 7).

## Normative data

Engine data is JSON, not code: `params.json`, `schema/`, `data/`. Norms live apart: `rules/<NORM>.rules.json` (values with clause and summary, one `review` state per rule), `standards/<NORM>.json` (title, jurisdiction, edition, where the source is kept) and `norm_data.py` (reads them; approved rules only unless `include_pending=True`). The first one is `D351-79` (Argentina, Decreto 351/79, Annex IV), all rules `pending`: the pipeline does not use them until a person reviews and approves them. The source PDF is not in the repository.

## Depends on

Python ≥ 3.10 and nothing else: no third-party packages and no other `epc_*` engine. Its layer is the independent one (`epc_titleblock | epc_symbols | epc_plan | epc_aea90364 | epc_arch | epc_lighting`). It is a pure function over a small document, so the backend can call it in process (lazy import) rather than as a subprocess.

## Known limits

- **Rectangular rooms only.** No L-shaped rooms, no obstructions, no windows or daylight. The daylight criteria of the ICARO manual are not implemented; only its uniformity ratios (min/avg ≥ 1/3, max/avg ≤ 3, max/min ≤ 10) are used, as warnings on the point-by-point grid. Those are not normative for artificial light.
- **The CU table must come from the luminaire maker.** The supplied PDFs refer to annexes (CU tables, effective reflectances, luminaire efficiency, maintenance curves) that were not included. Without a `cu` or `cu_table` the engine falls back to the one illustrative table printed in the UPV article, with a warning and confidence 0.4.
- **Interpolation differs from the article's.** Between reflectance columns the engine uses inverse-distance weighting; the article averages four table cells. For the article classroom the table gives about 0.92 where the article prints 0.96 (and then uses 0.97). The article's own figures are reproduced by giving `coefficient_of_utilisation: 0.97`.
- **Effective cavity reflectance** is the standard IES formula, not taken from the PDFs (they defer to annex tables).
- **Point-by-point is direct light only**: no inter-reflections, luminaires aimed straight down, no tilt or rotation, no glare (UGR) calculation. Angles beyond the last tabulated gamma emit nothing. The engine flags a table that emits more than the lamp flux.
- **Exterior**: the beam utilisation (CBU) comes from the isocandela curves, which are not computed; give it or accept the assumed 0.75 (confidence 0.4). Floodlights are counted, not placed.
- **Levels** are only the values quoted in the supplied material (three EN 12464-1 rows as quoted in the UPV article, and the ICARO manual's task table). The standard itself is copyrighted and not stored: confirm with the project standard, or give `target_lux`.
- **Spacing** is not checked along an axis with a single luminaire (UNAC: no spacing exists with one row).
- **Source quirks kept visible**: the article's closing exercise verifies with 5 luminaires although its own 3 × 2 grid holds 6; the engine verifies with the installed 6 (395.5 lux instead of 329.6).
- No drawing: it delivers positions and tags. DXF/PDF output and layers belong to `epc_dxf` / `epc_drawing`.
- Default work plane 0.85 m (UPV); the ICARO manual uses 0.80 m. Set `work_plane_height_m` to change it.

## Tests

```
cd engine/lighting
python -m unittest discover -s tests
```

158 tests, 98 % branch coverage. They include the worked examples of the articles, a golden file (`tests/fixtures/classroom.expected.json`, regenerate it only for an intended change and review the diff), determinism, the CLI codes, input and output schemas, and isolation rules.
