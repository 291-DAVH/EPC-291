# Autocontrol de cierre documental — `$ARGUMENTS`

Este skill ejecuta la lista fija de autocontrol del punto 7 de M5 para el paquete indicado.

## Paso 1 — Verificación mecánica (script)

Correr el verificador automático desde la raíz del proyecto:

```bash
python3 -B .claude/library/plugins/calculations/document_verifier.py <ruta_carpeta_proyecto>
```

Leer su salida completa. Los ítems marcados como `ERROR` son CRITICAL; los `AVISO` son MAJOR o MINOR según el tipo.

Si el paquete contiene un pliego (`PG`), correr también:

```bash
python3 -B .claude/library/plugins/calculations/specification_verifier.py 02-engineering/TECHNICAL_SPECS
```

## Paso 2 — Verificaciones manuales (los 10 puntos que el script no cubre)

Para cada documento `.md` del paquete, verificar:

1. **Revisión en portada = revisión en nombre de archivo = revisión en `deliverables.md`** (el script verifica esto, pero confirmar visualmente si hay AVISO).
2. **Control de revisiones completo**: cada fila describe el cambio; las filas con `REV-nnn` citan el comentario; las filas con `00.n` citan la `rfc-00n`.
3. **Sufijo de fase correcto** en la revisión (`.IC`, `.IB`, `.ID`, `.IE`); coincide con la fase actual en `project-status.md`.
4. **Toda marca abierta** (`[DEFINIR]`, `[VERIFICAR]`) está registrada como pendiente aceptado en `project-status.md` bloque B, con ID, fecha y firmante.
5. **IDs citados existen** en sus registros (el script verifica DEC, SUP, INF, REV, rfc, PAR; verificar manualmente ALD, CAC, ENG-INT).
6. **No hay valores redefinidos** que deberían venir de `project-information.md` (tensiones, potencias, Icc).
7. **Cheklist de `DOCUMENT_RULES.md`, sección 12** superado (el script verifica formato Pandoc; verificar manualmente la tabla de portada y el bloque YAML).
8. **`traceability-matrix.md`** actualizado con los `ENT-nnn` de este paquete.
9. **`deliverables.md`** actualizado: estado `FOR_REVIEW`, columna *Paquete* completa.
10. **`project-status.md`** actualizado: paquete actual, estado, próximo paquete propuesto.

Para un paquete con **síntesis de cálculo** (`SM`): verificar además que ningún valor, hipótesis ni conclusión de la síntesis difiere de su memoria de cálculo.

## Paso 3 — Resultado

Si no hay ítems CRITICAL ni errores del script:

```
AUTOCONTROL OK — PQ-nn listo para FOR_REVIEW
Ejecutar: python3 -B .claude/hooks/send-to-review.py PQ-nn
```

Si hay ítems CRITICAL:

```
AUTOCONTROL BLOQUEADO — PQ-nn
Ítems CRITICAL:
  [lista]
Corregir antes de enviar a revisión.
```

Listar también los MAJOR para que el usuario los conozca, aunque no bloqueen el envío.
