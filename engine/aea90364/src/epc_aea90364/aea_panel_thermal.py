"""CAL-018 · aea_panel_thermal — Verificación térmica de tableros (770 Anexo B / 771 H).

ESTADO: BORRADOR — pendiente de validación por el usuario.

OBJETIVO
    Factores de simultaneidad de tablero y potencia disipada por aparatos para comprobar
    que la potencia total disipada no excede la admisible de la envolvente.

FÓRMULAS
    I_nq = I_ne·K_e  (K_e = 0,85)
    K por cantidad de circuitos (Tabla 770-B.XII): 2–3→0,8; 4–5→0,7; 6–9→0,6; ≥10→0,5
    K_nivel = I_nu_cabecera·K_padre/ΣI_nu_hijos
    P_dp = K_e²·P_d(entrada) + Σ K²·P_d(salidas)
    P_tot = P_dp + 0,2·P_dp + P_au ≤ P_de
    P_d por polo (Tabla 770-B.XI) [W/polo]: In≤10→3; ≤16→3,5; ≤25→4,5; ≤32→6;
                                            ≤40→7,5; ≤50→9; ≤63→13; ≤100→15; ≤125→20
    Poder de corte mínimo de diferenciales (770-B.X): 25 A→500; 40 A→500; 63 A→630; 80 A→800; 100 A→1000

UNIDADES
    I [A], P [W].

LIMITACIONES
    - Cálculo de verificación simplificada; no sustituye el ensayo de la envolvente.
    - P_d(salida) se evalúa con la corriente de cada salida, no con In del aparato.

NORMA DE REFERENCIA
    AEA 90364-7-770 Anexo B; AEA 90364-7-771 §20.4.2 / Anexo H.3.  [VERIFICAR]
"""
import math
from epc_aea90364._validate import num as _num

__version__ = "0.1.0"

K_E = 0.85
K_CABLEADO = 0.2            # +20 % por conexiones y cableado
_K_CIRCUITOS = ((10, 0.5), (6, 0.6), (4, 0.7), (2, 0.8))
_PD_POLO = ((10, 3.0), (16, 3.5), (25, 4.5), (32, 6.0), (40, 7.5), (50, 9.0), (63, 13.0), (100, 15.0), (125, 20.0))
_PDC_DIF = ((25, 500), (40, 500), (63, 630), (80, 800), (100, 1000))


def current_nominal_equivalent(i_ne_a, ke=K_E):
    """I_nq = I_ne·K_e."""
    _num(i_ne_a, "i_ne_a")
    _num(ke, "ke", 0.0, True)
    return i_ne_a * ke


def factor_k_circuitos(n_circuitos):
    """Tabla 770-B.XII."""
    _num(n_circuitos, "n_circuitos", 2)
    for n_min, k in _K_CIRCUITOS:
        if n_circuitos >= n_min:
            return k


def factor_k_nivel(i_nu_cabecera_a, k_padre, i_nu_hijos_a):
    """K_nivel = I_nu_cabecera·K_padre/ΣI_nu_hijos."""
    _num(i_nu_cabecera_a, "i_nu_cabecera_a")
    _num(k_padre, "k_padre", 0.0, True)
    suma = sum(i_nu_hijos_a)
    _num(suma, "ΣI_nu_hijos", 0.0, True)
    return i_nu_cabecera_a * k_padre / suma


def potencia_disipada_polo_w(i_n_a):
    """Tabla 770-B.XI [W/polo]."""
    _num(i_n_a, "i_n_a", 0.0, True)
    for lim, p in _PD_POLO:
        if i_n_a <= lim:
            return p
    raise ValueError("In > 125 A: usar dato del fabricante")


def potencia_disipada_aparato_w(i_n_a, polos, k=1.0):
    """P_d = K²·(W/polo)·polos."""
    _num(polos, "polos", 1)
    _num(k, "k", 0.0, True)
    return k ** 2 * potencia_disipada_polo_w(i_n_a) * polos


def potencia_tablero_w(p_dp_w, p_aparatos_aux_w=0.0):
    """P_tot = P_dp + 0,2·P_dp + P_au."""
    _num(p_dp_w, "p_dp_w")
    _num(p_aparatos_aux_w, "p_aparatos_aux_w")
    return p_dp_w * (1.0 + K_CABLEADO) + p_aparatos_aux_w


def verify_panel(p_tot_w, p_admisible_w):
    """P_tot ≤ P_de."""
    _num(p_tot_w, "p_tot_w")
    _num(p_admisible_w, "p_admisible_w", 0.0, True)
    return p_tot_w <= p_admisible_w


def poder_corte_minimo_diferencial_a(i_n_a):
    """Tabla 770-B.X (2P y 4P): 25/40 A→500; 63 A→630; 80 A→800; 100 A→1000."""
    _num(i_n_a, "i_n_a", 0.0, True)
    for lim, pdc in _PDC_DIF:
        if i_n_a <= lim:
            return pdc
    raise ValueError("In > 100 A fuera de la Tabla 770-B.X")
