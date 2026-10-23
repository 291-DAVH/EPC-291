# template-extract.md — Ficha de tabla extraída de una norma

**Uso.** Una ficha por tabla (o por conjunto de valores) tomada de una norma que está `EN ARCHIVO`. Se guarda como `98_LIBRARY/standards/<disciplina>/extractos/<ID NRM>_extracto_<tabla>.md` y se cita desde los cálculos con su ID. Los valores de la ficha son los que se pasan como parámetro a los módulos de `98_LIBRARY/calculations/` (por ejemplo, la tabla JSON de `conductor_selection.py`, CAL-009); la biblioteca de cálculos **nunca** embebe tablas normativas.

**Reglas.**
1. Solo se transcribe de un archivo de norma presente en la biblioteca; sin archivo no hay ficha (el valor queda `[VERIFICAR]`, ver `calc-library.md`).
2. Los valores se marcan `[VERIFICAR]` hasta que una persona los compare con el original y lo registre en «Verificado por».
3. Si cambia la edición de la norma, se crea una ficha nueva; la anterior queda marcada `OBSOLETA`.

---

| Campo | Valor |
|---|---|
| ID de norma (`NRM-nnn`) | `[DEFINIR]` |
| Designación y edición | `[DEFINIR]` (por ejemplo, designación y año de la edición en archivo) |
| Tabla / cláusula | `[DEFINIR]` |
| Página del archivo | `[DEFINIR]` |
| Título de la tabla | `[DEFINIR]` |
| Condiciones de aplicación (método de instalación, material, temperatura, agrupamiento) | `[DEFINIR]` |
| Unidades | `[DEFINIR]` |
| Fecha de extracción | `[DEFINIR]` (AAAA-MM-DD) |
| Extraído por | `[DEFINIR]` |
| Verificado por / fecha | `[DEFINIR]` — sin verificación, los valores permanecen `[VERIFICAR]` |
| Estado de la ficha | `BORRADOR` / `VERIFICADA` / `OBSOLETA` |
| Archivo JSON derivado (si se usa en un cálculo) | `[DEFINIR]` (por ejemplo, `02-engineering/calculations/.../conductor_table.json`) |

## Valores extraídos

| Fila / parámetro | Valor | Unidad | Observación |
|---|---|---|---|
| `[DEFINIR]` | `[VERIFICAR]` | | |

## Notas

- `[DEFINIR]`
