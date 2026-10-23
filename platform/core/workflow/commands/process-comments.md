# Procesar comentarios de revisión — `$ARGUMENTS`

Ejecutar cuando el usuario entrega comentarios sobre el paquete en revisión. Implementa M6 sección 11.1 (transición `INTERNAL_REVIEW → FOR_REVIEW`).

## Paso 1 — Registrar cada comentario como REV-nnn

Para cada comentario recibido:

1. Asignar el siguiente `REV-nnn` disponible en `project-status.md`, sección M.
2. Registrar: ID, fecha, paquete afectado, documento afectado, descripción del comentario, origen (USUARIO / CLIENTE / AUDITORÍA).

## Paso 2 — Clasificar: rfc o corrección documental

Para cada `REV-nnn`, determinar si es:

**rfc (abre `rfc-nnn` en `change-requests.md`)** cuando modifica:
- La línea base, el alcance, los requisitos del cliente
- Parámetros maestros (tensiones, potencias, Icc, régimen de neutro)
- Filosofía de operación, criterios de diseño
- El equipamiento aprobado o una decisión registrada

**Corrección documental (no genera rfc)** cuando:
- Corrige un error de representación, una inconsistencia, una omisión
- El dato afectado YA estaba definido en otro documento; simplemente no estaba reflejado

Presentar la clasificación propuesta al usuario con la frase: "¿Confirmar clasificación?"

## Paso 3 — Actualizar revisión de los documentos afectados

Con la clasificación confirmada:

| Caso | Cambio de revisión |
|---|---|
| Corrección documental | `00.R.C` → `00.R.C+1` (suma 1 al último dígito) |
| rfc aprobada `rfc-n` | `00.R.C` → `00.n` (el dígito intermedio = número de rfc; C vuelve a 0) |

Para cada documento modificado:
- Actualizar el YAML de portada (campo `revision`).
- Agregar una fila al control de revisiones: fecha, revisión nueva, descripción específica, `REV-nnn` o `rfc-nnn`.
- Renombrar el archivo: `CÓDIGO_RevXX.md` → `CÓDIGO_RevYY.md`.
- Archivar la versión superada: mover el archivo anterior a `02-engineering/Archive/` con su nombre `_RevXX`.
- Actualizar la columna `Rev.` en `deliverables.md`.

Verificar además: ¿algún otro documento `REVIEWED` **usa el dato modificado** (no solo lo cita)? Si sí, ese paquete queda `REABIERTO` y vuelve a `FOR_REVIEW` según el grafo.

## Paso 4 — Incorporar los cambios al documento

Editar el contenido del documento con los cambios derivados de cada `REV-nnn`, sin cambiar lo que no fue comentado.

## Paso 5 — Correr el verificador

```bash
python3 -B .claude/library/plugins/calculations/document_verifier.py <ruta_proyecto>
```

Resolver cualquier ERROR antes de continuar.

## Paso 6 — Generar la nueva hoja de revisión

Crear `03-review/review-sheets/REVIEW-nn_YYYYMMDD_PQ-nn_v2.md` (o el número que corresponda) con **solo los cambios**:
- Parte A: lista de los documentos modificados, con la revisión nueva y los `REV-nnn` incorporados.
- Parte B: si algún `REV-nnn` abrió nuevas preguntas, listarlas.
- Parte C: cierre (en blanco; lo llena el usuario).

Ejecutar `send-to-review.py PQ-nn` y detenerse.

## Paso 7 — Actualizar project-status.md

En sección M: cerrar cada `REV-nnn` con estado INCORPORATED.
En sección L: actualizar ruta y versión de la hoja de revisión.
