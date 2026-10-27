# Guía para agregar normas nuevas (AEA 90364, IEC 60364, NFPA, IRAM…)

> Documento autocontenido: se puede pegar entero en otro chat. Explica cómo entra una norma a la plataforma **sin distribuirla**, en qué formas se convierte (reglas verificables, tablas, fórmulas, criterios de diseño), qué comandos se usan, cómo se valida y se aprueba, y **qué límites tiene hoy el sistema** (están marcados como "Estado actual").
> Fuentes en el repositorio: `docs/explanation/knowledge.md`, `ADR-0011`, `ADR-0012`, `engine/standards`, `engine/rules`, `engine/jurisdictions`, `shared/schemas/rules.schema.json`, `claude/skills/analyze-standard/SKILL.md`.
> El código, los ids, los esquemas y los parámetros van **en inglés**; el texto de resumen de cada regla va por idioma (`es`, `en`); a quien usa el programa se le explica en español.

---

## 1. Idea central: Claude lee una vez, Python calcula siempre

Una norma es un PDF con copyright. La plataforma **no lo distribuye ni lo copia**: lo estudia una vez y deja lo aprendido como **datos y código propios**, con una referencia (norma, edición, cláusula, página) para que cualquiera pueda ir a la fuente.

| Capa | Qué es | Dónde vive | ¿Se versiona? |
|---|---|---|---|
| 1. Fuente | El PDF de la norma y el material de estudio | `local/dev-knowledge/standards/<CC>/<ID>/` | **Nunca** (carpeta ignorada, `*.pdf` bloqueado por el hook de git) |
| 2. Conocimiento extraído | Lo entendido, redactado con palabras propias como datos estructurados | `engine/jurisdictions/<CC>/<dominio>/<ID>/rules.json`, tablas y constantes del motor, `design-criteria.json` | Sí |
| 3. Ejecución | Código que aplica ese conocimiento | `engine/rules` (reglas verificables), `engine/calc` (fórmulas y tablas), módulos del backend `knowledge` y `norms` | Sí |

Una norma, según lo que contenga, se convierte en **cuatro cosas** (una norma real suele dar varias):

| Contenido de la norma | En qué se convierte | Quién lo usa | Sección |
|---|---|---|---|
| Requisitos que se pueden comprobar ("reserva ≥ 20 %", "altura ≤ 1,8 m") | `rules.json` con `check` | `epc_rules`, API `/api/rules`, skills | 4 |
| Tablas y constantes numéricas (capacidad de corriente, factores) | JSON de datos del motor, con la cláusula al lado | `epc_calc` | 5 |
| Fórmulas (caída de tensión, corriente admisible, cortocircuito) | Función Python pura + test con ejemplo resuelto | `epc_calc` | 5 |
| Valores que el ingeniero elige por proyecto (alturas, límites de caída) | Catálogo `design-criteria.json` | pipeline de diseño, pantalla de criterios | 6 |

---

## 2. Reglas de oro (no negociables)

1. **Copyright.** Ningún PDF, página escaneada ni texto copiado entra al repositorio. Una regla lleva la **referencia** (cláusula y página), un **resumen parafraseado** de hasta 240 caracteres por idioma y **parámetros numéricos**. El validador rechaza cualquier resumen que comparta **12 o más palabras seguidas** con el texto de la fuente.
2. **Nunca inventar valores.** Cada número sale de la norma. Si es ilegible o ambiguo: baja la `confidence`, marca `verification` y anótalo como duda para el revisor humano.
3. **Claude redacta, el humano valida.** `source_status` queda en `draft` hasta que el revisor diga que validó. Solo entonces se promueve. **Producción usa únicamente lo `verified`.**
4. **Una sola fuente por dato (ADR-0012).** Un valor de norma vive en un archivo; todo lo demás lo lee. El gate falla si dos archivos versionados tienen el mismo contenido.
5. **Python hace las cuentas, no el modelo.** Un requisito con límite numérico es un `check`; una fórmula es una función con test; una tabla es un dato consultado por código.
6. **Idioma.** Ids, temas, parámetros y `title` en inglés; `summary` por idioma (`es` para Argentina). La cita literal, si hace falta para trazabilidad, va **solo** en `analysis/evidence.json`, dentro de `local/` (privado).
7. **Lo privado no viaja.** El hook de git rechaza PDF/DWG, archivos de más de 5 MB y cualquier cosa de `local/dev-knowledge/`.

---

## 3. Preparar la norma (una vez por norma)

### 3.1 Identificador y carpeta
Convención de id: `<ENTE>-<número>[-parte]`, por ejemplo `AEA-90364-7-771`, `IEC-60364-5-52`, `NFPA-70`, `IRAM-2178`.
País: código ISO 3166 alfa-2 (`AR`, `US`) o `INTL` para IEC/ISO.

```
local/dev-knowledge/standards/<CC>/<ID>/
├── source/                 # el PDF (nunca versionado)
│   └── <archivo>.pdf
├── standard.json           # metadatos (lo creas tú)
├── extracted/              # lo genera el extractor
├── draft/rules.json        # el borrador que redacta Claude
└── analysis/evidence.json  # citas literales privadas (opcional)
```

`standard.json` (ejemplo real del repositorio):
```json
{
  "id": "IEC-60364-5-52",
  "country": "INTL",
  "body": "IEC",
  "title": "Selection and erection of electrical equipment — Wiring systems",
  "edition": "2009",
  "language": "en",
  "domain": "electrical",
  "license": "copyrighted-internal-study-only",
  "status": "draft",
  "source_files": ["source/IEC_60364-5-52.pdf"],
  "notes": ""
}
```
Si el PDF llegó a `local/dev-knowledge/_inbox/`, muévelo a `source/`.

### 3.2 Extraer el texto
```
set PYTHONPATH=engine/standards/src;engine/rules/src        (en Windows; en bash usa ":")
python -m epc_standards.extract_standard INTL/IEC-60364-5-52
```
Escribe en `extracted/<pdf>/`: `pages/pNNNN.txt`, `extraction.json` (modo `text | scanned | mixed`), `clauses.json` (cláusulas detectadas), `tables.json` (títulos de tablas), `needs_vision.json`.
- Si el PDF es **escaneado** (sin capa de texto), no se extrae texto: se leen las páginas como imágenes. Renderiza con `python -m epc_standards.render_pages <pdf> 41-45` y marca esas reglas con `verification: "visual"` (u `"ocr"`).

### 3.3 Acordar el alcance
Una norma de 300 páginas no se redacta de una vez. Lista con el responsable los **capítulos o cláusulas** a cubrir en esta pasada (circuitos, protección, conductores, puesta a tierra…) y trabaja capítulo por capítulo. Skill de apoyo: `analyze-standard`.

---

## 4. Camino A: requisitos verificables → `rules.json`

### 4.1 Redactar `draft/rules.json` (esquema `shared/schemas/rules.schema.json`, versión 1.1)

Estructura mínima:
```json
{
  "schema_version": "1.1",
  "standard": {"id": "IEC-60364-5-52", "country": "INTL", "body": "IEC", "edition": "2009", "domain": "electrical", "title": "…", "extends": ""},
  "source_status": "draft",
  "tables": [],
  "rules": []
}
```

Una **regla** (un requisito = una regla):
```json
{
  "id": "trays.reserve_pct",
  "clause": "521.4",
  "page": {"printed": 67, "pdf": 71},
  "topic": "trays",
  "title": "Reserve in cable trays",
  "summary": {"es": "El ancho de la bandeja deja una reserva mínima del 20 % para cables futuros.",
              "en": "Tray width leaves at least 20 % spare capacity for future cables."},
  "type": "mandatory",
  "applies_to": {"installation_types": ["dwellings", "offices"], "when": {"room_type": "bathroom"}},
  "params": {"reserve_min_pct": 20},
  "check": {"field": "tray_reserve_pct", "op": ">=", "value": 20},
  "table_ref": "",
  "evidence_ref": "trays.reserve_pct",
  "verification": "text",
  "confidence": "high"
}
```
Reglas del formato:
- `id`: estable, con puntos (`grupo.nombre`), en inglés. No lo cambies después de promover: otros datos pueden referirlo.
- `clause`: **solo el número** de cláusula, nunca su texto. `page`: la impresa y la del PDF.
- `topic`: grupo con puntos (`trays`, `bathrooms`, `earthing.electrodes`).
- `summary.<idioma>`: paráfrasis ≤ 240 caracteres, **no transcripción**.
- `type`: `mandatory | recommended | prohibited`.
- `params`: valores máquina con la **unidad en el sufijo** de la clave (`_m`, `_mm`, `_mm2`, `_pct`, `_a`, `_v`, `_ma`).
- `check`: solo cuando el requisito es una **comparación limpia** sobre un campo con nombre del contexto (`==`, `!=`, `<`, `<=`, `>`, `>=`, `in`, `not_in`). Si se deduce mecánicamente de un `*_min/_max`, marca `derived: true` (necesita confirmación humana). Un requisito informativo **no lleva** `check`.
- `applies_to.when`: condiciones sobre el contexto de evaluación (escalar = igual, lista = pertenece, o `{lt,le,gt,ge,ne,in,not_in}`).
- `verification`: `text | ocr | visual | unverified`; `confidence`: `low | medium | high`.
- `overrides`: id de una regla de otra norma que esta reemplaza (ver 8).
- **Tablas numéricas** en `tables[]` (`id`, `clause`, `columns`, `rows`, `notes`) y se referencian con `table_ref`; cada fila tiene tantas celdas como columnas.

### 4.2 Validar
```
python -m epc_standards.validate_rules local/dev-knowledge/standards/INTL/IEC-60364-5-52/draft/rules.json --standard-dir local/dev-knowledge/standards/INTL/IEC-60364-5-52
```
- **ERROR** (bloquea): incumple el esquema, ids repetidos, `table_ref` inexistente, fila que no calza con las columnas, resumen con 12+ palabras copiadas, operador inválido.
- **WARN** (revisar): cláusula no encontrada en el texto extraído, regla sin `check` ni `params`, `check` derivado sin confirmar, `evidence_ref` ausente en `evidence.json`.
- Código de salida 1 si hay algún ERROR.

### 4.3 Revisión humana
Entrega al revisor una lista corta (en español) de: reglas con `confidence: low`, checks derivados, páginas leídas visualmente y dudas abiertas. **No promuevas por tu cuenta.**

### 4.4 Promover (solo después de la validación humana)
```
python -m epc_standards.promote_rules INTL/IEC-60364-5-52 --mark-verified "Nombre del revisor"
```
Puerta de la promoción: pasa la validación sin ERROR; `source_status == "verified"` con `validated_by` y `validated_on` (el flag `--mark-verified` sella nombre y fecha **solo** cuando el humano dijo que validó); nada del PDF ni de `evidence.json` viaja.
Resultado: `engine/jurisdictions/<CC>/<dominio>/<ID>/rules.json`, un `promotion.json` junto al borrador y la norma queda listada en `engine/jurisdictions/<CC>/jurisdiction.json`.

### 4.5 Usarlas
```python
from epc_rules import RuleSet
rs = RuleSet.load("AR", "electrical", env="production")      # production = solo "verified"
rs.query(topic="trays", installation_type="dwellings")
report = rs.check({"tray_reserve_pct": 15}, installation_type="dwellings")   # PASS / FAIL / not evaluated
```
- Un dato que falta **se informa, nunca se adivina** (`passed: None`, con el motivo).
- CLI: `python -m epc_rules list|query|check`. Backend: `/api/rules` (solo consola de administración). En desarrollo se pueden leer borradores con `--drafts local/dev-knowledge`.

---

## 5. Camino B: fórmulas y tablas → `epc_calc`

Aplica a normas con cálculo (la AEA 90364-7-771 es el ejemplo hecho; la IEC 60364-5-52 sería el siguiente).

1. **Tablas y constantes** → un JSON de datos dentro de `engine/calc/src/epc_calc/` (hoy `aea_tables.json` con las secciones `tablas_capacidad`, `factores_correccion`, `constantes` y un bloque `meta` con norma, origen, estado y unidades). **Cada valor lleva la cláusula al lado.** Un cargador con caché (`aea_tables.cargar()` y `limpiar_cache_tablas()`) las expone; el código **no** trae números normativos sueltos.
2. **Reglas del motor de cálculo** → `engine/calc/src/epc_calc/rules/*.json` (una por requisito, con `fuente`: norma, edición, cláusula, página; sin texto de la norma), indexadas en `_indice.json`.
3. **Fórmulas** → función **pura** en un módulo de `epc_calc`, con el docstring que ya usan los demás: `OBJETIVO`, `FÓRMULAS`, `UNIDADES`, `LIMITACIONES`, `NORMA DE REFERENCIA` y la marca `[VERIFICAR]` mientras no esté validada.
4. **Prueba con ejemplo resuelto** en `engine/calc/tests/`: el número esperado está calculado a mano de la norma (no del propio código). Sin test, la fórmula no entra.
5. **Catálogo de módulos** (`aea_catalog.py`): agrega la línea del módulo con su norma y resumen para que aparezca en la documentación del motor.

### Estado actual (honesto)
- El motor de cálculo está escrito **para AEA**: los módulos se llaman `aea_*` y las tablas son las de AEA 771. **No hay todavía un selector de norma** (por ejemplo "calcular con IEC 60364-5-52 en vez de AEA"). Agregar IEC al cálculo exige **diseñar ese selector**.
- Camino recomendado (hay que escribirlo en un ADR antes de implementarlo): una **política por norma** como dato (límites, factores, constantes, con norma y cláusula) cargada por una fábrica; los algoritmos reciben la política y no números sueltos; agregar una norma pasa a ser declarar datos. Mínimo viable: un archivo de datos por norma (`iec_tables.json`) + un criterio de diseño `standard` + un parámetro `norm` en la tubería de cálculo que elige qué archivo leer.
- Mientras tanto, lo que sí se puede hacer sin tocar el motor: ingerir IEC como `rules.json` (camino A) para **consulta y verificación**, y agregar sus tablas como datos nuevos.

---

## 6. Criterios de diseño (valores por proyecto)

Catálogo `engine/jurisdictions/<CC>/<dominio>/design-criteria.json` (hoy `AR/electrical`):
```json
{
  "schema_version": "1.0",
  "jurisdiction": "AR",
  "discipline": "electrical",
  "validated": false,
  "note": "Starting values proposed by the platform. They are NOT validated against the standards…",
  "criteria": [
    {"id": "socket_height_m", "group": {"en": "Mounting heights", "es": "Alturas de montaje"},
     "label": {"en": "Socket outlets height", "es": "Altura de tomacorrientes"},
     "unit": "m", "type": "number", "min": 0.1, "max": 2.0, "default": 0.3},
    {"id": "frequency_hz", "group": {"en": "Supply", "es": "Alimentación"},
     "label": {"en": "Frequency", "es": "Frecuencia"}, "unit": "Hz", "type": "choice", "options": [50, 60], "default": 50}
  ]
}
```
- `type`: `number` (con `min`/`max`) o `choice` (con `options`); el `default` debe caer dentro de ellos.
- Etiquetas `{"en","es"}`; la unidad va en `unit` y en el sufijo del `id`.
- El catálogo se marca `validated: true` **solo** mientras **todos** sus criterios estén aprobados. Un proyecto puede sobrescribir cualquiera (`<proyecto>/workspace/00-setup/design-criteria.json`).
- Un criterio nuevo de una norma nueva va aquí, no en el código.

---

## 7. Revisión y aprobación punto por punto (ADR-0011)

- Rol de plataforma `standards` (el **revisor de normas**): una cuenta sin organización que solo alcanza `/api/norms/*`. La crea un administrador (`python -m epc.modules.identity.cli create-admin --role standards`).
- El módulo `norms` lista los **puntos** (una regla, una tabla o constante, un criterio) y permite **corregir** el valor (se reescribe en el archivo de datos con su propio formato, para que git muestre solo ese cambio) y **aprobar** o **marcar** con una nota.
- Estados: **pendiente** hasta aprobar; la aprobación guarda quién, cuándo, nota y la **huella** del valor aprobado en `engine/jurisdictions/AR/review.json`, y cada acción se agrega a `review-log.jsonl`. Un valor que cambia por otra vía después de aprobar (por ejemplo un merge) aparece como **desactualizado** y pide nueva aprobación.
- El revisor corrige **valores, no estructura**: las reglas conservan sus campos y tipos; las tablas, sus claves y tamaños.

### Estado actual (honesto)
- La pantalla de revisión cubre hoy los **datos de cálculo AEA** (reglas de `epc_calc`, tablas/constantes, criterios de diseño). Las `rules.json` ingeridas con `epc_standards` se validan con `validate_rules` y `--mark-verified`, pero **aún no tienen pantalla de revisión punto por punto**.
- No hay flujo de **dos aprobadores**.
- En la imagen de contenedor (solo lectura) la revisión se hace en la copia de desarrollo y se versiona.

---

## 8. Jurisdicciones, normas internacionales y relación entre normas

- Una **jurisdicción** es una carpeta `engine/jurisdictions/<CC>/` con `jurisdiction.json` (copiado de `_template`): `id`, `name`, `default_locale`, `currency`, `frequency_hz`, `standards_bodies`, `voltages_lv`, `status`, `packs`. Las **subcarpetas** de dominio (`electrical`, `hvac`, `fire`, `civil`, `mechanical`, `instrumentation`, `telecom`) son las **disciplinas** que la creación de proyecto ofrece para ese país.
- Una norma nueva de un país ya existente: se promueve a `engine/jurisdictions/<CC>/<dominio>/<ID>/rules.json`.
- **IEC/ISO (internacional):** el esquema acepta `country: "INTL"`. En el repositorio solo existe `INTL` en el material privado (`local/dev-knowledge`); **no hay** `engine/jurisdictions/INTL/` todavía. Crearlo implica un `jurisdiction.json` propio y que `INTL` aparezca como opción al crear un proyecto.
- **Relación entre normas:** el esquema define `standard.extends` (norma base) y `rule.overrides` (id de la regla que se reemplaza). 
  - `overrides` **funciona** dentro de una misma jurisdicción (`RuleSet` descarta la regla reemplazada).
  - **Estado actual:** `extends` está en el esquema pero **el cargador no lo resuelve**, y `RuleSet.load("AR")` solo lee `jurisdictions/AR/*/*/rules.json`. Para que un proyecto argentino vea las reglas de IEC hay que implementar carga de varias jurisdicciones o la resolución de `extends`. Es un cambio del motor `epc_rules` con su ADR y sus tests.

---

## 9. Pruebas y puertas de calidad

| Qué | Cómo |
|---|---|
| Un `rules.json` | `validate_rules` (esquema, ids únicos, tablas, cláusula existente, copia literal) |
| Promoción | `promote_rules` (bloquea si hay ERROR o no está verificada) |
| Motor de reglas | `engine/rules/tests` (`python -m unittest discover -s tests` con `PYTHONPATH=src`) |
| Pipeline de ingesta | `engine/standards/tests` |
| Fórmulas y tablas | `engine/calc/tests`: ejemplo resuelto a mano por cada función |
| Todo junto | `python tools/ci/run_gate.py` en verde (hoy 35/35): `engine-rules`, `engine-standards`, `engine-calc`, `single-source`, `coverage`, `complexity` |

Una norma que **solo** agrega datos (sin código) igual pasa por `single-source` (sin duplicados) y por el hook (sin PDF ni material privado).

---

## 10. Plan de trabajo sugerido para una norma de la familia 90364 / 60364

1. Crear la carpeta `local/dev-knowledge/standards/<CC>/<ID>/source/` y su `standard.json` (sección 3).
2. Extraer (3.2) y acordar el alcance por capítulos (3.3).
3. Por capítulo: redactar `draft/rules.json` (4.1), validar (4.2), pasar la lista de dudas al revisor (4.3).
4. Mientras tanto, para lo que tenga **tablas o fórmulas**: datos con cláusula + función + test con ejemplo resuelto (sección 5).
5. Valores por proyecto → `design-criteria.json` (sección 6).
6. Con la validación humana: `promote_rules --mark-verified` (4.4).
7. Si es una norma de otro ente (IEC, NFPA): decidir **jurisdicción** (sección 8) y, si debe usarse en el cálculo, escribir el **ADR del selector de norma** (sección 5).
8. Línea en `CHANGELOG.md`; si cambió código, ADR y gate en verde; fusionar con `--no-ff` y **sin subir a GitHub** hasta que el dueño lo pida.

Orden razonable de capítulos para 60364: **4** (protección: contactos, sobrecorriente), **5-52** (canalizaciones y conductores), **5-54** (puesta a tierra), **5-53** (aparamenta), luego los **7-xxx** (locales especiales).

---

## 11. Prompt sugerido para el otro chat

> Voy a incorporar la norma **<ID>** (`<país>`, edición `<año>`, dominio `<dominio>`) a la plataforma EPC-291 sin distribuirla. El PDF queda en `local/dev-knowledge/standards/<CC>/<ID>/source/` y no se versiona. Quiero `draft/rules.json` (esquema 1.1 de `shared/schemas/rules.schema.json`) **capítulo por capítulo**: una regla por requisito con `id` en inglés, `clause`, `page`, `topic`, `summary` parafraseado (≤240 caracteres por idioma, nunca 12 palabras seguidas de la fuente), `type`, `applies_to`, `params` con la unidad en el sufijo y `check` solo cuando sea una comparación limpia; tablas en `tables[]`. Nunca inventes valores: si algo es ilegible baja `confidence`, marca `verification` y anótalo como duda. Valida con `python -m epc_standards.validate_rules` y entrégame una lista corta en español de dudas, checks derivados y páginas leídas visualmente. **No promuevas**: solo lo hago yo tras validar. Para lo que tenga tablas o fórmulas, propón datos con cláusula + función pura + test con ejemplo resuelto en `engine/calc`. Capítulos de esta pasada: **<lista>**.

---

## 12. Qué decirme al volver

Para dejarlo integrado necesito: el **id y la edición** de la norma, el **dominio**, qué **capítulos** quedaron hechos, cuántas **reglas** hay y cuántas con `confidence` baja, qué **tablas/fórmulas** se agregaron (y a qué módulo), qué **criterios de diseño** nuevos hay, y si debe **usarse en el cálculo** (lo que dispara el ADR del selector de norma) o solo para **consulta y verificación**.
