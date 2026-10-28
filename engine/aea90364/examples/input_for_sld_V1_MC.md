# Memoria de Cálculo: alimentador principal C-01

**Proyecto:** input_for_sld_V1 · **Circuito:** C-01 – ALIMENTADOR TD-PB PLANTA BAJA

## 1. Objeto y alcance
Dimensionar y verificar el alimentador principal del tablero. Los demás circuitos se documentan en el JSON de cálculo.

## 2. Marco normativo
- AEA 90364-7-771 (ed. 2006): instalaciones en viviendas y similares
- AEA 90364-7-770 (ed. 2017): instalaciones en edificios
- AEA 90364-7-701 y 90364-7-722: locales de baño y alimentación de vehículos eléctricos
- AEA 90909-1: cálculo de cortocircuito
- IEC 60364: referencia de instalaciones de baja tensión

## Etapa 1 – Datos genéricos
| Parámetro | Valor |
|---|---|
| Tensión nominal U | 380 V |
| Sistema de puesta a tierra | TN-S |
| Icc en barras del tablero | 36 kA |
| Factor de potencia | 0,85 |
| Longitud del tendido | 40 m |
| Tipo de cable | tetra_sep |
| Temperatura de servicio | 70 °C |

## Etapa 2 – Corriente de proyecto
Carga declarada en amperes: Ib = 250 A (sin conversión).

## Etapa 3 – Criterios de verificación
- Capacidad: Iz ≥ In ≥ Ib.
- Caída de tensión: ΔU ≤ 1,0 % (alimentador seccional).
- Disparo magnético: Icc mínima al final del cable ≥ 10·In.
- Sección mínima: S ≥ 2,5 mm².
- Poder de corte: icu ≥ Icc en barras.

## Etapa 4 – Selección de la sección
- Sección elegida: S = 185 mm² de cobre; Iz = 260 A según tabla 771.16.I.
- Resistencia a 70 °C: R = 0,1186 Ω/km; reactancia X = 0,08 Ω/km.
- Caída de tensión: ΔU = k · I · L · (R · cos φ + X · sen φ) / U, con I = Ib = 250 A y L = 40 m → ΔU = 0,7 %.
- Pendiente: factores de agrupamiento y de temperatura (k) no aplicados; el cálculo usa la tabla vigente a 40 °C.

## Etapa 5 – Verificaciones finales
| Verificación | Valor | Requisito | Resultado |
|---|---|---|---|
| Capacidad de conducción | Iz = 260 A | Iz ≥ In = 250 A | CUMPLE |
| Coordinación de sobrecarga | In = 250 A | In ≥ Ib = 250 A | CUMPLE |
| Caída de tensión | 0,7 % | ≤ 1,0 % | CUMPLE |
| Disparo magnético | Icc mín = 16000 A | ≥ 10·In = 2500 A | CUMPLE |
| Sección mínima | S = 185 mm² | ≥ 2,5 mm² | CUMPLE |
| Poder de corte | icu = 36 kA | ≥ Icc barras = 36 kA | CUMPLE |
| PE y N (S_PE = S_N) | Pendiente | Pendiente | Pendiente |
| Icc máxima y selectividad | Pendiente | Pendiente | Pendiente |

**Resultado global:** CUMPLE (sujeto a las verificaciones pendientes).

## Etapa 6 – Conclusión y puntos a verificar
El alimentador C-01 con cable de 185 mm² de cobre y protección MCCB (250 A) cumple las verificaciones calculadas.
Puntos a verificar: Icc máxima, selectividad, conductores PE y N, y factores de agrupamiento y temperatura.
