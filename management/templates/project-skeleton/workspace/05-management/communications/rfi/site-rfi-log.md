# site-rfi-log.md — Registro de consultas de obra (rfi)

| Campo | Valor |
|---|---|
| Versión | 1.0 |
| Fecha | 2026-10-12 |
| Responsable | Project Engineer |

---

# GUÍA DEL ARCHIVO (no editar)

## 1. Objetivo

Controlar las consultas técnicas entre obra e ingeniería: qué se preguntó, quién debe responder, en qué plazo y qué documento queda afectado.

## 2. Alcance

Consultas de obra, proveedores y subcontratistas durante `CONSTRUCTION`, `PRECOMMISSIONING` y `COMMISSIONING`. Una respuesta que cambie un documento emitido abre una `rfc`.

## 3. Forma de utilización

1. Se registra con `registrar consulta de obra`.
2. Se asigna plazo de respuesta; al vencer, aparece en `estado del proyecto`.
3. Si la respuesta modifica un documento, Claude propone `registrar cambio`.

## 4. Estructura recomendada

ID `Srfi-nnn`, fecha, quien consulta, asunto, documento afectado, respuesta, quien responde, fecha de respuesta, rfc asociada, estado.

## 5. Ejemplos (ilustrativos)

`Srfi-005 | 2027-02-03 | Obra | Cruce de bandeja con ducto | PL-E-012 | pendiente | Líder Técnico | 2027-02-06`.

## 6. Buenas prácticas

- Responder por escrito y citar el documento.
- Una consulta sin respuesta a tiempo es riesgo de plazo.
- Si la respuesta cambia el diseño, es cambio, no consulta.

---

# REGISTRO (completar)

| Srfi | Fecha | Consulta de | Asunto | Documento afectado | Responsable | Plazo | Respuesta | Fecha respuesta | rfc | Estado |
|---|---|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |  |  |
