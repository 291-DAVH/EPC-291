# Guía para construir un motor compatible con EPC-291

> **Estado del documento.** Describe lo que **existe hoy** y, marcado como **(objetivo)**, lo que fija el ADR-0028 (selector de norma, aún propuesto). Para el procedimiento de ingesta de una norma ver [GUIA_NORMAS.md](GUIA_NORMAS.md).

> Documento autocontenido: se puede pegar entero en otro chat. Explica qué es un motor en esta plataforma, cómo se estructura, qué recibe y qué entrega, qué patrones de diseño sigue, cómo se prueba y **todos los lugares del repositorio que hay que tocar para registrarlo**. Los motores de referencia son `engine/arch` (el más limpio y aislado), `engine/plan` (documento JSON de entrada, esquema, trabajos en segundo plano) y `engine/aea90364` (tablas como datos).
> El código, los comentarios, los identificadores, los esquemas y los textos del producto van **en inglés**; la explicación al usuario, en español.

---

## 1. Qué es un motor

Un motor es una **librería Python pura** que hace un trabajo de ingeniería. Vive en `engine/<area>/` y se importa como `epc_<area>`.

Reglas que lo definen (el gate las verifica casi todas):

1. **Sin web, sin Claude, sin base de datos.** No importa `epc` (el backend), ni `fastapi`, ni nada del frontend. El backend lo orquesta; los plugins de Claude lo empaquetan; la futura app de escritorio lo embebe.
2. **Se instala solo.** Tiene su propio `pyproject.toml`, sus tests y su README. Se puede copiar la carpeta a otro lugar y funciona.
3. **Puro y determinista.** La misma entrada da la misma salida. Sin red, sin reloj, sin estado global mutable, sin efectos al importar (nada de leer `argv`, variables de entorno, archivos o lanzar procesos al hacer `import`).
4. **Los datos son datos.** Umbrales, tablas, perfiles, reglas y catálogos viven en JSON dentro del paquete, no como constantes en el código. Cada dato tiene **una sola fuente** (ADR-0012): nada de copias.
5. **No importa a sus hermanos** salvo lo que permite la capa en que se declare (sección 9). Un motor nuevo que no necesite a nadie queda en la capa de los independientes.
6. **Dos formas de usarlo:** como función Python (`import epc_<area>`) y como comando (`python -m epc_<area> ENTRADA --out DIR`). El backend usa una u otra según el caso (sección 7).
7. **Entrega datos, no pantallas.** Devuelve JSON serializable y/o archivos. Quien muestra es el frontend; quien convierte a entregables (DXF, PDF) son `epc_dxf` y `epc_drawing`.

---

### 1.1 Tres tipos de motor

| Tipo | Qué hace | Ejemplos | Estado |
|---|---|---|---|
| **Motor de servicio** | Un trabajo técnico sobre una entrada (reconocer, dibujar, exportar, calcular geometría) | `epc_arch`, `epc_plan`, `epc_dxf`, `epc_titleblock`, `epc_sld`, `epc_mld`, `epc_drawing` | existe |
| **Motor de cálculo genérico** (uno por disciplina) | Los algoritmos y la secuencia de un cálculo, **sin ningún número de norma**: todo lo normativo llega en una *política* que el llamador pasa | `epc_calc_electrical`, luego `epc_calc_hvac`, `epc_calc_civil`… | **(objetivo)**; hoy el cálculo eléctrico está mezclado dentro de `epc_aea90364` |
| **Paquete de norma** | Una norma **completa por sí sola**: sus tablas y constantes, reglas, criterios de diseño, revisión, normas promovidas y la política que ofrece | `epc_aea90364`, luego `epc_iec60364`, `epc_nfpa70`… | existe en forma inicial (AEA) |

Cómo decidir de qué tipo es el tuyo: si su razón de ser es **una norma** (sus valores, sus cláusulas, su revisión) es un paquete de norma; si es **un método de cálculo** que sirve a cualquier norma de una disciplina, es un motor de cálculo genérico; si es **cualquier otro trabajo**, es un motor de servicio. Las secciones 2 a 8 y 10 a 16 valen para los tres; la **2.1** y la **13.2** cubren lo que añade una norma.

## 2. Estructura de carpetas (exacta)

```
engine/<area>/
├── README.md                     # qué hace, cómo se usa, de qué depende, límites conocidos
├── pyproject.toml                # nombre epc-<area>, dependencias, package-data
├── src/
│   └── epc_<area>/
│       ├── __init__.py           # API pública: lo único que otros importan (+ __version__, __all__)
│       ├── __main__.py           # CLI: python -m epc_<area>
│       ├── model.py              # tipos de valor (dataclass), Options, Result, excepción de dominio
│       ├── config.py             # carga de params.json (PARAMS) y derivados de la configuración
│       ├── params.json           # umbrales y constantes de ajuste (datos)
│       ├── pipeline.py           # el flujo de extremo a extremo, en pasos fijos
│       ├── <pasos>.py            # un módulo por paso o responsabilidad (normalize, svgout, …)
│       ├── sources/              # (si lee archivos) un lector por formato + registro (Adapter + Registry)
│       ├── recognizers/ o strategies/   # (si hay algoritmos intercambiables) una estrategia por módulo
│       ├── schema/
│       │   ├── input.schema.json  # JSON Schema del documento de entrada (si la entrada es JSON)
│       │   └── output.schema.json # y de la salida
│       └── data/                 # perfiles, catálogos, reglas, símbolos… (JSON; etiquetas {"es":…,"en":…})
├── tests/
│   ├── helpers.py                # generadores de datos sintéticos para las pruebas
│   ├── test_<tema>.py            # unittest; uno por responsabilidad
│   └── fixtures/                 # entradas y salidas esperadas fijadas (golden), si hacen falta
├── docs/                         # (opcional) notas de diseño
└── examples/                     # (opcional) una entrada de ejemplo que el gate pueda ejecutar
```

Reglas de la carpeta:
- El paquete se llama `epc_<area>` (minúsculas, guion bajo) y la carpeta `<area>`; el proyecto PyPI, `epc-<area>`.
- Nada de `.egg-info`, `__pycache__`, `.cov` ni archivos de salida en git.
- **No** guardes normas con copyright, PDFs, material de clientes ni credenciales (CLAUDE.md, ADR-0005).
- Los datos que el paquete lee en tiempo de ejecución se declaran en `[tool.setuptools.package-data]` para que viajen al instalar.

---

### 2.1 Paquete de norma (AEA 90364, IEC 60364, NFPA 70…)

Una norma es **un motor propio**, nombrado por la **norma** y **nunca por el país** (`aea90364`, `iec60364`): el país es dato de la jurisdicción. Es **completa por sí sola**: no hereda de otra norma ni importa a otro paquete de norma; si dos normas coinciden en un valor, cada una guarda el suyo con su cláusula y edición.

Forma de la carpeta (hoy, con lo marcado **(objetivo)** que añade el ADR-0028):
```
engine/<norma>/
├── README.md   pyproject.toml   tests/   docs/   examples/
└── src/epc_<norma>/
    ├── <cálculo propio de la norma>.py     # solo lo que de verdad es de la norma; los algoritmos genéricos irán al motor de cálculo (objetivo)
    ├── <norma>_tables.json                 # tablas y constantes, cada valor con su cláusula y edición
    ├── rules/*.json  (+ _indice.json)      # reglas de ingeniería derivadas de la norma (paráfrasis; solo la referencia)
    ├── data/
    │   ├── design-criteria.json            # catálogo de criterios base por disciplina; el proyecto los sobrescribe
    │   ├── review.json  review-log.jsonl   # quién aprobó qué punto, cuándo, y la huella del valor
    │   └── standard-solutions.json         # soluciones normalizadas (si aplica)
    ├── standards/<ID>/rules.json           # partes de la norma ingeridas y promovidas (esquema 1.1)
    ├── norm_data.py                        # dónde está cada dato: criteria_file(), REVIEW, REVIEW_LOG…
    ├── norm.json                           # (objetivo) manifiesto: id, familia, nombre {es,en}, ediciones, disciplinas, estado y el punto de entrada de su política por disciplina
    └── policy.py                           # (objetivo) la política que implementa el protocolo del motor de cálculo de cada disciplina
```
Reglas del paquete de norma:
- **Todo lo de la norma está dentro de su carpeta** (cálculo propio, datos, reglas, criterios, revisión, normas promovidas). Lo único fuera es el material privado (`local/dev-knowledge/standards/<CC>/<ID>/`: PDF y estudio, nunca versionado) y el esquema común (`shared/schemas/`).
- **Los números van en JSON con cláusula y edición**; el código solo existe para lo que difiere en método y no solo en valores.
- **El país la usa si lo dice su jurisdicción**: `engine/jurisdictions/<CC>/jurisdiction.json`, `packs` (`{"electrical": ["aea90364", "iec60364"]}` lista lo que el país acepta; el proyecto elige una por disciplina **(objetivo)**).
- **Entrada de normas nuevas:** pipeline de ingesta y promoción de [GUIA_NORMAS.md](GUIA_NORMAS.md): `epc_standards.promote_rules` escribe en `standards/` del paquete que la jurisdicción nombra, y `epc_rules.RuleSet` las consulta.
- **Se revisa punto por punto** (ADR-0011): sus valores quedan *pendientes* hasta que el revisor de normas los aprueba.
- **Contrato que debe pasar (objetivo, `epc_norms.contract`):** manifiesto válido; todo archivo declarado existe y cumple su esquema; todo valor tiene cláusula y edición; la política responde todo lo que su motor pregunta; la revisión solo refiere puntos que existen; no importa a otro paquete de norma.
- **Forma antigua:** el paquete AEA es anterior a esta guía (nombres en español, funciones sueltas, sin esquema ni `Options/Result`); un paquete de norma **nuevo** debe seguir la guía, y el AEA se lleva a ella por las fases del ADR-0028.

### 2.2 Motor de cálculo genérico (objetivo)
Un `calc_<disciplina>` tiene la forma de un motor de servicio (secciones 2 a 8) y, además: **no contiene ninguna constante normativa**. Define con `typing.Protocol` la **política** que necesita (`ElectricalPolicy`: tablas de capacidad, factores de corrección, límites de caída de tensión, constantes de protección, secciones mínimas, factores de cortocircuito…) y la recibe como parámetro: `calculate(board, policy)`. Mantiene la **secuencia** de pasos de la disciplina (para la eléctrica: demanda → corriente de proyecto → protección → capacidad → sección → caída → cortocircuito → verificaciones) y cada paso pregunta a la política; si una norma difiere en el *método*, la política ofrece un *hook* para ese paso. Se prueba con una política de mentira, sin norma alguna.

## 3. `pyproject.toml` (plantilla)

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "epc-<area>"
version = "0.1.0"
description = "EPC-291 <area> engine: <una línea de lo que hace>"
requires-python = ">=3.10"
dependencies = ["ezdxf", "numpy"]          # solo terceros; ningún epc-* salvo los que su capa permite

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
epc_<area> = ["params.json", "data/*.json", "schema/*.json"]
```

Las dependencias de terceros declaradas aquí son las que el generador de plugins copia como `python.requires` (`tools/build/regen_plugins.py`): **declara todas las que importas**.

---

## 4. API pública (`__init__.py`)

Una función principal pura, tipos de valor inmutables y una excepción de dominio.

```python
"""epc_<area>: <qué hace>. See README.md."""
from epc_<area>.model import Options, Result, <Area>Error
from epc_<area>.pipeline import run

__version__ = "0.1.0"
__all__ = ["run", "Options", "Result", "<Area>Error"]
```

Convenciones:
- **Una función de entrada** con nombre de verbo (`recognize`, `process`, `design`, `calculate`): `run(entrada, options=Options()) -> Result`. Sin parámetros mutables por defecto, sin globals.
- `Options` es un `@dataclass(frozen=True)` con valores por defecto; **todo lo que el llamador pueda querer cambiar va aquí**, no en variables de entorno.
- `Result` tiene `as_dict()` que devuelve un `dict` serializable a JSON con claves **estables** y, si produce un dibujo, el SVG/DXF como `str`/`bytes`.
- **Errores de dominio:** `raise <Area>Error("mensaje accionable en inglés")` cuando la entrada no se puede procesar (archivo ilegible, documento inválido). Lo recuperable **no** es excepción: se agrega a `warnings` y se sigue.
- Sin `print` fuera del CLI. Sin `logging` hacia afuera; lo que el usuario debe saber va en `warnings`.
- Las funciones internas son pequeñas: **complejidad ciclomática ≤ 10** (el gate lo exige a las funciones nuevas).

---

## 5. Entradas

### 5.1 Documento JSON (como `epc_plan`, `epc_aea90364`)
- Objeto con `"schema_version": "1.0"` y los campos del dominio. El esquema vive en `schema/input.schema.json` (JSON Schema 2020-12) y la validación da **mensajes que dicen qué corregir** (`"discipline 'xx' is not valid: profiles are …"`).
- Identificadores: `id` de nodo/línea/elemento son cadenas estables; `tag` es la etiqueta correlativa que pone el motor (`LU-001`); `kind` es un tipo del perfil de la disciplina.
- Los datos que vienen del usuario son opcionales con valores por defecto razonables; lo que falta se dice en `warnings`.

### 5.2 Archivos (como `epc_arch`)
- `run(data: bytes, name: str = "", options=Options())`: bytes y nombre; el tipo se deduce de los primeros bytes, la extensión solo desempata. Un lector por formato.
- El motor **no abre rutas** por su cuenta salvo en el CLI; el que llama lee el archivo.

### 5.3 Unidades y marcos de coordenadas
- **Metros** para longitudes reales, **grados** para ángulos, voltios/amperios/VA según el dominio (el nombre del campo lleva la unidad: `length_m`, `distance_m`, `voltage_v`, `power_va`).
- Un dibujo trabaja en un **espacio de plano** (x a la derecha, y hacia abajo, origen arriba a la izquierda) y solo pasa a metros cuando conoce la escala (`metres_per_unit`). Si la entrada no trae escala, el motor **no inventa**: da una pista (`scale_hint`) y avisa.
- Los textos que el usuario verá (etiquetas de tipos, nombres de capas) llevan `{"es": "...", "en": "..."}` en los datos; los mensajes técnicos (`warnings`, errores) van en inglés.

---

## 6. Salidas

- **Siempre un `dict` JSON estable**, con al menos: `schema_version`, los resultados del dominio, `counts` o `stats` (cuántos de cada cosa), `warnings: [str]`. Los números redondeados a lo que tiene sentido (`round(x, 3)`), nunca `NaN`.
- **Trazabilidad:** cada elemento calculado o reconocido lleva **por qué** (`reason`) y **cuánta confianza** (`confidence` 0–1) cuando el resultado es una estimación (como `epc_arch`).
- **Archivos** que escribe el CLI en `--out DIR`: `<stem>.<tipo>.json`, `<stem>.<tipo>.svg`, `<stem>.dxf`, `result.json`… Nombres predecibles: el backend los lee por nombre.
- **SVG** solo como intermedio de trabajo (con capas con los nombres del catálogo). `.svg` **no** es un entregable (CLAUDE.md); los entregables son DXF/PDF/XLSX y se generan con `epc_dxf`/`epc_drawing`.
- **Capas DXF:** si dibuja, usa nombres del catálogo `engine/dxf/src/epc_dxf/data/layers.json` (prefijo por disciplina: `ARQ-`, `ELEC-`, `HVAC-`, `PCI-`, `SAN-`, `COM-`, `CIV-`, `MEC-`, `INS-`, `PLAN-`, `291-`) y registra las nuevas ahí (una sola fuente), agrupadas por `data/disciplines.json`.
- **Resultado reproducible:** nada de fechas, rutas absolutas ni ids aleatorios dentro del JSON (los tests dorados lo comparan byte a byte).
- El usuario final **no ve formatos internos** (JSON, YAML, Markdown): el motor produce datos; lo que se muestra o entrega lo decide el frontend o el exportador.

---

## 7. Cómo lo invoca el backend (contrato de ejecución)

### 7.1 Como proceso (`python -m epc_<area>`) — para archivos de cualquier tamaño o calidad
El backend lo llama con `epc.core.engine.run_module("epc_<area>", args, timeout=N)`: un subproceso con límite de tiempo, salida capturada y sin poder tumbar el servidor.

Contrato del CLI (`__main__.py`):
```python
"""python -m epc_<area> INPUT --out DIR  [--option VALUE]"""
import argparse, json, sys
from pathlib import Path
from epc_<area> import <Area>Error, Options, run

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="epc_<area>", description="…")
    ap.add_argument("input")
    ap.add_argument("--out", default="out")
    a = ap.parse_args(argv)
    src = Path(a.input)
    try:
        result = run(src.read_bytes(), src.name, Options())
    except <Area>Error as e:
        print(f"ERROR {e}", file=sys.stderr)          # el backend muestra el final de stderr
        return 1
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    (out / f"{src.stem}.<tipo>.json").write_text(json.dumps(result.as_dict(), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"OK … -> {out}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```
- Código de salida **0** = bien; **1** = error de dominio (mensaje en stderr, empieza con `ERROR`); cualquier otro = fallo inesperado.
- Sin entrada interactiva, sin stdin, sin colores. Escribe solo dentro de `--out`.
- Variables de entorno que ya existen y debe respetar si dibuja: `EPC_LAYERS_JSON` y `EPC_SOLUTIONS_JSON` (rutas separadas por `os.pathsep`; la última gana: global → empresa → proyecto).
- El backend decide qué significa un código distinto de cero; la prueba del backend reemplaza el proceso con `engine.set_runner(fn)`.

### 7.2 En proceso (importación perezosa) — para cálculos rápidos y puros
El módulo del backend hace `from epc_<area> import run` **dentro de una función** (`_engine()`), no al importar el módulo, para que el backend arranque aunque el motor falte. `epc_plan` y `epc_aea90364` se usan así.
Criterio: **subproceso** si lee archivos externos o puede tardar/colgarse; **en proceso** si es una función pura sobre un documento pequeño.

### 7.3 Trabajos largos (`jobs.py`)
Si una operación tarda, el motor ofrece `run(...)` síncrono y `start(...)` que la lanza en un hilo y **escribe `status.json`** (`state: running|done|failed`, `progress` 0–1, `message`, `error`) de forma atómica (archivo temporal + reemplazo) para que quien consulta no lea medio archivo. Ver `engine/plan/src/epc_plan/jobs.py`.

---

## 8. Patrones de diseño que debe seguir

| Patrón | Dónde y para qué | Ejemplo |
|---|---|---|
| **Pipeline** (pasos fijos) | El flujo de extremo a extremo es una secuencia clara; cada paso es una función que no conoce el interior de los demás. Se puede reemplazar un paso sin tocar el resto. | `epc_arch/pipeline.py`: leer → normalizar → paredes → aberturas → escala → SVG |
| **Adapter + Registry** | Un lector por formato de entrada, todos producen el **mismo modelo interno**; `@register` los hace disponibles; un formato nuevo es un módulo nuevo y nada más cambia. | `epc_arch/sources/` (dxf, pdf, raster) |
| **Strategy** | Algoritmos intercambiables detrás de la misma interfaz; se prueba el más seguro primero. | `epc_arch/recognizers/walls.py` |
| **Datos dirigidos (Policy as data)** | Umbrales, perfiles, reglas, tablas en JSON con la norma/cláusula citada; el algoritmo recibe la política, no números sueltos. Agregar una norma o disciplina = declarar datos. | `params.json`, `profiles/*.json`, `aea_tables.json` |
| **Value Object inmutable** | `@dataclass(frozen=True)` para lo que viaja entre pasos; los contenedores pueden ser mutables pero no se comparten. | `model.py` |
| **Result Object** | Se devuelve un objeto con datos + advertencias, no se imprime ni se lanza por lo recuperable. | `Result.as_dict()` |
| **Null Object / resultado vacío con aviso** | Sin elementos reconocidos se devuelve resultado vacío + `warnings`, no una excepción. | `_empty_warnings` |
| **Registro por clave (Factory)** | Perfiles/disciplinas cargados por id desde datos. | `core.load_profile(id)` |
| **Strategy + Registro (política por norma)** | **(objetivo)** El cálculo de una disciplina recibe la política de una norma; `epc_norms.registry.policy(norma, disciplina)` la entrega importando el paquete por nombre, así que agregar una norma no toca código existente. | ADR-0028 |
| **Seam de pruebas** | Un punto para reemplazar lo externo (proceso, cliente) sin red. | `engine.set_runner` |
| **Job runner** | Trabajo largo con progreso en archivo de estado. | `jobs.py` |

Principios (SOLID aplicados):
- **S**: un módulo = una responsabilidad (leer, normalizar, reconocer, dibujar).
- **O**: se extiende agregando un lector/estrategia/perfil, no editando los existentes.
- **L**: todos los lectores devuelven el mismo modelo; cualquiera puede ocupar el lugar de otro.
- **I**: interfaces mínimas (`Protocol` con `kind` y `read`).
- **D**: los algoritmos dependen de modelos y datos (abstracciones), no de formatos de archivo.
- Más: funciones pequeñas y puras; nombres que dicen el dominio; el *porqué* en el docstring, no el *qué*; sin números mágicos (van a `params.json`).

---

## 9. Dependencias entre motores (capas)

Impuestas por el contrato `engine-layers` de import-linter (generado por `tools/ci/gen_importlinter.py`). Un paquete importa solo de capas **inferiores**, nunca de un hermano de su misma capa:

```
epc_drawing
epc_mld | epc_sld
epc_titleblock | epc_symbols | epc_plan | epc_aea90364 | epc_arch
epc_dxf
```
- `epc_standards` necesita `epc_aea90364`; `epc_rules`, `epc_documents` son independientes.
- Un motor nuevo que no dependa de nadie va en la capa `epc_titleblock | … | epc_arch` (la de los independientes). Si necesita DXF/capas, puede importar `epc_dxf`.
- **Ningún motor importa `epc`** (el backend): contrato `engine-independent`.
- Si tu motor necesita calcular, **usa el motor de cálculo** en vez de recalcular por su cuenta (ADR-0022: los dibujos solo dibujan; hoy los números vienen de `epc_aea90364`, y con el ADR-0028 vendrán de `epc_calc_<disciplina>` con la política de la norma del proyecto).
- **(objetivo, ADR-0028)** Capas: `epc_drawing` > `epc_mld | epc_sld` > los motores de cálculo genéricos y `epc_norms` (independientes entre sí) > `epc_dxf`. Los **paquetes de norma** quedan **al lado**, no debajo: importan `epc_norms` (para cargar sus datos) y nada más de la plataforma, y **nadie los importa de forma estática**: el registro los importa por nombre.

---

## 10. Datos y única fuente de la verdad (ADR-0012)

- Cada dato vive en **un** archivo; lo demás lo lee. El gate `single-source` falla si dos archivos versionados tienen el mismo contenido (salvo fixtures de pruebas).
- `params.json` con `"schema_version": "1.0"` y una nota que dice qué son los valores y en qué unidad. Se carga una vez en `config.py`:
  ```python
  PARAMS = json.loads((Path(__file__).resolve().parent / "params.json").read_text(encoding="utf-8"))
  ```
- Perfiles/catálogos con etiquetas `{"es","en"}` y, para normas, la **cita de la cláusula**. Los valores típicos (no normativos) se marcan como tales: "el ingeniero los confirma con la norma del proyecto".
- Lo **derivado** se marca y se regenera, no se edita (`dist/`, `registry.json`, `DEPENDENCIAS.md`, `.importlinter`).

---

## 11. Pruebas

- `unittest` (el gate ejecuta `python -m unittest discover -s tests` desde `engine/<area>`, con todos los `engine/*/src` en `PYTHONPATH`, bajo `coverage`).
- Cada archivo de test empieza así (no hace falta instalar):
  ```python
  import sys, unittest
  from pathlib import Path
  HERE = Path(__file__).resolve().parent
  sys.path.insert(0, str(HERE.parent / "src"))
  from epc_<area> import run   # noqa: E402
  ```
- **Datos sintéticos** generados por `tests/helpers.py` (un plano pequeño, un documento mínimo) para que cada lector/estrategia se compruebe contra el mismo resultado esperado.
- **Golden files** en `tests/fixtures/` (entrada + `expected_output.json`) para fijar el comportamiento; si el cambio es intencional se regenera y el diff se revisa.
- Qué probar: contrato de entrada (válidas e inválidas con su mensaje), contrato de salida (claves estables, `schema_version`), casos vacíos (sin elementos → `warnings`, no excepción), cada lector/estrategia, determinismo (dos corridas idénticas), el CLI (`main([...])` con códigos 0 y 1).
- Sin red, sin reloj real, sin archivos fuera de `tempfile`.
- **Cobertura:** el gate tiene un piso por área (`tools/ci/coverage_floor.json`); parte del valor medido al crear el motor y solo sube.

---

## 12. Calidad que exige el gate (`python tools/ci/run_gate.py`)

| Check | Qué exige a un motor |
|---|---|
| `engine-<area>` | sus tests en verde |
| `coverage` | no bajar de su piso |
| `complexity` | funciones **nuevas** ≤ 10 de complejidad ciclomática (radon); las existentes no pueden empeorar |
| `importlinter-config` + `backend-contracts` | no importa `epc`; respeta las capas |
| `impact-map` | `docs/architecture/DEPENDENCIAS.md` regenerado |
| `plugins-generated` / `registry` | si un plugin lo posee, sus campos generados al día |
| `single-source` | sin archivos duplicados |
| `ignored-sources` / `dev-credentials` | nada privado versionado |

Antes de fusionar: `python tools/ci/run_gate.py` en **verde (35/35 hoy)**. Nunca se sube a GitHub sin que el dueño lo pida.

---

## 13. Cómo se registra un motor nuevo (checklist exacto)

Con el motor ya creado en `engine/<area>/`:

1. **`tools/ci/run_gate.py`** → agregar `"<area>"` a la tupla `AREAS`.
2. **`tools/ci/check_coverage.py`** → agregar `"engine-<area>": "/engine/<area>/src/"` en `AREAS`; **`tools/ci/coverage_floor.json`** → agregar `"engine-<area>": <cobertura medida>`. (No uses `--update` global: reescribe todos los pisos; agrega solo el tuyo.)
3. **`tools/build/impact_map.py`** → agregar `"epc_<area>": "<area>"` en `ENGINE_PKGS` **y** el nombre en la expresión regular `NAME_REF` (lista cerrada de nombres).
4. **`tools/ci/gen_importlinter.py`** → ubicar `epc_<area>` en `ENGINE_LAYERS` (normalmente en la capa de los independientes: `epc_titleblock | epc_symbols | epc_plan | epc_aea90364 | epc_arch | epc_<area>`).
5. Regenerar lo derivado:
   ```
   python tools/ci/gen_importlinter.py
   python tools/build/impact_map.py
   python tools/build/epc_build.py registry
   python tools/build/regen_plugins.py
   ```
6. **`engine/README.md`**: una fila en la tabla de áreas y la ruta en `PYTHONPATH`/`pip install -e`.
7. **ADR** en `docs/architecture/decisions/ADR-00NN-<tema>.md` (contexto, decisiones, límites conocidos) y una línea en **`CHANGELOG.md`**.
8. *(Opcional)* **Plugin de Claude** en `claude/plugins/<id>/plugin.json` que declara solo lo que posee (`owns: ["<area>"]`); `engine`, `requires` y `python` se generan solos. Skills en `claude/skills/`, agentes en `claude/agents/`.
9. `python tools/ci/run_gate.py` → verde.

---

### 13.2 Si es un paquete de norma (además de lo anterior)
1. **Nombre** por la norma, sin país ni versión (`iec60364`); la edición va en `norm.json` **(objetivo)**.
2. **`engine/jurisdictions/<CC>/jurisdiction.json`** → agregarlo a `packs` del dominio que cubre (lista si el país acepta varias normas).
3. **Datos** con cláusula y edición, `data/design-criteria.json` si define criterios, y la carpeta `standards/` para lo que se promueva.
4. **Ingesta** de la norma con [GUIA_NORMAS.md](GUIA_NORMAS.md) (PDF en `local/dev-knowledge`, borrador, validación, revisión humana, promoción).
5. **Política** y **contrato** **(objetivo)**: `norm.json`, `policy.py` y pasar `epc_norms.contract`.
6. **Revisión**: los puntos quedan pendientes hasta que el revisor de normas los apruebe.
7. En el gate no hay cambios especiales: se registra con los pasos de la sección 13 (un paquete de norma es un motor más).

## 14. Si además necesita API o pantalla

**Backend** (`backend/src/epc/modules/<modulo>/`):
```
__init__.py   api.py   service.py   repository.py   models.py   public.py
```
- Capas **api → service → repository → models** (import-linter las impone); otros módulos solo importan `epc.modules.<modulo>.public`.
- El `service` llama al motor (7.1 o 7.2), traduce errores a `Invalid`/`NotFound` (`epc.core.errors`), revisa permisos (`identity`), audita (`identity.audit_event`) y guarda en el proyecto (`repository` con `epc.core.fsutil`).
- Pruebas de integración con `TestClient` y un proyecto temporal (ver `backend/tests/integration/test_layout_api.py`).
- Datos de proyecto en `<proyecto>/workspace/…` (ver `docs/USER_DATA_MODEL.md`).

**Frontend** (`frontend/web/src/features/…`, `frontend/packages/ui`): textos nuevos en `dict/es.ts` **y** `dict/en.ts` (el test de i18n exige paridad), iconos en `icons.tsx`, estilos en `styles.css`, tipos TypeScript que reflejan el JSON del motor, y pruebas Vitest de la lógica pura.

---

## 15. Convenciones de trabajo

- **Ramas:** `feature|fix|chore/<tema>` desde `dev`; el hook impide commitear en `dev`/`main`. Se fusiona con `--no-ff` tras el gate en verde. **No se sube a GitHub** sin pedido del dueño.
- **Commits:** Conventional Commits (`feat(arch): …`, `fix(plan): …`).
- **Versiones:** `__version__` y `pyproject` en semver; cada cambio de comportamiento lleva línea en `CHANGELOG.md`.
- **Idioma:** código, esquemas, ids, plantillas y prompts en inglés; interfaz con i18n es/en; al usuario se le explica en español.
- **Privado:** normas con copyright, informes de terceros y datos de clientes nunca entran al repositorio; lo local vive en `local/` (ignorado).
- **Sin efectos secundarios** al importar y sin dependencias nuevas sin declararlas en `pyproject.toml`.

---

## 16. Esqueleto mínimo para empezar (copiar y adaptar)

`src/epc_<area>/model.py`
```python
"""The values the engine passes around. Immutable but the containers."""
from dataclasses import dataclass, field
from typing import Any, Dict, List


class <Area>Error(Exception):
    """The input cannot be processed: the message says what to fix."""


@dataclass(frozen=True)
class Options:
    units_per_metre: float | None = None


@dataclass
class Result:
    items: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {"schema_version": "1.0", "counts": {"items": len(self.items)}, "items": self.items, "warnings": list(self.warnings)}
```

`src/epc_<area>/config.py`
```python
import json
from pathlib import Path
PARAMS = json.loads((Path(__file__).resolve().parent / "params.json").read_text(encoding="utf-8"))
```

`src/epc_<area>/pipeline.py`
```python
"""The work end to end, always in the same order. Each step is a function of its own."""
from epc_<area>.model import <Area>Error, Options, Result


def run(data: bytes, name: str = "", options: Options = Options()) -> Result:
    if not data:
        raise <Area>Error("the input is empty")
    result = Result()
    # 1. read   2. normalize   3. find   4. say it as data
    if not result.items:
        result.warnings.append("nothing was found: <why, and what the person can do>")
    return result
```

`tests/test_pipeline.py`
```python
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from epc_<area> import <Area>Error, run   # noqa: E402


class TestRun(unittest.TestCase):
    def test_an_empty_input_is_refused_with_its_reason(self):
        with self.assertRaises(<Area>Error):
            run(b"")

    def test_nothing_found_is_a_warning_not_an_error(self):
        self.assertTrue(run(b"x").as_dict()["warnings"])

    def test_the_same_input_gives_the_same_output(self):
        self.assertEqual(run(b"x").as_dict(), run(b"x").as_dict())


if __name__ == "__main__":
    unittest.main()
```

`README.md` (cuatro bloques): qué hace en una frase; cómo se usa (`epc_<area>.run(...)` y `python -m epc_<area> …`); de qué depende (y de nada más); **límites conocidos** (honestos: qué no hace todavía).

---

## 17. Prompt sugerido para el otro chat

> Voy a construir un motor para la plataforma EPC-291. Debe ser una librería Python pura en `engine/<area>/` (paquete `epc_<area>`), sin importar el backend ni a sus hermanos, con `pyproject.toml`, `src/epc_<area>/{__init__,__main__,model,config,pipeline}.py`, `params.json` con los umbrales, `schema/` si la entrada es JSON, `tests/` con `unittest` y `README.md`. Una función pública pura `run(entrada, Options) -> Result` con `Result.as_dict()` (JSON estable con `schema_version`, `counts`, `warnings`); errores de dominio con `<Area>Error`; lo recuperable va a `warnings`. CLI `python -m epc_<area> ENTRADA --out DIR` (exit 0 = OK; 1 = `ERROR …` en stderr; escribe solo en `--out`). Patrones: Pipeline de pasos fijos, Adapter+Registry para lectores de formatos, Strategy para algoritmos intercambiables, datos dirigidos (nada de constantes mágicas), Value Objects inmutables. Código, comentarios y textos en inglés; funciones de complejidad ≤ 10; cobertura medida; sin efectos al importar. Al terminar dame la lista de archivos a tocar para registrarlo (run_gate AREAS, check_coverage + coverage_floor, impact_map, gen_importlinter, README de engine, ADR, CHANGELOG). Lo que el motor debe hacer es: **<describe aquí qué recibe, qué entrega y para qué disciplina>**.

---

### 17.1 Variante para un paquete de norma

> Voy a crear el paquete de norma **<norma>** (`engine/<norma>/`, paquete `epc_<norma>`, dominio `<dominio>`) para EPC-291. Debe ser **completo por sí solo**: sus tablas y constantes en JSON con cláusula y edición, sus reglas, `data/design-criteria.json`, `data/review.json` vacío, `standards/` para lo promovido y `norm_data.py`. Nada de números normativos en código fuera de la política; **no importa a otro paquete de norma**. Nombre por la norma, no por el país. Sigue las secciones 2 a 8, 10 a 13.2 de esta guía y entrégame al final: la lista de datos creados, lo que falta ingerir con la guía de normas y qué se agrega a `packs` de qué jurisdicción.

## 18. Qué decirme al volver de ese chat

Para integrarlo al programa necesito (y, si es una norma, también las partes de la norma ingeridas y a qué jurisdicción se agrega): el **nombre del área**, **qué recibe** (JSON o archivos y de qué tipo), **qué entrega** (claves del JSON y archivos), **de qué depende**, si va **en proceso o como subproceso**, qué **disciplina/subdisciplina** sirve (para registrar capas, símbolos y tipos), y si tendrá **pantalla** en el editor de planos o en la consola.
