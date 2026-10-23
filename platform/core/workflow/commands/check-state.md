# Estado del proyecto

## Paso 1 — Ejecutar el script

```bash
python3 -B .claude/hooks/check-state.py
```

Leer la salida completa.

## Paso 2 — Interpretar y presentar

Presentar al usuario en este formato exacto:

```
## Estado del proyecto — [FECHA]

**Fase de ingeniería:** [IC / IB / ID / IE / ASB]
**Estado del proyecto:** [planning / ENGINEERING / FOR_REVIEW / FOR_AUDIT / AUDITED / ifa / ifc / ...]

### Paquetes

| Paquete | Nombre | Estado | Próximo paso |
|---|---|---|---|
| PQ-nn | [nombre] | ENGINEERING / FOR_REVIEW / REVIEWED / FOR_AUDIT / ... | [acción] |

### Alertas
[Hashes modificados fuera de Engineering — si los hay]
[Copias sueltas detectadas — si las hay]
[Paquetes REABIERTO — si los hay]

### Pendiente del usuario
[Qué se espera: revisar hoja de PQ-nn / confirmar siguiente paquete / nada]

### Próximo paso
**Frase fija:** `[frase exacta de COMMANDS.md]`
```

## Reglas de interpretación

- **Hash modificado fuera de `02-engineering`**: reportar inmediatamente como alerta CRITICAL. El paquete afectado vuelve a `02-engineering`.
- **Copia suelta** (mismo código de documento en más de una carpeta fuera de Archive): reportar. No eliminar sin confirmación del usuario.
- **Paquete `FOR_REVIEW` sin hoja de revisión**: alertar al usuario de que hay una revisión pendiente sin atender.
- **Estado `FOR_AUDIT`**: reportar que la auditoría automática se ejecutará antes de cualquier otra tarea.
- Si `check-state.py` no existe o falla: reportarlo y listar manualmente los paquetes presentes en `03-review/`, `04-audit/`, `05-released/` y `02-engineering/`.
