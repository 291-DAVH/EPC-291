# Módulo M9 — Checklists de ingeniería, carpetas, calidad y mejores prácticas

> Módulo de `CLAUDE.md` (secciones 7, 9, 10, 12 y 15). Tiene la **misma autoridad** que `CLAUDE.md`. Se lee **antes de generar cualquier documento**, antes de crear carpetas, antes de entregar un paquete o cuando se indica explícitamente.

---

## 7. Antes de generar cualquier documento

Checklist obligatorio, en este orden:

1. Revisar `goals.md` y `project-scope.md` — ¿el documento contribuye a un objetivo y está dentro del alcance?
2. Revisar `project-information.md` — datos y parámetros maestros.
3. Revisar `client-requirements.md` — requisitos que el documento debe cumplir o evidenciar.
4. Revisar `assumptions-and-decisions.md` — decisiones vigentes y supuestos abiertos.
5. Consultar la **biblioteca por relevancia**: `.claude/library/standards/standards-index.md` filtrando por la disciplina y el tema del documento (nunca se leen normas ajenas al tema); `.claude/library/equipment/equipment-catalog.md` para equipos reales; `.claude/library/calculations/calc-library.md` para usar los cálculos validados en lugar de recalcular con fórmulas nuevas. Revisar `engineering-standards.md` y `DESIGN_RULES.md` — criterios y reglas generales aplicables (un desvío de una regla de `DESIGN_RULES.md` se registra como decisión).
6. Revisar `DOCUMENT_RULES.md` — tipo de documento, estructura, estilo, nomenclatura. Si el documento es un pliego (`PG`), leer además `TECHNICAL_SPECIFICATIONS_GUIDE.md`.
7. Revisar `deliverables.md` — el documento existe en la lista maestra; si no, registrarlo.
8. Revisar `traceability-matrix.md` — IDs de requisitos que cubre; actualizar la matriz.
9. **Verificar coherencia técnica** contra los documentos ya entregados y contra la **línea base** (`project-charter.md`, sección 9).
10. **Evitar redundancias:** si el contenido ya existe en otro documento, referenciarlo.
11. **Todo cambio deja evidencia y se resuelve:** un pedido de cambio (del cliente, de obra, de un comentario o de la auditoría) abre una `rfc-nnn` en `change-requests.md` con la evidencia guardada, se evalúa su impacto, se resuelve con una decisión y se cierra tras verificación. Nunca se implementa un cambio sin `rfc`. Cada documento `REVIEWED` que la rfc aprobada modifica pasa a `Rev 00.n` (`n` = número de la rfc); los comentarios `REV-nnn` de un paquete aún no `REVIEWED` no cambian la revisión (6.1, principio 11).
12. **Lecciones:** cuando algo enseñe una regla, criterio, cálculo o equipo reutilizable, se registra `LEC-nnn` en `lessons-learned.md`.
13. **Formato:** los documentos de texto se generan en Markdown compatible con Pandoc (`RG-15` y `RG-20`; `DOCUMENT_RULES.md`, 7.1).
14. Superar la **puerta de preparación** (sección 8.3): sin parámetros críticos confirmados, o sin los paquetes de los que depende el documento en estado `REVIEWED`, no se redacta.

Al terminar la redacción de cada paquete: actualizar `traceability-matrix.md`, `deliverables.md` y `project-status.md`.

---

## 9. Antes de crear carpetas

1. Revisar `folder-templates.md`.
2. Identificar el **cliente**.
3. Identificar el **tipo de proyecto** (ingeniería, EPC, licitación, construcción, cliente recurrente).
4. Seleccionar la **plantilla más adecuada** (A, B, C, D o E) y registrar la elección en `assumptions-and-decisions.md`.
5. Mantener consistencia con proyectos anteriores del cliente.
6. Respetar la numeración fija de carpetas de primer nivel; no renumerar ni inventar niveles nuevos sin decisión registrada.

---

## 10. Clientes recurrentes

Si existen proyectos históricos del mismo cliente (la ruta se registra en `project-information.md`, sección *Proyectos históricos*), Claude debe, antes de definir estructura o criterios:

1. Analizar la **estructura documental** utilizada.
2. Analizar las **nomenclaturas** de documentos, equipos y cables.
3. Analizar los **criterios CAD** (capas, formatos, rótulos, plotstyles).
4. Analizar los **criterios de ingeniería** adoptados y sus decisiones.
5. **Reutilizar** lo apropiado y registrar en `assumptions-and-decisions.md` qué se reutiliza y qué se descarta, con motivo.

Reutilizar no es copiar a ciegas: cada criterio heredado se revalida contra las normas vigentes y los requisitos del proyecto actual. Lo que el cliente exige de forma estable se traslada a `client-requirements.md`.

---

## 12. Quality Assurance

Antes de considerar finalizado cualquier documento (y antes de entregar su paquete a revisión) Claude debe:

1. Revisar **objetivos** (`goals.md`).
2. Revisar **requisitos** (`client-requirements.md`, `traceability-matrix.md`).
3. Revisar **estándares** (`engineering-standards.md`, `DOCUMENT_RULES.md`, `CAD_standards.md`).
4. Revisar **decisiones** (`assumptions-and-decisions.md`).
5. Revisar **entregables** (`deliverables.md`).
6. Revisar **trazabilidad**.
7. **Ejecutar la auditoría** (`project-audit.md`), una sola vez por emisión (cada ifa y cada ifc tienen la suya) y sobre el conjunto de paquetes `REVIEWED`; por paquete solo se hace la auto-verificación ligera de 8.3, punto 7.

**No emitir conformidad sin evidencia.** Evidencia válida: referencia a documento, sección, plano, cálculo, registro o protocolo identificable por código y revisión. "Se considera que cumple" no es evidencia.

---

## 15. Buenas prácticas

- Actualizar los archivos de gestión **en el mismo momento** en que cambia la realidad del proyecto.
- Un cambio de alcance, criterio o parámetro se registra primero como decisión y después se propaga.
- Cada vez que se corrige un documento, revisar qué otros documentos citan ese dato.
- Preferir tablas y listas verificables a texto narrativo ambiguo en lo normativo y contractual.
- No dejar pendientes sin dueño ni fecha.
- Tratar a todo documento propio como si lo hubiera escrito un tercero al auditarlo.
