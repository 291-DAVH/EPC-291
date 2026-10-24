"""board_memo — Memoria de Cálculo (MC) y Síntesis de Proyecto (SP) de un tablero completo.

ESTADO: BORRADOR — los valores base de los criterios están pendientes de validación (ver aviso en la memoria).

OBJETIVO
    Con el resultado del dimensionamiento (`aea_pipeline.calculate`) documentar TODO el tablero, no solo su alimentador:
      1. Cables, separados en acometida (cable que alimenta al tablero), cableado interno (térmico, dentro del tablero)
         y cableado externo (de salida hacia la carga, por caída de tensión y capacidad de conducción).
      2. Protección de cada circuito: In, curva, poder de corte, Icc mínima y disparo magnético, sobrecarga y coordinación.
      3. Diferencial: sensibilidad, tipo, esquema de conexión a tierra y contacto indirecto.
      4. Curvas y selectividad entre protecciones en serie (bandas normativas; el fabricante puede ser más estrecho).
      5. Síntesis de una página (requisito | dato técnico, resultado y hasta tres observaciones).
    No recalcula nada: lee los valores del mismo cálculo que alimenta el unifilar (fuente única).

FÓRMULAS
    Iz ≥ In ≥ Ib ;  I2 = k2·In ≤ 1,45·Iz ;  Icc_mín ≥ k_máx·In (disparo magnético garantizado)
    Zs_máx = U0/Ia ;  TT: Ra_máx = UL/IΔn ;  selectividad térmica: In_arriba/In_abajo ≥ 1,6
    selectividad magnética: Icc ≤ k_mín(arriba)·In(arriba)  →  total; en otro caso parcial hasta Is = k_mín·In

LIMITACIONES
    - Las curvas son las bandas de IEC 60898-1 / IEC 60947-2: sin las tablas del fabricante la selectividad parcial
      queda como "confirmar con el fabricante".
    - La curva adoptada (B/C/D) es un supuesto de proyecto (C general, D para motores con MCB); se informa en la memoria.
    - Icc en bornes = Icc de barras del tablero (cota superior).

NORMA DE REFERENCIA
    AEA 90364-4-41, 4-43, 7-771 ; IEC 60898-1, IEC 60947-2, IEC 60364-5-53 ; AEA 90909-1.  [VERIFICAR]
"""
import math
from typing import Dict, List, Optional

from epc_calc import aea_protection as PR

__version__ = "0.1.0"

# disparo magnético [× In]: (mínimo que NO debe disparar, máximo que DEBE disparar)
K_MAG = {"B": (3, 5), "C": (5, 10), "D": (10, 20), "MCCB": (5, 10)}
U0_V = 230.0
UL_V = 50.0
RATIO_TERMICO = 1.6
RCD_KINDS = ("rccb", "rcbo")
MOTORES = {"dol", "dol_ol", "star_delta", "softstarter", "vfd", "dol_rcd"}

NORMA_MARCO = (
    "AEA 90364-7-771 (ed. 2006): instalaciones en viviendas y similares",
    "AEA 90364-7-770 (ed. 2017): instalaciones en edificios",
    "AEA 90364-4-41 y 4-43: protección contra contactos indirectos y contra sobrecorrientes",
    "AEA 90909-1: cálculo de cortocircuito",
    "IEC 60898-1 e IEC 60947-2: características de disparo de los interruptores",
)


# ---------------------------------------------------------------- formato
def p1(x) -> str:
    return "Pendiente" if x is None else f"{x:.1f}".replace(".", ",")


def sig2(x) -> str:
    if x is None:
        return "Pendiente"
    if not x:
        return "0"
    d = 1 - int(math.floor(math.log10(abs(x))))
    v = round(x, d)
    return (f"{v:.0f}" if d <= 0 else f"{v:.{d}f}").replace(".", ",")


def mm(x) -> str:
    return "Pendiente" if x is None else f"{x:g}".replace(".", ",")


def ok(b: Optional[bool]) -> str:
    return "—" if b is None else ("CUMPLE" if b else "NO CUMPLE")


# ---------------------------------------------------------------- curvas
def curve_letter(kind: str, tipo: str, topologia: str) -> str:
    """Curva adoptada: MCCB con disparo magnético ajustable (5–10·In); MCB/RCBO C, y D para motores protegidos con MCB."""
    if kind == "mccb":
        return "MCCB"
    return "D" if topologia in MOTORES and kind in ("mcb", "rcbo") else "C"


def curve_band(in_a: float, letter: str) -> Dict[str, List[List[float]]]:
    """Banda de disparo [A, s] (mínimo y máximo) según IEC 60898-1 (MCB) o IEC 60947-2 (MCCB), puntos para un gráfico log-log."""
    kmin, kmax = K_MAG[letter]
    mccb = letter == "MCCB"
    f_no, f_si = (1.05, 1.30) if mccb else (1.13, 1.45)
    t_conv = 3600 if in_a <= 63 else 7200
    t_255 = 60 if in_a <= 32 else 120
    mx = [[f_si * in_a, t_conv], [2.55 * in_a, t_255], [kmax * in_a, 0.1], [kmax * in_a, 0.01]]
    mn = [[f_no * in_a, t_conv], [2.55 * in_a, 1], [kmin * in_a, 0.1], [kmin * in_a, 0.01]]
    return {"min": [[round(a, 1), t] for a, t in mn], "max": [[round(a, 1), t] for a, t in mx]}


# ---------------------------------------------------------------- análisis por circuito
def _rcd_of(tag: str, circ: Dict[str, dict], det: Dict[str, dict]) -> Optional[str]:
    """TAG del circuito cuyo diferencial protege a `tag`: él mismo (RCBO / RCCB / motor con diferencial) o su antecesor más cercano."""
    cur, seen = tag, set()
    while cur and cur not in seen:
        seen.add(cur)
        d = det.get(cur, {})
        if d.get("kind") in RCD_KINDS or d.get("topologia") == "dol_rcd":
            return cur
        cur = (circ.get(cur, {}).get("parent_tag") or "").strip()
    return None


def _rcd_type(tag: str, circ: Dict[str, dict], det: Dict[str, dict], rcd_tag: str) -> str:
    """Tipo de diferencial según la carga: variadores de frecuencia (corrientes con componente continua) piden tipo B; el resto, tipo A."""
    tops = {det.get(t, {}).get("topologia") for t in (tag, rcd_tag)}
    kids = [t for t, c in circ.items() if (c.get("parent_tag") or "").strip() == rcd_tag]
    tops |= {det.get(k, {}).get("topologia") for k in kids}
    return "B" if "vfd" in tops else "A"


def _circuit(tag: str, circ: Dict[str, dict], dat: dict, det: dict, board: dict, rcd_ma: float, system: str, icc_a: float) -> dict:
    c, d = circ.get(tag, {}), det[tag]
    in_a, ib = dat["In"], dat["Ib"]
    s_ext, s_int = dat["S"], d.get("s_termica_mm2")
    iz = d.get("iz_a")
    kind = d.get("kind", "mcb")
    letter = curve_letter(kind, d["tipo"], d.get("topologia", "single"))
    kmin, kmax = K_MAG[letter]
    icc_min = d.get("icc_min_a")
    k2 = PR.K2_CONVENCIONAL["mccb" if kind == "mccb" else "mcb"]
    i2 = k2 * in_a
    sobrecarga = bool(iz is not None and ib <= in_a <= iz)
    coordinacion = bool(iz is not None and i2 <= 1.45 * iz)
    disparo = None if icc_min is None else icc_min >= kmax * in_a
    icu_ok = dat["icu"] * 1000 >= icc_a
    cable_ok = bool(d["cumple"])
    # diferencial
    rcd_tag = _rcd_of(tag, circ, det)
    dif = None
    if rcd_tag:
        idn = rcd_ma
        dif = {"tag_rcd": rcd_tag, "idn_ma": idn, "tipo": _rcd_type(tag, circ, det, rcd_tag), "esquema": system,
               "zs_max_ohm": round(U0_V / (idn / 1000), 0), "ra_max_tt_ohm": round(UL_V / (idn / 1000), 0),
               "contacto_indirecto": system != "IT", "cumple": True}
        if system == "IT":
            dif["nota"] = "IT: la primera falla no desconecta (monitor de aislación); la segunda falla se verifica con 2·Ia·Zs ≤ U."
    needs_rcd = d["tipo"] == "tomacorrientes"
    falta_rcd = needs_rcd and dif is None
    if falta_rcd:
        dif = {"tag_rcd": None, "idn_ma": None, "tipo": None, "esquema": system, "zs_max_ohm": None, "ra_max_tt_ohm": None,
               "contacto_indirecto": False, "cumple": False, "nota": "Tomacorrientes sin protección diferencial de alta sensibilidad: se requiere."}
    prot_ok = all([sobrecarga, coordinacion, icu_ok, disparo is not False])
    cumple = cable_ok and prot_ok and not falta_rcd
    return {
        "tag": tag, "description": c.get("description", ""), "tipo": d["tipo"], "parent": d.get("padre", ""), "Ib": ib, "In": in_a,
        "interno": {"S_mm2": s_int, "criterio": "térmico: Iz ≥ In"},
        "externo": {"S_mm2": s_ext, "length_m": d.get("largo_m"), "iz_a": iz, "du_propia_pct": d.get("du_propia_pct"), "du_acum_pct": d.get("du_acum_pct"),
                    "limite_pct": d.get("limite_pct"), "cumple": cable_ok},
        "transicion": bool(s_int is not None and s_ext is not None and s_ext > s_int),
        "proteccion": {"disp": dat["disp"], "kind": kind, "curva": letter, "In": in_a, "icu_ka": dat["icu"], "icu_ok": icu_ok, "icc_a": round(icc_a, 0),
                       "icc_min_a": icc_min, "k_min": kmin, "k_max": kmax, "disparo_ok": disparo, "iz_a": iz, "sobrecarga_ok": sobrecarga,
                       "i2_a": round(i2, 1), "coordinacion_ok": coordinacion, "cumple": prot_ok},
        "diferencial": dif, "cumple": cumple,
    }


def _selectividad(circuits: List[dict], by_tag: Dict[str, dict], icc_a: float, upstream: Optional[dict]) -> List[dict]:
    pairs = []

    def pair(up: dict, down: dict, up_name: str, down_name: str):
        up_in, dn_in = up["In"], down["In"]
        ratio = up_in / dn_in if dn_in else None
        kmin = up["k_min"]
        is_a = kmin * up_in
        total = icc_a <= is_a
        term_ok = ratio is not None and ratio >= RATIO_TERMICO
        res = "total" if (total and term_ok) else ("parcial" if term_ok or total else "revisar")
        pairs.append({"aguas_arriba": up_name, "aguas_abajo": down_name, "In_arriba": up_in, "In_abajo": dn_in, "curva_arriba": up["curva"], "curva_abajo": down["curva"],
                      "relacion_termica": None if ratio is None else round(ratio, 2), "termica_ok": term_ok, "is_a": round(is_a, 0), "icc_a": round(icc_a, 0),
                      "magnetica_total": total, "resultado": res,
                      "nota": ("Selectividad total hasta la Icc del tablero." if res == "total" else
                               f"Selectiva hasta {sig2(is_a)} A; por encima intervienen ambas protecciones: confirmar con la tabla de selectividad del fabricante o usar disparo retardado."
                               if res == "parcial" else
                               "Relación de corrientes insuficiente y sin selectividad magnética: cambiar calibres o curvas.")})

    for c in circuits:
        p = c["parent"]
        if p and p in by_tag and by_tag[p]["proteccion"]["kind"] not in ("rccb",):
            pair(by_tag[p]["proteccion"], c["proteccion"], p, c["tag"])
        elif not p and upstream and upstream.get("In"):
            up = {"In": upstream["In"], "curva": upstream.get("curva", "MCCB" if upstream.get("In", 0) > 63 else "C"),
                  "k_min": K_MAG["MCCB" if upstream.get("In", 0) > 63 else "C"][0]}
            pair(up, c["proteccion"], f"{upstream.get('board', 'aguas arriba')} · {upstream.get('tag', '')}".strip(" ·"), c["tag"])
    return pairs


def build(board: dict, circuits_in: List[dict], datos: dict, detalle: dict, limites: dict, conductor: dict, rcd_ma: float,
          upstream: Optional[dict] = None, validated: bool = True) -> dict:
    """Memoria completa del tablero como datos. `board`/`circuits_in` son los datos del formulario; `datos`/`detalle` el resultado del cálculo."""
    circ = {c["tag"]: c for c in circuits_in}
    system = board.get("system", "TN-S")
    icc_a = float(board.get("icc_ka", 10)) * 1000
    items = [_circuit(t, circ, datos[t], detalle, board, rcd_ma, system, icc_a) for t in datos]
    by_tag = {c["tag"]: c for c in items}
    sel = _selectividad(items, by_tag, icc_a, upstream)
    curvas = {c["tag"]: {"curva": c["proteccion"]["curva"], "In": c["In"], **curve_band(c["In"], c["proteccion"]["curva"])} for c in items}
    ac = {"desde": (upstream or {}).get("board") or "Red / fuente externa al proyecto", "tag": (upstream or {}).get("tag", ""),
          "length_m": (upstream or {}).get("length_m", board.get("feeder_length_m")), "S_mm2": (upstream or {}).get("S"),
          "In": (upstream or {}).get("In"), "du_pct": (upstream or {}).get("dU"), "disp": (upstream or {}).get("disp"),
          "dato_faltante": not upstream}
    obs = _observations(items, sel, ac, validated)
    resumen = {"circuits": len(items), "cumplen": sum(1 for c in items if c["cumple"]), "no_cumplen": sum(1 for c in items if not c["cumple"]),
               "transiciones": sum(1 for c in items if c["transicion"]), "global": all(c["cumple"] for c in items),
               "selectividad": {k: sum(1 for s in sel if s["resultado"] == k) for k in ("total", "parcial", "revisar")}, "observaciones": obs}
    return {"schema_version": "1.0", "validated": validated,
            "board": {"name": board.get("name", ""), "voltage_v": board.get("voltage_v"), "system": system, "icc_ka": board.get("icc_ka"), "fp": board.get("fp_default"),
                      "frequency_hz": board.get("frequency_hz"), "project": board.get("project", "")},
            "criteria": {"limits_pct": limites, "conductor": conductor, "rcd_ma": rcd_ma, "curvas_k": {k: list(v) for k, v in K_MAG.items()}},
            "acometida": ac, "circuits": items, "selectividad": sel, "curvas": curvas, "resumen": resumen,
            "supuestos": ["Curva adoptada: C en MCB/RCBO generales, D en motores protegidos con MCB, disparo 5–10·In en MCCB (ajustable).",
                          "Icc en bornes de cada protección = Icc de barras del tablero (cota superior).",
                          "Conductor de protección de la misma sección que la fase para el cálculo de Icc mínima.",
                          "Bandas de disparo según IEC 60898-1 / IEC 60947-2; el fabricante puede ser más estrecho."]}


def _observations(items: List[dict], sel: List[dict], ac: dict, validated: bool) -> List[str]:
    """Hasta tres observaciones, de lo más grave a lo menos."""
    obs: List[str] = []
    for c in items:
        if not c["externo"]["cumple"]:
            obs.append(f"{c['tag']}: el cable de salida no cumple capacidad de conducción o caída de tensión ({p1(c['externo']['du_acum_pct'])} % acumulada).")
        p = c["proteccion"]
        if not p["icu_ok"]:
            obs.append(f"{c['tag']}: poder de corte {sig2(p['icu_ka'])} kA menor que la Icc del tablero ({sig2(p['icc_a'] / 1000)} kA).")
        if p["disparo_ok"] is False:
            obs.append(f"{c['tag']}: Icc mínima {sig2(p['icc_min_a'])} A < {p['k_max']}·In ({sig2(p['k_max'] * p['In'])} A): el disparo magnético no está garantizado.")
        if c["diferencial"] and c["diferencial"]["cumple"] is False:
            obs.append(f"{c['tag']}: {c['diferencial']['nota']}")
    if any(s["resultado"] == "revisar" for s in sel):
        obs.append("Hay protecciones en serie sin selectividad: revisar calibres o curvas (ver tabla de selectividad).")
    transiciones = [c["tag"] for c in items if c["transicion"]]
    if transiciones:
        obs.append(f"Circuitos con cable de salida mayor al interno (bornera de transición): {', '.join(transiciones[:6])}{'…' if len(transiciones) > 6 else ''}.")
    if any(s["resultado"] == "parcial" for s in sel):
        obs.append("Selectividad parcial entre protecciones en serie: confirmar con las tablas del fabricante.")
    if ac["dato_faltante"]:
        obs.append("Acometida: cable y protección de cabecera Pendientes (no hay tablero superior definido).")
    if not validated:
        obs.append("Valores base de criterios y tablas sin validar contra las normas: confirmar antes de emitir.")
    return obs[:3]


# ---------------------------------------------------------------- documentos
# Un documento es una estructura {title, subtitle, footer, blocks}: de ella salen el Markdown (vista y archivo) y el PDF (entregable), con los mismos textos.
def mark(b: Optional[bool]) -> str:
    return "—" if b is None else ("✓" if b else "✗")


def _doc(m: dict, title: str, blocks: list) -> dict:
    b = m["board"]
    return {"title": title, "subtitle": b["name"], "footer": f"{title} · {b['name']} · {b.get('project') or ''}".strip(" ·"), "page_label": "Página {n} de {total}", "blocks": blocks}


def memoria_doc(m: dict) -> dict:
    b, cr, ac, r = m["board"], m["criteria"], m["acometida"], m["resumen"]
    lim, cond = cr["limits_pct"], cr["conductor"]
    mat = {"cu": "cobre", "al": "aluminio"}.get(cond.get("material"), cond.get("material", ""))
    B: list = []
    if not m["validated"]:
        B += [{"type": "p", "text": "Valores base sin validar contra las normas: confirmar antes de emitir."}]
    B += [{"type": "h", "text": "1. Objeto, alcance y marco normativo"},
          {"type": "p", "text": f"Dimensionamiento de cables y protecciones de todos los circuitos del tablero {b['name']}, con análisis del diferencial y de la selectividad."},
          {"type": "bullets", "items": list(NORMA_MARCO)},
          {"type": "h", "text": "2. Datos generales"},
          {"type": "kv", "rows": [["Proyecto", b.get("project") or "Pendiente"], ["Tensión", f"{p1(b['voltage_v'])} V"], ["Esquema de conexión a tierra", b["system"]],
                                  ["Icc en barras", f"{sig2(b['icc_ka'])} kA"], ["Frecuencia", f"{sig2(b['frequency_hz'])} Hz"],
                                  ["Factor de potencia", str(b["fp"]).replace(".", ",")], ["Conductor", f"{mat}, aislación {str(cond.get('aislacion', '')).upper()}"],
                                  ["Caída de tensión máxima", f"seccionales {p1(lim['seccional'])} %, iluminación y tomas {p1(lim['terminal'])} %, motores {p1(lim['motor'])} %"],
                                  ["Sensibilidad del diferencial", f"{sig2(cr['rcd_ma'])} mA"]]},
          {"type": "h", "text": "3. Cables"}, {"type": "h", "text": "3.1 Cable de acometida (alimenta al tablero)"}]
    if ac["dato_faltante"]:
        B += [{"type": "p", "text": f"Alimentación desde: {ac['desde']}. Longitud de acometida: {sig2(ac['length_m'])} m. Sección y protección de cabecera: Pendiente (se definen en el tablero superior)."}]
    else:
        B += [{"type": "p", "text": f"Alimentación desde el circuito {ac['tag']} de {ac['desde']}: {mm(ac['S_mm2'])} mm², {sig2(ac['length_m'])} m, protección {ac['disp']}, caída de tensión {p1(ac['du_pct'])} %."}]
    B += [{"type": "h", "text": "3.2 Cableado interno y cableado externo de cada circuito"},
          {"type": "p", "text": "El cableado interno (dentro del tablero) se dimensiona por capacidad térmica: Iz ≥ In. El cableado externo (de salida hacia la carga) se dimensiona además por caída de tensión sobre la longitud real; "
                                "si resulta mayor que el interno, se indica la bornera de transición."},
          {"type": "table", "columns": [["TAG", 0.1], ["Ib A", 0.07], ["In A", 0.07], ["S int. mm²", 0.09], ["S ext. mm²", 0.09], ["Largo m", 0.08], ["Iz A", 0.07], ["ΔU %", 0.08],
                                        ["ΔU acum. %", 0.1], ["Límite %", 0.08], ["Trans.", 0.07], ["Cumple", 0.1]],
           "rows": [[c["tag"], sig2(c["Ib"]), sig2(c["In"]), mm(c["interno"]["S_mm2"]), mm(c["externo"]["S_mm2"]), sig2(c["externo"]["length_m"]), sig2(c["externo"]["iz_a"]),
                     p1(c["externo"]["du_propia_pct"]), p1(c["externo"]["du_acum_pct"]), p1(c["externo"]["limite_pct"]), "sí" if c["transicion"] else "no", mark(c["externo"]["cumple"])]
                    for c in m["circuits"]]},
          {"type": "h", "text": "4. Protecciones"},
          {"type": "table", "columns": [["TAG", 0.09], ["Dispositivo", 0.2], ["Curva", 0.07], ["In A", 0.06], ["Icu kA", 0.07], ["Icc mín A", 0.1], ["k·In A", 0.08], ["Disparo", 0.08],
                                        ["Sobrec.", 0.08], ["I2 A", 0.07], ["Coord.", 0.07], ["Cumple", 0.08]],
           "rows": [[c["tag"], c["proteccion"]["disp"], c["proteccion"]["curva"], sig2(c["proteccion"]["In"]), sig2(c["proteccion"]["icu_ka"]), sig2(c["proteccion"]["icc_min_a"]),
                     sig2(c["proteccion"]["k_max"] * c["proteccion"]["In"]), mark(c["proteccion"]["disparo_ok"]), mark(c["proteccion"]["sobrecarga_ok"]), sig2(c["proteccion"]["i2_a"]),
                     mark(c["proteccion"]["coordinacion_ok"]), mark(c["proteccion"]["cumple"])] for c in m["circuits"]]},
          {"type": "p", "text": f"Icc en barras {sig2(b['icc_ka'])} kA. Disparo: Icc mínima al final del circuito ≥ k·In (k = 5 curva B, 10 curva C, 20 curva D). Coordinación: I2 = k2·In ≤ 1,45·Iz."},
          {"type": "h", "text": "5. Diferencial"}]
    difs = [c for c in m["circuits"] if c["diferencial"]]
    if not difs:
        B += [{"type": "p", "text": "Ningún circuito del tablero lleva protección diferencial."}]
    else:
        B += [{"type": "p", "text": f"Esquema {b['system']}. Zs máx = U0/IΔn con U0 = 230 V; en esquema TT, Ra máx = 50 V/IΔn."},
              {"type": "table", "columns": [["TAG", 0.14], ["Diferencial en", 0.18], ["IΔn mA", 0.12], ["Tipo", 0.1], ["Zs máx Ω", 0.16], ["Ra máx TT Ω", 0.18], ["Cumple", 0.12]],
               "rows": [[c["tag"], c["diferencial"]["tag_rcd"] or "—", sig2(c["diferencial"]["idn_ma"]), c["diferencial"]["tipo"] or "—", sig2(c["diferencial"]["zs_max_ohm"]),
                         sig2(c["diferencial"]["ra_max_tt_ohm"]), mark(c["diferencial"]["cumple"])] for c in difs]}]
        notas = sorted({c["diferencial"]["nota"] for c in difs if c["diferencial"].get("nota")})
        if notas:
            B += [{"type": "bullets", "items": notas}]
    B += [{"type": "h", "text": "6. Curvas y selectividad"},
          {"type": "p", "text": "Banda de disparo normativa de cada protección (curvas en la aplicación) y análisis entre protecciones en serie."}]
    if m["selectividad"]:
        B += [{"type": "table", "columns": [["Aguas arriba", 0.2], ["Aguas abajo", 0.15], ["In A", 0.12], ["Relación", 0.1], ["Selectiva hasta A", 0.15], ["Icc A", 0.13], ["Resultado", 0.15]],
               "rows": [[s["aguas_arriba"], s["aguas_abajo"], f"{sig2(s['In_arriba'])} / {sig2(s['In_abajo'])}", p1(s["relacion_termica"]), sig2(s["is_a"]), sig2(s["icc_a"]), s["resultado"]]
                        for s in m["selectividad"]]}]
    else:
        B += [{"type": "p", "text": "No hay protecciones en serie dentro del tablero."}]
    B += [{"type": "h", "text": "7. Conclusión y puntos a verificar"},
          {"type": "p", "text": f"Resultado global: {ok(r['global'])} ({r['cumplen']} de {r['circuits']} circuitos cumplen)."},
          {"type": "bullets", "items": [f"{i}. {o}" for i, o in enumerate(r["observaciones"], 1)] or ["Sin observaciones."]},
          {"type": "h", "text": "Supuestos"}, {"type": "bullets", "items": list(m["supuestos"])}]
    return _doc(m, "Memoria de Cálculo", B)


def sintesis_doc(m: dict) -> dict:
    b, r, ac = m["board"], m["resumen"], m["acometida"]
    items = m["circuits"]

    def worst(vals):
        v = [x for x in vals if x is not None]
        return min(v) if v else None

    marg_iz = worst([c["externo"]["iz_a"] / c["In"] for c in items if c["externo"]["iz_a"]])
    du_max = max([c["externo"]["du_acum_pct"] or 0 for c in items] or [0])
    lim = m["criteria"]["limits_pct"]
    icu_min = worst([c["proteccion"]["icu_ka"] for c in items])
    icc_min = worst([c["proteccion"]["icc_min_a"] for c in items])
    difs = [c for c in items if c["diferencial"] and c["diferencial"]["tag_rcd"]]
    sel = r["selectividad"]
    rows = [
        ["Capacidad de conducción (Iz ≥ In)", f"Iz/In mínimo = {p1(marg_iz)}" if marg_iz else "Pendiente", ok(all(c["proteccion"]["sobrecarga_ok"] for c in items))],
        ["Caída de tensión", f"máxima acumulada {p1(du_max)} % (límites {p1(lim['seccional'])} / {p1(lim['terminal'])} / {p1(lim['motor'])} %)", ok(all(c["externo"]["cumple"] for c in items))],
        ["Cableado interno y externo", f"{r['transiciones']} circuito(s) con cable de salida mayor al interno (bornera de transición)", "—"],
        ["Poder de corte", f"Icu mínimo = {sig2(icu_min)} kA frente a Icc = {sig2(b['icc_ka'])} kA", ok(all(c["proteccion"]["icu_ok"] for c in items))],
        ["Disparo magnético", f"Icc mínima = {sig2(icc_min)} A, curvas " + ", ".join(sorted({c["proteccion"]["curva"] for c in items})),
         "—" if all(c["proteccion"]["disparo_ok"] is None for c in items) else ok(all(c["proteccion"]["disparo_ok"] is not False for c in items))],
        ["Diferencial", f"{len(difs)} circuito(s) con IΔn {sig2(m['criteria']['rcd_ma'])} mA, esquema {b['system']}" if difs else f"sin diferencial, esquema {b['system']}",
         ok(not any(c["diferencial"] and c["diferencial"]["cumple"] is False for c in items))],
        ["Selectividad", f"{sel['total']} total, {sel['parcial']} parcial, {sel['revisar']} a revisar", ok(sel["revisar"] == 0)],
        ["Acometida", f"{mm(ac['S_mm2'])} mm², {sig2(ac['length_m'])} m" if not ac["dato_faltante"] else f"{sig2(ac['length_m'])} m; sección Pendiente", "—"],
    ]
    B = [{"type": "table", "columns": [["Requisito normativo", 0.3], ["Dato técnico", 0.5], ["Resultado", 0.2]], "rows": rows},
         {"type": "p", "text": f"Resultado global: {ok(r['global'])}"},
         {"type": "h", "text": "Observaciones"},
         {"type": "bullets", "items": [f"{i}. {o}" for i, o in enumerate(r["observaciones"], 1)] or ["Sin observaciones."]}]
    return _doc(m, "Síntesis de Proyecto", B)


def doc_markdown(doc: dict) -> str:
    L = [f"# {doc['title']} — Tablero {doc['subtitle']}", ""]
    for b in doc["blocks"]:
        t = b["type"]
        if t == "h":
            L += [f"## {b['text']}", ""]
        elif t == "p":
            L += [b["text"], ""]
        elif t == "bullets":
            L += [f"- {i}" for i in b["items"]] + [""]
        elif t == "kv":
            L += ["| Dato | Valor |", "|---|---|"] + [f"| {k} | {v} |" for k, v in b["rows"]] + [""]
        elif t == "table":
            cols = [c for c, _ in b["columns"]]
            L += ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)] + ["| " + " | ".join(str(x) for x in row) + " |" for row in b["rows"]] + [""]
    L += ["_Generado automáticamente a partir del cálculo del tablero._", ""]
    return "\n".join(L)


def memoria_md(m: dict) -> str:
    return doc_markdown(memoria_doc(m))


def sintesis_md(m: dict) -> str:
    return doc_markdown(sintesis_doc(m))
