"""CAL-015 · aea_voltage_drop — Caída de tensión por tablas y coeficientes de AEA 771/770.

ESTADO: BORRADOR — pendiente de validación por el usuario.

OBJETIVO
    Complementar `voltage_drop.py` (fórmula general con R y X del catálogo) con los
    métodos simplificados y los LÍMITES normativos de AEA 90364-7-771 (§19.7) y
    AEA 90364-7-770 (§15.6): método de la Tabla 771.19.IV (V/A·km), método de los
    coeficientes GDC y límites por tipo de circuito. NO repite ΔU = k·I·L·(R cosφ + X senφ):
    para eso usar `voltage_drop.caida_tension`.

FÓRMULAS
    Método a) tabla: ΔU = (V/A·km)(S)·I·L[km]          (monofásico, cosφ 0,8; Tabla 771.19.IV)
    Método c) GDC:   ΔU = GDC·I·L/S                     (L [m], S [mm²]; Tabla de coeficientes GDC)
    Longitud máx.:   L = ΔU_adm·S/(GDC·I)
    Sección mín.:    S = GDC·I·L/ΔU_adm
    Carga en el extremo (iluminación): 66 % (771) o 2/3 (770) de la corriente total;
                     tomacorrientes: 100 % de la corriente.
    Límites: terminales 3 % (iluminación y tomas); motores 5 % régimen / 15 % arranque;
             seccionales ≤ 1 %.  Total = ΔU_seccional + ΔU_terminal.

HIPÓTESIS
    - cosφ 0,8 (carga común) o 0,3 (arranque); cables a 70 °C (ver nota de la norma).
    - GDC en V·mm²/(A·m) para L en metros y S en mm².

UNIDADES
    I [A], L [m], S [mm²], ΔU [V], % sobre Un.

LIMITACIONES
    - Para otros cosφ o secciones fuera de 1,5–120 mm² usar `voltage_drop.caida_tension`.
    - GDC de arranque definido para 1,5–25 mm² y 35–70 mm².

NORMA DE REFERENCIA
    AEA 90364-7-771 §19.7 (Tabla 771.19.IV); AEA 90364-7-770 §15.6.  [VERIFICAR]
"""
import math
from epc_calc._validate import num as _num

__version__ = "0.1.0"

# Tabla 771.19.IV: caída unitaria [V/(A·km)] monofásica, cosφ 0,8
VA_KM_TABLA = {1.5: 26.0, 2.5: 15.0, 4: 10.0, 6: 6.5, 10: 3.8, 16: 2.4, 25: 1.6,
               35: 1.2, 50: 0.8, 70: 0.6, 95: 0.5, 120: 0.4}

# GDC [V·mm²/(A·m)]: (material, fases, régimen) -> valor (el de arranque es (S≤25, 35≤S≤70))
GDC_COMUN = {("cu", 1): 0.040, ("cu", 3): 0.035, ("al", 1): 0.063, ("al", 3): 0.055}
GDC_ARRANQUE = {("cu", 1): (0.0160, 0.0205), ("al", 1): (0.0250, 0.0290),
                ("cu", 3): (0.0135, 0.0175), ("al", 3): (0.0215, 0.0255)}

LIMITES_PCT = {
    "iluminacion": 3.0, "tomacorrientes": 3.0,
    "motor_regimen": 5.0, "motor_arranque": 15.0,
    "seccional": 1.0,
}
FRACCION_ILUM_771 = 0.66
FRACCION_ILUM_770 = 2.0 / 3.0


def drop_unit_table(seccion_mm2):
    """V/(A·km) de la Tabla 771.19.IV (monofásico, cosφ 0,8)."""
    if seccion_mm2 not in VA_KM_TABLA:
        raise ValueError(f"sección {seccion_mm2} no está en la Tabla 771.19.IV: {sorted(VA_KM_TABLA)}")
    return VA_KM_TABLA[seccion_mm2]


def drop_by_table(i_a, longitud_m, seccion_mm2, un_v=220.0):
    """ΔU = (V/A·km)·I·L[km]. Devuelve {'delta_u_v','delta_u_pct'}."""
    _num(i_a, "i_a")
    _num(longitud_m, "longitud_m")
    _num(un_v, "un_v", 0.0, True)
    du = drop_unit_table(seccion_mm2) * i_a * longitud_m / 1000.0
    return {"delta_u_v": du, "delta_u_pct": 100.0 * du / un_v}


def coeficiente_gdc(material, fases, arranque=False, seccion_mm2=None):
    """GDC [V·mm²/(A·m)]. En arranque (cosφ 0,3) requiere seccion_mm2 (≤70)."""
    clave = (material.lower(), fases)
    if clave not in GDC_COMUN:
        raise ValueError("material 'cu'|'al' y fases 1|3")
    if not arranque:
        return GDC_COMUN[clave]
    _num(seccion_mm2, "seccion_mm2", 0.0, True)
    if seccion_mm2 > 70:
        raise ValueError("GDC de arranque definido hasta 70 mm²")
    return GDC_ARRANQUE[clave][0 if seccion_mm2 <= 25 else 1]


def caida_gdc(i_a, longitud_m, seccion_mm2, material="cu", fases=1, un_v=None, arranque=False):
    """ΔU = GDC·I·L/S. un_v por defecto 220 (mono) o 380 (tri)."""
    _num(i_a, "i_a")
    _num(longitud_m, "longitud_m")
    _num(seccion_mm2, "seccion_mm2", 0.0, True)
    g = coeficiente_gdc(material, fases, arranque, seccion_mm2)
    un = un_v if un_v is not None else (220.0 if fases == 1 else 380.0)
    du = g * i_a * longitud_m / seccion_mm2
    return {"delta_u_v": du, "delta_u_pct": 100.0 * du / un}


def longitud_maxima_gdc(i_a, seccion_mm2, du_adm_pct, material="cu", fases=1, un_v=None, arranque=False):
    """L = ΔU_adm·S/(GDC·I) [m]."""
    _num(i_a, "i_a", 0.0, True)
    _num(du_adm_pct, "du_adm_pct", 0.0, True)
    g = coeficiente_gdc(material, fases, arranque, seccion_mm2)
    un = un_v if un_v is not None else (220.0 if fases == 1 else 380.0)
    return (du_adm_pct / 100.0 * un) * seccion_mm2 / (g * i_a)


def seccion_minima_gdc(i_a, longitud_m, du_adm_pct, material="cu", fases=1, un_v=None):
    """S = GDC·I·L/ΔU_adm [mm²] (régimen, cosφ 0,8)."""
    _num(i_a, "i_a")
    _num(longitud_m, "longitud_m")
    _num(du_adm_pct, "du_adm_pct", 0.0, True)
    un = un_v if un_v is not None else (220.0 if fases == 1 else 380.0)
    return coeficiente_gdc(material, fases) * i_a * longitud_m / (du_adm_pct / 100.0 * un)


def limite_caida_pct(tipo):
    """Límite [%] por tipo: iluminacion, tomacorrientes, motor_regimen, motor_arranque, seccional."""
    if tipo not in LIMITES_PCT:
        raise ValueError(f"tipo debe ser uno de {sorted(LIMITES_PCT)}")
    return LIMITES_PCT[tipo]


def corriente_extremo(i_total_a, tipo, norma="771"):
    """Corriente equivalente concentrada en el extremo: iluminación 66 % (771) o 2/3 (770); tomas 100 %."""
    _num(i_total_a, "i_total_a")
    if tipo == "iluminacion":
        return i_total_a * (FRACCION_ILUM_770 if norma == "770" else FRACCION_ILUM_771)
    if tipo == "tomacorrientes":
        return i_total_a
    raise ValueError("tipo debe ser 'iluminacion' o 'tomacorrientes'")


def caida_disponible_terminal_pct(limite_total_pct, caida_seccional_pct):
    """Margen del circuito terminal = límite total − caída ya consumida aguas arriba (≥ 0)."""
    _num(limite_total_pct, "limite_total_pct")
    _num(caida_seccional_pct, "caida_seccional_pct")
    return max(0.0, limite_total_pct - caida_seccional_pct)


def verify_drop(caida_pct, tipo):
    """True si la caída no supera el límite del tipo."""
    _num(caida_pct, "caida_pct")
    return caida_pct <= limite_caida_pct(tipo)
