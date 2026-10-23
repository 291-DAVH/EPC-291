# equipment-catalog.md — Catálogo de Equipos y Materiales de la Oficina

| Campo | Valor |
|---|---|
| Versión | 1.0 |
| Fecha | 2026-10-07 |
| Responsable | Líder Técnico |

---

# GUÍA DEL ARCHIVO (no editar)

## 1. Objetivo

Reunir en un solo archivo los equipos y materiales que la oficina conoce, usa y recomienda, con sus **datos garantizados** y su experiencia de uso, para que las especificaciones, listas y cálculos partan de productos reales y no de supuestos.

## 2. Alcance

Todas las disciplinas: luminarias, tableros, interruptores, cables, transformadores, bombas, detectores, equipos HVAC, etc. Las hojas de datos y certificados se guardan en `98_LIBRARY/equipment/datasheets/` con el nombre `<ID>_<fabricante>_<modelo>.pdf`.

## 3. Forma de utilización

1. **Consulta previa.** Antes de especificar un equipo, Claude filtra este catálogo por disciplina y tipo y propone primero los equipos `APPROVED`. Las listas de marcas aprobadas del **cliente** (`client-requirements.md`) prevalecen: un equipo del catálogo que no esté en la lista del cliente no se propone para ese proyecto.
2. **Datos garantizados.** Los valores de un equipo se toman **solo de la hoja de datos** archivada. Un dato no presente en la hoja se deja `[DEFINIR]`; Claude no lo estima ni lo completa de memoria.
3. **Reemplazo de supuestos.** Cuando un cálculo usó un equipo de referencia (`SUP-nnn`), al seleccionar un equipo del catálogo se reemplaza el supuesto por los datos reales y se recalcula.
4. **Alta de equipos.** Un equipo se agrega por pedido del usuario o durante la extracción de lecciones (`lessons-learned.md`), con su hoja de datos y la primera experiencia de uso. Estado inicial: `CANDIDATE` hasta que el usuario lo apruebe.
5. **Experiencia de uso.** Después de cada proyecto se actualizan las columnas *Proyectos donde se usó* y *Experiencia / lecciones*. Un problema repetido pasa el estado a `NOT_RECOMMENDED` con motivo.
6. **Vigencia.** Cada fila lleva fecha de la hoja de datos; una hoja con más de 24 meses se revisa antes de usarla (`[VERIFICAR]`).
7. La auditoría verifica que los equipos citados en especificaciones y listas coincidan con el catálogo o con una decisión registrada (A3 y A4).

## 4. Estructura recomendada

| Estado | Significado |
|---|---|
| `CANDIDATE` | Cargado; sin aprobación del usuario |
| `APPROVED` | Aprobado para proponer |
| `CONDITIONAL` | Aprobado solo bajo condiciones indicadas |
| `NOT_RECOMMENDED` | No proponer; se indica el motivo |
| `OBSOLETE` | Fuera de producción |

## 5. Ejemplos de uso (ilustrativos)

- Especificación de luminarias: Claude propone dos modelos `APPROVED` con su flujo, potencia, IP y vida útil de la hoja de datos, en lugar de usar una luminaria de referencia supuesta.
- El cliente tiene su propia lista de marcas: Claude propone solo la intersección con el catálogo y consulta al usuario si no hay coincidencia.

## 6. Buenas prácticas

- Cargar pocos datos clave por equipo (los que se usan en cálculo y especificación), no la hoja completa.
- Indicar siempre unidad y condiciones de ensayo de cada dato (por ejemplo, flujo a 25 °C).
- No cargar precios ni condiciones comerciales (`RG-05`).
- Archivar la hoja de datos con la versión y fecha.

---

# CATÁLOGO (completar y mantener)

| ID | Disciplina | Tipo | Fabricante | Modelo / serie | Datos garantizados clave (valor, unidad, condición) | Norma de producto | Hoja de datos (archivo) | Fecha de la hoja | Estado | Aprobado por clientes | Proyectos donde se usó | Experiencia / lecciones |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EQP-001 | | | | | | | | | | | | |
