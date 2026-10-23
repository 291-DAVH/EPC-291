---
name: "generate-electrical-symbol"
description: "Genera símbolos eléctricos SVG (unifilar SLD y multifilar MLD, en MV y LV) con el estándar de la biblioteca: colores, trazo, medidas, puertos, texto fijo/variable y catálogo, desde PDF, imagen, boceto o texto."
---

# Símbolos eléctricos → SVG estándar de biblioteca (SLD/MLD × MV/LV)

## Contexto de ejecución
- **Invocación:** explícita — ejecutar solo cuando el usuario solicite crear o agregar un nuevo símbolo a la biblioteca, o cuando otra skill del pipeline (p. ej. `create-electrical-line-diagram`) reporte que falta un símbolo necesario.
- **Contexto requerido:** directorio `03_ENGINEERING`. No ejecutar en `90_MANAGEMENT`, `01_INPUT`, `02_PROJECT` ni `04_REVIEW`.
- **No ejecutar si:** el usuario solo consulta, visualiza o menciona un símbolo existente; si está leyendo o analizando la biblioteca; si la conversación es sobre análisis o revisión de planos.
- **Señales de activación:** el usuario dice "generar símbolo", "agregar símbolo", "falta el símbolo de X", "crear nuevo símbolo", o una skill reporta que un símbolo no existe en `_catalog.json`.

Objetivo: convertir CUALQUIER entrada (PDF vectorial, PDF/imagen raster, foto o boceto a mano, captura, descripción en texto) en un símbolo SVG que se vea **idéntico en estilo** a los de la biblioteca, sin importar el color o el trazo de la fuente (azul, negro, lápiz, etc.).

**La biblioteca está en mm según IRAM desde la v2.0.0 (10/10/2026); MLD_LV va por la v2.1.0.** Todo símbolo nuevo se dibuja en mm, a escala 1, con líneas IRAM 4502 y letras IRAM 4503. La versión anterior en pt quedó en `PLUGINS\<lib>\_backup\<lib>_pt_v<x.y.z>`: no usarla como referencia de medidas.

## 0. Las cuatro bibliotecas (decidir SIEMPRE antes de dibujar)
Raíz: `E:\Proyectos\00-Template-Claude\.claude\library\plugins\`
| Carpeta | Contenido | Prefijo de id |
|---|---|---|
| `sld-mv` | Unifilar, media tensión (celdas MT y equipos MT) | `mv_` |
| `sld-lv` | Unifilar, baja tensión (TGBT, tableros, cargas) | `lv_` |
| `mld-mv` | Multifilar, media tensión | `mv_..._<n>p_mld` |
| `mld-lv` | Multifilar, baja tensión | `lv_..._<n>p_mld` |
SLD = una línea por circuito. MLD = cada fase dibujada (L1, L2, L3, y N/PE si aplica).
- Si la tensión o el contexto no dicen MV/LV (MV: celdas, >1 kV, TT/TC MT, trafos de potencia; LV: ≤ 1 kV, interruptores ACB/MCCB/MCB, tableros), o no dicen SLD/MLD, **preguntar una vez** con AskUserQuestion. Si el usuario pide "los dos", generar el par SLD+MLD del mismo equipo.
- Cada símbolo SLD puede tener sus equivalentes MLD: mismo id con sufijo `_<n>p_mld` (ej. `lv_mcb_3p_mld`). En el catálogo MLD el campo `sld_equivalent` apunta al id SLD, y en el SLD `mld_equivalent` es la LISTA de ids MLD. Mantener coherentes ports, tag y variables entre ambos.
- Antes de dibujar: leer `_catalog.json` de la carpeta destino y 2–3 símbolos parecidos como referencia de estilo/medidas. Acceso por el puente (`device_list_dir`, `device_stage_files` para leer, `device_commit_files` para escribir; `device_bash` con `$HOME/mnt/00-Template-Claude/98_LIBRARY`). Sin puente: entregar con SendUserFile y avisarlo.
- **Forma del símbolo:** tomarla de la norma IEC 60617 (`IEC_60617_Simbologia.pdf` en la raíz `E:\Proyectos\00-Template-Claude\.claude\library\`) y anotar su número (ej. S00287) en el campo `iec_60617` del catálogo. Si el equipo no está en la norma (p. ej. celdas de fabricante QM, CM, GBC), armarlo combinando símbolos IEC y decirlo en `notes` y en el README.
- **Estado actual (10/10/2026):** SLD_MV (25) y SLD_LV (39) en v2.0.0; MLD_LV (58) en **v2.1.0**, con marcación de bornes (respaldo de la v2.0.0 en `PLUGINS\MLD_LV\_backup\MLD_LV_v2.0.0`). MLD_MV está VACÍA.
- **Carpeta ASSETS**: cada plugin (`PLUGINS/<lib>/ASSETS/`) contiene documentos de referencia (normas, catálogos de fabricantes, ejemplos de proyectos, notas de optimización). Leer estos archivos cuando el usuario quiera enriquecer, estudiar u optimizar el framework.

## 1. Estándar visual (NO negociable, vale para SLD y MLD)
| Elemento | Valor |
|---|---|
| Unidad | **1 unidad = 1 mm**, símbolo a escala 1 (en el diagrama NO se agranda). Puertos sobre **retícula de 2,5 mm** |
| Trazo conductores y aparamenta | `#0000ff`, `stroke-width="0.25"`, `fill="none"`, `stroke-linecap="butt"`, `stroke-linejoin="round"` |
| Barra / nodo | línea `stroke-width="0.5"`; punto relleno `#0000ff` r=0.78 |
| Bordes de rellenos, hachurados | `stroke-width="0.18"` (mínimo absoluto: nada por debajo de 0,18 mm) |
| Línea de trazos (IRAM 4502 tipo E: enlace mecánico, ocultos, contorno de celda) | `stroke-dasharray="3 1"` |
| Trazo largo y corto (tipo F: PE, ejes) | `stroke-dasharray="10 1 2 1"` |
| Cables externos / flechas de cable | rojo `#ff0000` (flecha = triángulo relleno) |
| Tierra PE | verde `#139b48` |
| Contorno de celda MV | gris `#dcdcdc` |
| Texto estructural (I>, I>>, AR, M, G, 3~, VFD, kW, UPS) | azul `#0000ff`, font-size 3.47 (h 2,5) si entra en su caja; mínimo 2.5 (h 1,8) en cajas chicas (IΔ, 3~) |
| Texto FIJO de tipo de equipo (MCCB, ACB, RCCB, MCB, NH00, SPD, PE, CT, VT…) | **negro `#000000`, negrita, font-size 3.47 (h 2,5), `text-anchor="end"`**, a la izquierda del símbolo |
| Marcación de bornes (MLD) | negro `#000000`, font-size 2.5 (h 1,8), `anchor start`, a la derecha del conductor (ver 2b) |
| Títulos (cabecera de celda MT) | font-size 4.86 (h 3,5) |
| Texto VARIABLE | placeholder `{clave}`, verde `#008800`, font-size 3.47, dentro de `<g id="label_slots">` |
| Fuente | `font-family="Arial, sans-serif"` |

Letras (IRAM 4503): font-size = h / 0,72. h 2,5 → 3.47; h 3,5 → 4.86; h 1,8 → 2.5. Ningún texto por debajo de 2.5.

Normalización de entrada: se IGNORA el color y el grosor de la fuente: todo trazo se reescribe con el estándar (rojo/verde/gris solo si el elemento lo es semánticamente: cable externo, PE, contorno de celda). Se ignoran fondos, sombreados, marcos, cotas y texto ajeno al símbolo.

## 2. Sistema de coordenadas y medidas (mm)
- `x=0` = eje del conductor (SLD) o eje del PRIMER polo (MLD). `y=0` = puerto superior. `y` crece hacia abajo.
- Conductor entra por arriba y sale por abajo (salvo cargas/tierras: solo puerto superior; nodos de barra: solo inferior).
- Todos los puertos en múltiplos de 2,5 mm y tocando el extremo de su conductor.
- Medidas de referencia SLD_LV (medir siempre un par existente antes de dibujar):
  - `lv_mcb`: puerto inferior y=32.5. `lv_mccb_basic`: puerto inferior y=35.
  - Motor/generador: círculo r≈5.4. Nodo de barra `lv_busbar_node`: barra a y=0.78 (trazo 0.5), punto r=0.78, puerto inferior y=5.
  - Conversión aproximada desde planos viejos en pt: mm = pt × 0,49 (la retícula de 2,55 pt de las láminas de origen = 1,25 mm).
- Celdas MT: marco gris de ≈72,3 × 216,9 mm (x = ±36,2), barra a y=5 (trazo 0.5) con tramos rojos en los extremos, puertos `bus_l` (−35, 5), `bus_r` (35, 5) y `cable` (0, 212.5); rótulos de cabecera arriba (y negativa) como en `mv_cell_im_interruptor`.
- Un símbolo nuevo debe tener el mismo tamaño/proporciones que sus equivalentes de la biblioteca.
- Desplazar para que el contenido empiece en y=0 (el texto solo cuenta para el viewBox, no para los puertos).

## 2b. Multifilar (MLD) — reglas confirmadas por el usuario
- Estilo idéntico al SLD (sección 1).
- **Protecciones y maniobra (interruptores, fusibles, diferenciales, relé térmico, SPD, seccionador, contactor):** se REPITE el símbolo SLD completo una vez por polo y se generan variantes **1P, 2P, 3P y 4P** (ids `<id_sld>_1p_mld` … `_4p_mld`).
- **Paso entre polos uniforme: 12,5 mm** en todos los equipos (polo n en x = 12.5·(n−1)). En equipos con caja (ACB, MCCB, relé térmico) la caja ocupa el paso y los polos siguen pegados.
- Rotulado de polos (texto fijo negro, font-size 3.47, `anchor start`) a la derecha del conductor: x = eje + 1.2, y = −1.2. 1P = L · 2P = L N · 3P = L1 L2 L3 · 4P = L1 L2 L3 N.
- **Mecanismo común**: si el SLD tiene mecanismo a la izquierda (ACB, MCCB: cuadrado con cruz, motor M, línea de trazos vertical a la unidad de protección) se dibuja UNA vez y su línea de trazos horizontal (`3 1`) se extiende hasta el último polo. En MCB, FS, seccionador y contactor se agrega una línea de trazos de enlace mecánico (IEC 60617 S00295) entre las cuchillas. Fusibles, relé térmico y SPD no llevan enlace.
- **Diferenciales (RCCB, RCBO):** solo existen en **1P, 2P y 4P** (no hay 3P). Un Único toroide (elipse) a la misma altura que en el SLD que abarca todos los polos, y UN SOLO relé IΔ (cuadrado con texto) en el último polo de la derecha; su línea de trazos llega hasta la cuchilla del primer polo. La conexión toroide → relé sale del último polo.
- Texto fijo de tipo de equipo y rótulos variables: una sola vez, a la izquierda del primer polo (mismas posiciones que el SLD). La variable `poles` NO va en MLD.
- Puertos: `top_<polo>` y `bottom_<polo>` (ej. `top_L1`, `bottom_N`), cada uno con `data-dir`.
- **Marcación de bornes (IEC 60445 / IEC 60947, desde v2.1.0):** cada polo n lleva su número, impar arriba (2n−1) y par abajo (2n): 1-2, 3-4, 5-6, 7-8. Contactores: `1/L1 3/L2 5/L3` y `2/T1 4/T2 6/T3` en los polos de fase (L, L1, L2, L3); el polo N lleva solo 7-8 (o 3-4 en 2P). Texto negro, font-size 2.5 (h 1,8), `anchor start`, dentro de un `<g id="terminal_marks">` al final del grupo principal (así entra en el sprite). Posición: arriba en (x_polo + 1, 3,2) y abajo en (x_polo + 1, y_puerto − 1). Excepciones: ACB y MCCB x + 3 (chevrones de extraíble); fusible x + 2,3 (caja de 3,4 mm); relé térmico arriba en y 2,4 y abajo en y_puerto + 2,6 (caja pegada a los bornes). Los SPD y FU+SPD no llevan número. Agrandar el viewBox si la marca no entra. En el catálogo: `terminal_marks: [{"port": "top_L1", "mark": "1"}, …]`, las marcas también en `fixed_texts`, y `conventions.terminal_marks` con la regla. Un símbolo MLD nuevo debe traerla. Script de referencia: `PLUGINS/MLD_LV/aprendizaje_mld/_lib_v2.1.0/marcar.py` (y `sprite.py` para regenerar el sprite y copiar el viewBox al catálogo).
- Si la fuente ya es multifilar, respetar su disposición de fases (normalizada al paso de 12,5 mm) y no inventar otra.
- Para equipos que no son protección ni maniobra (medición, trafos, cargas) aún no hay muestra MLD: pedir un ejemplo al usuario antes de generar en lote.

## 3. Puertos (OBLIGATORIO desde el inicio — sin excepciones)
**Todo símbolo entregado a las bibliotecas SLD_LV, MLD_LV, SLD_MV y MLD_MV DEBE incluir su grupo de puertos correctamente definido.** Un símbolo sin puertos no está terminado y no puede entregarse.

Grupo oculto `<g id="ports" display="none" fill="#ff00ff" stroke="none">` con `<circle id="port_top" cx cy r="0.6" data-dir="up"/>` y `port_bottom` (`data-dir="down"`). Puertos extra (`secondary`, `primary`, `bus_l`, `bus_r`, `cable`, `trip`, `top_1`/`top_2`) con `data-dir` left/right/up. Coordenadas en la retícula de 2,5 mm, sobre el extremo del conductor. Se calculan sobre el cuerpo (primitivas + texto fijo), NO sobre los placeholders.

Reglas de puertos por tipo de símbolo:
- **SLD pasante** (interruptores, fusibles, aparamenta en serie): `port_top` (y=0, dir=up) + `port_bottom` (y=altura, dir=down). Ambos obligatorios.
- **Carga / terminal SLD** (motor, generador, condensador, cargador, iluminación): solo `port_top` (y=0, dir=up). Sin port_bottom.
- **Barra / nodo**: solo `port_bottom` (y=altura, dir=down).
- **Celda MV**: `port_bus_l`, `port_bus_r` (en la barra) + `port_cable` (y inferior). Los tres obligatorios.
- **MLD pasante**: un par `top_<polo>` + `bottom_<polo>` por cada polo. Todos los polos declarados.
- **MLD terminal** (motor, generador, condensador): solo `top_<polo>` por cada polo. Sin bottoms.

Verificar que cada puerto esté sobre el extremo exacto del conductor y alineado a la retícula de 2,5 mm.

## 4. Texto: fijo vs variable
- **Fijo** (parte de la simbología, no cambia entre proyectos): tipo de equipo, marcas estructurales y marcación de bornes. `<text>` dentro del grupo principal.
- **Variable** (cambia por proyecto): **todo símbolo nuevo lleva las variables de los datos técnicos que requiere ese equipo**, no solo `{tag}`. Diccionario (claves en inglés, minúsculas, snake_case): marca (`manufacturer`), modelo (`model`), corriente nominal (`rated_current`), poder de corte (`breaking_capacity`), polos (`poles`), curva (`curve_rating`), sensibilidad (`sensitivity`), retardo (`time_delay`), unidad de disparo (`trip_unit`), clase (`class`), corriente de impulso (`impulse_current`), potencia (`power_kw`, `rated_power`), corriente (`current`), designación (`designation`), tag (`tag`), sección de cable (`cable_spec`), tensión (`voltage`), relación TC (`ct_ratio`), relación TT (`vt_ratio`), fusible (`fuse_rating`), corriente de cortocircuito (`short_circuit_current`), funciones ANSI (`ansi_functions`), clase de precisión (`accuracy_class`), rango de escala (`scale_range`), color de señalización (`color`), serie y número de serie en celdas MV (`series`, `serial`).
- Cada variable en `<g id="label_slots">` con `data-key` y `data-example`.
- Todo símbolo lleva al menos `{tag}` (ejemplo `-Q1`), salvo flechas de cable, leyendas y celdas MV.

## 5. Procedimiento según la entrada
**A. PDF vectorial (CAD):** `pdfplumber` → extraer líneas, rectángulos, texto. Recortar al símbolo, pasar a mm, fusionar segmentos colineales, mapear colores al estándar.
**B. Imagen / PDF raster / foto / boceto:** NO vectorizar automáticamente. Mirar, identificar el símbolo normalizado IEC y **redibujarlo con primitivas ideales** en las medidas de la sección 2.
**C. Descripción en texto:** igual que B, tomando la forma de IEC 60617.
**D. MLD de un SLD existente:** replicar el cuerpo del SLD por polo desplazando x en múltiplos de 12,5 mm, según 2b, y agregar la marcación de bornes.

## 6. Estructura del archivo SVG
```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="X Y W H" width="Wmm" height="Hmm" role="img" aria-label="NOMBRE_ES">
  <title>NOMBRE_ES</title>
  <desc>DESCRIPCIÓN | Origen: FUENTE. NOTAS</desc>
  <g id="ID_SIMBOLO" fill="none" stroke-linecap="butt" stroke-linejoin="round" font-family="Arial, sans-serif">
    <!-- cuerpo del símbolo -->
  </g>
  <g id="ports" display="none" fill="#ff00ff" stroke="none">...</g>
  <g id="label_slots" fill="#008800" font-family="Arial, sans-serif">...</g>
</svg>
```
- `viewBox` = bbox del contenido + 1 mm de margen.
- Solo primitivas vectoriales (`line`, `rect`, `path`, `text`, `circle` solo para puertos). Sin imágenes, base64, `transform` ni CSS externo.
- Nombre de archivo = id (snake_case inglés).

## 7. Catálogo, sprite y vista previa
Por símbolo, en `_catalog.json`: id, file, diagram_type, sld_equivalent/mld_equivalent, name_es, name_en, description, tags, origin, source, notes, iec_60617, size, viewBox, ports, fixed_texts, label_slots. En MLD, además poles y terminal_marks.
`_library.svg` (sprite), `_preview.png` y `README.md` actualizados con cada cambio.

## 8. Verificación obligatoria antes de entregar
1. XML válido de cada SVG.
2. Renderizar y MIRAR (cairosvg). Comparar con la fuente y con el SLD equivalente lado a lado.
3. Verificar puertos: grupo `<g id="ports">` presente con todos los puertos del tipo de símbolo (ver sección 3).
4. Trazos solo 0.25 / 0.5 / 0.18; dashes solo `3 1` y `10 1 2 1`; puertos en retícula de 2,5 mm; texto ≥ 2.5; variables solo `{clave}`; nada fuera del viewBox.
5. Mismo tamaño/proporciones que sus pares; en pares SLD/MLD, mismas claves de variables y mismo tag.

## 9. Entrega
- Mostrar UNA muestra antes de generar en lote y esperar OK.
- Escribir en la carpeta correcta. Subir versión al cambiar o agregar un símbolo. No renombrar ids ya usados.
- Responder en español: qué símbolos se agregaron, qué quedó fijo vs variable, incertidumbres.
