# standards-index.md — Biblioteca de Normas y Reglamentos

| Campo | Valor |
|---|---|
| Versión | 1.0 |
| Fecha | 2026-10-07 |
| Responsable | Líder Técnico |

---

# GUÍA DEL ARCHIVO (no editar)

## 1. Objetivo

Tener las normas y reglamentos de la oficina en una carpeta ordenada por disciplina, con un **índice que permite consultar solo las que corresponden al proyecto**, y que Claude verifique contra la norma real (no de memoria) los valores que cita.

## 2. Alcance

Todas las disciplinas. Los archivos de las normas (PDF u otro) se guardan en `98_LIBRARY/standards/<disciplina>/` (`G_General`, `E_Electrical`, `F_Fire`, `h-hvac`, `M_Mechanical`, `P_Piping`, `C_Civil`, `S_Structures`, `I_Instrumentation`, `T_Telecommunications`, `A_Architecture`). Las normas de un cliente o proyecto específico van en `01-input/07_CODES_AND_standards`; si se reutilizan, se incorporan aquí.

## 3. Forma de utilización

1. **Consulta por relevancia (regla principal).** Claude no lee la biblioteca completa. Para cada documento o cálculo:
   1. toma la **disciplina** del entregable y el **sistema o tema** que trata (por ejemplo `iluminación`, `cables BT`, `tableros`, `detección de incendio`, `rociadores`, `ventilación`);
   2. filtra el índice por esa disciplina **y** por esas etiquetas de la columna *Aplica a (etiquetas)*;
   3. abre solo los archivos filtrados y, dentro de ellos, solo las secciones necesarias;
   4. nunca consulta normas de otras disciplinas o sistemas para resolver un dato (por ejemplo, no se busca un parámetro de aire acondicionado en una norma de construcción naval).
2. **Verificación.** Un valor citado de una norma con archivo en la biblioteca se verifica contra el archivo (sección y edición) y deja de ser `[VERIFICAR]`. Si la norma está en el índice como `SIN ARCHIVO`, el valor permanece `[VERIFICAR]` y Claude pide el archivo al usuario con un `INF-nnn`.
3. **Norma no indexada.** Si el proyecto exige una norma que no figura, Claude agrega la fila con estado `SIN ARCHIVO`, la registra en `project-information.md` (sección G, `NOR-nnn`, anotando su `NRM-nnn` en la columna de correspondencia) y solicita el archivo. Cada norma del proyecto tiene así un `NOR-nnn` (ID del proyecto) y, si está indexada, el `NRM-nnn` (ID de la biblioteca) en la misma fila.
4. **Edición vigente.** La columna *Edición en archivo* es la del archivo guardado; la vigencia legal local la confirma el usuario. Si el archivo está desactualizado respecto de lo que exige el contrato, se registra como `[VERIFICAR]` hasta recibir el correcto.
5. **Extractos.** Claude puede crear fichas de extracto (`<ID>_extract.md`) con los valores clave y su sección, para evitar leer el archivo completo cada vez; la ficha cita edición y sección y es verificable.
6. Un valor normativo citado sin edición ni sección, cuando la norma está en la biblioteca, es un hallazgo de auditoría (A3).

## 4. Estructura recomendada

Cada fila: `NRM-nnn`, designación, título, disciplina, etiquetas de aplicación, edición en archivo, ruta del archivo, estado (`EN ARCHIVO`, `SIN ARCHIVO`, `OBSOLETA`), ficha de extracto, observaciones.

## 5. Ejemplos de uso (ilustrativos)

- Memoria de cálculo luminotécnico (E, etiqueta `iluminación`): se consultan `NRM-` de iluminación general y de emergencia; no se abren normas de cables.
- Especificación de tablero BT (E, `tableros`): se consulta la norma de conjuntos de aparamenta de BT.
- Sistema de rociadores (F, `rociadores`): se consulta la norma de rociadores; no se abren normas de detección salvo que el alcance las incluya.

## 6. Buenas prácticas

- Guardar el archivo con el nombre `<designación>_<edición>.pdf`.
- Mantener etiquetas cortas y consistentes.
- Retirar las normas obsoletas a una subcarpeta `OBSOLETAS` y marcarlas en el índice.
- Respetar los derechos de autor: no redistribuir fuera de la oficina.

---

# ÍNDICE DE standards (completar y mantener)

> Las filas siguientes se precargaron **solo con la designación, de memoria**: todas están `SIN ARCHIVO` y las ediciones deben verificarse. Se listan para que Claude sepa qué familias existen para cada tema; no son una afirmación de que apliquen a un proyecto.

| ID | Designación | Título (resumen) | Disciplina | Aplica a (etiquetas) | Edición en archivo | Ruta del archivo | Estado | Observaciones |
|---|---|---|---|---|---|---|---|---|
| NRM-001 | IEC 60364 (serie) | Instalaciones eléctricas de baja tensión | E | `instalaciones BT`, `conductores`, `protecciones`, `puesta a tierra`, `iluminación circuitos` | `[VERIFICAR]` | — | SIN ARCHIVO | |
| NRM-002 | IEC 60909 (serie) | Corrientes de cortocircuito | E | `cortocircuito` | `[VERIFICAR]` | — | SIN ARCHIVO | |
| NRM-003 | IEC 61439 (serie) | Conjuntos de aparamenta de BT | E | `tableros BT` | `[VERIFICAR]` | — | SIN ARCHIVO | |
| NRM-004 | IEC 60947 (serie) | Aparamenta de baja tensión | E | `interruptores`, `protecciones` | `[VERIFICAR]` | — | SIN ARCHIVO | |
| NRM-005 | IEC 62271 (serie) | Aparamenta de alta tensión | E | `celdas MT`, `aparamenta MT` | `[VERIFICAR]` | — | SIN ARCHIVO | |
| NRM-006 | IEC 60076 (serie) | Transformadores de potencia | E | `transformadores` | `[VERIFICAR]` | — | SIN ARCHIVO | |
| NRM-007 | IEC 60502 (serie) | Cables de energía aislados | E | `cables MT`, `cables BT` | `[VERIFICAR]` | — | SIN ARCHIVO | |
| NRM-008 | IEC 60228 | Conductores de cables aislados | E | `cables` | `[VERIFICAR]` | — | SIN ARCHIVO | |
| NRM-009 | IEC 62305 (serie) | Protección contra el rayo | E | `pararrayos`, `puesta a tierra` | `[VERIFICAR]` | — | SIN ARCHIVO | |
| NRM-010 | IEC 60529 | Grados de protección (código IP) | G | `IP`, `envolventes` | `[VERIFICAR]` | — | SIN ARCHIVO | |
| NRM-011 | EN 12464-1 | Iluminación de lugares de trabajo en interiores | E | `iluminación`, `niveles de iluminancia` | `[VERIFICAR]` | — | SIN ARCHIVO | |
| NRM-012 | EN 1838 | Iluminación de emergencia | E | `iluminación de emergencia`, `escape`, `antipánico` | `[VERIFICAR]` | — | SIN ARCHIVO | |
| NRM-013 | IEC 60598-2-22 | Luminarias para iluminación de emergencia | E | `luminarias de emergencia` | `[VERIFICAR]` | — | SIN ARCHIVO | |
| NRM-014 | NFPA 13 | Instalación de sistemas de rociadores | F | `rociadores`, `agua contra incendio` | `[VERIFICAR]` | — | SIN ARCHIVO | |
| NRM-015 | NFPA 14 | Sistemas de tubería vertical y mangueras | F | `hidrantes interiores`, `mangueras` | `[VERIFICAR]` | — | SIN ARCHIVO | |
| NRM-016 | NFPA 20 | Bombas estacionarias contra incendio | F | `bombas contra incendio` | `[VERIFICAR]` | — | SIN ARCHIVO | |
| NRM-017 | NFPA 72 | Código nacional de alarmas y señalización | F | `detección de incendio`, `alarma` | `[VERIFICAR]` | — | SIN ARCHIVO | |
| NRM-018 | EN 54 (serie) | Sistemas de detección y alarma de incendio | F | `detección de incendio`, `alarma` | `[VERIFICAR]` | — | SIN ARCHIVO | |
| NRM-019 | ASHRAE 62.1 | Ventilación para calidad de aire interior | H | `ventilación`, `aire exterior` | `[VERIFICAR]` | — | SIN ARCHIVO | |
| NRM-020 | ASHRAE 90.1 | Eficiencia energética de edificios | H | `eficiencia energética` | `[VERIFICAR]` | — | SIN ARCHIVO | |
| NRM-021 | ASME B31.3 | Tuberías de proceso | P | `cañerías de proceso` | `[VERIFICAR]` | — | SIN ARCHIVO | |
| NRM-022 | ISO 7010 | Señales de seguridad | G | `señalización` | `[VERIFICAR]` | — | SIN ARCHIVO | |
| NRM-023 | IEC 61508 / IEC 61511 | Seguridad funcional | I | `SIL`, `seguridad funcional` | `[VERIFICAR]` | — | SIN ARCHIVO | |
| NRM-024 | Reglamentación local de instalaciones eléctricas | Según país o jurisdicción | E | `instalaciones eléctricas` | `[VERIFICAR]` | — | SIN ARCHIVO | A definir por proyecto |
| NRM-025 | Reglamentación local de seguridad e higiene y de protección contra incendio | Según país o jurisdicción | G / F | `seguridad`, `evacuación`, `incendio` | `[VERIFICAR]` | — | SIN ARCHIVO | A definir por proyecto |

> **Extractos de tablas:** los valores tomados de una norma (por ejemplo, capacidades de conducción) se guardan con la ficha `98_LIBRARY/standards/template-extract.md` (ID NRM, edición, tabla, página, valores, fecha y quién verificó). Sin ficha verificada, el valor queda `[VERIFICAR]`.
