# MLD_LV

Biblioteca de símbolos **multifilares de baja tensión** (SVG vectorial editable), creada el 10/10/2026 (94 símbolos: 94 SVG + 94 DXF; 70 entradas en `_catalog.json`, 36 variantes ACB/MCCB con drawout, LSIG o motorizado aún sin entrada).

## Contenido
- `<id>.svg`: un archivo por símbolo, con nombre `<id SLD>_<n>p_mld`.
- `_library.svg`, `_catalog.json` y `_preview.png`: sprite, catálogo y hoja de muestra, con la misma estructura que SLD_LV.

## Convenciones
- **Protecciones y maniobra:** el símbolo SLD completo se repite una vez por polo (1P, 2P, 3P y 4P).
- **Mecanismo:** cuando el equipo tiene mecanismo (ACB y MCCB), se dibuja una sola vez a la izquierda y su línea discontinua se extiende a todos los polos. En MCB, FS, seccionador y contactor se agrega un enlace mecánico discontinuo entre cuchillas (IEC 60617 S00295). Los fusibles, el relé térmico y los SPD no llevan enlace.
- **Paso entre polos (uniforme):** 10 mm en todos los equipos desde 0.4.14 (antes 12.5 mm). Las celdas ACB/MCCB miden 10 mm y quedan contiguas; el relé térmico, 4,9 mm por polo.
- **Etiquetas de polo:** L, N, L1, L2, L3 van a la derecha del conductor (x = eje + 1,2 mm, anchor start, h = 2,5 mm), nunca encima de la línea.
- **Polos:** 1P = L · 2P = L N · 3P = L1 L2 L3 · 4P = L1 L2 L3 N.
- **Diferenciales (RCCB y RCBO):** solo existen en 1P, 2P y 4P (no hay 3P). Llevan un único toroide a la misma altura que en el SLD, que abarca todos los polos, y un solo relé IΔ en el último polo. La línea discontinua del relé llega hasta la cuchilla del primer polo, para indicar que todos abren y cierran juntos.
- **Marcación de bornes (IEC 60445 / IEC 60947):** cada polo lleva su número en negro, h 1,8 (font-size 2,5), a la derecha del conductor: impar en el borne de arriba y par en el de abajo (1-2, 3-4, 5-6 y 7-8). Los contactores marcan las fases como `1/L1 3/L2 5/L3` y `2/T1 4/T2 6/T3`. En ACB y MCCB el número se corre 3 mm para no pisar los chevrones de extraíble; en el relé térmico, el número de abajo va debajo del borne. Los SPD y los FU+SPD no llevan numeración. El catálogo lista las marcas de cada puerto en `terminal_marks`.
- **Coordenadas:** `x = 0` es el eje del primer polo e `y = 0` es el puerto superior. Los puertos son `top_<polo>` y `bottom_<polo>`.
- **Estilo:** el mismo que el SLD de origen (azul `#0000ff`, texto fijo en negro y datos variables `{clave}` en verde).
- Unidad: **1 unidad = 1 mm**, símbolos a escala 1. Puertos sobre retícula de 2,5 mm.
- Líneas (IRAM 4502): símbolos y conductores **0,25 mm**, bordes de rellenos 0,18 mm. Trazos tipo E 3 mm / 1 mm; trazo largo y corto (tipo F) 10 / 1 / 2 / 1 mm.
- Letras (IRAM 4503): h = 2,5 mm (font-size 3,47) en tipo de equipo, datos y polos; mínimo h = 1,8 mm en cajas chicas (IΔ). Fuente osifont (ISO 3098), ISOCPEUR o DejaVu Sans.
- Cada símbolo MLD apunta a su SLD con `sld_equivalent`, y el SLD apunta a sus cuatro versiones con `mld_equivalent`. La variable `poles` no se usa en MLD porque la cantidad de polos ya está en el símbolo.

## Símbolos
- `lv_mccb_basic_1p_mld`: Interruptor de caja moldeada MCCB 1P (multifilar). Variables: `tag`, `manufacturer`, `rated_current`, `breaking_capacity`, `trip_unit`.
- `lv_mccb_basic_2p_mld`: Interruptor de caja moldeada MCCB 2P (multifilar). Variables: `tag`, `manufacturer`, `rated_current`, `breaking_capacity`, `trip_unit`.
- `lv_mccb_basic_3p_mld`: Interruptor de caja moldeada MCCB 3P (multifilar). Variables: `tag`, `manufacturer`, `rated_current`, `breaking_capacity`, `trip_unit`.
- `lv_mccb_basic_4p_mld`: Interruptor de caja moldeada MCCB 4P (multifilar). Variables: `tag`, `manufacturer`, `rated_current`, `breaking_capacity`, `trip_unit`.
- `lv_rcbo_1p_mld`: Interruptor termomagnético diferencial RCBO 1P (multifilar). Variables: `curve_rating`, `sensitivity`, `breaking_capacity`, `tag`.
- `lv_rcbo_2p_mld`: Interruptor termomagnético diferencial RCBO 2P (multifilar). Variables: `curve_rating`, `sensitivity`, `breaking_capacity`, `tag`.
- `lv_rcbo_4p_mld`: Interruptor termomagnético diferencial RCBO 4P (multifilar). Variables: `curve_rating`, `sensitivity`, `breaking_capacity`, `tag`.
- `lv_acb_basic_1p_mld`: Interruptor de aire ACB (símbolo de leyenda) 1P (multifilar). Variables: `tag`.
- `lv_acb_basic_2p_mld`: Interruptor de aire ACB (símbolo de leyenda) 2P (multifilar). Variables: `tag`.
- `lv_acb_basic_3p_mld`: Interruptor de aire ACB (símbolo de leyenda) 3P (multifilar). Variables: `tag`.
- `lv_acb_basic_4p_mld`: Interruptor de aire ACB (símbolo de leyenda) 4P (multifilar). Variables: `tag`.
- `lv_acb_motorized_1p_mld`: Interruptor de aire ACB con motorización 1P (multifilar). Variables: `manufacturer`, `rated_current`, `breaking_capacity`.
- `lv_acb_motorized_2p_mld`: Interruptor de aire ACB con motorización 2P (multifilar). Variables: `manufacturer`, `rated_current`, `breaking_capacity`.
- `lv_acb_motorized_3p_mld`: Interruptor de aire ACB con motorización 3P (multifilar). Variables: `manufacturer`, `rated_current`, `breaking_capacity`.
- `lv_acb_motorized_4p_mld`: Interruptor de aire ACB con motorización 4P (multifilar). Variables: `manufacturer`, `rated_current`, `breaking_capacity`.
- `lv_mccb_motorized_1p_mld`: Interruptor de caja moldeada MCCB (LSIG, motorizado) 1P (multifilar). Variables: `manufacturer`, `rated_current`, `breaking_capacity`.
- `lv_mccb_motorized_2p_mld`: Interruptor de caja moldeada MCCB (LSIG, motorizado) 2P (multifilar). Variables: `manufacturer`, `rated_current`, `breaking_capacity`.
- `lv_mccb_motorized_3p_mld`: Interruptor de caja moldeada MCCB (LSIG, motorizado) 3P (multifilar). Variables: `manufacturer`, `rated_current`, `breaking_capacity`.
- `lv_mccb_motorized_4p_mld`: Interruptor de caja moldeada MCCB (LSIG, motorizado) 4P (multifilar). Variables: `manufacturer`, `rated_current`, `breaking_capacity`.
- `lv_mcb_1p_mld`: Interruptor termomagnético (MCB) 1P (multifilar). Variables: `curve_rating`, `breaking_capacity`.
- `lv_mcb_2p_mld`: Interruptor termomagnético (MCB) 2P (multifilar). Variables: `curve_rating`, `breaking_capacity`.
- `lv_mcb_3p_mld`: Interruptor termomagnético (MCB) 3P (multifilar). Variables: `curve_rating`, `breaking_capacity`.
- `lv_mcb_4p_mld`: Interruptor termomagnético (MCB) 4P (multifilar). Variables: `curve_rating`, `breaking_capacity`.
- `lv_rccb_1p_mld`: Interruptor diferencial (RCCB) 1P (multifilar). Variables: `rated_current`, `sensitivity`.
- `lv_rccb_2p_mld`: Interruptor diferencial (RCCB) 2P (multifilar). Variables: `rated_current`, `sensitivity`.
- `lv_rccb_4p_mld`: Interruptor diferencial (RCCB) 4P (multifilar). Variables: `rated_current`, `sensitivity`.
- `lv_fuse_1p_mld`: Fusible 1P (multifilar). Variables: `tag`.
- `lv_fuse_2p_mld`: Fusible 2P (multifilar). Variables: `tag`.
- `lv_fuse_3p_mld`: Fusible 3P (multifilar). Variables: `tag`.
- `lv_fuse_4p_mld`: Fusible 4P (multifilar). Variables: `tag`.
- `lv_fuse_disconnector_nh00_1p_mld`: Fusible seccionable NH00 1P (multifilar). Variables: `manufacturer`, `rated_current`, `breaking_capacity`.
- `lv_fuse_disconnector_nh00_2p_mld`: Fusible seccionable NH00 2P (multifilar). Variables: `manufacturer`, `rated_current`, `breaking_capacity`.
- `lv_fuse_disconnector_nh00_3p_mld`: Fusible seccionable NH00 3P (multifilar). Variables: `manufacturer`, `rated_current`, `breaking_capacity`.
- `lv_fuse_disconnector_nh00_4p_mld`: Fusible seccionable NH00 4P (multifilar). Variables: `manufacturer`, `rated_current`, `breaking_capacity`.
- `lv_fuse_switch_fs_1p_mld`: Fusible seccionador (FS) 1P (multifilar). Variables: `tag`.
- `lv_fuse_switch_fs_2p_mld`: Fusible seccionador (FS) 2P (multifilar). Variables: `tag`.
- `lv_fuse_switch_fs_3p_mld`: Fusible seccionador (FS) 3P (multifilar). Variables: `tag`.
- `lv_fuse_switch_fs_4p_mld`: Fusible seccionador (FS) 4P (multifilar). Variables: `tag`.
- `lv_switch_disconnector_1p_mld`: Seccionador (corte visible) 1P (multifilar). Variables: `tag`.
- `lv_switch_disconnector_2p_mld`: Seccionador (corte visible) 2P (multifilar). Variables: `tag`.
- `lv_switch_disconnector_3p_mld`: Seccionador (corte visible) 3P (multifilar). Variables: `tag`.
- `lv_switch_disconnector_4p_mld`: Seccionador (corte visible) 4P (multifilar). Variables: `tag`.
- `lv_contactor_1p_mld`: Contactor de potencia 1P (multifilar). Variables: `tag`.
- `lv_contactor_2p_mld`: Contactor de potencia 2P (multifilar). Variables: `tag`.
- `lv_contactor_3p_mld`: Contactor de potencia 3P (multifilar). Variables: `tag`.
- `lv_contactor_4p_mld`: Contactor de potencia 4P (multifilar). Variables: `tag`.
- `lv_thermal_overload_1p_mld`: Relé térmico de sobrecarga 1P (multifilar). Variables: `tag`.
- `lv_thermal_overload_2p_mld`: Relé térmico de sobrecarga 2P (multifilar). Variables: `tag`.
- `lv_thermal_overload_3p_mld`: Relé térmico de sobrecarga 3P (multifilar). Variables: `tag`.
- `lv_thermal_overload_4p_mld`: Relé térmico de sobrecarga 4P (multifilar). Variables: `tag`.
- `lv_spd_varistor_1p_mld`: Descargador de sobretensión (SPD) con varistor 1P (multifilar). Variables: `class`, `impulse_current`.
- `lv_spd_varistor_2p_mld`: Descargador de sobretensión (SPD) con varistor 2P (multifilar). Variables: `class`, `impulse_current`.
- `lv_spd_varistor_3p_mld`: Descargador de sobretensión (SPD) con varistor 3P (multifilar). Variables: `class`, `impulse_current`.
- `lv_spd_varistor_4p_mld`: Descargador de sobretensión (SPD) con varistor 4P (multifilar). Variables: `class`, `impulse_current`.
- `lv_fuse_spd_fu_1p_mld`: Fusible + descargador de sobretensión (FU+SPD) 1P (multifilar). Variables: `tag`.
- `lv_fuse_spd_fu_2p_mld`: Fusible + descargador de sobretensión (FU+SPD) 2P (multifilar). Variables: `tag`.
- `lv_fuse_spd_fu_3p_mld`: Fusible + descargador de sobretensión (FU+SPD) 3P (multifilar). Variables: `tag`.
- `lv_fuse_spd_fu_4p_mld`: Fusible + descargador de sobretensión (FU+SPD) 4P (multifilar). Variables: `tag`.

## Historial

> Nota: este historial (v1.x, v2.x) corresponde a una copia de trabajo anterior. La fuente vigente de versiones es `CHANGELOG.md` en la raíz del repo; la última versión es 0.4.14.
- v1.3.0 (10/10/2026): paso uniforme 26.64 pt en los 58 símbolos y etiquetas de polo al costado del conductor. Copia de la v1.2.1 en `ELECTRICAL_SYMBOLS/_backup/MLD_LV_v1.2.1`.

## v2.0.0 (10/10/2026): migración a mm según IRAM

Toda la biblioteca pasó de pt a mm: geometría escalada (la retícula de 2,55 pt de los planos de origen es ahora 1,25 mm), puertos en retícula de 2,5 mm, grosores, trazos y letras según IRAM 4502 y 4503, y fuente ISO. La forma de cada símbolo (IEC 60617), los ids, los puertos y las variables no cambiaron. Copia de la versión en pt en `ELECTRICAL_SYMBOLS/_backup/MLD_LV_pt_v1.3.0`. Script: `entrenamiento_dibujo_tecnico/migracion_iram/convertir_biblioteca_iram.py`.

## v2.1.0 (10/10/2026): marcación de bornes

Se agregó el número de borne IEC 60445 en cada polo de 50 símbolos (todos menos los 8 SPD y FU+SPD), según la convención de arriba. En los símbolos donde la marca no entraba se agrandó el viewBox; la geometría, los puertos y las variables no cambiaron. Copia de la v2.0.0 en `ELECTRICAL_SYMBOLS/_backup/MLD_LV_v2.0.0`. Script: `aprendizaje_mld/_lib_v2.1.0/marcar.py`.
