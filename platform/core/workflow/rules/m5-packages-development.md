# Módulo M5 — Puerta de preparación y desarrollo por paquetes

> Módulo de `CLAUDE.md` (secciones 8.3). Tiene la **misma autoridad** que `CLAUDE.md`: el texto se movió aquí, sin cambios de fondo, para que `CLAUDE.md` se lea corto en cada sesión. La numeración de las secciones se conserva, de modo que las referencias «`CLAUDE.md`, 8.1» y similares siguen valiendo. Se lee **a demanda**, cuando `CLAUDE.md` (sección 3.1) lo indica.

---

### 8.3 Puerta de preparación y desarrollo progresivo por paquetes

**Principio de secuencia.** El trabajo es **secuencial entre entrega y revisión**: Claude no entrega veinte documentos para que el usuario revise veinte documentos. Desarrolla **un paquete de revisión** (`PQ-nn`: un documento o un grupo pequeño, normalmente de 1 a 3, que van de la mano), lo entrega, se detiene y espera el OK o los comentarios del usuario; recién entonces sigue. No se redacta un pliego sin haber dimensionado antes el cable: el orden lo fija el grafo de dependencias de la LME (`deliverables.md`, 4.1).

Antes de generar **cualquier** documento Claude:

1. Identifica el entregable en la LME y su **paquete** (`PQ-nn`); si no existe, lo registra con su paquete o consulta al usuario.
2. Revisa los archivos de la lista de la sección 7 de este documento.
3. **Puerta de dependencias:** verifica que todos los paquetes de la columna *Depende de* de su paquete estén `REVIEWED`. Si alguno no lo está, **no desarrolla**: informa qué paquete falta y propone desarrollarlo antes. Un documento no se desarrolla antes que aquellos de los que depende, salvo `[DEFINIR]` justificado y registrado en una `DEC`.
4. Verifica la **matriz de preparación** de `deliverables.md` (sección 9): todos los parámetros marcados *críticos* para ese tipo de documento deben estar confirmados en la línea base. En un **pliego** se evalúa **capítulo por capítulo** (`TECHNICAL_SPECIFICATIONS_GUIDE.md`, 4.7): se desarrollan los paquetes de pliego cuya puerta se cumple y los demás quedan `BLOCKED`.
5. Si falta cualquier parámetro crítico: **no redacta ni asume**. Presenta al usuario el **formulario de la puerta** (uno solo para el paquete) y el usuario elige una opción por fila con la frase fija `opción A [ENT-nnn]`, `opción B [ENT-nnn]` u `opción C [ENT-nnn]` (una por documento):

   | Documento (`ENT-nnn`) | Parámetro crítico faltante | Opción A: esperar `INF-nnn` | Opción B: autorizar `SUP-nnn` (con base del valor y marca `[VERIFICAR]`) | Opción C: `BLOCKED` (`BLQ-nnn`) |
   |---|---|---|---|---|

   - **A:** se abre la `INF-nnn` (con responsable y fecha) y el documento queda `BLOCKED` hasta recibir el dato.
   - **B:** se registra el `SUP-nnn` con su base del valor y una **decisión de autorización** (`DEC-nnn`: quién autoriza, para qué documento y fecha); el documento queda marcado con la dependencia `[SUPUESTO SUP-nnn]`. La opción B solo existe para parámetros **autorizables**.
   - **C:** el documento queda `BLOCKED` con su `BLQ-nnn`. Como los paquetes son chicos, **el paquete completo queda `BLOCKED`** (salvo que el usuario decida dividirlo en el plan) y Claude propone el siguiente paquete independiente cuya puerta se cumpla; esto no impide el resto del plan.
   - **«No sé / pendiente»** se trata como `opción A`: queda una `INF-nnn` con responsable y fecha, y Claude propone el siguiente paso (A, B o C).
   - **Críticos no autorizables** (nunca opción B; si el usuario no los tiene, solo A o C): en eléctrica, los **niveles de cortocircuito y el poder de corte (Icc)**, el **régimen de neutro** y las **tensiones de servicio**. Para otras disciplinas, Claude propone la lista no autorizable al usarla por primera vez (`deliverables.md`, sección 9) y se registra en una `DEC`.
   - Los parámetros no críticos pueden quedar `[DEFINIR]` con `INF-nnn`.
6. Redacta el documento manteniendo coherencia con el alcance, los requisitos del cliente, las decisiones, los estándares de ingeniería y los entregables requeridos.
7. **Paquete y cierre.** El *paquete* es lo que Claude desarrolla entre dos entradas a `FOR_REVIEW`: **un** paquete de la LME. Por defecto es el siguiente según el grafo, con sus dependencias `REVIEWED` y sin `BLOCKED`; `desarrollar paquete PQ-nn` indica otro. **Máximo por defecto: un paquete por vez.** Dos paquetes independientes entre sí pueden proponerse juntos solo si el usuario lo autoriza de forma explícita (`desarrollar paquetes [PQ-nn] y [PQ-nn]`) y se registra en una `DEC`. Cada documento pasa el **autocontrol de cierre documental** al terminarse y el **paquete completo** lo pasa una vez más (incluido el verificador y, en una síntesis de cálculo, el contraste de cada valor con su memoria). Al terminar, los documentos y el proyecto pasan a **`FOR_REVIEW` (PARA REVISAR)** y Claude entrega la **hoja de revisión del paquete** (ver 11.1), con solo ese paquete. Claude **se detiene**: no avanza más allá de `FOR_REVIEW`, no empieza el paquete siguiente ni «en paralelo», y solo propone el siguiente cuando el actual quedó `REVIEWED`.
   **Lista fija de autocontrol de cierre documental** (se ejecuta con `python3 .claude/library/calculations/document_verifier.py <carpeta_del_proyecto>`, desde la raíz de la copia de la plantilla; los puntos 1 a 5 y 10 son mecánicos y se comprueban con el verificador, los demás son manuales). Es la **auto-verificación ligera por paquete**; la auditoría formal se ejecuta una sola vez por entrega (`project-audit.md`):

   1. La revisión de la portada coincide con la del nombre de archivo y con la de la LME (revisión **interna** `00.R.C.FF`: `00.0`, `00.0.c`, `00.n` o `00.n.c`; en el editable nunca figura `Rev 00` a secas, que es el rótulo del cliente).
   2. Cada referencia cruzada apunta a un código existente en la LME y cumple la regla de `DOCUMENT_RULES.md`, RG-11 y sección 9 («revisión vigente» en los documentos de trabajo; revisión exacta, `Rev 00`, en las copias que se entregan).
   3. Los valores de `project-information.md` citados coinciden; no quedan valores de revisiones anteriores.
   4. Toda marca abierta (`[DEFINIR]`, `[VERIFICAR]`, `[PENDIENTE INF-nnn]`, `[SUPUESTO SUP-nnn]`) figura en la sección *Pendientes y supuestos* del documento y está justificada.
   5. Todos los IDs citados (`DEC`, `SUP`, `INF`, `REQ`, `ENT`, `ENG`, `NOR`) existen en su registro, y el documento no escribe el estado de una `DEC` o `SUP`.
   6. Control de revisiones completo, con descripción específica, el `REV-nnn` de cada comentario incorporado (último dígito) y la `rfc-00n` en cada revisión `00.n`, y la revisión con su sufijo de fase.
   7. Se cumple el checklist de `DOCUMENT_RULES.md`, sección 12.
   8. `traceability-matrix.md`, `deliverables.md` y `project-status.md` quedaron actualizados.
   8b. Los archivos del paquete están en `02-engineering` con nombres `<código>_Rev…` y, si hay planos, el usuario entregó DWG + xref + PDF (Claude revisa solo el PDF). Recién entonces `send-to-review.py PQ-nn`.
   9. **Paquete:** los paquetes de los que depende están `REVIEWED`; los documentos del paquete son coherentes entre sí; y una síntesis de cálculo (`SM`) no contiene ningún valor, hipótesis ni conclusión que no figure en su memoria.
   10. **Formato Markdown/Pandoc (`DOCUMENT_RULES.md`, RG-20):** títulos sin numeración manual (`# Alcance`, nunca `# 1. Alcance`), un solo `#` por archivo y sin saltos de nivel, viñetas con `-` (ninguna con `*` ni `+`), referencias por nombre y no por número, lista precedida de una línea en blanco y bloque YAML de portada. El verificador marca como ERROR los títulos numerados y las viñetas `*` o `+`, y como AVISO el resto.

   **Pliegos.** Además de la lista anterior, un pliego pasa el **autocontrol del pliego** (`TECHNICAL_SPECIFICATIONS_GUIDE.md`, 4.8) y `python3 -B .claude/library/calculations/specification_verifier.py 02-engineering/TECHNICAL_SPECS` (CAL-011) sin errores. Es una ayuda heurística: no reemplaza el juicio del redactor ni la auditoría (`project-audit.md`, A4-13).

8. Al cerrar el paquete (`revisión aprobada`) actualiza `traceability-matrix.md`, `deliverables.md` (estado `REVIEWED`, columna *Revisó*) y `project-status.md` (paquete actual, conteo de paquetes y próximo paquete propuesto), y propone el paquete siguiente; no actualiza ni cambia de revisión paquetes ajenos salvo lo previsto para el cambio aguas arriba (11.1).

**Ingeniería progresiva (orden de dependencia).** Esta tabla es la **base con la que Claude arma el grafo de paquetes** al proponer el plan (8.1, Fase 4); el grafo definitivo vive en las columnas *Paquete* y *Depende de* de la LME. Se desarrolla siguiendo el grafo; un documento no se desarrolla antes que aquellos de los que depende, salvo `[DEFINIR]` justificado y registrado en una `DEC`:

| Etapa | Documentos | Requieren |
|---|---|---|
| 1 | Criterios de diseño (`CR`) | Línea base |
| 2 | Cálculos (cada memoria con su síntesis en el mismo paquete), en este orden: balance de cargas → cortocircuito y caída de tensión → conductores y protecciones → iluminación (el cálculo luminotécnico solo requiere la etapa 1 y la geometría; la alimentación de sus circuitos requiere las etapas anteriores) | Etapa 1; datos de cargas |
| 3 | Diagramas unifilares (`DG`) | Etapa 2 (potencias, secciones, protecciones) |
| 4 | Insumos de dibujo de los planos (estado `CAD_INPUT`) | Etapas 2 y 3 |
| 5 | Memorias descriptivas (`MD`) | Etapas 2 y 3 (las potencias salen del cálculo de cargas) |
| 6 | Especificaciones técnicas (`ET`) y pliegos (`PG`, un paquete por capítulo o grupo de capítulos) | Etapas 2 y 3 (pliego: línea base y etapa 1; los capítulos que citan potencias, secciones o niveles de falla requieren los paquetes de cálculo de la etapa 2 `REVIEWED`; el capítulo de responsabilidades es el último) |
| 7 | Listados (`LC`, `LE`, `LM`, `LI`) | Unifilares (etapa 3) e insumos de planos entregados (etapa 4) |
| 8 | Planos DWG | Los dibuja el usuario con los insumos de la etapa 4; no los genera Claude |
| 9 | Protocolos de ensayo | Especificaciones y criterios de aceptación |
