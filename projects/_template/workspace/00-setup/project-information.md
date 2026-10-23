# project-information.md — Información General y Parámetros Maestros

| Campo | Valor |
|---|---|
| Proyecto | `[DEFINIR]` |
| Código de proyecto | `[DEFINIR]` |
| Versión | 0.1 |
| Fecha | `[DEFINIR]` |
| Responsable | `[DEFINIR]` |

---

# GUÍA DEL ARCHIVO (no editar)

## 1. Objetivo

Concentrar los **hechos técnicos** del proyecto: instalación, sitio, normas, condiciones y **parámetros técnicos maestros**. Es la **fuente única** de tensiones, potencias, frecuencia, régimen de neutro, niveles de cortocircuito, condiciones ambientales y normas aplicables. Ningún otro documento debe redefinir estos valores: los referencia por ID.

## 2. Alcance

Cubre ubicación, descripción, parámetros técnicos, sistema de distribución, instalaciones afectadas, normas, condiciones especiales, restricciones operativas, históricos, contactos y documentos de entrada. **No contiene** los datos que declara el usuario (cliente, código, qué se contrata, disciplinas, fases, plazo, modo de gestión: `starting-data.md`), el alcance ni los criterios de aceptación (`project-scope.md`), la línea base (`project-charter.md`), criterios de diseño (`engineering-standards.md`) ni requisitos contractuales (`client-requirements.md`).

## 3. Forma de utilización

1. Claude lo completa en `iniciar proyecto` con la documentación depositada en `01-input` y lo sigue completando en `planning` con visitas y nueva documentación del cliente.
2. Cada parámetro lleva **fuente** y **estado** (`CONFIRMED`, `ASSUMED`, `PENDING`, `DERIVED`). Un parámetro `ASSUMED` se vincula a un `SUP-nnn`. Un parámetro `DERIVED` es el que se **calcula o se infiere** de otros: su *Ref.* cita el documento y la revisión que lo origina (por ejemplo la memoria de cálculo de cargas para `PAR-004` y `PAR-005`) o la regla de derivación escrita y citable (por ejemplo la frecuencia, deducida de otro crítico confirmado); se actualiza cuando cambia ese documento, lleva su revisión y no necesita un `SUP` propio, pero si el cálculo usó supuestos abiertos hereda su dependencia (cita los `SUP-nnn`).
3. Si un dato cambia, se actualiza **aquí primero**, se registra la decisión, y luego se auditan los documentos que lo usan.
4. Durante cualquier auditoría, los valores de los documentos se contrastan contra la tabla de *Parámetros maestros*.
5. No se escriben datos inventados: usar `[DEFINIR]` hasta contar con fuente.

## 4. Estructura recomendada

1. Identificación técnica (A).
2. Descripción (B).
3. Parámetros maestros (`PAR-nnn`) (D).
4. Sistema de distribución (E).
5. Instalaciones afectadas (F).
6. Normas aplicables (G).
7. Condiciones especiales (H) y restricciones operativas (I).
8. Proyectos históricos del cliente (J).
9. Contactos e interfaces (K).
10. Documentos de entrada recibidos (L).
11. Parámetros técnicos por disciplina (P).

Las secciones C, M, N y O no existen en este archivo: el alcance, las exclusiones y los criterios de aceptación están en `project-scope.md` y la línea base en `project-charter.md`. Las letras se conservan para no romper referencias.

## 5. Ejemplos (ilustrativos, no vinculantes)

| ID | Parámetro | Valor de ejemplo | Fuente | Estado |
|---|---|---|---|---|
| EJ-PAR-001 | Tensión nominal MT | 13,2 kV | Datos de la distribuidora | CONFIRMED |
| EJ-PAR-002 | Frecuencia | 50 Hz | Sistema local | CONFIRMED |
| EJ-PAR-003 | Régimen de neutro BT | TN-S | Decisión EJ-DEC-004 | CONFIRMED |
| EJ-PAR-004 | Nivel de cortocircuito en punto de conexión | `[DEFINIR]` | Pendiente EJ-INF-002 | PENDING |
| EJ-PAR-005 | Demanda máxima prevista | 18 kW | Memoria de cálculo de cargas, revisión 00.0 | DERIVED |

## 6. Buenas prácticas

- Registrar la fuente de **cada** dato (documento, fecha, revisión).
- Incluir unidades siempre; usar el SI.
- Diferenciar **valor nominal** de **valor de diseño** y de **valor medido**.
- Mantener esta información corta y tabular; las explicaciones van en memorias.
- Revisar la tabla antes de redactar cualquier memoria de cálculo.

---

# REGISTRO DEL PROYECTO (completar)

## A. Identificación técnica

Los datos que declara el usuario (cliente, proyecto, código, rol, qué se contrata, disciplinas, fases, entregables, plazo, modo de gestión) **están en `starting-data.md`** y no se repiten aquí.

| Campo | Valor |
|---|---|
| Tipo de proyecto (plantilla de carpetas A/B/C/D/E) | `[DEFINIR]` |
| Disciplina principal | `[DEFINIR]` |
| Ubicación (planta, dirección, coordenadas) | `[DEFINIR]` |
| Responsable por el cliente | `[DEFINIR]` |
| Responsable técnico propio | `[DEFINIR]` |
| Contrato / orden de compra | `[DEFINIR]` |
| **ifa por fase** (cada fase contratada se emite como ifa y, con `cliente aprueba`, dispara la siguiente; la ifc se emite al terminar la Ejecutiva; omitir una fase o su ifa es una `DEC`) | `[DEFINIR]` |
| Ruta de la plantilla maestra y de la biblioteca (`98_LIBRARY/`) | `[DEFINIR]` |
| Versión de la plantilla maestra con que parte el proyecto (versión y fecha de `CLAUDE.md` y huella abreviada, ver `CLAUDE.md`, 8.1 (copia de la plantilla, `M3`)) | `[DEFINIR]` |

## B. Descripción del proyecto

`[DEFINIR]` — Descripción breve (máx. 10 líneas): qué es la instalación, qué se modifica o construye y con qué finalidad.

## D. Parámetros maestros

| ID | Parámetro | Valor | Unidad | Fuente | Estado (CONFIRMED / ASSUMED / PENDING / DERIVED) | Ref. |
|---|---|---|---|---|---|---|
| PAR-001 | Tensión nominal de media tensión | `[DEFINIR]` | kV | | PENDING | |
| PAR-002 | Tensión nominal de baja tensión | `[DEFINIR]` | V | | PENDING | |
| PAR-003 | Frecuencia | `[DEFINIR]` | Hz | | PENDING | |
| PAR-004 | Potencia instalada total (derivada de la memoria de cálculo de cargas; *Ref.* = código y revisión de esa memoria) | `[DEFINIR]` | kW / kVA | | PENDING | |
| PAR-005 | Demanda máxima prevista (derivada de la memoria de cálculo de cargas; *Ref.* = código y revisión de esa memoria) | `[DEFINIR]` | kW / kVA | | PENDING | |
| PAR-006 | Potencia de cortocircuito / corriente de falla en punto de conexión | `[DEFINIR]` | MVA / kA | | PENDING | |
| PAR-007 | Régimen de neutro MT | `[DEFINIR]` | — | | PENDING | |
| PAR-008 | Régimen de neutro BT | `[DEFINIR]` | — | | PENDING | |
| PAR-009 | Temperatura ambiente de diseño | `[DEFINIR]` | °C | | PENDING | |
| PAR-010 | Altitud de instalación | `[DEFINIR]` | m s.n.m. | | PENDING | |
| PAR-011 | Resistividad del terreno | `[DEFINIR]` | Ω·m | | PENDING | |
| PAR-012 | Clasificación de áreas (peligrosas / no peligrosas) | `[DEFINIR]` | — | | PENDING | |
| PAR-013 | Grado de protección mínimo (IP) por ambiente | `[DEFINIR]` | — | | PENDING | |
| PAR-014 | Factor de potencia objetivo | `[DEFINIR]` | — | | PENDING | |

Agregar filas `PAR-nnn` según necesidad. Cada fila nueva debe tener fuente. Hasta que exista la memoria de cargas, `PAR-004` y `PAR-005` pueden quedar `PENDING` o `ASSUMED` (con `SUP`); al generarse la memoria pasan a `DERIVED`.

## E. Sistema de distribución

| Elemento | Descripción |
|---|---|
| Punto de suministro / acometida | `[DEFINIR]` |
| Esquema de distribución MT (radial, anillo, etc.) | `[DEFINIR]` |
| Subestaciones / centros de transformación existentes | `[DEFINIR]` |
| Generación propia / respaldo / UPS | `[DEFINIR]` |
| Esquema de puesta a tierra existente | `[DEFINIR]` |
| Diagramas unifilares existentes (código y revisión) | `[DEFINIR]` |

## F. Instalaciones afectadas

| ID | Instalación / área | Tipo de intervención (nueva, modificación, retiro, sin cambio) | Criticidad operativa | Observaciones |
|---|---|---|---|---|
| INS-001 | `[DEFINIR]` | `[DEFINIR]` | `[DEFINIR]` | |

## G. Normas aplicables

| ID | Norma / reglamento | Edición / año | Origen (obligatoria legal / contractual / referencia de buena práctica) | Alcance de aplicación | `NRM-nnn` de la biblioteca (o «—» si no está indexada) |
|---|---|---|---|---|---|
| NOR-001 | `[DEFINIR]` — referencia principal IEC (ver `engineering-standards.md`) | `[DEFINIR]` | | | |

Registrar también reglamentación local y normas corporativas del cliente. Verificar la **vigencia** de cada edición antes de entregar.

## H. Condiciones especiales

| ID | Condición | Impacto esperado | Tratamiento |
|---|---|---|---|
| CON-001 | `[DEFINIR]` (p. ej. ambiente corrosivo, polvo combustible, intemperie, zona sísmica, cercanía a costa) | | |

## I. Restricciones operativas

| ID | Restricción | Ventana / condición | Fuente |
|---|---|---|---|
| ROP-001 | `[DEFINIR]` (p. ej. cortes permitidos, trabajos en caliente, accesos, permisos de trabajo) | | |

## J. Proyectos históricos del cliente

| Proyecto | Año | Ruta / ubicación del repositorio | Aspectos a reutilizar (estructura, nomenclatura, CAD, criterios) |
|---|---|---|---|
| `[DEFINIR]` | | | |

## K. Contactos e interfaces

| Rol | Nombre | Organización | Contacto | Responsabilidad |
|---|---|---|---|---|
| `[DEFINIR]` | | | | |

## L. Documentos de entrada recibidos

| Código / nombre | Revisión | Fecha de recepción | Emisor | Uso en el proyecto |
|---|---|---|---|---|
| `[DEFINIR]` | | | | |


## P. Parámetros técnicos por disciplina

Los parámetros eléctricos generales están en la sección D (`PAR-nnn`). Cada disciplina involucrada agrega los suyos con ID `PAR-<DISC>-nnn` (letra de disciplina de `CAD_standards.md`). Solo se completan las disciplinas declaradas en `starting-data.md`, sección 3. Todo valor lleva fuente y estado (CONFIRMED / ASSUMED / PENDING).

| Disciplina | Parámetros mínimos a definir |
|---|---|
| **C** Civil | Estudio geotécnico y capacidad portante; topografía; cotas de nivel; cargas de equipos; período de retorno de lluvia; clase de exposición ambiental; servicios enterrados existentes |
| **S** Estructuras | Acciones de viento, sismo y nieve; sobrecargas; norma de diseño; materiales; exigencia de resistencia al fuego |
| **A** Arquitectura | Programa de áreas; rutas de evacuación; exigencias de compartimentación; terminaciones y ambiente |
| **M** Mecánica y termomecánica | Equipos y capacidades; fluidos; presiones y temperaturas de diseño y operación; servicios auxiliares disponibles; combustible; eficiencia y garantías; código de diseño |
| **P** Cañerías | Servicios y fluidos; presión y temperatura de diseño; clases de cañería; materiales y sobreespesor por corrosión; requisitos de aislación y traceado; pruebas exigidas |
| **H** HVAC | Condiciones exteriores e interiores de diseño; cargas térmicas internas; caudales de ventilación y presurización; áreas limpias o clasificadas; fuente de energía fría y caliente; límites de ruido |
| **F** Incendio (combate) | Clasificación de riesgo y ocupación por área; sistemas exigidos; criterio de diseño (densidad / área, caudales); fuente de agua, presión y caudal disponibles; reserva y autonomía; autoridad o aseguradora y su norma |
| **F** Incendio (detección) | Riesgo por área; tipo de sistema (direccionable / convencional); central y autonomía de baterías; notificación y evacuación; integraciones requeridas (HVAC, extinción, SCADA, accesos) |
| **I** Instrumentación y control | Señales y protocolos; arquitectura de control; áreas clasificadas; requisitos SIL; sistemas existentes a integrar |
| **T** Telecomunicaciones | Servicios (datos, voz, CCTV, acceso, radio); categoría de cableado; topología; fibra; redes existentes |

**Plantilla de registro por disciplina** (repetir una tabla por disciplina declarada):

| ID | Parámetro | Valor | Unidad | Fuente | Estado | Ref. |
|---|---|---|---|---|---|---|
| PAR-<DISC>-001 | `[DEFINIR]` | | | | PENDING | |
