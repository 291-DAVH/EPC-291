"""CAL-020 · aea_icc_decay — κ exacto, μ, λ, q, m y n (AEA IT 90909-1).

ESTADO: BORRADOR — pendiente de validación por el usuario.

OBJETIVO
    Factores que describen la evolución temporal de la corriente de cortocircuito:
    corriente de pico (κ exacto), corriente de ruptura (μ), corriente permanente (λ),
    motores (q) y efecto térmico (m, n). Complementa `short_circuit.py`, que contiene
    κ aproximado [68] e i_p; aquí solo se agrega el cálculo exacto y los demás factores.

FÓRMULAS (numeración AEA IT 90909-1)
    [67] i_p = κ·√2·I''k ; [72] κ = máx_t[ sen(ωt − γ) + e^(−(R/X)·ωt)·senγ ], γ = atan(X/R)
    [78] I_k,ac(t) = (I''k−I'k)e^(−t/T''N) + (I'k−Ik)e^(−t/T'N) + Ik
    [79] I''k = E''/(X''d+XN) ; I'k = E'/(X'd+XN) ; Ik = E/(Xd+XN)
    [80] T''N = T''0·(X''d+XN)/(X'd+XN) ; T'N = T'0·(X'd+XN)/(Xd+XN)
    [81] μ ≈ [1 − (X''d+XN)/(X'd+XN)]·e^(−t_min/T''N) + (X''d+XN)/(X'd+XN)
    [83] I_kmax = λmax·I_rG ; [84] I_kmin = λmin·I_rG
    [89] E'' = U_rG/√3·(1 + x''d·senφ_rG) ; [90] E_r = U_rG/√3·√(1 + x²_dsat + 2·x_dsat·senφ_rG)
    [91] q = I_bM/(μ·I''kM) ; T_μq = −t_min/ln(μ·q)
    [92] ∫i²dt = I''k²·(m+n)·T_k ; [93] I_th = I''k·√(m+n)
    [96c] T_aN ≈ −1/(2f·ln(κ−1)) ; [96b] T'dN ≈ T'd0·(X'd+XN)/(Xd+XN)
    [99] ∫i²dt = I''k²·T_k·[1 + T_aN/T_k·(1 − e^(−2T_k/T_aN))]
    [100] m = [e^(4f·T_k·ln(κ−1)) − 1]/(2f·T_k·ln(κ−1))
    [101] n = (1/(I''k²·T_k))∫i²dt − m ; [102b] n con T''dN ≈ 0,1·T'dN

UNIDADES
    Tiempos [s], f [Hz], reactancias [Ω o p.u., coherentes], corrientes [A].

LIMITACIONES
    - El informe indica NO usar [82] para cálculos; no se codifica.
    - μ [81] solo para un cortocircuito con única alimentación (no redes malladas).
    - [96c] y [100] exigen 1 < κ < 2 (ln(κ−1) < 0); con κ = 2 (R = 0) no están definidas.
    - λ: fórmulas [83]–[90] dan la corriente de referencia; las curvas λmax/λmin
      (fig. 18/19 de 90909-0) NO se reproducen.

NORMA DE REFERENCIA
    AEA IT 90909-1 (2005) §2.4–2.8; AEA 90909-0.  [VERIFICAR]
"""
import math
from epc_calc._validate import num as _num

__version__ = "0.1.0"

U_FMAX = {("cilindrico", 1): 1.3, ("cilindrico", 2): 1.6, ("salientes", 1): 1.6, ("salientes", 2): 2.0}


def kappa_exacto(r_ohm, x_ohm, pasos=20000):
    """[72] κ = máx sobre ωt∈(0, 2π) de sen(ωt−γ) + e^(−(R/X)ωt)·senγ."""
    _num(r_ohm, "r_ohm")
    _num(x_ohm, "x_ohm", 0.0, True)
    g = math.atan2(x_ohm, r_ohm)
    rx = r_ohm / x_ohm
    mejor = -1.0
    for k in range(1, pasos + 1):
        wt = 2.0 * math.pi * k / pasos
        v = math.sin(wt - g) + math.exp(-rx * wt) * math.sin(g)
        if v > mejor:
            mejor = v
    return mejor


def current_peak_to(kappa, ik_a):
    """[67] i_p = κ·√2·I''k."""
    _num(kappa, "kappa", 0.0, True)
    _num(ik_a, "ik_a")
    return kappa * math.sqrt(2) * ik_a


def corrientes_generador(e2, e1, e, x_d2, x_d1, x_d, x_n=0.0):
    """[79] (I''k, I'k, Ik). E en V de fase; X en Ω."""
    for v, n in ((x_d2, "x_d2"), (x_d1, "x_d1"), (x_d, "x_d")):
        _num(v, n, 0.0, True)
    _num(x_n, "x_n")
    return (e2 / (x_d2 + x_n), e1 / (x_d1 + x_n), e / (x_d + x_n))


def constantes_tiempo(t2_0, t1_0, x_d2, x_d1, x_d, x_n=0.0):
    """[80] (T''N, T'N) [s] a partir de T''0 y T'0 de circuito abierto equivalentes."""
    for v, n in ((x_d2, "x_d2"), (x_d1, "x_d1"), (x_d, "x_d")):
        _num(v, n, 0.0, True)
    return (t2_0 * (x_d2 + x_n) / (x_d1 + x_n), t1_0 * (x_d1 + x_n) / (x_d + x_n))


def corriente_alterna_t(t, ik2, ik1, ik, t2_n, t1_n):
    """[78] I_k,ac(t)."""
    _num(t, "t")
    _num(t2_n, "t2_n", 0.0, True)
    _num(t1_n, "t1_n", 0.0, True)
    return (ik2 - ik1) * math.exp(-t / t2_n) + (ik1 - ik) * math.exp(-t / t1_n) + ik


def mu_generador(t_min, t2_n, x_d2, x_d1, x_n=0.0):
    """[81] μ ≈ [1 − (X''d+XN)/(X'd+XN)]·e^(−t_min/T''N) + (X''d+XN)/(X'd+XN)."""
    _num(t_min, "t_min")
    _num(t2_n, "t2_n", 0.0, True)
    _num(x_d1 + x_n, "x_d1+x_n", 0.0, True)
    r = (x_d2 + x_n) / (x_d1 + x_n)
    return (1.0 - r) * math.exp(-t_min / t2_n) + r


def current_steady_to(lambda_f, i_rg_a):
    """[83]/[84] I_k = λ·I_rG."""
    _num(lambda_f, "lambda_f")
    _num(i_rg_a, "i_rg_a")
    return lambda_f * i_rg_a


def voltage_internal_subtransient(u_rg, x_d2_pu, sen_fi_rg):
    """[89] E'' = U_rG/√3·(1 + x''d·senφ_rG)."""
    _num(u_rg, "u_rg", 0.0, True)
    return u_rg / math.sqrt(3) * (1.0 + x_d2_pu * sen_fi_rg)


def voltage_internal_rated(u_rg, x_dsat_pu, sen_fi_rg):
    """[90] E_r = U_rG/√3·√(1 + x²_dsat + 2·x_dsat·senφ_rG)."""
    _num(u_rg, "u_rg", 0.0, True)
    return u_rg / math.sqrt(3) * math.sqrt(1.0 + x_dsat_pu ** 2 + 2.0 * x_dsat_pu * sen_fi_rg)


def factor_q(ib_motor_a, mu, ik_motor_a):
    """[91] q = I_bM/(μ·I''kM)."""
    _num(ib_motor_a, "ib_motor_a")
    _num(mu, "mu", 0.0, True)
    _num(ik_motor_a, "ik_motor_a", 0.0, True)
    return ib_motor_a / (mu * ik_motor_a)


def constante_tiempo_mu_q(t_min, mu, q):
    """T_μq = −t_min/ln(μ·q) [s] (requiere 0 < μ·q < 1)."""
    if not 0.0 < mu * q < 1.0:
        raise ValueError("se requiere 0 < μ·q < 1")
    return -t_min / math.log(mu * q)


def constante_aperiodica_s(kappa, f_hz):
    """[96c] T_aN ≈ −1/(2f·ln(κ−1)), válido con 1 < κ < 2."""
    _num(f_hz, "f_hz", 0.0, True)
    if not 1.0 < kappa < 2.0:
        raise ValueError("κ debe estar entre 1 y 2")
    return -1.0 / (2.0 * f_hz * math.log(kappa - 1.0))


def factor_m(kappa, f_hz, t_k_s):
    """[100] m = [e^(4f·T_k·ln(κ−1)) − 1]/(2f·T_k·ln(κ−1)); 1 < κ < 2."""
    _num(f_hz, "f_hz", 0.0, True)
    _num(t_k_s, "t_k_s", 0.0, True)
    if not 1.0 < kappa < 2.0:
        raise ValueError("κ debe estar entre 1 y 2")
    a = 2.0 * f_hz * t_k_s * math.log(kappa - 1.0)
    return (math.exp(2.0 * a) - 1.0) / a


def factor_n_generico(ik2, ik1, ik, t_k, t2_dn, t1_dn):
    """[102a] con T_SN: 1/T_SN = 1/T''dN + 1/T'dN."""
    for v, nm in ((ik2, "ik2"), (ik1, "ik1"), (ik, "ik"), (t_k, "t_k"), (t2_dn, "t2_dn"), (t1_dn, "t1_dn")):
        _num(v, nm, 0.0, True)
    t_sn = 1.0 / (1.0 / t2_dn + 1.0 / t1_dn)
    a = ik2 / ik - ik1 / ik
    b = ik1 / ik - 1.0
    e = math.exp
    c = (1.0 + t2_dn / (2 * t_k) * (1 - e(-2 * t_k / t2_dn)) * a ** 2
         + t1_dn / (2 * t_k) * (1 - e(-2 * t_k / t1_dn)) * b ** 2
         + 2 * t2_dn / t_k * (1 - e(-t_k / t2_dn)) * a
         + 2 * t1_dn / t_k * (1 - e(-t_k / t1_dn)) * b
         + 2 * t_sn / t_k * (1 - e(-t_k / t_sn)) * a * b)
    return c / (ik2 / ik) ** 2


def factor_n_simplificado(ik2, ik1, ik, t_k, t1_dn):
    """[102b] con T''dN ≈ 0,1·T'dN."""
    for v, nm in ((ik2, "ik2"), (ik1, "ik1"), (ik, "ik"), (t_k, "t_k"), (t1_dn, "t1_dn")):
        _num(v, nm, 0.0, True)
    a = ik2 / ik - ik1 / ik
    b = ik1 / ik - 1.0
    e = math.exp
    c = (1.0 + t1_dn / (20 * t_k) * (1 - e(-20 * t_k / t1_dn)) * a ** 2
         + t1_dn / (2 * t_k) * (1 - e(-2 * t_k / t1_dn)) * b ** 2
         + t1_dn / (5 * t_k) * (1 - e(-10 * t_k / t1_dn)) * a
         + 2 * t1_dn / t_k * (1 - e(-t_k / t1_dn)) * b
         + t1_dn / (5.5 * t_k) * (1 - e(-11 * t_k / t1_dn)) * a * b)
    return c / (ik2 / ik) ** 2


def current_thermal_equivalent_to(ik2_a, m, n):
    """[93] I_th = I''k·√(m+n)."""
    _num(ik2_a, "ik2_a")
    _num(m + n, "m+n")
    return ik2_a * math.sqrt(m + n)
