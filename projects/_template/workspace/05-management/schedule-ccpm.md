# schedule-ccpm.md — Cronograma por Cadena Crítica (CCPM)

| Campo | Valor |
|---|---|
| Proyecto | `[DEFINIR]` |
| Versión | 1.1 |
| Fecha | 2026-10-07 |
| Responsable | Project Engineer |

---

# GUÍA DEL ARCHIVO (no editar)

## 1. Objetivo

Planificar el proyecto por **Cadena Crítica (CCPM)**: estimar las tareas sin colchones ocultos, proteger la fecha del proyecto con **buffers compartidos** y gestionar el avance por el **consumo de buffer** y no por fechas individuales de tarea.

## 2. Alcance

Cubre todas las tareas de la LME (`deliverables.md`) y las dependencias externas (información del cliente, revisiones del cliente, aprobaciones). Se genera automáticamente al iniciar el proyecto y se recalcula ante cambios aprobados (`change-requests.md`), bloqueos o cambios de recursos.

## 3. Forma de utilización

1. **Generación.** Con **«generar cronograma»** (y automáticamente en la Fase 4 de «iniciar proyecto»), Claude arma la lista de tareas a partir de la LME y de la plantilla de la sección 5, estima la **duración segura** de cada una, asigna recurso, predecesores y **paquete de revisión** (`paquete` y `fase_paquete`, punto 11) y escribe `90-management/Planning/ccpm_input.json`. Las duraciones propuestas se presentan al usuario en el **resumen de inicio** (ver nota de la sección 5): Claude propone y el usuario confirma.
2. **Cálculo.** Ejecutar desde la **raíz del proyecto** (`ccpm.py` vive en `98_LIBRARY/calculations/`, ver `calc-library.md`, CAL-008):

   `python3 -B 98_LIBRARY/calculations/ccpm.py 90-management/Planning/ccpm_input.json --md 90-management/Planning/ccpm_output.md --json 90-management/Planning/ccpm_output.json`

   Para obtener las tablas de las secciones B, C y (si las tareas declaran paquete) B2 listas para pegar, con el formato exacto de columnas de este archivo, agregar `--md-secciones` (a pantalla) o `--md-secciones <archivo>`. **Nunca se calculan fechas a mano ni se arman las tablas a mano.**
   **Unidad del plazo.** El plazo del contrato puede venir en horas (por ejemplo, 120 horas hábiles de ingeniería). `ccpm.py` trabaja en días hábiles y lo convierte con `horas_por_dia` (defecto 8): las duraciones pueden darse en horas (`dur_segura_h`, `dur_agresiva_h`) y el plazo en `plazo_horas`. Hay que fijar qué significa: `tipo_plazo = "transcurrido"` (horas que corren en el calendario; deriva la fecha límite en el día hábil `ceil(plazo_horas / horas_por_dia)`) o `"esfuerzo"` (horas de trabajo de ingeniería; no fija una fecha, se compara con el esfuerzo de las tareas internas y se informa el déficit). Si el contrato no lo aclara, Claude lo consulta al usuario antes de calcular.
3. **Confirmación.** Las duraciones y los recursos son **estimaciones de Claude: el usuario las confirma o corrige** (cada responsable estima sus propias tareas; con un único ingeniero revisor, la confirmación se hace en el charter de inicio). Hasta entonces figuran `[VERIFICAR]`.
4. **Déficit contra el plazo.** Si el resultado indica déficit frente a la fecha límite contractual (el fin con buffer, o la cadena sola, supera el plazo), Claude **propone tres opciones** y el usuario elige: (a) **recortar duraciones o alcance** (por ejemplo, paquetes a una entrega posterior); (b) **nuevo plazo** (renegociar la fecha); (c) **más recursos** (por ejemplo, un segundo dibujante o revisor). La opción elegida se registra como **`DEC-nnn`** en `assumptions-and-decisions.md` y se recalcula antes de comprometer la fecha.
5. **Reglas CCPM del proyecto:**
   - Duración agresiva = 70 % de la segura, es decir un recorte del 30 % (salvo estimación propia): una parte de las tareas tardará más, y eso es normal; el buffer lo absorbe.
   - **No hay fechas límite por tarea**, solo hitos contractuales; se ejecuta con conducta «de relevo»: quien recibe una tarea la hace sin pausas y la entrega apenas termina.
   - **Sin multitarea** en la cadena crítica: cada recurso termina una tarea antes de empezar otra de la cadena.
   - Las **dependencias externas** (cliente) se modelan como tareas externas; su demora consume buffer y se informa.
   - La fecha de entrega del proyecto es el fin de la cadena crítica más el **buffer de proyecto**; si supera el límite contractual, se informa el déficit y se decide según el punto 4 antes de comprometer la fecha.
6. **Estados de tarea y replanificación** (`ccpm.py`, campo `estado` de cada tarea):
   - `pendiente` (por defecto): entra en el cálculo.
   - `hecha`: ya terminada; se informa con `inicio_real` y `fin_real` (una tarea con `fin_real` es `hecha`). **No se reprograma**; sus sucesoras no arrancan antes del día hábil siguiente a su `fin_real`.
   - `bloqueada`: se calcula con su duración, pero se informa en la salida con un aviso y **no se cuenta como cumplible**, ni ella ni las tareas que dependen de ella; si el fin del proyecto depende de una tarea bloqueada, el resultado se informa «NO CUMPLIBLE (bloqueo)». Se desbloquea cambiando el estado a `pendiente` y recalculando.
   - `excluida`: fuera de la entrega parcial o del alcance; no entra en la cadena ni en los buffers (las dependencias hacia ella se ignoran con aviso).
   - **Cadena de una entrega parcial:** al entregar por partes (decisión registrada como `DEC-nnn`; una entrega se compone de paquetes `REVIEWED`), cada tarea puede declarar un `lote` (nombre heredado del campo: identifica la entrega parcial a la que pertenece); con `--lote "<nombre>"` las tareas de otra entrega quedan `excluida` y se obtiene la cadena y el buffer de esa entrega (las tareas sin `lote` son comunes y se incluyen). También se puede marcar `excluida` a mano.
   - **Replanificar desde hoy:** con `--desde AAAA-MM-DD` el calendario arranca en esa fecha, las tareas `hecha` no se reprograman y las pendientes se programan desde ahí (se agregan al JSON de entrada las tareas nuevas, los estados y las fechas reales; no hace falta rearmar el cronograma).
   - Para el seguimiento, el JSON de entrada puede traer `base`: `{"fin_cadena": "AAAA-MM-DD", "buffer_proyecto_dias": n, "cadena": ["T1", ...]}` (la cadena y el fin del cálculo base, copiados de la sección C); `ccpm.py` informa entonces el avance de la cadena, el retraso proyectado y el consumo del buffer (definiciones en la sección D).
7. **Fuente única de las fechas.** Este cronograma es la **fuente única** de las fechas. La fecha prevista de cada entregable en la LME (`deliverables.md`) **se copia de aquí en cada replanificación**; no se edita en la LME por separado. Una fecha de la LME distinta de la del cronograma vigente es un hallazgo de auditoría.
8. **Gestión de buffers.** En cada informe de avance, el auditor (`project-audit.md`, sección 3.4) registra en la **sección D** de este archivo el avance global, el avance de la cadena, el retraso proyectado, el **consumo del buffer de proyecto** y su zona, **con las definiciones de la sección D**: **VERDE** (sin acción), **AMARILLO** (preparar un plan de recuperación), **ROJO** (ejecutar el plan e informar al usuario). Los umbrales y pesos por defecto son parámetros a validar por el usuario.
9. **Recálculo.** Un cambio aprobado, un bloqueo nuevo o una información que llega tarde disparan un recálculo; se anota en la sección E con el motivo y el efecto en la fecha.
10. Un cronograma sin recalcular tras un cambio aprobado es un hallazgo de auditoría.
11. **Paquetes de revisión y secuencia de revisión del usuario.** El trabajo avanza por paquete (`deliverables.md`, 4.1): Claude elabora un paquete, el usuario lo revisa, y recién entonces se empieza el siguiente. El cronograma lo modela así:
    - Cada tarea puede declarar `paquete` (`PQ-nn`) y `fase_paquete`: `elaborar` (Claude), `revisar` (el usuario) o `procesar` (Claude procesa los comentarios). Son campos opcionales: sin ellos el cálculo es el de siempre.
    - **La revisión del usuario es una tarea propia por paquete, con duración propia (la confirma el usuario; valor de partida: 2 días hábiles) y un recurso distinto de Claude** (por ejemplo `Usuario`). Así la cadena crítica pasa por la revisión y el cronograma muestra el cuello de botella real: si la revisión ocupa la mayor parte de la cadena, acortar la elaboración no adelanta la fecha.
    - La elaboración del paquete siguiente tiene como predecesora la tarea `revisar` (o `procesar`) del paquete del que depende, no su elaboración: refleja la regla «un paquete no empieza hasta que los paquetes de los que depende estén `REVIEWED`». `ccpm.py` advierte si un paquete depende de una tarea que no es la revisión del anterior, si un paquete no tiene tarea `revisar`, si revisión y elaboración comparten recurso y si hay dependencias circulares entre paquetes.
    - La salida incluye el **Plan de paquetes** (sección B2): orden por dependencias, paquete, tareas, de qué depende, inicio, fecha de entrega al usuario, ventana de revisión del usuario, fecha de «Revisado», días de revisión y estado; más el peso de la revisión en la cadena crítica. Se obtiene con `--md-secciones` y es la fuente de las fechas del plan de paquetes de la LME (`deliverables.md`, sección 8), que las copia en cada replanificación.
    - Los paquetes no alteran la cadena ni los buffers: son una vista de las tareas.

## 4. Estructura recomendada

Cada tarea: ID, entregable (`ENT-nnn`) o actividad, recurso, duración segura y agresiva (días hábiles), predecesores, estado y, si el proyecto se gestiona por paquetes, `paquete` y `fase_paquete`. Resultado: cadena crítica, buffers de alimentación, buffer de proyecto, fechas y comparación con el límite contractual.

## 5. Plantilla de tareas por tipo de entregable (valores de partida a ajustar por el usuario)

| Tipo | Tarea | Recurso | Duración segura (días hábiles) | Predecesor |
|---|---|---|---|---|
| Documento (memoria, especificación, criterios) | Elaborar (`fase_paquete = elaborar`) | Claude | 3 | Datos de entrada, o la tarea `revisar` (o `procesar`) del paquete del que depende |
| Paquete | Revisar el paquete (`revisar`): verificación del usuario de los 1 a 3 documentos del paquete | Usuario | 2 | Elaborar (todos los documentos del paquete) |
| Paquete | Procesar comentarios (`procesar`) | Claude | 1 | Revisar |
| Cálculo | Elaborar (script de biblioteca + memoria + síntesis, en el mismo paquete) | Claude | 3 | Datos críticos de la matriz de preparación; paquete anterior `REVIEWED` |
| Plano | Entregar insumos de dibujo | Claude | 2 | Cálculos y listados |
| Plano | Dibujar (DWG) | Usuario | 3 | Insumos |
| Plano | Verificar contra insumos | Claude | 1 | Dibujo |
| Entrega | Auditoría (una por entrega) | Auditor (Claude, rol independiente) | 3 | Todos los paquetes de la entrega `REVIEWED` |
| Entrega | Entregar (transmittal) | Usuario | 1 | Auditoría aprobada |
| Cliente | Revisión del cliente | Cliente (externo) | Según contrato (por ejemplo 10) | Entrega |
| Información | Entrega de `INF-nnn` | Cliente (externo) | `[DEFINIR]` | Solicitud |

**Regla genérica de duraciones.** El cronograma es **genérico** (no depende del tamaño del proyecto). Las duraciones de la tabla son las **seguras** y la **duración agresiva se obtiene recortando un 30 %** (agresiva = 70 % de la segura, redondeo hacia arriba, mínimo 1 día hábil). El buffer de proyecto se calcula sobre la suma de las agresivas de la cadena crítica (método `50pct`). No se aplica ningún factor especial por tamaño de proyecto.
- **Claude propone y el usuario confirma:** Claude presenta la tabla de «duraciones propuestas» en el **`project-charter.md`** (Fase 3 de «iniciar proyecto») y el usuario las confirma o corrige antes de comprometer fechas. Si el cálculo arroja déficit, se aplica el punto 4 de la sección 3.

## 6. Buenas prácticas

- Estimar con quien ejecuta la tarea, no por él.
- Mantener pocas tareas simultáneas en cada recurso.
- Subordinar todo a la cadena crítica: las tareas de alimentación no deben demorar su unión.
- No «gastar» el buffer por anticipado: se usa solo ante demoras reales.
- Informar al usuario apenas el buffer pase a amarillo.

---

# CRONOGRAMA DEL PROYECTO (completar)

## A. Parámetros

| Parámetro | Valor |
|---|---|
| Fecha de inicio | `[DEFINIR]` |
| Calendario laborable / feriados | `[DEFINIR]` |
| Método de buffer (`50pct` / `rss`) | `[DEFINIR]` |
| Fecha límite contractual y hitos (ifa de cada fase contratada, ifc) | `[DEFINIR]` |
| Recursos | Claude (generación), Usuario (revisión de cada paquete, dibujo CAD, entrega), Cliente (externo), Auditor (rol independiente) |
| Duración de la revisión del usuario por paquete | 2 días hábiles (valor de partida confirmado; se ajusta con la experiencia real) |
| Archivo de entrada | `90-management/Planning/ccpm_input.json` |

## B. Tareas (resumen de la entrada)

| ID | Entregable / actividad | Recurso | Dur. segura | Dur. agresiva | Predecesores | Estado |
|---|---|---|---|---|---|---|
| T01 | | | | | | |

## B2. Plan de paquetes (pegar la salida de `ccpm.py --md-secciones`; solo si las tareas declaran `paquete`)

| Orden | Paquete | Tareas | Depende de | Inicio | Entrega al usuario | Revisión del usuario | Revisado | Días de revisión | Estado |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PQ-01 | | — | | | | | | |

## C. Resultado del cálculo (pegar la salida de `ccpm.py`)

_Generar con `--md-secciones` (ver sección 3, punto 2) y pegar las tablas B y C._

| Concepto | Valor |
|---|---|
| Fin de la cadena crítica | |
| Buffer de proyecto (días) | |
| Fecha de fin del proyecto (con buffer) | |
| Margen o déficit frente al límite contractual (días) | |
| Cadena crítica (tareas) | |
| Buffers de alimentación | |

## D. Seguimiento de buffers (lo completa el auditor en cada informe de avance)

| Informe | Fecha | Avance global (%) | Avance de la cadena (%) | Retraso proyectado (días hábiles) | Consumo del buffer de proyecto (%) | Zona | Acción |
|---|---|---|---|---|---|---|---|
| progress-01 | | | | | | | |

### Definiciones (no editar) — única fuente de estos cálculos

`project-audit.md` (3.4) y `project-status.md` citan estas definiciones; no se definen en otro lugar. Las calcula `ccpm.py` (funciones `avance_entregable`, `avance_global`, `consumo_buffer`, `estado_buffer` y el bloque `seguimiento` de la salida).

**D.1 Pesos por hito de un entregable `[VERIFICAR]`** (valores de partida; **la oficina los ajusta**):

| Hito | Se cumple cuando | Peso |
|---|---|---|
| Generado | el documento existe en la LME en estado `ENGINEERING` o posterior (Claude lo elaboró) | 40 % |
| Revisado | el usuario aprobó su paquete (`revisión aprobada`, documento `REVIEWED`; hoja de revisión sin comentarios abiertos) | 20 % |
| Auditado | tiene auditoría `APPROVED` (`AUD-nn`) | 20 % |
| Entregado (hito `emitido` en el JSON de `ccpm.py`) | figura en un transmittal entregado | 20 % |

**D.2 Avance de un entregable** = suma de los pesos de los hitos cumplidos (de 0 % a 100 %).

**D.3 Avance global (única definición)** = promedio de los avances de los entregables **aplicables** (`Aplica = SÍ` en la LME; los `NO` no cuentan), ponderado por entregable; por defecto todos pesan lo mismo (promedio simple) y la oficina puede asignar pesos (por ejemplo, horas estimadas) `[VERIFICAR]`. No se define «avance = entregados / total»: con esa fórmula el avance sería 0 % hasta la primera entrega. Todo informe (`project-status.md`, `progress-nn`) usa este número.

**D.4 Avance de la cadena** (solo para la zona del buffer; no es el avance global) = suma de las duraciones agresivas de las tareas **hechas** de la cadena crítica base ÷ suma de las duraciones agresivas de toda la cadena base.

**D.5 Consumo del buffer de proyecto** = **retraso proyectado ÷ duración del buffer de proyecto**, donde el retraso proyectado son los **días hábiles** entre el fin de la cadena de la línea base (sección C) y el fin de la cadena replanificado con el avance real (`--desde`); un retraso ≤ 0 es consumo 0 %. **Si el buffer es 0 o la cadena con su buffer no cabe en el plazo** (déficit contra el límite contractual), el porcentaje no está definido: se reporta **«retraso proyectado en N días hábiles frente al límite»** y la zona es **ROJO**.

**D.6 Zonas (regla de tercios)** `[VERIFICAR]`: la zona depende del consumo y del avance de la cadena; la banda VERDE es la tercera parte del buffer más un margen inicial, y la ROJA, las dos terceras partes:
- **VERDE** si consumo ≤ 0,33 × avance de la cadena + 0,10.
- **ROJO** si consumo ≥ 0,67 × avance de la cadena + 0,33, o si el consumo es ≥ 100 %.
- **AMARILLO** en cualquier otro caso.
- Sin avance de la cadena disponible: VERDE si consumo ≤ 1/3; ROJO si consumo ≥ 2/3; AMARILLO en medio.
Son los valores por defecto de `ccpm.py` (`PARAMS_SEMAFORO_DEFECTO`), a validar con datos reales.

## E. Historial de recálculos

| Fecha | Motivo (`rfc-`, `BLQ-`, `INF-`, otro) | Fin de proyecto anterior | Fin de proyecto nuevo | Responsable |
|---|---|---|---|---|
| | | | | |
