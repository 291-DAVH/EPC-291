"""CAL-004 · short_circuit — Corriente de cortocircuito trifásica simétrica inicial (IEC 60909 simplificado).

ESTADO: BORRADOR — pendiente de validación por el usuario.

OBJETIVO
    Calcular Ik'' (trifásica, simétrica, inicial) en un punto de una red radial de baja tensión
    por el método de impedancias: red aguas arriba + transformador + cable.

FÓRMULAS
    Ik'' = c · Un / (√3 · |Z_k|) ,   Z_k = Σ R + j Σ X      (suma en el nivel de tensión del punto de falla)
    Red aguas arriba (referida a Un del punto de falla, relación de transformación nominal):
        por potencia de cortocircuito:  Z_Q = c · Un² / Sk''
        por corriente:                  Z_Q = c · Un / (√3 · Ik''_Q)
        Descomposición: R_Q = Z_Q / √(1 + (X/R)²) ,  X_Q = (X/R) · R_Q ;
        X/R por defecto 10 (R_Q = 0,1·X_Q). [VERIFICAR]
    Transformador (Sn, Un secundario, uk%, Pcu opcional):
        Z_T = (uk/100) · Un² / Sn
        con Pcu :  R_T = Pcu · Un² / Sn² ,  X_T = √(Z_T² − R_T²)
        sin Pcu :  R_T = 0, X_T = Z_T (simplificación; no siempre conservadora con cable en serie:
                   ingresar Pcu del ensayo/catálogo para mayor exactitud)
        Corriente asignada secundaria: In = Sn / (√3·Un)  ;  con red infinita y sin cable:
        Ik'' = c·In/(uk/100).
    Cable:  R_C = r·L/(1000·n) ,  X_C = x·L/(1000·n)   (r, x en Ω/km; L en m; n conductores en paralelo)
    Factor de tensión c (tensión máxima de cálculo, IEC 60909, baja tensión):
        c_max = 1,05 si la tolerancia de tensión es 6 %;  c_max = 1,10 si es 10 %.  [VERIFICAR]

FUNCIONES ADICIONALES (documentadas y SEPARADAS; no se aplican salvo que se llamen)
    - factor_kt(x_t, c): factor de corrección de impedancia del transformador
          K_T = 0,95 · c / (1 + 0,6 · x_T) ,  x_T = X_T / Z_nominal_T (en p.u.)  [VERIFICAR]
      Se aplica sólo si se pide `aplicar_kt=True` en calcular_ik.
    - aporte_motor(sr_va, un_v, ilr_ir, c): aporte inicial de un motor asíncrono
          Ik''_M = c · (I_LR / I_rM) · I_rM  ;  I_rM = S_rM / (√3 · Un)
      con suma aritmética (conservadora) con la corriente de la red. I_LR/I_rM típico 5 a 7 [VERIFICAR].
    - factor_kappa(r, x) y corriente_pico(ik, r, x):
          κ = 1,02 + 0,98 · exp(−3 · R/X) ;  i_p = κ · √2 · Ik''   [VERIFICAR]

HIPÓTESIS
    - Falla trifásica franca (impedancia de falla nula), red radial, sistema equilibrado.
    - Relación de transformación nominal; se desprecian capacidades y cargas.
    - Resistencias a 20 °C salvo que el usuario ingrese R ya corregida (para Ik máx. es lo habitual;
      para Ik mín. la resistencia debe corregirse por temperatura y usar c_min — no incluido).

UNIDADES
    Un [V], Sn [VA], Sk'' [VA], Ik'' [A], R, X, Z [Ω], cable [Ω/km] y L [m], uk [%], Pcu [W].

LIMITACIONES / ADVERTENCIAS
    - calcular_ik NO incluye el aporte de motores ni el factor κ (corriente de pico):
      cada resultado trae esta advertencia en el campo "advertencias". Usar aporte_motor y
      corriente_pico explícitamente si se requieren.
    - No calcula Ik mínima (c_min = 0,95 [VERIFICAR] y R a temperatura final no están incluidos),
      ni corrientes de falla asimétricas (bifásica, fase-tierra), ni redes malladas.
    - No hay tabla de impedancias de cables ni de transformadores: son datos de entrada.

NORMA DE REFERENCIA (por designación)
    - IEC 60909-0 (corrientes de cortocircuito en redes trifásicas de c.a.). [VERIFICAR] los
      valores de c, K_T y κ citados de memoria.
"""

import math
from epc_calc._validate import nonneg as _nonneg, pos as _pos

__version__ = "0.1.0"

#: Factor de tensión c_max en BT según tolerancia de tensión. [VERIFICAR]
C_MAX_BT_TOL_6 = 1.05   # [VERIFICAR]
C_MAX_BT_TOL_10 = 1.10  # [VERIFICAR]
#: Relación X/R por defecto de la red aguas arriba (R_Q = 0,1·X_Q). [VERIFICAR]
XR_RED_DEFECTO = 10.0   # [VERIFICAR]
#: Umbral de aporte de motores BT despreciable (fracción de Ik'' sin motores). [VERIFICAR]
UMBRAL_MOTORES_DESPRECIABLE = 0.05  # [VERIFICAR]

WARNING_MOTORS = ("No incluye aporte de motores (usar aporte_motor() y sumar explícitamente).")
ADVERTENCIA_KAPPA = ("No incluye factor κ ni corriente de pico i_p (usar corriente_pico() explícitamente).")

_RAIZ3 = math.sqrt(3.0)


def factor_c(tolerancia_pct):
    """c_max para BT: 6 % -> 1,05 ; 10 % -> 1,10. Otro valor: ValueError (pasar c explícito)."""
    if tolerancia_pct == 6:
        return C_MAX_BT_TOL_6
    if tolerancia_pct == 10:
        return C_MAX_BT_TOL_10
    raise ValueError(f"Tolerancia {tolerancia_pct!r} % sin c predefinido (solo 6 o 10); ingresar c explícito")


def corriente_asignada_trafo(sn_va, un_v):
    """In [A] = Sn / (√3·Un)."""
    _pos(sn_va, "sn_va")
    _pos(un_v, "un_v")
    return sn_va / (_RAIZ3 * un_v)


def impedancia_red(un_v, c, sk_va=None, ik_a=None, x_r=XR_RED_DEFECTO):
    """(R, X) [Ω] de la red aguas arriba referida a Un. Indicar EXACTAMENTE uno de sk_va o ik_a."""
    _pos(un_v, "un_v")
    _pos(c, "c")
    _pos(x_r, "x_r")
    if (sk_va is None) == (ik_a is None):
        raise ValueError("Indicar exactamente uno de sk_va (potencia de cortocircuito) o ik_a (corriente)")
    if sk_va is not None:
        _pos(sk_va, "sk_va")
        z = c * un_v ** 2 / sk_va
    else:
        _pos(ik_a, "ik_a")
        z = c * un_v / (_RAIZ3 * ik_a)
    r = z / math.sqrt(1.0 + x_r ** 2)
    return r, x_r * r


def impedancia_transformador(sn_va, un_v, uk_pct, pcu_w=None):
    """(R, X) [Ω] del transformador referida al secundario (Un). pcu_w opcional."""
    _pos(sn_va, "sn_va")
    _pos(un_v, "un_v")
    _pos(uk_pct, "uk_pct")
    if uk_pct >= 100:
        raise ValueError("uk_pct debe ser < 100")
    z = (uk_pct / 100.0) * un_v ** 2 / sn_va
    if pcu_w is None:
        return 0.0, z
    _nonneg(pcu_w, "pcu_w")
    r = pcu_w * un_v ** 2 / sn_va ** 2
    if r >= z:
        raise ValueError("Pcu incompatible con uk: R_T ≥ Z_T (pérdidas en el cobre ≥ uk·Sn)")
    return r, math.sqrt(z * z - r * r)


def impedance_cable(r_ohm_km, x_ohm_km, longitud_m, n_paralelo=1):
    """(R, X) [Ω] de un tramo de cable (n_paralelo conductores por fase)."""
    _nonneg(r_ohm_km, "r_ohm_km")
    _nonneg(x_ohm_km, "x_ohm_km")
    _nonneg(longitud_m, "longitud_m")
    if not isinstance(n_paralelo, int) or isinstance(n_paralelo, bool) or n_paralelo < 1:
        raise ValueError("n_paralelo debe ser entero ≥ 1")
    k = longitud_m / 1000.0 / n_paralelo
    return r_ohm_km * k, x_ohm_km * k


def factor_kt(x_t_pu, c):
    """K_T = 0,95·c/(1 + 0,6·x_T), x_T = X_T/Z_nominal en p.u. [VERIFICAR]."""
    _nonneg(x_t_pu, "x_t_pu")
    _pos(c, "c")
    return 0.95 * c / (1.0 + 0.6 * x_t_pu)


def ik_desde_impedancia(un_v, c, r_ohm, x_ohm):
    """Ik'' [A] = c·Un/(√3·|Z|)."""
    _pos(un_v, "un_v")
    _pos(c, "c")
    _nonneg(r_ohm, "r_ohm")
    _nonneg(x_ohm, "x_ohm")
    z = math.hypot(r_ohm, x_ohm)
    if z == 0:
        raise ValueError("Impedancia total nula: Ik'' infinita (agregar red, transformador o cable)")
    return c * un_v / (_RAIZ3 * z)


def calcular_ik(un_v, c, red=None, trafo=None, cables=None, aplicar_kt=False):
    """Ik'' trifásica inicial en el punto de falla.

    red   : None (red infinita, Z_Q = 0) o dict {"sk_va": ..} / {"ik_a": ..} [+ "x_r"]
    trafo : None o dict {"sn_va", "uk_pct", ["pcu_w"]}; usa un_v como tensión secundaria
    cables: lista de dicts {"r_ohm_km", "x_ohm_km", "longitud_m", ["n_paralelo"]} (en serie)
    aplicar_kt: si True, multiplica la impedancia del transformador por K_T (requiere trafo)
    Devuelve dict: ik_a, z_ohm, r_ohm, x_ohm, c, advertencias (list[str]).
    """
    _pos(un_v, "un_v")
    _pos(c, "c")
    r_tot = x_tot = 0.0
    adv = [WARNING_MOTORS, ADVERTENCIA_KAPPA]
    if red is None:
        adv.append("Red aguas arriba considerada infinita (Z_Q = 0): resultado conservador.")
    else:
        r, x = impedancia_red(un_v, c, red.get("sk_va"), red.get("ik_a"), red.get("x_r", XR_RED_DEFECTO))
        r_tot += r
        x_tot += x
    if trafo is not None:
        r, x = impedancia_transformador(trafo["sn_va"], un_v, trafo["uk_pct"], trafo.get("pcu_w"))
        if aplicar_kt:
            # x_T en p.u. = X_T / Z_nominal_T, con Z_nominal_T = Un²/Sn
            kt = factor_kt(x * trafo["sn_va"] / un_v ** 2, c)
            r, x = r * kt, x * kt
            adv.append(f"Se aplicó K_T = {kt:.4f} al transformador [VERIFICAR].")
        r_tot += r
        x_tot += x
    elif aplicar_kt:
        raise ValueError("aplicar_kt requiere un transformador")
    for cab in (cables or []):
        r, x = impedance_cable(cab["r_ohm_km"], cab["x_ohm_km"], cab["longitud_m"], cab.get("n_paralelo", 1))
        r_tot += r
        x_tot += x
    ik = ik_desde_impedancia(un_v, c, r_tot, x_tot)
    return {"ik_a": ik, "z_ohm": math.hypot(r_tot, x_tot), "r_ohm": r_tot, "x_ohm": x_tot,
            "c": c, "advertencias": adv}


def aporte_motor(sr_va, un_v, ilr_ir, c):
    """Aporte inicial [A] de un motor asíncrono: Ik''_M = c·(I_LR/I_rM)·I_rM. [VERIFICAR]
    Se suma ARITMÉTICAMENTE a Ik'' de la red (conservador)."""
    _pos(sr_va, "sr_va")
    _pos(un_v, "un_v")
    _pos(ilr_ir, "ilr_ir")
    _pos(c, "c")
    return c * ilr_ir * sr_va / (_RAIZ3 * un_v)


def motors_negligible(ik_motores_a, ik_sin_motores_a):
    """True si el aporte de motores ≤ 5 % de Ik'' sin motores. [VERIFICAR] umbral."""
    _nonneg(ik_motores_a, "ik_motores_a")
    _pos(ik_sin_motores_a, "ik_sin_motores_a")
    return ik_motores_a <= UMBRAL_MOTORES_DESPRECIABLE * ik_sin_motores_a


def factor_kappa(r_ohm, x_ohm):
    """κ = 1,02 + 0,98·exp(−3·R/X). [VERIFICAR]"""
    _nonneg(r_ohm, "r_ohm")
    _nonneg(x_ohm, "x_ohm")
    if r_ohm == 0 and x_ohm == 0:
        raise ValueError("R y X no pueden ser ambos cero")
    if x_ohm == 0:
        return 1.02
    return 1.02 + 0.98 * math.exp(-3.0 * r_ohm / x_ohm)


def corriente_pico(ik_a, r_ohm, x_ohm):
    """i_p [A] = κ·√2·Ik''. [VERIFICAR]"""
    _pos(ik_a, "ik_a")
    return factor_kappa(r_ohm, x_ohm) * math.sqrt(2.0) * ik_a


if __name__ == "__main__":
    print("== CAL-004 short_circuit — ejemplo (valores ilustrativos) ==")
    un, c = 400.0, factor_c(6)
    print(f"In del transformador 1000 kVA / 400 V = {corriente_asignada_trafo(1e6, un):.1f} A")
    r = calcular_ik(un, c, red=None, trafo={"sn_va": 1e6, "uk_pct": 6})
    print(f"Ik'' en bornes secundarios (red infinita, c={c}): {r['ik_a']/1000:.2f} kA")
    r = calcular_ik(un, c, red={"sk_va": 500e6}, trafo={"sn_va": 1e6, "uk_pct": 6},
                    cables=[{"r_ohm_km": 0.2, "x_ohm_km": 0.08, "longitud_m": 50}])
    print(f"Ik'' al final de 50 m de cable (red 500 MVA): {r['ik_a']/1000:.2f} kA  |Z| = {r['z_ohm']*1000:.2f} mΩ")
    for a in r["advertencias"]:
        print("  ADVERTENCIA:", a)
