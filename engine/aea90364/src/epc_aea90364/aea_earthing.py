"""CAL-016 · aea_earthing — Puesta a tierra, protección diferencial (TT) y electrodos.

ESTADO: BORRADOR — pendiente de validación por el usuario.

OBJETIVO
    Resistencia de puesta a tierra admisible para esquema TT (Tabla 771.3.I), tiempos máximos
    de desconexión (Tabla 771.18.I) y resistencia de electrodos (jabalina, conductor horizontal,
    placa circular, 771-C.10).

FÓRMULAS
    Ra ≤ UL/IΔn  (UL = 50 V col. 1; 24 V col. 2); adoptado: min(0,5·24/IΔn, 40 Ω)
    Jabalina:     R = ρ/(2πL)·(ln(8L/d) − 1)
                  simplificada: 0,75ρ/L (25≤L/d≤100); ρ/L (100<L/d≤600); 1,2ρ/L (600<L/d≤3000)
    Horizontal:   R = ρ/(2πL)·(ln(4L/d) + ln(L/h) − 2 + 2h/L − h²/L² + h⁴/(2L⁴))
                  simplificada: 2ρ/L
    Placa:        R = ρ/(2D)·(1/2 + D/(4πh) + 7D³/(384h³) + 99D⁵/(81920h⁵))
    Conductor PE (Tabla 771-C.II): S≤16 → S; 16<S≤35 → 16; S>35 → S/2; otro material ×k1/k2

UNIDADES
    ρ [Ω·m], L, d, h, D [m], R [Ω], IΔn [A].

LIMITACIONES
    - Las series de la placa y del conductor horizontal se truncan en los términos citados.
    - Ra máximo permanente 40 Ω; electrodos a ≥ 10 radios equivalentes entre sí.

NORMA DE REFERENCIA
    AEA 90364-7-771 §3, §18, Anexo C.10 y C.II.  [VERIFICAR]
"""
import math
from epc_aea90364._validate import num as _num

__version__ = "0.1.0"

UL_V = 24.0
UL_COL1_V = 50.0
RA_MAX_OHM = 40.0

# Tabla 771.18.I: (Un máx [V], ca TN, cc TN, ca TT, cc TT) — [s]; 50–120 V ca/cc; >120–230; >230–400
TIEMPOS_DESCONEXION_S = {
    "TN": ((120, 0.4, None), (230, 0.2, 5.0), (400, 0.06, 0.2)),
    "TT": ((120, 0.2, None), (230, 0.06, 0.2), (400, 0.01, 0.02)),
}
T_SECCIONAL_S = {"TT": 1.0, "TN": 5.0}


def ra_maxima(i_dn_a):
    """Tabla 771.3.I: {'col1_50v','col2_24v','adoptada'} [Ω]."""
    _num(i_dn_a, "i_dn_a", 0.0, True)
    c2 = UL_V / i_dn_a
    return {"col1_50v": UL_COL1_V / i_dn_a, "col2_24v": c2, "adoptada": min(0.5 * c2, RA_MAX_OHM)}


def verifica_ra(ra_ohm, i_dn_a):
    """True si Ra ≤ valor adoptado."""
    _num(ra_ohm, "ra_ohm")
    return ra_ohm <= ra_maxima(i_dn_a)["adoptada"]


def tiempo_desconexion_max_s(esquema, un_v, corriente="ca"):
    """Tabla 771.18.I. esquema 'TN'|'TT'; un_v entre 50 y 400; corriente 'ca'|'cc'."""
    if esquema not in TIEMPOS_DESCONEXION_S:
        raise ValueError("esquema 'TN' o 'TT'")
    _num(un_v, "un_v", 50.0)
    for lim, t_ca, t_cc in TIEMPOS_DESCONEXION_S[esquema]:
        if un_v <= lim:
            if corriente == "ca":
                return t_ca
            if corriente == "cc":
                if t_cc is None:
                    raise ValueError("sin valor cc en ese rango")
                return t_cc
            raise ValueError("corriente 'ca' o 'cc'")
    raise ValueError("un_v fuera de la tabla (≤ 400 V)")


def tiempo_seccional_max_s(esquema):
    """Circuitos seccionales: TT ≤ 1 s, TN ≤ 5 s."""
    return T_SECCIONAL_S[esquema]


def resistance_rod(rho, largo_m, diametro_m, simplificada=False):
    """R de una jabalina vertical [Ω]. Simplificada: 0,75/1,0/1,2 ·ρ/L según L/d."""
    for v, n in ((rho, "rho"), (largo_m, "largo_m"), (diametro_m, "diametro_m")):
        _num(v, n, 0.0, True)
    if simplificada:
        r = largo_m / diametro_m
        if r < 25 or r > 3000:
            raise ValueError("L/d fuera de 25–3000")
        k = 0.75 if r <= 100 else (1.0 if r <= 600 else 1.2)
        return k * rho / largo_m
    return rho / (2 * math.pi * largo_m) * (math.log(8 * largo_m / diametro_m) - 1)


def resistance_conductor_horizontal(rho, largo_m, diametro_m, prof_m, simplificada=False):
    """R de un conductor desnudo enterrado horizontalmente [Ω]."""
    for v, n in ((rho, "rho"), (largo_m, "largo_m"), (diametro_m, "diametro_m"), (prof_m, "prof_m")):
        _num(v, n, 0.0, True)
    if simplificada:
        return 2 * rho / largo_m
    L, h = largo_m, prof_m
    return rho / (2 * math.pi * L) * (math.log(4 * L / diametro_m) + math.log(L / h) - 2
                                      + 2 * h / L - (h / L) ** 2 + h ** 4 / (2 * L ** 4))


def resistencia_placa_circular(rho, diametro_m, prof_m):
    """R de una placa circular de diámetro D a profundidad h [Ω]."""
    for v, n in ((rho, "rho"), (diametro_m, "diametro_m"), (prof_m, "prof_m")):
        _num(v, n, 0.0, True)
    D, h = diametro_m, prof_m
    return rho / (2 * D) * (0.5 + D / (4 * math.pi * h) + 7 * D ** 3 / (384 * h ** 3)
                            + 99 * D ** 5 / (81920 * h ** 5))


def resistance_parallel(resistencias_ohm):
    """Electrodos suficientemente separados: 1/R = Σ 1/Ri."""
    if not resistencias_ohm:
        raise ValueError("lista vacía")
    for r in resistencias_ohm:
        _num(r, "R", 0.0, True)
    return 1.0 / sum(1.0 / r for r in resistencias_ohm)


def seccion_pe_mm2(s_fase_mm2, k_fase=1.0, k_pe=1.0):
    """Tabla 771-C.II; con material distinto multiplicar por k_fase/k_pe."""
    _num(s_fase_mm2, "s_fase_mm2", 0.0, True)
    _num(k_fase, "k_fase", 0.0, True)
    _num(k_pe, "k_pe", 0.0, True)
    if s_fase_mm2 <= 16:
        s = s_fase_mm2
    elif s_fase_mm2 <= 35:
        s = 16.0
    else:
        s = s_fase_mm2 / 2.0
    return s * k_fase / k_pe
