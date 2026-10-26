"""CAL-014 · aea_demand — Demanda de potencia máxima simultánea (DPMS) y corrientes de proyecto.

ESTADO: BORRADOR — pendiente de validación por el usuario.

OBJETIVO
    Determinar el grado de electrificación, la DPMS de un inmueble (viviendas, oficinas,
    locales) y la corriente de proyecto I_B, con los criterios de AEA 90364-7-771 (Ed. 2006)
    y de su sucesora AEA 90364-7-770 (Ed. 2017). Incluye alimentador de motores, reducción
    por agrupamiento en paralelo y desequilibrio entre fases.

FÓRMULAS (numeración de la norma entre corchetes)
    DPMS total = DPMS(circuitos de uso general, por grado) + DPMS(cargas específicas)  [771.9 / 770.8]
    Iluminación general (771.9.1): 66 % de n·150 VA (viviendas), 100 % (oficinas/locales);
                       (770.8.I):  2/3 de n·60 VA.
    TUG: 2200 VA por circuito; TUE: 3300 VA por circuito.
    DPMS = Σ(circuitos) · coeficiente de simultaneidad (Tablas 771.9.II / 770.8.II / 771.9.III)
    I_B monofásica = DPMS/220 ; trifásica = DPMS/(√3·380)
    Desequilibrio de fases = (Imax − Imin)/Imax ≤ 30 % [770.8.3.4]
    Alimentador de motores: I ≥ 1,25·In(mayor) + Σ In(resto)·fs
    Paralelo: fs = 1 (2 y 4 cables/fase), 0,8 en otros casos y multipolares; 0,85 por radiación solar.

HIPÓTESIS
    - Tensiones nominales 220 V / 380 V (AEA 771/770).
    - El grado de electrificación se decide por superficie; la potencia de la tabla
      (kVA) se devuelve como referencia y no condiciona el grado.
    - Los coeficientes por grado (771) y por cantidad de circuitos (770) se aplican
      al conjunto de circuitos de uso general, no a los específicos (TUE).

UNIDADES
    Superficie [m²], potencia [VA], corriente [A].

LIMITACIONES
    - Edificios en propiedad horizontal: el 771.9.4.2 es transitorio; se codifica solo la Tabla 771.9.III.
    - La norma 770 define el grado solo por superficie (cubierta + 50 % semicubierta).

NORMA DE REFERENCIA
    AEA 90364-7-771 (2006) §8 (grados), §9 (DPMS), §13; AEA 90364-7-770 (2017) §7 (grados), §8 (DPMS); IEC 60364-5-52 (paralelo).  [VERIFICAR]
"""
import math
from epc_calc._validate import num as _num

__version__ = "0.1.0"

U_MONO_V = 220.0
U_TRI_V = 380.0
VA_BOCA_VIVIENDA = 150.0     # 771.9.1
VA_BOCA_770 = 60.0           # 770.8.I
VA_TUG = 2200.0
VA_TUE = 3300.0
COEF_GRADO_771 = {"minimo": 1.0, "medio": 0.9, "elevado": 0.8, "superior": 0.7}
COEF_CIRCUITS_770 = ((6, 0.6), (5, 0.7), (3, 0.8), (2, 1.0))   # (n mínimo, coeficiente)
DESEQUILIBRIO_MAX_PCT = 30.0

# (límite superior de superficie [m²], grado, DPMS de referencia [kVA])
_GRADOS_771 = {
    "vivienda": ((60, "minimo", 3.7), (130, "medio", 7.0), (200, "elevado", 11.0), (math.inf, "superior", None)),
    "oficina": ((30, "minimo", 4.5), (75, "medio", 7.8), (150, "elevado", 12.2), (math.inf, "superior", None)),
    "local": ((300, "minimo", 6.7), (2000, "medio", 10.0), (5000, "elevado", 14.5), (math.inf, "superior", None)),
}
_CONJUNTOS_771_III = ((26, 0.5, 0.4), (15.5, 0.6, 0.5), (5, 0.8, 0.6), (2, 0.9, 0.7))  # n mín; (Mín/Medio, Elev/Sup)


def grade_electrification_771(tipo, superficie_m2):
    """Grado según 771 (Tablas 771.8.I viviendas, 771.8.IV oficinas y locales, 771.8.IX otros locales). tipo: 'vivienda' | 'oficina' | 'local'.
    Devuelve {'grado', 'dpms_ref_kva'}."""
    _num(superficie_m2, "superficie_m2", 0.0, True)
    if tipo not in _GRADOS_771:
        raise ValueError(f"tipo debe ser uno de {sorted(_GRADOS_771)} (recibido: {tipo!r})")
    for limite, grado, kva in _GRADOS_771[tipo]:
        if superficie_m2 <= limite:
            return {"grado": grado, "dpms_ref_kva": kva}


def grade_electrification_770(superficie_cubierta_m2, superficie_semicubierta_m2=0.0):
    """Grado según 770 (Tabla 770.7.I): superficie = cubierta + 50 % de semicubierta; ≤60, ≤130, ≤200, >200 m²."""
    _num(superficie_cubierta_m2, "superficie_cubierta_m2")
    _num(superficie_semicubierta_m2, "superficie_semicubierta_m2")
    s = superficie_cubierta_m2 + 0.5 * superficie_semicubierta_m2
    _num(s, "superficie equivalente", 0.0, True)
    for limite, grado in ((60, "minimo"), (130, "medio"), (200, "elevado"), (math.inf, "superior")):
        if s <= limite:
            return {"grado": grado, "superficie_equivalente_m2": s}


def coef_simultaneity_771(grado):
    """Tabla 771.9.II: Mínimo 1; Medio 0,9; Elevado 0,8; Superior 0,7."""
    if grado not in COEF_GRADO_771:
        raise ValueError(f"grado debe ser uno de {sorted(COEF_GRADO_771)}")
    return COEF_GRADO_771[grado]


def coef_simultaneity_770(n_circuitos):
    """Tabla 770.8.II por cantidad mínima de circuitos: 2→1; 3→0,8; 5→0,7; 6→0,6 (1 circuito: 1,0)."""
    _num(n_circuitos, "n_circuitos", 1)
    for n_min, c in COEF_CIRCUITS_770:
        if n_circuitos >= n_min:
            return c
    return 1.0


def coef_simultaneidad_conjunto(n_unidades, grado):
    """Tabla 771.9.III para conjuntos de viviendas/locales: columna Mín/Medio o Elev/Sup."""
    _num(n_unidades, "n_unidades", 2)
    if grado not in COEF_GRADO_771:
        raise ValueError(f"grado debe ser uno de {sorted(COEF_GRADO_771)}")
    alto = grado in ("elevado", "superior")
    for n_min, bajo, hi in _CONJUNTOS_771_III:
        if n_unidades >= n_min:
            return hi if alto else bajo


def msd_lighting_general(n_bocas, norma="771", tipo="vivienda"):
    """771: 66 % de n·150 VA (vivienda) o 100 % (oficina/local); 770: 2/3 de n·60 VA."""
    _num(n_bocas, "n_bocas")
    if norma == "770":
        return n_bocas * VA_BOCA_770 * 2.0 / 3.0
    if norma != "771":
        raise ValueError("norma debe ser '771' o '770'")
    return n_bocas * VA_BOCA_VIVIENDA * (0.66 if tipo == "vivienda" else 1.0)


def msd_circuits(n_tug=0, n_tue=0, n_ilum_con_tomas=0):
    """Σ VA de circuitos: TUG y alumbrado con tomas derivadas 2200 VA c/u; TUE 3300 VA c/u."""
    for v, n in ((n_tug, "n_tug"), (n_tue, "n_tue"), (n_ilum_con_tomas, "n_ilum_con_tomas")):
        _num(v, n)
    return (n_tug + n_ilum_con_tomas) * VA_TUG + n_tue * VA_TUE


def dpms_total(p_generales_va, coef, p_especificas_va=0.0):
    """DPMS = Σ(uso general)·coef + Σ(cargas específicas)."""
    _num(p_generales_va, "p_generales_va")
    _num(p_especificas_va, "p_especificas_va")
    _num(coef, "coef", 0.0, True)
    return p_generales_va * coef + p_especificas_va


def current_msd(dpms_va, fases):
    """I_B = DPMS/220 (mono) o DPMS/(√3·380) (tri)."""
    _num(dpms_va, "dpms_va")
    if fases == 1:
        return dpms_va / U_MONO_V
    if fases == 3:
        return dpms_va / (math.sqrt(3) * U_TRI_V)
    raise ValueError("fases debe ser 1 o 3")


def requiere_trifasico(dpms_va, i_a=None):
    """Trifásico recomendado si DPMS > 7 kVA o I > 32 A."""
    return dpms_va > 7000.0 or (i_a is not None and i_a > 32.0)


def imbalance_phases(currents_to):
    """(Imax − Imin)/Imax en %; cumple si ≤ 30 % (770.8.3.4)."""
    if len(currents_to) < 2:
        raise ValueError("se requieren al menos 2 corrientes")
    for i in currents_to:
        _num(i, "corriente")
    mx, mn = max(currents_to), min(currents_to)
    pct = 0.0 if mx == 0 else 100.0 * (mx - mn) / mx
    return {"desequilibrio_pct": pct, "cumple": pct <= DESEQUILIBRIO_MAX_PCT}


def corriente_alimentador_motores(in_motores_a, fs_resto=1.0):
    """I ≥ 1,25·In(mayor) + Σ In(resto)·fs."""
    if not in_motores_a:
        raise ValueError("in_motores_a vacío")
    for i in in_motores_a:
        _num(i, "In motor", 0.0, True)
    _num(fs_resto, "fs_resto", 0.0, True)
    lista = sorted(in_motores_a, reverse=True)
    return 1.25 * lista[0] + sum(lista[1:]) * fs_resto


def factor_parallel(cables_por_fase, multipolar=False, radiacion_solar=False):
    """fs = 1 con 2 o 4 cables/fase (unipolares), 0,8 en otros casos y en multipolares; ×0,85 con radiación solar."""
    _num(cables_por_fase, "cables_por_fase", 1)
    if cables_por_fase == 1:
        fs = 1.0
    else:
        fs = 1.0 if (cables_por_fase in (2, 4) and not multipolar) else 0.8
    return fs * (0.85 if radiacion_solar else 1.0)
