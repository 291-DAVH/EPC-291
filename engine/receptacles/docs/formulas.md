# Formulas of epc_receptacles

| What | Formula | Source | Module |
|---|---|---|---|
| Outlets by area | `N = max(min, ceil(A / per_m2))`, `A = length · width` | typical value of the use, to verify | `pipeline._required` |
| Outlets by perimeter | `N = max(min, ceil(P / per_m))`, `P = 2 (length + width)` | warehouse: AEA 90364-7-771, rule `tomacorrientes.deposito_perimetro` (9 m, at least 2); the other uses are typical values to verify | `pipeline._required` |
| Fixed | `N = min` | typical value of the use, to verify | `pipeline._required` |
| Position `i` of `N` | arc length `s = (i + 0.5) · P / N` along the walls south → east → north → west, then moved `corner_clearance_m` away from the corners | this engine | `layout.positions` |
| Mounting height | `z >= min` (771: 0.15 m), `min <= z <= max` (770: 0.2 to 0.3 m), wet rooms `z >= 0.2 m` | AEA 90364-7-771 and 770, rules `tomacorrientes.altura_arista_inferior_771/770`, `tomacorrientes.baldeado_771` | `pipeline._checks` |
| Load | `S = N · power_va` | catalogue of outlets | `pipeline._room` |
| Circuits | `ceil(N / max_outlets)` of the family | typical value of the plan engine (15 TUG, 1 TUE), to verify | `pipeline._room` |

No discrepancy between sources was found: the typical values are not taken from a source that can disagree; they are marked `confidence` 0.4 and wait for the review.
