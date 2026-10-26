# Resultados de la optimización con SOLID y patrones

Rama `refactor/solid` (51 commits desde `9908bc2`), integrada en `dev` por fases con `--no-ff`. **No se subió nada a GitHub.**
El plan y el motivo de cada paso están en `PLAN_OPTIMIZACION.md`; los hallazgos que no se tocan, en `FINDINGS.md`.

## En una frase

El comportamiento no cambió: los resultados de cálculo, los dibujos (SVG/DXF/PDF), los informes y los documentos verificados son los mismos
que antes (lo prueban los archivos dorados, que no se modificaron para que pasen). Se redujo la complejidad de las funciones más grandes
(la peor pasó de 142 a 76), se partieron los módulos de más de 1.000 líneas y se eliminó la duplicación literal que había en el motor, el backend y el frontend.

## Qué se hizo

| Etapa | Contenido | Estado |
|---|---|---|
| 0. Medición | Trinquete de complejidad (radon), piso de cobertura por área, Vitest en el gate, métricas de línea base | hecho (E0.3 descartado: ver abajo) |
| 1. Red de seguridad | Pruebas de caracterización con archivos dorados: cálculo (pipeline, memoria, ampacidad, informe de alimentador, protecciones), dibujo (unifilar y multifilar de 3 tableros), documentos (CCPM, verificadores, lienzo), informes PM², validaciones del backend, identidad, cliente de API y diccionario es/en del frontend | hecho |
| 2. Plan | `PLAN_OPTIMIZACION.md`: hallazgos con archivo y línea, tabla de patrones, pasos ordenados, lista de archivos revisados | hecho |
| 3A. Extraer | Validadores, formato, topologías, reloj, ids, slug, hash, idioma, `first_or_404` y cabecera/`errorText` del frontend: una sola copia | hecho |
| 3B. Abstracciones | Constantes de protección, métodos de instalación en tablas, estrategias por tipo de punto de normas, adaptador del motor, división de `identity`, `engineering`, `sld`, `reporting`, `i18n` y `Project.tsx` | hecho (B3 y B12 descartados) |
| 3C. Mayor riesgo | Extract Method en CCPM, `verificar_proyecto`, `verificar_pliego`, `comprobar_charter_ejecutivo` y `sld.validate` | hecho (C1–C3 y C6 descartados) |

## Métricas

Antes = commit `9908bc2`; después = final de la rama. Ambas se midieron con las mismas herramientas (la primera línea base no medía seis módulos con marca de orden de bytes; se corrigió y se volvió a medir).

| Métrica | Antes | Después |
|---|---|---|
| Líneas de producción (Python / TypeScript) | 29.000 / 6.464 | 29.955 / 6.489 |
| Archivos (Python / TypeScript) | 243 / 43 | 274 / 54 |
| Funciones medidas | 1.605 | 1.694 |
| Complejidad máxima de una función | 142 (`ccpm._validar`) | 76 (`capas_dxf.colorear`) |
| Funciones con complejidad > 30 | 16 | 8 |
| Funciones con complejidad > 40 | 12 | 4 |
| Funciones con complejidad > 20 | 52 | 48 |
| Funciones con complejidad > 10 | 168 | 181 |
| Complejidad total por encima de 10 (suma) | 1.822 | 1.455 (−20 %) |
| Pruebas Python (definiciones `test_`) | 708 | 783 |
| Pruebas del frontend | 0 | 21 |
| Cobertura backend | 94,1 % | 95,0 % |
| Cobertura engine/calc | 74,7 % | 82,9 % |
| Cobertura engine/drawing | 43,8 % | 45,9 % |
| Cobertura engine/documents | 69,9 % | 76,4 % |
| Cobertura engine/rules · standards | 77,2 · 35,9 % | 77,2 · 35,9 % |
| Archivos de más de 300 líneas | 26 | 25 (`identity/service.py` 1.118 → 144; `i18n.tsx` 1.834 → 33; `Project.tsx` 464 → 81) |

Cómo leerlo: dividir una función grande en pasos nombrados **agrega funciones medianas** (11–28), por eso sube el número de funciones por encima de 10
aunque la complejidad total por encima de 10 baje. `ccpm.py` y `document_verifier.py` crecieron en líneas por las firmas y docstrings de los pasos.

Los archivos de métricas completos: `metrics_before.json` y `metrics_after.json`; el archivo `baseline.json` es la primera medición (sin los seis módulos con marca).

## Pasos descartados o reducidos, y por qué

| Paso | Decisión | Motivo |
|---|---|---|
| E0.3 `workflow` en el gate | descartado | Las pruebas de `management/workflow` están escritas para otro diseño de carpetas (F1): 26 de 27 fallan en este repositorio |
| A3 serie / √3 compartidos | descartado | Las copias restantes viven en scripts de subproceso de `drawing`; compartirlas los acoplaría a `epc_calc` |
| A4 topologías | reducido | Solo el conjunto de topologías de motor de `epc_calc` |
| A10 ZIP con índice | descartado | Los dos constructores difieren en columnas, errores y limpieza; lo común son ~6 líneas |
| A12b `reload()` en lugar de `rev` | descartado | Cambia las URLs pedidas y se reparte en pantallas sin prueba de comportamiento |
| B1 Policy normativa | reducido | `policy.py` con las constantes de protección; no se movieron a `aea_tables.json` (cambiaría los datos que revisa el módulo de normas, que guarda aprobaciones por hash) |
| B3 Strategy de la cadena de protecciones | descartado | Las tres cadenas no son la misma lógica: una produce texto, otra símbolos con polos y parámetros, otra difiere en el variador |
| B4 `MethodologyPack` | reducido | Solo `core/methodology.py`; la metodología ya es dato y no existe una segunda (PRINCE2/PMBOK) |
| B9 lector de cálculo único | descartado | `engineering.calculation_view` y `sld.calculation` leen archivos y devuelven formas distintas |
| B12 `useCrud` | descartado | Los tres CRUD de `Data.tsx` se comportan distinto y no hay prueba de la pantalla |
| C1–C3 `sld_generator`, `sld_paginate`, `titleblock/*` | descartado | Corren en subproceso, sin cobertura por rama; reescribirlos podría cambiar un dibujo entregable sin que nada lo detecte. Es una tarea propia (aislar el módulo de dibujo) |
| C6 `workflow` vs `reporting` | descartado | Pruebas no ejecutables (F1) y vocabularios distintos (F8) |

## Cambios a pruebas existentes (notificados)

Ninguna prueba de caracterización ni archivo dorado se modificó para que pase. Estos son los cambios a pruebas, todos por detalles internos o por un dato volátil:

1. `test_company_registration.py`: fijaba `RESEND_SECONDS` y `CODE_ATTEMPTS` sobre `identity.service`; ahora los fija sobre `identity.registration`, donde viven tras dividir el módulo (B7).
2. `engine/drawing/tests/characterization.py`: la hoja imprime la fecha del día (dd/mm/aaaa) y los hashes escritos el 25/10 fallaron el 26/10. Se normalizó la fecha como los demás datos volátiles y se comprobó que el código previo a la refactorización (`4aae771`) da exactamente el mismo archivo dorado que el actual.
3. `engine/calc/tests`: la grilla de ampacidad se amplió (grupos de 2, 3 y 8 circuitos) antes de B2; las 256 filas anteriores quedan idénticas dentro de las 640 nuevas, y la prueba de forma de la grilla sigue ese tamaño.
4. `i18n.test.tsx`: lee los diccionarios importando `dict/es.ts` y `dict/en.ts` en lugar de analizar el código fuente.

## Herramientas del gate que cambiaron

- `check_complexity.py` no medía los archivos con marca de orden de bytes (seis módulos de documentos y los scripts de `workflow`): corregido, y ahora avisa de los archivos que no puede medir. La actualización de la línea base se rechaza si aumenta la complejidad por encima de 10.
- Un paso de extracción puede crear funciones de hasta 10, o hasta la complejidad de la función del mismo nombre que reemplazan.
- `run_gate.py` guarda en `.cov/failed-<chequeo>.txt` la salida completa de un chequeo que falla.
- El registro de plugins (`claude/plugins/registry.json`) se regeneró con cada cambio del motor (los hashes cubren el código de los plugins).

## Estado del CI

- **Local:** el gate completo da 26/26 sobre el último commit.
- **No se pudo verificar localmente:** los jobs `migrations-postgres` y las compilaciones Docker de GitHub Actions.
- **Archivos dorados:** se generaron en Windows con Python 3.15; el CI de Linux usa 3.12. Los dorados de dibujo normalizan fechas, GUID y orden de objetos del DXF, y los PDF solo se comparan por cantidad de páginas.
- **Un error intermitente:** en dos ejecuciones del gate el chequeo `backend` terminó con un error que no se repitió en seis ejecuciones posteriores (con y sin cobertura). No se pudo identificar la prueba; desde entonces el gate guarda la salida completa de un fallo en `.cov/` para diagnosticarlo si reaparece.
- **Cobertura del código en subproceso:** `sld_generator`, `sld_paginate` y `titleblock/*` no entran en la cobertura; los dorados de dibujo los protegen de punta a punta.

## Defectos de comportamiento que quedan pendientes (no se tocaron)

Son decisiones para después de la refactorización porque cambian resultados. Detalle y pruebas que los fijan en `FINDINGS.md`:

- F2: el informe de alimentador no aplica «XLPE sin método = B2» (falla para aluminio XLPE; el cálculo sí lo aplica).
- F3: `sld_generator` calcula por su cuenta la acometida y, sin el cálculo de `epc_calc`, todo el circuito con fórmulas simplificadas.
- F4: el analizador de IA fuerza una herramienta (`tool_choice`) que la API actual rechaza con el modelo por defecto.
- F5: aislación por defecto PVC en el motor, XLPE en el catálogo de criterios.
- F6: el informe de alimentador usa Ib para la caída de iluminación; el cálculo usa el 66 % al final de la línea.
- F7: los dibujos escriben 30 mA fijo e ignoran el criterio de sensibilidad.
- F8: vocabularios de emisión distintos entre `management/workflow` y el backend.
- Nuevo: los valores de `K_MAX_I2_IZ`, `K2_CONVENCIONAL` y `K1_NO_DISPARO` siguen en `policy.py`, no en `aea_tables.json` (la función `constante()` de las tablas nunca se llama).

## Cómo comprobarlo

```bash
python tools/ci/run_gate.py
```

El gate corre las 26 verificaciones; los dorados están en `engine/*/tests/golden/` y `backend/tests/unit/golden/`.
