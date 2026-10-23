# redline-log.md — Registro de marcas de obra (redline) para as-built

| Campo | Valor |
|---|---|
| Versión | 1.0 |
| Fecha | 2026-10-12 |
| Responsable | Project Engineer |

---

# GUÍA DEL ARCHIVO (no editar)

## 1. Objetivo

Acumular durante la obra las diferencias entre lo diseñado y lo construido, para que el as-built parta de una lista verificada y no de la memoria.

## 2. Alcance

Desviaciones de obra marcadas por contratista o inspección, por documento. Alimenta `iniciar as-built` y la revisión `Rev 01`.

## 3. Forma de utilización

1. Se anota cada diferencia con documento, ubicación y fuente (plano marcado, foto, acta).
2. Las diferencias se consolidan antes de `iniciar as-built`.
3. Cada fila se cierra al incorporarse al documento as-built.

## 4. Estructura recomendada

ID `RED-nnn`, documento, ubicación, diferencia, fuente, fecha, responsable, estado (`ABIERTA`, `INCORPORADA`, `DESCARTADA`).

## 5. Ejemplos (ilustrativos)

`RED-012 | PL-E-004 | eje C-4 | tablero desplazado 0,8 m | plano marcado obra | 2027-03-10 | ABIERTA`.

## 6. Buenas prácticas

- Una marca sin fuente no vale.
- Fechar todo.
- Descartar con motivo.

---

# REGISTRO (completar)

| RED | Documento | Ubicación | Diferencia | Fuente | Fecha | Responsable | Estado |
|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |
