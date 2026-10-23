# drawing-status.md — Listado de Planos y Diagramas

| Campo | Valor |
|---|---|
| Proyecto | `[DEFINIR]` |
| Versión | 0.1 |
| Fecha | `[DEFINIR]` |
| Responsable | `[DEFINIR]` |

---

# GUÍA DEL ARCHIVO (no editar)

## Objetivo

Registrar el estado real de cada plano y diagrama dibujado en CAD. Los planos los dibuja el usuario a mano en su programa CAD, por lo que Claude no puede conocer su estado ni leer el DWG: este archivo es la **fuente única** del estado de los planos (`DOCUMENT_RULES.md`, RG-06). `deliverables.md` (LME) y `project-status.md` solo remiten a él; no repiten ese estado.

## Alcance

Todos los planos (`PL`) y diagramas dibujados en CAD (`DG`) de la LME, de cualquier fase (`IC`, `IB`, `ID`, `IE`, `ASB`); el plano es el mismo archivo y madura de fase en fase. Los diagramas y esquemas que Claude redacta en Markdown no figuran aquí: tienen su estado en la LME como cualquier documento.

## Forma de utilización

1. **Quién edita:** el usuario, a mano. **Claude nunca modifica la columna *Estado***. Claude solo (a) propone filas nuevas con estado `PLANNED` o `CAD_INPUT` (las agrega al aprobarse el plan de paquetes o al entregar los insumos de dibujo) y (b) completa la columna *Verificación de Claude* y, si hace falta, las observaciones propias.
2. **Estados:**

   | Estado | Significa | Quién lo fija |
   |---|---|---|
   | `PLANNED` | Plano previsto en la LME; todavía sin insumos | Claude (al proponer la fila) |
   | `CAD_INPUT` | Claude entregó los insumos de dibujo (y su paquete está `REVIEWED`) | Claude (al proponer la fila) o el usuario |
   | `DRAWN` | El usuario dibujó el plano y dejó el DWG de trabajo y el PDF de revisión | El usuario |
   | `REVIEWED` | El usuario revisó el plano y lo da por conforme (su OK personal, sin hoja de revisión aparte) | El usuario |
   | `ENTREGADO` | El plano salió en una entrega confirmada con `entrega enviada TR-nnn` | El usuario |

3. **Flujo:** Claude entrega los insumos (`CAD_INPUT`) → el usuario dibuja, marca `DRAWN` y deja el PDF de revisión → dice `verificar plano [código]` o `actualizar planos` → Claude escribe su verificación; cada observación se registra como `REV-nnn` → el usuario corrige y, cuando queda conforme, marca `REVIEWED` → tras `entrega enviada TR-nnn`, marca `ENTREGADO`. Un plano ya `REVIEWED` que cambia se tramita como `rfc` (`change-requests.md`): se entregan insumos actualizados y el plano vuelve a `CAD_INPUT`.
4. **Al abrir cada sesión** Claude lee este archivo. Si la fecha del último cambio (la mayor de la columna *Fecha del estado*) es anterior al último paquete entregado, pregunta si hubo cambios que no se registraron.
5. **Auditoría:** `project-audit.md` verifica la coherencia entre este archivo, la LME y las carpetas (A1-13, A4-02 y A4-14, según corresponda) y que ningún plano figure en una entrega si no está `REVIEWED`.
6. **Fase y paquete:** *Fase* es `IC`, `IB`, `ID`, `IE` o `ASB` (la fase en que está el plano; cambia sin duplicar el archivo); *Paquete* es el `PQ-nn` de la LME que contiene los insumos del plano.
7. **Rutas:** *Archivo DWG* y *PDF de revisión* son rutas relativas a la raíz del proyecto, dentro de `02-engineering` (`CAD_standards.md`, 3.1). Sin archivo todavía, se escribe `—`.
8. **Rev interna:** la revisión interna del plano (`00.0`, `00.n` por `rfc`, `01` as-built). El cliente siempre lo recibe rotulado `Rev 00` (`DOCUMENT_RULES.md`, sección 9).
9. **Verificación de Claude:** `—` (sin verificar), `OK` o `OBSERVACIONES rfc/REV-nnn` (con los identificadores que corresponda). Una verificación queda vigente solo si es posterior a la *Fecha del estado* del plano.

## Estructura recomendada

Una fila por plano o diagrama, ordenada por código. Los IDs de ejemplo llevan el prefijo `EJ-`.

## Buenas prácticas

- Actualizar el estado en el mismo momento en que cambia; es la única fuente.
- No marcar `REVIEWED` un plano con observaciones abiertas, salvo decisión registrada (`DEC-nnn`) en *Observaciones del usuario*.
- Dejar el PDF de revisión con el mismo nombre del DWG y en la misma carpeta (`CAD_standards.md`, sección 10).
- No borrar filas: un plano dado de baja se marca en *Observaciones del usuario* con su `DEC-nnn` o `rfc-nnn`.

---

# PLANTILLA — LISTADO DE PLANOS (completar)

| Código | Título | Disciplina | Fase | Paquete | Rev interna | Estado | Fecha del estado | Archivo DWG | PDF de revisión | Verificación de Claude | Observaciones del usuario |
|---|---|---|---|---|---|---|---|---|---|---|---|
| EJ-ACM01-E-PL-110 | Planta de sala eléctrica, distribución de tableros | Electricidad | ID | EJ-PQ-06 | 00.0 | DRAWN | 2026-10-21 | `02-engineering/DRAWINGS/ACM01-E-PL-110_Rev00.0.dwg` | `02-engineering/DRAWINGS/ACM01-E-PL-110_Rev00.0.pdf` | OBSERVACIONES REV-014 | Corregiré la cota del tablero TG-01 |
| EJ-ACM01-E-DG-020 | Esquema unifilar general de media tensión | Electricidad | IB | EJ-PQ-04 | 00.0 | CAD_INPUT | 2026-10-14 | — | — | — | Empiezo a dibujar la semana próxima |
| `[DEFINIR]` | `[DEFINIR]` | `[DEFINIR]` | | | | | | | | | |
