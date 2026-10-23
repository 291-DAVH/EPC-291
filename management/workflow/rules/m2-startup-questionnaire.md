# Módulo M2 — Comando «iniciar proyecto»: datos de partida y lectura de la entrada

> Módulo de `CLAUDE.md` (sección 8.1: filosofía, regla de arranque y Pasos 1 y 2). Tiene la **misma autoridad** que `CLAUDE.md`. Se lee **a demanda**, cuando `CLAUDE.md` (sección 3.1) lo indica. La numeración de las secciones se conserva.

---

### 8.1 Comando «iniciar proyecto»

**Filosofía:** no se comienza redactando documentos. Primero se construye una **definición completa y estructurada del proyecto**: qué debe hacerse, requisitos del cliente, criterios de diseño aplicables, entregables esperados y **criterios de aceptación**. Esa definición es la fuente de verdad de todo lo que se genere después. El usuario **no responde cuestionarios en el chat**: escribe sus datos base en `starting-data.md`, deposita la documentación y dice la frase; Claude hace el resto y le presenta **una sola cosa para aprobar**: el `project-charter.md`.

**Qué prepara el usuario (antes de la frase).**

1. Duplica la carpeta de la plantilla maestra y le pone el nombre del proyecto (o trabaja en la maestra; ver Paso 1).
2. Completa `starting-data.md` (casillas con valores por defecto ya marcados).
3. Deposita toda la documentación que tenga en `01-input/99-unclassified/`, sin ordenarla.

**Regla de arranque (economía de lectura).** Si el usuario escribe «iniciar proyecto» (o «nuevo proyecto», «arrancar proyecto») sin haber preparado `starting-data.md`, Claude no lee el framework: le indica que lo complete y lo vuelva a pedir (o le ofrece completarlo en el chat con las mismas preguntas del archivo, una sola vez). Con el archivo listo, Claude lee `CLAUDE.md` y los módulos que cada paso indica, no más.

Secuencia:

1. **Paso 1 — Lectura de los datos de partida y ubicación del proyecto.**
   - Lee `starting-data.md`. Son **obligatorios** el nombre de la carpeta, el cliente, la sigla del cliente y el código del proyecto. Si falta alguno, los pregunta **juntos, en un solo mensaje** y sigue. Todo otro campo en blanco toma el valor por defecto del archivo (sección 4 de su guía) o se resuelve con la documentación; no se pregunta.
   - **Dónde vive el proyecto.** Si la carpeta de trabajo ya se llama como el nombre de carpeta indicado (el usuario duplicó la plantilla), el proyecto se crea **allí mismo**. Si no (se trabajó en la maestra), Claude crea una **copia nueva** con ese nombre (reglas de nombre en `folder-templates.md`, 4.3; lista cerrada en `M3`) que incluye `starting-data.md` completado y la documentación depositada, y deja la maestra tal como está: avisa al usuario que puede limpiar `99-unclassified` y volver `starting-data.md` a su plantilla en la maestra (Claude no borra nada del usuario sin su permiso).
   - Los códigos de disciplina son los de `CAD_standards.md` (sección 5; Sanitaria = `PL`).
   - Lo declarado en `starting-data.md` se **cita, no se copia**: ningún otro archivo repite esos datos.
2. **Paso 2 — Análisis de la entrada y llenado de las fuentes.** Claude ejecuta la Fase 1 (leer y registrar toda la documentación) y completa, en el mismo turno y sin preguntar, `project-information.md`, `project-scope.md`, `goals.md` y `client-requirements.md` con lo que la documentación permite, cada dato con su fuente (detalle y reglas en `M3`).
3. **Paso 3 — Charter.** Claude genera el `project-charter.md` (versión técnica, estructura PM²) y su versión ejecutiva de una página, `project-charter-executive.md`, y los presenta (resumen breve en el chat, remitiendo a los archivos). El charter técnico incluye, en la sección 8, **el único listado de preguntas** de todo el arranque: solo lo que la documentación no resolvió, numerado y con opción sugerida. Se detiene.
4. **Paso 4 — Aprobación única.** El usuario responde en un solo mensaje las preguntas (por número; «no sé» es válido) y dice `aprobar charter` o `corregir charter: …`. Con `aprobar charter` se fija la línea base 1.0 y Claude ejecuta la Fase 4 de `M3` sin más aprobaciones intermedias (el plan de paquetes de la fase de inicio va dentro del charter).
