"""Memoria de Cálculo (MC) y Síntesis de Proyecto (SP) del alimentador principal del tablero.

Formato según la skill aea90364-feeder-sizing: etapas 1 a 5 en la MC y tabla requisito | dato
técnico con máximo tres observaciones en la SP. Solo se documenta el alimentador principal;
el resto de los circuitos queda en el JSON. Salida en Markdown (sin PDF).
Formato numérico: 1 decimal en tensiones y porcentajes; 2 cifras significativas en corrientes.
Dato faltante: "Pendiente".
"""
import math
import os

from epc_calc import aea_ampacity as AMP
from epc_calc import aea_conductors as CO
from epc_calc import aea_pipeline as P
from epc_calc import aea_voltage_drop as VD
from epc_calc import short_circuit as SC
from epc_calc import voltage_drop as VDG

NORMA_MARCO = (
    "AEA 90364-7-771 (ed. 2006): instalaciones en viviendas y similares",
    "AEA 90364-7-770 (ed. 2017): instalaciones en edificios",
    "AEA 90364-7-701 y 90364-7-722: locales de baño y alimentación de vehículos eléctricos",
    "AEA 90909-1: cálculo de cortocircuito",
    "IEC 60364: referencia de instalaciones de baja tensión",
)


def _p1(x):
    return f"{x:.1f}".replace(".", ",")


def _sig2(x):
    if not x:
        return "0"
    d = 1 - int(math.floor(math.log10(abs(x))))
    v = round(x, d)
    return (f"{v:.0f}" if d <= 0 else f"{v:.{d}f}").replace(".", ",")


def _mm(x):
    """Sección en mm² con su valor exacto (sin redondeo)."""
    return f"{x:g}".replace(".", ",")


def _cumple(ok):
    return "CUMPLE" if ok else "NO CUMPLE"


def alimentador_principal(circuitos, tag=None):
    """Alimentador principal: el TAG indicado, o el primer circuito sin PARENT_TAG y con KIND 'mccb'."""
    if tag:
        for c in circuitos:
            if c["TAG"] == tag:
                return c
        raise ValueError(f"alimentador {tag!r} no existe en CIRCUITOS")
    for c in circuitos:
        sin_padre = not str(c.get("PARENT_TAG") or "").strip()
        if sin_padre and str(c.get("KIND") or "").strip().lower() == "mccb":
            return c
    raise ValueError("no hay alimentador principal: se requiere un circuito sin PARENT_TAG y con KIND 'mccb'")


def verificaciones(tablero, c, reg, temp_c=70.0, k_magnetico=P.K_MAGNETICO_C):
    """Magnitudes intermedias del alimentador, con las mismas reglas que aea_pipeline."""
    u = float(tablero.get("TENSION_V", 380))
    icc = float(tablero.get("ICC_KA", 10))
    fp_def = float(tablero.get("FP_DEFAULT", 0.85))
    fases = P._fases(c)
    ib = P.corriente_proyecto(c, u, fp_def)
    fp = P._num_opt(c.get("FP"), fp_def)
    largo = P._num_opt(c.get("LONGITUD_m"), 0.0)
    s = reg["S"]
    par = AMP.parametros(c)
    t_cond = AMP.temp_conductor(par, temp_c)
    r = AMP.resistencia_ohm_km(s, par["material"], t_cond)
    x = CO.X_CABLE_OHM_KM
    un = u if fases == 3 else u / math.sqrt(3)
    du = 0.0 if largo == 0 else VDG.caida_tension(fases, ib, largo, r, x, fp, un)["delta_u_pct"]
    rc, xc = SC.impedance_cable(r, x, largo)
    return {
        "u": u, "icc": icc, "fases": fases, "fp": fp, "largo": largo, "ib": ib,
        "in": reg["In"], "s": s, "iz": AMP.iz(par, s, fases), "par": par, "t_cond": t_cond,
        "r": r, "x": x, "du": du, "limite": VD.limite_caida_pct(P._LIMITE["seccional"]),
        "i_min": P.current_sc_min(u, icc, rc, xc, fases), "k": k_magnetico,
        "smin": CO.section_min_circuit(P._SECCION_MIN["seccional"]),
        "icu": reg["icu"], "disp": reg["disp"],
    }


def _checks(v):
    """(verificación, valor, requisito, cumple) de la etapa 5."""
    return [
        ("Capacidad de conducción", f"Iz = {_sig2(v['iz'])} A", f"Iz ≥ In = {_sig2(v['in'])} A", v["iz"] >= v["in"]),
        ("Coordinación de sobrecarga", f"In = {_sig2(v['in'])} A", f"In ≥ Ib = {_sig2(v['ib'])} A", v["in"] >= v["ib"]),
        ("Caída de tensión", f"{_p1(v['du'])} %", f"≤ {_p1(v['limite'])} %", v["du"] <= v["limite"]),
        ("Disparo magnético", f"Icc mín = {_sig2(v['i_min'])} A", f"≥ {v['k']}·In = {_sig2(v['k'] * v['in'])} A",
         v["i_min"] >= v["k"] * v["in"]),
        ("Sección mínima", f"S = {_mm(v['s'])} mm²", f"≥ {_mm(v['smin'])} mm²", v["s"] >= v["smin"]),
        ("Poder de corte", f"icu = {_sig2(v['icu'])} kA", f"≥ Icc barras = {_sig2(v['icc'])} kA", v["icu"] >= v["icc"]),
    ]


def memoria_calculo(tablero, c, v, proyecto):
    """Memoria de Cálculo (MC) en Markdown: objeto, marco, etapas 1 a 6."""
    valor, base = P.convert_load(c["CARGA"], c.get("UNIDAD_CARGA"))
    fp_txt = f"{v['fp']:.2f}".replace(".", ",")
    if base == "a":
        ib_txt = f"Carga declarada en amperes: Ib = {_sig2(v['ib'])} A (sin conversión)."
    else:
        formula = "Ib = P / (√3 · U · cos φ)" if v["fases"] == 3 else "Ib = P / (U_f · cos φ)"
        ib_txt = (f"{formula} con P = {_sig2(valor)} {base.upper()}, U = {_sig2(v['u'])} V, "
                  f"cos φ = {fp_txt} → Ib = {_sig2(v['ib'])} A.")
    filas = "\n".join(f"| {n} | {vv} |" for n, vv in [
        ("Tensión nominal U", f"{_sig2(v['u'])} V"),
        ("Sistema de puesta a tierra", tablero.get("SISTEMA", "Pendiente")),
        ("Icc en barras del tablero", f"{_sig2(v['icc'])} kA"),
        ("Factor de potencia", fp_txt),
        ("Longitud del tendido", f"{_sig2(v['largo'])} m"),
        ("Tipo de cable", c.get("CABLE_TIPO") or "Pendiente"),
        ("Aislación / material", f"{v['par']['aislacion'].upper()} / {v['par']['material'].upper()}"),
        ("Método de instalación", f"{v['par']['metodo']} · {v['par']['ternas']} terna(s) · {v['par']['agrup']} circuito(s) agrupados"),
        ("Temperatura de servicio", f"{_sig2(v['t_cond'])} °C"),
    ])
    r_txt = f"{v['r']:.4f}".replace('.', ',')
    chk = _checks(v)
    tabla = "\n".join(f"| {a} | {b} | {r} | {_cumple(ok)} |" for a, b, r, ok in chk)
    global_ok = all(ok for *_, ok in chk)
    return f"""# Memoria de Cálculo: alimentador principal {c['TAG']}

**Proyecto:** {proyecto} · **Circuito:** {c['TAG']} – {c.get('DESCRIPCION') or ''}

## 1. Objeto y alcance
Dimensionar y verificar el alimentador principal del tablero. Los demás circuitos se documentan en el JSON de cálculo.

## 2. Marco normativo
{chr(10).join('- ' + n for n in NORMA_MARCO)}

## Etapa 1 – Datos genéricos
| Parámetro | Valor |
|---|---|
{filas}

## Etapa 2 – Corriente de proyecto
{ib_txt}

## Etapa 3 – Criterios de verificación
- Capacidad: Iz ≥ In ≥ Ib.
- Caída de tensión: ΔU ≤ {_p1(v['limite'])} % (alimentador seccional).
- Disparo magnético: Icc mínima al final del cable ≥ {v['k']}·In.
- Sección mínima: S ≥ {_mm(v['smin'])} mm².
- Poder de corte: icu ≥ Icc en barras.

## Etapa 4 – Selección de la sección
- Sección elegida: S = {_mm(v['s'])} mm² de {'cobre' if v['par']['material'] == 'cu' else 'aluminio'} ({v['par']['aislacion'].upper()}, método {v['par']['metodo']}); Iz = {_sig2(v['iz'])} A según tablas 771.16.
- Resistencia a 70 °C: R = {r_txt} Ω/km; reactancia X = 0,08 Ω/km.
- Caída de tensión: ΔU = k · I · L · (R · cos φ + X · sen φ) / U, con I = Ib = {_sig2(v['ib'])} A y L = {_sig2(v['largo'])} m → ΔU = {_p1(v['du'])} %.
- Pendiente: factores de agrupamiento y de temperatura (k) no aplicados; el cálculo usa la tabla vigente a 40 °C.

## Etapa 5 – Verificaciones finales
| Verificación | Valor | Requisito | Resultado |
|---|---|---|---|
{tabla}
| PE y N (S_PE = S_N) | Pendiente | Pendiente | Pendiente |
| Icc máxima y selectividad | Pendiente | Pendiente | Pendiente |

**Resultado global:** {_cumple(global_ok)} (sujeto a las verificaciones pendientes).

## Etapa 6 – Conclusión y puntos a verificar
El alimentador {c['TAG']} con cable de {_mm(v['s'])} mm² de cobre y protección {v['disp']} {'cumple' if global_ok else 'no cumple'} las verificaciones calculadas.
Puntos a verificar: Icc máxima, selectividad, conductores PE y N, y factores de agrupamiento y temperatura.
"""


def sintesis_proyecto(c, v, proyecto):
    """Síntesis de Proyecto (SP): una página, requisito normativo | dato técnico, máximo tres observaciones."""
    chk = _checks(v)
    global_ok = all(ok for *_, ok in chk)
    filas = "\n".join([
        f"| Capacidad de conducción (771) | {v['par']['material'].capitalize()} {_mm(v['s'])} mm², Iz {_sig2(v['iz'])} A ≥ In {_sig2(v['in'])} A |",
        f"| Caída de tensión (771.19) | ΔU {_p1(v['du'])} % ≤ {_p1(v['limite'])} % |",
        f"| Protección y poder de corte (90909-1) | {v['disp']}, icu {_sig2(v['icu'])} kA ≥ Icc {_sig2(v['icc'])} kA |",
        f"| Disparo magnético | Icc mín {_sig2(v['i_min'])} A ≥ {v['k']}·In |",
        f"| Sección mínima (771.13) | S {_mm(v['s'])} mm² ≥ {_mm(v['smin'])} mm² |",
    ])
    return f"""# Síntesis de Proyecto: {c['TAG']}

**Proyecto:** {proyecto} · **Alimentador principal:** {c['TAG']}

| Requisito normativo | Dato técnico |
|---|---|
{filas}

**Resultado global:** {_cumple(global_ok)}

**Observaciones**
1. Pendiente: Icc máxima y selectividad.
2. Pendiente: conductores PE y N.
3. Factores de agrupamiento y temperatura no aplicados en esta versión.
"""


def generar_documentos(base, tablero, circuitos, datos, tag=None, temp_c=70.0, k_magnetico=P.K_MAGNETICO_C):
    """Escribe <base>_MC.md y <base>_SP.md del alimentador principal. Devuelve las rutas."""
    c = alimentador_principal(circuitos, tag)
    v = verificaciones(tablero, c, datos[c["TAG"]], temp_c, k_magnetico)
    proyecto = os.path.basename(base)
    rutas = []
    for sufijo, texto in (("_MC.md", memoria_calculo(tablero, c, v, proyecto)),
                          ("_SP.md", sintesis_proyecto(c, v, proyecto))):
        ruta = base + sufijo
        with open(ruta, "w", encoding="utf-8", newline="\n") as f:
            f.write(texto)
        rutas.append(ruta)
    return rutas

