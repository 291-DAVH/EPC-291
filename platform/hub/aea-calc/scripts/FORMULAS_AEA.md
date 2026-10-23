# Catálogo de fórmulas AEA (generado por `aea_catalog.py`)


## `aea_demand` — Demanda y corrientes de proyecto
*Norma:* AEA 771 §9, 770 §8

| Función | Fórmula / descripción |
|---|---|
| `coef_simultaneidad_conjunto(n_unidades, grado)` | Tabla 771.9.III para conjuntos de viviendas/locales: columna Mín/Medio o Elev/Sup. |
| `coef_simultaneity_770(n_circuitos)` | Tabla 770.8.II por cantidad mínima de circuitos: 2→1; 3→0,8; 5→0,7; 6→0,6 (1 circuito: 1,0). |
| `coef_simultaneity_771(grado)` | Tabla 771.9.II: Mínimo 1; Medio 0,9; Elevado 0,8; Superior 0,7. |
| `corriente_alimentador_motores(in_motores_a, fs_resto=1.0)` | I ≥ 1,25·In(mayor) + Σ In(resto)·fs. |
| `current_msd(dpms_va, fases)` | I_B = DPMS/220 (mono) o DPMS/(√3·380) (tri). |
| `dpms_total(p_generales_va, coef, p_especificas_va=0.0)` | DPMS = Σ(uso general)·coef + Σ(cargas específicas). |
| `factor_parallel(cables_por_fase, multipolar=False, radiacion_solar=False)` | fs = 1 con 2 o 4 cables/fase (unipolares), 0,8 en otros casos y en multipolares; ×0,85 con radiación solar. |
| `grade_electrification_770(superficie_cubierta_m2, superficie_semicubierta_m2=0.0)` | Grado según 770 (Tabla 770.7.I): superficie = cubierta + 50 % de semicubierta; ≤60, ≤130, ≤200, >200 m². |
| `grade_electrification_771(tipo, superficie_m2)` | Grado según 771 (Tablas 771.8.I viviendas, 771.8.IV oficinas y locales, 771.8.IX otros locales). tipo: 'vivienda' / 'oficina' / 'local'. |
| `imbalance_phases(currents_to)` | (Imax − Imin)/Imax en %; cumple si ≤ 30 % (770.8.3.4). |
| `msd_circuits(n_tug=0, n_tue=0, n_ilum_con_tomas=0)` | Σ VA de circuitos: TUG y alumbrado con tomas derivadas 2200 VA c/u; TUE 3300 VA c/u. |
| `msd_lighting_general(n_bocas, norma='771', tipo='vivienda')` | 771: 66 % de n·150 VA (vivienda) o 100 % (oficina/local); 770: 2/3 de n·60 VA. |
| `requiere_trifasico(dpms_va, i_a=None)` | Trifásico recomendado si DPMS > 7 kVA o I > 32 A. |

## `aea_voltage_drop` — Caída de tensión (tablas, GDC, límites)
*Norma:* AEA 771 §19.7, 770 §15.6

| Función | Fórmula / descripción |
|---|---|
| `caida_disponible_terminal_pct(limite_total_pct, caida_seccional_pct)` | Margen del circuito terminal = límite total − caída ya consumida aguas arriba (≥ 0). |
| `caida_gdc(i_a, longitud_m, seccion_mm2, material='cu', fases=1, un_v=None, arranque=False)` | ΔU = GDC·I·L/S. un_v por defecto 220 (mono) o 380 (tri). |
| `coeficiente_gdc(material, fases, arranque=False, seccion_mm2=None)` | GDC [V·mm²/(A·m)]. En arranque (cosφ 0,3) requiere seccion_mm2 (≤70). |
| `corriente_extremo(i_total_a, tipo, norma='771')` | Corriente equivalente concentrada en el extremo: iluminación 66 % (771) o 2/3 (770); tomas 100 %. |
| `drop_by_table(i_a, longitud_m, seccion_mm2, un_v=220.0)` | ΔU = (V/A·km)·I·L[km]. Devuelve {'delta_u_v','delta_u_pct'}. |
| `drop_unit_table(seccion_mm2)` | V/(A·km) de la Tabla 771.19.IV (monofásico, cosφ 0,8). |
| `limite_caida_pct(tipo)` | Límite [%] por tipo: iluminacion, tomacorrientes, motor_regimen, motor_arranque, seccional. |
| `longitud_maxima_gdc(i_a, seccion_mm2, du_adm_pct, material='cu', fases=1, un_v=None, arranque=False)` | L = ΔU_adm·S/(GDC·I) [m]. |
| `seccion_minima_gdc(i_a, longitud_m, du_adm_pct, material='cu', fases=1, un_v=None)` | S = GDC·I·L/ΔU_adm [mm²] (régimen, cosφ 0,8). |
| `verify_drop(caida_pct, tipo)` | True si la caída no supera el límite del tipo. |

## `aea_earthing` — Puesta a tierra, diferenciales y electrodos
*Norma:* AEA 771 §3, §18, Anexo C

| Función | Fórmula / descripción |
|---|---|
| `ra_maxima(i_dn_a)` | Tabla 771.3.I: {'col1_50v','col2_24v','adoptada'} [Ω]. |
| `resistance_conductor_horizontal(rho, largo_m, diametro_m, prof_m, simplificada=False)` | R de un conductor desnudo enterrado horizontalmente [Ω]. |
| `resistance_parallel(resistencias_ohm)` | Electrodos suficientemente separados: 1/R = Σ 1/Ri. |
| `resistance_rod(rho, largo_m, diametro_m, simplificada=False)` | R de una jabalina vertical [Ω]. Simplificada: 0,75/1,0/1,2 ·ρ/L según L/d. |
| `resistencia_placa_circular(rho, diametro_m, prof_m)` | R de una placa circular de diámetro D a profundidad h [Ω]. |
| `seccion_pe_mm2(s_fase_mm2, k_fase=1.0, k_pe=1.0)` | Tabla 771-C.II; con material distinto multiplicar por k_fase/k_pe. |
| `tiempo_desconexion_max_s(esquema, un_v, corriente='ca')` | Tabla 771.18.I. esquema 'TN'/'TT'; un_v entre 50 y 400; corriente 'ca'/'cc'. |
| `tiempo_seccional_max_s(esquema)` | Circuitos seccionales: TT ≤ 1 s, TN ≤ 5 s. |
| `verifica_ra(ra_ohm, i_dn_a)` | True si Ra ≤ valor adoptado. |

## `aea_conductors` — Conductores: secciones, sobrecarga, armónicos
*Norma:* AEA 771 §13, §16, §19; 770 §11

| Función | Fórmula / descripción |
|---|---|
| `current_corrected(i_a, factor)` | I' = I/factor (corriente a considerar para elegir el cable). |
| `current_neutral_harmonics(i_fase_a, h3_pct)` | I_N = 3·I_f·h3/100. |
| `current_phase_three_phase(p_w, u_v, cos_fi)` | I_f = P/(√3·U·cosφ). |
| `d_desde_thd(thd_pu)` | D² = THD²/(1−THD²) (p.u.). |
| `distorsion_d_pct(armonicos)` | D [%] respecto de la fundamental. |
| `factor_harmonics(thd3_pct)` | Tabla 771.16.XIII: devuelve {'factor','aplicado_a'} según el THD (3.º armónica) [%]. |
| `iz_admisible(seccion_mm2, cargados=3)` | Tabla 771.16.I [A]: Cu/PVC, 40 °C, método B1. cargados = 2 (monofásico) o 3 (trifásico). |
| `k_adiabatico_771(aislacion, material)` | Tabla 771.19.II. |
| `resistencia_cu_ohm_km(seccion_mm2, temp_c=70.0)` | R(θ) = R20·(1 + 0,00393·(θ − 20)) [Ω/km]; 70 °C = temperatura máxima del PVC en servicio. |
| `seccion_pen_minima_mm2(material)` | PEN ≥ 10 mm² Cu / 16 mm² Al. |
| `section_min_circuit(tipo)` | Tabla 771.13.I [mm²]. |
| `thd_desde_d(d_pu)` | THD² = D²/(1+D²) (p.u.). |
| `thd_pct(armonicos)` | THD [%] respecto del valor eficaz. armonicos = {n: h_n} (n=1 fundamental, cualquier unidad común). |
| `verifica_poder_corte(pdc_a, i_k_a)` | PdC ≥ I''k. |
| `verify_overload(i_b_a, i_n_a, i_z_a, i_2_a=None)` | I_B ≤ I_n ≤ I_Z y, si se da I_2, I_2 ≤ 1,45·I_Z. Devuelve dict de comprobaciones. |
| `volumen_combustible_dm3_m(diametro_ext_mm, secciones_conductores_mm2)` | V = π·De²/4000 − ΣS/1000 [dm³/m]. |

## `aea_panel_thermal` — Verificación térmica de tableros
*Norma:* AEA 770 Anexo B; 771 Anexo H

| Función | Fórmula / descripción |
|---|---|
| `current_nominal_equivalent(i_ne_a, ke=0.85)` | I_nq = I_ne·K_e. |
| `factor_k_circuitos(n_circuitos)` | Tabla 770-B.XII. |
| `factor_k_nivel(i_nu_cabecera_a, k_padre, i_nu_hijos_a)` | K_nivel = I_nu_cabecera·K_padre/ΣI_nu_hijos. |
| `poder_corte_minimo_diferencial_a(i_n_a)` | Tabla 770-B.X (2P y 4P): 25/40 A→500; 63 A→630; 80 A→800; 100 A→1000. |
| `potencia_disipada_aparato_w(i_n_a, polos, k=1.0)` | P_d = K²·(W/polo)·polos. |
| `potencia_disipada_polo_w(i_n_a)` | Tabla 770-B.XI [W/polo]. |
| `potencia_tablero_w(p_dp_w, p_aparatos_aux_w=0.0)` | P_tot = P_dp + 0,2·P_dp + P_au. |
| `verify_panel(p_tot_w, p_admisible_w)` | P_tot ≤ P_de. |

## `aea_icc_factors` — Factores K de impedancia (Icc)
*Norma:* AEA IT 90909-1 §2.1–2.2, §2.3, §2.9

| Función | Fórmula / descripción |
|---|---|
| `c_max_desde_tension(u_q_max, un)` | [15] c_max ≈ U_Qmax/Un. |
| `defecto_tierra_rigido(u_le, u_ye)` | True si U_L,E/U_Y,E ≤ 1,4 (red puesta rígidamente a tierra). |
| `delta_i_kmax(delta_u_max)` | [12] Δi''kmax = 1/(1+Δu_max) − 1 (Δu en p.u.). |
| `ik_generador(c, un, k_gen, z_g)` | [19] I''kG [A] con Z_G complejo (R_G + jX''d). |
| `ik_grupo_conmutador(c, un_q, t_r, z_g, z_thv, k_sgrp)` | [32] I''kS [A]; z_g y z_thv complejos (Ω) referidos a AT (Z_THV = t_r²·Z_TLV). |
| `ik_trafo_con_red(c, un, z_t, k_t, z_qt)` | [59] I''kT = c·Un/(√3·/Z_T·K_T + Z_Qt/) [A]; Z complejos. |
| `k_g(un, u_rg, c_max, x_d2_pu, sen_fi_rg)` | [22] K_G. |
| `k_gs(c_max, x_d2_pu, sen_fi_rg)` | [38]/[45a] K_G,S. |
| `k_gso(p_g, c_max, x_d2_pu, sen_fi_rg)` | [52] K_G,SO. |
| `k_s(un_q, u_rg, u_rtlv, u_rthv, c_max, x_d2_pu, x_t_pu, sen_fi_rg)` | [31] K_S (grupo con conmutador bajo carga). |
| `k_so(un_q, u_rg, p_g, u_rtlv, u_rthv, c_max, x_d2_pu, sen_fi_rg, p_t=0.0)` | [49a] (p_t=0) / [49b] (con (1 − p_T), el caso de mayor corriente). |
| `k_t_general(un, u_b, c_max, x_t_pu, i_tb_sobre_irt, sen_fi_tb)` | [62]/[63] K_T = Un/U^b·c_max/(1 + x_T·(I^b_T/I_rT)·senφ^b_T). |
| `k_ts(c_max, x_t_pu, x_d_pu=None, sen_fi_rg=None)` | [43] con x_d (reactancia síncrona) o [45b] con senφ_rG: K_T,S. |
| `k_tso(c_max, u_rthv, un_q)` | [54] K_T,SO = c_max·U_rTHV/U_nQ. |
| `motores_baja_tension_despreciables(suma_irm_a, ik_red_a)` | [110] ΣI_rM ≤ 0,01·I''kQ (con I_LR/I_rM = 5). |
| `motors_contribution_negligible(ik_motores_a, ik_red_a)` | [108] I''kM ≤ 0,05·I''kQ. |
| `reactancia_red_lv_ohm(c_q, un_q, ik_q, u_rtlv, u_rthv)` | [61] X_Qt = c_Q·U_nQ/(√3·I''kQ)·U²_rTLV/U²_rTHV. |
| `reactancia_trafo_ohm(u_xr_pct, u_rtlv, s_rt)` | [60] X_T = u_Xr/100·U²_rTLV/S_rT (U [V], S [VA]). |

## `aea_icc_decay` — κ, μ, λ, q, m, n (Icc)
*Norma:* AEA IT 90909-1 §2.4–2.8

| Función | Fórmula / descripción |
|---|---|
| `constante_aperiodica_s(kappa, f_hz)` | [96c] T_aN ≈ −1/(2f·ln(κ−1)), válido con 1 < κ < 2. |
| `constante_tiempo_mu_q(t_min, mu, q)` | T_μq = −t_min/ln(μ·q) [s] (requiere 0 < μ·q < 1). |
| `constantes_tiempo(t2_0, t1_0, x_d2, x_d1, x_d, x_n=0.0)` | [80] (T''N, T'N) [s] a partir de T''0 y T'0 de circuito abierto equivalentes. |
| `corriente_alterna_t(t, ik2, ik1, ik, t2_n, t1_n)` | [78] I_k,ac(t). |
| `corrientes_generador(e2, e1, e, x_d2, x_d1, x_d, x_n=0.0)` | [79] (I''k, I'k, Ik). E en V de fase; X en Ω. |
| `current_peak_to(kappa, ik_a)` | [67] i_p = κ·√2·I''k. |
| `current_steady_to(lambda_f, i_rg_a)` | [83]/[84] I_k = λ·I_rG. |
| `current_thermal_equivalent_to(ik2_a, m, n)` | [93] I_th = I''k·√(m+n). |
| `factor_m(kappa, f_hz, t_k_s)` | [100] m = [e^(4f·T_k·ln(κ−1)) − 1]/(2f·T_k·ln(κ−1)); 1 < κ < 2. |
| `factor_n_generico(ik2, ik1, ik, t_k, t2_dn, t1_dn)` | [102a] con T_SN: 1/T_SN = 1/T''dN + 1/T'dN. |
| `factor_n_simplificado(ik2, ik1, ik, t_k, t1_dn)` | [102b] con T''dN ≈ 0,1·T'dN. |
| `factor_q(ib_motor_a, mu, ik_motor_a)` | [91] q = I_bM/(μ·I''kM). |
| `kappa_exacto(r_ohm, x_ohm, pasos=20000)` | [72] κ = máx sobre ωt∈(0, 2π) de sen(ωt−γ) + e^(−(R/X)ωt)·senγ. |
| `mu_generador(t_min, t2_n, x_d2, x_d1, x_n=0.0)` | [81] μ ≈ [1 − (X''d+XN)/(X'd+XN)]·e^(−t_min/T''N) + (X''d+XN)/(X'd+XN). |
| `voltage_internal_rated(u_rg, x_dsat_pu, sen_fi_rg)` | [90] E_r = U_rG/√3·√(1 + x²_dsat + 2·x_dsat·senφ_rG). |
| `voltage_internal_subtransient(u_rg, x_d2_pu, sen_fi_rg)` | [89] E'' = U_rG/√3·(1 + x''d·senφ_rG). |

## `aea_special_locations` — Baños (701) y vehículos eléctricos (722)
*Norma:* AEA 701, 722

| Función | Fórmula / descripción |
|---|---|
| `factor_demand(demanda_max, carga_instalada)` | 722: factor de demanda = demanda máxima/carga instalada (mismas unidades). |
| `induccion_admisible(i_a, distancia_m)` | True si B ≤ 2,5·10⁻⁵ T. |
| `induccion_conductor_t(i_a, distancia_m)` | B = μ0·i/(2π·R) [T] a la distancia R del conductor (701). |
| `load_multiple_complies(n_tomas, n_bocas, i_circuito_a, i_max_boca_a)` | 722: ≤ 8 tomas; circuito ≥ ½·(bocas·I_máx) y ≥ 10 A. Devuelve dict. |
| `radio_zona2_con_tabique_m(ancho_tabique_m)` | Radio de la zona 2 [m] = 0,60 − a (701). |

## `aea_pipeline` — Excel de circuitos → dimensionado → JSON
*Norma:* AEA 771 §13, §16, §19.7

| Función | Fórmula / descripción |
|---|---|
| `calcular_desde_xlsx(ruta_xlsx, ruta_json=None, alimentador=None, **opc)` | Lee el Excel, calcula, valida, escribe el JSON y la MC/SP del alimentador principal. |
| `calculate(tablero, circuitos, margen_iz=1.0, eta_motores=False, temp_c=70.0, k_magnetico=10)` | Dimensiona todos los circuitos. Devuelve (datos_json, avisos) con `datos_json` listo para `aea_export`. |
| `convert_load(carga, unidad=None)` | Normaliza la carga a (valor en la unidad base, base) con base 'a' (A), 'w' (W), 'va' (VA) o 'hp' (W mecánicos). |
| `corriente_proyecto(c, u_linea, fp_def, eta_motores=False)` | Ib [A] del circuito desde CARGA/UNIDAD_CARGA (A, W, kW, MW, VA, kVA, MVA, HP); None si no tiene carga (padre). |
| `current_sc_min(u_linea, sc_busbar_ka, r_ohm, x_ohm, fases, c_max=1.05, c_min=0.95)` | Icc mínima [A] al final de un circuito, con R a temperatura de servicio. |
| `leer_xlsx(ruta)` | Devuelve {nombre_hoja: [[valores de la fila], ...]} (texto o número; None si vacío). |
| `load_input(ruta)` | Lee TABLERO y CIRCUITOS. Devuelve (tablero: dict, circuitos: lista de dict con claves en mayúsculas). |
| `type_circuit(c, tiene_hijos)` | 'seccional' / 'motor' / 'iluminacion' / 'tomacorrientes' (para límites y sección mínima). |

## `aea_tables` — Tablas de capacidad de cables y factores de corrección
*Norma:* AEA 771 §16 (771.16.I a XI)

| Función | Fórmula / descripción |
|---|---|
| `cargar(ruta=None)` | Devuelve el contenido de `aea_tables.json` (con caché por ruta). |
| `constante(nombre)` | Devuelve una constante del motor (clave de `constantes`, p. ej. '771.19.II_k_adiabatico'). |
| `factor_agrupamiento_aire(item, n_circuitos)` | Tabla 771.16.IV: item '1'..'5'; para n mayor que el último valor, se usa el último. |
| `factor_agrupamiento_canos(circuitos, trifasicos=True)` | Tabla 771.16.II.b: 2 o 3 circuitos en un mismo caño (monofásicos u trifásicos). |
| `factor_agrupamiento_enterrado(tabla, n_circuitos, separacion_idx)` | Tablas 771.16.VII.c / d1 / d2: `tabla` en {'c','d1','d2'}; `separacion_idx` 0.. según columnas. |
| `factor_resistividad(metodo, rho_kmw)` | Tabla 771.16.VII.b: método 'D1' (caños enterrados) o 'D2' (directamente enterrado). |
| `factor_temperatura_aire(aislacion, temp_c)` | Tabla 771.16.II.a: factor por temperatura ambiente distinta de 40 °C. |
| `factor_temperatura_suelo(aislacion, temp_c)` | Tabla 771.16.VII.a: factor por temperatura del suelo distinta de 25 °C. |
| `iz_corregida(iz_base_a, ternas=1, clase5=False, f_temp=1.0, f_agrup=1.0, f_suelo=1.0)` | I_z = N · I_z0 · f_clase · f_temp · f_agrup · f_suelo   [A]. |
| `iz_tabla(tabla, aislacion, material, seccion_mm2, columna, grupo=None)` | Intensidad admisible base [A] de una tabla 771.16, para `columna` (clave impresa). |
| `secciones(tabla, aislacion, material)` | Secciones [mm²] disponibles para (tabla, aislación, material), de menor a mayor. |

## `aea_ampacity` — Capacidad de conducción por aislación, material y método
*Norma:* AEA 771 §16, §13; IEC 60228

| Función | Fórmula / descripción |
|---|---|
| `factores(p, trifasico=True)` | Dict con f_clase, f_temp, f_agrup y f_suelo. |
| `iz(p, s, fases)` | I_z total [A] del circuito con sección s. ValueError si la combinación no está tabulada. |
| `iz_base(p, s, cargados)` | I_z0 por terna [A]: IZ_A si se informó, si no la tabla 771.16 correspondiente. |
| `parametros(c)` | Lee las columnas de instalación de una fila de CIRCUITOS y aplica los valores por defecto. |
| `resistencia_ohm_km(s, material, temp_c)` | R(θ) del conductor [Ω/km]. |
| `seccion_valida(p, s)` | El aluminio exige S ≥ 16 mm² y R20 tabulada. |
| `temp_conductor(p, temp_c_defecto=70.0)` | Temperatura de servicio: la dada, o 90 °C si es XLPE y no se fijó otra. |

## `aea_rules` — Reglas de ingeniería (alturas, reservas, llenado, circuitos)
*Norma:* AEA 771, 770, 701, 722

| Función | Fórmula / descripción |
|---|---|
| `buscar(texto=None, grupo=None, aplica_a=None, tipo=None, norma=None)` | Filtra reglas por texto (tema, regla, id), grupo, tipo de inmueble, tipo de regla y norma (p. ej. '771'). |
| `grupos()` | Nombres de los grupos de reglas. |
| `indice()` | Índice de grupos con su archivo y cantidad de reglas. |
| `regla(id_)` | Regla por id ('grupo.nombre'). |
| `reglas(grupo=None)` | Lista de reglas de un grupo, o de todos si `grupo` es None. |
| `valor(id_, parametro)` | Valor de un parámetro de una regla, p. ej. valor('bandejas.reserva_20pct', 'reserva_min_pct') = 20. |

## `aea_protection` — Protección contra contactos indirectos (TN/TT/IT) e I2
*Norma:* AEA 4-41, 4-43, 771.18

| Función | Fórmula / descripción |
|---|---|
| `corriente_falla_tt(u0_v, ra_ohm, rb_ohm)` | TT: corriente de primera falla If = U0/(Ra + Rb) [A]. |
| `i2_convencional(in_a, tipo='mcb')` | Corriente convencional de funcionamiento I2 = k2·In [A]. |
| `in_max_por_iz(iz_a, tipo='mcb')` | In máxima que cumple In ≤ Iz e I2 ≤ 1,45·Iz [A]. |
| `ra_maxima_tt(ia_a, ul_v=50.0)` | TT: resistencia de puesta a tierra máxima Ra = UL/Ia [Ω]. |
| `verifica_it_segunda_falla(zs_ohm, ia_a, u_v=400.0, u0_v=230.0, neutro_distribuido=False)` | IT, segunda falla: 2·Ia·Zs ≤ U (sin neutro) o ≤ U0 (con neutro distribuido). |
| `verifica_tn(zs_ohm, ia_a, u0_v=230.0)` | TN: Zs·Ia ≤ U0. Devuelve dict con producto, límite, margen y cumple. |
| `verifica_tt(ra_ohm, ia_a, ul_v=50.0)` | TT: Ra·Ia ≤ UL. |

## `aea_feeder_report` — Memoria de cálculo y síntesis del alimentador principal
*Norma:* AEA 771 §13, §16, §19.7, §18

| Función | Fórmula / descripción |
|---|---|
| `alimentador_principal(circuitos, tag=None)` | Alimentador principal: el TAG indicado, o el primer circuito sin PARENT_TAG y con KIND 'mccb'. |
| `generar_documentos(base, tablero, circuitos, datos, tag=None, temp_c=70.0, k_magnetico=10)` | Escribe <base>_MC.md y <base>_SP.md del alimentador principal. Devuelve las rutas. |
| `memoria_calculo(tablero, c, v, proyecto)` | Memoria de Cálculo (MC) en Markdown: objeto, marco, etapas 1 a 6. |
| `sintesis_proyecto(c, v, proyecto)` | Síntesis de Proyecto (SP): una página, requisito normativo / dato técnico, máximo tres observaciones. |
| `verificaciones(tablero, c, reg, temp_c=70.0, k_magnetico=10)` | Magnitudes intermedias del alimentador, con las mismas reglas que aea_pipeline. |

## `aea_export` — Exportación del cálculo a JSON (sin PDF)
*Norma:* Contrato con sld-generator

| Función | Fórmula / descripción |
|---|---|
| `circuito_json(i_n_a, i_b_a, icu_ka, s_mm2, du_pct, disp, decimales=2)` | Arma el registro de un circuito (redondea Ib, S y dU). |
| `export_calculation(datos, ruta)` | Valida y escribe el JSON (UTF-8, sin BOM, sangría 1). Rechaza rutas .pdf/.docx/.md. |
| `load_calculation(ruta)` | Lee el JSON (acepta BOM) y lo devuelve validado; lanza ValueError si hay errores. |
| `validate_calculation(datos)` | Devuelve {'errores': [...], 'avisos': [...]} (listas de str). |

## Ya existentes (no duplicar)

| Función | Fórmula |
|---|---|
| `voltage_drop.caida_tension` | ΔU = k·I·L·(R cosφ + X senφ) |
| `short_circuit.factor_c` | factor c |
| `short_circuit.impedancia_red` | Z_Qt |
| `short_circuit.impedancia_transformador` | Z_T, R_T, X_T |
| `short_circuit.factor_kt` | K_T [65] |
| `short_circuit.factor_kappa` | κ [68] |
| `short_circuit.corriente_pico` | i_p [67] |
| `short_circuit.aporte_motor` | I''kM [109] |
| `cable_thermal.seccion_minima_mm2` | S ≥ I√t/k |
| `cable_thermal.verificar_i2t` | k²S² ≥ I²t |
| `current_and_loads.corriente_monofasica` | I monofásica |
| `current_and_loads.corriente_trifasica` | I trifásica |
