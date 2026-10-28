"""CAL-007 · hvac_airflow — Caudal de aire por carga sensible y por renovaciones; conversiones.

ESTADO: BORRADOR — pendiente de validación por el usuario.

OBJETIVO
    Calcular el caudal de aire de impulsión necesario para disipar una carga térmica sensible con
    un salto de temperatura dado, o para lograr un número de renovaciones por hora (ACH), y convertir
    caudales entre m³/h y L/s.

FÓRMULAS
    Carga sensible:       Q_s = ρ · cp · V̇ · ΔT         [kW]  (con V̇ en m³/s, ρ en kg/m³, cp en kJ/(kg·K))
    Caudal por carga:     V̇ = Q_s / (ρ · cp · ΔT)        [m³/s]  ->  ×3600 = m³/h ;  ×1000 = L/s
    Salto de temperatura: ΔT = Q_s / (ρ · cp · V̇)
    Renovaciones:         V̇ [m³/h] = n · Vol             (n [1/h], Vol [m³])
                          n = V̇ [m³/h] / Vol
    Conversiones:         L/s = (m³/h) / 3,6 ;  m³/h = (L/s) · 3,6

CONSTANTES  (aire a ~20 °C, nivel del mar)
    ρ = 1,2 kg/m³ ;  cp = 1,006 kJ/(kg·K)       [VERIFICAR]

HIPÓTESIS
    - Aire seco con propiedades constantes (sin corrección por altitud ni temperatura).
    - Solo calor sensible; la carga latente (humedad) no se considera.
    - Mezcla perfecta; sin infiltraciones ni recirculación consideradas.

UNIDADES
    Q_s [kW], ΔT [K], V̇ [m³/s] (internas) con salidas en m³/h y L/s, Vol [m³], n [1/h].

LIMITACIONES
    - No determina la carga térmica (ganancias solares, personas, equipos, iluminación): es dato.
    - No incluye caudales mínimos de aire exterior ni valores de ACH recomendados (criterio del
      proyecto / norma aplicable).
    - A altitudes elevadas o temperaturas muy distintas de 20 °C, ρ debe pasarse como parámetro.

NORMA DE REFERENCIA (por designación)
    - ASHRAE Fundamentals (ecuación de calor sensible del aire) y EN 16798-1 / ASHRAE 62.1
      para caudales de ventilación. [VERIFICAR] — sin cláusulas; ningún valor normativo está embebido.
"""

import math
from epc_aea90364._validate import nonneg as _nonneg, pos as _pos

__version__ = "0.1.0"

RHO_AIRE = 1.2    # kg/m³  [VERIFICAR]
CP_AIRE = 1.006   # kJ/(kg·K)  [VERIFICAR]


def m3h_a_ls(m3h):
    """m³/h -> L/s (÷ 3,6)."""
    _nonneg(m3h, "m3h")
    return m3h / 3.6


def ls_a_m3h(ls):
    """L/s -> m³/h (× 3,6)."""
    _nonneg(ls, "ls")
    return ls * 3.6


def caudal_por_carga_sensible_m3h(q_sensible_kw, delta_t_k, rho=RHO_AIRE, cp=CP_AIRE):
    """Caudal [m³/h] = 3600·Q_s/(ρ·cp·ΔT)."""
    _nonneg(q_sensible_kw, "q_sensible_kw")
    _pos(delta_t_k, "delta_t_k")
    _pos(rho, "rho")
    _pos(cp, "cp")
    return 3600.0 * q_sensible_kw / (rho * cp * delta_t_k)


def flow_by_load_sensible(q_sensible_kw, delta_t_k, rho=RHO_AIRE, cp=CP_AIRE):
    """Devuelve dict {m3_h, l_s, m3_s}."""
    m3h = caudal_por_carga_sensible_m3h(q_sensible_kw, delta_t_k, rho, cp)
    return {"m3_h": m3h, "l_s": m3h_a_ls(m3h), "m3_s": m3h / 3600.0}


def load_sensible_kw(caudal_m3h, delta_t_k, rho=RHO_AIRE, cp=CP_AIRE):
    """Q_s [kW] = ρ·cp·(V̇/3600)·ΔT."""
    _nonneg(caudal_m3h, "caudal_m3h")
    _nonneg(delta_t_k, "delta_t_k")
    _pos(rho, "rho")
    _pos(cp, "cp")
    return rho * cp * (caudal_m3h / 3600.0) * delta_t_k


def delta_t_por_caudal(q_sensible_kw, caudal_m3h, rho=RHO_AIRE, cp=CP_AIRE):
    """ΔT [K] = Q_s/(ρ·cp·V̇)."""
    _nonneg(q_sensible_kw, "q_sensible_kw")
    _pos(caudal_m3h, "caudal_m3h")
    _pos(rho, "rho")
    _pos(cp, "cp")
    return q_sensible_kw / (rho * cp * caudal_m3h / 3600.0)


def flow_by_renewals(volumen_m3, renov_por_hora):
    """Devuelve dict {m3_h, l_s}: V̇ = n·Vol."""
    _pos(volumen_m3, "volumen_m3")
    _pos(renov_por_hora, "renov_por_hora")
    m3h = renov_por_hora * volumen_m3
    return {"m3_h": m3h, "l_s": m3h_a_ls(m3h)}


def renovaciones_por_hora(caudal_m3h, volumen_m3):
    """n [1/h] = V̇/Vol."""
    _nonneg(caudal_m3h, "caudal_m3h")
    _pos(volumen_m3, "volumen_m3")
    return caudal_m3h / volumen_m3


if __name__ == "__main__":
    print("== CAL-007 hvac_airflow — ejemplo (valores ilustrativos) ==")
    c = flow_by_load_sensible(10.0, 10.0)
    print(f"Carga sensible 10 kW, ΔT 10 K: {c['m3_h']:.0f} m³/h = {c['l_s']:.1f} L/s")
    r = flow_by_renewals(10 * 6 * 3, 6)
    print(f"Local 10×6×3 m, 6 ren/h: {r['m3_h']:.0f} m³/h = {r['l_s']:.1f} L/s")
    print(f"Conversión: 360 m³/h = {m3h_a_ls(360):.1f} L/s ; 100 L/s = {ls_a_m3h(100):.0f} m³/h")
