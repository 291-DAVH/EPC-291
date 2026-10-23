# SCRIPTS — flujo por ubicación (WF-001)

El **estado de un paquete de revisión (`PQ-nn`) es la ubicación física de sus archivos**. Estos scripts son la única forma de moverlo entre etapas: Claude no mueve documentos a mano. Solo biblioteca estándar de Python; no hacen commits ni editan el contenido de ningún documento.

```text
02_ENGINEERING ──SEND_TO_REVIEW──► 03_REVIEW/REVIEW_PACKAGES/PQ-nn ──SEND_TO_AUDIT──► 04_AUDIT/AUDIT_PACKAGES/PQ-nn
      ▲                                  │ (Resultado ≠ APPROVED)                            │ (conjunto de la emisión completo
      └────────── RETURN_TO_ENGINEERING ◄┴───────────────────────────────────────────────────┘  + informe APPROVED)
                                                                                  APPROVE_AUDIT
                                                                                        ▼
                                              05_RELEASED/PQ-nn ──RELEASE_DOCUMENTS──► ISSUE_IFA / ISSUE_IFC ──► 06_DELIVERABLES (copia Rev 00)
                                                                                        CONFIRM_SENT (el usuario envió)
```

## Reglas que hacen cumplir

1. **Solo `APPROVED` avanza.** `APPROVED_WITH_COMMENTS`, `REJECTED` y `REJECTED_WITH_COMMENTS` ⇒ `RETURN_TO_ENGINEERING` y el ciclo se reinicia por completo.
2. **Todo paquete modificado vuelve a Ingeniería.** Al entrar en `03_REVIEW` se registra el SHA-256 de cada archivo (`90_MANAGEMENT/LEDGER/PQ-nn.json`); si al avanzar algún archivo difiere, el script se niega.
3. **Un paquete aprobado que vuelve a Ingeniería invalida la auditoría de su emisión**: los hermanos ya liberados y no emitidos regresan a `04_AUDIT`.
4. **Auditoría por conjunto**: una sola vez por emisión, con todos sus paquetes en `04_AUDIT` (`APPROVE_AUDIT.py` lo verifica contra el campo `Paquetes:` del informe).
5. **Planos**: el DWG, sus XREF (`..._XREF_...dwg`) y el PDF viajan juntos y quedan congelados; un DWG sin su PDF no entra al paquete. Claude revisa solo el PDF. Los insumos de dibujo (`_DIN_`) son internos y no se emiten.
6. **`06_DELIVERABLES` es una copia renombrada** (`_Rev00`; as-built `_Rev01`) y solo lectura; `05_RELEASED` conserva el conjunto aprobado.

## Scripts (ejecutar desde la raíz del proyecto o con `--root`)

| Script | Qué hace | Condición |
|---|---|---|
| `SEND_TO_REVIEW.py PQ-nn [--emision IFA\|IFC\|IFR\|AS_BUILT] [--extra ruta]` | 03 → 04; manifiesto; ronda +1 | Dependencias ya `REVIEWED`; un solo paquete en revisión (salvo `--permitir-varios DEC-nnn`); DWG con PDF |
| `RETURN_TO_ENGINEERING.py PQ-nn… --motivo "…" [--resultado X] [--con-dependientes]` | 04 / 05 / 06 → 03 | Siempre permitido; avisa de dependientes y de la auditoría invalidada |
| `SEND_TO_AUDIT.py PQ-nn` | 04 → 05 | Hoja de esta ronda con `Resultado: APPROVED`; hash intacto |
| `APPROVE_AUDIT.py --emision X [--aud AUD-nn]` | 05 → 06 (todo el conjunto) | Informe con `Emisión:`, `Paquetes:` = conjunto y `Resultado: APPROVED`; la aprobación humana la da el usuario con `aprobar auditoría` |
| `RELEASE_DOCUMENTS.py --emision X` | Registro de liberación en 06 | Conjunto completo y sin modificar |
| `ISSUE_IFA.py` / `ISSUE_IFC.py` / `ISSUE_ASBUILT.py [--tr TR-nnn]` | 06 → copia en `06_DELIVERABLES/<emisión>/YYYYMMDD_TR-nnn_Rev00/` + transmittal borrador | Liberación vigente |
| `CONFIRM_SENT.py TR-nnn` | Registra el envío al cliente (`IFA` / `IFC` / `AS_BUILT`) | Lo pide el usuario con `entrega enviada` |
| `START_ASBUILT.py` | Paquetes con IFC confirmado vuelven a 03 (emisión `AS_BUILT`) | IFC enviado |
| `CLOSE_PROJECT.py [--sin-asbuilt DEC-nnn]` | Cierra | Todo emitido y confirmado, nada en 03–05 |
| `CHECK_STATE.py [--escribir]` | Revisa ubicación, hashes, copias sueltas y emisiones; muestra el siguiente paso | Código de salida 1 si hay errores |

## Contratos de formato

- **Hoja de revisión** `03_REVIEW/REVIEW_SHEETS/REVIEW-nn_YYYYMMDD_PQ-nn.md`: línea `Resultado: APPROVED | APPROVED_WITH_COMMENTS | REJECTED | REJECTED_WITH_COMMENTS`, escrita por Claude **solo** cuando el usuario dicta su decisión. La hoja debe ser de esta ronda (fecha ≥ último envío).
- **Informe de auditoría** `04_AUDIT/AUDIT_REPORTS/AUD-nn_YYYYMMDD.md`: líneas `Emisión: IFA`, `Paquetes: PQ-01, PQ-02` y `Resultado: …`.
- **Registro** (generado, no se edita): `90_MANAGEMENT/LEDGER/` (`PQ-nn.json`, `EVENTS.md`, `COMPUTED_STATE.md`, `CLOSURE.md`) y la sección «Movimientos de paquetes» del `CHANGELOG.md`.

Pruebas: `python3 -B -m unittest discover -s 99_CORE/SCRIPTS`.
