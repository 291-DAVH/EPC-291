# Plan: Framework EPC Automatizado "tipo Lego"

> **Documento histórico (plan original).** Paths written as `platform/...` or `\platform\...` describe the layout during the migration. Where things live now:
> `platform/hub` -> `claude/plugins` · `platform/skills` -> `claude/skills` · `platform/agents` -> `claude/agents` · `platform/core/rules` -> `engine/rules` ·
> `platform/core/workflow` -> `management/workflow` · `platform/methodologies` -> `management/methodologies` · `platform/jurisdictions` -> `engine/jurisdictions` ·
> `platform/schemas`, `platform/i18n` -> `shared/` · `platform/tools` -> `tools/` · `platform/apps/api` -> `backend/` · `platform/apps/web` -> `frontend/` ·
> `dev-knowledge`, `_legacy`, `projects*` -> `local/`. The `platform/` folder no longer exists (see `docs/architecture/target-structure.md`).


Base del análisis: las 6 carpetas de `E:\plugins\prueba` (PDFs de assets ignorados). Fecha: 2026-10-23.

---

## 1. Qué tienes hoy (lectura de tu carpeta)

Sin haberlo nombrado, ya tienes 4 capas. Solo falta que estén separadas y conectadas con contratos.

| Capa | Carpeta | Qué hace | Madurez |
|---|---|---|---|
| **Gobierno / orquestación** | `00-Template-Claude` | Metodología PM² + reglas M1–M10, estado = ubicación física (`02-engineering → 03-review → 04-audit → 05-released → 06-deliverables`), scripts de transición con hash SHA-256, comandos en frases fijas, roles (ingeniero, revisor, auditor, document controller) | Alta (v1.4) |
| **Conocimiento / datos** | `291_E_IEC60617_Symbols_Generator`, `291_G_IRAM_Custom_TitleBlocks_Generator` | Biblioteca de símbolos SVG/DXF (SLD/MLD, LV/MV) con catálogo Excel; láminas IRAM A0–A4 con rótulo | Media-alta (v0.4.16 / v0.5.1) |
| **Motor de cálculo** | `elec-calc-generator` (plugin `aea90364-standard`) | Excel de tablero → dimensionado BT (Ib, protección, sección, ΔU, Icc) → `<proyecto>_calculo.json` + Memoria de Cálculo + Síntesis. Tablas normativas en JSON | Media (borrador, falta validar contra norma) |
| **Generadores de entregable** | `sld-generator`, `mld-generator`, skill `generar-pliego` | JSON → unifilar/multifilar en SVG+DXF por hoja; pliegos con agente Document Writer | SLD media, MLD pendiente |

Tu patrón ya es el correcto: **`entrada estructurada → motor → JSON → generador → entregable → revisión → auditoría → emisión`**. Es una línea de producción EPC.

### Lo que ya funciona como "Lego"
- `sld-generator` declara `dependencies` (calc + símbolos + rótulos): ya hay un grafo de plugins.
- `<proyecto>_calculo.json` es el embrión del bus de datos entre plugins.
- Cada plugin tiene `.claude-plugin/plugin.json` + `skills/`.
- El template ya tiene un workflow engine implícito (estados, puertas, scripts).

### Problemas que frenan el escalado (hallazgos concretos)
1. **Copias en vez de referencias.** `elec-calc-generator` tiene skills duplicadas (`skills/` y `plugin/elec-calc-generator/skills/`), `library/calculations` vs `plugin/.../scripts`. `sld-generator` usa `vendor/*.plugin` (copia congelada de otros plugins). Y el template trae otra copia en `.claude/library/PLUGINS`. Hay 2–3 versiones de la misma cosa → deriva garantizada.
2. **Contratos implícitos.** El Excel `input_for_sld` y el `_calculo.json` no tienen schema formal ni versión. Si cambias una columna, se rompe el SLD en silencio.
3. **Estado = carpeta del disco.** Brillante para uso local, pero no sirve en web multiusuario (concurrencia, permisos, auditoría). Hay que abstraerlo.
4. **Todo es prompt-driven.** Las reglas viven en Markdown que Claude interpreta. Para un producto de pago, lo crítico (transiciones, permisos, independencia redactor≠aprobador) debe ser **código que se hace cumplir**, no solo instrucciones.
5. **Migración de nombres a medias.** Las reglas hablan de `98_LIBRARY/99_CORE`, el `pyproject` apunta a `.claude/library/PLUGINS/CALCULATIONS`, los módulos están en minúscula-guion. `SEAL.json` vacío.
6. **Solo eléctrica BT + Argentina.** El template habla de 12 disciplinas, pero hay plugins para una sola y una sola norma (AEA).
7. **Normas con copyright.** AEA/IEC/IRAM en PDF son material de pago. Para un producto comercial no se pueden redistribuir (ver §7).

---

## 2. Arquitectura objetivo

```
                    ┌──────────────────────── CLIENTES ───────────────────────┐
                    │ Claude Code/Cowork │  Web (SaaS)   │  Desktop (offline)  │
                    └────────┬───────────┴───────┬───────┴──────────┬──────────┘
                             │   MISMA API: MCP tools + REST + CLI  │
                    ┌────────▼───────────────────▼──────────────────▼──────────┐
 KERNEL (core)      │ Registry de plugins · Workflow engine · Ledger (hash)    │
 "la baseplate"     │ Rules/Audit engine · Job runner · RBAC · Entitlements    │
                    └───┬──────────────┬────────────────┬──────────────┬───────┘
                        │              │                │              │
             ┌──────────▼───┐  ┌───────▼──────┐  ┌──────▼───────┐ ┌────▼────────┐
 PLUGINS     │ DOMINIO/CALC │  │ GENERADORES  │  │ GESTIÓN      │ │ CONECTORES  │
 "los ladrillos" aea-calc     │  │ sld · mld    │  │ pm2-docs     │ │ cotización  │
             │ (futuro:     │  │ lamina-iram  │  │ pliegos      │ │ ERP / CAD   │
             │ civil, hvac, │  │ pliego · MC  │  │ auditoría    │ │ Drive/Email │
             │ incendio…)   │  │ BOM/cómputo  │  │ transmittals │ │ Stripe      │
             └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ └─────────────┘
                    └─────────────────┼─────────────────┘
                           ┌──────────▼───────────┐
 DATOS                     │ Project Data Model   │  ← schema JSON versionado
                           │ (PDM) + Libraries    │  ← símbolos, tablas normativas
                           └──────────────────────┘
```

### 2.1 Principios
1. **Kernel pequeño y tonto; plugins inteligentes.** El kernel no sabe de cables ni de pliegos: sabe de proyectos, paquetes, estados, permisos y plugins.
2. **Los plugins se hablan por entidades del PDM, no por archivos.** Un plugin declara qué entidades *consume* y cuáles *produce*.
3. **Una sola fuente por plugin** (un repo/paquete versionado, semver). Nada de `vendor/*.plugin` copiados: se instalan por dependencia con rango de versión.
4. **El motor es código; la IA es una capa encima.** Cálculo, transiciones y permisos = determinista y testeable. Claude = redacta, interpreta, revisa, propone.
5. **Humano firma.** Se mantiene tu principio: Claude prepara/verifica/audita, el ingeniero responsable aprueba y firma.
6. **Un mismo plugin corre en los tres entornos.** Claude Code hoy, web mañana, desktop después, sin reescribir.

### 2.2 Contrato de plugin (el "conector Lego")
Extender el `plugin.json` actual (compatible hacia atrás):

```jsonc
{
  "id": "aea-calc",                    // estable, único
  "name": "aea90364-standard",
  "version": "1.6.0",                  // semver
  "kind": "calc",                      // calc | generator | knowledge | workflow | connector
  "discipline": ["electrical"],
  "standards": ["AEA 90364-7-771", "IEC 60364"],
  "requires": { "iec-symbols": "^0.4", "iram-titleblock": "^0.5" },
  "consumes": ["Board", "Circuit"],              // entidades del PDM
  "produces": ["CircuitCalculation", "Document:MC", "Document:SP"],
  "capabilities": ["calc.electrical.lv.dimensioning"],
  "entrypoints": {
    "skills": ["./skills/feeder-sizing"],
    "mcp":    "./mcp/server.py",
    "cli":    "aea-calc run"
  },
  "gates": ["requires:package.state>=ENGINEERING"],   // dónde puede actuar en el workflow
  "entitlement": "feature.calc.electrical",           // para suscripción (§6)
  "data_policy": { "reads_client_data": true, "exports_externally": false }
}
```

Con esto un plugin se puede **instalar, resolver dependencias, activar según plan y ejecutar** sin que el kernel conozca sus internos.

### 2.3 Project Data Model (PDM) — el bus de datos
Entidades mínimas (schemas JSON con `schema_version`):

`Project · Client · Discipline · Requirement · Parameter(PAR) · Decision/Assumption(DEC/SUP) · Change(RFC) · Package(PQ) · Deliverable(ENT) · Document(rev, hash) · Drawing · Board · Circuit · Equipment · Review/Comment(REV) · Audit/Finding · Transmittal(TR)`

Tu trabajo actual ya los define casi todos (IDs `PAR-nnn`, `DEC`, `SUP`, `INF`, `REQ`, `ENT`, `PQ`, `REV`, `rfc`, `TR`). Es **ingeniería de datos que ya hiciste en Markdown**: hay que volcarla a schemas.
Primer schema a formalizar: `Board` + `Circuit` + `CircuitCalculation` (el Excel TABLERO/CIRCUITOS y el `_calculo.json` que hoy conectan calc→SLD).

### 2.4 Workflow engine (extraer M6 a código)
Tabla de transiciones como datos (YAML/JSON), no como prosa:

```
state: ENGINEERING → FOR_REVIEW   guard: deps REVIEWED, selfcheck ok     actor: engineer
state: FOR_REVIEW  → AUDIT        guard: result == APPROVED               actor: reviewer(≠author)
state: AUDIT       → RELEASED     guard: audit APPROVED, no CRITICAL      actor: auditor(≠author)
state: RELEASED    → ISSUED(ifa)  guard: TR confirmed                     actor: doc_controller
```

- **Estado = ubicación** se mantiene en local (carpetas). En web el estado es un campo en DB y las "carpetas" son una vista. El ledger SHA-256 se conserva en ambos.
- La regla "quien redacta no aprueba" pasa a ser un check de RBAC real.

---

## 3. Mapa EPC: qué cubre cada ladrillo y qué falta

| Etapa EPC | Ya existe | Plugin a construir |
|---|---|---|
| **Inicio / PM** | Template: charter PM², starting-data, gates, informes D01–D28, programas (M10) | `pm2-docs` (extraer del template a plugin); `scheduler-ccpm` |
| **Ingeniería conceptual/básica** | Parámetros, criterios, cargas | `load-balance` (balance de cargas), `design-basis` |
| **Ingeniería de detalle – eléctrica BT** | `aea-calc`, SLD, símbolos, láminas IRAM | cerrar `mld-generator`; `cable-schedule`, `raceway-routing` |
| **Documentación técnica** | `generar-pliego`, memoria, síntesis | `spec-writer` multi-disciplina, `datasheets` |
| **Otras disciplinas** | Solo carpetas/plantillas | `civil`, `hvac` (hay `hvac_airflow.py`), `incendio` (hay `hazen_williams.py`), `instrumentación`, `MT` |
| **Cómputos / MTO / BOM** | — | `mto-bom` (salida de calc+diagramas → lista de materiales) |
| **Procurement** | Skill `get-cotizacion` | `procurement` (BOM → cotización → comparativa → OC), `vendor-catalog` |
| **Planificación / costos** | CCPM, esfuerzo (sin costos por confidencialidad) | `schedule`, `effort-tracker` (costos solo si el usuario lo pide) |
| **Construcción / obra** | RFI de obra, redlines, punch list (solo plantillas) | `site-qc`, `redline-to-asbuilt` |
| **Comisionado / As-built** | Estados y scripts | `commissioning-protocols`, `asbuilt` |
| **Calidad transversal** | Auditoría A1–A5, `document_verifier` | `audit-engine` como plugin con reglas por disciplina |

**"EPC automatizado" realista:** automatizar *el 70–80 % repetitivo* (cálculo → diagramas → listados → pliego → BOM → cotización → paquetes de revisión/auditoría) y dejar al humano las **puertas de decisión**. Eso ya es tu diseño.

---

## 4. Estrategia de tres entornos (Claude Code → Web → Desktop)

**Clave: un solo "engine" con tres adaptadores finos.**

| Pieza | Claude Code (hoy) | Web | Desktop |
|---|---|---|---|
| Engine (Python, ya stdlib-first) | scripts locales | backend (contenedor) | proceso local empaquetado |
| Interfaz a IA | Skills + subagentes | Claude API / Agent SDK con las mismas skills como definiciones de agente | idem, con clave propia o proxy |
| Pegamento | — | **MCP server por plugin** + REST | MCP local / IPC |
| Estado del proyecto | carpetas | PostgreSQL + object storage (S3) | SQLite + carpetas (compatible con el template) |
| UI | terminal | React/Next: dashboard de paquetes, hojas de revisión, visor SVG/PDF | misma UI en Tauri/Electron |
| Jobs largos (SLD multi-hoja, DXF) | proceso | cola (Celery/RQ) | hilo/proceso |

Decisiones recomendadas:
- **Exponer cada plugin como servidor MCP.** Es lo que hace que el mismo ladrillo funcione en Claude Code, en tu web (vía Agent SDK) y en desktop.
- **Skills (`SKILL.md`) se mantienen** como "procedimientos del agente"; lo determinista baja a scripts/tools.
- **Offline-first en desktop** es un diferenciador (ingeniería en obra/planta sin internet); la IA es lo único que requiere red.
- Mantener **formatos abiertos** (SVG, DXF, Markdown, JSON, XLSX): el cliente nunca queda atrapado.

Stack sugerido (a validar contigo): Python (engine, FastAPI) · Postgres · S3-compatible · Next.js · Tauri para desktop · Stripe (+ pasarela local si vendes en LATAM).

---

## 5. Estructura de repositorio propuesta (monorepo)

```
epc-platform/
├─ core/                    kernel: registry, workflow, ledger, rbac, entitlements
├─ schemas/                 PDM (JSON Schema versionado) + contratos de plugin
├─ plugins/
│  ├─ aea-calc/             (ex elec-calc-generator; una sola copia de skills/scripts)
│  ├─ iec-symbols/          (ex 291_E…)  → library
│  ├─ iram-titleblock/      (ex 291_G…)
│  ├─ sld/  mld/            (sin vendor/: dependen por versión)
│  ├─ pm2-docs/  pliegos/  audit/
│  └─ <nuevos>/
├─ libraries/               símbolos, tablas normativas derivadas, plantillas
├─ project-template/        (ex 00-Template-Claude, sin copias de plugins)
├─ apps/  cli/  mcp/  api/  web/  desktop/
├─ tests/                   golden files (Excel → JSON → SVG esperado)
└─ docs/
```

Regla de oro: **ningún plugin contiene copia de otro**. El `project-template` referencia plugins por `id@version` (lockfile), no los copia.

---

## 6. Usuarios, organizaciones y suscripciones

### 6.1 Modelo de cuentas
```
Organization (tenant)  ←→ Plan/Subscription
   ├─ Members (User, rol)          roles: owner · admin · project_engineer · reviewer · auditor · doc_controller · client_viewer
   ├─ Projects  →  Packages  →  Documents (revisión + hash)
   ├─ Private Knowledge (pliegos propios, criterios, lecciones)   ← aislado por tenant
   └─ Usage ledger (jobs, tokens, almacenamiento)
Cuenta individual = Organization de 1 miembro (mismo modelo, sin caso especial).
```
- **Independiente** = org unipersonal; **corporativo** = org con miembros, SSO (SAML/OIDC), auditoría de accesos, retención configurable.
- **Cliente externo** = rol `client_viewer` con acceso solo a `06-deliverables` y transmittals (encaja con tu flujo ifa/ifc).
- Los roles de tu M5 (Ingeniero, Revisor, Auditor, Document Controller) **ya son el RBAC**.

### 6.2 Planes (propuesta inicial, ajustable)
| | Individual | Equipo | Corporativo |
|---|---|---|---|
| Usuarios | 1 | hasta ~10 | ilimitado, SSO |
| Plugins | Núcleo (calc BT, SLD, láminas) | + pliegos, PM², auditoría | + todas las disciplinas, conectores, plugins privados |
| Proyectos activos | limitados | más | ilimitados |
| Conocimiento propio (pliegos del cliente) | básico | compartido en la org | por unidad de negocio |
| Soporte / SLA | comunidad | email | dedicado + on-prem opcional |

### 6.3 Técnica
- **Entitlements** = flags por plan que el kernel evalúa contra `entitlement` del plugin (§2.2). Un plugin sin permiso no se carga ni aparece.
- **Metering:** contar jobs de generación, hojas emitidas, almacenamiento y consumo de IA. La IA es **costo variable**: precio debe incluir cuota o créditos.
- **Billing:** Stripe (suscripción + uso medido); webhooks → actualiza entitlements.
- **Marketplace (fase tardía):** plugins de terceros (otras disciplinas/normas) con reparto de ingresos y revisión de seguridad.

---

## 7. Riesgos que debes decidir temprano

1. **Licencia de normas (AEA/IEC/IRAM).** *Resuelto en política (§15):* los PDF son solo estudio interno y nunca entran al repo; el producto lleva tablas derivadas con referencia a cláusula. Sigue pendiente la validación formal del borrador contra el ejemplar oficial (`source_status`) y revisar con asesoría legal qué nivel de derivación es aceptable antes de comercializar.
2. **Responsabilidad profesional.** Cálculos automáticos + firma humana obligatoria, con trazabilidad (quién validó qué versión del motor y de las tablas). Disclaimers y versión del motor grabada en cada documento.
3. **Confidencialidad.** Tu regla RG-21 (no extraer costos del cliente) pasa a ser política de plataforma + aislamiento por tenant. Los pliegos de ejemplo (p. ej. Ford) son conocimiento privado de *tu* cuenta: nunca deben alimentar a otros tenants.
4. **Calidad del cálculo.** Sin suite de pruebas con casos validados por un ingeniero, no hay producto. Hay que crear *golden tests* (entrada Excel → salida JSON/SVG esperada).
5. **Multi-norma.** Diseñar ya el cálculo como `reglas por jurisdicción` (AEA hoy, IEC/NEC/NBR mañana) para no atar el core a Argentina.
6. **Dependencia de la IA.** Todo lo determinista debe poder correr sin LLM; la IA acelera pero no es el único camino.

---

## 8. Roadmap por oleadas

**Ola 0 — Higiene (1–2 semanas, sin features nuevas)**
- Eliminar duplicados (skills y `library` vs `plugin/`), quitar `vendor/*.plugin`.
- Un único nombre/ubicación para librerías en el template; arreglar `pyproject`, `SEAL.json`.
- Congelar versiones y crear `CHANGELOG` unificado.

**Ola 1 — Contratos (2–3 semanas)**
- JSON Schema de `Board/Circuit/CircuitCalculation` y de `plugin.json` extendido.
- Validador: cada plugin se prueba contra schema en CI.
- Golden tests para `aea-calc` y `sld` (3–5 tableros reales).

**Ola 2 — Kernel local (3–4 semanas)**
- Registry + resolución de dependencias + lockfile.
- Workflow engine desde tablas (reemplaza a los scripts SEND_TO_REVIEW, etc., sin cambiar el comportamiento).
- Cada plugin expone CLI y **MCP server**. El template pasa a ser sólo "estructura + reglas".

**Ola 3 — Completar la cadena eléctrica BT (4–6 semanas)**
- Cerrar `mld-generator`; añadir `load-balance`, `cable-schedule`, `mto-bom`.
- Conectar `get-cotizacion` al BOM. Primer flujo punta a punta: *Excel → cálculo → SLD/MLD → listados → pliego → BOM → cotización → paquete de revisión/auditoría*.

**Ola 4 — Web MVP (6–8 semanas)**
- Backend (API + cola de jobs), DB, almacenamiento; UI de proyecto, paquetes, hoja de revisión, visor de láminas.
- Agente web con Agent SDK reutilizando las skills.
- Auth + organizaciones (cuenta individual = org de 1).

**Ola 5 — Comercial (4–6 semanas)**
- Planes, entitlements, Stripe, metering, panel de uso.
- Roles corporativos, auditoría de accesos, SSO.

**Ola 6 — Desktop (4–6 semanas)**
- Empaquetar engine + UI (Tauri), modo offline, sincronización opcional con la nube.

**Ola 7 — Expansión**
- Nuevas disciplinas (HVAC, incendio, civil), multi-norma, marketplace.

---

## 9. Próximos 5 pasos concretos (empezar esta semana)

1. **Elegir la fuente única** de cada plugin y borrar copias (Ola 0). Es el paso con más retorno y menos riesgo.
2. **Escribir el schema `Board/Circuit/CircuitCalculation`** a partir de `input_for_sld_V1.xlsx` y `_calculo.json` existentes.
3. **Definir el `plugin.json` v2** (§2.2) y migrar los 5 plugins actuales manteniendo compatibilidad.
4. **Crear 3 casos de prueba dorados** de tableros reales y validarlos con tu criterio de ingeniero.
5. **Prototipo de un MCP server** para `aea-calc` (una sola tool: `dimension_board`). Si funciona en Claude Code y en un script externo, la arquitectura web/desktop está validada.

---

## 10. Decisiones confirmadas (2026-10-23) y su impacto

| # | Decisión | Impacto en el diseño |
|---|---|---|
| 1 | Solo Argentina, preparado para otros países desde el inicio | **Jurisdiction Packs** (§11): la norma es un paquete de datos+reglas, no código del core |
| 2 | Herramienta interna hoy, producto comercial después | Primero se construye para uso propio; multi-tenant y billing se diseñan ahora pero se activan en Ola 5 |
| 3 | Python + React | Engine y API en Python (FastAPI); web en React (TypeScript solo en el front) |
| 4 | Cliente corporativo puede personalizar con logo y datos; on-premise posible | **White-label por tenant** (§12) + despliegue empaquetado en contenedores (Docker Compose / Helm) |
| 5 | Todas las disciplinas de construcción; primero BT, luego MT, etc. | Orden de plugins en §3 y §13; el core no asume "eléctrica" |
| 6 | Multi-idioma | i18n en UI, documentos generados y mensajes (§14) |
| 7 | Los PDF de assets son material interno de estudio | Se tratan como *material de desarrollo*, nunca como parte del producto (§15) |
| 8 | Todos los plugins en un solo lugar; reemplazo uno y aviso | **Plugin Hub único** `plugins/` (§16) + protocolo de actualización |
| 9 | Los PDF con copyright nunca suben al repositorio | Reglas de `.gitignore` y chequeo en CI (§15) |
| 10 | Contenido base en inglés; explicaciones de Claude en español | Política de idioma (§14) |
| 11 | Gestión inicial PM², el usuario elige PMI u otra | **Methodology Packs** intercambiables (§17) |

---

## 11. Jurisdiction Packs (preparado para otros países desde el día 1)

El core y los plugins de cálculo **no contienen reglas de un país**. Cada país es un paquete de datos + reglas:

```
jurisdictions/
  AR/                      # Argentina — único activo al inicio
    jurisdiction.json      # id, name, locale default, currency, units, voltages, frequency
    electrical/
      standard-map.json    # qué norma aplica a qué tema (AEA 90364-7-771, AEA 90909-1…)
      tables/*.json        # tablas derivadas (tu aea_tables.json actual)
      rules/*.json         # reglas de ingeniería (alturas, reservas, colores…)
      drawing/             # IRAM (láminas, rótulos), convenciones de símbolos
    docs/                  # nomenclatura de documentos, requisitos de rótulo
  _template/               # esqueleto para crear PE, CL, CO, MX, ES…
```

- El calc plugin recibe `jurisdiction: "AR"` y carga tablas/reglas de ese pack. Para sumar Perú/Chile se añade un pack, no se toca el motor.
- Las normas se referencian por **ID de cláusula** (`AEA-90364-7-771:2006/cl.771.19.1`), no se transcriben textos largos.
- Cada pack declara su `source_status` (`verified | draft | pending-validation`), para que el borrador AEA actual quede marcado y no pase a producción sin tu validación.
- Mapeo AR→IEC como base común: muchas reglas AEA derivan de IEC 60364; los packs pueden heredar (`extends: "IEC"`) y sobreescribir.

## 12. Personalización por cliente corporativo (white-label)

Configuración por organización, guardada como datos (no como código):
- `branding`: logos (SVG/PNG), colores, nombre comercial, pie de documento.
- `company`: razón social, dirección, roles/firmas, numeración de documentos, textos legales.
- `titleblock`: datos de rótulo y logos de proveedor/cliente (ya soportado por `iram-titleblock-plugin`: `provider-logo-*.svg`, `client-logo-*.svg`).
- `templates`: plantillas de documentos propias (override de las base).
- `jurisdiction` y `methodology` por defecto.
- `deployment`: SaaS compartido, SaaS dedicado u **on-premise** (contenedores, base de datos y almacenamiento del cliente, sin telemetría externa si lo exige). Las llamadas a IA pueden ir por su propia cuenta de API o por proxy corporativo.

Regla: toda plantilla de salida lee primero el override del tenant, luego el default del producto.

## 13. Orden de disciplinas (todas las de construcción)

| Ola | Disciplina | Estado de partida en tu carpeta |
|---|---|---|
| 1 | **Eléctrica BT** | calc AEA, SLD, símbolos, láminas (en curso) |
| 2 | **Eléctrica MT** | símbolos SLD_MV/MLD_MV/SSD_MV ya existen |
| 3 | Protección y detección de incendio | pliegos Ford + `hazen_williams.py` |
| 4 | HVAC | pliegos + `hvac_airflow.py` |
| 5 | Civil / estructuras / arquitectura | pliegos civiles |
| 6 | Mecánica, termomecánica, cañerías | pliegos termomecánica |
| 7 | Instrumentación, control, telecomunicaciones | solo carpetas en el template |

Cada disciplina = un conjunto de plugins (`calc-*`, `drawing-*`, `spec-*`) que siguen el mismo contrato; el core no cambia.

## 14. Idiomas

Dos ejes distintos, que no se deben mezclar:

1. **Contenido del producto (código, schemas, claves, nombres de archivo, plugins, skills, prompts base, plantillas base):** **inglés**.
   - Se migra el contenido actual en español: claves de schema (`TENSION_V` → `voltage_v`), nombres de plugin/skill, IDs. Los códigos de proyecto (`PQ-nn`, `DEC-nnn`) se mantienen como identificadores neutrales.
2. **Idioma de salida para humanos:**
   - **Respuestas y explicaciones de Claude al usuario: español** (configurable por usuario; por defecto `es`). Se fija en las instrucciones del agente (`Respond to the user in Spanish`), no dentro de cada skill.
   - **Documentos generados** (memorias, pliegos, informes, rótulos): en el idioma del proyecto (`project.locale`), por defecto el de la jurisdicción (AR → `es-AR`).
   - **UI web/desktop:** catálogos de traducción (`en`, `es` al inicio; `pt`, etc. luego) con claves estables.

Mecánica i18n:
- `i18n/<locale>/*.json` por plugin (strings de UI y de plantillas); fallback `en`.
- Plantillas de documento por locale: `templates/<doc>/<locale>.md`.
- Terminología técnica con glosario por idioma (`glossary/es-AR.json`: *tablero*, *interruptor termomagnético*…) que Claude usa al redactar.
- Formatos regionales (decimal coma/punto, fechas, unidades) vienen del pack de jurisdicción y del locale.
- Regla de calidad: ningún string visible al usuario hardcodeado en el código.

## 15. Política de material con copyright y de assets de estudio

- Los PDF de normas y los pliegos de ejemplo (`elec-calc-generator/assets/*.pdf`, `sld-generator/assets/*.pdf`, `291_E…/assets/*.pdf`, `generar-pliego/knowledge/pdf/*.pdf`) son **material de estudio local**. No forman parte del producto.
- **Nunca se suben al repositorio.** Medidas:
  1. `.gitignore` global: `**/assets/**/*.pdf`, `**/knowledge/pdf/`, `*.pdf` salvo whitelist explícita (`!docs/**/*.pdf` si hiciera falta).
  2. Mover todo el material de estudio a una carpeta **fuera del repo**, p. ej. `E:\plugins\_study\` (o submódulo privado), y dejar en el repo solo un `STUDY_MATERIAL.md` con la lista de qué documento se usó para derivar qué tabla.
  3. **Hook de pre-commit y CI** que rechaza cualquier `.pdf`/`.dwg` no whitelisteado y falla si un archivo supera cierto tamaño.
  4. Si algún PDF ya se subió alguna vez a un remoto: limpiar historial (`git filter-repo`) antes de publicar.
- Lo que sí entra al repo: **tablas y reglas derivadas** en JSON, con referencia a cláusula y `source_status`. Evitar transcribir textos extensos de la norma.
- Los pliegos de clientes (p. ej. Ford) son datos confidenciales del cliente: se usan para aprender estilo en tu entorno, **no se versionan** y no deben pasar al producto.
- Cuando vendas: el producto no incluye normas; la organización cliente puede cargar las suyas a su propio espacio privado.

## 16. Plugin Hub único y protocolo de actualización

Objetivo: *"si modifico un plugin, lo reemplazo en un solo lugar y te digo qué hice"*.

```
E:\plugins\
 ├─ hub\                         ← ÚNICO lugar de plugins (fuente de verdad)
 │   ├─ aea-calc\                (cada uno con plugin.json, skills\, scripts\, tests\, CHANGELOG.md)
 │   ├─ iec-symbols\
 │   ├─ iram-titleblock\
 │   ├─ sld\   mld\   pliegos\   pm2-docs\ …
 │   └─ registry.json            ← índice: id, versión, ruta, dependencias, hash
 ├─ project-template\            ← sin copias de plugins; solo estructura + lockfile
 ├─ jurisdictions\  schemas\  core\
 └─ _study\                      ← PDFs de estudio (fuera de git)
```

Reglas:
1. **Una sola carpeta por plugin en `hub/`.** Sin `vendor/`, sin `plugin/` anidado, sin copia en el template. Los proyectos y otros plugins lo referencian por `id@versión` (lockfile `plugins.lock`).
2. Cuando modifiques un plugin: **reemplazas su carpeta en `hub/`** y me avisas ("actualicé `aea-calc`"). Yo entonces:
   - leo su `CHANGELOG.md` y `plugin.json`, comparo contra `registry.json`;
   - valido el schema y corro sus tests (golden);
   - detecto dependientes (`sld`, `mld`…) y reporto si se rompe un contrato;
   - actualizo `registry.json`, `plugins.lock` y subo la versión si corresponde.
3. Empaquetado `.plugin` (para Claude Code/Cowork) y servidores MCP se **generan** desde `hub/` con un script de build; nunca se editan a mano.
4. El template deja de traer `.claude/library/PLUGINS`: lee del hub (local) o del registro (web/desktop).

Pasos de migración: elegir la copia "buena" de cada plugin duplicado, moverla a `hub/`, borrar el resto tras tu confirmación (no borro nada sin ti).

## 17. Methodology Packs (PM² por defecto; PMI u otra a elección del usuario)

La gestión se separa del core en un paquete intercambiable:

```
methodologies/
  pm2/        # default: artefactos, fases (Initiating→Planning→Executing→Closing), gates, plantillas D01–D28
  pmi/        # PMBOK: charter, WBS, registros, performance domains, plantillas
  custom/     # plantilla vacía para metodología propia de una empresa
```

Cada pack define, en datos:
- `phases` y `gates` (con criterios),
- `artifacts` (catálogo de documentos, plantilla por idioma, disparador),
- `roles` y su mapeo a los roles del RBAC,
- `terminology` (p. ej. *Project Owner* ↔ *Sponsor*),
- `mappings` a entidades del PDM (cualquier metodología llena el mismo `Project/Package/Risk/Change/Decision`).

Consecuencias:
- Lo que hoy es el módulo M8/M10 del template pasa a ser `methodologies/pm2/`.
- El **flujo técnico de ingeniería** (paquetes, revisión, auditoría, emisión ifr/ifa/ifc) es independiente de la metodología: se queda en el workflow engine del core. La metodología solo cambia los artefactos y puertas de *gestión*.
- El usuario elige por proyecto (`project.methodology = "pm2" | "pmi" | "custom:<id>"`); la organización puede fijar un default.

## 18. Cambios al roadmap por estas decisiones

- **Ola 0 (higiene)** pasa a incluir: crear `hub/`, mover plugins, `.gitignore` anti-PDF, sacar el material de estudio a `_study/`, y **plan de migración a inglés** (inventario de claves/archivos en español).
- **Ola 1 (contratos)** añade: schema de `jurisdiction.json` y de `methodology.json`; extraer `aea_tables.json` y `rules/` a `jurisdictions/AR/`.
- **Ola 2 (kernel)** añade: loader de jurisdicción, loader de metodología, capa i18n.
- **Ola 3** sigue siendo cerrar la cadena BT; **Ola 4–5** (web, planes) mantienen Python+React, white-label y despliegue on-premise por contenedores.
- **MT** entra justo después de BT, reutilizando contrato y generadores (símbolos MV ya existen).

---

## 19. Estructura de carpetas profesional (creada en `epc-workspace/`)

### 19.1 Tres zonas con reglas distintas

```
epc-workspace/
├─ platform/        ← REPO GIT: el producto
│   ├─ core/  hub/  schemas/  i18n/{en,es}/  docs/  tests/golden/
│   ├─ jurisdictions/{_template, AR/{electrical,civil,hvac,fire,mechanical,instrumentation,telecom}}
│   ├─ methodologies/{pm2,pmi,custom}
│   ├─ apps/{cli,mcp,api,web,desktop}
│   └─ tools/{hooks,ci,build}
├─ local/dev-knowledge/   ← NUNCA versionado ni subido (ni siquiera git init)
│   ├─ _inbox/                         zona de descarga: lo nuevo, sin clasificar
│   ├─ standards/<PAÍS>/<ID-NORMA>/{source,extracted,analysis,draft}/ + standard.json
│   ├─ third-party-reports/            informes de otras empresas
│   ├─ reference-specs/                pliegos de ejemplo (estilo)
│   ├─ training-material/{drawings,calculations}/   (tus sld_*.pdf, etc.)
│   └─ notes/
└─ projects/<CLIENTE>/<PROYECTO>/      ← ver 19.3
```

### 19.2 Carga de normas por país → `rules.json` por norma

Flujo (documentado también en `local/dev-knowledge/README.md`):

```
local/dev-knowledge/standards/AR/AEA-90364-7-771/
   source/      PDF original               (copyright; se queda aquí)
   extracted/   texto y tablas extraídos   (generado)
   analysis/    índice de cláusulas y notas de Claude, en español  (generado)
   draft/       rules.json borrador + informe de dudas             (generado)
   standard.json  metadatos: id, ente, edición, idioma, dominio, licencia, estado
```

1. Dejas el PDF en `source/` (o en `_inbox/` y Claude lo clasifica por país).
2. Claude extrae y analiza → `extracted/` y `analysis/`.
3. Claude genera `draft/rules.json` según `platform/schemas/rules.schema.json`: cada regla lleva **cláusula, tema, tipo (parámetro/tabla/fórmula/restricción), valor, unidad, severidad y confianza**; el campo `summary` está limitado a 240 caracteres para evitar transcribir la norma.
4. Tú validas → `source_status: verified` (con `validated_by` y fecha).
5. **Promoción** a `platform/jurisdictions/AR/<dominio>/<ID-NORMA>/rules.json`. La puerta rechaza borradores sin validar y textos largos.
6. Un plugin de cálculo carga las reglas por jurisdicción + norma, sin saber de dónde vinieron.

Esto reemplaza lo que hoy es `aea_tables.json` + `rules/` dentro de `elec-calc-generator`. Se hará un plugin `standard-ingest` en `hub/` que automatiza los pasos 2–3 y 5.

### 19.3 Proyecto: entorno editable vs. entregables

```
projects/<CLIENTE>/<PROYECTO>/
├─ .epc/                      estado de la plataforma
│   ├─ project.json           (cliente, jurisdicción, idioma, metodología, disciplinas)
│   ├─ plugins.lock           versiones exactas de plugins usados
│   ├─ ledger/                manifiestos SHA-256 de cada transición
│   └─ state/
├─ workspace/                 ← EDITABLE · INTERNO · GIT
│   ├─ 00-setup/              datos de partida
│   ├─ 01-input/              documentación recibida del cliente
│   ├─ 02-engineering/<disciplina>/<PQ-nn>/
│   │      ├─ src/            fuentes (Excel, md, parámetros)
│   │      ├─ calc/           resultados *.json (internos)
│   │      ├─ drawings/svg/   SVG de trabajo → versionado en git, NUNCA se entrega
│   │      ├─ drawings/dxf/   DXF maestro → se edita aquí, se entrega una copia sellada
│   │      ├─ docs/           fuentes md → se entregan como pdf/docx
│   │      └─ build/          temporales (ignorado)
│   ├─ 03-review/             paquetes y hojas de revisión
│   ├─ 04-audit/              auditoría
│   ├─ 05-management/         documentos de gestión (según la metodología)
│   └─ 06-staging/            aprobado y congelado, listo para publicar
├─ deliverables/              ← CLIENTE · SOLO LECTURA · generado únicamente por "publicar"
│   ├─ ifr/  ifa/  ifc/  as-built/
│   └─ transmittals/
└─ _out/                      cachés y renders temporales (fuera de git)
```

Mapeo con tu template actual: `01-input`→`workspace/01-input`, `02-engineering`→igual, `03-review`/`04-audit` iguales, `05-released`→`workspace/06-staging`, `06-deliverables`→`deliverables/`, `90-management`→`workspace/05-management`. La diferencia clave es que **ahora hay una frontera física**: todo lo que está bajo `workspace/` es de trabajo; todo lo que está bajo `deliverables/` ya salió.

### 19.4 Política de entregables (`platform/schemas/deliverable-policy.json`)

| Formato | Rol | ¿Se entrega? | ¿Git? |
|---|---|---|---|
| `.svg` | fuente interna de trabajo | **Nunca** | Sí |
| `.dxf` | editable entregable | **Sí**, copia sellada tal cual | Sí (maestro) |
| `.dwg` | editable entregable (lo dibuja el usuario) | Sí | No (LFS o fuera de git) |
| `.xlsx` | editable entregable | Sí | Sí |
| `.md` | fuente de documentos | No (se entrega como pdf/docx) | Sí |
| `.pdf` | entregable final, se genera al publicar | Sí | No |
| `.docx` | entregable editable, se genera desde md | Sí | No |
| `.json`, `.log` | datos internos / temporales | No | json sí, log no |

Cada plugin declara en su `plugin.json` qué salidas produce y su canal: `internal` o `internal+deliverable`. Ejemplo: `sld` → `svg: internal`, `dxf: internal+deliverable`.

**Publicar** (`publish`) es una copia unidireccional:
- origen: `workspace/06-staging` (solo paquetes en estado `RELEASED`);
- destino: `deliverables/<emisión>/<TR-nnn>_Rev<cliente>/<disciplina>/…`;
- sella revisión del cliente (`Rev 00`), revisión interna, SHA-256, versión del motor y de los plugins;
- los entregables son inmutables: un cambio genera nueva emisión, nunca se edita en `deliverables/`.

### 19.5 Protecciones para que lo privado no se suba
- `platform/.gitignore` bloquea `*.pdf`, `*.dwg`, `local/dev-knowledge/`, `_study/`, `**/knowledge/`.
- Hook `platform/tools/hooks/pre-commit` (activar con `git config core.hooksPath tools/hooks`): rechaza PDF/DWG y archivos de más de 5 MB.
- `local/dev-knowledge/` está fuera del repo; no se le hace `git init`.
- CI repetirá las mismas comprobaciones (Ola 0/1).
- Los plugins actuales que traen PDF (`assets/*.pdf`, `knowledge/pdf/`) se moverán a `local/dev-knowledge/` al migrar (no borro nada sin tu confirmación).

---

## 20. Skills en un lugar, plugins en otro (los plugins gobiernan)

Decisión: `platform/skills/` contiene **todas** las skills; `platform/hub/` contiene **todos** los plugins. Los plugins gobiernan.

```
platform/
 ├─ hub/<plugin-id>/     plugin.json (gobierna) · scripts/ · data/ · tests/ · CHANGELOG.md
 └─ skills/<skill-id>/   SKILL.md · references/ · templates/
```

Qué significa "gobiernan":
1. Cada skill tiene **un solo plugin dueño** (`role: owner`); otros plugins pueden usarla como `consumer`.
2. Una skill que ningún plugin lista está **inactiva**: no se construye ni se ofrece al agente.
3. Versión, dependencias, permisos, plan de suscripción (`entitlement`), salidas (internas o entregables) e idioma los define el plugin. El `overrides` del plugin gana sobre los valores por defecto de la skill.
4. Scripts y datos viven en el plugin; la skill los invoca a través de él, nunca trae su propia copia.
5. El schema está en `platform/schemas/plugin.schema.json`.

Ejemplo (`hub/aea-calc/plugin.json`, fragmento):

```jsonc
"skills": [
  { "id": "size-feeder",          "version": "^1.6", "role": "owner" },
  { "id": "dimension-board",      "version": "^1.6", "role": "owner" },
  { "id": "write-calculation-memo","version": "^1.6", "role": "owner",
    "overrides": { "language": "es-AR", "jurisdiction": "AR" } },
  { "id": "apply-titleblock",     "version": "^0.5", "role": "consumer" }
]
```

Consecuencia técnica: Claude Code espera `skills/` dentro del `.plugin`. Para eso el paso `tools/build` **arma cada paquete copiando** las skills que el plugin lista desde `platform/skills/`. La fuente única sigue siendo `platform/skills/`; las copias dentro de un paquete construido se regeneran y no se editan.

Tu protocolo no cambia: reemplazas una skill en `skills/` o un plugin en `hub/`, me avisas, y yo valido que cada skill tenga dueño, que las versiones resuelvan y que no queden skills huérfanas.

### Skills actuales y su plugin dueño propuesto (nombres en inglés)

| Skill actual | Skill id propuesto | Plugin dueño |
|---|---|---|
| `feeder-sizing` | `size-feeder` | `aea-calc` |
| `electrical-dimensioning` | `dimension-installation` | `aea-calc` |
| `calculation-memo` (y `memoria-calculos`) | `write-calculation-memo` | `aea-calc` |
| `memo-summary` (y `sintesis-memoria`) | `write-memo-summary` | `aea-calc` |
| `sld-generator` / `create-electrical-line-diagram` | `generate-sld` | `sld` |
| `convert-sld-to-mld` | `convert-sld-to-mld` | `mld` |
| `generate-electrical-symbol` | `generate-electrical-symbol` | `iec-symbols` |
| `iram-titleblock-custom-generator` / `generate-laminas-iram` | `generate-titleblock-sheet` | `iram-titleblock` |
| `generar-pliego` | `generate-specification` | `spec-writer` |
| `create-pm2-document` | `create-management-document` | `pm2-docs` |
| `get-cotizacion` | `request-quotation` | `procurement` |

### 20.1 Regla de duplicados: gobierna la copia del plugin, y se advierte

Si una skill existe en `platform/skills/` **y** dentro de un plugin (`hub/<plugin>/skills/<id>/`), **gobierna la del plugin**. Claude te lo advierte siempre, para resolverlo antes de producción:

| Situación | Desarrollo | Producción |
|---|---|---|
| Skill duplicada (central + plugin), igual o distinta | **ADVERTENCIA**: indica cuál gobierna y si el contenido difiere | **ERROR**: el build se bloquea hasta dejar una sola copia |
| Misma skill dentro de dos plugins | ERROR | ERROR |
| Skill sin plugin que la liste (huérfana) | ADVERTENCIA | ADVERTENCIA |
| Plugin que lista una skill inexistente | ERROR | ERROR |

Implementado en `platform/tools/ci/check_skill_conflicts.py` (probado con un caso simulado; sobre la plataforma real, que aún está vacía, no encuentra nada). Cuando me avises que reemplazaste una skill o un plugin, lo ejecuto y te informo en español qué encontró y qué copia gobierna.

---

## 21. Motor de reglas (implementado, 2026-10-23)

Piezas:
- **`core/rules/epc_rules`** (stdlib): `RuleSet.load(jurisdiction, domain, env)`, `query(topic, standard, clause_prefix, installation_type)`, `check(context)`, `lookup(tabla, ...)`. En `env=production` solo ve normas `verified`; en `dev` puede leer borradores de `local/dev-knowledge`. `check` devuelve PASS / FAIL / SKIP; nunca adivina un dato faltante (lo informa como SKIP).
- **`hub/standard-ingest`** + skill **`analyze-standard`**: `extract_standard.py` (texto y índice de cláusulas), `render_pages.py` (PNG de páginas para normas escaneadas), `validate_rules.py` (schema, id duplicados, tablas, cláusula presente en el texto, **rechazo de copia textual de 12+ palabras**), `promote_rules.py` (compuerta a `jurisdictions/`), `import_legacy_rules.py`.
- **`schemas/rules.schema.json` 1.1**: regla = id, cláusula, página, tema, resumen parafraseado por idioma (≤240), tipo (mandatory/recommended/prohibited), aplica a (tipos de inmueble + condiciones), parámetros, `check` ejecutable, tablas, `evidence_ref`. La cita textual queda privada en `local/dev-knowledge/.../analysis/evidence.json`.

Flujo: `PDF en local/dev-knowledge → extract → Claude redacta draft/rules.json → validate → tú validas → promote → jurisdictions/AR/<dominio>/<norma>/rules.json → los plugins de cálculo consultan el motor`.

Estado de los datos: las 177 reglas que ya tenías en `aea-calc/scripts/rules` quedaron importadas como **borradores** de 6 normas (7-771: 82, 5: 55, 4: 16, 7-701: 12, 7-770: 6, 7-722: 6) con 16 tablas. 49 reglas tienen un `check` derivado del nombre del parámetro (`*_min`/`*_max`) que debes confirmar. Seis resúmenes que copiaban la norma se reescribieron. Las normas 90364-2, -4, -4-42, -5 y 90909-1 son escaneadas (sin texto): se leen visualmente.

Pendiente: (1) tu validación de los borradores; (2) que `aea-calc` consulte el motor en vez de `aea_rules.py`; (3) pasar `aea_tables.json` (tablas de capacidad) al mismo formato; (4) traducir ids y parámetros al inglés; (5) reglas de MT, incendio, etc. con la misma skill.
