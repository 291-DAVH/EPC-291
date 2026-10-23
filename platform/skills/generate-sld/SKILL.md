---
name: "generate-sld"
description: "Genera el diagrama unifilar (SLD) de un tablero en láminas IRAM (A1 o A3) a partir de un Excel de circuitos, con fórmulas de elec-calc-generator, símbolos de iec60617-symbol-generator y rótulos de iram-titleblock-plugin. Entrega SVG y DXF por hoja."
---

# sld-generator

## Fuentes (carpeta del plugin `sld-generator`)
- **Fórmulas:** `vendor/elec-calc-generator.plugin` -> `scripts/voltage_drop.py` (caída de tensión, ΔU). Cortocircuito y conductores todavía no están integrados.
- **Símbolos:** `vendor/iec60617-symbol-generator.plugin` -> `src/sld-lv-symbol`.
- **Rótulo:** `vendor/iram-titleblock-plugin.plugin` -> `scripts/titleblocks-generator.py` (y `sheet-generator.py` para la lámina A0–A4).
- **Entradas en `src/`:** `input_for_sld_V1.xlsx` (hojas TABLERO y CIRCUITOS) e `input-titleblocks.xlsx` (rótulo, una fila por hoja).
- **Logos:** `src/provider-logo-*.svg` y `src/client-logo-*.svg`, junto al Excel de rótulos. Se copian a la carpeta de trabajo antes de generar.
- **Dependencias Python:** `openpyxl`, `lxml`, `cairosvg`, `ezdxf`, `svgelements`, `shapely`.
- Los `vendor/*.plugin` son de solo lectura: no se modifican desde este plugin.

## Reglas de cantidad
- **Hojas:** la define la cantidad de circuitos. `sld_paginate.py` agrupa las salidas por circuito raíz hasta `maxl` hojas-hoja (18 por defecto; el tercer argumento opcional lo cambia). Un circuito raíz con muchas salidas no se parte: puede quedar sola en una hoja que supera `maxl`.
- **Rótulos:** uno por hoja. Antes de generar, `input-titleblocks.xlsx` se reescribe con una fila por hoja (plano propio `<NAME>_H<i>`, página `i / N`, denominación y proyecto). Los datos comunes (empresa, cliente, personas) salen de la primera fila del formato pedido.
- **Nombre en el rótulo:** sin sufijo de hoja (queda "TGBT-02 – TABLERO PLANTA BAJA"). El número de hoja va en "Página (n / m)". El sufijo "(hoja N de M)" solo aparece en el título del dibujo.
- **Lista de modificaciones:** NO. `MOD_LISTA = False` en `sld_generator.py`; activarla solo con revisiones cargadas.

## Formato de lámina
- **A1** (841 × 594, por defecto): diagrama a escala 1 en la zona útil, columna de referencias a la derecha del rótulo, tabla de circuitos bajo el diagrama.
- **A3** (420 × 297, `SLD_FORMATO=A3`, en prueba):
  - el recuadro del diagrama ocupa x 35–400 mm con 5 mm de margen izquierdo, derecho y superior (escala 0,60);
  - la tabla de circuitos va bajo el diagrama, a la misma escala;
  - referencias, cálculos, verificación y notas van en tres columnas a la izquierda del rótulo, a escala 1 y con texto de 2 mm;
  - la prueba usa `maxl = 9` (6 hojas para 13 circuitos).
- No hay otros formatos para el SLD.

## Comando
Desde la raíz del plugin:
`python src/sld_paginate.py default src/input_for_sld_V1.xlsx <carpeta_salida> <NAME> default default [maxl]`
Para A3: anteponer `SLD_FORMATO=A3`.

## Salidas por hoja
- `<NAME>_H<i>.svg`: lámina del plugin con el diagrama en la casilla `dibujo`.
- `<NAME>_H<i>.dxf`: convertidor del plugin (`svg_to_dxf.convertir`) y después `src/capas_dxf.py`.
- `<NAME>_H<i>_calculo.json`: cálculos de la hoja.
- `<NAME>_TABLA.svg` / `.dxf`: hoja propia con la **tabla de cálculo de circuitos** (todos los circuitos del tablero, en el mismo formato que el diagrama). Las hojas del diagrama no llevan la tabla. Su rótulo dice "TABLA DE CÁLCULO DE CIRCUITOS" y va numerada como la última.
- No se generan PDF ni PNG.

Las referencias, cálculos y verificación siguen en las hojas del diagrama.

## Ajustes del DXF (`src/capas_dxf.py`)
Se aplican sobre el DXF del plugin, sin modificarlo:
- **Capas:** todas las hojas tienen la misma tabla de capas y estados: `291-E-DIAGRAMA` (color 5), `291-E-TEXTOS` (7), `291-G-ROTULO` (7), `291-A-LAMINA` (8). Todas encendidas, no congeladas, no bloqueadas, tipo Continuous. Las capas viejas (LINEAS, TEXTO, LOGOS) se eliminan. La asignación de capas usa coordenadas A1; en A3 no está ajustada.
- **Color y grosor:** cada línea y texto toma el color y grosor de trazo del SVG (negro → color 7). El rótulo y el marco conservan el color de su capa.
- **Trazos discontinuos:** se crea un tipo de línea por patrón (`SVG_DASH_n`) a partir de `stroke-dasharray`.
- **Rellenos:** las formas cerradas con relleno (flechas, puntos de unión) se pasan a HATCH con su color.
- **Negrita:** los textos en negrita usan el estilo `ARIAL_BOLD`.
- **Altura de texto (A3):** texto del diagrama a 1,7 mm, proporcional al SVG; letras del marco a 1,7 mm. El rótulo mantiene su altura original.
- **Posición de texto (A3):** los textos del diagrama vuelven a su posición exacta del SVG (el convertidor la desplaza por la lógica de rótulo).
- **Separación de textos (A3):** los textos que se solapan se empujan perpendicularmente a su línea. Las líneas de un mismo cable (textos rotados) se reparten con 3,4 mm de paso, manteniendo orden y centro. Un mismo cable agrupa sus líneas a menos de 7,5 mm entre sí.
- Si un DXF está abierto en CAD, el generador avisa y no lo sobrescribe: cerrarlo y regenerar.

## Entrada desde plantilla Excel
Hoja **TABLERO**: NOMBRE, TENSION_V, SISTEMA (TN-S/TN-C-S/IT), ICC_KA; opcionales FP_DEFAULT (0,85 por defecto), FRECUENCIA_HZ (50), PROYECTO, LONG_ACOMETIDA_m.

Hoja **CIRCUITOS**:
- Obligatorias: TAG, DESCRIPCION, CARGA, UNIDAD_CARGA (`A|W|kW|MW|VA|kVA|MVA|HP`), DESTINO.
- Opcionales: PARENT_TAG, TOPOLOGY, FASE (3F/1F/3F+N), LONGITUD_m, FP, RENDIMIENTO, KIND, NOTAS.

**Conversión a Ib:** `A` → Ib = CARGA; `W/kW/MW` → Ib = P / (√3·V·FP) en 3F o P / (V·FP) en 1F; `VA/kVA/MVA` → S / (√3·V) en 3F o S / V en 1F; `HP` → kW = CARGA · 0,7457 / RENDIMIENTO.

**PARENT_TAG:** vacío = cuelga de la barra principal; con valor = hijo del equipo indicado. Un padre sin CARGA suma las de sus hijos (ej. RCCB → N MCB).

**TOPOLOGY:** `single` (MCCB o MCB según Ib), `dol` (MPCB + KM), `dol_ol` (MCB/MCCB + KM + OL), `star_delta`, `softstarter`, `vfd`, `dol_rcd`, `manual` (usa KIND). Si se omite, se infiere por KIND e Ib.

**Dimensionado (AEA 90364 / IEC 60364):** In ≥ 1,25·Ib en motores y ≥ Ib en el resto; Icu ≥ ICC_KA en comercial (6/10/16/25/36/50/65/85/100 kA); sección con Iz ≥ In y ΔU ≤ 3 % (5 % motores); 4P (3F+N TN-S), 3P (3F), 2P (1F).

## Procedimiento
1. Leer el Excel con `openpyxl`; calcular Ib, In, Icu y sección antes de dibujar.
2. Verificar que `src/input-titleblocks.xlsx` tenga la fila A1 con los datos comunes.
3. Generar las hojas con el comando y revisar el resultado: cantidad de hojas, circuitos por hoja, rótulos y columnas de texto sin pisarse.
4. Revisar el DXF en CAD: altura de texto, colores, separación de los textos de cable y capas.

## Reglas del generador
- Símbolos: se insertan desde la biblioteca de `iec60617-symbol-generator` sin escalarlos (K = 1). No se redibujan a mano.
- Colores: azul `#0000ff` para conductores internos y aparamenta; rojo `#ff0000` para cables externos; verde `#139b48` para PE; negro para textos, marco y tablas.
- Barra PE: por encima de las cargas, con su puesta a tierra a la izquierda y la etiqueta "BARRA PE".
- Grosores: conductores 0,25; BUS de potencia y barra de tierra 0,7.
- Escapar `&` como `&amp;` en todos los textos.
- Si falta un símbolo de la biblioteca, avisar al usuario y no modificar la biblioteca sin preguntar.

## Pendientes conocidos
- Separar símbolos de conductores en `291-E-SIMBOLOS` y `291-E-CONDUCTORES` (requiere etiquetar el SVG).
- Capas del DXF en A3: `capas_dxf.py` asigna capas con coordenadas A1.
- Nombres de tablero largos pueden salirse de la casilla del rótulo (el plugin no ajusta el texto).
- Datos de empresa, cliente y códigos en el Excel del rótulo: completar antes de entregar.
- Referencias, cálculos y notas en A3 quedan en texto de 2 mm y pueden no caber cuando hay muchos circuitos por hoja.
- Archivo `.lay` de estados de capas de AutoCAD: no generado.
