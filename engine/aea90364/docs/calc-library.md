# Biblioteca de cálculos eléctricos — Índice

**Versión del índice:** 0.6.0 · **Fecha:** 2026-10-20 · **Estado global:** BORRADOR — pendiente de validación por el usuario
**Ubicación:** `library/calculations/` · **Requisitos:** Python 3, solo biblioteca estándar (sin dependencias).
**Ejecución de pruebas:** `python3 -B -m unittest discover -s library/calculations -v` desde la raíz del plugin (**170 pruebas**).
**Sin `__pycache__`:** ejecutar siempre con `python3 -B` (o `PYTHONDONTWRITEBYTECODE=1`). Todos los comandos se escriben desde la **raíz del plugin**.

Cada módulo es un `.py` con docstring en español (objetivo, fórmulas, hipótesis, unidades SI, limitaciones, norma por designación y marcas `[VERIFICAR]`), funciones con validación de entradas (`ValueError`), un ejemplo ejecutable y pruebas con valores calculados a mano.

## Índice de cálculos

| ID | Módulo | Objetivo | Entradas principales | Salidas principales | Norma de referencia | Estado de validación | Pruebas (pasan) | Limitaciones |
|---|---|---|---|---|---|---|---|---|
| CAL-001 | (movido a `engine/lighting`, paquete `epc_lighting`: ADR-0030, fase 6) | Número de luminarias, distribución, punto a punto, emergencia antipánico, eje de ruta de escape, UGR; ya no es parte del motor AEA 90364 | ver `engine/lighting/README.md` | ver `engine/lighting/README.md` | EN 12464-1 / EN 1838 `[VERIFICAR]` | portado con los mismos casos de prueba | — | — |
| CAL-002 | `voltage_drop.py` | Caída de tensión monofásica y trifásica en V y %; longitud máxima | I [A], L [m], R y X [Ω/km], cosφ, Un [V] | ΔU [V], ΔU [%], L máx [m] | IEC 60364-5-52 y reglamentación local `[VERIFICAR]` | BORRADOR — pendiente de validación por el usuario | 9 / 9 | Sin límites normativos ni tabla de R/X; carga concentrada; sin corrección por temperatura |
| CAL-003 | `current_and_loads.py` | Corriente de diseño, potencia aparente, balance con factores de utilización y simultaneidad, reserva frente a interruptor, reparto en fases (voraz) | P [W], V [V], cosφ, η, lista de cargas (P, cosφ, fu), fs, I_n, lista de circuitos (nombre, I) | I [A], S [VA], P/Q/S/fp de demanda, reserva [A, %], asignación a fases y desbalance [%] | IEC 60364-1 / IEC 60364-5-52 `[VERIFICAR]` | BORRADOR — pendiente de validación por el usuario | 14 / 14 | Reparto voraz no óptimo; sin neutro ni armónicos; fu y fs son datos |
| CAL-004 | `short_circuit.py` | Ik'' trifásica simétrica inicial por impedancias (IEC 60909 simplificado): red + transformador + cable; funciones separadas para K_T, aporte de motores y κ / corriente de pico | Un, c, red (Sk'' o Ik''), trafo (Sn, uk%, Pcu), cables (R, X, L) | Ik'' [A], R, X, \|Z\| [Ω], advertencias; aporte de motor, κ, i_p (funciones aparte) | IEC 60909-0 `[VERIFICAR]` | BORRADOR — pendiente de validación por el usuario | 20 / 20 | `calcular_ik` NO incluye motores ni κ; sin Ik mínima, bifásica ni fase-tierra |
| CAL-005 | `cable_thermal.py` | Verificación térmica adiabática de cable ante cortocircuito | I_cc [A], t [s], k, S [mm²] | S mín [mm²], cumple I²t ≤ k²S², margen, t máx, I máx | IEC 60364-4-43; IEC 60949 `[VERIFICAR]` | BORRADOR — pendiente de validación por el usuario | 9 / 9 | Válido para t corto (≲ 5 s); para t < 0,1 s usar I²t del dispositivo; sin tabla de secciones |
| CAL-006 | `hazen_williams.py` | Pérdida de carga por fricción (Hazen-Williams), velocidad, pérdida total con longitud equivalente y desnivel | Q [L/min], d [mm], C, L [m], L_eq [m], Δz [m] | J [bar/m], v [m/s], Δp fricción / estática / total [bar] | Ecuación de Hazen-Williams; NFPA 13 como uso típico `[VERIFICAR]` | BORRADOR — pendiente de validación por el usuario | 8 / 8 | Solo agua, flujo turbulento; sin tabla de C ni de accesorios; desviación de −0,24 % frente a forma SI (ver docstring) |
| CAL-007 | `hvac_airflow.py` | Caudal de aire por carga sensible y por renovaciones; conversiones m³/h ↔ L/s | Q sensible [kW], ΔT [K], volumen [m³], renovaciones [1/h] | Caudal [m³/h, L/s, m³/s], ΔT, n [1/h] | ASHRAE Fundamentals; EN 16798-1 / ASHRAE 62.1 `[VERIFICAR]` | BORRADOR — pendiente de validación por el usuario | 8 / 8 | Solo calor sensible; ρ y cp fijos (parametrizables); sin caudales mínimos normativos |
| CAL-009 | `conductor_selection.py` | Sección mínima de conductor por conducción y por caída de tensión; protección (In ≥ Ib, Iz ≥ In) | Ib [A], L [m], fases, Un, cosφ, límite ΔU [%], factores de agrupamiento y temperatura, **tabla de conductores (JSON)**, **serie de In (parámetro)** | Sección por conducción, por caída y adoptada [mm²], In, Iz, ΔU [%], criterio gobernante; «NO VERIFICABLE» sin tabla | IEC 60364-5-52 y 60364-4-43 `[VERIFICAR]` (los valores vienen de la ficha de extracto) | BORRADOR — pendiente de validación por el usuario | 12 / 12 | La tabla NO está embebida; sin I2 ≤ 1,45·Iz, sin cortocircuito (CAL-005), un solo conductor por fase; el ejemplo `example_conductor_table.json` es FICTICIO |
| CAL-014 | `aea_demand.py` | Grado de electrificación, DPMS, coeficientes de simultaneidad, I_B, desequilibrio, alimentador de motores, paralelo | tipo, superficie, nº de bocas/circuitos, fases | Grado, DPMS [VA], I_B [A], coeficientes | AEA 771 §9; AEA 770 §8 `[VERIFICAR]` | BORRADOR — pendiente de validación por el usuario | 34 / 34 (`test_aea_formulas.py`, compartido) | Solo stdlib; fórmulas literales de la norma, sin tablas del fabricante |
| CAL-015 | `aea_voltage_drop.py` | Caída de tensión por Tabla 771.19.IV y GDC; límites normativos; carga en el extremo | I, L, S, material, fases | ΔU [V, %], L máx, S mín, límite [%] | AEA 771 §19.7; AEA 770 §15.6 `[VERIFICAR]` | BORRADOR — pendiente de validación por el usuario | incl. en CAL-014 | Solo stdlib; fórmulas literales de la norma, sin tablas del fabricante |
| CAL-016 | `aea_earthing.py` | Ra admisible, tiempos de desconexión, electrodos (jabalina, horizontal, placa), sección del PE | IΔn, ρ, geometría, S de fase | Ra [Ω], t máx [s], R de electrodo [Ω], S_PE | AEA 771 §3, §18, Anexo C `[VERIFICAR]` | BORRADOR — pendiente de validación por el usuario | incl. en CAL-014 | Solo stdlib; fórmulas literales de la norma, sin tablas del fabricante |
| CAL-017 | `aea_conductors.py` | Secciones mínimas, tabla k, sobrecarga, armónicos (THD, D, factores), neutro, volumen combustible | I_B, I_n, I_Z, armónicos, De, S | Cumple/no cumple, factor, I_N, dm³/m | AEA 771 §13, §16, §19; AEA 770 §11 `[VERIFICAR]` | BORRADOR — pendiente de validación por el usuario | incl. en CAL-014 | Solo stdlib; fórmulas literales de la norma, sin tablas del fabricante |
| CAL-018 | `aea_panel_thermal.py` | Verificación térmica de tableros: K por circuitos y por nivel, W/polo, P total, poder de corte de diferenciales | In, polos, nº de circuitos | P_tot [W], K, PdC mín | AEA 770 Anexo B; AEA 771 Anexo H `[VERIFICAR]` | BORRADOR — pendiente de validación por el usuario | incl. en CAL-014 | Solo stdlib; fórmulas literales de la norma, sin tablas del fabricante |
| CAL-019 | `aea_icc_factors.py` | Factores K_G, K_S, K_SO, K_G,S, K_T,S, K_T, K_G,SO, K_T,SO; I''k de generador, grupo y transformador; X_T y X_Qt; motores despreciables | Un, U_r, c, x''d, x_T, senφ | K [p.u.], I''k [A], X [Ω] | AEA IT 90909-1 (2005) `[VERIFICAR]` | BORRADOR — pendiente de validación por el usuario | incl. en CAL-014 | Solo stdlib; fórmulas literales de la norma, sin tablas del fabricante |
| CAL-020 | `aea_icc_decay.py` | κ exacto, i_p, μ, λ, q, m, n, I_th, decrecimiento I_k,ac(t) | R, X, T, reactancias del generador | κ, i_p, μ, q, m, n, I_th | AEA IT 90909-1 §2.4–2.8 `[VERIFICAR]` | BORRADOR — pendiente de validación por el usuario | incl. en CAL-014 | Solo stdlib; fórmulas literales de la norma, sin tablas del fabricante |
| CAL-021 | `aea_special_locations.py` | Baños (inducción magnética, radio de zona 2) y vehículos eléctricos (factor de demanda, carga múltiple) | i, distancia, nº de tomas | B [T], r [m], cumple | AEA 701; AEA 722 `[VERIFICAR]` | BORRADOR — pendiente de validación por el usuario | incl. en CAL-014 | Solo stdlib; fórmulas literales de la norma, sin tablas del fabricante |
| CAL-022 | `aea_catalog.py` | Catálogo único de fórmulas por introspección; búsqueda; genera `FORMULAS_AEA.md` y `formulas_aea.json` | Palabra a buscar | Tabla Markdown / JSON | — `[VERIFICAR]` | BORRADOR — pendiente de validación por el usuario | incl. en CAL-014 | Solo stdlib; fórmulas literales de la norma, sin tablas del fabricante |
| CAL-023 | `aea_export.py` | Exportación del cálculo a JSON (`<proyecto>_calculo.json`): construye, valida (errores y avisos) y escribe; rechaza `.pdf`/`.docx`/`.md` | In, Ib, icu, S, dU, disp por circuito | JSON para `sld-generator`; lista de avisos | Contrato de datos con `sld-generator` | BORRADOR — pendiente de validación por el usuario | 8 / 8 (`test_aea_export.py`) | Sin campos extra; el entregable del plugin es solo este JSON |
| CAL-024 | `aea_pipeline.py` | Lee el Excel de circuitos (`src/input_for_sld_V1.xlsx`, hojas TABLERO y CIRCUITOS) y dimensiona Ib, In, icu, S, dU y disp por circuito con jerarquía PARENT_TAG; exporta con `aea_export` | `.xlsx`, `--margen-iz`, `--eta-motores`, `--temp-c` | `<entrada>_calculo.json`, avisos | AEA 771 §13, §16 (Tabla 771.16.I), §19.7 `[VERIFICAR]` | BORRADOR — pendiente de validación por el usuario | 19 / 19 (`test_aea_pipeline.py`) | Carga en A, W, kW, MW, VA, kVA, MVA, HP/CV (o texto «15 kW»); Cu/PVC en cañería; icu = Icc en barras; Icc mínima al final de cada circuito solo como aviso (disparo magnético, `--k-magnetico`); sin I²t del cable ni selectividad; η solo en HP; R20 de IEC 60228 |

## Valores marcados `[VERIFICAR]` (resumen)

| Módulo | Valor / criterio |
|---|---|
| CAL-001 | Criterios de emergencia antipánico (E mín ≥ 0,5 lx; E máx/E mín ≤ 40); designaciones EN 1838 / ISO 30061 |
| CAL-004 | c = 1,05 (tolerancia 6 %) y 1,10 (tolerancia 10 %); X/R de red = 10; K_T = 0,95·c/(1+0,6·x_T); κ = 1,02 + 0,98·e^(−3R/X); umbral de motores despreciables 5 %; I_LR/I_rM típico 5–7 |
| CAL-005 | k: Cu/PVC = 115, Cu/XLPE = 143, Al/PVC = 76, Al/XLPE = 94; límites de validez adiabática (5 s) y t corto (0,1 s) |
| CAL-006 | Constante 6,05·10⁵ y exponentes 1,85 / 4,87; forma SI de contraste 10,67 / 1,852 / 4,8704; g = 9,80665 m/s²; rango de validez |
| CAL-007 | ρ = 1,2 kg/m³; cp = 1,006 kJ/(kg·K) |

## Reglas de uso

1. **Cita obligatoria.** Todo cálculo que use la biblioteca cita el ID `CAL-nnn` y la versión del módulo (`__version__`), p. ej. «CAL-004 v0.1.0».
2. **Archivo del script.** El script o llamada exacta usada, con sus datos de entrada, se archiva junto al resultado para que sea reproducible.
3. **Cambios y altas.** Todo cambio se registra en el historial de este archivo (fecha, ID, versión, descripción, autor), se sube `__version__` del módulo y se vuelven a ejecutar las pruebas completas.
4. **Sin aceptación ciega.** Los resultados nunca se aceptan sin compararlos con el criterio de proyecto (límites, normas aplicables, datos de fabricante). La biblioteca calcula; la verificación de cumplimiento es responsabilidad del ingeniero.
5. **Datos normativos.** La biblioteca no embebe tablas normativas salvo las de los módulos `aea_*` y las expresamente citadas; el resto se pasa como parámetro desde la norma vigente.
6. **Estado de validación.** Todos los cálculos están en `BORRADOR — pendiente de validación por el usuario`; hasta entonces, los resultados no son aptos para construcción.
7. **Advertencias propias.** Cuando un resultado trae advertencias (p. ej. cortocircuito sin motores ni κ), deben trasladarse al cálculo que se entrega.

## Comandos (desde la raíz del plugin)

| Módulo | Comando |
|---|---|
| CAL-001 a CAL-007 | `python3 -B library/calculations/<modulo>.py` (ejemplo) o `sys.path.insert(0, "library/calculations")` + `import <modulo>` |
| CAL-009 | `python3 -B library/calculations/conductor_selection.py table.json --ib 24 --longitud 100 --fases 3 --un 400 --fp 0.9 --caida-max 3 --fa 0.8 --ft 1.0` |
| CAL-024 (entrada Excel) | `python3 -B library/calculations/aea_pipeline.py src/input_for_sld_V1.xlsx` → `src/input_for_sld_V1_calculo.json` |
| CAL-023 (validar JSON) | `python3 -B library/calculations/aea_export.py validar <archivo_calculo.json>` |
| CAL-022 (catálogo) | `python3 -B library/calculations/aea_catalog.py --md` · `--buscar <palabra>` · `--json` |

## Historial de cambios

| Fecha | ID | Versión | Cambio | Autor |
|---|---|---|---|---|
| 2026-10-07 | CAL-001 a CAL-007 | 0.1.0 | Alta inicial de la biblioteca de cálculo (lighting, voltage_drop, current_and_loads, short_circuit, cable_thermal, hazen_williams, hvac_airflow). | Claude Code (borrador, pendiente de revisión del usuario) |
| 2026-10-07 | CAL-009 | 0.1.0 | Alta de `conductor_selection.py` (tabla por JSON, sin tablas embebidas) y `example_conductor_table.json` FICTICIO. | Claude Code (borrador, pendiente de revisión del usuario) |
| 2026-10-20 | CAL-014 a CAL-022 | 0.1.0 | Alta de los módulos `aea_*` (demanda, caída de tensión, puesta a tierra, conductores, tablero, factores de Icc, κ/μ/λ/m/n, baños y VE) y del catálogo `aea_catalog.py`. | Claude Code (borrador, pendiente de revisión del usuario) |
| 2026-10-20 | CAL-023 | 0.1.0 | Alta de `aea_export.py`: el entregable del cálculo es un único JSON; no se genera PDF. | Claude Code (borrador, pendiente de revisión del usuario) |
| 2026-10-20 | CAL-024 | 0.2.1 | Alta de `aea_pipeline.py` (Excel de circuitos → Ib, In, icu, S, dU, disp → JSON); conversión de carga A/W/kW/MW/VA/kVA/MVA/HP/CV; aviso de Icc mínima frente al disparo magnético. | Claude Code (borrador, pendiente de revisión del usuario) |
| 2026-10-20 | Biblioteca | 0.6.0 | Se retira todo lo de gestión de proyectos y los generadores/convertidores de PDF; la biblioteca queda solo con cálculo eléctrico y de apoyo (170 pruebas). | Claude Code (borrador, pendiente de revisión del usuario) |
