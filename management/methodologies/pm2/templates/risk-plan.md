# risk-plan.md — Plan de gestión de riesgos

| Campo | Valor |
|---|---|
| Versión | 1.0 |
| Fecha | 2026-10-12 |
| Responsable | Project Engineer |

---

# GUÍA DEL ARCHIVO (no editar)

## 1. Objetivo

Fijar cómo se identifican, evalúan, responden y vigilan los riesgos, con escalas únicas, para que el registro `RIE-nnn` sea comparable entre revisiones y proyectos.

## 2. Alcance

Riesgos técnicos, de plazo, costo, seguridad, cliente y obra. El registro vivo sigue siendo el de `assumptions-and-decisions.md` (`RIE-nnn`); este plan define las reglas, no repite el registro.

## 3. Forma de utilización

1. Se completa al aprobar el charter.
2. Cada `RIE-nnn` usa las escalas de la sección A y una estrategia de la sección B.
3. Se revisan según la cadencia de la sección C y siempre antes de cada gate.

## 4. Estructura recomendada

A. Escalas de probabilidad (1 a 5) e impacto (1 a 5), con criterios de plazo y costo del proyecto. Nivel = probabilidad × impacto. B. Zonas: verde ≤ 2, amarillo 3 a 16, rojo ≥ 20 (PM²). C. Estrategias: evitar, reducir, aceptar, transferir. D. Cadencia y umbral de escalamiento.

## 5. Ejemplos (ilustrativos)

`Probabilidad 4 × Impacto 5 = 20 → rojo: escalar al patrocinador y definir respuesta antes del gate`.

## 6. Buenas prácticas

- Todo riesgo rojo tiene responsable, respuesta y fecha.
- Un riesgo materializado pasa a incidencia (`ISSUE_LOG`).
- Cerrar el riesgo con motivo, no borrarlo.

---

# PARÁMETROS DEL PROYECTO (completar)

## A. Escalas del proyecto

| Valor | Probabilidad | Impacto en plazo | Impacto en costo |
|---|---|---|---|
| 1 | Muy baja (< 10 %) | Sin efecto en hitos | `[DEFINIR]` |
| 2 | Baja (10 a 30 %) | Retraso menor al buffer | `[DEFINIR]` |
| 3 | Media (30 a 50 %) | Consume buffer sin mover entregas | `[DEFINIR]` |
| 4 | Alta (50 a 70 %) | Retrasa una entrega | `[DEFINIR]` |
| 5 | Muy alta (> 70 %) | Retrasa el plazo contractual | `[DEFINIR]` |

Zonas por nivel (probabilidad × impacto): verde ≤ 2, amarillo 3 a 16, rojo ≥ 20.

## B. Cadencia de revisión

| Qué se revisa | Cuándo | Quién |
|---|---|---|
|  |  |  |

## C. Umbrales de escalamiento

| Nivel | Zona | Acción |
|---|---|---|
|  |  |  |
