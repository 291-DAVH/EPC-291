# 07 · Verificaciones complementarias

Estas verificaciones están implementadas como módulos, pero **no se aplican automáticamente en el cálculo del tablero**. Se usan al revisar un caso puntual.

## 7.1 Sección térmica en cortocircuito (adiabático)

**Pasos.** S ≥ I · √t / k, donde k depende del aislamiento y el material (tabla 771.19.II): PVC 115 Cu / 76 Al; XLPE 143 Cu / 94 Al. Con t en segundos e I en amperes, S resulta en mm².

**Módulos:** `cable_thermal.seccion_minima_mm2`, `cable_thermal.verificar_i2t`, `aea_conductors.k_adiabatico_771`.

## 7.2 Protección contra contactos indirectos

**Pasos según el esquema:**

- **TN:** Zs · Ia ≤ U0 (230 V). Ia es la corriente que asegura el disparo en el tiempo de la tabla 771.18.I: para 230 V, 0,2 s en circuitos terminales y 5 s en seccionales.
- **TT:** Ra · Ia ≤ UL (50 V). Ra máxima = UL / Ia.
- **IT (segunda falla):** 2 · Ia · Zs ≤ U (400 V sin neutro distribuido; U0 con neutro distribuido).

**Módulos:** `aea_protection.verifica_tn`, `aea_protection.verifica_tt`, `aea_protection.verifica_it_segunda_falla`, `aea_earthing.tiempo_desconexion_max_s`, `aea_earthing.ra_maxima`.

## 7.3 Sección del conductor de protección (PE)

**Pasos.** Se toma de la tabla 771-C.II según la sección de fase; con material distinto se multiplica por k_fase / k_pe.

**Módulo:** `aea_earthing.seccion_pe_mm2`.

## 7.4 Tableros: verificación térmica

**Pasos.**

1. Potencia disipada de cada aparato: P = K² · (W por polo) · polos.
2. Potencia total del tablero: P_tot = P_dp + 0,2 · P_dp + P_au.
3. Factor K de circuitos (tabla 770-B.XII) y nivel.
4. Cumple si P_tot ≤ potencia disipable del envolvente.

**Módulos:** `aea_panel_thermal`.

## 7.5 Armónicos y neutro

**Pasos.** THD y factor de reducción de la tabla 771.16.XIII; corriente de neutro I_N = 3 · I_f · h3/100.

**Módulo:** `aea_conductors.factor_harmonics`, `aea_conductors.current_neutral_harmonics`.

## 7.6 Locales especiales

- **Baños (701):** radio de zona 2 con tabique y límite de inducción 2,5 · 10⁻⁵ T.
- **Vehículos eléctricos (722):** máximo 8 tomas por circuito y circuito mayor o igual que la mitad de la suma de bocas y 10 A.

**Módulos:** `aea_special_locations`.
