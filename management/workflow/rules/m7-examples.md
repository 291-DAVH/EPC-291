# Módulo M7 — Ejemplos

> Módulo de `CLAUDE.md` (secciones 14). Tiene la **misma autoridad** que `CLAUDE.md`: el texto se movió aquí, sin cambios de fondo, para que `CLAUDE.md` se lea corto en cada sesión. La numeración de las secciones se conserva, de modo que las referencias «`CLAUDE.md`, 8.1» y similares siguen valiendo. Se lee **a demanda**, cuando `CLAUDE.md` (sección 3.1) lo indica.

---

## 14. Ejemplos

**Ejemplo 1 — Pedido de una memoria descriptiva.**
Claude revisa los archivos de la lista de la sección 7, detecta que la tensión de MT figura como 13,2 kV en `project-information.md` pero 13,8 kV en un requisito del cliente, **no elige**: registra la contradicción, propone una decisión `DEC-nnn` y pide confirmación antes de redactar valores.

**Ejemplo 2 — Estado FOR_AUDIT.**
Al abrir la sesión, `project-status.md` indica `FOR_AUDIT`. Claude ejecuta las cinco auditorías (documental, requisitos, ingeniería, entregables, trazabilidad), emite el informe `AUD-nn_YYYYMMDD.md` en formato simple (resultado, observaciones con documento, problema, impacto y acción requerida, y anexos de respaldo; ver `project-audit.md`, sección 8) con hallazgos y veredicto, y propone el estado `AUDITED` solo si se cumplen las condiciones de la sección 11; el estado cambia cuando el usuario dice `aprobar auditoría` y el gestor del proyecto lo registra.

**Ejemplo 3 — Nuevo proyecto de cliente recurrente.**
Claude identifica al cliente, localiza proyectos previos, extrae nomenclatura y criterios CAD, selecciona la plantilla E, y presenta al usuario un resumen de lo que reutilizará y lo que propone cambiar.

**Ejemplo 4 — Secuencia por paquetes.**
El plan confirmado tiene `EJ-PQ-02` (balance de cargas, memoria + síntesis), `EJ-PQ-03` (dimensionamiento de cables de BT, memoria + síntesis) y, mucho más adelante, el capítulo «Requisitos de Diseño» del pliego, que depende de `EJ-PQ-03`. El usuario pide redactar el pliego. Claude no lo redacta: informa que `EJ-PQ-03` no está `REVIEWED`, desarrolla `EJ-PQ-03` (dos documentos), hace su autocontrol, entrega `REVIEW-nn_YYYYMMDD_EJ-PQ-03.md` con solo esos dos documentos y se detiene. El usuario responde `procesar comentarios de revisión`; Claude entrega una nueva hoja de `EJ-PQ-03` solo con lo cambiado; el usuario dice `revisión aprobada` y Claude propone el paquete siguiente.

**Ejemplo 5 — Revisiones, comentarios y rfc.**
El paquete `EJ-PQ-03` está en revisión: el usuario hace dos comentarios a la memoria (`EJ-REV-004` y `EJ-REV-005`) y Claude los incorpora: la memoria pasa de `Rev 00.0` a `00.0.2` y la revisión superada se archiva. Tras `revisión aprobada` y la auditoría, el ifa se envía rotulado `Rev 00` (el transmittal `TR-001` anota «revisión interna enviada 00.0.2»). El cliente comenta dos cosas: que falta un circuito en el unifilar (corrección documental: el circuito existe, no se representó; la memoria sube a `00.0.3`) y que quiere sumar una soldadora (cambia las potencias: es la `EJ-rfc-001`). Con `aprobar rfc EJ-rfc-001` la memoria pasa a `Rev 00.1`. En ambos casos el documento vuelve a ifr, se revisa, se audita lo cambiado y recién entonces se emite un nuevo ifa (`TR-002`), donde el cliente sigue viendo `Rev 00`.

**Ejemplo 6 — Fases y emisiones.**
Cerrada la fase de Detalle, `entrega enviada TR-001` deja el proyecto en `ifa`. Llegan comentarios: `comentarios del cliente recibidos` registra tres `REV-nnn`; Claude propone tratar dos como correcciones documentales y una como rfc, y el usuario responde `confirmar clasificación`. Los documentos afectados vuelven a ifr; con los paquetes `REVIEWED` de nuevo, `auditar` revisa solo lo cambiado, y con `aprobar auditoría` se dice `entregar ifa` y `entrega enviada TR-002`. Cuando el cliente aprueba, el usuario dice `cliente aprueba` y arranca la fase Ejecutiva: Claude propone su plan de paquetes. Al completarla y auditarla, se dice `entregar ifc` y, enviada, el proyecto pasa a obra.
