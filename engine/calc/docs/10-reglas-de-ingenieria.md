# 10 · Reglas de ingeniería

## Qué resuelve

Reúne en JSON los requisitos de diseño que fijan las normas y que no son cálculo: alturas de tomacorrientes e interruptores, reservas en tableros y bandejas, llenado de canalizaciones, distancias entre cajas, tipos de circuito y zonas de baño. Sirve para verificar proyectos y, más adelante, para que otros módulos o skills consulten un valor sin releer la norma.

## Dónde está

`library/calculations/rules/`: un archivo por subgrupo y un `_indice.json`. Total: 177 reglas.

| Archivo | Reglas | Contenido |
|---|---|---|
| `bandejas.json` | 6 | Reserva, capas, separación, altura de montaje y tapas. |
| `banos.json` | 12 | Zonas 0 a 3, grados IP, diferenciales de 30 mA y separación eléctrica (701). |
| `canalizaciones.json` | 16 | Ortogonalidad, distancias entre cajas, curvas, llenado, diámetros mínimos y radios de curvatura. |
| `circuitos.json` | 18 | Tipos de circuito (IUG, TUG, IUE, TUE, APM, MBTF, ATE, ITE): bocas máximas, corriente y protección. |
| `colores.json` | 4 | Colores de neutro, PE, PEN y líneas L1, L2 y L3 (51). |
| `conductores.json` | 9 | Secciones mínimas (Tabla 52.24), neutro (524.2) y caída de tensión máxima (525) (52). |
| `conductores_proteccion.json` | 22 | PE, PEN y equipotenciales: Tablas 54.5 a 54.10 (secciones y factor k), tipos y prohibiciones (54). |
| `curvas_canerias.json` | 4 | Cantidad y distancia entre curvas, radios de curvatura de caños metálicos y sintéticos (Tablas 52.11 y 52.12). |
| `enterrados.json` | 7 | Profundidad, pendiente, diámetros de conductos, cruces con caño de reserva y protección. |
| `iluminacion.json` | 9 | Bocas de iluminación en escaleras, ventiladores, depósitos y acceso a luminarias. |
| `interruptores.json` | 6 | Altura y ubicación de teclas de luz, pasillos, ascensores y garajes. |
| `otros.json` | 1 | Cercas electrificadas. |
| `proteccion_choques.json` | 8 | Tensión límite 24 V, tiempos de desconexión (Tabla 41.3, TN-S, TT) y diferencial de 30 mA (41). |
| `proteccion_sobrecorrientes.json` | 8 | Coordinación IB ≤ In ≤ IZ, I2 ≤ 1,45·IZ, temperaturas (Tabla 43.1), neutro y poder de corte (43). |
| `puesta_a_tierra.json` | 16 | Ra máxima (40 Ω, Tabla 54.1), electrodos (Tabla 54.2), barra equipotencial y mediciones (54). |
| `tableros.json` | 11 | Reserva, alturas de comandos y borneras, grado IP, ubicación y verificación térmica. |
| `tomacorrientes.json` | 20 | Altura de cajas, mesadas, baldeado, niños, aulas y carga de vehículos eléctricos. |

## Qué lleva cada regla

```json
{
 "id": "tomacorrientes.altura_arista_inferior_771",
 "tema": "Altura de cajas de tomacorrientes",
 "regla": "En la Sección 771, la arista inferior de la caja ... queda a no menos de 0,15 m del solado terminado.",
 "tipo": "obligatorio",
 "parametros": {"altura_min_m": 0.15, "referencia": "arista inferior de la caja"},
 "aplica_a": ["viviendas", "oficinas", "locales"],
 "fuente": {"norma": "AEA 90364-7-771", "edicion": "2006", "clausula": "771.8.6.2", "pagina_impresa": 44}
}
```

- **tipo**: `obligatorio`, `recomendado` o `prohibido`.
- **parametros**: el valor de la regla, con la unidad en el nombre (`_m`, `_mm`, `_pct`, `_a`, `_cm`, `_va`).
- **fuente**: norma, edición, cláusula y página impresa, solo como referencia para ubicar el requisito en la norma; no se incluye texto de la norma (derecho de autor). En las Partes 4 y 5 la página impresa es de la forma `54-5` y se agregan `pagina_pdf` y `verificacion`.
- **tabla** (opcional): las tablas de la norma, con `columnas`, `filas`, unidades y notas.

### Cómo se leyeron las Partes 4 y 5

Esas normas están escaneadas (sin texto). El texto sale de OCR, que pierde las tildes y desfigura las tablas. Por eso cada regla de esas partes dice cómo se comprobó:

- `ocr`: el requisito se ubicó y se contrastó en el OCR de la página PDF indicada; los números en prosa se contrastaron además con la imagen de la página.
- `visual`: los valores de la tabla se leyeron sobre la imagen de la página; el título de la tabla se comprobó contra el OCR.

## Pasos para usarlo

1. Elegir el subgrupo (por ejemplo `tomacorrientes`).
2. Buscar la regla por tema o por id con `aea_rules.buscar("altura", grupo="tomacorrientes")`.
3. Leer el valor con `aea_rules.valor("bandejas.reserva_20pct", "reserva_min_pct")`, que devuelve 20.
4. Comparar con el dato del proyecto y registrar la cláusula de la fuente en la verificación.

La Sección 771 (viviendas, oficinas y locales) y la 770 (viviendas) a veces exigen valores distintos: por ejemplo, la arista inferior de los tomacorrientes es 0,15 m en 771 y de 0,2 a 0,3 m en 770. Por eso hay una regla por norma.

## Cómo se verifica

Cada regla se redactó con palabras propias a partir de la lectura de la norma y se contrastó contra ella (cláusula, página y valores). Las normas y la herramienta de verificación que las contrastaba (con los fragmentos literales que usaba para ubicarlas) son material privado: están fuera del repositorio, en `local/dev-knowledge/`, porque contienen texto protegido por derecho de autor. Lo que se publica es solo el resultado: reglas, parámetros y referencias. Una prueba (`test_sin_texto_literal_de_la_norma`) impide que vuelva a entrar texto literal de la norma en estos archivos.

## Limitaciones

- Cubre las Secciones 771, 770, 701 y 722 y, de las Partes 4 y 5, los capítulos 41, 43, 51 (colores), 52 (secciones mínimas, neutro, caída de tensión y curvas) y 54 (puesta a tierra y conductores de protección).
- De las Partes 4 y 5 no se incorporaron: el capítulo 42 (efectos térmicos), el 44 (sobretensiones), el 434 (cortocircuito), las Tablas 52.1 y B52 (capacidad de cables, que ya están en 771.16) y la Parte 2 (definiciones). La IT 90909-1 remite a AEA 90909-0 para el factor de tensión c, que no está en `assets/`; por eso no hay reglas con ese factor.
- La Tabla 41.3 se leyó sobre una imagen de 120 dpi; conviene confirmar los tiempos de 230 V contra la norma impresa.
- El valor de `parametros` es una lectura de la norma; ante una duda, la fuente es la cláusula y la página indicadas.
- No están todas las reglas de las normas: están las que se expresan como valor, límite o prohibición y se pudieron respaldar con su cláusula y página. Los puntos mínimos de utilización por ambiente de viviendas y oficinas (tablas por grado de electrificación) no se incluyeron porque sus tablas no son confiables en el texto extraído; solo se incluyeron las densidades de depósitos, que están en prosa.
- Estado: borrador pendiente de validación del usuario.

## Módulo

`aea_rules`: `indice`, `grupos`, `reglas`, `regla`, `valor`, `buscar`.
