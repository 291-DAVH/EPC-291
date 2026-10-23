# starting-data.md — Datos de partida del proyecto

| Campo | Valor |
|---|---|
| Estado | PENDIENTE DE COMPLETAR |
| Versión | 0.1 |
| Fecha | `[DEFINIR]` |
| Responsable | Usuario |

---

# GUÍA DEL ARCHIVO (no editar)

## 1. Objetivo

Es el **único lugar donde el usuario escribe los datos básicos del proyecto** antes de arrancar: carpeta, cliente, rol, códigos, qué se contrata, disciplinas, fases, entregables, plazo y modo de gestión. Reemplaza al cuestionario de preguntas y respuestas del chat. Es la **fuente única** de esos datos: ningún otro archivo los repite (los cita).

## 2. Alcance

Contiene solo lo que **declara el usuario**. No contiene datos técnicos (van en `project-information.md`), alcance ni criterios de aceptación (`project-scope.md`), objetivos (`goals.md`) ni requisitos del cliente (`client-requirements.md`): esos los extrae Claude de la documentación depositada. **No se escriben costos, presupuestos ni montos** (`CLAUDE.md`, principio 14).

## 3. Forma de utilización

1. Antes de arrancar: duplicar la carpeta de la plantilla maestra, darle el nombre del proyecto y completar este archivo en la copia. También sirve completarlo en la maestra: Claude hace la copia con el nombre indicado y se la lleva con la documentación depositada.
2. Depositar la documentación disponible en `01-input/99-unclassified/` sin ordenarla (Claude la clasifica y la registra en `_INPUT_REGISTER.md`).
3. Decir **`iniciar proyecto`**. Claude lee este archivo y la documentación, completa los demás archivos y presenta el `project-charter.md`.
4. Las casillas ya marcadas son los **valores por defecto**: si coinciden con su caso, no las toque. Marque con `[x]` o desmarque con `[ ]`.
5. Los campos obligatorios son **nombre de la carpeta, cliente, sigla del cliente y código del proyecto**. Si faltan, Claude pregunta solo esos. Todo lo demás en blanco toma el valor por defecto o se resuelve con la documentación.
6. Al aprobar el charter, el estado pasa a **CONSUMIDO**. Si después un dato cambia, Claude lo actualiza aquí junto con la decisión `DEC-nnn` que lo justifica.

## 4. Valores por defecto

Rol: Ingeniero Proyectista Senior. Qué se contrata: pliego para licitación. Disciplinas: electricidad. Fases: Conceptual y Base si solo se contrata el pliego. Contenido de la oferta: bases y condiciones, oferta técnica y oferta económica. Plazo: 120 horas hábiles de ingeniería. Modo de gestión: solo ingeniería y trazabilidad documental.

---

# DATOS A COMPLETAR

## 1. Identificación

| Campo | Valor |
|---|---|
| **Nombre de la carpeta** (formato `[CLI]_[PRY]_[Description]`) | `[DEFINIR]` |
| Nombre del proyecto | `[DEFINIR]` |
| **Cliente** | `[DEFINIR]` |
| **Sigla del cliente** (por ejemplo `FORD`) | `[DEFINIR]` |
| Cliente recurrente (sí / no) | `[DEFINIR]` |
| **Código del proyecto** (3 a 6 caracteres, por ejemplo `SET01`) | `[DEFINIR]` |
| Su rol en el proyecto | Ingeniero Proyectista Senior |
| Ubicación (si ya la conoce) | |

## 2. Qué se contrata (puede marcar más de una)

- [x] Pliego para licitación
- [ ] Ingeniería
- [ ] Construcción

## 3. Disciplinas dentro del alcance de ingeniería

- [x] Electricidad
- [ ] Civil
- [ ] Termomecánica
- [ ] Combate de incendios
- [ ] Detección de incendios
- [ ] HVAC
- [ ] Mecánica
- [ ] Sanitaria

## 4. Fases de ingeniería que desarrollamos nosotros

Si solo marcó «Pliego para licitación», las fases siguientes (Detalle, Ejecutiva y As-built) las desarrolla el Contratista adjudicatario: quedan fuera de nuestro alcance y se exigen en el pliego.

- [x] Conceptual
- [x] Base
- [ ] Detalle
- [ ] Ejecutiva
- [ ] As-built

## 5. Entregables

### 5-a. Los que elaboramos nosotros (los que le damos al cliente y, en una licitación, a los oferentes)

- [ ] Memorias descriptivas
- [ ] Memorias de cálculo
- [ ] Planos
- [ ] Diagramas (unifilar, multifilar, esquemáticos)
- [ ] Listados (cargas, cables, materiales)
- [ ] Cómputo de cantidades (sin precios)
- [ ] Pliegos / especificaciones técnicas
- [ ] Hojas de datos de equipos
- [ ] Ensayos e inspección
- [ ] FAT
- [ ] SAT
- [ ] Pre-commissioning
- [ ] COMMISSIONING
- [ ] Capacitación
- [ ] Documentación As-Built
- [ ] Otros: ______

### 5-b. Los que debe producir el Contratista en la obra (solo si marcó «Pliego para licitación»)

Son los documentos de la obra final que el pliego le exigirá al Contratista adjudicatario. No los elaboramos nosotros ni se piden con la oferta.

- [ ] Ingeniería de detalle: memorias de cálculo, planos, diagramas y listados
- [ ] Ingeniería ejecutiva y planos de construcción / montaje
- [ ] Planos de taller y de fabricación
- [ ] Hojas de datos y aprobación de equipos y materiales
- [ ] Protocolos de ensayos e inspección
- [ ] FAT y SAT
- [ ] Pre-commissioning y commissioning
- [ ] Manuales de operación y mantenimiento
- [ ] Capacitación
- [ ] Documentación As-Built
- [ ] Otros: ______

### 5-c. Contenido de la oferta (qué presenta el oferente al licitar)

Los montos de la oferta económica no se transcriben en el proyecto.

- [x] Bases y condiciones aceptadas
- [x] Oferta técnica
- [x] Oferta económica
- [ ] Otros: ______

## 6. Plazo

| Campo | Valor |
|---|---|
| Plazo contractual | 120 horas hábiles de ingeniería |
| Unidad (`transcurridas` / `de esfuerzo`; si no lo sabe, Claude lo consulta en el charter) | `[DEFINIR]` |
| Fecha de inicio y fecha objetivo de cierre (si las hay) | |

## 7. Modo de gestión

- [x] **Solo ingeniería y trazabilidad documental:** sin cronograma, sin duraciones propuestas, sin buffers ni control de plazos. El plazo se registra como dato del contrato. **Gestión mínima incluida:** hitos, horas por paquete (`effort-baseline.md`), semáforo, `issue-log.md`, informe de estado y tablero (`99_core/RULES/m8-management-documents.md`).
- [ ] **Ingeniería + gestión del proyecto:** además, cronograma CCPM, duraciones propuestas, buffers e informe de avance con control de plazos (`schedule-ccpm.md`), y los planes de `90-management/Governance/` completos con los informes de riesgos, esfuerzo y cambios.

## 8. Notas libres

Cualquier otro dato que quiera que Claude tenga en cuenta (sin costos ni montos):

`[DEFINIR]`

## 9. Registro

| Versión | Fecha | Cambio | Decisión asociada |
|---|---|---|---|
| 0.1 | `[DEFINIR]` | Versión inicial de la plantilla | — |
