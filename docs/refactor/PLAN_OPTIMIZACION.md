# Plan de optimización del código con SOLID y patrones de diseño

Estado: Etapa 2 (plan). Rama `refactor/solid`. Base: Etapa 0 (medición) y Etapa 1 (red de seguridad) cerradas con el gate en verde (26 verificaciones).
Regla de oro: **ningún paso cambia el comportamiento**. Si un paso altera un resultado normativo, un dibujo o un documento, se detiene y se informa.

## 1. Línea base (medida con `tools/ci/collect_metrics.py`, ver `baseline.json`)

| Métrica | Antes de la Etapa 1 | Al cerrar la Etapa 1 |
|---|---|---|
| Líneas de producción | Python 29.190 · TypeScript 6.475 | igual (la Etapa 1 no toca producción) |
| Archivos | Python 245 · TypeScript 44 | igual |
| Funciones con complejidad ciclomática > 10 | 141 de 1.457 (máx. 76, media 4,49) | igual (trinquete activo: ninguna puede subir) |
| Tests | Python 708 · frontend 2 | + caracterización de cálculo, dibujo, documentos, informes, validaciones, identidad; frontend 21 |
| Cobertura (piso del gate) | backend 94,0 · calc 74,6 · rules 77,2 · standards 35,9 · drawing 43,8 · documents 69,9 | backend 94,6 · calc 82,5 · rules 76,8 · standards 35,6 · drawing 45,5 · documents 76,1 |

Limitaciones de la medición: el código que corre por subproceso (`sld_generator`, `sld_paginate`, `titleblock/*`) no entra en la cobertura; lo protegen los tests dorados byte a byte
(`engine/drawing/tests/golden/drawings.json`). Los goldens se produjeron en Windows con Python 3.15; el CI de Linux (3.12) no se puede verificar localmente.

Archivos de más de 300 líneas (los candidatos naturales a dividir): `i18n.tsx` 1.834 · `ccpm.py` 1.706 · `identity/service.py` 1.118 · `workflow.py` 1.001 ·
`document_verifier.py` 889 · `skill_learn.py` 725 · `charter_exporter.py` 683 · `canvas_exporter.py` 650 · `sld_generator.py` 594 · `fwlib.py` 572 · `aea_pipeline.py` 501 · `specification_verifier.py` 493.

## 2. Hallazgos

Severidad: **A** = riesgo de divergencia o de error al cambiar (la misma regla en varios lugares); **M** = costo de mantenimiento; **B** = limpieza.
"Pin" indica el test que protege el hallazgo.

### 2.1 Engine — cálculo (`engine/calc/src/epc_calc`)

| # | Dónde | Hallazgo | Sev. | Pin |
|---|---|---|---|---|
| E1 | `aea_conductors:77`, `aea_demand:62`, `aea_earthing:45`, `aea_icc_decay:46`, `aea_icc_factors:50`, `aea_panel_thermal:40`, `aea_special_locations:40`, `aea_voltage_drop:58` | `_num(v, nombre, minimo, estricto)` copiado **idéntico** 8 veces (mismo código fuente). | M | `golden/core.json`, `test_aea_*` |
| E2 | `cable_thermal:62`, `current_and_loads:56`, `hazen_williams:62`, `hvac_airflow:48`, `lighting:89`, `short_circuit:77` | `_pos` idéntico ×6; `_nonneg` idéntico ×4 (`current_and_loads:63`, `hazen_williams:69`, `hvac_airflow:55`, `short_circuit:84`); `_frac` idéntico ×2 (`current_and_loads:70`, `lighting:96`). Variantes distintas (no se tocan): `voltage_drop:50`, `aea_ampacity:79`, `conductor_selection:65`. | M | idem |
| E3 | `aea_feeder_report:28-46` vs `board_memo:56-76` | Formateo es-AR (`p1`, `sig2`, `mm`) duplicado; la variante de `board_memo` devuelve «Pendiente» para `None`. | M | `golden/memo.json`, `golden/core.json` |
| E4 | `aea_pipeline:230,234,245,381`, `aea_feeder_report:77`, `aea_conductors:198`, `aea_demand:149`, `current_and_loads:53`, `short_circuit:74` | √3 escrito de 5 maneras (`_RAIZ3`, `math.sqrt(3)`, `math.sqrt(3.0)`). | B | `golden/pipeline.json` |
| E5 | `aea_pipeline:170 (_primero)`, `mld_generator:130 (nxt)`, `sld_generator:63 (nxt)` | «Siguiente valor de la serie» tres veces. La de `sld_generator` vive en un script de subproceso (Fase C). | M | `golden/pipeline.json`, `drawings.json` |
| E6 | `aea_pipeline:270 (_dispositivo)`, `sld_generator:156 (chain)`, `mld_generator:143 (device_chain)` | La cadena de protecciones por topología (DOL, DOL+OL, Y-Δ, arrancador, VFD, DOL+RCD) se arma en **tres** lugares. Un cambio de norma exige tocar los tres. | A | `golden/pipeline.json`, `drawings.json` |
| E7 | `aea_tables.py:167 (constante)` + `aea_tables.json["constantes"]` | La función `constante()` **no se llama nunca**. Las constantes viven copiadas: `K_MAX_I2_IZ=1.45` (`aea_conductors:37`), `K2_CONVENCIONAL` (`aea_protection:29`), `X_CABLE_OHM_KM=0.08` (`aea_conductors:71`), y `1.05/1.30/1.13/1.45` en línea en `board_memo:90,131`. | A | `golden/core.json`, `memo.json` |
| E8 | `aea_ampacity:132 (_fuente)` y `:158 (factores)` | Dos cadenas `if` paralelas por método de instalación (B1…D2) que deben mantenerse sincronizadas. | M | `golden/core.json` (ampacidad por método) |
| E9 | `aea_pipeline:321 (calculate)` 142 líneas, CC alta | Función larga con varias fases (resolución de criterios, corrientes, sección, protección, verificaciones). | M | `golden/pipeline.json` |
| E10 | `aea_pipeline` forma `resolver_criterios:291` | Aislación por defecto PVC mientras el catálogo de criterios dice XLPE (**cambia resultados**: F5). | — | fuera de alcance |

### 2.2 Engine — dibujo (`engine/drawing/src/epc_drawing`)

| # | Dónde | Hallazgo | Sev. | Pin |
|---|---|---|---|---|
| D1 | `sld/sld_generator.py` (594 líneas) | Script con efectos al importar (lee `argv`, entorno, archivos, lanza subprocesos), tablas de series y de Iz propias, fórmula propia de la acometida (R=1000/56S, X=0,08) — **calcula por su cuenta** (F3). | A | `drawings.json` |
| D2 | `sld/sld_paginate.py`, `titleblock/{sheet_generator,svg_to_dxf,…}` | Misma forma de script con efectos al importar. `sheet_generator.dibujar_final` 98 líneas, `svg_to_dxf.convertir` 92, `capas_dxf.colorear` 141. | M | `drawings.json` |
| D3 | `mld/mld_generator:349` y `sld_generator:18,326` | √3 y series duplicadas (ver E4–E5). | B | `drawings.json` |
| D4 | `export/report_pdf.layout` 90 líneas | Función larga. | B | PDFs: páginas (`drawings.json`) |

### 2.3 Engine — documentos (`engine/documents/src/epc_documents`)

| # | Dónde | Hallazgo | Sev. | Pin |
|---|---|---|---|---|
| X1 | `ccpm.py` (1.706 líneas; funciones de CC 134/52/45/40) | Cálculo de red, buffers, seguimiento y Markdown en un solo módulo. | M | `golden/documents.json` |
| X2 | `document_verifier.py` (889) y `specification_verifier.py` (493) | Funciones largas con verificación + informe mezclados. | M | idem |
| X3 | `charter_exporter.py` (683), `canvas_exporter.py` (650) | Exportadores con estructura parecida (parsear → generar HTML). Sin test de caracterización del charter. | B | `canvas` fijado; charter **no** |

### 2.4 Backend (`backend/src/epc`)

| # | Dónde | Hallazgo | Sev. | Pin |
|---|---|---|---|---|
| K1 | `engineering:165`, `issuing:77,140`, `norms:38`, `projects:80`, `registers:134`, `requirements:43`, `sld:303,327`, `intake/analyzer:187` | «Ahora» con **dos formatos** distintos (naive `isoformat(timespec="seconds")` y con zona `astimezone()`) escrito 10 veces. | M | integración + dorados |
| K2 | `backlog:43`, `deliverables:148`, `management:76`, `registers:148` | «Siguiente id secuencial» ×4 (dos filtran por prefijo). | M | integración |
| K3 | `identity:105`, `masterdata:68`, `norms:25`, `sld/repository:46` | `slug` con 4 variantes (largos 40/32/sin tope; valor por defecto distinto). | M | `test_identity_units.py`, integración |
| K4 | `issuing/repository:46`, `norms:29`, `sld:262`, `deliverables:139` | Hash SHA-256 de archivo y de JSON canónico repetido. | B | integración |
| K5 | `issuing:165`, `registers:34`, `reporting:29` | Elección de idioma `es/en` repetida. | B | integración |
| K6 | `issuing/repository:69,81,87`, `reporting/repository:42`, `sld/repository:122,133`, `admin/repository:60` | Envoltorio de subproceso del motor repetido (timeout, recorte de error) y sin costura para probar. | A | integración |
| K7 | `deliverables:131-139` y `issuing:197-209` | ZIP + `INDICE.csv` duplicado. | M | integración |
| K8 | `engineering.calculation_view`, `sld.calculation`, `sld._upstream` | Lector del resultado de cálculo triplicado. | M | integración |
| K9 | 20 archivos con `05-management` | Ruta de gestión escrita en 20 lugares. | M | integración |
| K10 | `identity/service.py` (1.118 líneas) | Sesiones, organizaciones, invitaciones, registro, OAuth y staff en un módulo; `signup` y `oauth_complete` duplicados. | A | `test_identity_*`, `test_company_registration`, `test_social_login_api` |
| K11 | `engineering/service.py`, `sld/service.py` (≈340 líneas) | Mezclan archivos, criterios, validación, tableros y trabajos. | M | integración + `test_validation_units.py` |
| K12 | `reporting/builders.py` (456) | Textos, builders y renderizado juntos; `BUILDERS` y estados PM² fijos en el código. | M | `golden/reporting.json` |
| K13 | `registers/service.py:_derive` | Umbrales de riesgo (≥20 alto, ≥3 medio) fijos en el código, no en la metodología. | M | `test_planning_units.py` |
| K14 | `norms/service.py` | Ramifica por tipo de punto (regla / tabla / criterio) con `if` repetidos. | M | `test_validation_units.py` |
| K15 | `"pm2"` por defecto en 6 lugares | Metodología por defecto repetida. | B | integración |

### 2.5 Frontend (`frontend`)

| # | Dónde | Hallazgo | Sev. | Pin |
|---|---|---|---|---|
| F-1 | 12 archivos con `const json = { "Content-Type": … }` | Cabecera repetida. | B | Vitest + tsc |
| F-2 | `console/…/Identity.tsx:6`, `ui/…/Norms.tsx:9`, `web/…/Account.tsx:6`, `web/…/Data.tsx:32` | `errorText` copiado ×4. | M | tsc |
| F-3 | 18 pantallas con contador `rev` + `useApi` | Patrón de recarga repetido (`reload()` en `useApi`). | M | Vitest (`api.test.tsx`) |
| F-4 | `web/…/Data.tsx` | CRUD de emisores / clientes / personas con la misma forma. | M | **sin test** (ver 5) |
| F-5 | `ui/src/i18n.tsx` (1.834 líneas) | Un archivo para todos los textos. | M | `i18n.test.tsx` (paridad es/en, placeholders) |
| F-6 | `Project.tsx` | Pantalla grande con subcomponentes en el mismo archivo. | B | tsc + build |

### 2.6 Defectos que **cambian resultados** (documentados, fuera de alcance)

F2–F8 de `docs/refactor/FINDINGS.md` más E10: se anotan en `RESULTADOS.md` como pendientes de decisión; ningún paso los toca.

## 3. Patrones

| Patrón | Dónde aplica | Qué elimina | Costo | Decisión |
|---|---|---|---|---|
| **Extract Module / función compartida** | E1–E5, K1–K5, K9, F-1–F-3 | Duplicación literal | Bajo | **Aplicar** (Fase A) |
| **Policy + Factory** (política normativa) | E7 | Constantes normativas copiadas; agregar una norma = declarar datos | Medio | **Aplicar** (B1), leyendo `aea_tables.json["constantes"]` sin cambiar valores |
| **Tabla de registro** (método → tabla/columna/factores) | E8 | Dos cadenas `if` paralelas | Medio | **Aplicar** (B2) |
| **Strategy** por topología | E6 | Cadena de protecciones en 3 lugares | Medio-alto | **Aplicar parcialmente** (B3): `aea_pipeline` y `mld_generator`; `sld_generator` queda para la Fase C |
| **Factory** `MethodologyPack` + registro de builders | K12, K13, K15 | Metodología fija en código | Medio | **Aplicar** (B4) |
| **Strategy** por tipo de punto | K14 | `if` por tipo | Bajo | **Aplicar** (B5) |
| **Adapter** del motor | K6 | Subprocesos repetidos, sin costura | Medio | **Aplicar** (B6) |
| **SRP split** | K10, K11, K12, F-5 | Módulos de más de 1.000 líneas | Medio | **Aplicar** (B7–B11) |
| **Extract Method / Template Method** | E9, X1, X2, D2 | Funciones de CC > 40 | Alto (sin cobertura de subproceso) | **Aplicar con goldens** (Fase C) |
| **Repository** | backend | Ya existe `repository.py` por módulo | — | **Descartado**: ya aplicado |
| **Observer / Decorator / Builder** | — | No hay problema que resuelvan hoy | — | **Descartados**: sin evidencia de necesidad |
| **Null Object / Result** | — | Los errores de dominio ya se lanzan como `DomainError` y la API los traduce | — | **Descartados** |

## 4. Pasos ordenados (de menor a mayor riesgo)

Cada paso: un commit `refactor(<área>): <id> <principio/patrón>`, gate completo en verde después, sin modificar tests de caracterización.
Si un paso resulta más riesgoso de lo previsto, se marca **DESCARTADO** aquí con el motivo.

### Fase A — extraer sin cambiar estructura

| Id | Paso | Archivos | Tests que lo cubren | Verificación | Riesgo / mitigación |
|---|---|---|---|---|---|
| A1 | `epc_calc/_validate.py` con `num`, `pos`, `nonneg`, `frac`; los módulos de E1–E2 lo importan **conservando el nombre local** (`_num`, …). Solo las copias de código fuente idéntico. | 14 módulos de `epc_calc` | `golden/{pipeline,memo,core}.json`, `test_aea_*` | gate + hash de los goldens sin cambio | Bajo: el cuerpo es idéntico; mensajes de error idénticos |
| A2 | `epc_calc/fmt.py` con `p1/sig2/mm`; `pending=` como parámetro para la variante «Pendiente» | `aea_feeder_report`, `board_memo` | `golden/memo.json`, `core.json` | goldens sin cambio | Bajo; si las salidas difieren en algún borde, se mantiene la variante |
| A3 | **DESCARTADO.** `_primero` solo tiene un usuario dentro de `epc_calc`; las otras copias (`nxt`) y `SQRT3` viven en scripts de subproceso de `drawing` que no importan `epc_calc`: compartirlas obligaría a acoplarlos (Fase C). Reemplazar `math.sqrt(3)` por una constante no elimina duplicación real. | — | — | — | Motivo: valor bajo, acoplamiento nuevo |
| A4 | **REDUCIDO.** `epc_calc/topology.py` con `MOTOR_TOPOLOGIES`, usado por `aea_pipeline` (`TOPOLOGIAS_MOTOR`) y `board_memo` (`MOTORES`). El árbol de circuitos no se comparte: las copias están en `drawing` (subproceso) o difieren. | `aea_pipeline`, `board_memo` | `golden/pipeline.json`, `memo.json` | goldens sin cambio | Bajo |
| A5 | Backend `core/clock.py` (`now_naive`, `now_aware`) conservando cada formato | 10 sitios de K1 | integración | tests de integración + dorados | Bajo: mismo `isoformat` |
| A6 | `core/ids.py` `next_seq(items, prefix=None)` | K2 (4 módulos) | integración | idem | Bajo |
| A7 | `core/text.py` `slugify(text, max_len, default)` con las variantes como argumentos | K3 | `test_identity_units`, integración | idem | Bajo |
| A8 | `core/hashing.py` (`sha256_file`, `sha256_json`) | K4 | integración | idem | Bajo |
| A9 | `core/lang.py` `pick(lang, meta)` | K5 | integración | idem | Bajo |
| A10 | `core/packages.py` `zip_with_index` | K7 | `test_deliverable_package_api`, `test_issuing_api` | idem | Medio: el orden de archivos del ZIP debe ser el mismo |
| A11 | `core/errors.get_or_404` solo para el patrón «buscar en lista» (se revisan los 57 `raise NotFound`) | varios | integración | idem | Medio: se descartan los casos con mensaje distinto |
| A12 | Frontend: `JSON_HEADERS` y `errorText` en `api.ts`; `useApi(...).reload` reemplaza los contadores `rev` | F-1–F-3 | Vitest + `tsc` + build | `web-tests`, `web-types`, `web-build` | Bajo |

### Fase B — abstracciones

| Id | Paso | Archivos | Tests | Verificación | Riesgo / mitigación |
|---|---|---|---|---|---|
| B1 | `epc_calc/policy.py`: objeto de política que lee `aea_tables.constante()`; reemplaza `K_MAX_I2_IZ`, `K2_CONVENCIONAL`, `X_CABLE_OHM_KM` y los `1.05/1.30/1.13/1.45` de `board_memo`. **Primero** un test que demuestra que los valores de la tabla son iguales a los literales; luego el reemplazo. | `aea_conductors`, `aea_protection`, `board_memo`, `aea_tables` | `golden/{pipeline,memo,core}.json` | goldens idénticos | Alto si algún literal difiere de la tabla: **se detiene y se informa** (sería un cambio normativo) |
| B2 | Tabla de registro por método de instalación en `aea_ampacity` | `aea_ampacity` | `golden/core.json` (ampacidad B1…D2 × aislación × material) | goldens idénticos | Medio |
| B3 | Strategy por topología para la cadena de protecciones, usada por `aea_pipeline` y `mld_generator` | `aea_pipeline`, `mld_generator` (+ nuevo `protection_chain.py`) | `pipeline.json`, `drawings.json` | goldens idénticos, DXF por hash | Alto: `sld_generator` queda fuera hasta C1 |
| B4 | `MethodologyPack` (Factory desde `management/methodologies/<id>`) + registro de builders; umbrales de riesgo desde la metodología | `reporting/builders`, `registers/service`, `registers/repository` | `golden/reporting.json`, `test_planning_units` | goldens idénticos | Medio |
| B5 | Strategy por tipo de punto en `norms` | `norms/service` | `test_validation_units`, `test_norms_api` | tests | Bajo |
| B6 | `core/engine.py` (Adapter del subproceso del motor, con costura `set_runner` como `intake.analyzer.set_client_factory`) | K6 (5 repositorios) | integración | tests | Medio: mismo timeout y mismo recorte de error |
| B7 | SRP: `identity/service.py` → `sessions`, `orgs`, `invitations`, `registration`, `oauth`, `staff`, conservando `identity.public` y las firmas | `identity/*` | `test_identity_*`, `test_company_registration`, `test_social_login_api`, `test_identity_units` | tests + contratos de importación | Medio-alto; se regenera `gen_importlinter.py` |
| B8 | `engineering/service.py` → `files.py` + `criteria.py` | `engineering/*` | `test_engineering_api`, `test_design_criteria_api`, `test_validation_units` | tests | Bajo |
| B9 | `sld/service.py` → `validation`, `boards`, `jobs`; lector de cálculo único (K8) | `sld/*`, `engineering/*` | `test_sld_api`, `test_validation_units` | tests | Medio |
| B10 | `reporting/builders.py` → textos aparte + builders | `reporting/*` | `golden/reporting.json` | goldens idénticos | Bajo |
| B11 | Frontend: `i18n.tsx` partido por idioma/área | `ui/src/i18n*` | `i18n.test.tsx` | Vitest + build | Bajo |
| B12 | `useCrud` / `CrudTable` para `Data.tsx` | `web/…/Data.tsx` | **sin test previo**: se escribe antes un test de `Data` | Vitest + build | Medio |
| B13 | `Project.tsx` en archivos por subcomponente | `web/…/project` | `tsc` + build | build | Bajo |

### Fase C — mayor riesgo

| Id | Paso | Archivos | Tests | Verificación | Riesgo / mitigación |
|---|---|---|---|---|---|
| C1 | `sld_generator` → funciones puras + `main()`; sin efectos al importar; tablas a datos. **Los números no cambian** (la acometida propia sigue como está: F3) | `sld/sld_generator.py` | `drawings.json` byte a byte | goldens idénticos | Alto: se hace en subpasos con el golden en cada uno |
| C2 | `sld_paginate` igual | `sld/sld_paginate.py` | `drawings.json` | idem | Alto |
| C3 | `titleblock/*` igual | `titleblock/*` | `drawings.json` | idem | Alto |
| C4 | `ccpm`: Extract Method sobre las funciones de CC > 40 | `ccpm.py` | `golden/documents.json` | idem | Medio |
| C5 | `document_verifier` y `specification_verifier`: Extract Method | `*_verifier.py` | `golden/documents.json` | idem | Medio |
| C6 | `management/workflow` vs `reporting`: unificar solo lo idéntico | `workflow.py`, `fwlib.py` | `test_workflow.py` **no corre** (F1) | — | **DESCARTADO de antemano**: los tests del workflow no son ejecutables en este layout (F1) y los vocabularios difieren (F8) |

## 5. Descartados y límites declarados desde ahora

- **E0.3** (`workflow` en el gate): descartado (F1).
- **C6**: descartado (F1, F8).
- **Sin red de seguridad suficiente**: `charter_exporter` (X3), `RouteEditor` y `Data.tsx` (F-4) no tienen test de caracterización. Antes de tocarlos se escribe uno; si no es posible, el paso se descarta.
- **CI**: `migrations-postgres` y las compilaciones Docker no se pueden ejecutar localmente: se reportan como *no verificados localmente*.
- **Defectos de comportamiento** (F2–F8, E10): fuera de alcance, anotados para decisión.

## 6. Criterio de verificación de cada paso

1. `python tools/ci/run_gate.py` → 26/26.
2. Los archivos `golden/*.json` no cambian (`git diff --stat` vacío en `**/golden/`).
3. `check_complexity` no sube ninguna función; `check_coverage` no baja de su piso.
4. Si falla: `git restore`/`git reset --hard` al commit anterior, análisis, y se anota en este plan.

## 7. Archivos revisados

Ver el apéndice (lista completa de archivos de producción por área, con líneas).

## Apéndice — archivos de producción revisados (299)

**backend/src/epc** — 131 archivos, 8646 líneas

`__init__.py` 3 · `core/__init__.py` 1 · `core/config.py` 100 · `core/db.py` 68 · `core/errors.py` 51 · `core/fsutil.py` 54 · `core/mail.py` 68 · `main.py` 73 · `modules/__init__.py` 1 · `modules/admin/__init__.py` 1 · `modules/admin/api.py` 35 · `modules/admin/public.py` 2 · `modules/admin/repository.py` 64 · `modules/admin/service.py` 37 · `modules/backlog/__init__.py` 1 · `modules/backlog/api.py` 22 · `modules/backlog/models.py` 24 · `modules/backlog/public.py` 17 · `modules/backlog/repository.py` 17 · `modules/backlog/service.py` 64 · `modules/billing/__init__.py` 3 · `modules/billing/public.py` 2 · `modules/construction/__init__.py` 3 · `modules/construction/public.py` 2 · `modules/deliverables/__init__.py` 1 · `modules/deliverables/api.py` 33 · `modules/deliverables/public.py` 40 · `modules/deliverables/repository.py` 17 · `modules/deliverables/service.py` 168 · `modules/engineering/__init__.py` 3 · `modules/engineering/api.py` 53 · `modules/engineering/models.py` 9 · `modules/engineering/public.py` 39 · `modules/engineering/repository.py` 116 · `modules/engineering/service.py` 233 · `modules/identity/__init__.py` 1 · `modules/identity/api.py` 368 · `modules/identity/cli.py` 61 · `modules/identity/countries.py` 134 · `modules/identity/guard.py` 39 · `modules/identity/models.py` 78 · `modules/identity/oauth.py` 137 · `modules/identity/permissions.py` 77 · `modules/identity/public.py` 7 · `modules/identity/repository.py` 306 · `modules/identity/service.py` 1118 · `modules/identity/terms.py` 28 · `modules/intake/__init__.py` 1 · `modules/intake/analysis_api.py` 27 · `modules/intake/analyzer.py` 193 · `modules/intake/api.py` 21 · `modules/intake/public.py` 17 · `modules/intake/repository.py` 28 · `modules/intake/service.py` 60 · `modules/issuing/__init__.py` 1 · `modules/issuing/api.py` 52 · `modules/issuing/models.py` 16 · `modules/issuing/public.py` 2 · `modules/issuing/repository.py` 89 · `modules/issuing/service.py` 217 · `modules/issuing/texts.py` 103 · `modules/knowledge/__init__.py` 1 · `modules/knowledge/api.py` 34 · `modules/knowledge/models.py` 10 · `modules/knowledge/public.py` 10 · `modules/knowledge/repository.py` 9 · `modules/knowledge/service.py` 68 · `modules/management/__init__.py` 1 · `modules/management/api.py` 28 · `modules/management/public.py` 17 · `modules/management/repository.py` 12 · `modules/management/service.py` 83 · `modules/masterdata/__init__.py` 1 · `modules/masterdata/api.py` 121 · `modules/masterdata/models.py` 47 · `modules/masterdata/parties.py` 95 · `modules/masterdata/public.py` 49 · `modules/masterdata/repository.py` 112 · `modules/masterdata/service.py` 296 · `modules/norms/__init__.py` 0 · `modules/norms/api.py` 54 · `modules/norms/public.py` 12 · `modules/norms/repository.py` 105 · `modules/norms/service.py` 353 · `modules/notifications/__init__.py` 3 · `modules/notifications/public.py` 2 · `modules/procurement/__init__.py` 3 · `modules/procurement/public.py` 2 · `modules/projects/__init__.py` 1 · `modules/projects/api.py` 33 · `modules/projects/models.py` 16 · `modules/projects/public.py` 41 · `modules/projects/repository.py` 112 · `modules/projects/service.py` 136 · `modules/quality/__init__.py` 3 · `modules/quality/public.py` 2 · `modules/registers/__init__.py` 0 · `modules/registers/api.py` 53 · `modules/registers/public.py` 23 · `modules/registers/repository.py` 22 · `modules/registers/service.py` 232 · `modules/reporting/__init__.py` 0 · `modules/reporting/api.py` 33 · `modules/reporting/builders.py` 456 · `modules/reporting/models.py` 10 · `modules/reporting/public.py` 12 · `modules/reporting/repository.py` 44 · `modules/reporting/service.py` 157 · `modules/requirements/__init__.py` 1 · `modules/requirements/api.py` 23 · `modules/requirements/public.py` 16 · `modules/requirements/repository.py` 16 · `modules/requirements/service.py` 47 · `modules/schedule/__init__.py` 1 · `modules/schedule/api.py` 17 · `modules/schedule/models.py` 18 · `modules/schedule/public.py` 12 · `modules/schedule/repository.py` 17 · `modules/schedule/service.py` 108 · `modules/sld/__init__.py` 1 · `modules/sld/api.py` 61 · `modules/sld/models.py` 75 · `modules/sld/public.py` 2 · `modules/sld/repository.py` 184 · `modules/sld/service.py` 360 · `modules/wbs/__init__.py` 1 · `modules/wbs/api.py` 17 · `modules/wbs/models.py` 17 · `modules/wbs/public.py` 21 · `modules/wbs/repository.py` 17 · `modules/wbs/service.py` 94

**claude/plugins** — 2 archivos, 270 líneas

`intake-analysis/scripts/intake.py` 186 · `intake-analysis/scripts/test_intake.py` 84

**claude/skills** — 4 archivos, 656 líneas

`generate-specification/_refactor.py` 146 · `generate-specification/_update_00_checklist.py` 183 · `generate-specification/_update_checklists.py` 186 · `generate-specification/assemble-spec.py` 141

**database/migrations** — 7 archivos, 380 líneas

`env.py` 33 · `versions/0001_baseline.py` 100 · `versions/0002_identity.py` 78 · `versions/0003_audit_and_assignments.py` 52 · `versions/0004_username_and_identities.py` 43 · `versions/0005_view_as.py` 24 · `versions/0006_company_registration.py` 50

**engine/calc/src** — 28 archivos, 5148 líneas

`epc_calc/__init__.py` 2 · `epc_calc/aea_ampacity.py` 185 · `epc_calc/aea_catalog.py` 107 · `epc_calc/aea_conductors.py` 206 · `epc_calc/aea_demand.py` 187 · `epc_calc/aea_earthing.py` 140 · `epc_calc/aea_export.py` 138 · `epc_calc/aea_feeder_report.py` 215 · `epc_calc/aea_icc_decay.py` 194 · `epc_calc/aea_icc_factors.py` 181 · `epc_calc/aea_panel_thermal.py` 107 · `epc_calc/aea_pipeline.py` 501 · `epc_calc/aea_protection.py` 72 · `epc_calc/aea_route.py` 132 · `epc_calc/aea_rules.py` 99 · `epc_calc/aea_special_locations.py` 82 · `epc_calc/aea_tables.py` 172 · `epc_calc/aea_voltage_drop.py` 150 · `epc_calc/board_memo.py` 403 · `epc_calc/cable_thermal.py` 138 · `epc_calc/conductor_selection.py` 228 · `epc_calc/current_and_loads.py` 222 · `epc_calc/hazen_williams.py` 123 · `epc_calc/hvac_airflow.py` 128 · `epc_calc/lighting.py` 371 · `epc_calc/make_template.py` 273 · `epc_calc/short_circuit.py` 254 · `epc_calc/voltage_drop.py` 138

**engine/documents/src** — 7 archivos, 4625 líneas

`epc_documents/__init__.py` 2 · `epc_documents/canvas_exporter.py` 650 · `epc_documents/ccpm.py` 1706 · `epc_documents/charter_exporter.py` 683 · `epc_documents/document_verifier.py` 889 · `epc_documents/input_converter.py` 202 · `epc_documents/specification_verifier.py` 493

**engine/drawing/src** — 22 archivos, 3547 líneas

`epc_drawing/__init__.py` 2 · `epc_drawing/board_design.py` 238 · `epc_drawing/export/__init__.py` 1 · `epc_drawing/export/pdf.py` 45 · `epc_drawing/export/report_pdf.py` 166 · `epc_drawing/export/stamp.py` 44 · `epc_drawing/export/transmittal_pdf.py` 142 · `epc_drawing/mld/__init__.py` 1 · `epc_drawing/mld/mld_generator.py` 439 · `epc_drawing/sld/__init__.py` 1 · `epc_drawing/sld/bloques_dxf.py` 101 · `epc_drawing/sld/capas_dxf.py` 323 · `epc_drawing/sld/deps.py` 125 · `epc_drawing/sld/make_variants.py` 60 · `epc_drawing/sld/sld_generator.py` 594 · `epc_drawing/sld/sld_paginate.py` 65 · `epc_drawing/symbols/__init__.py` 12 · `epc_drawing/titleblock/__init__.py` 1 · `epc_drawing/titleblock/lamina_iram.py` 282 · `epc_drawing/titleblock/sheet_generator.py` 471 · `epc_drawing/titleblock/svg_to_dxf.py` 392 · `epc_drawing/titleblock/titleblocks_generator.py` 42

**engine/drawing/tools** — 3 archivos, 410 líneas

`symbols/build_cat9.py` 100 · `symbols/build_pkg.py` 20 · `symbols/svg2dxf_all.py` 290

**engine/rules/src** — 4 archivos, 286 líneas

`epc_rules/__init__.py` 6 · `epc_rules/__main__.py` 48 · `epc_rules/conditions.py` 41 · `epc_rules/ruleset.py` 191

**engine/standards/src** — 7 archivos, 484 líneas

`epc_standards/__init__.py` 2 · `epc_standards/common.py` 55 · `epc_standards/extract_standard.py` 86 · `epc_standards/import_legacy_rules.py` 122 · `epc_standards/promote_rules.py` 64 · `epc_standards/render_pages.py` 48 · `epc_standards/validate_rules.py` 107

**frontend/console/src** — 10 archivos, 944 líneas

`App.tsx` 61 · `features/checker/Checker.tsx` 103 · `features/identity/Identity.tsx` 263 · `features/overview/Overview.tsx` 70 · `features/planning/Planning.tsx` 114 · `features/plugins/Plugins.tsx` 62 · `features/project-files/ProjectFiles.tsx` 99 · `features/rules/Rules.tsx` 122 · `features/skills/Skills.tsx` 32 · `main.tsx` 18

**frontend/console/vite.config.ts** — 1 archivos, 8 líneas

`frontend/console/vite.config.ts` 8

**frontend/packages/ui** — 14 archivos, 3171 líneas

`src/CompanySignup.tsx` 146 · `src/NewProject.tsx` 150 · `src/Shell.tsx` 84 · `src/api.ts` 274 · `src/auth.tsx` 223 · `src/calculation.tsx` 43 · `src/components.tsx` 57 · `src/i18n.tsx` 1834 · `src/index.ts` 14 · `src/markdown.tsx` 48 · `src/norms/Norms.tsx` 197 · `src/plan/Gantt.tsx` 49 · `src/plan/WbsTree.tsx` 29 · `src/theme.ts` 23

**frontend/vitest.config.ts** — 1 archivos, 11 líneas

`frontend/vitest.config.ts` 11

**frontend/web/src** — 17 archivos, 2333 líneas

`App.tsx` 41 · `features/account/Account.tsx` 210 · `features/data/Data.tsx` 249 · `features/new-project/NewProjectPage.tsx` 14 · `features/portfolio/Dashboard.tsx` 173 · `features/project/BoardMemo.tsx` 97 · `features/project/DesignCriteria.tsx` 107 · `features/project/Engineering.tsx` 107 · `features/project/Issuing.tsx` 128 · `features/project/Observations.tsx` 70 · `features/project/Parties.tsx` 83 · `features/project/Project.tsx` 464 · `features/project/Registers.tsx` 137 · `features/project/Reporting.tsx` 85 · `features/project/RouteEditor.tsx` 70 · `features/project/SldInput.tsx` 280 · `main.tsx` 18

**frontend/web/vite.config.ts** — 1 archivos, 8 líneas

`frontend/web/vite.config.ts` 8

**management/workflow** — 20 archivos, 2144 líneas

`scripts/DASHBOARD.py` 11 · `scripts/approve-audit.py` 11 · `scripts/check-inf.py` 11 · `scripts/check-state.py` 11 · `scripts/close-project.py` 11 · `scripts/confirm-sent.py` 11 · `scripts/effort-report.py` 11 · `scripts/fwlib.py` 572 · `scripts/issue-asbuilt.py` 11 · `scripts/issue-ifa.py` 11 · `scripts/issue-ifc.py` 11 · `scripts/progress-report.py` 11 · `scripts/release-documents.py` 11 · `scripts/return-to-engineering.py` 11 · `scripts/send-to-audit.py` 11 · `scripts/send-to-review.py` 11 · `scripts/start-asbuilt.py` 11 · `scripts/sync-ccpm.py` 11 · `scripts/test_workflow.py` 384 · `scripts/workflow.py` 1001

**tools/build** — 1 archivos, 266 líneas

`epc_build.py` 266

**tools/ci** — 11 archivos, 837 líneas

`check_complexity.py` 91 · `check_coverage.py` 81 · `check_dev_credentials.py` 46 · `check_frontend_boundaries.py` 46 · `check_ignored_sources.py` 39 · `check_infra.py` 74 · `check_single_source.py` 47 · `check_skill_conflicts.py` 112 · `collect_metrics.py` 77 · `gen_importlinter.py` 73 · `run_gate.py` 151

**tools/dev** — 5 archivos, 1761 líneas

`new_module.py` 370 · `preview.py` 96 · `reconstruir_indices.py` 147 · `seed_demo.py` 423 · `skill_learn.py` 725

**tools/migrate** — 2 archivos, 536 líneas

`generate_project_files.py` 236 · `migrate_legacy.py` 300

**tools/planning** — 1 archivos, 119 líneas

`board.py` 119
