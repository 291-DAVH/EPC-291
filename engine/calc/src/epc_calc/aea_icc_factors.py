"""CAL-019 · aea_icc_factors — Factores de corrección de impedancia y fuente equivalente (AEA IT 90909-1).

ESTADO: BORRADOR — pendiente de validación por el usuario.

OBJETIVO
    Factores K de AEA IT 90909-1 (Ed. 2005, informe técnico de AEA 90909-0) para corregir las
    impedancias de generadores, grupos con y sin conmutador bajo carga y transformadores
    en el cálculo de I''k. Las ecuaciones citan la numeración [n] del propio informe.
    NO repite `short_circuit.py` (factor_c, impedancia_red/trafo/cable, factor_kt [65],
    factor_kappa [68], corriente_pico, aporte_motor): usar ese módulo para esos casos.

FÓRMULAS
    [15] c_max ≈ U_Qmax/Un ; [12] Δi''kmax = 1/(1+Δu_max) − 1
    [21]/[22] K_G   = (Un/U_rG)·c_max/(1 + x''d·senφ_rG)
    [31] K_S   = (U²_nQ/U²_rG)(U²_rTLV/U²_rTHV)·c_max/(1 + |x''d − x_T|·senφ_rG)
    [49a/b] K_SO = U_nQ/(U_rG(1+p_G))·(U_rTLV/U_rTHV)·[(1±p_T)]·c_max/(1 + x''d·senφ_rG)
    [38]/[45a] K_G,S = c_max/(1 + x''d·senφ_rG)
    [43] K_T,S = c_max/(1 + x_T/x_d) ; [45b] K_T,S = c_max/(1 − x_T·senφ_rG)
    [52] K_G,SO = 1/(1+p_G)·c_max/(1 + x''d·senφ_rG) ; [54] K_T,SO = c_max·U_rTHV/U_nQ
    [62]/[63] K_T = Un/U^b·c_max/(1 + x_T(I^b_T/I_rT)·senφ^b_T)
    [19] I''kG = c·Un/(√3·(R_G + jX''d)·K_G)
    [32] I''kS = c·U_nQ/(√3·(t_r²·Z_G + Z_THV)·K_S)
    [59] I''kT = c·Un/(√3·|Z_T·K_T + Z_Qt|) ; [60] X_T = u_Xr/100·U²_rTLV/S_rT
    [61] X_Qt = c_Q·U_nQ/(√3·I''kQ)·U²_rTLV/U²_rTHV
    Motores [108] I''kM ≤ 0,05·I''kQ → despreciables ; [110] ΣI_rM ≤ 0,01·I''kQ (I_LR/I_rM = 5)
    Defecto a tierra rígido si U_L,E/U_Y,E ≤ 1,4.

UNIDADES
    Tensiones [V o kV, coherentes], reactancias en p.u. (x = X/Z_r), Z en Ω, I en A.

LIMITACIONES
    - R_G ≪ X''d en las expresiones aproximadas.
    - x_T es la reactancia del transformador en p.u. sobre su base (u_Xr/100).
    - Para K_SO con tomas sin carga usar el signo que da mayor corriente: (1 − p_T).
    - K_T de [65] (0,95·c_max/(1+0,6x_T)) está en short_circuit.factor_kt.

NORMA DE REFERENCIA
    AEA IT 90909-1 (2005); AEA 90909-0 (IEC 60909-0).  [VERIFICAR]
"""
import math
from epc_calc._validate import num as _num

__version__ = "0.1.0"

C_MAX_RED = 1.10
RIGIDO_MAX_U_RATIO = 1.4
LIM_MOTORES_I_PCT = 5.0       # [108]
LIM_MOTORES_SUMA_IRM_PCT = 1.0  # [110]


def c_max_desde_tension(u_q_max, un):
    """[15] c_max ≈ U_Qmax/Un."""
    _num(u_q_max, "u_q_max", 0.0, True)
    _num(un, "un", 0.0, True)
    return u_q_max / un


def delta_i_kmax(delta_u_max):
    """[12] Δi''kmax = 1/(1+Δu_max) − 1 (Δu en p.u.)."""
    _num(delta_u_max, "delta_u_max")
    return 1.0 / (1.0 + delta_u_max) - 1.0


def defecto_tierra_rigido(u_le, u_ye):
    """True si U_L,E/U_Y,E ≤ 1,4 (red puesta rígidamente a tierra)."""
    _num(u_le, "u_le")
    _num(u_ye, "u_ye", 0.0, True)
    return u_le / u_ye <= RIGIDO_MAX_U_RATIO


def k_g(un, u_rg, c_max, x_d2_pu, sen_fi_rg):
    """[22] K_G."""
    for v, n in ((un, "un"), (u_rg, "u_rg"), (c_max, "c_max")):
        _num(v, n, 0.0, True)
    _num(x_d2_pu, "x_d2_pu")
    return (un / u_rg) * c_max / (1.0 + x_d2_pu * sen_fi_rg)


def k_s(un_q, u_rg, u_rtlv, u_rthv, c_max, x_d2_pu, x_t_pu, sen_fi_rg):
    """[31] K_S (grupo con conmutador bajo carga)."""
    for v, n in ((un_q, "un_q"), (u_rg, "u_rg"), (u_rtlv, "u_rtlv"), (u_rthv, "u_rthv"), (c_max, "c_max")):
        _num(v, n, 0.0, True)
    return (un_q ** 2 / u_rg ** 2) * (u_rtlv ** 2 / u_rthv ** 2) * c_max / (
        1.0 + abs(x_d2_pu - x_t_pu) * sen_fi_rg)


def k_so(un_q, u_rg, p_g, u_rtlv, u_rthv, c_max, x_d2_pu, sen_fi_rg, p_t=0.0):
    """[49a] (p_t=0) / [49b] (con (1 − p_T), el caso de mayor corriente)."""
    for v, n in ((un_q, "un_q"), (u_rg, "u_rg"), (u_rtlv, "u_rtlv"), (u_rthv, "u_rthv"), (c_max, "c_max")):
        _num(v, n, 0.0, True)
    _num(p_g, "p_g")
    _num(p_t, "p_t")
    return (un_q / (u_rg * (1.0 + p_g))) * (u_rtlv / u_rthv) * (1.0 - p_t) * c_max / (1.0 + x_d2_pu * sen_fi_rg)


def k_gs(c_max, x_d2_pu, sen_fi_rg):
    """[38]/[45a] K_G,S."""
    _num(c_max, "c_max", 0.0, True)
    return c_max / (1.0 + x_d2_pu * sen_fi_rg)


def k_ts(c_max, x_t_pu, x_d_pu=None, sen_fi_rg=None):
    """[43] con x_d (reactancia síncrona) o [45b] con senφ_rG: K_T,S."""
    _num(c_max, "c_max", 0.0, True)
    if x_d_pu is not None:
        _num(x_d_pu, "x_d_pu", 0.0, True)
        return c_max / (1.0 + x_t_pu / x_d_pu)
    if sen_fi_rg is None:
        raise ValueError("indicar x_d_pu ([43]) o sen_fi_rg ([45b])")
    return c_max / (1.0 - x_t_pu * sen_fi_rg)


def k_gso(p_g, c_max, x_d2_pu, sen_fi_rg):
    """[52] K_G,SO."""
    _num(c_max, "c_max", 0.0, True)
    return 1.0 / (1.0 + p_g) * c_max / (1.0 + x_d2_pu * sen_fi_rg)


def k_tso(c_max, u_rthv, un_q):
    """[54] K_T,SO = c_max·U_rTHV/U_nQ."""
    _num(un_q, "un_q", 0.0, True)
    return c_max * u_rthv / un_q


def k_t_general(un, u_b, c_max, x_t_pu, i_tb_sobre_irt, sen_fi_tb):
    """[62]/[63] K_T = Un/U^b·c_max/(1 + x_T·(I^b_T/I_rT)·senφ^b_T)."""
    _num(un, "un", 0.0, True)
    _num(u_b, "u_b", 0.0, True)
    return (un / u_b) * c_max / (1.0 + x_t_pu * i_tb_sobre_irt * sen_fi_tb)


def ik_generador(c, un, k_gen, z_g):
    """[19] I''kG [A] con Z_G complejo (R_G + jX''d)."""
    _num(c, "c", 0.0, True)
    _num(un, "un", 0.0, True)
    _num(k_gen, "k_gen", 0.0, True)
    return c * un / (math.sqrt(3) * abs(z_g) * k_gen)


def ik_grupo_conmutador(c, un_q, t_r, z_g, z_thv, k_sgrp):
    """[32] I''kS [A]; z_g y z_thv complejos (Ω) referidos a AT (Z_THV = t_r²·Z_TLV)."""
    _num(t_r, "t_r", 0.0, True)
    _num(k_sgrp, "k_sgrp", 0.0, True)
    return c * un_q / (math.sqrt(3) * abs(t_r ** 2 * z_g + z_thv) * k_sgrp)


def ik_trafo_con_red(c, un, z_t, k_t, z_qt):
    """[59] I''kT = c·Un/(√3·|Z_T·K_T + Z_Qt|) [A]; Z complejos."""
    _num(c, "c", 0.0, True)
    return c * un / (math.sqrt(3) * abs(z_t * k_t + z_qt))


def reactancia_trafo_ohm(u_xr_pct, u_rtlv, s_rt):
    """[60] X_T = u_Xr/100·U²_rTLV/S_rT (U [V], S [VA])."""
    _num(s_rt, "s_rt", 0.0, True)
    return u_xr_pct / 100.0 * u_rtlv ** 2 / s_rt


def reactancia_red_lv_ohm(c_q, un_q, ik_q, u_rtlv, u_rthv):
    """[61] X_Qt = c_Q·U_nQ/(√3·I''kQ)·U²_rTLV/U²_rTHV."""
    for v, n in ((un_q, "un_q"), (ik_q, "ik_q"), (u_rthv, "u_rthv")):
        _num(v, n, 0.0, True)
    return c_q * un_q / (math.sqrt(3) * ik_q) * u_rtlv ** 2 / u_rthv ** 2


def motors_contribution_negligible(ik_motores_a, ik_red_a):
    """[108] I''kM ≤ 0,05·I''kQ."""
    _num(ik_red_a, "ik_red_a", 0.0, True)
    return ik_motores_a <= LIM_MOTORES_I_PCT / 100.0 * ik_red_a


def motores_baja_tension_despreciables(suma_irm_a, ik_red_a):
    """[110] ΣI_rM ≤ 0,01·I''kQ (con I_LR/I_rM = 5)."""
    _num(ik_red_a, "ik_red_a", 0.0, True)
    return suma_irm_a <= LIM_MOTORES_SUMA_IRM_PCT / 100.0 * ik_red_a
