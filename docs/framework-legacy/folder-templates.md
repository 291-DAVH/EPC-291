# folder-templates.md — Plantillas de carpetas y tabla de archivos

> Documento de referencia del framework. Tiene la misma autoridad que `CLAUDE.md`. **Solo lectura:** no editar en proyectos individuales, solo en la plantilla maestra. Las secciones se numeran para que las referencias cruzadas de `CLAUDE.md` y los módulos M2/M3 sigan siendo válidas.

---

## 4.1 Estructura global del repositorio

La estructura global se describe en `CLAUDE.md`, sección 4. Este archivo define las plantillas internas de `02-engineering` y `01-input`, las reglas de nomenclatura de carpetas y la tabla de ubicación de archivos.

---

## 4.2 Plantilla de `02-engineering`

### 4.2.1 Tres niveles

| Nivel | Qué contiene | Cuándo se crea |
|---|---|---|
| **Compartido** | `00-general`, `18-cad-resources`, `19-temp` | Siempre, en todo proyecto |
| **Por disciplina** | Una carpeta por cada disciplina marcada `[x]` en `starting-data.md`, sección 3 | En `iniciar proyecto`, tras `aprobar charter` (M3, Fase 4) |
| **Interno de disciplina** | Subcarpetas `01` a `15` dentro de cada disciplina | Junto con la carpeta de disciplina |

### 4.2.2 Tabla de disciplinas

Claude crea **solo** las carpetas cuya disciplina está marcada `[x]` en `starting-data.md`, sección 3. Las no marcadas no se crean.

| Disciplina en `starting-data.md` | Carpeta en `02-engineering` | Código CAD |
|---|---|---|
| Electricidad | `01_ELECTRICAL` | `EL` |
| Civil | `02_CIVIL` | `CV` |
| Termomecánica | `03_THERMOMECHANICAL` | `TM` |
| Combate de incendios | `04_FIRE_SUPPRESSION` | `FP` |
| Detección de incendios | `05_FIRE_DETECTION` | `FD` |
| HVAC | `06_HVAC` | `HV` |
| Mecánica | `07_MECHANICAL` | `ME` |
| Sanitaria | `08_SANITARY` | `PL` |

Si un proyecto requiere una disciplina no listada, registrar `DEC-nnn` y asignarle el siguiente número disponible (actualmente: 09 en adelante). Nunca usar los slots 16–17, que están reservados para uso futuro del framework.

### 4.2.3 Estructura interna de cada disciplina

Cada carpeta de disciplina replica la siguiente plantilla. Se crea con un archivo `.gitkeep` en cada subcarpeta vacía.

```
<DISC>/
├── 01_DESIGN_CRITERIA       ← criterios y bases de diseño de la disciplina
├── 02_STUDIES               ← estudios técnicos (cargas, cortocircuito, etc.)
├── 03_calculations          ← memorias de cálculo
├── 04_SPECIFICATIONS        ← especificaciones técnicas (generales y particulares)
├── 05_DIAGRAMS              ← unifilares, trifilares, esquemas de control
├── 06_DRAWINGS              ← planos 2D finales
├── 07_MODELS                ← modelos 3D / BIM
├── 08_LISTS                 ← listados: equipos, cables, canalizaciones, E/S
├── 09_datasheets            ← fichas técnicas de equipos
├── 10_TENDER_AND_PROCUREMENT ← paquetes de licitación y órdenes de compra
├── 11_CONSTRUCTION          ← documentación de construcción
├── 12_SITE_AND_WORKSHOP     ← documentación de obra y taller
├── 13_COMMISSIONING         ← protocolos de puesta en marcha
├── 14_as-built              ← documentos "como construido"
└── 15_ARCHIVE               ← archivo histórico del proyecto
```

### 4.2.4 Carpetas compartidas (siempre presentes en la raíz de `02-engineering`)

| Carpeta | Contenido |
|---|---|
| `00-general` | Documentación transversal a todas las disciplinas. Subcarpetas: `01-design-basis` (bases de diseño del proyecto, normas y reglamentos aplicables) y `02-interface-matrix` (interfaces entre disciplinas: documentos, señales, datos compartidos) |
| `18-cad-resources` | Recursos CAD compartidos por todas las disciplinas del proyecto. Subcarpeta `xref/`: archivos de referencia externa (DWG). **Bloques, símbolos y plantillas CAD** viven en `98_LIBRARY/`, no aquí |
| `19-temp` | Archivos de trabajo temporales. No se versiona su contenido ni se emite desde aquí. Se vacía al cerrar el proyecto |

### 4.2.5 Slots reservados

Los números **16 y 17** están reservados para disciplinas o categorías que se agreguen en versiones futuras del framework. No crearlos hasta que el framework los defina formalmente.

### 4.2.6 Plantillas A–E (por tipo de proyecto)

La plantilla interna de cada disciplina (sección 4.2.3) es única para todas las variantes. Las plantillas A–E diferencian **qué disciplinas aplican por defecto** según el tipo de proyecto:

| Plantilla | Tipo de proyecto | Disciplinas por defecto |
|---|---|---|
| A | Solo pliego para licitación | `01_ELECTRICAL` (mínimo) |
| B | Ingeniería eléctrica | `01_ELECTRICAL` |
| C | Ingeniería eléctrica + civil | `01_ELECTRICAL`, `02_CIVIL` |
| D | Ingeniería multidisciplina (3 o más disciplinas) | Según `starting-data.md` |
| E | Construcción y puesta en marcha | Según `starting-data.md`; énfasis en subcarpetas 11–14 |

En todos los casos, las carpetas se crean **únicamente para las disciplinas marcadas `[x]` en `starting-data.md`, sección 3**. La plantilla solo orienta la selección; el estado de los checkboxes decide.

---

## 4.3 Reglas de nombres de carpeta del proyecto

| Elemento | Regla |
|---|---|
| Formato | `[CLI]_[PRY]_[Descripción]` — por ejemplo `FORD_SET01_Planta-Pacheco` |
| `[CLI]` | Sigla del cliente (de `starting-data.md`, campo «Sigla del cliente») |
| `[PRY]` | Código del proyecto (de `starting-data.md`, campo «Código del proyecto») |
| Separadores | Guion medio (`-`) dentro de la descripción; guion bajo (`_`) entre los tres bloques |
| Caracteres | Sin acentos, sin espacios, sin caracteres especiales; solo letras, números, guiones |
| Longitud | Máximo 60 caracteres en total |

---

## 4.4 Estructura de `01-input`

| Subcarpeta | Contenido |
|---|---|
| `00-setup` | `starting-data.md` completado por el usuario; fuente única de los datos de partida |
| `01_CLIENT_SPECS` | Especificaciones técnicas del cliente |
| `02-requirements` | Requisitos técnicos, listas de cargas, datos de entrada para cálculos (p. ej. `INPUT_SLD_DATA.xlsx`) |
| `03_DRAWINGS` | Planos recibidos del cliente |
| `04_reports` | Informes y estudios previos |
| `05_standards` | Normas y reglamentos aplicables al proyecto |
| `06_CONTRACTS` | Contratos y pliegos recibidos |
| `07_EXISTING_DOCS` | Documentación existente de la instalación |
| `08_PHOTOS` | Fotografías del sitio y equipos existentes |
| `09_communications` | Correos, actas y comunicaciones (`MINUTES-000_Initial_Request.md`, etc.) |
| `99-unclassified` | Depósito inicial; Claude clasifica y mueve a 01–09 |

---

## 4.5 Tabla «Dónde vive cada archivo»

Ver `CLAUDE.md`, sección 6.3 (fuente única para la localización de cada archivo).

---

## 4.6 Notas de uso

1. Las carpetas de disciplina se crean **automáticamente** al ejecutar `iniciar proyecto` → `aprobar charter`, durante la Fase 4 de `M3`. No crearlas a mano antes de ese momento.
2. Si una disciplina se agrega al alcance después de aprobado el charter, se registra como `rfc-nnn` → `DEC-nnn`, y Claude crea la carpeta correspondiente en ese momento.
3. Si una disciplina se elimina del alcance, la carpeta existente se mueve a `15_ARCHIVE` de la propia disciplina; nunca se borra contenido de ingeniería.
4. La estructura interna (01–15) es la misma para todas las disciplinas. No todas las subcarpetas tendrán contenido en todos los proyectos: las vacías se conservan con `.gitkeep` para mantener la estructura de referencia.
