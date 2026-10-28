# Formulas, sources and where they live

UPV = "Luminotecnia: Cálculo según el método de los lúmenes" (Universitat Politècnica de València).
UPV-PP = "Luminotecnia: Cálculo según el método del punto por punto" (same authors).
UNAC = Universidad Nacional del Callao, Ingeniería de iluminación, chapter III.
ICARO = Manual de iluminación, Manuales de diseño ICARO (Las Palmas de Gran Canaria).

| Formula | Source | Module |
|---|---|---|
| `k = a·b / (h·(a+b))` direct, semi-direct, mixed, general diffuse | UPV table 3; UNAC §1 | `geometry.room_index` |
| `k = 3·a·b / (2·(h+h')·(a+b))` indirect, semi-indirect | UPV table 3; UNAC §1 | `geometry.room_index` |
| Mounting height: as high as possible; high rooms `h = 2/3 (H-h')` min, `4/5 (H-h')` optimum (direct); `d' = 1/5 (H-h')`, `h = 3/4 (H-h')` (indirect) | UPV tables 1-2 | `geometry.mounting_height`, `data/lighting_systems.json` |
| `Phi_T = Em·S / (Cu·Cm)` | UPV eq. 1; UNAC §1 | `methods/lumen.py`, `methods/zonal.py` |
| `Phi_r = Phi / eta_L` | UNAC §1 | `pipeline._required_count` (field `efficiency`) |
| `NL = Phi_T / (n·Phi_L)`, rounded up | UPV eq. 2 | `pipeline._required_count` |
| `N_w = sqrt(N·a/b)`, `N_l = N_w·b/a` | UPV eq. 3-4 | `layout.grid_counts` |
| Wall distance `e/2` | UPV fig. 8 | `layout.plan` |
| Max spacing by room height (> 10 m: 1.2h; 6-10: 1.5h; 4-6: 1.5h; ≤ 4: 1.6h) | UPV table 7 | `data/spacing.json`, `layout._by_height` |
| Max spacing by system (direct 1.2h, semi-direct 1.5h, semi-indirect 1.5h, indirect 1.6h) | UNAC §2.6 | `data/lighting_systems.json` |
| `Em = NL·n·Phi_L·Cu·Cm / S >= Etables` | UPV eq. 5 | `pipeline._verify` |
| `RCR = 5·h·(l+w) / (l·w)` | UNAC §2 | `geometry.cavity_ratio` |
| Effective cavity reflectance `rho·A0 / (As - rho·As + rho·A0)` | IES standard formula (UNAC defers to annex tables not supplied) | `geometry.effective_reflectance` |
| `E_H = I·cos³(alpha)/H²`, `E_V = I·cos²(alpha)·sin(alpha)/H²` | UPV-PP; UNAC §6 | `pointcalc.illuminance_at` (vector form) |
| `I_real = I_graph (cd/klm) · Phi / 1000` | UPV-PP step B | `photometry.intensity_cd` |
| `N = Em·S / (Phi·CBU·fm)`; CBU 0.6-0.9; fm 0.65 open, 0.85 closed | UNAC §5 | `exterior.calculate` |
| Cm: clean 0.8, dirty 0.6 (usual range 0.5-0.8) | UPV table 6; UNAC §1 | `data/maintenance.json` |
| Reflectance defaults 0.5 / 0.3 / 0.1 and the material ranges | UPV table 4 | `data/reflectances.json` |
| CU table example (ERCO downlight, percent) | UPV table 5 | `data/cu_generic.json` |
| Levels: classroom 300, evening classes 500, reading room 500; task table | UPV fig. 2 (EN 12464-1 as quoted); ICARO I.1 §2.1 | `data/levels.json` |
| Uniformity ratios 1/3, 3, 10 | ICARO I.5 §3 (daylight criteria, reused as warnings) | `params.json` |
| `kWh = kW · hours` | UNAC §7 | `energy.summarise` |

## Differences between the sources, and what the engine does

- Room-index formulas agree between UPV and UNAC (semi-direct and mixed use the direct formula; semi-indirect and indirect use the indirect one).
- UPV table 7 chooses the spacing limit by room height; UNAC §2.6 by lighting system. Both are available (`spacing_basis`); the default is UPV's because it reproduces the article example.
- UPV prints `Cu = 0.96` from its interpolation and then substitutes `0.97`; the engine reproduces the printed `Phi_T = 9278.35 lm` when `coefficient_of_utilisation` is 0.97.
- UPV's closing exercise verifies with 5 luminaires although its grid holds 3 × 2 = 6; the engine verifies with the installed count.
- UPV-PP prints 493.18 lux; the exact value of its own numbers is about 492.4 (the article rounds `cos³` to 0.73 and `H²` to 1.56). The test accepts both within 1.5 lux.
