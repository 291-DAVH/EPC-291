"""Topologías de circuito de la plataforma, en un solo lugar para `aea_pipeline` y `board_memo` (antes copiadas en cada uno)."""

# Circuitos de motor: arranque directo (con o sin protección térmica o diferencial), estrella-triángulo, arrancador suave y variador.
MOTOR_TOPOLOGIES = frozenset({"dol", "dol_ol", "star_delta", "softstarter", "vfd", "dol_rcd"})
