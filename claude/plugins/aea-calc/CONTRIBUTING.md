# Cómo contribuir

Motor de cálculo de instalaciones de baja tensión según AEA 90364-7 (771, 770, 701, 722) y AEA 90909-1, empaquetado como plugin `aea90364-standard`.

## Estructura

| Carpeta | Contenido |
|---|---|
| `library/calculations/` | Fuente del motor: módulos `aea_*.py`, pruebas `test_*.py` y catálogo de fórmulas (`FORMULAS_AEA.md`, `formulas_aea.json`) |
| `skills/` | Skills de trabajo: `feeder-sizing`, `electrical-dimensioning`, `calculation-memo`, `memo-summary` |
| `plugin/elec-calc-generator/` | Carpeta a empaquetar: manifiesto, scripts (copia de `library/calculations/`), skills y README |
| `plugin/aea90364-standard.plugin` | Paquete generado. No se edita a mano |
| `src/` | Excel de entrada (`input_for_sld_V1.xlsx`) y salidas generadas. El Excel no se modifica |
| `assets/` | Logo del proyecto (`logo.png`, `logo.svg`) y normas AEA en PDF (referencia para las fórmulas) |

## Flujo de trabajo

1. Crear una rama desde `main`: `git checkout -b feat/nombre-corto`.
2. Cambiar el código en `library/calculations/`.
3. Correr las pruebas desde `library/calculations/`: `python -m unittest discover -s . -p "test_*.py"`. Tienen que pasar todas.
4. Regenerar la salida de ejemplo: `python library/calculations/aea_pipeline.py src/input_for_sld_V1.xlsx`, y revisar los avisos.
5. Copiar los módulos cambiados a `plugin/elec-calc-generator/scripts/` en el mismo PR.
6. Actualizar `CHANGELOG.md` y la versión en `.claude-plugin/plugin.json` y en `plugin/elec-calc-generator/.claude-plugin/plugin.json`.
7. Reconstruir `plugin/aea90364-standard.plugin` desde `plugin/elec-calc-generator/`.
8. Abrir un Pull Request con la plantilla de `.github/pull_request_template.md`.

## Qué no se rompe sin una versión MAJOR

- Las claves del JSON por circuito: `In`, `Ib`, `icu`, `S`, `dU`, `disp`. `sld-generator` las lee.
- Los nombres de las hojas y columnas del Excel de entrada (`TABLERO`, `CIRCUITOS`, `TOPOLOGIAS`).
- Las opciones de línea de comando de `aea_pipeline.py`.
- El Excel de `src/` no se modifica desde el código.

## Cada fórmula cita su cláusula

Toda fórmula, tabla o factor nuevo indica la cláusula de la norma de donde sale (por ejemplo, `771.19.7 a`). Si el valor no es normativo (por ejemplo, la reactancia típica), se marca como `[VERIFICAR]`.

## Mensajes de commit

Usar [Conventional Commits](https://www.conventionalcommits.org/es/v1.0.0/):

- `feat(calc): ...` nueva fórmula, tabla o norma
- `feat(skill): ...` cambio en `feeder-sizing`, `calculation-memo` o `memo-summary`
- `fix(calc): ...` corrección de una fórmula, un factor o una conversión de unidades
- `fix(pipeline): ...` lectura del Excel o escritura del JSON, MC o SP
- `test: ...`
- `docs: ...`
- `chore(release): x.y.z` cambio de versión

## Versionado

Se usa Versionado Semántico:

- **MAJOR**: cambia el formato del JSON, del Excel de entrada o de las opciones de línea de comando.
- **MINOR**: nueva norma, fórmula, skill o documento (MC o SP).
- **PATCH**: corrección de un valor, de una cláusula o de un error.

## Reportar problemas

Abrir un issue con la cláusula o fórmula, la fila del Excel usada, la versión del plugin, el valor esperado (con su fuente) y el valor obtenido.
