# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el proyecto usa [Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

## [1.6.0] - 2026-10-22

### Corregido

- Descripciones de las skills `calculation-memo` y `memo-summary`: sin etiquetas XML (`<PROJECT>`), que la validación del plugin rechazaba.

### Añadido

- `library/calculations/rules/`: 177 reglas de ingeniería en JSON por subgrupo, cada una con cláusula, página y cita verificada; módulo `aea_rules.py`. Las 106 de la Parte 7 (771, 770, 701, 722) se comprueban contra el texto del PDF.
- Reglas de las Partes 4 y 5 (escaneadas, por OCR): puesta a tierra (Ra ≤ 40 Ω, Tablas 54.1 a 54.3), conductores de protección y equipotenciales (Tablas 54.5 a 54.10), colores, secciones mínimas y neutro (Tabla 52.24, 524), caída de tensión (525), curvas de cañerías (Tablas 52.11 y 52.12), protección contra sobrecargas (43) y contra choques (41). Cada regla indica si se comprobó por OCR o sobre la imagen de la página.
- `aea_tables.json` y `aea_tables.py`: tablas 771.16 de capacidad de cables (I, III, V, VI, VIII, XI) y factores de corrección (II, IV, VII, IX, X) extraídos de los PDF y verificados contra su texto, con consultas e interpolación.
- `aea_protection.py`: I2 convencional, In máxima por Iz y verificaciones TN, TT e IT.
- `aea_ampacity.py`: Iz según aislación, material, método de instalación, clase, ternas, agrupamiento y temperaturas; el cálculo y la MC/SP usan estos datos.
- Plantilla `src/input_motor_AEA_V2.xlsx` (y `make_template.py`) con columnas ordenadas por grupos, método de instalación por descripción, clase 5 por defecto y formato sobrio; el Excel original no se modifica.
- Carpeta `docs/` con la descripción paso a paso del cálculo (00 a 09); el README enlaza a cada paso.
- README resumido: descripción del cálculo y enlaces a `docs/`.
- `docs/11-pendientes.md`: tabla de pendientes con prioridad y estado.

### Eliminado

- Logo y material del proyecto de láminas IRAM, espejos de `assets/calculations/` y `test/`, carpetas vacías y carpetas legacy de las skills.

### Cambiado

- Logo del proyecto restablecido en `assets/logo.png` y `assets/logo.svg`, usado en el README.
- Documentación de git (`CONTRIBUTING.md`, plantillas, `.gitignore`) y `README.md` para el motor AEA.
- `skill.json` de las skills, sin referencias a carpetas eliminadas.

## [1.5.0] - 2026-10-22

### Añadido

- Skill `feeder-sizing`: formulario de entrada previo, criterios de caída de 1 %, 3 % y 5 %, búsqueda con aluminio y, si no cumple, cobre XLPE.

### Cambiado

- El plugin se llama `aea90364-standard`.

## [1.4.0]

### Añadido

- Memoria de Cálculo (`_MC.md`) y Síntesis de Proyecto (`_SP.md`) del alimentador principal del tablero.
- Opción `--alimentador TAG` en `aea_pipeline.py`.

## [1.3.0]

### Cambiado

- Toda la salida de cálculo va a un único JSON (`<proyecto>_calculo.json`), sin PDF.
- Identificadores de código en inglés; los textos internos siguen en español.
- Skills renombradas: `memoria-calculos` a `calculation-memo` y `sintesis-memoria` a `memo-summary`.

### Eliminado

- Generadores de PDF y todo lo relacionado con gestión de proyectos (CCPM, verificadores documentales, charter y canvas).

El historial anterior del proyecto corresponde a otro generador y no se conserva aquí.
