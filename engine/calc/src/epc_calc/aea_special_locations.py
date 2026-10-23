"""CAL-021 · aea_special_locations — Baños (701) y alimentación de vehículos eléctricos (722).

ESTADO: BORRADOR — pendiente de validación por el usuario.

OBJETIVO
    Cálculos y criterios numéricos de AEA 90364-7-701 (Ed. 2012) y AEA 90364-7-722 (Ed. 2018).

FÓRMULAS
    701: B = μ0·i/(2π·R), μ0 = 4π·10⁻⁷ H/m, límite B ≤ 2,5·10⁻⁵ T
         Radio de la zona 2 con tabique de ancho a: r = 0,60 − a [m]
    722: factor de demanda = demanda máxima/carga instalada
         carga múltiple: ≤ 8 tomacorrientes y circuito ≥ mitad de las bocas a corriente máxima
         y ≥ 10 A
         diferencial: clase A ≤ 30 mA con detección de c.c. > 6 mA, o clase B
         IP ≥ 44 (55 en exterior según el caso)

UNIDADES
    I [A], distancia [m], B [T], ancho [m].

LIMITACIONES
    - Los requisitos IP, IRAM 2071 y de modo de carga se devuelven como constantes/avisos;
      la elección final es de proyecto.

NORMA DE REFERENCIA
    AEA 90364-7-701 (2012); AEA 90364-7-722 (2018).  [VERIFICAR]
"""
import math

__version__ = "0.1.0"

MU0 = 4.0e-7 * math.pi
B_LIM_T = 2.5e-5
RADIO_ZONA2_M = 0.60
MAX_OUTLETS_LOAD_MULTIPLE = 8
I_MIN_LOAD_MULTIPLE_TO = 10.0
IDN_DIFERENCIAL_EV_MA = 30.0
I_CC_DETECCION_MA = 6.0


def _num(v, nombre, minimo=0.0, estricto=False):
    if not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v):
        raise ValueError(f"{nombre} debe ser un número finito (recibido: {v!r})")
    if (estricto and v <= minimo) or (not estricto and v < minimo):
        raise ValueError(f"{nombre} debe ser {'>' if estricto else '≥'} {minimo} (recibido: {v})")


def induccion_conductor_t(i_a, distancia_m):
    """B = μ0·i/(2π·R) [T] a la distancia R del conductor (701)."""
    _num(i_a, "i_a")
    _num(distancia_m, "distancia_m", 0.0, True)
    return MU0 * i_a / (2 * math.pi * distancia_m)


def induccion_admisible(i_a, distancia_m):
    """True si B ≤ 2,5·10⁻⁵ T."""
    return induccion_conductor_t(i_a, distancia_m) <= B_LIM_T


def radio_zona2_con_tabique_m(ancho_tabique_m):
    """Radio de la zona 2 [m] = 0,60 − a (701)."""
    _num(ancho_tabique_m, "ancho_tabique_m")
    return max(0.0, RADIO_ZONA2_M - ancho_tabique_m)


def factor_demand(demanda_max, carga_instalada):
    """722: factor de demanda = demanda máxima/carga instalada (mismas unidades)."""
    _num(demanda_max, "demanda_max")
    _num(carga_instalada, "carga_instalada", 0.0, True)
    return demanda_max / carga_instalada


def load_multiple_complies(n_tomas, n_bocas, i_circuito_a, i_max_boca_a):
    """722: ≤ 8 tomas; circuito ≥ ½·(bocas·I_máx) y ≥ 10 A. Devuelve dict."""
    _num(n_tomas, "n_tomas", 1)
    _num(n_bocas, "n_bocas", 1)
    _num(i_circuito_a, "i_circuito_a")
    _num(i_max_boca_a, "i_max_boca_a", 0.0, True)
    r = {"tomas_ok": n_tomas <= MAX_OUTLETS_LOAD_MULTIPLE,
         "mitad_bocas_ok": i_circuito_a >= 0.5 * n_bocas * i_max_boca_a,
         "minimo_10a_ok": i_circuito_a >= I_MIN_LOAD_MULTIPLE_TO}
    r["cumple"] = all(r.values())
    return r
