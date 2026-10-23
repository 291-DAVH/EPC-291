# engineering-standards.md — Biblioteca de Criterios de Ingeniería

| Campo | Valor |
|---|---|
| Referencia normativa principal | IEC (eléctrica); NFPA / EN / ISO (incendio); ASME / API / ISO (mecánica, termomecánica, cañerías); ASHRAE / SMACNA / EN / ISO (HVAC); ACI / AISC / ASCE / Eurocódigos (civil y estructuras); ISO/IEC y TIA (telecomunicaciones). Verificar vigencia y aplicabilidad local. |
| Versión de la biblioteca | 1.0 |
| Fecha | 2026-10-06 |
| Responsable | Líder Técnico |

---

# GUÍA DEL ARCHIVO (no editar)

## 1. Objetivo

Disponer de una **biblioteca reutilizable de criterios de ingeniería**, con identificador único, referencia normativa y parámetro de proyecto, que permita diseñar de forma consistente y auditar el cumplimiento. Cada criterio `ENG-xxx-nnn` es un eslabón de la cadena de trazabilidad (Requisito → **Criterio de Ingeniería** → Documento).

## 2. Alcance

Cubre **diez disciplinas** y sus interfaces. **Eléctrica** (15 áreas, secciones 7 a 21): diseño general, media tensión, baja tensión, conductores, canalizaciones, bandejas, tableros, protecciones, transformadores, puesta a tierra, instrumentación, automatización, seguridad eléctrica, pre-commissioning y commissioning. **Otras disciplinas** (secciones 22 a 32): civil, estructuras, mecánica y equipos, termomecánica, cañerías, HVAC, protección contra incendio (combate), detección y alarma de incendio, telecomunicaciones, arquitectura e interfaces entre disciplinas. **Iluminación normal y de emergencia (`ILU`)** es un área de eléctrica y se ubica en la sección 35 (después de las secciones 33 y 34, que son transversales). Solo se evalúan las disciplinas declaradas en `project-information.md`.

Los criterios son **de método y de exigencia**. Los **valores numéricos de diseño** (tensiones, factores, límites, márgenes) no se fijan aquí salvo que provengan de una norma citada: se definen para cada proyecto en `project-information.md` (parámetros `PAR-nnn`) o en una decisión de `assumptions-and-decisions.md` (`DEC-nnn`), y se marcan `[DEFINIR]` hasta entonces.

## 3. Forma de utilización

1. **Selección:** al iniciar el proyecto, marcar en la columna *Aplica* de cada criterio `SÍ`, `NO` (con motivo) o `PARCIAL`. Cuando una disciplina o área completa queda fuera de alcance, se marca cada criterio con `NO (DEC-nnn)` citando la decisión que lo justifica; se admite hacerlo por bloque con la **tabla de aplicabilidad por bloque** del inicio de la biblioteca (una fila por sección, con `SÍ` / `NO` / `PARCIAL` y la `DEC-nnn`): una fila `SÍ` o `NO` rige para todos los criterios del bloque y solo se completa la columna *Aplica* de cada criterio cuando el bloque es `PARCIAL` o un criterio difiere del resto. Un criterio no evaluado es un hallazgo de auditoría.
2. **Parametrización:** completar `[DEFINIR]` con el valor y su fuente (`PAR-nnn` o `DEC-nnn`).
3. **Aplicación:** las memorias, cálculos, especificaciones y planos citan el ID del criterio que cumplen.
4. **Cliente:** si `client-requirements.md` impone un criterio más exigente o distinto, se agrega en la sección 33 con origen CLIENTE y se registra la decisión. Un criterio del cliente menos exigente que una norma de cumplimiento obligatorio se reporta como conflicto (ver jerarquía en `CLAUDE.md`).
5. **Vigencia:** las normas se citan por serie. La **edición vigente y su aplicabilidad legal deben verificarse en cada proyecto** y registrarse en `project-information.md` (`NOR-nnn`). Esta biblioteca no reemplaza la lectura de la norma: los valores se verifican contra el archivo de `98_LIBRARY/standards/` consultando solo las normas relevantes al tema (`standards-index.md`).
6. **Mejora continua:** los criterios validados en proyectos recurrentes se incorporan a esta biblioteca mediante decisión registrada.

## 4. Estructura recomendada

Cada tabla de criterios usa las columnas:

| Columna | Contenido |
|---|---|
| ID | `ENG-<ÁREA>-nnn`. Eléctrica: `GEN`, `MT`, `BT`, `CND`, `CAN`, `BAN`, `TAB`, `PRO`, `TRA`, `PAT`, `INS`, `AUT`, `SEG`, `PRE`, `COM`. Otras: `CIV`, `EST`, `MEC`, `TER`, `PIP`, `HVA`, `FFI`, `FDE`, `TEL`, `ARQ`, `INT`; iluminación (área eléctrica): `ILU` |
| Criterio | Exigencia redactada de forma verificable |
| Referencia | Norma IEC (serie) y/o documento fuente |
| Parámetro / nota | Dato de proyecto a completar o aclaración |
| Aplica | SÍ / NO / PARCIAL (completar por proyecto) |

## 5. Ejemplos de uso (ilustrativos)

- Una memoria de cálculo de conductores cita `ENG-CND-002` (verificación por caída de tensión) y `ENG-CND-004` (verificación térmica ante cortocircuito) e incluye el valor de `PAR-006`.
- Una auditoría de ingeniería verifica que para `ENG-TAB-003` exista evidencia (tipo de ensayo o certificado) en la especificación del tablero.
- Un requisito del cliente sobre canalizaciones se traduce en un criterio `ENG-CAN-nnn` con origen CLIENTE y se vincula en `traceability-matrix.md`.

## 6. Buenas prácticas

- Citar siempre el ID del criterio en lugar de repetir su texto en los documentos.
- No usar un valor numérico sin fuente identificable; si no existe, `[DEFINIR]`.
- Justificar por escrito toda desviación (decisión `DEC-nnn`), nunca omitirla.
- Revisar las normas citadas cuando se publique una nueva edición.
- Mantener el criterio breve y verificable: si no se puede auditar, reescribirlo.

---

# 98_LIBRARY DE CRITERIOS

## Aplicabilidad por bloque (completar al iniciar el proyecto)

| Sección | Bloque | Aplica (`SÍ` / `NO` / `PARCIAL`) | Decisión (`DEC-nnn`) | Observaciones |
|---|---|---|---|---|
| 7 | Diseño eléctrico general (`GEN`) | | | |
| 8 | Media tensión (`MT`) | | | |
| 9 | Baja tensión (`BT`) | | | |
| 10 | Conductores (`CND`) | | | |
| 11 | Canalizaciones (`CAN`) | | | |
| 12 | Bandejas portacables (`BAN`) | | | |
| 13 | Tableros (`TAB`) | | | |
| 14 | Protecciones (`PRO`) | | | |
| 15 | Transformadores (`TRA`) | | | |
| 16 | Puesta a tierra (`PAT`) | | | |
| 17 | Instrumentación (`INS`) | | | |
| 18 | Automatización (`AUT`) | | | |
| 19 | Seguridad eléctrica (`SEG`) | | | |
| 20 | Pre-COMMISSIONING (`PRE`) | | | |
| 21 | COMMISSIONING (`COM`) | | | |
| 22 | Civil (`CIV`) | | | |
| 23 | Estructuras (`EST`) | | | |
| 24 | Mecánica y equipos (`MEC`) | | | |
| 25 | Termomecánica (`TER`) | | | |
| 26 | Cañerías (`PIP`) | | | |
| 27 | HVAC (`HVA`) | | | |
| 28 | Protección contra incendio — combate (`FFI`) | | | |
| 29 | Detección y alarma de incendio (`FDE`) | | | |
| 30 | Telecomunicaciones (`TEL`) | | | |
| 31 | Arquitectura (`ARQ`) | | | |
| 32 | Interfaces entre disciplinas (`INT`) | | | |
| 33 | Criterios específicos del proyecto o del cliente (`—`) | | | |
| 35 | Iluminación normal y de emergencia (`ILU`) | | | |

La sección 34 (normas complementarias) no lleva criterios y no figura en la tabla.

## 7. Diseño eléctrico general (GEN)

| ID | Criterio | Referencia | Parámetro / nota | Aplica |
|---|---|---|---|---|
| ENG-GEN-001 | La tensión nominal de los sistemas se adopta de los valores normalizados y de los datos del suministro. | IEC 60038 | PAR-001, PAR-002, PAR-003 | |
| ENG-GEN-002 | Debe elaborarse un balance de cargas con factores de simultaneidad y de utilización justificados, y reserva de capacidad. | IEC 60364-1 (criterios generales) | Reserva: `[DEFINIR]` | |
| ENG-GEN-003 | Las corrientes de cortocircuito (máx. y mín.) se calculan para cada nivel de tensión y barra relevante. | IEC 60909 | PAR-006 | |
| ENG-GEN-004 | Debe realizarse estudio de flujo de carga y, cuando corresponda, de arranque de motores y caída de tensión transitoria. | Buenas prácticas; IEC 60034 (motores) | `[DEFINIR]` | |
| ENG-GEN-005 | Debe evaluarse el impacto de armónicos y compensación de reactiva cuando existan cargas no lineales o penalización por factor de potencia. | IEC 61000 (serie) | PAR-014 | |
| ENG-GEN-006 | Los esquemas y símbolos se elaboran según símbolos gráficos y designación de referencia normalizados. | IEC 60617; IEC 81346 | Ajustar a norma corporativa del cliente | |
| ENG-GEN-007 | Toda hipótesis de diseño debe estar registrada como supuesto o decisión. | `CLAUDE.md` | SUP-nnn / DEC-nnn | |
| ENG-GEN-008 | Los equipos y materiales se seleccionan según las condiciones ambientales y de servicio del sitio (temperatura, altitud, ambiente). | IEC 60721 (clasificación ambiental); IEC 60529 | PAR-009, PAR-010, PAR-013 | |

## 8. Media tensión (MT)

| ID | Criterio | Referencia | Parámetro / nota | Aplica |
|---|---|---|---|---|
| ENG-MT-001 | Las instalaciones de potencia de tensión superior a 1 kV c.a. se proyectan conforme a la norma de instalaciones de potencia. | IEC 61936-1 | NOR-nnn | |
| ENG-MT-002 | Las celdas de MT cumplen la norma de aparamenta bajo envolvente metálica, con clasificación de arco interno definida. | IEC 62271-1; IEC 62271-200 | Clase IAC: `[DEFINIR]` | |
| ENG-MT-003 | Interruptores, seccionadores y contactores se especifican con poder de corte y de cierre mayores al nivel de falla en su ubicación. | IEC 62271-100; IEC 62271-102 | PAR-006 | |
| ENG-MT-004 | La coordinación de aislamiento y la protección contra sobretensiones se justifican según el nivel de aislamiento y el entorno. | IEC 60071 (serie); IEC 60099 (serie) | Nivel de aislamiento: `[DEFINIR]` | |
| ENG-MT-005 | Los transformadores de medida (corriente y tensión) se especifican con clase y carga acordes a su uso (medición / protección). | IEC 61869 (serie) | `[DEFINIR]` | |
| ENG-MT-006 | Los cables de MT se especifican con nivel de tensión, aislación, pantalla y sección verificada térmicamente ante cortocircuito. | IEC 60502-2; IEC 60287 (serie) | Aislación y pantalla: `[DEFINIR]` | |
| ENG-MT-007 | Las terminaciones y empalmes se especifican y ejecutan según instrucciones del fabricante, con personal calificado. | IEC 60502-4 | | |
| ENG-MT-008 | Las distancias de seguridad, accesos, ventilación y contención de fuego en recintos de MT se definen según la norma de instalaciones de potencia. | IEC 61936-1 | | |

## 9. Baja tensión (BT)

| ID | Criterio | Referencia | Parámetro / nota | Aplica |
|---|---|---|---|---|
| ENG-BT-001 | Las instalaciones de BT se proyectan según los requisitos generales de instalaciones eléctricas de BT, o reglamento local equivalente cuando sea de cumplimiento obligatorio. | IEC 60364 (serie); reglamento local `[VERIFICAR]` | NOR-nnn | |
| ENG-BT-002 | Debe definirse el esquema de conexión a tierra (TN-S, TN-C-S, TT, IT) por instalación, con justificación. | IEC 60364-1; IEC 60364-4-41 | PAR-008 | |
| ENG-BT-003 | La protección contra sobrecorriente se coordina con la capacidad de los conductores. | IEC 60364-4-43 | | |
| ENG-BT-004 | La protección contra sobretensiones y perturbaciones electromagnéticas se evalúa por zona. | IEC 60364-4-44; IEC 61000 (serie) | | |
| ENG-BT-005 | La aparamenta de BT se selecciona por poder de corte, categoría de utilización y coordinación. | IEC 60947 (serie) | | |
| ENG-BT-006 | Los circuitos de servicios de seguridad y emergencia se identifican, alimentan y protegen según criterios específicos. | IEC 60364-5-56 | | |
| ENG-BT-007 | El diseño de alumbrado cumple niveles de iluminancia definidos para cada tarea o área. | Norma de iluminación aplicable `[DEFINIR]` | Niveles: `[DEFINIR]` | |

## 10. Conductores (CND)

| ID | Criterio | Referencia | Parámetro / nota | Aplica |
|---|---|---|---|---|
| ENG-CND-001 | La sección se verifica por capacidad de conducción de corriente, con factores de corrección por temperatura, agrupamiento y modo de instalación. | IEC 60364-5-52; IEC 60287 (serie) | PAR-009 | |
| ENG-CND-002 | La sección se verifica por caída de tensión en régimen y, cuando corresponda, en arranque. | IEC 60364-5-52 | Límite: `[DEFINIR]` | |
| ENG-CND-003 | La sección se verifica por protección contra choque eléctrico (impedancia de lazo / tiempo de actuación). | IEC 60364-4-41 | | |
| ENG-CND-004 | La sección se verifica térmicamente ante la corriente de cortocircuito durante el tiempo de despeje. | IEC 60949; IEC 60909 | PAR-006 | |
| ENG-CND-005 | Los conductores cumplen la norma de construcción aplicable a su tensión y clase de conductor. | IEC 60228; IEC 60502-1; IEC 60502-2 | | |
| ENG-CND-006 | El comportamiento frente al fuego (no propagación de llama, baja emisión de humos y halógenos, resistencia al fuego) se define por ambiente y circuito. | IEC 60332 (serie); IEC 61034; IEC 60754; IEC 60331 | Circuitos de seguridad: `[DEFINIR]` | |
| ENG-CND-007 | La identificación de cables y conductores es única, legible y consistente con las listas de cables. | `DOCUMENT_RULES.md`; norma corporativa | | |
| ENG-CND-008 | Los radios de curvatura y esfuerzos de tendido se verifican con datos del fabricante. | Datos del fabricante | | |

## 11. Canalizaciones (CAN)

| ID | Criterio | Referencia | Parámetro / nota | Aplica |
|---|---|---|---|---|
| ENG-CAN-001 | Los caños y conductos cumplen la norma de sistemas de conductos y el grado IP requerido. | IEC 61386 (serie); IEC 60529 | PAR-013 | |
| ENG-CAN-002 | El factor de ocupación de caños y ductos respeta el límite definido, con reserva. | IEC 60364-5-52; guía del fabricante | Límite: `[DEFINIR]` | |
| ENG-CAN-003 | Se segregan físicamente circuitos de MT, BT potencia, control, señales y comunicaciones según criterio definido. | IEC 60364-5-52; IEC 61000-5-2 | Distancias: `[DEFINIR]` | |
| ENG-CAN-004 | Los canales y electroductos cumplen su norma de producto. | IEC 61084 (serie); IEC 61439-6 | | |
| ENG-CAN-005 | La canalización enterrada define profundidad, protección mecánica, señalización y separación con otros servicios. | IEC 60364-5-52; reglamento local `[VERIFICAR]` | `[DEFINIR]` | |
| ENG-CAN-006 | Los materiales se seleccionan por resistencia a la corrosión del ambiente. | IEC 60721 (serie) | CON-nnn | |
| ENG-CAN-007 | Se prevé accesibilidad para mantenimiento y reserva de espacio. | Buenas prácticas | Reserva: `[DEFINIR]` | |

## 12. Bandejas portacables (BAN)

| ID | Criterio | Referencia | Parámetro / nota | Aplica |
|---|---|---|---|---|
| ENG-BAN-001 | Las bandejas y escalerillas cumplen la norma de producto en carga y flecha admisibles. | IEC 61537 | Carga de trabajo: `[DEFINIR]` | |
| ENG-BAN-002 | La carga de cables (peso, incluyendo reserva) se verifica contra la carga admisible y la separación de soportes. | IEC 61537; datos del fabricante | | |
| ENG-BAN-003 | Se garantiza la continuidad eléctrica y la conexión a tierra del sistema de bandejas. | IEC 61537; IEC 60364-5-54 | | |
| ENG-BAN-004 | Se definen niveles y segregación (potencia MT, potencia BT, control, instrumentación, comunicaciones). | IEC 61000-5-2 | Niveles: `[DEFINIR]` | |
| ENG-BAN-005 | El material y acabado (galvanizado, acero inoxidable, aluminio, PRFV) se selecciona por ambiente. | IEC 61537; IEC 60721 | | |
| ENG-BAN-006 | Los cables de potencia monopolares se disponen para limitar corrientes inducidas y esfuerzos electrodinámicos. | IEC 60287; IEC 61914 (fijación) | | |
| ENG-BAN-007 | Los pasos de muros cortafuego se sellan con sistema certificado. | Norma de ensayo de sellos `[DEFINIR]` | | |

## 13. Tableros (TAB)

| ID | Criterio | Referencia | Parámetro / nota | Aplica |
|---|---|---|---|---|
| ENG-TAB-001 | Los conjuntos de BT cumplen la norma de conjuntos de aparamenta, con verificación de diseño y ensayos individuales. | IEC 61439-1; IEC 61439-2 | | |
| ENG-TAB-002 | Se define y verifica la corriente asignada, la resistencia a cortocircuito (Icw / Icc) y la elevación de temperatura. | IEC 61439-1 | PAR-006 | |
| ENG-TAB-003 | Se especifica la forma de separación interna y la accesibilidad para operación y mantenimiento. | IEC 61439-2 | Forma: `[DEFINIR]` | |
| ENG-TAB-004 | El grado de protección IP e IK se define según el ambiente de instalación. | IEC 60529; IEC 62262 | PAR-013 | |
| ENG-TAB-005 | Se prevé espacio de reserva y barras de distribución con capacidad de ampliación. | Buenas prácticas | Reserva: `[DEFINIR]` | |
| ENG-TAB-006 | La identificación de equipos, circuitos y advertencias es completa y coincide con unifilares y planos. | IEC 61439-1; `DOCUMENT_RULES.md` | | |
| ENG-TAB-007 | Se exigen los ensayos de rutina en fábrica y los registros asociados (FAT) antes de despacho. | IEC 61439-1; IEC 62271-200 (MT) | | |
| ENG-TAB-008 | Los tableros de procesos o máquinas cumplen la norma de equipamiento eléctrico de máquinas cuando aplique. | IEC 60204-1 | | |

## 14. Protecciones (PRO)

| ID | Criterio | Referencia | Parámetro / nota | Aplica |
|---|---|---|---|---|
| ENG-PRO-001 | Se elabora un estudio de coordinación de protecciones con curvas, ajustes y selectividad entre niveles. | IEC 60947-2; IEC 60255 (serie) | | |
| ENG-PRO-002 | Los relés de protección se seleccionan por funciones requeridas (sobrecorriente, falla a tierra, diferencial, tensión, frecuencia, etc.) con justificación. | IEC 60255 (serie) | Funciones: `[DEFINIR]` | |
| ENG-PRO-003 | Los ajustes se documentan en una planilla de ajustes con fuente de cálculo. | IEC 60255 | | |
| ENG-PRO-004 | La protección de falla a tierra se define en función del régimen de neutro. | IEC 60364-4-41; IEC 61936-1 | PAR-007, PAR-008 | |
| ENG-PRO-005 | Se evalúa energía incidente de arco (arc flash) y se define señalización y medidas de mitigación cuando corresponda. | IEEE 1584 (complementaria); IEC 61482 (EPP) | Alcance: `[DEFINIR]` | |
| ENG-PRO-006 | Los enclavamientos eléctricos y mecánicos se definen y documentan en una matriz de enclavamientos. | IEC 62271-200; buenas prácticas | | |
| ENG-PRO-007 | La alimentación auxiliar de protección y control (baterías, rectificadores) se dimensiona para la autonomía requerida. | IEC 60896 (serie); IEC 62040 (UPS) | Autonomía: `[DEFINIR]` | |

## 15. Transformadores (TRA)

| ID | Criterio | Referencia | Parámetro / nota | Aplica |
|---|---|---|---|---|
| ENG-TRA-001 | Los transformadores de potencia cumplen la norma de producto y sus ensayos. | IEC 60076 (serie) | | |
| ENG-TRA-002 | Los transformadores tipo seco cumplen su norma específica y la clase ambiental, climática y de comportamiento al fuego. | IEC 60076-11 | Clases: `[DEFINIR]` | |
| ENG-TRA-003 | La potencia se dimensiona con balance de cargas, factor de carga y reserva; se verifica la capacidad de sobrecarga. | IEC 60076-7 (guía de carga); IEC 60076-12 | Reserva: `[DEFINIR]` | |
| ENG-TRA-004 | Se define grupo de conexión, impedancia, regulación (cambiador de tomas) y régimen de neutro. | IEC 60076-1; IEC 60076-8 | `[DEFINIR]` | |
| ENG-TRA-005 | Se verifica la capacidad de soportar cortocircuitos. | IEC 60076-5 | PAR-006 | |
| ENG-TRA-006 | Para transformadores con aceite se define contención, distancia a edificios y protección contra incendio. | IEC 61936-1 | | |
| ENG-TRA-007 | Se define ventilación o refrigeración del recinto según pérdidas y temperatura ambiente. | IEC 60076-2 | PAR-009 | |
| ENG-TRA-008 | Las protecciones propias (térmica, Buchholz, presión, nivel) se integran con el esquema de protección y disparo. | IEC 60076-1; IEC 60255 | | |

## 16. Puesta a tierra (PAT)

| ID | Criterio | Referencia | Parámetro / nota | Aplica |
|---|---|---|---|---|
| ENG-PAT-001 | El sistema de puesta a tierra se diseña para limitar tensiones de paso y contacto a valores admisibles. | IEC 61936-1; IEC 60479 (serie); IEEE 80 (complementaria) | Tiempos de despeje: `[DEFINIR]` | |
| ENG-PAT-002 | El diseño parte de la medición de resistividad del terreno por método reconocido. | IEC 61936-1; IEEE 81 (complementaria) | PAR-011 | |
| ENG-PAT-003 | Los conductores de tierra y electrodos se dimensionan por corriente de falla y durabilidad frente a corrosión. | IEC 60364-5-54; IEC 62561 (serie) | PAR-006 | |
| ENG-PAT-004 | Se realiza unión equipotencial principal y suplementaria, incluyendo estructuras metálicas, bandejas y cañerías. | IEC 60364-5-54; IEC 60364-4-41 | | |
| ENG-PAT-005 | La protección contra descargas atmosféricas se evalúa por análisis de riesgo. | IEC 62305 (serie) | | |
| ENG-PAT-006 | Las tierras de servicio, protección, instrumentación y pararrayos se interconectan o separan según criterio justificado. | IEC 61000-5-2; IEC 62305-3 | `[DEFINIR]` | |
| ENG-PAT-007 | Se prevén puntos de medición y se define el valor objetivo de resistencia del sistema. | Reglamento local `[VERIFICAR]` | Valor: `[DEFINIR]` | |

## 17. Instrumentación (INS)

| ID | Criterio | Referencia | Parámetro / nota | Aplica |
|---|---|---|---|---|
| ENG-INS-001 | Las señales analógicas y digitales se identifican y documentan en lista de instrumentos y de señales (I/O). | Norma corporativa; ISA 5.1 (complementaria) | | |
| ENG-INS-002 | Los cables de instrumentación se seleccionan con apantallamiento y se segregan de potencia. | IEC 61000-5-2 | | |
| ENG-INS-003 | Los equipos en áreas clasificadas se seleccionan con el modo de protección acorde a la clasificación de área. | IEC 60079 (serie) | PAR-012 | |
| ENG-INS-004 | Se aplica seguridad intrínseca cuando se defina, con documentación de lazo de seguridad intrínseca. | IEC 60079-11; IEC 60079-14 | | |
| ENG-INS-005 | Los lazos de control se documentan con diagramas de lazo y conexionado. | Norma corporativa | | |
| ENG-INS-006 | Los sistemas instrumentados de seguridad se diseñan según el ciclo de vida de seguridad funcional. | IEC 61508; IEC 61511 | SIL: `[DEFINIR]` | |
| ENG-INS-007 | La alimentación de instrumentos se define con protección y selectividad propias. | Buenas prácticas | | |

## 18. Automatización (AUT)

| ID | Criterio | Referencia | Parámetro / nota | Aplica |
|---|---|---|---|---|
| ENG-AUT-001 | Se define arquitectura de control (PLC, DCS, SCADA, redes) con diagrama de arquitectura. | Norma corporativa | | |
| ENG-AUT-002 | La programación de controladores programables sigue lenguajes y estructura normalizados. | IEC 61131-3 | Plataforma: `[DEFINIR]` | |
| ENG-AUT-003 | La integración de protecciones y subestaciones usa protocolos de comunicación normalizados definidos en el proyecto. | IEC 61850; IEC 60870-5-104 `[VERIFICAR]` | Protocolo: `[DEFINIR]` | |
| ENG-AUT-004 | Se elaboran matrices causa–efecto y lista de señales por equipo. | Buenas prácticas | | |
| ENG-AUT-005 | Se definen requisitos de ciberseguridad industrial de la arquitectura. | IEC 62443 (serie) | Nivel: `[DEFINIR]` | |
| ENG-AUT-006 | Se define sincronización horaria y registro de eventos. | IEC 61850 `[VERIFICAR]` | | |
| ENG-AUT-007 | Se prevén pruebas de aceptación en fábrica (FAT) y en sitio (SAT) para sistemas de control. | Buenas prácticas | | |

## 19. Seguridad eléctrica (SEG)

| ID | Criterio | Referencia | Parámetro / nota | Aplica |
|---|---|---|---|---|
| ENG-SEG-001 | Se garantiza protección contra contactos directos e indirectos. | IEC 61140; IEC 60364-4-41 | | |
| ENG-SEG-002 | Se evalúan los efectos de la corriente en el cuerpo humano para fijar límites de tensión de contacto. | IEC 60479 (serie) | | |
| ENG-SEG-003 | Se define el sistema de bloqueo y etiquetado (LOTO) y la secuencia de puesta en condición segura. | Norma corporativa del cliente; IEC 61936-1 | | |
| ENG-SEG-004 | Se define señalización de advertencia y rótulos de seguridad en equipos y recintos. | ISO 7010 `[VERIFICAR]` | | |
| ENG-SEG-005 | Los trabajos en o cerca de instalaciones eléctricas siguen requisitos de operación segura. | IEC 61936-1; EN 50110-1 (complementaria) | | |
| ENG-SEG-006 | Se prevé iluminación de emergencia y vías de evacuación en recintos eléctricos. | IEC 60364-5-56 | | |
| ENG-SEG-007 | Se provee equipamiento de protección personal para riesgo de arco y tensión. | IEC 61482 (serie) | | |
| ENG-SEG-008 | Se evalúan los riesgos de explosión, incendio y calor en recintos con baterías o equipos especiales. | IEC 60079 (serie); IEC 62485 (baterías) `[VERIFICAR]` | | |

## 20. Pre-COMMISSIONING (PRE)

| ID | Criterio | Referencia | Parámetro / nota | Aplica |
|---|---|---|---|---|
| ENG-PRE-001 | Se verifica la completitud mecánica y la conformidad de la instalación con planos ifc antes de comenzar. | Procedimiento del proyecto | | |
| ENG-PRE-002 | Se realiza inspección visual y verificación de montaje (torques, identificación, distancias, accesibilidad). | IEC 60364-6 | | |
| ENG-PRE-003 | Se mide la continuidad de conductores de protección y de uniones equipotenciales. | IEC 60364-6; IEC 61557 (serie) | | |
| ENG-PRE-004 | Se mide la resistencia de aislación de cables y equipos con tensión de ensayo acorde a su clase. | IEC 60364-6; IEC 60502-2 | Tensiones de ensayo: `[DEFINIR]` | |
| ENG-PRE-005 | Los cables de MT se ensayan después de su instalación según método y tensión definidos. | IEC 60502-2; IEEE 400 (complementaria) | Método: `[DEFINIR]` | |
| ENG-PRE-006 | Se verifica relación, polaridad y curva de saturación de transformadores de medida cuando corresponda. | IEC 61869 | | |
| ENG-PRE-007 | Se ensayan transformadores de potencia (relación, aislación, resistencia de bobinados, otros definidos). | IEC 60076-1 | | |
| ENG-PRE-008 | Se verifican, cargan y prueban ajustes y lógicas de protecciones por inyección secundaria. | IEC 60255 | Planilla de ajustes aprobada | |
| ENG-PRE-009 | Se verifica la secuencia de fases, rotación de motores y funcionamiento de enclavamientos sin energía. | IEC 60364-6; IEC 62271-200 | | |
| ENG-PRE-010 | Se mide la resistencia del sistema de puesta a tierra. | IEC 61936-1; reglamento local `[VERIFICAR]` | Valor objetivo: ENG-PAT-007 | |
| ENG-PRE-011 | Todos los resultados se registran en protocolos con instrumentos identificados y calibración vigente. | Sistema de calidad | | |
| ENG-PRE-012 | Las no conformidades se registran en una lista de pendientes (punch list) categorizada. | Procedimiento del proyecto | | |

## 21. COMMISSIONING (COM)

| ID | Criterio | Referencia | Parámetro / nota | Aplica |
|---|---|---|---|---|
| ENG-COM-001 | La energización se ejecuta según procedimiento aprobado, con permisos de trabajo y secuencia definida. | Procedimiento del proyecto; IEC 61936-1 | | |
| ENG-COM-002 | Antes de energizar se verifica el cierre de la lista de pendientes categoría A y los protocolos de pre-commissioning aprobados. | `project-audit.md` | | |
| ENG-COM-003 | Se realizan pruebas funcionales de enclavamientos, mandos, señalizaciones, alarmas y disparos. | IEC 62271-200; buenas prácticas | | |
| ENG-COM-004 | Se verifican en servicio tensiones, secuencia de fases, corrientes y sentidos de giro. | IEC 60364-6 | | |
| ENG-COM-005 | Se efectúan pruebas con carga y verificación de ajustes de protección en servicio. | Procedimiento del proyecto | | |
| ENG-COM-006 | Se realiza termografía de conexiones bajo carga cuando se defina. | Procedimiento del proyecto | | |
| ENG-COM-007 | Los sistemas de control se prueban integralmente (SAT) frente a la matriz causa–efecto. | ENG-AUT-004; ENG-AUT-007 | | |
| ENG-COM-008 | Se elabora el acta de puesta en servicio y los registros firmados por las partes. | Contrato | | |
| ENG-COM-009 | Se transfiere conocimiento a operación y mantenimiento según plan de capacitación. | `DOCUMENT_RULES.md` | | |
| ENG-COM-010 | Las modificaciones realizadas en obra se registran para su incorporación a la documentación as-built. | `deliverables.md` | | |

## 22. Civil (CIV)

| ID | Criterio | Referencia | Parámetro / nota | Aplica |
|---|---|---|---|---|
| ENG-CIV-001 | El diseño se basa en estudio geotécnico y relevamiento topográfico vigentes del sitio; sin estudio, la capacidad portante se declara como supuesto. | Estudio geotécnico del sitio | `PAR-C-nnn` | |
| ENG-CIV-002 | Movimiento de suelos, nivelación y drenaje pluvial se dimensionan con un criterio hidrológico definido. | Reglamentación local `[VERIFICAR]` | Período de retorno: `[DEFINIR]` | |
| ENG-CIV-003 | Las fundaciones de equipos se diseñan con las cargas estáticas y dinámicas informadas por el proveedor, verificando asentamientos admisibles. | ACI 318; datos del fabricante | | |
| ENG-CIV-004 | Clase de resistencia del hormigón, recubrimiento y durabilidad se definen según el ambiente de exposición. | ACI 318; CIRSOC 201 `[VERIFICAR]` | `[DEFINIR]` | |
| ENG-CIV-005 | Vialidad interna y accesos contemplan equipos de montaje, mantenimiento y vehículos de emergencia. | Criterio del proyecto | | |
| ENG-CIV-006 | Zanjas, cámaras, bases y canalizaciones civiles se coordinan con las disciplinas de servicios mediante planos de interfaz. | `ENG-INT-nnn` | | |
| ENG-CIV-007 | Se define un plan de control de calidad de materiales y ensayos de hormigón y suelos. | Normas de ensayo ASTM aplicables `[VERIFICAR]` | | |
| ENG-CIV-008 | Excavaciones e interferencias con servicios enterrados existentes se identifican y gestionan antes de intervenir. | Reglamentación local | | |

## 23. Estructuras (EST)

| ID | Criterio | Referencia | Parámetro / nota | Aplica |
|---|---|---|---|---|
| ENG-EST-001 | Las acciones (permanentes, sobrecargas, viento, sismo, nieve, térmicas y de equipos) y sus combinaciones se definen y documentan. | ASCE 7; EN 1990 / EN 1991; CIRSOC 101 / 102 / 103 `[VERIFICAR]` | `PAR-S-nnn` | |
| ENG-EST-002 | Las estructuras de acero se diseñan con una norma única definida para el proyecto. | AISC 360; EN 1993; CIRSOC 301 `[VERIFICAR]` | Norma: `[DEFINIR]` | |
| ENG-EST-003 | Las estructuras de hormigón armado se diseñan con una norma única definida para el proyecto. | ACI 318; EN 1992; CIRSOC 201 `[VERIFICAR]` | Norma: `[DEFINIR]` | |
| ENG-EST-004 | Soportes de cañerías, bandejas, conductos y equipos se verifican con las cargas de servicio, expansión térmica y vibración informadas por la disciplina de origen. | Datos de las disciplinas | | |
| ENG-EST-005 | Uniones, soldaduras y protección anticorrosiva se definen según el ambiente. | AWS D1.1 / EN 1090; ISO 12944 | `[DEFINIR]` | |
| ENG-EST-006 | Se verifican deformaciones, vibraciones y estados límite de servicio. | Norma de diseño adoptada | | |
| ENG-EST-007 | La memoria de cálculo declara modelo, hipótesis, software, versión y resultados verificables. | `DOCUMENT_RULES.md`, 6.7 | | |
| ENG-EST-008 | Cuando se exija, se verifica la resistencia al fuego de elementos estructurales. | EN 1993-1-2 / reglamentación local `[VERIFICAR]` | Exigencia: `[DEFINIR]` | |

## 24. Mecánica y equipos (MEC)

| ID | Criterio | Referencia | Parámetro / nota | Aplica |
|---|---|---|---|---|
| ENG-MEC-001 | Los equipos rotativos (bombas, ventiladores, compresores) se especifican con hoja de datos: punto de operación, curvas, materiales y servicio. | API 610 / ISO 13709 (bombas); ISO 5199 | `PAR-M-nnn` | |
| ENG-MEC-002 | La selección verifica el punto de operación en todo el rango de trabajo, con margen justificado y eficiencia declarada. | Datos del fabricante | Margen: `[DEFINIR]` | |
| ENG-MEC-003 | Recipientes a presión, intercambiadores y tanques se diseñan según un código único definido. | ASME BPVC Sección VIII; API 650; TEMA; EN 13445 | Código: `[DEFINIR]` | |
| ENG-MEC-004 | Los límites de vibración de equipos rotativos se definen y se verifican en pruebas. | ISO 20816 (serie) | | |
| ENG-MEC-005 | Partes móviles y acoplamientos cuentan con protecciones de seguridad. | ISO 14120; ISO 12100 | | |
| ENG-MEC-006 | Se prevén puntos de izaje, accesos y espacio de desmontaje para mantenimiento. | Criterio del proyecto | | |
| ENG-MEC-007 | Las cargas eléctricas de los equipos se informan a la disciplina eléctrica por documento controlado. | `ENG-INT-004`, `ENG-GEN-002` | | |
| ENG-MEC-008 | Pintura y protección superficial se definen según el ambiente. | ISO 12944 | | |

## 25. Termomecánica (TER)

| ID | Criterio | Referencia | Parámetro / nota | Aplica |
|---|---|---|---|---|
| ENG-TER-001 | Se elabora un balance de masa y energía documentado para operación normal, máxima y mínima. | Buenas prácticas | `PAR-M-nnn` | |
| ENG-TER-002 | Generadores de vapor y calderas se diseñan según un código único definido. | ASME BPVC Sección I; EN 12952 / EN 12953 | Código: `[DEFINIR]` | |
| ENG-TER-003 | Cañerías de vapor, condensado y agua de alimentación cumplen el código de cañerías de potencia. | ASME B31.1 | | |
| ENG-TER-004 | Los sistemas de combustión y de gas combustible cumplen los requisitos de seguridad de combustión aplicables. | NFPA 85 / NFPA 86 / NFPA 54 `[VERIFICAR]` | | |
| ENG-TER-005 | La aislación térmica se define por pérdida admisible y protección de personas (temperatura de superficie). | ISO 12241 | Temperatura de superficie: `[DEFINIR]` | |
| ENG-TER-006 | Se verifican la expansión térmica y la flexibilidad de cañerías calientes mediante análisis de tensiones. | ASME B31.1 / B31.3 | | |
| ENG-TER-007 | Las válvulas de seguridad y dispositivos de alivio se dimensionan con el escenario de descarga definido. | API 520 / API 521; ASME BPVC Sección VIII | | |
| ENG-TER-008 | Se define la calidad del agua de alimentación y el tratamiento y purgas asociados. | Guía del fabricante `[VERIFICAR]` | `[DEFINIR]` | |
| ENG-TER-009 | Se documenta la eficiencia objetivo y su método de verificación en pruebas. | Contrato / guía del fabricante | `[DEFINIR]` | |

## 26. Cañerías (PIP)

| ID | Criterio | Referencia | Parámetro / nota | Aplica |
|---|---|---|---|---|
| ENG-PIP-001 | Se elabora una especificación de cañerías (clases) por servicio: material, rating, sobreespesor por corrosión y conexiones. | ASME B31.3 / B31.1; ASME B16.5; ASME B16.34 | `PAR-P-nnn` | |
| ENG-PIP-002 | Los diagramas P&ID identifican tags, servicios, líneas, válvulas, instrumentos y lazos de control. | ISA 5.1; ISO 10628 | | |
| ENG-PIP-003 | Se dimensiona hidráulicamente: velocidad, pérdida de carga y golpe de ariete cuando corresponda. | Buenas prácticas | Velocidades límite: `[DEFINIR]` | |
| ENG-PIP-004 | Se analiza flexibilidad y se diseñan soportes donde el servicio lo requiera. | ASME B31.3 / B31.1 | | |
| ENG-PIP-005 | Se definen pruebas hidrostática o neumática y limpieza según el código aplicable. | ASME B31.3 / B31.1 | | |
| ENG-PIP-006 | Se elaboran lista de líneas, lista de válvulas, especialidades e isométricos. | `deliverables.md` | | |
| ENG-PIP-007 | Soldaduras y ensayos no destructivos se rigen por procedimientos y personal calificados. | ASME BPVC Sección IX | | |
| ENG-PIP-008 | Aislación, traceado y protección contra corrosión se definen por servicio y ambiente. | ISO 12241; ISO 12944 | | |

## 27. HVAC (HVA)

| ID | Criterio | Referencia | Parámetro / nota | Aplica |
|---|---|---|---|---|
| ENG-HVA-001 | Las condiciones de diseño exteriores e interiores (temperatura, humedad, ocupación) se definen y respaldan con datos climáticos del sitio. | ASHRAE Handbook – Fundamentals | `PAR-H-nnn` | |
| ENG-HVA-002 | Se calcula la carga térmica (sensible y latente) considerando envolvente, ocupación, iluminación y equipos. | ASHRAE Handbook – Fundamentals | | |
| ENG-HVA-003 | Los caudales mínimos de ventilación se definen por ocupación y área. | ASHRAE 62.1; EN 16798-1 | | |
| ENG-HVA-004 | Se verifica el confort térmico en áreas ocupadas. | ASHRAE 55; ISO 7730 | | |
| ENG-HVA-005 | Redes de conductos: dimensionamiento (velocidad, pérdida de carga), construcción y sellado. | SMACNA; ASHRAE | Velocidades límite: `[DEFINIR]` | |
| ENG-HVA-006 | Se definen presurización y cascadas de presión en salas eléctricas, salas limpias y áreas clasificadas. | ISO 14644 (serie) cuando aplique | | |
| ENG-HVA-007 | Equipos de climatización y enfriadoras se seleccionan por capacidad, eficiencia y refrigerante, con seguridad del refrigerante. | ASHRAE 15; EN 378 | Refrigerante: `[DEFINIR]` | |
| ENG-HVA-008 | Se definen dampers cortafuego, control de humo y detención de ventiladores ante incendio. | NFPA 90A; NFPA 92; EN 12101 | Interfaz con `ENG-FDE-006` | |
| ENG-HVA-009 | Se definen límites de ruido y vibración en áreas ocupadas. | Criterio del proyecto | `[DEFINIR]` | |
| ENG-HVA-010 | La ventilación de salas de baterías, transformadores y locales técnicos se dimensiona por calor disipado y gases. | Datos de la disciplina eléctrica | Interfaz con `ENG-INT-004` | |
| ENG-HVA-011 | Se define el procedimiento de balanceo y puesta en marcha del sistema. | ASHRAE Guideline 1.1; procedimiento TAB reconocido | | |

## 28. Protección contra incendio — combate de incendios (FFI)

| ID | Criterio | Referencia | Parámetro / nota | Aplica |
|---|---|---|---|---|
| ENG-FFI-001 | Se realiza un análisis de riesgo de incendio por área (ocupación, carga de fuego, sustancias) que determina el sistema y el criterio de diseño. | NFPA 13 (clasificación de riesgo); reglamentación local; exigencias de aseguradora `[VERIFICAR]` | `PAR-F-nnn` | |
| ENG-FFI-002 | Rociadores automáticos: densidad y área de diseño, tipo de rociador y cobertura según el riesgo. | NFPA 13; EN 12845 | Criterio: `[DEFINIR]` | |
| ENG-FFI-003 | Hidrantes, mangueras y montantes: caudal, presión residual y cobertura. | NFPA 14; NFPA 24 | | |
| ENG-FFI-004 | Fuente de agua y reserva: capacidad y autonomía de diseño. | NFPA 22; NFPA 13 | Autonomía: `[DEFINIR]` | |
| ENG-FFI-005 | Bombas contra incendio: tipo, curva, redundancia y alimentación confiable (eléctrica o diésel). | NFPA 20 | Interfaz eléctrica `ENG-INT-004` | |
| ENG-FFI-006 | Espuma, agua pulverizada y agentes gaseosos (CO₂, agente limpio) se aplican según el riesgo definido. | NFPA 11; NFPA 15; NFPA 12; NFPA 2001 | | |
| ENG-FFI-007 | Extintores portátiles: tipo, cantidad y ubicación. | NFPA 10; reglamentación local | | |
| ENG-FFI-008 | El cálculo hidráulico se documenta con curvas de demanda y de suministro, método de fricción y margen de seguridad. | NFPA 13; NFPA 20 | Margen: `[DEFINIR]` | |
| ENG-FFI-009 | Sectorización, compartimentación y sellado de penetraciones se coordinan con arquitectura. | `ENG-ARQ-002` | | |
| ENG-FFI-010 | Pruebas de aceptación: hidrostática, flujo, bombas y alarmas de flujo. | NFPA 13; NFPA 20; NFPA 25 | | |
| ENG-FFI-011 | Se define el plan de inspección, ensayo y mantenimiento del sistema. | NFPA 25 | | |
| ENG-FFI-012 | Se registran las aprobaciones de la autoridad competente o aseguradora. | Reglamentación local | Autoridad: `[DEFINIR]` | |

## 29. Detección y alarma de incendio (FDE)

| ID | Criterio | Referencia | Parámetro / nota | Aplica |
|---|---|---|---|---|
| ENG-FDE-001 | Se define la filosofía de detección por área y el tipo de detector (humo puntual, aspiración, lineal, llama, calor, gas). | NFPA 72; EN 54; ISO 7240 | `PAR-F-nnn` | |
| ENG-FDE-002 | Se define zonificación, direccionamiento y diseño de lazos. | NFPA 72; EN 54-14 | | |
| ENG-FDE-003 | Cobertura y espaciamiento de detectores se verifican por altura, ventilación y obstrucciones. | NFPA 72; EN 54-14 | | |
| ENG-FDE-004 | La central se dimensiona por capacidad, con alimentación principal y de respaldo (baterías) con autonomía definida y supervisión de circuitos. | NFPA 72; EN 54-2; EN 54-4 | Autonomía: `[DEFINIR]` | |
| ENG-FDE-005 | Se define la notificación (sirenas, luces, voz) y el nivel sonoro para evacuación. | NFPA 72; EN 54-3; EN 54-23 | | |
| ENG-FDE-006 | Se define la integración con HVAC, ascensores, puertas, sistemas de extinción, control de acceso y SCADA mediante una matriz causa–efecto. | NFPA 72; `ENG-HVA-008`; `ENG-FFI-006` | | |
| ENG-FDE-007 | El cableado se especifica con resistencia al fuego y supervisión; la alimentación y las canalizaciones eléctricas se coordinan con la disciplina eléctrica. | IEC 60331; NFPA 72 | Capa CAD `E-FIRE-ALARM` | |
| ENG-FDE-008 | Se prueban y verifican todos los dispositivos en la aceptación, con registros. | NFPA 72; EN 54-14 | | |
| ENG-FDE-009 | Se define el plan de pruebas periódicas y mantenimiento. | NFPA 72 | | |

## 30. Telecomunicaciones (TEL)

| ID | Criterio | Referencia | Parámetro / nota | Aplica |
|---|---|---|---|---|
| ENG-TEL-001 | El cableado estructurado define categoría, topología y longitudes máximas. | ISO/IEC 11801; ANSI/TIA-568; EN 50173 | `PAR-T-nnn` | |
| ENG-TEL-002 | Salas de telecomunicaciones y recorridos (pathways) se dimensionan y coordinan con las demás disciplinas. | ANSI/TIA-569 | | |
| ENG-TEL-003 | Cables, enlaces y gabinetes se identifican y administran con un esquema único. | ANSI/TIA-606 | | |
| ENG-TEL-004 | La fibra óptica en áreas industriales y subestaciones define tipo, protección, empalmes y mediciones. | Datos del fabricante | | |
| ENG-TEL-005 | Se define puesta a tierra y equipotencialidad de equipos de telecomunicaciones. | ANSI/TIA-607; IEC 61000-5-2 | | |
| ENG-TEL-006 | CCTV, control de acceso, megafonía y radiocomunicaciones se definen por filosofía, cobertura y alimentación. | Criterio del proyecto | | |
| ENG-TEL-007 | La ciberseguridad de redes se coordina con automatización y control. | IEC 62443 | | |
| ENG-TEL-008 | Se certifican los enlaces y se entrega el reporte de pruebas. | ANSI/TIA-568 | | |

## 31. Arquitectura (ARQ)

| ID | Criterio | Referencia | Parámetro / nota | Aplica |
|---|---|---|---|---|
| ENG-ARQ-001 | El programa de áreas y los requisitos funcionales se definen con el cliente. | Requisitos del cliente | | |
| ENG-ARQ-002 | La resistencia al fuego, compartimentación de elementos constructivos y rutas de evacuación cumplen la norma aplicable. | NFPA 101; reglamentación local `[VERIFICAR]` | | |
| ENG-ARQ-003 | Se garantiza accesibilidad para operación y mantenimiento (puertas, pasos para equipos, izaje). | Criterio del proyecto | | |
| ENG-ARQ-004 | Materiales y terminaciones se definen según el ambiente (corrosión, higiene, limpieza). | Criterio del proyecto | | |
| ENG-ARQ-005 | Se coordinan pasos, ductos verticales y cielorrasos con las disciplinas de servicios. | `ENG-INT-003` | | |

## 32. Interfaces entre disciplinas (INT)

| ID | Criterio | Referencia | Parámetro / nota | Aplica |
|---|---|---|---|---|
| ENG-INT-001 | Se mantiene una matriz de interfaces con responsable, dato intercambiado, fecha y estado. | Buenas prácticas | | |
| ENG-INT-002 | Todas las disciplinas usan coordenadas y cotas de referencia únicas. | `CAD_standards.md` | | |
| ENG-INT-003 | Se realiza detección de interferencias entre cañerías, conductos, bandejas y estructuras antes de la entrega ifc. | Buenas prácticas | | |
| ENG-INT-004 | Los datos de una disciplina que impactan a otra (cargas eléctricas de equipos, cargas estructurales, calor disipado, caudales) se transmiten por documento controlado con revisión. | `DOCUMENT_RULES.md` | | |
| ENG-INT-005 | Los límites de suministro entre disciplinas y terceros se definen en el alcance. | `project-scope.md`, sección A | | |
| ENG-INT-006 | Un cambio en una disciplina dispara análisis de impacto en las demás y registro en decisiones. | `assumptions-and-decisions.md` | | |

## 33. Criterios específicos del proyecto o del cliente

| ID | Criterio | Origen (CLIENTE / PROYECTO / HISTÓRICO) | Referencia (REQ- / DEC-) | Reemplaza o complementa | Aplica |
|---|---|---|---|---|---|
| ENG-xxx-nnn | | | | | |

## 34. Normas complementarias

Las siguientes familias se utilizan **solo cuando el cliente, el contrato o el reglamento local de cumplimiento obligatorio lo exijan, o cuando se adopten por decisión registrada**, y su edición vigente debe verificarse:

| Familia | Uso típico |
|---|---|
| IEEE (p. ej. 80, 81, 400, 1584) | Puesta a tierra, ensayos de cables, arco eléctrico |
| NFPA (70, 70E, 780 y las series de protección contra incendio) | Proyectos con requisito norteamericano o exigencia de aseguradora |
| FM Global (hojas de datos) | Exigencia de aseguradora |
| ASME / API / TEMA | Recipientes, cañerías, bombas, tanques e intercambiadores cuando el cliente lo exija |
| Reglamentos locales (p. ej. en Argentina: AEA para instalaciones eléctricas, CIRSOC para estructuras, normativa de seguridad e higiene y de protección contra incendio; verificar vigencia) | Cumplimiento obligatorio local |
| CENELEC EN 50xxx | Proyectos con requisito europeo |
| Normas corporativas del cliente | Requisitos específicos (registrar en `client-requirements.md`) |

## 35. Iluminación normal y de emergencia (ILU)

| ID | Criterio | Referencia | Parámetro / nota | Aplica |
|---|---|---|---|---|
| ENG-ILU-001 | La iluminancia mantenida, la uniformidad y el UGR de cada área se verifican por cálculo (método de flujo para dimensionar y punto a punto con fotometría del fabricante para verificar), con factor de mantenimiento justificado y área de cálculo definida. | EN 12464-1 `[VERIFICAR]` | Niveles por área: `[DEFINIR]` | |
| ENG-ILU-002 | La iluminación de escape y antipánico cumple los niveles mínimos en el eje de rutas y en áreas abiertas, y la uniformidad máxima, según la norma de emergencia. | EN 1838 `[VERIFICAR]` | Valores a confirmar en la edición vigente | |
| ENG-ILU-003 | La autonomía de las luminarias de emergencia es la exigida (mínimo normativo o el del cliente si es mayor) y las salidas tienen señalización permanente o mantenida. | EN 1838; IEC 60598-2-22 `[VERIFICAR]` | Autonomía: `[DEFINIR]` | |
| ENG-ILU-004 | El circuito de carga de luminarias autónomas no se interrumpe por el comando de zona; los circuitos se agrupan por zona de intervención y se equilibran entre fases. | IEC 60364 (serie) | | |
| ENG-ILU-005 | La altura de montaje y el acceso para mantenimiento se verifican frente a obstáculos (puentes grúa, ductos, estructura). | Buenas prácticas | Altura: `[DEFINIR]` | |
| ENG-ILU-006 | El control (sensores, comando por zonas, regulación) cumple el alcance acordado y se documenta en diagrama de comando. | Requisito del cliente | | |
| ENG-ILU-007 | Se exigen al fabricante archivos fotométricos (IES / LDT) y certificados de ensayo de luminarias; los valores de cálculo provienen de ellos. | IEC 60598 (serie) | | |
