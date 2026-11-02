# Backlog de pliegos técnicos

Pendientes de la redacción de pliegos (agente `Document Writer`, skill `generate-specification`, plugin `spec-writer` y verificador `epc_documents.specification_verifier`).
Estado: `[ ]` pendiente, `[~]` hecho en parte, `[x]` hecho.

## Hecho
- [x] **Agente `Document Writer` con el prompt generador de pliegos** (2026-11-01). Autor técnico de Especificaciones Técnicas Particulares: analiza el proyecto, propone la estructura y espera validación, lista los vacíos y redacta el pliego completo en Markdown (estructura objetivo de 16 secciones). Guarda el pliego como un solo archivo en `02-engineering/TECHNICAL_SPECS/` (tiene la herramienta `Write`). Conserva las reglas del proyecto: sin precios (RG-21), normas con su edición, marcas `[DEFINIR]`, `[VERIFICAR]` y `[SUPUESTO SUP-nnn]`, formato Pandoc y modo revisión.

## Pendientes
- [ ] **Tres convenciones de estructura conviven.** El agente nuevo usa 16 secciones en un solo archivo; el skill y el agente anterior usaban 9 capítulos (Alcance, Informe descriptivo, Normas, Materiales y equipos, Ejecución, Controles de calidad, Documentación de entrega, Garantías, Responsabilidades) y el verificador espera 10 archivos `NN_Nombre.md` con `00_Index_and_Control.md`. Decidir una sola y alinear las otras dos. Correspondencia aproximada del modelo de 9 capítulos al nuevo: Alcance y generalidades → Objetivo + Alcance; Informe descriptivo → Memoria Descriptiva; Normas → Marco Normativo; Materiales y equipos + Ejecución → Condiciones Generales de Ejecución + Requisitos Técnicos; Controles de calidad → Ensayos + Criterios de Aceptación; Documentación de entrega → Documentación Técnica; Garantías y Responsabilidades → Responsabilidades del Contratista + Recepción Provisoria y Final.
- [ ] **El verificador no revisa el archivo único.** `specification_verifier` lista `NN_Nombre.md` y marca como fuera de patrón cualquier otro archivo; hace falta un modo para un pliego en un solo archivo (las comprobaciones de obligaciones, normas repetidas, comerciales y formato Pandoc sirven igual).
- [ ] **Pasos 2, 5 y 6 del skill** (puerta por capítulo, guardado por capítulo, autocontrol por capítulo) a reescribir según la estructura que se elija.
- [ ] **Probar el agente con un pliego real**: el HVAC de `incoming/` (Parte 4, Especificaciones Particulares) como caso de comparación.
- [ ] **Modo de guardado**: el agente puede escribir en el proyecto; confirmar que solo lo haga en `02-engineering/TECHNICAL_SPECS/` y nunca sobrescriba (hoy lo dice su prompt, no hay una restricción técnica).
