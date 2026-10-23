# ncr-log.md — Registro de no conformidades (NCR)

| Campo | Valor |
|---|---|
| Versión | 1.0 |
| Fecha | 2026-10-12 |
| Responsable | Líder Técnico |

---

# GUÍA DEL ARCHIVO (no editar)

## 1. Objetivo

Registrar cada incumplimiento de un requisito de calidad o seguridad, su causa, la acción correctiva y su verificación, para evitar la repetición.

## 2. Alcance

No conformidades en entregables, en obra o en proveedores. No sustituye los hallazgos de auditoría (`HAL-nnn`): si un hallazgo es sistémico, se eleva a NCR.

## 3. Forma de utilización

1. Se abre con `registrar incidencia` tipo `NCR`, o por elevación de un hallazgo.
2. Cada NCR tiene causa raíz, acción correctiva, acción preventiva y verificación.
3. Las NCR cerradas alimentan `lessons_LEARNED`.

## 4. Estructura recomendada

ID `NCR-nnn`, fecha, descripción, requisito incumplido, severidad, causa raíz, corrección, prevención, responsable, verificación, estado.

## 5. Ejemplos (ilustrativos)

`NCR-002 | Planos con revisión equivocada en transmittal | RG de revisiones | MAJOR | falta de chequeo | corrección TR-004 | verificador previo al envío | CERRADA`.

## 6. Buenas prácticas

- Atacar la causa, no el síntoma.
- Verificar la corrección antes de cerrar.
- Revisar tendencias en cada gate.

---

# REGISTRO (completar)

| NCR | Fecha | Descripción | Requisito | Severidad | Causa raíz | Corrección | Prevención | Responsable | Verificación | Estado |
|---|---|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |  |  |
