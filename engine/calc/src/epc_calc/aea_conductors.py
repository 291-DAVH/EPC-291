"""CAL-017 · aea_conductors — Secciones mínimas, sobrecarga, armónicos y paralelo de conductores.

ESTADO: BORRADOR — pendiente de validación por el usuario.

OBJETIVO
    Criterios de AEA 90364-7-771/770 para conductores que NO están en `cable_thermal.py`:
    secciones mínimas (Tabla 771.13.I), tabla k completa (Tabla 771.19.II), coordinación
    de la protección contra sobrecarga, factores por armónicos (Tabla 771.16.XIII),
    corriente de neutro y volumen de material combustible.
    La verificación térmica ante cortocircuito se hace con `cable_thermal`
    (S ≥ I√t/k; k²S²≥I²t); aquí solo se aporta la tabla k ampliada.

FÓRMULAS
    Sobrecarga:     I_B ≤ I_n ≤ I_Z ;  I_2 ≤ 1,45·I_Z
    Poder de corte: PdC ≥ I''k
    THD = 100·√(Σ_{n≥2} h_n²)/h_ef ; h_ef = √(Σ_{n≥1} h_n²)
    D   = 100·√(Σ_{n≥2} h_n²)/h_1 ; D² = THD²/(1−THD²) ; THD² = D²/(1+D²)  (THD, D en p.u.)
    I_N = 3·I_f·(h_3/100)  (neutro con terceras armónicas) ; I' = I/f_arm
    Tabla 771.16.XIII: THD ≤15 %→1,00 (línea); 15–33 %→0,86 (línea); 33–45 %→0,86 (neutro); >45 %→1,00 (neutro)
    I_f = P/(√3·U·cosφ)
    Volumen combustible [dm³/m] = π·De²/4000 − ΣS/1000  (De [mm], S [mm²])

UNIDADES
    I [A], S [mm²], De [mm], h_n [% o p.u. según se indique].

LIMITACIONES
    - El factor armónico depende de la tabla de la norma por rangos de THD de 3.º armónica.
    - Sin cálculo de ampacidad (I_Z) desde la instalación: I_Z viene de las tablas del cable.

NORMA DE REFERENCIA
    AEA 90364-7-771 §13, §16, §19, Anexo H; AEA 90364-7-770 §11.  [VERIFICAR]
"""
import math

__version__ = "0.1.0"

K_MAX_I2_IZ = 1.45

# Tabla 771.13.I — secciones mínimas [mm²] (cobre)
SECCIONES_MIN_MM2 = {
    "linea_principal": 4.0, "seccional": 2.5, "iluminacion_terminal": 1.5,
    "tomacorrientes": 2.5, "iluminacion_con_tomas": 2.5, "uso_especial": 2.5,
    "uso_especifico": 2.5, "uso_especifico_mbtf": 1.5, "efecto_retorno": 1.5, "pe": 2.5,
}
PEN_MIN_MM2 = {"cu": 10.0, "al": 16.0}

# Tabla 771.19.II — k [A·s^½/mm²]
K_TABLA_771 = {
    ("pvc_hasta_300", "cu"): 115.0, ("pvc_hasta_300", "al"): 76.0,
    ("pvc_sobre_300", "cu"): 103.0, ("pvc_sobre_300", "al"): 68.0,
    ("epr_xlpe", "cu"): 143.0, ("epr_xlpe", "al"): 94.0,
    ("goma_60", "cu"): 141.0, ("goma_60", "al"): 93.0,
    ("mineral_pvc", "cu"): 115.0,
    ("mineral_desnudo", "cu"): 135.0, ("mineral_desnudo_expuesto", "cu"): 115.0,
    ("mineral_desnudo", "al"): 93.0,
    ("union_estanada", "cu"): 115.0,
}

# Tabla 771.16.I — corriente admisible [A], Cu, PVC, 40 °C, método B1 (cañería): {S: (2x, 3x)}
IZ_771_16_I = {
    1.5: (15, 14), 2.5: (21, 18), 4: (28, 25), 6: (36, 32), 10: (50, 44), 16: (66, 59),
    25: (88, 77), 35: (109, 96), 50: (131, 117), 70: (167, 149), 95: (202, 180),
    120: (234, 208), 150: (261, 228), 185: (297, 258), 240: (348, 301), 300: (398, 343),
}
# Resistencia de conductores de cobre a 20 °C [Ω/km] (IEC 60228, clase 2) — fuera de las normas AEA adjuntas
R20_CU_OHM_KM = {
    1.5: 12.1, 2.5: 7.41, 4: 4.61, 6: 3.08, 10: 1.83, 16: 1.15, 25: 0.727, 35: 0.524, 50: 0.387,
    70: 0.268, 95: 0.193, 120: 0.153, 150: 0.124, 185: 0.0991, 240: 0.0754, 300: 0.0601,
}
ALFA_CU = 0.00393          # coeficiente de temperatura del cobre [1/°C]
X_CABLE_OHM_KM = 0.08      # reactancia típica de cable en cañería [Ω/km]  [VERIFICAR]

# Tabla 771.16.XIII: (THD máx [%], factor, aplicado a)
FACTORS_HARMONICS = ((15.0, 1.00, "linea"), (33.0, 0.86, "linea"), (45.0, 0.86, "neutro"), (math.inf, 1.00, "neutro"))


def _num(v, nombre, minimo=0.0, estricto=False):
    if not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v):
        raise ValueError(f"{nombre} debe ser un número finito (recibido: {v!r})")
    if (estricto and v <= minimo) or (not estricto and v < minimo):
        raise ValueError(f"{nombre} debe ser {'>' if estricto else '≥'} {minimo} (recibido: {v})")


def section_min_circuit(tipo):
    """Tabla 771.13.I [mm²]."""
    if tipo not in SECCIONES_MIN_MM2:
        raise ValueError(f"tipo debe ser uno de {sorted(SECCIONES_MIN_MM2)}")
    return SECCIONES_MIN_MM2[tipo]


def iz_admisible(seccion_mm2, cargados=3):
    """Tabla 771.16.I [A]: Cu/PVC, 40 °C, método B1. cargados = 2 (monofásico) o 3 (trifásico)."""
    if seccion_mm2 not in IZ_771_16_I:
        raise ValueError(f"sección {seccion_mm2} fuera de la Tabla 771.16.I: {sorted(IZ_771_16_I)}")
    if cargados not in (2, 3):
        raise ValueError("cargados debe ser 2 o 3")
    return IZ_771_16_I[seccion_mm2][0 if cargados == 2 else 1]


def resistencia_cu_ohm_km(seccion_mm2, temp_c=70.0):
    """R(θ) = R20·(1 + 0,00393·(θ − 20)) [Ω/km]; 70 °C = temperatura máxima del PVC en servicio."""
    if seccion_mm2 not in R20_CU_OHM_KM:
        raise ValueError(f"sección {seccion_mm2} sin resistencia tabulada")
    return R20_CU_OHM_KM[seccion_mm2] * (1.0 + ALFA_CU * (temp_c - 20.0))


def k_adiabatico_771(aislacion, material):
    """Tabla 771.19.II."""
    clave = (aislacion, material.lower())
    if clave not in K_TABLA_771:
        raise ValueError(f"sin valor k para {clave}")
    return K_TABLA_771[clave]


def seccion_pen_minima_mm2(material):
    """PEN ≥ 10 mm² Cu / 16 mm² Al."""
    return PEN_MIN_MM2[material.lower()]


def verify_overload(i_b_a, i_n_a, i_z_a, i_2_a=None):
    """I_B ≤ I_n ≤ I_Z y, si se da I_2, I_2 ≤ 1,45·I_Z. Devuelve dict de comprobaciones."""
    for v, n in ((i_b_a, "i_b_a"), (i_n_a, "i_n_a"), (i_z_a, "i_z_a")):
        _num(v, n, 0.0, True)
    r = {"ib_le_in": i_b_a <= i_n_a, "in_le_iz": i_n_a <= i_z_a}
    if i_2_a is not None:
        _num(i_2_a, "i_2_a", 0.0, True)
        r["i2_le_1_45_iz"] = i_2_a <= K_MAX_I2_IZ * i_z_a
    r["cumple"] = all(r.values())
    return r


def verifica_poder_corte(pdc_a, i_k_a):
    """PdC ≥ I''k."""
    _num(pdc_a, "pdc_a", 0.0, True)
    _num(i_k_a, "i_k_a")
    return pdc_a >= i_k_a


def thd_pct(armonicos):
    """THD [%] respecto del valor eficaz. armonicos = {n: h_n} (n=1 fundamental, cualquier unidad común)."""
    if 1 not in armonicos:
        raise ValueError("falta la fundamental (n=1)")
    sup = sum(h ** 2 for n, h in armonicos.items() if n >= 2)
    h_ef = math.sqrt(sum(h ** 2 for h in armonicos.values()))
    _num(h_ef, "h_ef", 0.0, True)
    return 100.0 * math.sqrt(sup) / h_ef


def distorsion_d_pct(armonicos):
    """D [%] respecto de la fundamental."""
    if 1 not in armonicos:
        raise ValueError("falta la fundamental (n=1)")
    _num(armonicos[1], "h1", 0.0, True)
    return 100.0 * math.sqrt(sum(h ** 2 for n, h in armonicos.items() if n >= 2)) / armonicos[1]


def thd_desde_d(d_pu):
    """THD² = D²/(1+D²) (p.u.)."""
    _num(d_pu, "d_pu")
    return d_pu / math.sqrt(1.0 + d_pu ** 2)


def d_desde_thd(thd_pu):
    """D² = THD²/(1−THD²) (p.u.)."""
    _num(thd_pu, "thd_pu")
    if thd_pu >= 1:
        raise ValueError("THD debe ser < 1 p.u.")
    return thd_pu / math.sqrt(1.0 - thd_pu ** 2)


def factor_harmonics(thd3_pct):
    """Tabla 771.16.XIII: devuelve {'factor','aplicado_a'} según el THD (3.º armónica) [%]."""
    _num(thd3_pct, "thd3_pct")
    for lim, f, donde in FACTORS_HARMONICS:
        if thd3_pct <= lim:
            return {"factor": f, "aplicado_a": donde}


def current_neutral_harmonics(i_fase_a, h3_pct):
    """I_N = 3·I_f·h3/100."""
    _num(i_fase_a, "i_fase_a")
    _num(h3_pct, "h3_pct")
    return 3.0 * i_fase_a * h3_pct / 100.0


def current_corrected(i_a, factor):
    """I' = I/factor (corriente a considerar para elegir el cable)."""
    _num(i_a, "i_a")
    _num(factor, "factor", 0.0, True)
    return i_a / factor


def current_phase_three_phase(p_w, u_v, cos_fi):
    """I_f = P/(√3·U·cosφ)."""
    _num(p_w, "p_w")
    _num(u_v, "u_v", 0.0, True)
    _num(cos_fi, "cos_fi", 0.0, True)
    return p_w / (math.sqrt(3) * u_v * cos_fi)


def volumen_combustible_dm3_m(diametro_ext_mm, secciones_conductores_mm2):
    """V = π·De²/4000 − ΣS/1000 [dm³/m]."""
    _num(diametro_ext_mm, "diametro_ext_mm", 0.0, True)
    for s in secciones_conductores_mm2:
        _num(s, "S", 0.0, True)
    return math.pi * diametro_ext_mm ** 2 / 4000.0 - sum(secciones_conductores_mm2) / 1000.0
