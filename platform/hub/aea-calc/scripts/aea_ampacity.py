"""aea_ampacity — Capacidad de conducción de un circuito según aislación, material y método de instalación.

ESTADO: BORRADOR — pendiente de validación por el usuario.

OBJETIVO
    A partir de las columnas opcionales del Excel (AISLACION, MATERIAL, METODO, CLASE,
    N_TERNAS, AGRUP_CIRCUITOS, TEMP_AMBIENTE_C, TEMP_SUELO_C, RESIST_TERMICA_KMW, IZ_A)
    obtiene Iz de las tablas 771.16 y la resistencia del conductor. Sin esas columnas se
    comporta como antes: Cu, PVC, método B1, 40 °C (Tabla 771.16.I).

FÓRMULAS
    I_z = N · I_z0 · f_clase · f_temp · f_agrup · f_suelo
    R(θ) = R20 · (1 + α·(θ − 20)) ;  α_Cu = 0,00393 ; α_Al = 0,00403
    Si IZ_A está informada, se toma como I_z0 base del cable (por terna) y solo se aplican los factores.

UNIDADES
    I [A], S [mm²], R [Ω/km], T [°C], ρ [K·m/W].

LIMITACIONES
    - Aluminio solo desde 16 mm² (AEA 771.13) y con R20 de IEC 60228 clase 2 [VERIFICAR].
    - B1 solo existe para PVC en la Tabla 771.16.I; B1 con XLPE no tiene tabla: se informa.
    - F usa la disposición trébol para 3 cargados; G, horizontal separados.
    - Más de 3 circuitos en un caño (B1/B2) se reduce con la Tabla 771.16.IV ítem 1.

NORMA DE REFERENCIA
    AEA 90364-7-771 §16 (771.16.I a VII), §13; IEC 60228.  [VERIFICAR]
"""
import aea_conductors as CO
import aea_tables as T

__version__ = "0.1.0"

AISLACIONES = ("pvc", "xlpe")
MATERIALES = ("cu", "al")
METODOS = ("B1", "B2", "C", "E", "F", "G", "D1", "D2")
SECCION_MIN_AL_MM2 = 16.0
ALFA = {"cu": CO.ALFA_CU, "al": 0.00403}
#: R20 [Ω/km], aluminio clase 2 (IEC 60228)
R20_AL_OHM_KM = {10: 3.08, 16: 1.91, 25: 1.20, 35: 0.868, 50: 0.641, 70: 0.443, 95: 0.320,
                 120: 0.253, 150: 0.206, 185: 0.164, 240: 0.125, 300: 0.100}
TEMP_CONDUCTOR_C = {"pvc": 70.0, "xlpe": 90.0}


#: Descripción legible de cada método (se usa en el Excel; también se aceptan los códigos)
METODOS_DESCRIPCION = {
    "B1": "Conductores en caño o cablecanal (embutido o a la vista)",
    "B2": "Cable multipolar en caño (embutido o a la vista)",
    "C": "Bandeja no perforada o de fondo sólido",
    "E": "Bandeja perforada o escalera - cable multipolar",
    "F": "Bandeja perforada o escalera - unipolares en contacto",
    "G": "Aire libre - unipolares separados un diámetro",
    "D1": "Caño o ducto enterrado",
    "D2": "Directamente enterrado",
}
_SINONIMOS = {"cobre": "cu", "aluminio": "al"}


def _norm(v):
    """Minúsculas, sin guiones largos ni espacios repetidos."""
    return " ".join(str(v).replace("\u2013", "-").replace("\u2014", "-").lower().split())


def _metodo(v):
    """Código de método desde el código (B1, D2...) o desde su descripción."""
    if v in (None, ""):
        return "B1"
    t = _norm(v)
    for cod, desc in METODOS_DESCRIPCION.items():
        if t == cod.lower() or t == _norm(desc):
            return cod
    raise ValueError(f"METODO {v!r} inválido: use uno de {list(METODOS_DESCRIPCION.values())}")


def _txt(v, defecto):
    s = _norm(v) if v not in (None, "") else defecto
    return _SINONIMOS.get(s, s)


def _num(v, defecto):
    try:
        return float(v) if v not in (None, "") else defecto
    except (TypeError, ValueError):
        raise ValueError(f"valor numérico inválido: {v!r}")


def parametros(c):
    """Lee las columnas de instalación de una fila de CIRCUITOS y aplica los valores por defecto."""
    p = {
        "aislacion": _txt(c.get("AISLACION"), "pvc"),
        "material": _txt(c.get("MATERIAL"), "cu"),
        "metodo": _metodo(c.get("METODO")),
        "clase": int(_num(c.get("CLASE"), 2)),
        "ternas": int(_num(c.get("N_TERNAS"), 1)),
        "agrup": int(_num(c.get("AGRUP_CIRCUITOS"), 1)),
        "t_amb": _num(c.get("TEMP_AMBIENTE_C"), 40.0),
        "t_suelo": _num(c.get("TEMP_SUELO_C"), 25.0),
        "rho": _num(c.get("RESIST_TERMICA_KMW"), 1.0),
        "iz_a": _num(c.get("IZ_A"), None),
    }
    if p["aislacion"] not in AISLACIONES:
        raise ValueError(f"AISLACION {p['aislacion']!r} inválida: {AISLACIONES}")
    if p["material"] not in MATERIALES:
        raise ValueError(f"MATERIAL {p['material']!r} inválido: {MATERIALES}")
    if p["clase"] not in (2, 5) or p["ternas"] < 1 or p["agrup"] < 1:
        raise ValueError("CLASE debe ser 2 o 5; N_TERNAS y AGRUP_CIRCUITOS ≥ 1")
    return p


def seccion_valida(p, s):
    """El aluminio exige S ≥ 16 mm² y R20 tabulada."""
    if p["material"] == "al":
        return s >= SECCION_MIN_AL_MM2 and s in R20_AL_OHM_KM
    return s in CO.R20_CU_OHM_KM


def temp_conductor(p, temp_c_defecto=70.0):
    """Temperatura de servicio: la dada, o 90 °C si es XLPE y no se fijó otra."""
    if p["aislacion"] == "xlpe" and temp_c_defecto == 70.0:
        return TEMP_CONDUCTOR_C["xlpe"]
    return temp_c_defecto


def resistencia_ohm_km(s, material, temp_c):
    """R(θ) del conductor [Ω/km]."""
    if material == "cu":
        return CO.R20_CU_OHM_KM[s] * (1.0 + ALFA["cu"] * (temp_c - 20.0))
    if s not in R20_AL_OHM_KM:
        raise ValueError(f"sección {s} sin resistencia tabulada para Al")
    return R20_AL_OHM_KM[s] * (1.0 + ALFA["al"] * (temp_c - 20.0))


def _fuente(p, cargados):
    """(tabla, grupo, columna) de 771.16 para el método de instalación."""
    m, n = p["metodo"], cargados
    if m == "B1":
        if p["aislacion"] != "pvc":
            raise ValueError("B1 con XLPE no tiene tabla en 771.16.I: use B2 o C")
        return "771.16.I", None, f"{n}x"
    if m in ("B2", "C", "E"):
        return "771.16.III", "B2CE", f"{m}_{n}x"
    if m == "F":
        return "771.16.III", "FG", "F_2x1x" if n == 2 else "F_3x1x_trebol"
    if m == "G":
        return "771.16.III", "FG", "G_3x1x_horizontal"
    if m == "D1":
        return "771.16.V", None, f"{n}x"
    return "771.16.VI", None, "c2_2x" if n == 2 else "c4_3x"


def iz_base(p, s, cargados):
    """I_z0 por terna [A]: IZ_A si se informó, si no la tabla 771.16 correspondiente."""
    if p["iz_a"] is not None:
        return p["iz_a"]
    tabla, grupo, col = _fuente(p, cargados)
    return T.iz_tabla(tabla, p["aislacion"], p["material"], s, col, grupo)


def factores(p, trifasico=True):
    """Dict con f_clase, f_temp, f_agrup y f_suelo."""
    m, n = p["metodo"], p["agrup"]
    enterrado = m in ("D1", "D2")
    f_temp = 1.0 if enterrado else T.factor_temperatura_aire(p["aislacion"], p["t_amb"])
    f_suelo = (T.factor_temperatura_suelo(p["aislacion"], p["t_suelo"]) * T.factor_resistividad(m, p["rho"])
               if enterrado else 1.0)
    if n <= 1 or m == "G":
        f_agrup = 1.0
    elif m in ("B1", "B2"):
        f_agrup = T.factor_agrupamiento_canos(n, trifasico) if n <= 3 else T.factor_agrupamiento_aire("1", n)
    elif m == "C":
        f_agrup = T.factor_agrupamiento_aire("2", n)
    elif m in ("E", "F"):
        f_agrup = T.factor_agrupamiento_aire("4", n)
    elif m == "D2":
        f_agrup = T.factor_agrupamiento_enterrado("c", n, 0)
    else:
        f_agrup = T.factor_agrupamiento_enterrado("d1", n, 0)
    return {"f_clase": 0.95 if p["clase"] == 5 else 1.0, "f_temp": f_temp, "f_agrup": f_agrup, "f_suelo": f_suelo}


def iz(p, s, fases):
    """I_z total [A] del circuito con sección s. ValueError si la combinación no está tabulada."""
    cargados = 3 if fases == 3 else 2
    f = factores(p, fases == 3)
    return T.iz_corregida(iz_base(p, s, cargados), p["ternas"], p["clase"] == 5,
                          f["f_temp"], f["f_agrup"], f["f_suelo"])
