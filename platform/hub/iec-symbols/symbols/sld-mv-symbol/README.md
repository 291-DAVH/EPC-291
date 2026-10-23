# SLD_MV

Biblioteca de símbolos unifilares **de media tensión (celdas y equipos MT)** (SVG vectorial editable), generada el 09/10/2026.

## Contenido
- `<id>.svg` — un archivo por símbolo (editable con Inkscape, Illustrator, etc.).
- `_library.svg` — todos los símbolos como `<symbol>` para usar con `<use>` desde un generador de diagramas.
- `_catalog.json` — catálogo: nombre (ES/EN), descripción, etiquetas, tamaño, `viewBox`, **puertos de conexión** y **ranuras de rótulo**.
- `_preview.png` — hoja de muestra con todos los símbolos (los círculos magenta son los puertos).

## Convenciones
- Unidad: **1 unidad = 1 mm**. Los símbolos se usan a escala 1 en la lámina IRAM (no se agrandan por hoja).
- Puertos sobre **retícula de 2,5 mm**.
- Líneas (IRAM 4502): símbolos y conductores **0,25 mm**, barras 0,5 mm, bordes de rellenos 0,18 mm; ninguna menor a 0,18 mm. Trazos tipo E 3 mm / 1 mm; trazo largo y corto (tipo F) 10 / 1 / 2 / 1 mm.
- Letras (IRAM 4503): altura de mayúscula **h = 2,5 mm** (font-size 3,47) en tipo de equipo, datos y polos; h = 3,5 mm en títulos de celda MT; texto dentro de cajas chicas (IΔ, 3~) mínimo h = 1,8 mm. Fuente osifont (ISO 3098), ISOCPEUR o DejaVu Sans.
- Colores: azul `#0000ff` (conductores y aparamenta), rojo `#ff0000` (cables externos), verde `#139b48` (PE), gris `#dcdcdc` (contorno de celda).
- Origen: `x = 0` es el eje del conductor; `y = 0` es el puerto superior; `y` crece hacia abajo.
- Cada SVG trae `label_slots` (visible, negro): textos de ejemplo de los datos variables, con `data-key` (clave) y `data-placeholder` (`{clave}`); el texto estructural (I>, AR, M, G, 3~, kW…) va fijo en el símbolo. Los símbolos sin rótulos propios traen `{tag}`. El grupo `ports` está oculto (`display="none"`).
- Un generador sustituye `{clave}` por el dato o elimina el `<text>` si no hay dato; `_library.svg` (sprite) contiene solo el cuerpo, sin placeholders.
- `origin`: `extracted` = recortado del plano; `drawn` = dibujado nuevo con la misma simbología.

## Uso desde SVG
```xml
<use href="#lv_mcb" x="{X + vb.x}" y="{Y + vb.y}" width="{vb.w}" height="{vb.h}"/>
```
donde `(X, Y)` es el punto del puerto superior en el diagrama y `vb` es el `viewBox` del catálogo.

## Pendientes / dudas
- `mv_cell_gam2_remonte`: Incluye el contorno gris discontinuo de la celda y el tramo de barra que la cruza. Las flechas de terminal de cable fueron redibujadas como triángulos rellenos (el original usa sombreado).
- `mv_cell_dmva_proteccion`: Incluye el contorno gris discontinuo de la celda y el tramo de barra que la cruza. Las flechas de terminal de cable fueron redibujadas como triángulos rellenos (el original usa sombreado).
- `mv_cell_im_interruptor`: Incluye el contorno gris discontinuo de la celda y el tramo de barra que la cruza. Las flechas de terminal de cable fueron redibujadas como triángulos rellenos (el original usa sombreado).
- `mv_vpis`: Identificación por forma; el original no lo rotula.

## Agregados el 10/10/2026 (v1.1.0)

Dibujados según IEC 60617 con el estilo de la biblioteca; cada uno trae sus variables de datos técnicos.

- `mv_cell_qm_fusibles`: Celda QM (interruptor-seccionador + fusibles) (IEC 60617 S00290, S00364, S00367). Variables: `series`, `model`, `designation`, `rated_current`, `fuse_rating`, `short_circuit_current`, `manufacturer`, `serial`.
- `mv_cell_cm_medicion_tension`: Celda CM (transformadores de tensión) (IEC 60617 S00288, S00362, S00878). Variables: `series`, `model`, `designation`, `rated_current`, `vt_ratio`, `short_circuit_current`, `manufacturer`, `serial`.
- `mv_cell_gbc_medida`: Celda GBC (medida de tensión e intensidad) (IEC 60617 S00850, S00878, S00362). Variables: `series`, `model`, `designation`, `rated_current`, `ct_ratio`, `vt_ratio`, `short_circuit_current`, `manufacturer`, `serial`.
- `mv_protection_relay`: Relé de protección MT (IEC 60617 S00327, S00342). Variables: `ansi_functions`, `model`, `manufacturer`, `tag`.
- `mv_energy_meter`: Medidor de energía (kWh) MT (IEC 60617 S00933). Variables: `model`, `accuracy_class`, `ct_ratio`, `tag`.
- `mv_switch_fuse_combination`: Interruptor-seccionador con fusibles combinados (percutor) (IEC 60617 S00290, S00364, S00367). Variables: `rated_current`, `fuse_rating`, `tag`.

- Las celdas QM, CM y GBC son diseños de fabricante (SM AirSET), no símbolos IEC: están armadas con símbolos IEC y con el mismo marco, barra y rótulos que `mv_cell_im_interruptor`.

## v2.0.0 (10/10/2026): migración a mm según IRAM

Toda la biblioteca pasó de pt a mm: geometría escalada (la retícula de 2,55 pt de los planos de origen es ahora 1,25 mm), puertos en retícula de 2,5 mm, grosores, trazos y letras según IRAM 4502 y 4503, y fuente ISO. La forma de cada símbolo (IEC 60617), los ids, los puertos y las variables no cambiaron. Copia de la versión en pt en `ELECTRICAL_SYMBOLS/_backup/SLD_MV_pt_v1.1.0`. Script: `entrenamiento_dibujo_tecnico/migracion_iram/convertir_biblioteca_iram.py`.
