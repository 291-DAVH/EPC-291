# deliverables.md — Catálogo y Lista Maestra de Entregables

| Campo | Valor |
|---|---|
| Versión | 1.2 |
| Fecha | 2026-10-07 |
| Responsable | Document Controller |

---

# GUÍA DEL ARCHIVO (no editar)

## 1. Objetivo

Definir qué entregables componen un proyecto de ingeniería industrial multidisciplina (catálogo típico) y mantener la **Lista Maestra de Entregables (LME)** del proyecto: la única fuente de códigos, revisiones, estados y aplicabilidad de cada documento, plano y listado, y de su **agrupación en paquetes de revisión** (`PQ-nn`) y del orden de ejecución por dependencias entre ellos (4.1).

## 2. Alcance

Cubre nueve categorías: Documentación, Diagramas, Planos, Cálculos, Listados, Licitación, Construcción, COMMISSIONING y As-Built. El catálogo es **genérico**; para cada proyecto se selecciona lo que aplica y se completa la LME.

## 3. Forma de utilización

1. En `planning`, recorrer el catálogo (sección 7) y decidir qué aplica. Las filas del catálogo que se vuelcan a la LME llevan `Aplica = SÍ`; **las filas no volcadas a la LME se consideran `NO` por alcance**, y se justifican con **una decisión (`DEC-nnn`) por categoría y fase** (por ejemplo «las categorías 7.6 a 7.9 quedan fuera del alcance de ingeniería de detalle»), no una decisión por fila. Todo `NO` dentro de una categoría que sí aplica requiere su propio motivo y decisión.
2. Volcar los entregables aplicables a la **LME** (sección 8) con un ID `ENT-nnn`, código de documento (según `DOCUMENT_RULES.md`), título, fase y requisitos que cubre.
3. Actualizar estado y revisión **interna** en la LME **cada vez** que se entrega o cambia un documento (los borradores anteriores a `REVIEWED` no cambian la revisión; desde `REVIEWED`, cada rfc aprobada genera la `Rev 00.n` de los documentos afectados). El estado de los planos y diagramas dibujados por el usuario **no se registra aquí**: vive en `drawing-status.md`.
4. Al auditar, la LME se compara con las carpetas reales y con `traceability-matrix.md`.
5. Un documento que no está en la LME **no existe oficialmente**: se agrega o se elimina.
6. Antes de desarrollar un documento se supera la **matriz de preparación** (sección 9): los parámetros críticos deben estar confirmados **y** los paquetes de los que depende su paquete deben estar `REVIEWED`. Para el pliego (`PG`) la matriz se evalúa **capítulo por capítulo** (`TECHNICAL_SPECIFICATIONS_GUIDE.md`, 4.7), y cada capítulo (o grupo de capítulos que van de la mano) es un paquete con sus dependencias.
7. Al armar la LME, agrupar los entregables en **paquetes de revisión** (4.1), completar las columnas *Paquete* y *Depende de* y presentar al usuario el **plan de paquetes** (una tabla resumida) para su confirmación; queda registrado como `DEC-nnn`. Claude desarrolla y entrega **un paquete por vez**, en el orden del grafo.

## 4. Estructura recomendada

| Fase (código) | Significado |
|---|---|
| `IC` | Ingeniería Conceptual |
| `LIC` | Licitación |
| `IB` | Ingeniería Básica |
| `ID` | Ingeniería de Detalle |
| `IE` | Ingeniería Ejecutiva |
| `CON` | Construcción |
| `PRE` | Pre-COMMISSIONING |
| `COM` | COMMISSIONING |
| `ASB` | As-Built y cierre |

El catálogo cubre las disciplinas eléctrica (7.1 a 7.9) y las demás (7.10). Cada categoría presenta: tipo de entregable, código de tipo (ver `DOCUMENT_RULES.md`, sección 8.2), fases habituales y observaciones.

### 4.1 Paquete de revisión (`PQ-nn`)

El **paquete de revisión** es la unidad mínima de trabajo y de revisión: **un documento o un grupo pequeño (normalmente de 1 a 3) de documentos que van de la mano**, es decir, que se leen, se verifican y se aprueban juntos. El usuario nunca recibe veinte documentos a la vez: recibe un paquete, lo verifica, responde (OK o comentarios) y recién entonces se sigue con el siguiente.

| Regla | Contenido |
|---|---|
| Identificación | `PQ-nn` (dos dígitos, correlativo, sin reutilización). Un documento pertenece a **un solo** paquete. Cada paquete lleva un nombre corto. |
| Dónde se declara | En la LME (sección 8): columnas *Paquete* (`PQ-nn`) y *Depende de* (los `PQ` que deben estar `REVIEWED` antes de empezar este). Todas las filas de un mismo paquete llevan el mismo valor en *Depende de*. |
| Excepción del pliego | El pliego (`PG`) es **un** documento con una sola fila en la LME, pero se desarrolla y se revisa por capítulos. Su fila lleva en *Paquete* y *Depende de* el texto «varios: ver Plan de paquetes», y el Plan de paquetes tiene **una fila por paquete de pliego** (capítulo o grupo de capítulos, p. ej. `ENT-045 cap. 01-02`) con sus dependencias (`TECHNICAL_SPECIFICATIONS_GUIDE.md`, 4.10). El estado de la fila del pliego es el del paquete menos avanzado. |
| Tamaño | De 1 a 3 documentos. Un documento extenso es un paquete de uno (un capítulo de pliego, un cálculo largo). Más de 3 solo con motivo escrito en el plan, porque cada documento adicional encarece la revisión. |
| Qué va junto | Lo que no tiene sentido revisar por separado: una memoria de cálculo y su síntesis (`SM`, siempre en el mismo paquete que su memoria); un unifilar y su lista de cargas, si se derivan uno del otro; un capítulo de pliego y su anexo. |
| Dependencias | Un paquete depende de otro cuando usa un resultado, un dato o una decisión que el otro produce (los cálculos de cables dependen del balance de cargas; el capítulo de requisitos de diseño del pliego depende de los cálculos que cita). El grafo es **acíclico** y define el orden de ejecución. |
| Puerta | Un paquete **no empieza** hasta que todos los paquetes de los que depende están `REVIEWED` (OK del usuario) y, además, se cumple la matriz de preparación (sección 9). Esto forma parte de la puerta de preparación (`CLAUDE.md`, 8.3). |
| Ritmo | Claude desarrolla **un paquete por vez**, hace su autocontrol (incluido el verificador), entrega una hoja de revisión que contiene solo ese paquete y **se detiene**. Propone el siguiente solo cuando el actual está `REVIEWED`. Dos paquetes independientes entre sí pueden proponerse juntos solo si el usuario lo autoriza de forma explícita (`desarrollar paquetes [PQ-nn] y [PQ-nn]`), y esa autorización se registra como `DEC-nnn`. |
| Cambio aguas arriba | Si un paquete `REVIEWED` cambia (siempre por rfc), los paquetes dependientes ya `REVIEWED` que usan el dato modificado vuelven a `FOR_REVIEW` mediante una hoja corta de impacto (`review-sheet.md`, sección 7) y pasan a `Rev 00.n` con la misma rfc. Los que solo citan al documento modificado no cambian. |
| Estado del paquete | Es el de sus documentos (`DOCUMENT_RULES.md`, sección 9): `PLANNED`, `DRAFT`, `FOR_REVIEW`, `INTERNAL_REVIEW`, `REVIEWED`, y después `FOR_AUDIT` y `AUDITED`; más `BLOCKED` (con su `BLQ-nnn`) y `REABIERTO` (paquete `REVIEWED` cuya reapertura por un cambio aguas arriba está pendiente de hoja). |

## 5. Ejemplos de uso

- Para una ampliación industrial con ingeniería de detalle: se marcan como aplicables memoria descriptiva, criterios de diseño, unifilares, planos de implantación, cálculos de cortocircuito y cables, listas de cables y equipos, especificaciones de tableros y transformador. Se marca `NO` el apartado de pararrayos con la decisión `EJ-DEC-007` (instalación existente sin modificación).
- En la LME: `EJ-ENT-014 | ACM01-E-MC-002 | Memoria de cálculo de cortocircuito | Cálculos | IB | Rev 00.0 | ifa | EJ-REQ-ING-004`. Cada comentario incorporado suma 1 al último dígito (`00.0.1`, `00.0.2`…); si la `EJ-rfc-002` la modifica, la columna *Rev. interna* pasa a `00.2` y la entrega siguiente registra `Rev 00` (rótulo al cliente) con su `TR-nnn`.
- Paquetes (ilustrativo, IDs `EJ-`): `EJ-PQ-02` = balance de cargas (memoria + síntesis); `EJ-PQ-03` = **memoria de cálculo del dimensionamiento de cables eléctricos de baja tensión + síntesis de cálculo del mismo dimensionamiento**, que depende de `EJ-PQ-02`; el capítulo 05 «Requisitos de Diseño» del pliego es `EJ-PQ-10` y depende de `EJ-PQ-03`. Claude entrega `EJ-PQ-03` con una hoja que contiene solo esos dos documentos y se detiene; solo después de que el usuario lo deja `REVIEWED` se puede proponer `EJ-PQ-04` y, mucho más adelante, redactar el capítulo del pliego: **no se redacta un pliego sin haber dimensionado antes el cable**.

## 6. Buenas prácticas

- Registrar la LME desde el inicio; es más barato que reconstruirla al final.
- Un entregable = un propósito = un código.
- Planificar con fechas realistas considerando revisión interna y auditoría antes de cada entrega.
- Verificar los entregables exigidos por el cliente y el contrato antes de cerrar el listado.
- No marcar `NO APLICA` por conveniencia: es un hallazgo de auditoría si no está justificado.

---

# CATÁLOGO DE ENTREGABLES TÍPICOS

## 7.1 Documentación

| Entregable | Tipo | Fases | Observaciones |
|---|---|---|---|
| Memoria descriptiva general | `MD` | IB, ID | Describe la solución; no repite especificaciones |
| Memorias descriptivas por sistema (MT, BT, PAT, alumbrado, control) | `MD` | ID | |
| Criterios de diseño | `CR` | IB | Referencia a `engineering-standards.md` |
| Especificaciones técnicas de equipos y materiales (transformadores, celdas, tableros, cables, bandejas) | `ET` | ID, LIC | Lenguaje contractual |
| Especificaciones de montaje y construcción | `ET` | ID | |
| Alcance de trabajos y suministros | `AL` | LIC, ID | |
| Pliego técnico (documentación licitatoria) | `PG` | LIC, ID | Un único documento con un código y una revisión; se redacta por capítulos numerados (`02-engineering/TECHNICAL_SPECS`) y se entrega consolidado; sin precios ni condiciones comerciales. Cada capítulo (o grupo de capítulos que van de la mano) es un paquete de revisión que depende de los paquetes técnicos que cita y nunca se redacta antes que ellos. Ver `TECHNICAL_SPECIFICATIONS_GUIDE.md` |
| Matriz de responsabilidades | `AL` | LIC, CON | |
| Plan de calidad | `PC` | ID, CON | |
| Plan de capacitación | `PC` | COM | Transferencia de conocimiento |
| Informe de relevamiento de instalaciones existentes | `IN` | IB | |
| Informe de estudio de resistividad del terreno | `IN` | IB, ID | |
| Hojas de datos de equipos | `HD` | ID | |

## 7.2 Diagramas

| Entregable | Tipo | Fases | Observaciones |
|---|---|---|---|
| Diagrama unifilar general (MT / BT) | `DG` | IB, ID | Base de coherencia de cálculos y listados |
| Diagramas unifilares de tableros | `DG` | ID | |
| Diagramas funcionales y esquemas de control | `DG` | ID | |
| Diagramas de conexionado y borneras | `DG` | ID | |
| Diagramas de lazo de instrumentación | `DG` | ID | |
| Arquitectura de control y comunicaciones | `DG` | IB, ID | |
| Esquema de protecciones y enclavamientos | `DG` | ID | |

## 7.3 Planos

> Los diagramas `DG` que se dibujan en CAD (por ejemplo el unifilar) siguen el mismo flujo `CAD_INPUT` / `DRAWN` que los planos.
>
> **Los planos DWG los elabora el usuario personalmente. Claude no genera DWG ni puede conocer su estado.** Por cada plano de la LME Claude entrega los **insumos de dibujo** (lista de elementos con cantidades y ubicaciones o criterios de ubicación, capas y bloques según `CAD_standards.md`, notas, leyendas, cuadros, referencias a cálculos y listados, y datos pendientes) y propone su fila en `drawing-status.md` (`CAD_INPUT`). **El estado del plano (`PLANNED`, `CAD_INPUT`, `DRAWN`, `REVIEWED`, `ENTREGADO`) lo anota el usuario a mano en `drawing-status.md`, que es la fuente única: la LME no repite el estado de cada plano** (su columna *Estado* muestra el del documento de insumos). Ver `CAD_standards.md`, sección 3.1.

| Entregable | Tipo | Fases | Observaciones |
|---|---|---|---|
| Implantación general de áreas eléctricas | `PL` | IB, ID | |
| Plantas y cortes de salas eléctricas | `PL` | IB, ID | |
| Canalizaciones y bandejas (recorridos y cortes) | `PL` | ID | |
| Puesta a tierra y pararrayos | `PL` | ID | |
| Alumbrado y fuerza | `PL` | ID | |
| Disposición y vistas de tableros | `PL` | ID | |
| Detalles típicos de montaje | `PL` | ID | |
| Planos de obra civil asociada (soportes, zanjas, bases) – interfaz | `PL` | ID | Con disciplinas C / S |
| Planos de taller y de obra (cuando corresponde) | `PL` | CON | |

## 7.4 Cálculos

| Entregable | Tipo | Fases | Observaciones |
|---|---|---|---|
| Balance de cargas y demanda | `MC` | IB | |
| Cortocircuito | `MC` | IB, ID | |
| Flujo de carga y caída de tensión | `MC` | IB, ID | |
| Dimensionamiento de conductores | `MC` | ID | |
| Coordinación de protecciones y planilla de ajustes | `MC` | ID | |
| Malla de puesta a tierra | `MC` | ID | |
| Evaluación de riesgo de descargas atmosféricas | `MC` | ID | |
| Iluminación | `MC` | ID | |
| Energía incidente de arco | `MC` | ID | Si el alcance lo incluye |
| Carga de bandejas y soportes | `MC` | ID | |
| Dimensionamiento de transformadores y ventilación de recintos | `MC` | ID | |
| Baterías, rectificadores y UPS | `MC` | ID | |
| Síntesis de cada memoria de cálculo anterior | `SM` | Misma fase que su memoria | Documento corto con resultados, hipótesis y conclusiones de **una** memoria `MC` para lectura rápida, sin repetir procedimientos; no contiene valores que no estén en la memoria; va siempre en el mismo paquete que su memoria (4.1; `DOCUMENT_RULES.md`, 6.14) |

## 7.5 Listados

| Entregable | Tipo | Fases | Observaciones |
|---|---|---|---|
| Lista de cables | `LC` | ID, ASB | Coherente con unifilares y planos |
| Lista de equipos | `LE` | IB, ID, ASB | |
| Lista de cargas | `LE` | IB, ID | |
| Lista de materiales y cómputo | `LM` | LIC, ID | |
| Lista de instrumentos y señales (I/O) | `LI` | ID | |
| Matriz de enclavamientos | `LI` | ID, COM | |
| Planilla de ajustes de protección | `LI` | ID, COM, ASB | |
| Lista de planos y documentos | `RG` | Todas | Equivale a la LME |
| Lista de repuestos recomendados | `LM` | ID, ASB | |

## 7.6 Licitación

| Entregable | Tipo | Fases | Observaciones |
|---|---|---|---|
| Memoria técnica de oferta | `MD` | LIC | |
| Alcance y exclusiones de la oferta | `AL` | LIC | |
| Matriz de cumplimiento técnico y desvíos | `RG` | LIC | Requisito por requisito |
| Cómputos y estimación de cantidades | `LM` | LIC | |
| Cronograma y plan de ejecución | `PC` | LIC | |
| Listado de aclaraciones y supuestos de oferta | `RG` | LIC | Consistente con `assumptions-and-decisions.md` |
| Hojas de datos de equipos propuestos | `HD` | LIC | |
| Evaluación técnica de ofertas de proveedores | `IN` | LIC, ID | |
| Plan de seguridad y salud preliminar | `PC` | LIC | |

## 7.7 Construcción

| Entregable | Tipo | Fases | Observaciones |
|---|---|---|---|
| Planos y documentos ifc (entrega vigente) | `PL` / varios | CON | |
| Procedimientos de montaje y tendido | `PR` | CON | |
| Plan de inspección y ensayos (ITP) | `PC` | CON | |
| Plan de seguridad y salud | `PC` | CON | |
| Cronograma de obra y avances | `PC` | CON | |
| Consultas técnicas (rfi) y respuestas | `CT` | CON | |
| Registro de inspecciones | `RG` | CON | |
| Registro de cambios y marcas de obra (redlines) | `RG` | CON | Base del as-built |
| Dossier de materiales y certificados | `RG` | CON | |
| Informe de tendido y conexionado de cables | `IN` | CON | |
| Plan de cortes y conexiones sobre instalaciones existentes | `PR` | CON | |

## 7.8 COMMISSIONING

| Entregable | Tipo | Fases | Observaciones |
|---|---|---|---|
| Plan de pre-commissioning y commissioning | `PC` | PRE, COM | |
| Procedimientos de ensayo | `PR` | PRE, COM | |
| Listas de verificación de completitud mecánica | `RG` | PRE | |
| Protocolos de aislación y continuidad | `PT` | PRE | |
| Protocolos de protecciones (inyección secundaria) | `PT` | PRE | |
| Protocolos de transformadores, celdas y tableros | `PT` | PRE | |
| Protocolo de puesta a tierra (medición) | `PT` | PRE | |
| Procedimiento de energización | `PR` | COM | |
| Protocolos de pruebas funcionales y con carga | `PT` | COM | |
| Lista de pendientes (punch list) | `RG` | PRE, COM | Con categoría y cierre |
| Actas de energización y puesta en servicio | `RG` | COM | |
| Informe de commissioning | `IN` | COM | |
| Registros de capacitación | `RG` | COM | |

## 7.9 As-Built

| Entregable | Tipo | Fases | Observaciones |
|---|---|---|---|
| Planos as-built | `PL` | ASB | Rev 01 (as-built, todo el proyecto); cambios posteriores Rev 02, 03… por rfc |
| Unifilares y esquemas as-built | `DG` | ASB | |
| Listados as-built (cables, equipos, señales) | `LC` / `LE` / `LI` | ASB | |
| Planilla de ajustes de protección final | `LI` | ASB | Ajustes en servicio |
| Memorias y especificaciones actualizadas | `MD` / `ET` | ASB | Solo si hubo cambios |
| Informe de modificaciones respecto de ifc | `IN` | ASB | Causa y referencia de cada cambio |
| Manuales de operación y mantenimiento | `MN` | ASB | |
| Protocolos finales firmados (data book) | `PT` | ASB | |
| Archivos CAD nativos y PDF | `PL` | ASB | Según requisito del cliente |
| Acta de entrega y cierre | `RG` | ASB | |

## 7.10 Entregables típicos de otras disciplinas

Se agregan a los de las categorías anteriores según las disciplinas declaradas en `project-information.md`. Los códigos de tipo se definen en `DOCUMENT_RULES.md`, 8.2.

**Civil (`C`)**

| Entregable | Tipo | Fases |
|---|---|---|
| Memoria descriptiva civil | `MD` | IB, ID |
| Memorias de cálculo de fundaciones, movimiento de suelos y drenaje | `MC` | ID |
| Planos de implantación, nivelación, fundaciones, drenaje, zanjas y cámaras | `PL` | ID |
| Especificación de hormigón, suelos y obras civiles | `ET` | ID, LIC |
| Cómputo y planillas de armaduras | `LM` | LIC, ID |
| Plan de ensayos de materiales | `PC` | CON |

**Estructuras (`S`) y Arquitectura (`A`)**

| Entregable | Tipo | Fases |
|---|---|---|
| Memoria de cálculo estructural | `MC` | ID |
| Planos de estructura, uniones y montaje | `PL` | ID |
| Especificación de acero estructural y protección superficial | `ET` | ID |
| Memoria descriptiva de arquitectura | `MD` | IB, ID |
| Planos de plantas, cortes, fachadas y detalles constructivos | `PL` | ID |
| Planillas de locales, puertas y terminaciones | `LM` | ID |

**Mecánica y termomecánica (`M`)**

| Entregable | Tipo | Fases |
|---|---|---|
| Hojas de datos y especificaciones de equipos | `HD` / `ET` | ID, LIC |
| Lista de equipos mecánicos | `LE` | ID, ASB |
| Memorias de selección de equipos | `MC` | ID |
| Balance de masa y energía | `MC` | IB, ID |
| Diagramas de proceso y de flujo térmico | `DG` | IB, ID |
| Memorias de calderas, intercambiadores y dispositivos de alivio | `MC` | ID |
| Especificación de aislación | `ET` | ID |
| Planos de implantación, disposición general y soportes | `PL` | ID |
| Procedimiento de puesta en marcha térmica | `PR` | PRE, COM |

**Cañerías (`P`)**

| Entregable | Tipo | Fases |
|---|---|---|
| Especificaciones de cañerías (clases) | `ET` | ID |
| Diagramas P&ID | `DG` | IB, ID, ASB |
| Lista de líneas y lista de válvulas | `LM` / `LE` | ID, ASB |
| Cálculo hidráulico y análisis de tensiones | `MC` | ID |
| Planos de disposición e isométricos | `PL` | ID, ASB |
| Procedimientos y protocolos de pruebas hidrostática / neumática | `PR` / `PT` | PRE |

**HVAC (`H`)**

| Entregable | Tipo | Fases |
|---|---|---|
| Criterios de diseño HVAC | `CR` | IB |
| Balance térmico y cálculo de cargas | `MC` | IB, ID |
| Cálculo de caudales y conductos | `MC` | ID |
| Esquemas de principio y de control | `DG` | ID |
| Planos de conductos y de cañerías de agua | `PL` | ID, ASB |
| Lista de equipos y especificaciones técnicas | `LE` / `ET` | ID, LIC |
| Matriz de secuencias de operación | `LI` | ID, COM |
| Protocolos de balanceo y puesta en marcha | `PT` | PRE, COM |

**Protección contra incendio — combate (`F`)**

| Entregable | Tipo | Fases |
|---|---|---|
| Análisis de riesgo de incendio | `IN` | IB |
| Memoria descriptiva del sistema | `MD` | IB, ID |
| Memorias de cálculo hidráulico, reserva de agua y bombas | `MC` | ID |
| Diagramas de principio y P&ID | `DG` | ID |
| Planos de red de rociadores, hidrantes y montantes | `PL` | ID, ASB |
| Planos de sala de bombas y tanques | `PL` | ID, ASB |
| Especificaciones técnicas | `ET` | ID, LIC |
| Lista de equipos, rociadores e hidrantes | `LE` / `LM` | ID, ASB |
| Procedimientos y protocolos de prueba (hidrostática, flujo, bombas) | `PR` / `PT` | PRE, COM |
| Plan de inspección, ensayo y mantenimiento | `PC` | ASB |

**Detección y alarma de incendio (`F`)**

| Entregable | Tipo | Fases |
|---|---|---|
| Filosofía de detección | `CR` | IB |
| Memoria descriptiva | `MD` | IB, ID |
| Planos de zonificación y ubicación de dispositivos | `PL` | ID, ASB |
| Diagramas de lazos y conexionado | `DG` | ID, ASB |
| Matriz causa–efecto | `LI` | ID, COM, ASB |
| Lista de dispositivos | `LE` | ID, ASB |
| Cálculo de baterías y consumo | `MC` | ID |
| Especificaciones técnicas | `ET` | ID, LIC |
| Protocolo de pruebas de aceptación | `PT` | COM |

**Instrumentación y control (`I`) y Telecomunicaciones (`T`)**

| Entregable | Tipo | Fases |
|---|---|---|
| Lista de instrumentos y señales | `LI` | ID, ASB |
| Hojas de datos de instrumentos | `HD` | ID |
| Diagramas de lazo y arquitectura de control / red | `DG` | ID, ASB |
| Cálculos de dimensionamiento (válvulas de control, elementos de flujo) | `MC` | ID |
| Planos de montaje y canalizaciones | `PL` | ID |
| Lista de cables y enlaces | `LC` | ID, ASB |
| Protocolos de calibración, lazos y certificación de enlaces | `PT` | PRE, COM |

**Transversales (todas las disciplinas)**

| Entregable | Tipo | Fases |
|---|---|---|
| Matriz de interfaces entre disciplinas | `RG` | IB, ID |
| Registro de interferencias (clash) | `RG` | ID |
| Lista de tags y equipos del proyecto | `LE` | ID, ASB |
| Plan de ejecución del proyecto | `PC` | LIC, ID |

---

# LISTA MAESTRA DE ENTREGABLES (completar) — sección 8

| ID | Código | Título | Categoría | Fase | Tipo | Aplica (SÍ/NO) | Paquete (`PQ-nn`) | Depende de (`PQ-nn`) | Estado | Rev. interna | Fecha prevista | Emisión objetivo (ifa / ifc) y entrega en que entra | Fecha de entrega | Entrega (`TR-nnn`) y rótulo al cliente (`Rev 00`) | Requisitos cubiertos (IDs matriz) | Auditado (AUD-nn) | Ruta |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ENT-001 | `[DEFINIR]` | `[DEFINIR]` | | | | | | | | | | | | | | | |

**Revisiones.** *Rev. interna* es la revisión de trabajo vigente: `00.0` mientras el documento no sufre una rfc, `00.n` si la `rfc-n` lo modificó, `01` y siguientes tras el as-built (`DOCUMENT_RULES.md`, sección 9); los borradores anteriores a `REVIEWED` no la cambian. La columna *Entrega (`TR-nnn`) y rótulo al cliente* registra, por entrega, el `TR-nnn` y el rótulo `Rev 00`; la revisión interna enviada de cada documento figura en el transmittal. En las filas de planos y diagramas dibujados por el usuario, *Estado* es el del documento de insumos y el estado del dibujo se consulta en `drawing-status.md`.

**Paquete y Depende de.** *Paquete* es el `PQ-nn` al que pertenece el entregable (un solo paquete por entregable; los insumos de dibujo de un plano van en el paquete del plano) y *Depende de* son los `PQ-nn` que deben estar `REVIEWED` antes de empezar ese paquete (`—` si no depende de ninguno). Las dos columnas son la **fuente única** del grafo de ejecución; todas las filas de un mismo paquete llevan el mismo valor en *Depende de*. Un `PQ-nn` citado en *Depende de* que no existe en la columna *Paquete*, un ciclo de dependencias, o un entregable aplicable sin paquete son errores de la LME que la auditoría informa.

**Plan de paquetes (vista de la LME).** Tabla resumida que Claude presenta al usuario al armar la LME (`CLAUDE.md`, 8.1, Fase 4) y mantiene actualizada; **no se edita aparte**: se deriva de las columnas anteriores y de `schedule-ccpm.md` (fechas copiadas con `ccpm.py`, que la genera con la sección «Plan de paquetes»).

| Orden | Paquete | Nombre corto | Documentos (`ENT-nnn`) | Depende de | Estado del paquete | Hoja de revisión vigente | Entrega objetivo | Fecha prevista (entrega al usuario / revisado) |
|---|---|---|---|---|---|---|---|---|
| 1 | PQ-01 | `[DEFINIR]` | | — | `PLANNED` | — | | |

El **orden** es una ordenación topológica del grafo (los paquetes sin dependencias primero) y puede reordenarse con una frase del usuario sin violar las dependencias. *Estado del paquete* usa el vocabulario de 4.1.

**Fecha prevista:** es una **copia** de la fecha de `schedule-ccpm.md` (fuente única); se vuelve a copiar en cada replanificación, y no se edita a mano.

**Entrega parcial:** una entrega se compone de **paquetes `REVIEWED` y auditados**; cuando incluye solo parte de la LME, cada fila indica en qué entrega entra y se incluye el paquete completo (nunca solo algunos documentos de un paquete). Un entregable `BLOCKED` o de un paquete que no integra la entrega objetivo lleva en la columna *Incluido en la entrega* el valor **`Fuera de la entrega (PQ-nn)`** (o **`BLOQUEADO (PQ-nn)`**, con el `BLQ-nnn` en *Estado*) y no figura como incluido; un plano no se incluye en la entrega hasta estar `REVIEWED` en `drawing-status.md`, y su paquete queda fuera de la entrega mientras tanto. La auditoría de entrega verifica los entregables incluidos en la entrega objetivo (todos sus paquetes `REVIEWED`); los no incluidos deben figurar como planificados, con fecha y, si están bloqueados, con su `BLQ-nnn`. La decisión de entregar por partes se registra en `assumptions-and-decisions.md`. Cada fase se entrega como ifa y, tras `cliente aprueba`, dispara la fase siguiente; la ifc se emite al terminar la Ejecutiva (`CLAUDE.md`, 4.3 y 11); cada emisión exige su auditoría; lo que ya se entregó y no cambió se reentrega con el mismo rótulo `Rev 00`.

**Resumen de control (actualizar en cada entrega):**

| Indicador | Valor |
|---|---|
| Entregables aplicables | 0 |
| Paquetes (total / `REVIEWED` / pendientes / `REABIERTO`) | 0 / 0 / 0 / 0 |
| Entregados al cliente (en una entrega ifa / ifc) | 0 |
| Auditados | 0 |
| Pendientes | 0 |
| Planos y diagramas por estado | Ver `drawing-status.md` (no se duplica aquí) |
| Entregables marcados `NO` sin decisión registrada | 0 (debe ser 0) |


---

# MATRIZ DE PREPARACIÓN POR TIPO DE DOCUMENTO — sección 9

Define qué debe estar **confirmado en la línea base** (`project-information.md`, `goals.md`, `client-requirements.md`) antes de desarrollar cada tipo de documento. Es la **puerta de preparación** de `CLAUDE.md`, sección 8.3.

- **Puerta de dependencias (primera condición de toda puerta):** el paquete del documento no empieza hasta que todos los paquetes de su columna *Depende de* estén `REVIEWED`. Si alguno no lo está, el documento no se desarrolla ni se prepara el formulario de la puerta: Claude informa qué paquete falta y propone desarrollarlo antes (por ejemplo, no se redacta el capítulo de requisitos de diseño de un pliego sin haber dimensionado los cables que cita). Solo se puede apartar de esta regla con un `[DEFINIR]` justificado y registrado en una `DEC`.
- **Crítico:** debe estar confirmado (`CONFIRMED`) o ser `DERIVED` de otro crítico confirmado con una regla de derivación escrita y citable (por ejemplo, la frecuencia deducida de la tensión y el sistema de la red del país o reglamento indicado en `NOR-nnn`); un crítico `DERIVED` se muestra al usuario en una línea para su confirmación, no requiere `INF-nnn`. Si falta, Claude **no redacta** y presenta el **formulario de la puerta** (`CLAUDE.md`, 8.3, punto 5).
- **No crítico:** puede quedar `[DEFINIR]` con `INF-nnn`, y se declara en la sección *Pendientes y supuestos* del documento.
- Ningún parámetro crítico se asume. Si el usuario elige la **opción B** del formulario (autorizar un supuesto), el valor se registra como `SUP-nnn` con su **base del valor** (práctica típica citada, catálogo u otro proyecto identificable; sin base queda `[DEFINIR]`), se marca `[VERIFICAR]`, la autorización queda en una `DEC-nnn` y el documento queda marcado con esa dependencia.
- **Críticos no autorizables** (la opción B no existe): en **eléctrica**, el nivel de cortocircuito y el poder de corte (Icc), el régimen de neutro y las tensiones de servicio. Para las **demás disciplinas** el mecanismo es el mismo: la primera vez que se usa una disciplina, Claude propone en una `DEC` la lista de sus críticos no autorizables (los que comprometen la seguridad de las personas o la integridad del equipo si el valor fuese erróneo) y esa lista rige para el proyecto.
- La respuesta «no sé / pendiente» del usuario se trata como opción A (queda una `INF-nnn` con responsable y fecha) y Claude propone el siguiente paso.

## 9.1 Documentación licitatoria de una subestación (pliego)

| Grupo | Parámetros | Criticidad |
|---|---|---|
| Datos eléctricos | Tensiones nominales (MT y BT) | Crítico |
| | Potencias (instalada, demanda, transformadores) | Crítico |
| | Frecuencia y sistema de distribución (esquema, configuración de barras, redundancia) | Crítico |
| | Niveles de cortocircuito (punto de conexión y diseño) | Crítico |
| | Sistema de puesta a tierra (régimen de neutro, criterio de malla, resistividad disponible) | Crítico |
| Operación | Filosofía de operación (modos, continuidad de servicio, telecomando, enclavamientos, mantenimiento) | Crítico |
| | Condiciones ambientales y del sitio; áreas clasificadas | Crítico |
| | Restricciones operativas (cortes, accesos, ventanas) | No crítico (si no hay, declarar «sin restricciones informadas») |
| Alcance | Alcance de suministro (qué equipos y quién los provee) | Crítico |
| | Alcance de construcción (obra civil, edificio, fundaciones, zanjas, malla) | Crítico |
| | Alcance de montaje (electromecánico, cableado, conexionado) | Crítico |
| | Alcance de ensayos (en fábrica, en sitio, pre-commissioning, commissioning) | Crítico |
| | Alcance de control, protecciones, telecomunicaciones y puesta en marcha | Crítico |
| | Exclusiones e interfaces con terceros | Crítico |
| Ensayos y aceptación | Requisitos FAT | Crítico |
| | Requisitos SAT | Crítico |
| | Pruebas funcionales, de protecciones y ensayos eléctricos | Crítico |
| | Capacitación | No crítico |
| | Criterios de aceptación y de recepción provisoria y definitiva | Crítico |
| Documentales | Requisitos documentales (codificación, formatos, revisiones, medios de entrega) | Crítico |
| | Listado de entregables exigidos al contratista | Crítico |
| | Requisitos CAD | Crítico |
| | Documentación As-Built exigida | Crítico |
| Contractuales técnicos | Normas y reglamentos aplicables con edición | Crítico |
| | Plazo de ejecución, hitos, garantías técnicas | Crítico (los económicos y comerciales se tratan fuera de este alcance) |
| | Seguridad y salud, permisos y requisitos HSE del cliente | Crítico |
| | Marcas o proveedores aprobados | No crítico |

**Preparación del pliego (`PG`).** Esta tabla se aplica **capítulo por capítulo**: `TECHNICAL_SPECIFICATIONS_GUIDE.md`, 4.7, indica qué grupos y filas de esta tabla necesita cada capítulo (sin duplicar los parámetros). Claude puede **desarrollar los capítulos cuya puerta se cumple** y dejar los demás `BLOCKED` (con su `BLQ-nnn`); un faltante crítico en un capítulo no detiene el desarrollo de los otros.

## 9.2 Especificación técnica de equipo (celdas MT, transformador, tableros BT, cables, etc.)

| Parámetros | Criticidad |
|---|---|
| Tensión nominal, tensión máxima, nivel de aislamiento | Crítico |
| Corriente nominal, corriente de cortocircuito y duración | Crítico |
| Frecuencia, régimen de neutro, esquema de puesta a tierra | Crítico |
| Condiciones ambientales y grado de protección (IP / IK) | Crítico |
| Normas de producto aplicables y ensayos de rutina y de tipo exigidos | Crítico |
| Requisitos FAT y SAT del equipo | Crítico |
| Documentación a entregar por el proveedor | Crítico |
| Accesorios, repuestos, marcas aprobadas | No crítico |

## 9.3 Memoria descriptiva

| Parámetros | Criticidad |
|---|---|
| Alcance y descripción de la instalación | Crítico |
| Parámetros maestros: tensiones y neutro (`CONFIRMED` en la línea base) | Crítico |
| Potencia instalada y demanda (`PAR-004`, `PAR-005`): son `DERIVED` de la memoria de cálculo de cargas vigente; la memoria descriptiva las cita desde ella, no desde la línea base | Crítico (la memoria de cargas debe existir en la revisión vigente) |
| Filosofía de operación | Crítico |
| Referencias a especificaciones, planos y cálculos (códigos existentes en la LME) | Crítico |
| Detalles de equipos específicos | No crítico |

## 9.4 Memoria de cálculo

| Parámetros | Criticidad |
|---|---|
| Datos de entrada con fuente (potencias, longitudes, impedancias, niveles de falla, resistividad, etc.) | Crítico |
| Criterio aplicable (`ENG-`) y valores límite definidos | Crítico |
| Software y método | No crítico |
| Si es una síntesis de cálculo (`SM`): la memoria de cálculo de origen, en el mismo paquete y en la misma revisión de desarrollo | Crítico |

## 9.5 Planos, listados y protocolos

| Tipo | Parámetros críticos |
|---|---|
| Planos (insumos de dibujo) | Memorias y cálculos de base en estado `REVIEWED` o posterior (son los paquetes de los que depende el paquete del plano); estándar CAD definido; identificadores de equipos definidos |
| Listados | Unifilares en `REVIEWED` o posterior y planos de origen **con insumos entregados (`CAD_INPUT`) y `REVIEWED`**; nomenclatura definida |
| Protocolos | Criterios de aceptación definidos; procedimiento de ensayo y normas aplicables |
| Pliego técnico (`PG`) | Se evalúa **capítulo por capítulo** con los parámetros de 9.1 y 9.6; el detalle de qué necesita cada capítulo y cuáles son críticos está en `TECHNICAL_SPECIFICATIONS_GUIDE.md`, 4.7 (no se repite aquí) |

## 9.6 Documentación licitatoria y especificaciones de otras disciplinas

Además de los parámetros de 9.1 que apliquen (alcance, ensayos, aceptación, documentales), cada disciplina exige como **críticos**:

| Disciplina | Parámetros críticos (confirmados en la línea base) | No críticos |
|---|---|---|
| Protección contra incendio (combate) | Clasificación de riesgo y ocupación por área; sistemas y agentes exigidos; criterio de diseño (densidad / área, caudales); fuente de agua, presión y caudal disponibles; reserva y autonomía; alimentación eléctrica de bombas y respaldo; norma y exigencias de autoridad o aseguradora; pruebas y aceptación (hidrostática, flujo, bombas) | Marcas aprobadas; repuestos |
| Detección y alarma de incendio | Riesgo por área; tipo de sistema; integraciones requeridas; central y autonomía; notificación y evacuación; norma aplicable; pruebas de aceptación | Marcas aprobadas |
| Civil | Estudio geotécnico; topografía; cargas de equipos; acciones de viento y sismo; ambiente y materiales; norma; ensayos de materiales; servicios enterrados existentes | Terminaciones |
| Estructuras y arquitectura | Acciones y combinaciones; norma de diseño; materiales; protección anticorrosiva; exigencia de resistencia al fuego; programa de áreas y rutas de evacuación | Terminaciones |
| Mecánica, termomecánica y cañerías | Fluidos y condiciones de operación (presión, temperatura, caudal); capacidades de equipos; materiales y corrosión; código de diseño; servicios auxiliares disponibles; ensayos y pruebas exigidos | Eficiencia objetivo (crítico si es garantía contractual) |
| HVAC | Condiciones de diseño exteriores e interiores; cargas térmicas internas; caudales de ventilación y presurización; áreas limpias o clasificadas; fuente de energía fría y caliente; pruebas de balanceo y aceptación | Límites de ruido |
| Iluminación normal y de emergencia | **Para el cálculo luminotécnico:** dimensiones y alturas de montaje por área; obstáculos (puentes grúa, ductos); nivel de iluminancia, uniformidad y UGR por área; fotometría de las luminarias o supuestos declarados; definición del área de cálculo. **Para la iluminación de emergencia:** ubicación de salidas y rutas de evacuación; autonomía. **Solo para la alimentación de los circuitos** (no bloquean el cálculo luminotécnico): potencia disponible y cable de alimentación; nivel de cortocircuito para los conductores | Marcas aprobadas, color de luz |
| Instrumentación, control y telecomunicaciones | Señales y protocolos; arquitectura; áreas clasificadas; requisitos SIL; sistemas existentes a integrar; pruebas FAT y SAT | Marcas aprobadas |

**Pliego (`PG`) de estas disciplinas.** La preparación se evalúa capítulo por capítulo (`TECHNICAL_SPECIFICATIONS_GUIDE.md`, 4.7): la fila de cada disciplina involucrada es crítica para el capítulo 05 (requisitos de diseño), y sus normas, pruebas y aceptación lo son para los capítulos 03, 06, 07 y 08. Claude puede desarrollar los capítulos cuya puerta se cumple y dejar los demás `BLOCKED`.

## 9.7 Otros tipos

Para otros tipos de documento (alcances, planes, procedimientos), Claude construye la tabla de preparación equivalente, la propone al usuario y la agrega a esta sección mediante decisión registrada.

## 9.8 Instalaciones BT menores (con tablero seccional)

Para una instalación de baja tensión de pequeña escala alimentada desde una acometida existente (por ejemplo un taller o un local con un tablero seccional), sin media tensión ni subestación propia. Combina lo necesario de 9.2 a 9.5 y evita pedir parámetros que la instalación no tiene.

| Documento | Parámetros críticos | No críticos |
|---|---|---|
| Diagrama unifilar (`DG`) | Tensión y sistema de servicio; régimen de neutro; nivel de cortocircuito en el punto de conexión (Icc); potencia disponible o contratada; lista de cargas con potencia por circuito; ubicación del tablero y distancias a la acometida | Marcas de aparamenta; reserva de ampliación (con `SUP` y base si se adopta) |
| Memoria de cálculo de cargas | Lista de cargas con potencias y tipo de uso; factores de simultaneidad y utilización con su base (`SUP` con base del valor si no hay dato); tensión y sistema | Software y método |
| Memoria de cálculo de conductores y protecciones | Resultado del balance de cargas; longitudes por circuito; Icc en el origen; régimen de neutro; modo de instalación; tablas de capacidad de conducción de la norma aplicable (o `[VERIFICAR]` si la norma no está archivada) | Marcas de cables |
| Memoria de iluminación | Los críticos de 9.6, fila *Iluminación*, para el cálculo luminotécnico; la alimentación solo requiere lo de los conductores | Marcas, color de luz |
| Memoria descriptiva | Alcance de la instalación; tensiones y neutro; potencias (`DERIVED` del cálculo de cargas); referencias a cálculos y planos existentes en la LME | Detalle de equipos |
| Especificación técnica (tablero y cables) | Tensión, corriente nominal, Icc y duración; régimen de neutro; ambiente e IP; normas de producto | Accesorios, marcas aprobadas |
| Lista de materiales / cómputo | Unifilar y planos de origen con insumos entregados (`CAD_INPUT`) y `REVIEWED`; listados de cables y equipos; cantidades con su fuente | Marcas |
| Listados (cables, equipos, cargas) | Unifilar y planos de origen con insumos entregados y `REVIEWED`; nomenclatura definida | — |


---

# MATRIZ DE MADUREZ DE ENTREGABLES — sección 10

Un entregable **no se copia ni se rehace** al cambiar de fase: es el mismo documento que **madura** (misma identidad, mismo código, revisión que continúa). Esta matriz indica, para cada tipo de entregable, el **nivel de madurez** que se espera en cada fase. Se completa por proyecto en la LME (columna *Fase* y emisión objetivo) y rige la auditoría de cada emisión.

Convenciones: **—** no se desarrolla en esa fase; **Preliminar** alcance y criterios, sin dimensionamiento final; **Definido** dimensionado y verificable, apto para licitar o revisar; **Final** cerrado para construir; **Conforme a obra** refleja lo instalado.

| Entregable | Conceptual (IC) | Básica (IB) | Detalle (ID) | Ejecutiva (IE) | As-Built (ASB) |
|---|---|---|---|---|---|
| Memoria descriptiva | Preliminar | Definida | Completa | Final | Conforme a obra |
| Criterios de diseño | Preliminar | Definidos | Aplicados | Final | — |
| Balance de cargas | Estimado | Definido | Final | Final | — |
| Diagrama unifilar | Esquemático | Definido | Detallado | Final para construcción | Conforme a obra |
| Cálculos (cortocircuito, conductores, protecciones) | — | Preliminares | Definitivos | Final | — |
| Layout / implantación | Preliminar | Definido | Coordinado | Final | Conforme a obra |
| Planos de detalle (canalizaciones, montaje) | — | — | Desarrollados | Final para construcción | Conforme a obra |
| Listados (cables, cargas, equipos) | — | Preliminares | Definitivos | Final | Conforme a obra |
| Especificaciones técnicas | — | Preliminares | Definitivas | Final | — |
| Cómputo de cantidades (sin precios; RG-21) | Estimado | Preliminar | Detallado | Final | — |
| Documentación de licitación | — | Preliminar | Completa | Final | — |
| Documentación de construcción | — | — | — | Emitida (ifc) | Conforme a obra |

**Regla de madurez documental.**

- Cada entregable evoluciona **sobre el mismo archivo**: la fase siguiente continúa la numeración de revisión (`DOCUMENT_RULES.md`, sección 9), no abre un documento nuevo.
- La ifa de una fase exige que **todos los entregables aplicables** a esa fase alcancen el nivel de madurez de la matriz; la auditoría lo verifica y un entregable por debajo del nivel es una observación (`project-audit.md`).
- La matriz es un **mínimo**: el proyecto puede ajustarla en una `DEC-nnn` (por ejemplo, un proyecto sin Ejecutiva) y la LME refleja el ajuste.
- La **ifc** no es una aprobación documental: es la liberación para construcción de los entregables ya en nivel Final, y se emite al terminar la Ejecutiva.
- Un cambio de línea base, alcance, requisitos del cliente, parámetros maestros, filosofía de operación, criterios de diseño, potencias o equipos aprobados se tramita como **rfc**; una corrección documental (error de redacción, de cota, de referencia) es una revisión con comentario `REV-nnn`, sin rfc (`change-requests.md`).
