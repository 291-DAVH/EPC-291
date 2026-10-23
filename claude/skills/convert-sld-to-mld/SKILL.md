---
name: "convert-sld-to-mld"
description: "Convierte un diagrama unifilar (SLD) de tablero en multifilar (MLD) usando los símbolos MLD_LV de la biblioteca ELECTRICAL_SYMBOLS, con paso uniforme entre polos."
---

# convert-sld-to-mld

## Camino automático (preferido)
El generador `epc_drawing.mld.mld_generator` dibuja el multifilar a partir de los mismos datos y del mismo cálculo que el unifilar (`epc_calc.aea_pipeline`, con los criterios de diseño del proyecto): cada línea se despliega en L1 L2 L3 N, con los símbolos `<id>_<n>p_mld` a paso de 10 mm, cargas monofásicas repartidas entre fases, grupos con RCCB como sub-barras, PE y cable externo.
- Con el plugin `board-design`: `python -m epc_drawing.board_design --project <carpeta> --out <trabajo> --name <TABLERO> --diagrams sld,mld`.
- Solo el multifilar, con un cálculo ya hecho: `python -m epc_drawing.mld.mld_generator --input board.json --calc <TABLERO>_dimensionado.json --out <carpeta> --name MLD_<TABLERO>`.
- En la aplicación web: pestaña *Datos del unifilar* → *Generar multifilar*.
El procedimiento manual de más abajo queda como respaldo para casos que el generador no cubre (símbolos especiales, orígenes en PDF o imagen).

## Contexto de ejecución
- **Invocación:** pipeline — ejecutar solo cuando el usuario solicite explícitamente la conversión a MLD Y exista un SLD de origen (generado por `create-electrical-line-diagram` o entregado directamente por el usuario como SVG, PDF o Excel).
- **Contexto requerido:** directorio `03_ENGINEERING`. No ejecutar en `90_MANAGEMENT`, `01_INPUT`, `02_PROJECT` ni `04_REVIEW`.
- **No ejecutar automáticamente** después de generar un SLD: el pipeline SLD→MLD requiere confirmación explícita del usuario. El SLD es un entregable independiente.
- **Señales de activación:** el usuario dice "convertir a multifilar", "hacer el MLD", "desplegado", "multifilar de este tablero", o entrega un SLD y pide el MLD correspondiente.

Convierte un SLD (SVG, PDF, imagen o plantilla Excel MINIMAL) en un MLD (SVG + PDF + PNG de control), "desplegando" cada línea en sus conductores reales. Usa los símbolos de `PLUGINS/MLD_LV` (y `PLUGINS/SLD_LV` para auxiliares: tierra, TI, AR, flechas). No modifica la biblioteca. Si falta un símbolo, usar la skill `generate-electrical-symbol` y avisar.

**Biblioteca en mm (IRAM):** MLD_LV v2.1.0 (con marcación de bornes) y SLD_LV v2.0.0. Símbolos a escala 1, puertos en retícula de 2,5 mm, paso entre polos 12,5 mm, trazo 0,25, letras h 2,5. Se insertan sin escalar sobre una lámina IRAM (skill `iram-titleblocks-generator`, por defecto A1).

**Ruta de la biblioteca:** `E:\Proyectos\00-Template-Claude\.claude\library\plugins\` (acceso por el puente con `$HOME/mnt/00-Template-Claude/98_LIBRARY`). Cada plugin tiene una carpeta `ASSETS/` con documentos de referencia (normas, catálogos, ejemplos de proyectos) que se pueden leer para enriquecer el contexto.

**Ejemplo aprobado (10/10/2026):** `PLUGINS/MLD_LV/aprendizaje_mld/MLD_TS-01_A1` (SVG, PDF, PNG) con su generador `mld_ts01.py`, la lección `LECCION_MLD_01.md` y el estudio de planos reales `ANALISIS_entrenamiento_mld.md`. Usar `PLUGINS/MLD_LV/aprendizaje_mld/mld_ts01.py` como plantilla del generador: tiene los ayudantes `sym`, `bajada`, `puente`, `borne`, `bornera`, `salida`, `wl` (número de conductor) y `ubic` (coordenada de la lámina). `CORE/build_tgbt_mld.py` es una prueba vieja en pt: sirve solo como idea de acoplamientos y derivaciones escalonadas, no copiar sus números.

## Entradas
- El SLD de origen: SVG, PDF, imagen, o plantilla Excel MINIMAL (`sld_to_mld_input_MINIMAL.xlsx`). Si no es obvio cuál, preguntar.
- Salida en una carpeta del proyecto (nunca dentro de la biblioteca), p. ej. `/mnt/project-files/CONVERSIONES_MLD/<nombre>_mld.svg` + `.pdf` + `.png`.

## Entrada desde plantilla Excel MINIMAL
Cuando el usuario entrega `sld_to_mld_input_MINIMAL.xlsx` (o archivo similar con hojas TABLERO y CIRCUITOS), leer con `openpyxl`:

**Hoja TABLERO:**
- Obligatorios: NOMBRE, TENSION_V, SISTEMA (TN-S / TN-C-S / IT), ICC_KA
- Opcionales: FP_DEFAULT (cos φ por defecto = 0,9), FRECUENCIA_HZ (50), PROYECTO

**Hoja CIRCUITOS — columnas:**
- Obligatorias: TAG, DESCRIPCION, CARGA, UNIDAD_CARGA (`A|W|kW|MW|VA|kVA|MVA|HP`), DESTINO
- Opcionales: PARENT_TAG, TOPOLOGY, FASE (3F / 1F / 3F+N), LONGITUD_m, FP, RENDIMIENTO (motor), KIND, NOTAS

**Conversión de UNIDAD_CARGA a Ib:**
- `A`: Ib = CARGA (directo)
- `W`/`kW`/`MW`: Ib = P / (sqrt(3)*V*FP) si 3F, o P / (V*FP) si 1F
- `VA`/`kVA`/`MVA`: Ib = S / (sqrt(3)*V) si 3F, o S / V si 1F
- `HP`: P_kW = CARGA * 0,7457 / RENDIMIENTO; luego igual que kW

**PARENT_TAG — jerarquía de circuitos:**
- Vacío: el circuito cuelga de la barra principal
- Con valor: apunta al TAG de un equipo padre (p. ej. un RCCB grupal). El hijo MLD se dibuja aguas abajo del padre.
- El padre con CARGA vacía suma automáticamente las cargas de sus hijos
- Se permiten varios niveles de anidamiento (árbol)

**TOPOLOGY — cadena vertical de símbolos:**
| Código | Cadena de símbolos MLD |
|---|---|
| `single` | MCCB o MCB según Ib |
| `dol` | MPCB + KM |
| `dol_ol` | MCB/MCCB + KM + OL |
| `star_delta` | MCCB + KM_principal + KM_estrella + KM_delta + OL |
| `softstarter` | MCCB + SS + OL |
| `vfd` | MCCB + VFD |
| `dol_rcd` | RCCB + MPCB + KM |
| `manual` | usar KIND tal cual sin inferencia |

Omitido: inferir por KIND y/o Ib (motor <= 32 A -> `dol`; motor > 32 A -> `dol_ol`; carga general -> `single`).

**Dimensionado automático (AEA 90364 / IEC 60364):**
- In: primer valor comercial >= 1,25*Ib para motores; >= Ib para el resto
- Icu: >= ICC_KA redondeado al comercial superior (6/10/16/25/36/50/65/85/100 kA)
- Sección cable (método B2, XLPE, 40 °C): Iz >= In y delta_U <= 3 % (terminales) / 5 % (motores)
- Polos: 4P si SISTEMA = TN-S y FASE = 3F+N; 3P si FASE = 3F; 2P si FASE = 1F; RCCB/RCBO solo 1P/2P/4P

## Procedimiento
1. **Leer el origen**: renderizar a PNG (SVG: cairosvg; PDF: `pdftoppm`) y recortar/ampliar con PIL las zonas con detalle (marcas de conductores, datos de protecciones). En SVG, leer los `<text>` para los valores exactos. Para Excel: leer con `openpyxl`, dimensionar y construir el diccionario de circuitos antes de cualquier dibujo.
2. **Leer la biblioteca**: `PLUGINS/MLD_LV/README.md`, `PLUGINS/MLD_LV/_catalog.json` (`ports`, `label_slots`, `terminal_marks`, `conventions.pole_pitch_mm`) y `PLUGINS/SLD_LV/_catalog.json` para auxiliares.
3. **Determinar el nº de conductores de cada tramo** por las marcas del SLD:
   - 3 rayas + círculo (o 4 rayas) = 3F+N -> equipos 4P (L1 L2 L3 N).
   - 3 rayas sin círculo = 3F -> equipos 3P (L1 L2 L3), sin neutro.
   - 2 rayas = F+N -> equipos 2P (L N).
   - Confirmar con la sección del cable de salida (p. ej. 3x16 sin N = 3F).
4. **Mapear cada equipo SLD a su versión MLD** `<id SLD>_<n>p_mld` (ACB, MCCB, MCB, RCCB/RCBO solo 1P/2P/4P, NH00, FS, SPD, FU+SPD, contactor, térmico, seccionador). Polos según AEA 771.20.5.1: general de tablero trifásico 4P (corta el neutro), trifásico con neutro 4P, trifásico sin neutro (motor) 3P, monofásico 2P. Prohibidos los unipolares y los "1P+N" en circuitos terminales; un MCCB 3P con borne seccionable de neutro (como en planos EPLAN extranjeros) solo puede valer en un seccional y hay que avisarlo. Si el origen trae un neutro sin cortar, marcarlo como observación.
5. **Generar la lámina** con `python -m epc_drawing.titleblock.lamina_iram <FMT> [--mod]` y llenar el rótulo IRAM 4508.
6. **Generar con un script Python** que inserta los símbolos (`<g transform="translate(x,y)">` + contenido del SVG sin `<metadata>`, `<title>`, `<desc>`, grupo `ports` ni atributos `id`; x, y en mm sobre la retícula de 2,5 mm, sin `scale`) y sustituye `{clave}` por los datos del origen.
7. **Renderizar y revisar** el PNG (cairosvg), recortar zonas con PIL, corregir y repetir.
8. **Entregar** SVG + PDF + PNG en la carpeta del usuario y resumir las interpretaciones hechas.

## Reglas del MLD (aprobadas por el usuario)
- **Paso uniforme**: la separación entre conductores/polos es SIEMPRE 12,5 mm en todo el plano (la de todos los símbolos MLD_LV). Equipos en serie de la misma rama quedan alineados polo a polo, sin quiebres. Enlace mecánico con línea de trazos IRAM tipo E (`stroke-dasharray="3 1"`) donde corresponda (MCB, FS, seccionador, contactor; ya viene en los símbolos).
- **Etiquetas de polo** (L1, L2, L3, N, L): al costado derecho de cada línea (x + 1.2, anchor start, y - 1.2, font-size 3.47), nunca encima del conductor.
- **Barras**: cada barra del SLD se convierte en 4 barras horizontales L1, L2, L3, N (azul, trazo 0.5, separación 7,5 mm), con su rótulo (BdP = xxxx A) y nombres de fase a la izquierda. Barra PE verde aparte (trazo largo y corto `10 1 2 1`).
- **Conexiones**: punto relleno (r = 1) donde un conductor se conecta a su barra o en una derivación; los cruces sin conexión van sin punto. Cada conductor de un equipo va a la barra de su fase.
- **Reparto de fases**: las salidas monofásicas (F+N) se reparten L1, L2, L3 sucesivamente, cada una con **su propio conductor N** desde la barra N (el neutro no es común a varios circuitos). Armar el balance de fases en la columna derecha y poner la reserva en la fase menos cargada.
- **Derivaciones escalonadas** (p. ej. NH00+SPD tomados de la acometida): tomas a alturas crecientes por fase (L1 la más alta), separadas 2,5 mm, para que no se crucen entre sí.
- **Acoplamiento entre barras**: tomar las 4 barras del tablero A, y desde la salida del interruptor bajar, correr y subir a las barras del tablero B con recorridos anidados (L1 el más profundo y externo) para que no se crucen.
- **SPD**: salidas unidas por un conductor verde a la barra PE (o a `lv_earth_pe`). Es el único lugar donde un activo llega al PE.
- **PE**: nunca pasa por un polo, un fusible ni el toroide de un diferencial. El PE de la acometida entra por la izquierda directo a la barra PE, sin pasar por el general.
- **Marcación de bornes** (IEC 60445 / IEC 60947): ya viene en los símbolos MLD_LV v2.1.0 (1-2, 3-4, 5-6, 7-8; contactor 1/L1 3/L2 5/L3 y 2/T1 4/T2 6/T3; los SPD sin número). No dibujarla a mano ni taparla. El motor lleva sus bornes U1 V1 W1 (texto negro h 1,8 junto a cada entrada; W2 U2 V2 en estrella-triángulo).
- **Borneras de salida**: cada salida termina en su bornera `-X1`, `-X2`... dentro del tablero, con bornes numerados 1, 2, 3... (rectángulo 4 x 5 mm, azul 0,25, número negro h 1,8 a la derecha) y un borne **PE** verde. El tag `-Xn` va a la izquierda del primer borne. El conductor es azul desde el último equipo hasta la bornera, y el cable de campo sale en rojo desde la bornera hasta la flecha o la carga. El PE baja de la barra PE a su borne y sigue en verde.
- **Barra PE**: justo arriba de las borneras (aprox. 12 mm), dentro del recinto, cruzando los conductores azules sin punto. Las borneras quedan dentro del recinto y los cables rojos salen cruzando su borde.
- **Número de cada conductor**: fase*100 + circuito*10 + tramo, y `N` + circuito*10 + tramo para el neutro. Ejemplo: 121 = L1 del circuito 2 en el primer tramo (barra a equipo), 122 el siguiente; N21, N22 su neutro. El general es el circuito 0 (101, 201, 301, N01 hacia las barras). Si hay protecciones sin número propio (p. ej. -F1 del DPS), asignarles un circuito libre y decirlo en las notas. Texto negro h 1,8 (font-size 2.5) girado -90 grados, a la izquierda del conductor (x - 0,8), centrado en el tramo; en tramos de 5 mm entre equipos también va. El cable de campo no lleva número de conductor sino su designación `-Wn` delante de la formación (`-W2 5x4 mm2 * 30 m`).
- **Salidas**: cada conductor termina en flecha roja con su fase (L1, L2, L3, N) a la derecha; el PE en flecha verde con etiqueta PE. Debajo, destino (azul) y cable con su `-Wn` (negro), h 2,5.
- **Tabla de circuitos** bajo el diagrama: Circ., **Ubic.** (coordenada de la lámina del equipo principal, p. ej. F4: en A1 la letra es `'HGFEDCBA'[int(x / 105.125)]` y la fila `4 - int(y / 148.5)`, con x, y en mm de la hoja; A0 tiene 12 columnas M..A y 6 filas, A2 6 y 3, A3 4 y 2, y el módulo es hoja / cantidad), Destino, Conductores, Fase, Polos, Protección, **Bornera** (`-X2 1-4, PE`), Cable (`-W2 5x4`), IB.
- **Columna derecha** (175 mm, sobre el rótulo): REFERENCIAS (siglas usadas, más -X bornera y -W cable de campo), CONDUCTORES (barras, conductor interno, cable, barra PE, PE, punto de conexión, borne, número de conductor y los colores reales según AEA 90364-5 Tabla 55.1: L1 marrón, L2 negro, L3 rojo, N celeste, PE verde-amarillo), BALANCE DE FASES y NOTAS (TN-S, PE, corte bipolar/tetrapolar, bornes IEC 60445, esquema de numeración, ubicación, S/E IRAM 4524).
- **Referencias entre hojas**: si una línea sigue en otra hoja, termina en flecha con hoja/coordenada de destino (`2/G4`) y en la otra hoja arranca con la de origen. Si hay mando, va en una hoja aparte o a la derecha, como escalera entre L y N, con el espejo de contactos bajo cada bobina.
- **Medición por TI** (cuando el tablero lleva medidor): un TI por fase (círculo sobre L1, L2, L3) con P1-P2 en el primario y S1-S2 en el secundario, puente de cortocircuito en la bornera, y tomas de tensión por MCB 2 A por fase, con línea de trazos `3 1` al AR o multimedidor.
- **Colores y estilo**: rojo `#ff0000` conexiones por cable, azul `#0000ff` barras y aparamenta, verde `#139b48` PE/tierra, negro textos fijos y datos de los slots (sin negrita); destino de cada salida en azul. Negrita solo en las siglas de los equipos. Conductores 0.25, barras 0.5. Fuente osifont / ISOCPEUR / DejaVu Sans; texto 3.47 (h 2,5), títulos 4.86 (h 3,5), nunca menos de 2.5.
- Recintos de tablero con línea de trazos gris `#dcdcdc` (`3 1`, trazo 0.25) y su título en rojo (TGBT # 01, INTERFAZ...), igual que el SLD.
- Ningún texto debe tapar símbolos, motores ni conductores (revisar ACOPLAMIENTO y similares). Nada fuera de la zona útil ni encima del rótulo.

## Verificación final
- Mismo nº de equipos, valores (A, kA, tipo) y destinos que el SLD.
- Nº de polos de cada equipo coincide con las marcas del SLD.
- Paso entre polos 12,5 mm en todo el plano; etiquetas de polo fuera de las líneas.
- Cada conductor llega a la barra de su fase con punto; sin conductores flotantes.
- Grosores solo 0.25 / 0.5; dashes IRAM; letras >= h 1,8.
- Cada salida tiene su bornera -X con borne PE; cada conductor interno tiene su número y ninguno se repite; los números de borne de los símbolos se leen y no los tapa nada.
- El PE no pasa por ningún polo ni toroide; ningún monofásico comparte neutro.
- Si el origen es Excel: Ib calculado desde CARGA+UNIDAD_CARGA, In/Icu/sección dimensionados por la norma, topology aplicada.
