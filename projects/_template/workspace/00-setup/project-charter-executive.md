# project-charter-executive.md — Charter ejecutivo (lienzo de inicio del proyecto)

| Campo | Valor |
|---|---|
| Proyecto | `[DEFINIR]` |
| Versión de la línea base | 0.1 (borrador) |
| Estado | BORRADOR |
| Fecha | `[DEFINIR]` |

---

# GUÍA DEL ARCHIVO (no editar; no figura en el archivo generado para el proyecto)

## 1. Objetivo

Es la **salida ejecutiva** del charter: el proyecto en **una sola página**, para mostrárselo a jefes y a la dirección sin que lean el charter técnico. Reproduce el *Project Initiation Canvas* de PM² (misma disposición de cajas, pestañas, matriz de riesgos, organigrama de gobierno, círculos de partes interesadas e hitos por fase), sin logos ni código QR y con los textos en español.

La salida que se muestra es el **PDF** `PROJECT_charter_EXECUTIVE.pdf`. Este archivo `.md` es su **contenido**: el texto que el exportador `charter_exporter.py` (CAL-013) dibuja en HTML + CSS y exporta a PDF. Se eligió HTML + CSS y no Word porque el lienzo tiene elementos (pestañas sobre el borde de las cajas, esquinas redondeadas, matriz 5×5, círculos, flechas de fase) que Word no reproduce con fidelidad y que se desordenan al editar.

## 2. Alcance

Es una **vista derivada, no una fuente**. Se alimenta de **toda la información que el framework guarda en sus archivos fuente** (`STARTING_DATA`, `PROJECT_SCOPE`, `GOALS`, `CLIENT_REQUIREMENTS`, `PROJECT_INFORMATION`, `DELIVERABLES`, `ASSUMPTIONS_AND_decisions`, `SCHEDULE_CCPM` si hay gestión) a través de `project-charter.md`, y no agrega ningún dato propio. Comparte la línea base del charter técnico (misma versión, fecha y estado).

## 3. Forma de utilización

1. Claude lo genera junto con `project-charter.md` al final de `iniciar proyecto`, ejecuta `python3 -B 98_LIBRARY/calculations/charter_exporter.py 02_PROJECT/project-charter-executive.md` (produce `PROJECT_charter_EXECUTIVE.pdf` junto al `.md`) y presenta ambos. Se regenera cada vez que el charter se regenera (nueva línea base) y con el comando **`charter ejecutivo`**. No se edita a mano: el dato se corrige en su fuente y todo se regenera.
2. El archivo del proyecto contiene **solo el lienzo** (lo que está debajo de «LIENZO EJECUTIVO»).
3. **La auditoría valida que el charter técnico y el ejecutivo digan lo mismo** (`project-audit.md`, A3-19 y A3-20; verificación mecánica en `document_verifier.py`): misma versión, fecha y estado; los mismos `ALD`, `EXC`, `CAC`, `SUP`, `RIE` y `PQ`; mismos niveles de riesgo; mismo orden y dependencias de paquetes; mismas fechas de hitos; mismo tratamiento del costo; y que el PDF corresponde al `.md` vigente (sello `sha256` en su pie).

## 4. Formato del contenido (lo que lee el exportador)

Cada caja es un título `###` con el **nombre exacto** de la lista siguiente, seguido de viñetas (`- texto`), de una tabla o de un párrafo, según se indica. Un comentario HTML al final de la línea (`<!-- fuente: ALD-nnn, ALD-nnn -->`) registra el ID de donde sale el dato: no se ve en el PDF, pero permite a la auditoría comparar con el charter técnico. Todo ID del charter que pertenezca a los tipos comparados debe figurar aquí.

| Caja (título `###`) | Contenido | Sección de `project-charter.md` |
|---|---|---|
| `Alcance` | Tabla «Dentro del alcance \| Fuera del alcance»; una fila por par de ítems | 3.1 |
| `Contexto` | Viñetas | 2 |
| `Entregables` | Viñetas | 3.4 |
| `Resultados deseados` | Viñetas | 3.2 (`goals.md`) |
| `Beneficios` | Viñetas | 2 y 3.2 |
| `Supuestos` | Viñetas, cada una con su `SUP-nnn` en el comentario | 3.7 |
| `Restricciones y dependencias` | Viñetas | 3.6 |
| `Hitos` | Tabla «Inicio \| Planificación \| Ejecución \| Cierre» de una fila; varios hitos de una celda separados con « · », cada uno con su fecha `AAAA-MM-DD` | 4.2 |
| `Riesgos` | Tabla «Riesgo \| Prob. \| Impacto \| Nivel \| Qué haremos»; la celda de riesgo empieza con `RIE-nnn · `. La matriz 5×5 la dibuja el exportador desde esta tabla | 3.8 |
| `Gobierno y equipo` | Tabla «Rol \| Quién»; el rol lleva su sigla entre paréntesis: `AGB`, `PSC`, `PO`, `SP`, `BM`, `PM`, `BIG`, `PCT`, `PST` | 6.1 y 6.2 |
| `Otras partes interesadas` | Tabla «Parte interesada \| Interés \| Influencia (Alta / Media / Baja)» | 6.3 |
| `Presupuesto` | Párrafo: «A definir por el cliente.» o el monto tal como lo dio el usuario (`DEC-nnn`) | 4.1 |
| `Plazo` | Párrafo con el plazo contractual y su unidad | 4.2 |
| `Criterios críticos de éxito` | Viñetas, con `CAC-nnn` cuando corresponda | 3.2 |
| `Factores críticos de éxito` | Viñetas | 3.6, 3.7 y 8 |
| `Desglose del trabajo` | Tabla «Orden \| Paquete \| Qué contiene \| Depende de» | 7 |
| `Se solicita a la dirección` | Viñetas | 8 y 9 |

Antes de las cajas va el bloque de encabezado: un título `##` con el nombre del proyecto, la tabla «Proyecto \| Versión \| Fecha \| Estado» y la línea «**En una frase:** …».

## 5. Reglas de redacción

- **Una página**: entre 2 y 5 viñetas por caja, una línea cada una, sin párrafos largos. Si no cabe, el exportador avisa y se acorta el texto, no la letra.
- **Lenguaje de dirección**: frases cortas y sin siglas sin explicar. No se muestran IDs en el texto visible, salvo `PQ-nn` y `RIE-nnn`, que la dirección verá en los informes.
- **Cifras iguales a las del charter**: plazos, cantidades y niveles de riesgo no se redondean ni se reinterpretan.
- **Sin costos**: `Presupuesto` dice «A definir por el cliente.» mientras la sección 4.1 del charter esté `[DEFINIR]`; si el usuario autorizó un monto (`DEC-nnn`), se copia tal cual, sin cálculos (`DOCUMENT_RULES.md`, RG-21).
- **Lo pendiente se dice**: un `[DEFINIR]` del charter se escribe aquí `[DEFINIR]` y el PDF lo muestra como «Pendiente de definir»; lo que depende de la dirección va en `Se solicita a la dirección`.

---

# LIENZO EJECUTIVO (generado por Claude)

## `[DEFINIR]`

| Proyecto | Versión | Fecha | Estado |
|---|---|---|---|
| `[DEFINIR]` | 0.1 | `[DEFINIR]` | BORRADOR |

**En una frase:** `[DEFINIR]`

### Alcance

| Dentro del alcance | Fuera del alcance |
|---|---|
| `[DEFINIR]` | `[DEFINIR]` |

### Contexto

- `[DEFINIR]`

### Entregables

- `[DEFINIR]`

### Resultados deseados

- `[DEFINIR]`

### Beneficios

- `[DEFINIR]`

### Supuestos

- `[DEFINIR]`

### Restricciones y dependencias

- `[DEFINIR]`

### Hitos

| Inicio | Planificación | Ejecución | Cierre |
|---|---|---|---|
| `[DEFINIR]` | `[DEFINIR]` | `[DEFINIR]` | `[DEFINIR]` |

### Riesgos

| Riesgo | Prob. | Impacto | Nivel | Qué haremos |
|---|---|---|---|---|
| `[DEFINIR]` | | | | |

### Gobierno y equipo

| Rol | Quién |
|---|---|
| Cuerpo de gobierno (AGB) | `[DEFINIR]` |
| Comité de dirección (PSC) | `[DEFINIR]` |
| Propietario del proyecto (PO) | `[DEFINIR]` |
| Proveedor de la solución (SP) | `[DEFINIR]` |
| Gerente de negocio (BM) | `[DEFINIR]` |
| Responsable del proyecto (PM) | `[DEFINIR]` |
| Grupo de implementación (BIG) | `[DEFINIR]` |
| Equipo central (PCT) | `[DEFINIR]` |
| Equipo de apoyo (PST) | `[DEFINIR]` |

### Otras partes interesadas

| Parte interesada | Interés | Influencia |
|---|---|---|
| `[DEFINIR]` | | |

### Presupuesto

A definir por el cliente.

### Plazo

`[DEFINIR]`

### Criterios críticos de éxito

- `[DEFINIR]`

### Factores críticos de éxito

- `[DEFINIR]`

### Desglose del trabajo

| Orden | Paquete | Qué contiene | Depende de |
|---|---|---|---|
| 1 | PQ-01 | `[DEFINIR]` | — |

### Se solicita a la dirección

- `[DEFINIR]`
