# procurement-plan.md — Plan de adquisiciones

| Campo | Valor |
|---|---|
| Versión | 1.0 |
| Fecha | 2026-10-12 |
| Responsable | Project Engineer |

---

# GUÍA DEL ARCHIVO (no editar)

## 1. Objetivo

Planificar qué equipos, materiales y servicios se compran o contratan, con qué plazo de entrega y cuándo debe estar definida cada especificación, para que la ingeniería no frene las compras ni al revés.

## 2. Alcance

Equipos de largo plazo, materiales críticos y servicios de terceros del alcance. Enlaza con `98_LIBRARY/equipment` y con las hojas de datos de `02-engineering/datasheets`.

## 3. Forma de utilización

1. Se crea con la lista de equipos del charter.
2. Cada ítem indica fecha límite de especificación = fecha requerida en obra − plazo de entrega − margen.
3. Los ítems con plazo largo se marcan como riesgo (`RIE-nnn`) si la fecha límite está en peligro.

## 4. Estructura recomendada

Una fila por ítem: ID `ADQ-nnn`, descripción, paquete que lo especifica, plazo de entrega, fecha requerida en obra, fecha límite de especificación, proveedor, estado.

## 5. Ejemplos (ilustrativos)

`ADQ-004 | Tablero general | PQ-07 | 14 semanas | 2027-03-01 | 2026-11-23 | por definir | ESPECIFICANDO`.

## 6. Buenas prácticas

- Ordenar por fecha límite, no por importancia.
- Un ítem sin fecha requerida es información pendiente (`INF`).
- Registrar el proveedor elegido con una `DEC`.

---

# REGISTRO (completar)

| ADQ | Descripción | Paquete | Plazo entrega (sem) | Fecha requerida en obra | Fecha límite de especificación | Proveedor | Estado | Riesgo |
|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |
