---
name: "generate-iram-sheet"
description: "Genera láminas de dibujo técnico A0, A1, A2, A3 o A4 en SVG con recuadro y rótulo según IRAM 4504 y 4508, listas para colocar un diagrama eléctrico."
---

# Láminas IRAM A0 a A4 (recuadro + rótulo)

## Contexto de ejecución
- **Invocación:** pipeline o explícita — esta skill es un componente de soporte.
  - **Pipeline:** se invoca automáticamente como sub-paso dentro de `create-electrical-line-diagram` o `convert-sld-to-mld` para preparar la hoja antes de insertar el diagrama. En este caso NO requiere confirmación adicional del usuario.
  - **Explícita:** se invoca cuando el usuario pide directamente una lámina IRAM vacía o con un diagrama ya existente.
- **No ejecutar de forma independiente** salvo pedido explícito del usuario o llamada desde otra skill del pipeline.
- **Contexto requerido:** directorio `03_ENGINEERING`. No ejecutar en `90_MANAGEMENT`, `01_INPUT`, `02_PROJECT`.

Usá esta skill cuando haya que preparar una hoja de plano (A0, A1, A2, A3 o A4) con su recuadro (frame) y su rótulo según las normas IRAM, o cuando haya que poner un diagrama dentro de una de esas hojas.

Todo se dibuja con el script `lamina_iram.py`, que está completo al final de esta skill. No dibujes la lámina a mano: copiá el script tal cual a un archivo y ejecutalo.

## Las cinco láminas

Unidades en mm, origen arriba a la izquierda (1 unidad SVG = 1 mm).

| Lámina | Hoja (ancho × alto) | Orientación | Márgenes del recuadro | Coordenadas | Zona útil (x0..x1 × y0..y1) | Rótulo fig. 2 (x × y) | Modificaciones fig. 3 (x × y) |
|---|---|---|---|---|---|---|---|
| A0 | 1189 × 841 | Horizontal | 20 en los 4 lados | 12 × 6 (M..A, 6..1) | 25..1164 × 25..816 | 989..1164 × 765..816 | 989..1164 × 743,5..765 |
| A1 | 841 × 594 | Horizontal | 25 izq., 10 resto | 8 × 4 | 30..826 × 15..579 | 651..826 × 528..579 | 651..826 × 506,5..528 |
| A2 | 594 × 420 | Horizontal | 25 izq., 10 resto | 6 × 3 | 30..579 × 15..405 | 404..579 × 354..405 | 404..579 × 332,5..354 |
| A3 | 420 × 297 | Horizontal | 25 izq., 10 resto | 4 × 2 | 30..405 × 15..282 | 230..405 × 231..282 | 230..405 × 209,5..231 |
| A4 | 210 × 297 | Vertical | 25 izq., 10 resto | Sin coordenadas | 25..200 × 10..287 | 25..200 × 236..287 | 25..200 × 214,5..236 |

Qué lleva cada lámina:
- **Todas:** línea de corte de la hoja, recuadro de 1,0 mm, señales de centrado de 0,5 mm y el rótulo IRAM 4508 fig. 2 (175 × 51) abajo a la derecha, apoyado en la esquina de la zona útil.
- **A0 a A3:** franja de coordenadas de 5 mm con letras (A del lado del rótulo) y números (1 abajo), escala de comparación de 200 mm arriba a la izquierda y flecha de orientación abajo al centro.
- **A4:** sin coordenadas, sin escala de comparación y sin flecha (nota de la fig. 6 de IRAM 4504).

## Los dos bloques del rótulo

Son bloques distintos y no se mezclan:
- **Rótulo (IRAM 4508 fig. 2), 175 × 51:** va siempre. Columnas 26 / 20 / 10 / 19 / 45 / 55. Espesores: contorno 0,8; límites de casilla 0,4; subdivisiones 0,2. Sus únicas leyendas impresas son Fecha, Nombre, Dib., Rev., Apr., Esc., Toler. y Rug., más el símbolo del método ISO (E).
- **Lista de modificaciones (fig. 3), 175 × 21,5:** va solo cuando el plano registra modificaciones. Se apoya encima del rótulo. Tiene la casilla 12 (120 de ancho) y la casilla 13 (55 de ancho). Se agrega con `--mod`.

No agregues casillas, renglones ni leyendas que la norma no tiene.

## Campos a completar

Los textos variables son `<text data-key="clave">{clave}</text>`. Reemplazá el contenido `{clave}` por el valor. Si un campo no se usa, dejalo vacío.

| Clave | Casilla | Contenido |
|---|---|---|
| notas | 1 | Anotaciones complementarias (puede incluir "Hoja N de M") |
| escala | 2 | Escala, o "S/E" en diagramas eléctricos |
| cliente | 6 | Cliente |
| denominacion, denominacion_2 | 7 | Denominación de lo representado (2 renglones) |
| empresa | 8 | Empresa que hace el plano |
| plano_n | 9 | Número o clave del plano |
| emision | 10 | Fecha de emisión |
| reemplaza | 11 | Plano que reemplaza o reemplazante |
| plano_propio | 13 (solo con `--mod`) | Número propio cuando en 9 va el del cliente |

## Pasos

1. Copiá el script del final a `lamina_iram.py`. Ejecutalo con `python3 lamina_iram.py <A0|A1|A2|A3|A4> [salida.svg] [--mod]`. Imprime la zona útil y la posición del rótulo. Además deja `bloque_rotulo_IRAM4508.svg` y `bloque_modificaciones_IRAM4508.svg` junto a la salida, para usarlos como bloques sueltos.
2. Completá los campos reemplazando `{clave}` en el SVG. Escapá `&`, `<` y `>` en los valores.
3. Si hay un diagrama, ponelo dentro de `<g id="dibujo">`. Tiene que quedar dentro de la zona útil (`data-zona-util` del `<svg>`) y fuera del rectángulo del rótulo (`data-rotulo`). Si se usa `--mod`, también fuera de `data-modificaciones`. Escalá o trasladá el diagrama con `transform` y no toques el resto de los grupos.
4. Si hace falta un PDF a tamaño real, convertilo con `cairosvg.svg2pdf(url=svg, write_to=pdf)`. Verificá con `pdfinfo` que el tamaño de página sea el del formato.
5. Revisá visualmente: renderizá a PNG y mirá el rótulo y los bordes del diagrama.

## Criterios del script

- A0: margen de 20 en los 4 lados, porque el archivado usa banda adhesiva (IRAM 4504 fig. 16).
- A1 a A4: margen de archivado de 25 a la izquierda y de 10 en el resto (fig. 5).
- Coordenadas de alrededor de 105 × 148,5. A1 (8 × 4) y A3 (4 × 2) son exactas como en la fig. 6. A0 (12 × 6) y A2 (6 × 3) son la cantidad par más cercana.
- El grosor de 1,0 del recuadro y el margen de 20 del A0 son decisiones propias, porque la norma no fija esos valores. El resto sale de las figuras del Manual IRAM.

## Script completo

El script `lamina_iram.py` está disponible en:
el módulo `epc_drawing.titleblock.lamina_iram` (`python -m epc_drawing.titleblock.lamina_iram <A0|A1|A2|A3|A4> [salida.svg] [--mod]`)

Copiarlo a la carpeta de trabajo del proyecto y ejecutarlo desde allí.

Uso: `python3 lamina_iram.py <A0|A1|A2|A3|A4> [salida.svg] [--mod]`
