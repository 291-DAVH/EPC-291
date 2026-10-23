# close-checklist.md — Lista de verificación de cierre

| Campo | Valor |
|---|---|
| Versión | 1.0 |
| Fecha | 2026-10-12 |
| Responsable | Project Engineer |

---

# GUÍA DEL ARCHIVO (no editar)

## 1. Objetivo

Comprobar, antes de `cerrar proyecto`, que todo lo que debía suceder sucedió: entregas aceptadas, pendientes cerrados, lecciones extraídas, archivo completo y registros sin asuntos abiertos.

## 2. Alcance

Cierre administrativo, técnico y de gestión. Complementa las condiciones de `close-project.py` con elementos de gestión que el script no verifica.

## 3. Forma de utilización

1. Claude la completa con `generar informe de cierre`, marcando cada ítem con su evidencia.
2. Cualquier ítem no cumplido bloquea `cerrar proyecto` salvo `DEC` de excepción.
3. Se adjunta al `PROJECT_END_REPORT`.

## 4. Estructura recomendada

Ítems: aceptaciones `ACC` completas, `PUNCH_LIST` cerrada, `ISSUE_LOG` sin abiertos, `rfc` resueltas, riesgos cerrados o transferidos, lecciones extraídas, `ledger` verificado, archivo y backup, devolución de accesos, comunicación de cierre.

## 5. Ejemplos (ilustrativos)

`Lecciones extraídas | SÍ | lessons_EXTRACTED_20271110.md`.

## 6. Buenas prácticas

- Evidencia por ítem, no solo un tilde.
- Una excepción se registra como `DEC`.
- Hacerla al cierre de cada fase mayor, no solo al final.

---

# VERIFICACIÓN (completar)

| Ítem | Cumple (SÍ/NO/NA) | Evidencia | Observación |
|---|---|---|---|
|  |  |  |  |
