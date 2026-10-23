"""CAL-024 · aea_pipeline — Entrada Excel de circuitos → cálculo AEA → JSON del cálculo.

ESTADO: BORRADOR — pendiente de validación por el usuario.

OBJETIVO
    Lee el archivo de circuitos (`src/input_for_sld_V1.xlsx`: hojas TABLERO y CIRCUITOS), dimensiona
    cada circuito con los módulos de la biblioteca y exporta UN JSON (`aea_export`) para `sld-generator`.
    No genera PDF. Solo biblioteca estándar (lector xlsx propio).

USO
    python3 -B aea_pipeline.py src/input_for_sld_V1.xlsx [-o salida_calculo.json] [--margen-iz 1.0]
                                [--eta-motores] [--temp-c 70] [--k-magnetico 10]
    Por defecto escribe `<entrada>_calculo.json` junto al xlsx y lista los avisos en pantalla.

ENTRADA
    TABLERO (CAMPO/VALOR): TENSION_V (de línea), ICC_KA, FP_DEFAULT, [FRECUENCIA_HZ, SISTEMA, NOMBRE, PROYECTO].
    CIRCUITOS: TAG, DESCRIPCION, CARGA, UNIDAD_CARGA (A, W, kW, MW, VA, kVA, MVA, HP), PARENT_TAG,
               TOPOLOGY (single, dol, dol_ol, star_delta, softstarter, vfd, dol_rcd, manual), FASE (1F/3F),
               LONGITUD_m, FP, RENDIMIENTO, KIND (mcb, mccb, rccb, rcbo, auto), NOTAS.

MÉTODO
    Ib      : A → tal cual; W/kW/MW → P/(√3·U·fp) o P/(U_f·fp); VA/kVA/MVA → S/(√3·U) o S/U_f (sin fp);
              HP → 745,7 W con rendimiento. El rendimiento se aplica solo a HP (opción --eta-motores
              para aplicarlo también a kW de motores). U_f = U/√3. Carga vacía en un padre → suma de hijos.
    In      : 1,25·Ib en circuitos con TOPOLOGY ≠ single (motores); Ib en el resto; primera serie normal ≥.
    icu     : primer valor de la serie normal ≥ ICC_KA del tablero.
    S       : mínima de la serie con (a) sección mínima 771.13.I, (b) Iz(Tabla 771.16.I, 2x mono / 3x tri) ≥ margen·In,
              (c) caída de tensión propia ≤ límite y acumulada ≤ 5 %.
    dU      : ΔU = k·I·L·(R·cosφ + X·senφ), R a 70 °C; iluminación con 66 % de la corriente en el extremo (771);
              acumulada = caída del padre + propia.
    Límites : seccionales 1 %; iluminación y tomacorrientes 3 %; motores 5 %.
    disp    : cadena de protección según TOPOLOGY (p. ej. `MCB > KM > OL (25 A)`, `RCCB 4P 63 A 30 mA`).

CRITERIOS DE DISEÑO (parámetro `criterios`)
    Un diccionario con los criterios del proyecto manda sobre los valores base: `vd_sectional_pct` (seccionales),
    `vd_lighting_sockets_pct` (iluminación y tomacorrientes), `vd_motors_pct` (motores en régimen),
    `min_section_lighting_mm2`, `min_section_sockets_mm2`, `conductor_material` (cobre|aluminio), `insulation` (XLPE|PVC)
    y `rcd_sensitivity_ma`. Las columnas MATERIAL / AISLACION / METODO de una fila siguen mandando sobre los criterios.
    Con XLPE y sin METODO se usa B2 (Tabla 771.16.III), porque B1 solo existe para PVC. `detalle` (dict) recibe, por TAG, el
    tipo de circuito, el límite aplicado y la caída propia y acumulada.

LIMITACIONES
    - icu = Icc en barras; Icc mínima al final de cada circuito solo como AVISO (disparo magnético, curva C por defecto);
      sin verificación I²t del cable (requiere la energía pasante del interruptor), selectividad, agrupamiento ni temperatura.
    - Solo cobre/PVC en cañería (Tabla 771.16.I); sobre 300 mm² exige paralelo (aviso).
    - Suma aritmética de hijos para el padre (sin simultaneidad).

NORMA DE REFERENCIA
    AEA 90364-7-771 (2006) §13, §16, §19.7; AEA 90364-7-770 (2017).  [VERIFICAR]
"""
import argparse
import math
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

from epc_calc import aea_ampacity as AMP
from epc_calc import aea_conductors as CO
from epc_calc import aea_export as EX
from epc_calc import aea_voltage_drop as VD
from epc_calc import current_and_loads as CL
from epc_calc import short_circuit as SC
from epc_calc import voltage_drop as VDG

__version__ = "0.2.0"

HP_W = 745.7
HP_CV_W = 735.49875
SERIE_IN_A = (6, 10, 13, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630,
              800, 1000, 1250, 1600)
SERIE_ICU_KA = (6, 10, 15, 20, 25, 36, 50, 70, 100)
SERIE_S_MM2 = tuple(sorted(CO.IZ_771_16_I))
IN_MAX_MCB_A = 63
MARGIN_MOTOR = 1.25
C_MAX_BT = 1.05      # AEA 90909-0, tolerancia 6 %
C_MIN_BT = 0.95
K_MAGNETICO_C = 10   # disparo magnético máximo de la curva C [× In]
DU_ACUM_MAX_PCT = 5.0
TOPOLOGIAS_MOTOR = {"dol", "dol_ol", "star_delta", "softstarter", "vfd", "dol_rcd"}
CADENAS = {  # TOPOLOGY -> (cadena con MCB, cadena con MCCB)
    "dol": ("MCB > KM", "MCCB > KM"),
    "dol_ol": ("MCB > KM > OL", "MCCB > KM > OL"),
    "star_delta": ("MCB > KM > KM > KM > OL", "MCCB > KM > KM > KM > OL"),
    "softstarter": ("MCB > SS", "MCCB > SS"),
    "vfd": ("MCB > VFD", "MCCB > VFD"),
    "dol_rcd": ("RCBO > KM", "RCBO > KM"),
}


# ---------------------------------------------------------------- lector xlsx (stdlib)
_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
       "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
       "pr": "http://schemas.openxmlformats.org/package/2006/relationships"}


def _col(ref):
    n = 0
    for ch in re.match(r"[A-Z]+", ref).group(0):
        n = n * 26 + ord(ch) - 64
    return n - 1


def leer_xlsx(ruta):
    """Devuelve {nombre_hoja: [[valores de la fila], ...]} (texto o número; None si vacío)."""
    with zipfile.ZipFile(ruta) as z:
        ss = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", _NS):
                ss.append("".join(t.text or "" for t in si.iter("{%s}t" % _NS["m"])))
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rels = {r.get("Id"): r.get("Target") for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
        hojas = {}
        for sh in wb.find("m:sheets", _NS):
            tgt = rels[sh.get("{%s}id" % _NS["r"])].lstrip("/")
            tgt = tgt if tgt.startswith("xl/") else "xl/" + tgt
            filas = []
            for row in ET.fromstring(z.read(tgt)).iter("{%s}row" % _NS["m"]):
                vals = {}
                for c in row.findall("m:c", _NS):
                    t = c.get("t")
                    v = c.find("m:v", _NS)
                    if t == "inlineStr":
                        val = "".join(x.text or "" for x in c.iter("{%s}t" % _NS["m"]))
                    elif v is None or v.text is None:
                        continue
                    elif t == "s":
                        val = ss[int(v.text)]
                    elif t in ("str", "e"):
                        val = v.text
                    elif t == "b":
                        val = bool(int(v.text))
                    else:
                        f = float(v.text)
                        val = int(f) if f == int(f) else f
                    vals[_col(c.get("r"))] = val
                if vals:
                    filas.append([vals.get(i) for i in range(max(vals) + 1)])
            hojas[sh.get("name")] = filas
    return hojas


def load_input(ruta):
    """Lee TABLERO y CIRCUITOS. Devuelve (tablero: dict, circuitos: lista de dict con claves en mayúsculas)."""
    h = leer_xlsx(ruta)
    for n in ("TABLERO", "CIRCUITOS"):
        if n not in h:
            raise ValueError(f"falta la hoja {n} en {ruta}")
    tablero = {}
    for f in h["TABLERO"]:
        if len(f) > 1 and isinstance(f[0], str) and f[1] is not None and f[0].strip().replace("_", "").isalnum() \
                and f[0].strip() not in ("CAMPO", "Campo"):
            tablero[f[0].strip()] = f[1]
    filas = h["CIRCUITOS"]
    enc = next(i for i, f in enumerate(filas) if f and f[0] == "TAG")
    cols = [str(c).strip() if c is not None else "" for c in filas[enc]]
    circuitos = []
    for f in filas[enc + 1:]:
        if not f or f[0] in (None, ""):
            continue
        d = {cols[i]: (f[i] if i < len(f) else None) for i in range(len(cols)) if cols[i]}
        d["TAG"] = str(d["TAG"]).strip()
        circuitos.append(d)
    return tablero, circuitos


# ---------------------------------------------------------------- cálculo
def _primero(serie, minimo):
    for v in serie:
        if v >= minimo - 1e-9:
            return v
    return None


def _fases(c):
    return 1 if str(c.get("FASE") or "3F").strip().upper().startswith("1") else 3


def _num_opt(v, defecto=None):
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else defecto


_UNIDADES = {"a": ("a", 1.0), "w": ("w", 1.0), "kw": ("w", 1e3), "mw": ("w", 1e6),
             "va": ("va", 1.0), "kva": ("va", 1e3), "mva": ("va", 1e6),
             "hp": ("hp", HP_W), "cv": ("hp", HP_CV_W)}


def convert_load(carga, unidad=None):
    """Normaliza la carga a (valor en la unidad base, base) con base 'a' (A), 'w' (W), 'va' (VA) o 'hp' (W mecánicos).

    Acepta número + unidad por separado (cualquier mayúscula/minúscula: kW, KW, kva, Hp) o el texto
    '15 kW' / '7,5 HP' en CARGA (coma decimal admitida). Unidades: A, W, kW, MW, VA, kVA, MVA, HP (y CV).
    HP/CV se devuelven en W mecánicos (1 HP = 745,7 W; 1 CV = 735,5 W)."""
    if isinstance(carga, str):
        m = re.fullmatch(r"\s*([0-9]+(?:[.,][0-9]+)?)\s*([A-Za-z]*)\s*", carga)
        if not m:
            raise ValueError(f"carga no interpretable: {carga!r}")
        carga, u_txt = float(m.group(1).replace(",", ".")), m.group(2)
        if unidad in (None, "") or not str(unidad).strip():
            unidad = u_txt
    if not isinstance(carga, (int, float)) or isinstance(carga, bool) or not math.isfinite(carga) or carga < 0:
        raise ValueError(f"carga debe ser un número ≥ 0 (recibido: {carga!r})")
    clave = re.sub(r"[\s.]", "", str(unidad or "")).lower()
    if not clave:
        raise ValueError("falta UNIDAD_CARGA (A, W, kW, MW, VA, kVA, MVA, HP)")
    if clave not in _UNIDADES:
        raise ValueError(f"unidad de carga no reconocida: {unidad!r} (use A, W, kW, MW, VA, kVA, MVA, HP)")
    base, factor = _UNIDADES[clave]
    return carga * factor, base


def corriente_proyecto(c, u_linea, fp_def, eta_motores=False):
    """Ib [A] del circuito desde CARGA/UNIDAD_CARGA (A, W, kW, MW, VA, kVA, MVA, HP); None si no tiene carga (padre).

    A: tal cual · W: P/(√3·U·fp) o P/(U_f·fp) · VA: S/(√3·U) o S/U_f (sin fp) ·
    HP: potencia mecánica/(√3·U·fp·η) (con η obligatorio por defecto 1)."""
    bruta = c.get("CARGA")
    if bruta is None or (isinstance(bruta, str) and not bruta.strip()):
        return None
    try:
        valor, base = convert_load(bruta, c.get("UNIDAD_CARGA"))
    except ValueError as e:
        raise ValueError(f"{c['TAG']}: {e}") from None
    fases = _fases(c)
    fp = _num_opt(c.get("FP"), fp_def)
    eta = _num_opt(c.get("RENDIMIENTO"), 1.0)
    motor = str(c.get("TOPOLOGY") or "single").strip().lower() in TOPOLOGIAS_MOTOR
    u_f = u_linea / math.sqrt(3)
    if base == "a":
        return float(valor)
    if base == "va":
        return valor / (math.sqrt(3) * u_linea) if fases == 3 else valor / u_f
    e = eta if (base == "hp" or (eta_motores and motor)) else 1.0
    return (CL.corriente_trifasica(valor, u_linea, fp, e) if fases == 3
            else CL.corriente_monofasica(valor, u_f, fp, e))


def current_sc_min(u_linea, sc_busbar_ka, r_ohm, x_ohm, fases, c_max=C_MAX_BT, c_min=C_MIN_BT):
    """Icc mínima [A] al final de un circuito, con R a temperatura de servicio.

    Z_fuente (por fase) = c_max·U_f/Icc_barras ; Z = Z_fuente + (R + jX) del cable acumulado.
    3F (bifásico): I = c_min·U/(2·|Z|) ; 1F (fase-neutro): I = c_min·U_f/(2·|Z|)."""
    u_f = u_linea / math.sqrt(3)
    zs = c_max * u_f / (sc_busbar_ka * 1e3)
    z = math.hypot(zs + r_ohm, x_ohm)
    return c_min * (u_linea if fases == 3 else u_f) / (2.0 * z)


def type_circuit(c, tiene_hijos):
    """'seccional' | 'motor' | 'iluminacion' | 'tomacorrientes' (para límites y sección mínima)."""
    top = str(c.get("TOPOLOGY") or "single").strip().lower()
    desc = str(c.get("DESCRIPCION") or "").upper()
    if tiene_hijos or any(w in desc for w in ("ALIMENTADOR", "SUBTABLERO", "TABLERO")):
        return "seccional"
    if top in TOPOLOGIAS_MOTOR:
        return "motor"
    if str(c["TAG"]).upper().startswith("L-") or "ILUM" in desc:
        return "iluminacion"
    return "tomacorrientes"


_SECCION_MIN = {"seccional": "seccional", "motor": "uso_especifico",
                "iluminacion": "iluminacion_terminal", "tomacorrientes": "tomacorrientes"}
_LIMITE = {"seccional": "seccional", "motor": "motor_regimen",
           "iluminacion": "iluminacion", "tomacorrientes": "tomacorrientes"}


def _dispositivo(c, in_a, fases, sens_ma=30):
    top = str(c.get("TOPOLOGY") or "single").strip().lower()
    kind = str(c.get("KIND") or "auto").strip().lower()
    notas = str(c.get("NOTAS") or "").lower()
    if top in CADENAS:
        cad = CADENAS[top][0 if in_a <= IN_MAX_MCB_A else 1]
        return f"{cad} ({in_a} A)"
    if kind == "rccb":
        return f"RCCB {4 if fases == 3 else 2}P {in_a} A {sens_ma:g} mA"
    if kind == "auto":
        kind = "mcb" if in_a <= IN_MAX_MCB_A else "mccb"
    nombre = {"mcb": "MCB", "mccb": "MCCB", "rcbo": "RCBO"}.get(kind, kind.upper())
    base = f"{nombre} ({in_a} A)"
    if "ups" in notas:
        return f"{nombre} > UPS ({in_a} A)"
    return base


_MATERIAL = {"cobre": "cu", "cu": "cu", "aluminio": "al", "al": "al"}


def resolver_criterios(criterios=None):
    """Criterios de diseño -> (límites ΔU [%] por tipo, secciones mínimas [mm²] por tipo, material, aislación, sensibilidad RCD [mA]).

    Sin criterios (o con claves ausentes) valen los de las tablas: 1 % seccionales, 3 % iluminación y tomacorrientes, 5 % motores."""
    cr = criterios or {}
    lim = {k: VD.limite_caida_pct(v) for k, v in _LIMITE.items()}          # claves: seccional, motor, iluminacion, tomacorrientes
    if cr.get("vd_sectional_pct") is not None:
        lim["seccional"] = float(cr["vd_sectional_pct"])
    if cr.get("vd_lighting_sockets_pct") is not None:
        lim["iluminacion"] = lim["tomacorrientes"] = float(cr["vd_lighting_sockets_pct"])
    if cr.get("vd_motors_pct") is not None:
        lim["motor"] = float(cr["vd_motors_pct"])
    smin = {k: CO.section_min_circuit(v) for k, v in _SECCION_MIN.items()}
    if cr.get("min_section_lighting_mm2") is not None:
        smin["iluminacion"] = float(cr["min_section_lighting_mm2"])
    if cr.get("min_section_sockets_mm2") is not None:
        smin["tomacorrientes"] = float(cr["min_section_sockets_mm2"])
    material = _MATERIAL.get(str(cr.get("conductor_material", "cobre")).strip().lower(), "cu")
    aislacion = str(cr.get("insulation", "PVC")).strip().lower()
    if aislacion not in AMP.AISLACIONES:
        raise ValueError(f"insulation {aislacion!r} inválida: {AMP.AISLACIONES}")
    return lim, smin, material, aislacion, float(cr.get("rcd_sensitivity_ma", 30))


def calculate(tablero, circuitos, margen_iz=1.0, eta_motores=False, temp_c=70.0, k_magnetico=K_MAGNETICO_C, criterios=None, detalle=None):
    """Dimensiona todos los circuitos. Devuelve (datos_json, avisos) con `datos_json` listo para `aea_export`."""
    limites, smin_tab, mat_def, ais_def, sens_rcd = resolver_criterios(criterios)
    u = float(tablero.get("TENSION_V", 380))
    icc = float(tablero.get("ICC_KA", 10))
    fp_def = float(tablero.get("FP_DEFAULT", 0.85))
    icu = _primero(SERIE_ICU_KA, icc)
    avisos = []
    if icu is None:
        avisos.append(f"ICC_KA {icc} supera la serie de icu {SERIE_ICU_KA[-1]} kA")
        icu = SERIE_ICU_KA[-1]
    por_tag = {c["TAG"]: c for c in circuitos}
    if len(por_tag) != len(circuitos):
        raise ValueError("TAG duplicados en CIRCUITOS")
    hijos = {t: [] for t in por_tag}
    for c in circuitos:
        p = str(c.get("PARENT_TAG") or "").strip()
        if p:
            if p not in por_tag:
                raise ValueError(f"{c['TAG']}: PARENT_TAG {p!r} no existe")
            hijos[p].append(c["TAG"])
    ib, visitando = {}, set()

    def _ib(tag):
        if tag in ib:
            return ib[tag]
        if tag in visitando:
            raise ValueError(f"ciclo en PARENT_TAG en {tag}")
        visitando.add(tag)
        v = corriente_proyecto(por_tag[tag], u, fp_def, eta_motores)
        if v is None:
            v = sum(_ib(h) for h in hijos[tag])
            if not hijos[tag]:
                raise ValueError(f"{tag}: sin CARGA y sin hijos")
        visitando.discard(tag)
        ib[tag] = v
        return v

    for t in por_tag:
        _ib(t)
    resultado, du_acum, z_acum = {}, {}, {}

    def _procesar(tag):
        c = por_tag[tag]
        fases = _fases(c)
        tipo = type_circuit(c, bool(hijos[tag]))
        top = str(c.get("TOPOLOGY") or "single").strip().lower()
        i_b = ib[tag]
        in_a = _primero(SERIE_IN_A, i_b * (MARGIN_MOTOR if top in TOPOLOGIAS_MOTOR else 1.0))
        if in_a is None:
            avisos.append(f"{tag}: Ib {i_b:.0f} A supera la serie de In")
            in_a = SERIE_IN_A[-1]
        padre = str(c.get("PARENT_TAG") or "").strip()
        base = du_acum[padre] if padre else 0.0
        largo = _num_opt(c.get("LONGITUD_m"), 0.0)
        fp = _num_opt(c.get("FP"), fp_def)
        i_du = VD.corriente_extremo(i_b, "iluminacion") if tipo == "iluminacion" else i_b
        un_du = u if fases == 3 else u / math.sqrt(3)
        limite = limites[tipo]
        smin = smin_tab[tipo]
        cc = dict(c)
        if not cc.get("MATERIAL"):
            cc["MATERIAL"] = mat_def
        if not cc.get("AISLACION"):
            cc["AISLACION"] = ais_def
        if not cc.get("METODO") and cc["AISLACION"] == "xlpe":
            cc["METODO"] = "B2"                       # B1 solo tiene tabla para PVC
        par = AMP.parametros(cc)
        t_cond = AMP.temp_conductor(par, temp_c)
        elegida, du_prop, ultimo_error, iz_ok = None, 0.0, None, None
        for s in SERIE_S_MM2:
            if s < smin:
                continue
            if not AMP.seccion_valida(par, s):
                continue
            try:
                iz_s = AMP.iz(par, s, fases)
            except ValueError as e:
                ultimo_error = str(e)
                continue
            if iz_s < margen_iz * in_a:
                continue
            du_prop = 0.0 if largo == 0 else VDG.caida_tension(
                fases, i_du, largo, AMP.resistencia_ohm_km(s, par["material"], t_cond), CO.X_CABLE_OHM_KM, fp, un_du)["delta_u_pct"]
            if du_prop <= limite and base + du_prop <= DU_ACUM_MAX_PCT:
                elegida, iz_ok = s, iz_s
                break
        if elegida is None:
            elegida = SERIE_S_MM2[-1]
            avisos.append(f"{tag}: ninguna sección ≤ {elegida} mm² cumple Iz/caída (In {in_a} A, ΔU {du_prop:.2f} %): usar paralelo"
                          + (f" [{ultimo_error}]" if ultimo_error else ""))
        du_acum[tag] = base + du_prop
        rp, xp = z_acum[padre] if padre else (0.0, 0.0)
        rc, xc = SC.impedance_cable(AMP.resistencia_ohm_km(elegida, par["material"], t_cond), CO.X_CABLE_OHM_KM, largo)
        z_acum[tag] = (rp + rc, xp + xc)
        kind = str(c.get("KIND") or "").strip().lower()
        if kind != "rccb":
            i_min = current_sc_min(u, icc, *z_acum[tag], fases)
            if i_min < k_magnetico * in_a:
                avisos.append(f"{tag}: Icc mín al final {i_min:.0f} A < {k_magnetico}·In ({k_magnetico * in_a:.0f} A): "
                              "verificar disparo magnético (curva) o acortar/ensanchar el cable")
        resultado[tag] = EX.circuito_json(in_a, i_b, icu, elegida, du_acum[tag], _dispositivo(c, in_a, fases, sens_rcd))
        if detalle is not None:
            detalle[tag] = {"tipo": tipo, "limite_pct": limite, "du_propia_pct": round(du_prop, 3), "du_acum_pct": round(du_acum[tag], 3),
                            "iz_a": iz_ok, "seccion_min_mm2": smin, "material": par["material"], "aislacion": par["aislacion"], "metodo": par["metodo"],
                            "cumple": bool(elegida is not None and iz_ok is not None and du_prop <= limite and du_acum[tag] <= DU_ACUM_MAX_PCT)}
        for h in hijos[tag]:
            _procesar(h)

    for c in circuitos:
        if not str(c.get("PARENT_TAG") or "").strip():
            _procesar(c["TAG"])
    datos = {c["TAG"]: resultado[c["TAG"]] for c in circuitos}   # orden del Excel
    avisos += EX.validate_calculation(datos)["avisos"]
    return datos, avisos


def calcular_desde_xlsx(ruta_xlsx, ruta_json=None, alimentador=None, **opc):
    """Lee el Excel, calcula, valida, escribe el JSON y la MC/SP del alimentador principal.
    Devuelve (ruta_json, datos, avisos)."""
    tablero, circuitos = load_input(ruta_xlsx)
    datos, avisos = calculate(tablero, circuitos, **opc)
    ruta_json = ruta_json or os.path.splitext(ruta_xlsx)[0] + "_calculo.json"
    avisos += EX.export_calculation(datos, ruta_json)
    from epc_calc import aea_feeder_report as AFR  # diferido: aea_feeder_report importa este módulo
    base = ruta_json[:-len("_calculo.json")] if ruta_json.endswith("_calculo.json") else os.path.splitext(ruta_json)[0]
    try:
        AFR.generar_documentos(base, tablero, circuitos, datos, tag=alimentador,
                               temp_c=opc.get("temp_c", 70.0), k_magnetico=opc.get("k_magnetico", K_MAGNETICO_C))
    except ValueError as e:
        avisos.append(f"MC y SP no generadas: {e}")
    return ruta_json, datos, avisos


def _main(argv):
    ap = argparse.ArgumentParser(description="Excel de circuitos -> JSON del cálculo")
    ap.add_argument("xlsx")
    ap.add_argument("-o", "--salida")
    ap.add_argument("--margen-iz", type=float, default=1.0)
    ap.add_argument("--eta-motores", action="store_true")
    ap.add_argument("--temp-c", type=float, default=70.0)
    ap.add_argument("--k-magnetico", type=float, default=K_MAGNETICO_C, help="disparo magnético máx. × In (C=10, B=5, D=20)")
    ap.add_argument("--alimentador", help="TAG del alimentador principal (defecto: primer circuito sin padre con KIND mccb)")
    a = ap.parse_args(argv)
    ruta, datos, avisos = calcular_desde_xlsx(a.xlsx, a.salida, alimentador=a.alimentador, margen_iz=a.margen_iz,
                                              eta_motores=a.eta_motores, temp_c=a.temp_c, k_magnetico=a.k_magnetico)
    print(f"{len(datos)} circuitos -> {ruta} (+ MC y SP del alimentador principal)")
    for v in dict.fromkeys(avisos):
        print("AVISO:", v)
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
