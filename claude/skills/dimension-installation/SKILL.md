---
name: "dimension-installation"
description: "Guides the full electrical dimensioning workflow for LV/MV installations per AEA 90364 / IEC 60364. Always completes all calculations before generating any SLD or diagram."
---

# Electrical Dimensioning Skill

## Golden Rule
**ALL calculations must be completed and verified before generating the SLD (diagrama unifilar) or any diagram.** The SLD is an output, not an input.

## Input: the circuits workbook

The input is the Excel file of circuits in `src/` (e.g. `src/input_for_sld_V1.xlsx`; sheets **TABLERO** and **CIRCUITOS**). Read it with `aea_pipeline.cargar_entrada` — never ask the user to retype it.
- TABLERO: `TENSION_V` (line voltage), `ICC_KA`, `FP_DEFAULT`, `SISTEMA`, `PROYECTO`, ...
- CIRCUITOS: `TAG`, `DESCRIPCION`, `CARGA` + `UNIDAD_CARGA` (A, W, kW, MW, VA, kVA, MVA, HP/CV, any capitalization; `15 kW` text also accepted) — converted to Ib by `aea_pipeline.convertir_carga` / `corriente_proyecto` (W: P/(√3·U·fp); VA: S/(√3·U), no fp; HP: with η), `PARENT_TAG`, `TOPOLOGY`, `FASE`, `LONGITUD_m`, `FP`, `RENDIMIENTO`, `KIND`, `NOTAS`.

One command does the whole circuit sizing and writes the JSON:
`python -m epc_calc.aea_pipeline src/<input>.xlsx` → `src/<input>_calculo.json` (options `-o`, `--margen-iz`, `--eta-motores`, `--temp-c`, `--k-magnetico`; it also warns when the minimum short-circuit current at the end of a circuit is below the magnetic trip). Review the AVISO lines it prints, then continue with the stages below for anything the pipeline does not cover (earthing, short-circuit per busbar, panel thermal, MV).

## Calculation Sequence (ROADMAP Order)

Follow this exact dependency order — never skip ahead:

### Etapa 0 — Datos de Partida
- Collect: building type, use, floors, area, supply type (aerial/underground), voltage level
- Transformer data: Sn (kVA), Ucc (%), vector group, Ukr, PCu
- Network data: Scc at POC, Zred
- Ambient: Ta (°C), soil ρ (Ω·m), installation environment (BA codes)

### Etapa 1 — Esquema de Puesta a Tierra
- Select: TT (default Argentina), TN-S, TN-C-S, or IT
- For TT: Ra (= RTP) × IΔn ≤ UL (UL = 50 V AEA 771.3.I col. 1; 24 V adopted). Adopted Ra = min(0.5·24/IΔn, 40 Ω) → `aea_earthing.ra_maxima`
- Max disconnection times (AEA 771.18.I) → `aea_earthing.tiempo_desconexion_max_s`; seccionales TT ≤ 1 s, TN ≤ 5 s
- Define DDR IΔn: 30mA (direct contact protection), 300mA (fire)
- Electrode design: rod/plate/horizontal conductor, depth, soil ρ → `aea_earthing.resistencia_jabalina / _conductor_horizontal / _placa_circular` (AEA 771-C.10)

### Etapa 2 — Cargas y Demanda
- Assign electrification grade: Mínimo / Medio / Elevado / Superior (AEA 771.8: Tablas 771.8.I housing, 771.8.IV offices/shops, 771.8.IX other premises, by area; AEA 770.7.I by area, covered + 50 % semi-covered) → `aea_demand.grado_electrificacion_771 / _770`
- Count minimum mandatory circuits per grade
- Build load schedule: P (W), fp, circuit type (IL/TG/TE/CC)
- DPMS = Σ general-use circuits × simultaneity coefficient + Σ specific loads (AEA 771.9 / 770.8): lighting 66 % of n·150 VA (771 housing) or 2/3 of n·60 VA (770), TUG 2200 VA, TUE 3300 VA → `aea_demand.dpms_*`, `coef_simultaneidad_771 / _770 / _conjunto`
- Id = DPMS/220 (mono) or DPMS/(√3·380) (tri) → `aea_demand.corriente_dpms`; three-phase recommended > 7 kVA or > 32 A; phase imbalance ≤ 30 % → `imbalance_phases`

### Etapa 3 — Corrientes de Cortocircuito (AEA 90909)
- Icc máx: voltage factor c = 1.10, all impedances minimum
- Icc mín: voltage factor c = 0.95, all impedances maximum, end-of-line fault
- Calculate at: transformer secondary, main panel, each distribution panel
- Formula: Icc = c × Un / (√3 × Ztotal) → `short_circuit.calcular_ik` (do NOT re-implement)
- Generator / generating-unit / transformer correction factors K_G, K_S, K_SO, K_T (AEA IT 90909-1) → `aea_icc_factors`
- Peak current (κ exact), breaking current μ·q, thermal equivalent m+n → `aea_icc_decay`; approximate κ and i_p stay in `short_circuit`

### Etapa 4 — Conductores BT
Apply ALL four criteria — the governing section is the largest:
1. **Ampacity**: Iz = Iz₀ × k1 × k2 ≥ Ib (with k1 temp correction, k2 grouping factor)
   - Installation methods: A1/A2 (conduit in wall), B1/B2 (conduit on wall), C (surface), D1/D2 (buried)
2. **Overload**: In ≤ 1.45 × Iz; Ib ≤ In
3. **Voltage drop**: terminal circuits ≤ 3 % (lighting and sockets), motors ≤ 5 % running / 15 % starting, seccionales ≤ 1 % (AEA 771.19.7 / 770.15.6) → `aea_voltage_drop.limite_caida_pct`
   - General: `voltage_drop.caida_tension` (ΔU = k·I·L·(R cosφ + X senφ), k = 2 mono / √3 tri)
   - Simplified: Tabla 771.19.IV (`drop_by_table`) or GDC coefficient (`caida_gdc`, `seccion_minima_gdc`, `longitud_maxima_gdc`)
   - Lighting end-load = 66 % (771) or 2/3 (770) of total current; sockets 100 % → `corriente_extremo`
4. **Short-circuit thermal**: I²t ≤ K²S² via `cable_thermal`; k per AEA 771.19.II → `aea_conductors.k_adiabatico_771` (Cu: PVC≤300 115 / PVC>300 103 / EPR-XLPE 143; Al: PVC 76 / XLPE 94)
5. **Harmonics**: factor by THD (AEA 771.16.XIII), neutral current I_N = 3·I_f·h3 → `aea_conductors.factor_armonicos`, `current_neutral_harmonics`
6. **Parallel conductors**: `aea_demand.factor_paralelo`; motor feeder I ≥ 1.25·In(max) + Σ In → `aea_demand.corriente_alimentador_motores`

Minimum sections (AEA 771.13.I, Cu): main lines 4 mm²; seccionales 2.5; lighting terminal 1.5; sockets 2.5; lighting with sockets 2.5; special/specific use 2.5 (MBTF 1.5); switch returns 1.5; PE 2.5 → `aea_conductors.seccion_minima_circuito`

### Etapa 5 — Protecciones BT
- ITM selection: In ≥ Ib, curve B (residential)/C (industrial)/D (motor)
- Breaking capacity Iccr ≥ Icc máx at installation point
- Verify magnetic trip: Imag ≤ Icc mín (B: 3–5×In, C: 5–10×In, D: 10–20×In)
- DDR: IΔn 30mA individual circuits, type A (general), type B (VFD/DC loads)
- SPD: Type 1 (entrance, lightning risk), Type 2 (main panel), Type 3 (sensitive equipment)
- Selectivity: ampere (In_upstream / In_downstream ≥ 1.6) or time selectivity

### Etapa 6 — Caídas de Tensión
- Calculate accumulated ΔU from the supply point through each level
- ΔU terminal = ΔU_feeder + ΔU_branch
- Document in planilla with running totals
- Flag any circuit exceeding limits

### Etapa 7 — Canalizaciones
- Conduit fill factor limits: 1 cable=53%, 2 cables=31%, 3+=40% of interior area
- Cable types permitted per AEA 771.12
- Special environments: Annex 771-B (IP requirements, cable type restrictions)
- Minimum conduit diameter from fill calculation

### Etapa 8 — Tableros Eléctricos
- IP rating per environment (IP2X min, IP4X wet, IP5X dust)
- Reserve space ≥ 20% of installed modules
- Busbars sized for Icc máx (dynamic and thermal)
- Bipolar cuts on all active conductors; neutral switched with phase in TT
- Verify enclosure temperature rise: P_tot = P_dp·1.2 + P_au ≤ P_de with K by circuit count and W/pole (AEA 770 Annex B) → `aea_panel_thermal`

### Etapa 9 — Cableado MT (if applicable)
- Select cable per IRAM 2178-2: TERMOLITE MT / ZEROTOX MT / ECOPEX MT
- Voltage rating Uo/U: 3.3kV, 6.6kV Cat I/II, 13.2kV, 33kV
- Ampacity per IEC 60287: soil corrections k_ρ, k_T, grouping k_g
- Metallic shield section: S_shield ≥ Icc_fault × √t / 141 (Cu shield, K=141)
- Voltage drop MT: ΔU = √3 × (R×cos φ + X×sin φ) × L × I

### Etapa 10 — Protecciones MT (if applicable)
- MV fuse selection: In ≥ 1.3 × I_nominal; Iccr ≥ Icc máx MT
- Transformer protection relay functions (ANSI): 50/51 (overcurrent), 87T (differential), 27/59 (under/overvoltage), 64 (earth fault)
- Verify fuse-to-cable coordination: I²t_fuse ≤ K²S²_cable

### Etapa 11 — Tipos de Circuitos
- IL (Iluminación): 1.5mm² Cu, 10A max load, DDR 30mA
- ITE (Iluminación 3-phase): same rules, 3-phase supply
- TG (Tomas generales): 2.5mm² Cu, 16A sockets
- TE (Tomas especiales): 2.5–6mm² Cu, dedicated circuits (AC, dishwasher, dryer, EV)
- CC (Cargas específicas): sized per actual load, dedicated circuit
- Verify minimum mandatory circuits per electrification grade (AEA 771.8)

### Etapa 12 — Sistema de Puesta a Tierra
- PE conductor sections per AEA 771-C.II: S≤16mm²→S_PE=S; S=16–35mm²→S_PE=16mm²; S>35mm²→S_PE=S/2 (other material × k1/k2) → `aea_earthing.seccion_pe_mm2`; PEN ≥ 10 mm² Cu / 16 mm² Al
- Equipotential bonding: all exposed conductive parts, structural elements, pipes
- Final RTP verification with actual electrode design
- Confirm Ra × IΔn ≤ UL condition → `aea_earthing.verifica_ra`
- Bathrooms (AEA 701) and EV charging (AEA 722) checks → `aea_special_locations`

### Etapa 13 — Verificaciones Finales
- Cross-check all four conductor sizing criteria
- Verify protection coordination (ampere and/or time selectivity)
- Confirm accumulated voltage drops within limits
- Conduit fill verified at all junction points
- Panel reserve ≥ 20%
- Earthing Ra condition satisfied

## Output: a single JSON (no PDF)

**The ONLY deliverable is one JSON file, `<PROJECT>_calculo.json`, that feeds `sld-generator`. Never generate PDF, Word or Markdown reports.**
Intermediate results are shown in the conversation as tables; the final calculation is exported with `epc_calc.aea_pipeline` (from the Excel in `src/`) or `aea_export.py`.

Format (one key per circuit ID; see `epc_calc/example_calculo.json`):

```json
{
 "M-01": {"In": 25, "Ib": 19.7, "icu": 36, "S": 6, "dU": 0.69, "disp": "MCB > KM > OL (25 A)"}
}
```

| Field | Meaning | Unit |
|---|---|---|
| `In` | rated current of the protection | A |
| `Ib` | design current of the circuit | A |
| `icu` | breaking capacity of the protection | kA |
| `S` | adopted conductor section | mm² |
| `dU` | accumulated voltage drop from the supply point | % |
| `disp` | protection/switching chain, free text (e.g. `MCB > KM > OL (25 A)`) | — |

Rules: no extra fields; `In ≥ Ib`; `In` must appear in `disp`; `S` from the standard series; `dU` within the AEA limits (Etapa 6). Build each record with `aea_export.circuito_json(...)` and write with `aea_export.export_calculation(datos, "<PROJECT>_calculo.json")`, which validates and refuses any non-`.json` path. Check an existing file with `python -m epc_calc.aea_export validar <file>`.

Only after Etapas 0–13 are verified and the JSON validates:
1. Hand the JSON to **sld-generator** (the SLD reflects the calculated values).
2. Show the user the summary table and any FAIL/AVISO items in the conversation.

## Conversation Tables

For each calculation stage, show a structured table with columns:
- Circuit ID, Description, Calculated value, Limit, Governing criterion, Status (OK/FAIL)

Never present a partial result as final. Always flag FAIL items before proceeding.

## Formula Library (reusable scripts)

All formulas live in the `epc_calc` package (`engine/calc`) (pure Python stdlib, no duplicates). **Look up before coding**:
`python -m epc_calc.aea_catalog --buscar <word>` or read `FORMULAS_AEA.md` / `formulas_aea.json`.

| Module | Domain |
|---|---|
| `aea_demand` | Electrification grade, DPMS, simultaneity, I_B, imbalance, motors, parallel |
| `aea_voltage_drop` | Tabla 771.19.IV, GDC, ΔU limits, end-load |
| `aea_earthing` | Ra (Tabla 771.3.I), disconnection times, electrodes, PE |
| `aea_conductors` | Minimum sections, k table, overload, harmonics, combustible volume |
| `aea_panel_thermal` | Switchboard thermal verification (770 Annex B) |
| `aea_icc_factors` | K_G, K_S, K_SO, K_T, K_G,S, K_T,S (AEA IT 90909-1) |
| `aea_icc_decay` | κ exact, μ, λ, q, m, n |
| `aea_special_locations` | AEA 701 (bathrooms), 722 (EV) |
| `aea_pipeline` | Excel of circuits (`src/`) → sizing → JSON |
| `aea_export` | Build, validate and write the calculation JSON (no PDF) |

Pre-existing modules still own: `voltage_drop`, `short_circuit` (Z_Qt, Z_T, κ approx., K_T [65]), `cable_thermal`, `current_and_loads`, `conductor_selection`. Every function is a DRAFT marked `[VERIFICAR]` until the user validates it; AEA 770 (2017) supersedes 771 (2006) — state which edition each result follows.

## Runtime
The code is a Python package from `engine/` (`epc_calc`). In a repository checkout set `PYTHONPATH=engine/calc/src` (use `;` as separator on Windows) or run `pip install -e engine/<area>`; in an installed plugin set `PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/lib"`. Run modules with `python -m <module>`.
