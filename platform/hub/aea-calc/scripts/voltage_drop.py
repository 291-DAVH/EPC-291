"""CAL-002 · voltage_drop — Caída de tensión en conductores (monofásica y trifásica).

ESTADO: BORRADOR — pendiente de validación por el usuario.

OBJETIVO
    Calcular la caída de tensión de un circuito a partir de la corriente, la longitud,
    la resistencia y reactancia por km del conductor y el factor de potencia de la
    carga; expresarla en V y en % de la tensión nominal; y obtener la longitud máxima
    para un límite dado.

FÓRMULAS
    Trifásica (equilibrada):   ΔU = √3 · I · L · (R·cosφ + X·senφ)      [V, tensión de línea]
    Monofásica (ida y vuelta): ΔU = 2  · I · L · (R·cosφ + X·senφ)      [V]
    Porcentaje:                ΔU% = 100 · ΔU / Un
        I [A]; L [km] (la función recibe metros y convierte); R, X [Ω/km];
        senφ = √(1 − cos²φ) (carga inductiva; con carga capacitiva el signo de senφ es negativo).
        Un = tensión entre conductores de línea (trifásica) o entre los dos conductores
        del circuito (monofásica; p. ej. 230 V fase-neutro).
    Longitud máxima:           L_max = ΔU_max / (k · I · (R·cosφ + X·senφ))   con k = √3 o 2.

HIPÓTESIS
    - Sistema trifásico equilibrado; neutro sin corriente.
    - R y X dados a la temperatura de servicio del conductor (el usuario elige el valor;
      el módulo no corrige por temperatura).
    - Fórmula lineal aproximada (se desprecia el término de segundo orden de la caída).
    - Se ignora la capacitancia de la línea y el efecto de proximidad no incluido en R, X.
    - Corriente constante a lo largo del tramo (carga concentrada al final).

UNIDADES
    I [A], L de entrada en [m], R y X [Ω/km], ΔU [V], ΔU% [%], Un [V].

LIMITACIONES
    - No se incluye ningún límite normativo de caída de tensión: el límite (%) es dato
      de entrada, tomado del criterio del proyecto / reglamentación local.
    - No hay tabla de R, X de cables: se reciben del catálogo del fabricante o de la norma.
    - Cargas distribuidas, cargas múltiples en cascada y arranque de motores no están
      cubiertos (sumar tramos con la función por tramo).

NORMA DE REFERENCIA (por designación)
    - IEC 60364-5-52 (selección e instalación de canalizaciones; caída de tensión),
      y la reglamentación local de instalaciones eléctricas aplicable. [VERIFICAR]
      Los límites admisibles de ΔU% no se incluyen en este módulo.
"""

import math

__version__ = "0.1.0"


def _num(valor, nombre, minimo=0.0, estricto=False):
    if not isinstance(valor, (int, float)) or isinstance(valor, bool) or not math.isfinite(valor):
        raise ValueError(f"{nombre} debe ser un número finito (recibido: {valor!r})")
    if (estricto and valor <= minimo) or (not estricto and valor < minimo):
        op = ">" if estricto else "≥"
        raise ValueError(f"{nombre} debe ser {op} {minimo} (recibido: {valor})")


def _factor_z(r_ohm_km, x_ohm_km, fp, capacitiva):
    """R·cosφ + X·senφ [Ω/km]."""
    _num(r_ohm_km, "r_ohm_km")
    _num(x_ohm_km, "x_ohm_km")
    _num(fp, "fp")
    if fp > 1:
        raise ValueError(f"fp debe estar en [0, 1] (recibido: {fp})")
    sen = math.sqrt(max(0.0, 1.0 - fp * fp))
    if capacitiva:
        sen = -sen
    return r_ohm_km * fp + x_ohm_km * sen


def _delta_u(k, i_a, longitud_m, r_ohm_km, x_ohm_km, fp, capacitiva):
    _num(i_a, "i_a")
    _num(longitud_m, "longitud_m")
    return k * i_a * (longitud_m / 1000.0) * _factor_z(r_ohm_km, x_ohm_km, fp, capacitiva)


def drop_voltage_three_phase_v(i_a, longitud_m, r_ohm_km, x_ohm_km, fp, capacitiva=False):
    """ΔU [V] trifásica: √3·I·L·(R·cosφ + X·senφ)."""
    return _delta_u(math.sqrt(3.0), i_a, longitud_m, r_ohm_km, x_ohm_km, fp, capacitiva)


def drop_voltage_single_phase_v(i_a, longitud_m, r_ohm_km, x_ohm_km, fp, capacitiva=False):
    """ΔU [V] monofásica: 2·I·L·(R·cosφ + X·senφ)."""
    return _delta_u(2.0, i_a, longitud_m, r_ohm_km, x_ohm_km, fp, capacitiva)


def porcentaje(delta_u_v, un_v):
    """ΔU% = 100·ΔU/Un."""
    _num(delta_u_v, "delta_u_v")
    _num(un_v, "un_v", estricto=True)
    return 100.0 * delta_u_v / un_v


def caida_tension(fases, i_a, longitud_m, r_ohm_km, x_ohm_km, fp, un_v, capacitiva=False):
    """Caída de tensión en V y %. fases = 1 (monofásica) o 3 (trifásica).

    Devuelve dict {"delta_u_v", "delta_u_pct", "fases", "un_v"}.
    """
    if fases == 3:
        du = drop_voltage_three_phase_v(i_a, longitud_m, r_ohm_km, x_ohm_km, fp, capacitiva)
    elif fases == 1:
        du = drop_voltage_single_phase_v(i_a, longitud_m, r_ohm_km, x_ohm_km, fp, capacitiva)
    else:
        raise ValueError(f"fases debe ser 1 o 3 (recibido: {fases!r})")
    return {"delta_u_v": du, "delta_u_pct": porcentaje(du, un_v), "fases": fases, "un_v": un_v}


def complies_limit(delta_u_pct, limite_pct):
    """True si ΔU% ≤ límite (el límite es dato del proyecto, no de este módulo)."""
    _num(delta_u_pct, "delta_u_pct")
    _num(limite_pct, "limite_pct", estricto=True)
    return delta_u_pct <= limite_pct


def longitud_maxima_m(fases, delta_u_max_v, i_a, r_ohm_km, x_ohm_km, fp, capacitiva=False):
    """Longitud máxima [m] para no superar delta_u_max_v."""
    _num(delta_u_max_v, "delta_u_max_v", estricto=True)
    _num(i_a, "i_a", estricto=True)
    if fases == 3:
        k = math.sqrt(3.0)
    elif fases == 1:
        k = 2.0
    else:
        raise ValueError(f"fases debe ser 1 o 3 (recibido: {fases!r})")
    z = _factor_z(r_ohm_km, x_ohm_km, fp, capacitiva)
    if z <= 0:
        raise ValueError("R·cosφ + X·senφ ≤ 0: la caída no es positiva, longitud máxima indefinida")
    return 1000.0 * delta_u_max_v / (k * i_a * z)


if __name__ == "__main__":
    print("== CAL-002 voltage_drop — ejemplo (valores ilustrativos) ==")
    r = caida_tension(3, i_a=100, longitud_m=200, r_ohm_km=0.5, x_ohm_km=0.1, fp=0.8, un_v=400)
    print(f"Trifásica 100 A, 200 m, R=0,5 X=0,1 Ω/km, cosφ=0,8: ΔU = {r['delta_u_v']:.2f} V = {r['delta_u_pct']:.2f} % de 400 V")
    r = caida_tension(1, i_a=100, longitud_m=200, r_ohm_km=0.5, x_ohm_km=0.1, fp=0.8, un_v=230)
    print(f"Monofásica (mismos datos): ΔU = {r['delta_u_v']:.2f} V = {r['delta_u_pct']:.2f} % de 230 V")
    lm = longitud_maxima_m(3, 0.03 * 400, 100, 0.5, 0.1, 0.8)
    print(f"Longitud máxima trifásica para 3 % de 400 V: {lm:.0f} m")
