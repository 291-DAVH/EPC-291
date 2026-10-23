# 11 · Pendientes

Lista de lo que falta o hay que confirmar. Se actualiza al cerrar cada etapa.

| N.º | Tema | Qué falta | Dónde | Prioridad | Estado |
|---|---|---|---|---|---|
| 1 | Dimensionado de alimentadores | Pasar a código el formulario del Paso 0, el reemplazo de aluminio por cobre XLPE cuando el aluminio no cumple, y los criterios de caída de 1 %, 3 % y 5 %. | skill `aea90364-feeder-sizing`, `aea_pipeline.py` | Alta | Pendiente |
| 2 | Tabla 41.3 | Confirmar los tiempos de 230 V contra la norma impresa: se leyeron sobre una imagen de 120 dpi. | `rules/proteccion_choques.json` | Alta | Pendiente de usuario |
| 3 | Tabla 771.16.VI | Confirmar la ambigüedad de la columna `c4_3x`. | `aea_tables.json` | Alta | Pendiente de usuario |
| 4 | Resistividad del aluminio | Verificar los valores de R20 del aluminio, marcados `[VERIFICAR]`. | `aea_ampacity.py` | Media | Pendiente de usuario |
| 5 | Disposiciones F y G | Validar los supuestos de disposición de los métodos F y G. | `aea_ampacity.py` | Media | Pendiente de usuario |
| 6 | Tabla 771.16.XII | Incorporar la tabla; hoy no está en `aea_tables.json`. | `aea_tables.json` | Media | Pendiente |
| 7 | Tablas B52 de IEC 60364-5-52 | Incorporar las tablas apaisadas; el OCR no las lee bien y hay que leerlas sobre imagen. | `aea_tables.json` | Media | Pendiente |
| 8 | Método B1 con XLPE | No tiene tabla en la norma; definir qué hace el motor (hoy avisa). | `aea_ampacity.py` | Media | Pendiente de decisión |
| 9 | Tablas de las Partes 4 y 5 como consulta | Pasar a `aea_tables.json` las tablas 41.3, 43.1, 54.1 y 54.5 a 54.10 para que las consulte el motor (hoy son reglas). | `rules/`, `aea_tables.py` | Media | Pendiente |
| 10 | Capítulos sin incorporar | Capítulos 42 (efectos térmicos), 44 (sobretensiones) y 434 (cortocircuito) de la Parte 4. | `rules/reglas_ocr.py` | Baja | Pendiente |
| 11 | Parte 2 e IT 90909-1 | Las definiciones no tienen valores numéricos; el factor c está en AEA 90909-0, que no está en `assets/`. Agregar ese PDF para incorporarlo. | `assets/` | Baja | Bloqueado: falta el PDF |
| 12 | Reglas de la Parte 7 | Puntos mínimos de utilización por ambiente (tablas por grado de electrificación): el texto extraído no es confiable. Leerlos sobre imagen. | `rules/` | Baja | Pendiente |
| 13 | Validación de reglas | Revisar las 177 reglas, hoy en estado borrador, y confirmar valores y alcance (`aplica_a`). | `rules/*.json` | Media | Pendiente de usuario |
| 14 | Plantilla V2 | Probar la plantilla con un proyecto real y ajustar columnas y listas. | `src/input_motor_AEA_V2.xlsx` | Media | Pendiente de usuario |
| 15 | Archivo suelto | Decidir qué hacer con `aea90364-standard.plugin` de la raíz del repo, que no forma parte del proyecto. | raíz del repo | Baja | Pendiente de usuario |
| 16 | Publicación | Hacer push y abrir el PR de `feat/motor-aea90364`; no se pidió todavía. | git | Baja | Pendiente de usuario |
