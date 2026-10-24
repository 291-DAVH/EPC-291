# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el proyecto usa [Versionado Semántico](https://semver.org/lang/es/).

## [0.4.17] - 2026-10-24
- Packaging: one copy of the shared logo and of the multi-line symbol library (duplicates removed; the library of the generator is the only one).

## [0.4.16] - 2026-10-22

- Nuevos símbolos MCCB sin extracción (basic y motorized) en SLD (`mccb_basic`, `mccb_motorized`) y MLD 1p–4p (`mccb_basic_Np`, `mccb_motorized_Np`), generados a partir de sus versiones drawout quitando las flechas de extracción. En la versión motorizada, el puerto inferior se ubica al final del conductor.
- Catálogo: referencias de archivo corregidas para las 10 entradas MCCB; ya no quedan entradas sin SVG.

## [0.4.15] - 2026-10-22

- Catalogos JSON ordenados alfabéticamente por id, uno por biblioteca (sld-lv, sld-mv, mld-lv, mld-mv).
- Un único `catalogo_simbolos.xlsx` en `src/`; eliminados los duplicados.
- Catálogos: 42 entradas nuevas (32 MLD y 10 SLD) para las variantes ACB/MCCB con drawout, LSIG y motorizado, y `lv_cable_run`, que faltaba.
- Catálogos: `viewBox` y `size` sincronizados con los SVG (`size` = dimensiones en mm del SVG).
- Catálogos: puertos del SLD sincronizados con los SVG (15 corregidos).

## [0.4.14] - 2026-10-22

- Paso entre polos MLD = 10 mm (antes 12.5 mm): ejes de polo en x = 0, 10, 20, 30.
- Celdas ACB/MCCB de 10 mm contiguas en todas las variantes.
- Cajas anchas (ATS, VFD, UPS, motor, generador, etc.) = 10 mm por polo.
- Puertos, etiquetas, viewBox y DXF actualizados en los 72 archivos multipolo.

## [0.4.13] - 2026-10-22

- Geometría real unificada en SVG/DXF MLD: celdas de protección ACB/MCCB de 10 mm de ancho en 1p/2p/3p/4p, en todas las variantes (drawout, LSIG, motorizado).
- Relé térmico a 4.9 mm por polo.
- Decoración (drawout, motor) y viewBox alineados igual en todos los polos.
- DXF y catálogos regenerados.

## [0.4.12] - 2026-10-22

- Catálogo Excel con escala uniforme (4 px por mm) para todos los símbolos. Antes cada imagen se ajustaba a una caja fija y los símbolos más grandes se veían más chicos.
- Las celdas MV de gabinete (290 mm de alto) se reducen para entrar en la fila.

## [0.4.11]

- MLD actualizados según los cambios SLD:
  - Contactor (contacto NA con arco), interruptor-seccionador (barra y círculo) y fusible (rectángulo sobre la línea) por polo, con enlace mecánico punteado.
  - Generador y motor con círculo de 10 mm.
  - Bornes inferiores a 15 mm.
- Eliminados rótulos de tipo duplicados en 18 MLD.

## [0.4.10]

- Encuadre de textos en SLD y MLD: textos internos (A, V, W, M, G, 3~, I>, I>>, I>>>, I/Δ, kWh, VFD, ATS, etc.) centrados en su celda, círculo o caja.
- Etiqueta de tipo (ACB, MCCB...) en Arial, como el resto.
- Corregidos MLD ACB LSIG (glifos duplicados o faltantes) y MLD ACB LSIG motorizado (flecha y puerto inferior ahora debajo de la pila de celdas).
- Números de borne de los drawout separados de las flechas.
- En ACB/MCCB solo se movieron textos, no la geometría editada a mano.

## [0.4.9]

- Normalización de proporciones SLD (LV y MV) a la grilla de 2,5 mm:
  - Círculos a diámetro 10 mm (medidores, motores, generadores, lámparas, TC, TV, toroidal).
  - Cargas y cajas a 10 mm; alturas y anchos de reactores, relés, variador, UPS, arrancador suave, inversor, cargador EV, banco de capacitores, FV, etc. a múltiplos de 2,5 mm.
- Voltímetro rehecho (estaba roto).
- ACB/MCCB no se tocaron. MLD pendiente.

## [0.4.8]

- Símbolos SLD redibujados según IEC 60617 (`assets/IEC_60617_Simbologia.pdf`): contacto NA/NC, pulsadores NA/NC, contactor (arco), seccionador-fusible, interruptor-seccionador, seccionador (LV y MV), fusible (rectángulo), tomacorriente.
- Pendiente de alinear: TC, rectificador, parada de emergencia, relé térmico, SPD, reactancia, MCB/RCBO.
- ACB y MCCB editados a mano no se tocaron.

## [0.4.7]

- Revisión de símbolos SLD (LV y MV):
  - Eliminados rótulos de tipo duplicados y superpuestos.
  - Rótulos mal derivados corregidos (CABLE IN/OUT, PE BAR, 3PH, TERM).
  - Parámetros IEC agregados a los que faltaban (contactos, pulsadores, tierra, load box, conmutador, marcador trifásico, flechas de cable, medidores, selector, VPIS, seccionador de tierra, descargador).
  - Diámetros normalizados (ct LV, vt LV, ct_toroidal MV, transformer_2w MV).
- ACB y MCCB editados a mano no se tocaron.

## [0.4.6]

- Matriz ACB completa en SLD y MLD: `acb`, `acb_lsig`, `acb_motorized`, `acb_lsig_motorized`, `acb_drawout`, `acb_lsig_drawout`, `acb_motorized_drawout`, `acb_lsig_motorized_drawout`.
- Nombre de drawout por geometría (flechas arriba y abajo).
- Bloque LSIG con etiquetas I>, I>>, I>>> y marcadores.
- Motorizado drawout con flecha inferior bajo el bloque de protección.
- Catálogo Excel con imagen → SVG y nombre → DXF.

## [0.4.5]

- ACB y MCCB drawout/motorizado ajustados a mano, con DXF regenerados.
- Nuevo símbolo `mccb_lsig_drawout` (MCCB con funciones LSIG).

## [0.4.4]

- Drawout = flechas arriba y abajo (SLD y MLD).
- `acb_motorized` con flechas (drawout) y versión sin flechas.
- Parámetros IEC 60617 por familia (capacidad, In, disparo, sensibilidad, relación, potencia, etc.) a la izquierda del símbolo.

## [0.4.3]

- Todas las etiquetas (TAG, tipo de equipo, parámetros y MANUFACTURER) a la izquierda del símbolo, una debajo de otra.
- Drawout = equipo con flechas arriba y abajo (`acb_drawout`, `mccb_drawout`).

## [0.4.2]

- Todos los símbolos tienen TAG y MANUFACTURER (SVG y DXF).
- El atributo `cable_tag` pasa a ser TAG.
- El texto CONTACTOR pasa a KM.

## [0.4.1]

- Orden de etiquetas: TAG arriba, tipo de equipo debajo, MANUFACTURER al final.
- Equipos extraíbles con sufijo `_drawout` en el nombre.

## [0.4.0]

- TAG como primer atributo de cada símbolo (2,5 mm, azul).
- Resto de textos a 1,7 mm; textos fijos en azul TRUECOLOR; atributos en negro (ACI 7).
- SVG y DXF actualizados y catálogo regenerado.

## [0.3.0]

- Símbolo `lv_cable_run` (tramo de cable con identificación).
- Catálogo en Excel.

## [0.2.0]

- Salida DXF por bloques para todos los símbolos.

## [0.1.0]

- Biblioteca inicial en SVG.
