"""Formato de números es-AR (coma decimal) de las memorias y síntesis, compartido por `aea_feeder_report` y `board_memo` (antes copiado en cada uno)."""
import math


def p1(x):
    """Un decimal, con coma."""
    return f"{x:.1f}".replace(".", ",")


def sig2(x):
    """Dos cifras significativas, con coma."""
    if not x:
        return "0"
    d = 1 - int(math.floor(math.log10(abs(x))))
    v = round(x, d)
    return (f"{v:.0f}" if d <= 0 else f"{v:.{d}f}").replace(".", ",")


def mm(x):
    """Sección en mm² con su valor exacto (sin redondeo)."""
    return f"{x:g}".replace(".", ",")
