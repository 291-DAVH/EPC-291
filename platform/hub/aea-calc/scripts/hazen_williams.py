"""CAL-006 · hazen_williams — Pérdida de carga por fricción (Hazen-Williams) en tuberías de agua.

ESTADO: BORRADOR — pendiente de validación por el usuario.

OBJETIVO
    Pérdida de presión por fricción por metro de tubería, velocidad media, y pérdida total de un
    tramo con longitud equivalente de accesorios y diferencia de cota.

FÓRMULAS (unidades prácticas SI)
    Fricción unitaria:   J = 6,05·10⁵ · Q^1,85 / (C^1,85 · d^4,87)         [bar/m]
        Q [L/min] caudal ; d [mm] diámetro interior ; C [-] coeficiente de Hazen-Williams.
        La constante 6,05·10⁵ es la forma habitual (Q en L/min, d en mm, p en bar/m). [VERIFICAR]
    Velocidad:           v = Q/60 000 / (π·(d/1000)²/4)                    [m/s]
    Pérdida por fricción total:  Δp_f = J · (L + L_eq)                      [bar]
    Presión estática:    Δp_z = ρ · g · Δz / 10⁵                            [bar]   (Δz > 0: el punto final está MÁS ALTO)
    Pérdida total:       Δp = Δp_f + Δp_z
        ρ = 1000 kg/m³ (agua) ; g = 9,80665 m/s² [VERIFICAR] ; L_eq [m] longitud equivalente
        de accesorios (dato de entrada: no se incluye tabla de accesorios).

VERIFICACIÓN INDEPENDIENTE (caso Q = 1000 L/min, d = 100 mm, C = 120)
    Forma alternativa en SI "pura" (Q en m³/s, d en m, pérdida de altura en m/m):
        h_f/L = 10,67 · Q^1,852 / (C^1,852 · d^4,8704)   [m de columna de agua por m]  [VERIFICAR]
    Cálculo manual con logaritmos decimales (Q = 1/60 m³/s = 0,016667 m³/s, d = 0,1 m):
        log Q = −1,77815 ; ×1,852 = −3,29323
        log C =  2,07918 ; ×1,852 =  3,85070
        log d = −1,00000 ; ×4,8704 = −4,87040  (entra con signo opuesto: +4,87040)
        log(h_f/L) = log 10,67 (1,02816) − 3,29323 − 3,85070 + 4,87040 = −1,24537  ->  h_f/L = 0,05686 m/m
        Δp = ρ·g·h = 1000 · 9,80665 · 0,05686 / 10⁵ = 5,576·10⁻³ bar/m
    Fórmula de este módulo (6,05·10⁵): 5,5625·10⁻³ bar/m.
    DESVIACIÓN = (5,5625 − 5,5758)/5,5758 = −0,24 % (diferencia atribuible a los exponentes
    redondeados 1,85/4,87 frente a 1,852/4,8704 y al redondeo de la constante). Es del orden
    de la incertidumbre intrínseca del coeficiente C (±10 % o más), por lo que se considera aceptable.

HIPÓTESIS
    - Agua a temperatura ambiente (~15–20 °C), flujo turbulento, tubería llena y de sección constante.
    - C constante (es dato del material y envejecimiento; no se tabula aquí).
    - Longitudes equivalentes dadas por el usuario para accesorios y válvulas.

LIMITACIONES
    - No es válida para otros fluidos ni para agua muy caliente/fría; para flujo laminar o
      diámetros pequeños (< 50 mm aprox.) la exactitud decrece. [VERIFICAR]
    - No calcula pérdidas por velocidad (energía cinética) ni presiones dinámicas de boquillas.
    - La velocidad máxima admisible es criterio del proyecto (no se incluye).

NORMA DE REFERENCIA (por designación)
    - Ecuación empírica de Hazen-Williams; su uso en protección contra incendios se encuentra en
      NFPA 13 (rociadores) [VERIFICAR] — sin cláusulas. La forma y constante provienen de memoria.
"""

import math

__version__ = "0.1.0"

#: Constante de Hazen-Williams (Q [L/min], d [mm] -> bar/m). [VERIFICAR]
CONSTANTE_HW = 6.05e5   # [VERIFICAR]
EXP_Q = 1.85            # [VERIFICAR]
EXP_D = 4.87            # [VERIFICAR]
RHO_AGUA = 1000.0       # kg/m³ (aprox.)
G = 9.80665             # m/s²  [VERIFICAR]


def _pos(valor, nombre):
    if not isinstance(valor, (int, float)) or isinstance(valor, bool) or not math.isfinite(valor):
        raise ValueError(f"{nombre} debe ser un número finito (recibido: {valor!r})")
    if valor <= 0:
        raise ValueError(f"{nombre} debe ser > 0 (recibido: {valor})")


def _nonneg(valor, nombre):
    if not isinstance(valor, (int, float)) or isinstance(valor, bool) or not math.isfinite(valor):
        raise ValueError(f"{nombre} debe ser un número finito (recibido: {valor!r})")
    if valor < 0:
        raise ValueError(f"{nombre} debe ser ≥ 0 (recibido: {valor})")


def perdida_unitaria_bar_m(q_lmin, d_mm, c):
    """J [bar/m] = 6,05e5·Q^1,85/(C^1,85·d^4,87)."""
    _nonneg(q_lmin, "q_lmin")
    _pos(d_mm, "d_mm")
    _pos(c, "c")
    return CONSTANTE_HW * q_lmin ** EXP_Q / (c ** EXP_Q * d_mm ** EXP_D)


def velocidad_m_s(q_lmin, d_mm):
    """v [m/s] = Q/A con Q en L/min y d en mm."""
    _nonneg(q_lmin, "q_lmin")
    _pos(d_mm, "d_mm")
    area_m2 = math.pi * (d_mm / 1000.0) ** 2 / 4.0
    return (q_lmin / 60000.0) / area_m2


def presion_estatica_bar(dz_m, rho=RHO_AGUA, g=G):
    """Δp_z [bar] = ρ·g·Δz/1e5 (Δz > 0 sube; Δz < 0 baja y resta pérdida)."""
    if not isinstance(dz_m, (int, float)) or isinstance(dz_m, bool) or not math.isfinite(dz_m):
        raise ValueError(f"dz_m debe ser un número finito (recibido: {dz_m!r})")
    _pos(rho, "rho")
    _pos(g, "g")
    return rho * g * dz_m / 1e5


def perdida_total(q_lmin, d_mm, c, longitud_m, l_eq_m=0.0, dz_m=0.0):
    """Pérdida de presión de un tramo.

    longitud_m: longitud real de tubería [m] (≥ 0); l_eq_m: longitud equivalente de accesorios [m] (≥ 0);
    dz_m: cota final − cota inicial [m].
    Devuelve dict: j_bar_m, velocidad_m_s, longitud_total_m, dp_friccion_bar, dp_estatica_bar, dp_total_bar.
    """
    _nonneg(longitud_m, "longitud_m")
    _nonneg(l_eq_m, "l_eq_m")
    j = perdida_unitaria_bar_m(q_lmin, d_mm, c)
    l_tot = longitud_m + l_eq_m
    dp_f = j * l_tot
    dp_z = presion_estatica_bar(dz_m)
    return {"j_bar_m": j, "velocidad_m_s": velocidad_m_s(q_lmin, d_mm), "longitud_total_m": l_tot,
            "dp_friccion_bar": dp_f, "dp_estatica_bar": dp_z, "dp_total_bar": dp_f + dp_z}


if __name__ == "__main__":
    print("== CAL-006 hazen_williams — ejemplo (valores ilustrativos) ==")
    r = perdida_total(q_lmin=1000, d_mm=100, c=120, longitud_m=100, l_eq_m=20, dz_m=10)
    print(f"J = {r['j_bar_m']:.5f} bar/m ; v = {r['velocidad_m_s']:.2f} m/s")
    print(f"Fricción ({r['longitud_total_m']:.0f} m) = {r['dp_friccion_bar']:.3f} bar ; "
          f"estática (10 m) = {r['dp_estatica_bar']:.3f} bar ; TOTAL = {r['dp_total_bar']:.3f} bar")
