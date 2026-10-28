"""Cifras del tablero que acompañan a sus dibujos: barra principal, acometida, verificaciones y notas.

Los dibujos (unifilar y multifilar) solo dibujan: todo número que muestran sale de aquí y de `aea_pipeline` (potencias, secciones de PE y neutro en `detalle`).
Este módulo parte de lo que ya se calculó (`datos` y `detalle` del pipeline, la acometida de la memoria) y no dimensiona nada nuevo.
"""
import math
from typing import Dict, List, Optional

from epc_aea90364 import aea_pipeline as P

CHECK_PENDING = None                                  # verificación que depende de un dato que falta (p. ej. el tablero superior)


def _roots(detalle: Dict[str, dict]) -> List[str]:
    return [t for t, d in detalle.items() if not d.get("padre") or d["padre"] not in detalle]


DIFFERENTIAL_SYMBOLS = ("lv_rccb", "lv_rcbo")


def _own_differential(tag: str, detalle: Dict[str, dict]) -> bool:
    """Whether the devices the standard solution gave this circuit include a differential."""
    return any(item["symbol"] in DIFFERENTIAL_SYMBOLS for item in detalle[tag]["cadena"])


def _has_differential(tag: str, detalle: Dict[str, dict]) -> bool:
    """A circuit is protected by a differential of its own or by one of the groups above it."""
    while tag and tag in detalle:
        if _own_differential(tag, detalle):
            return True
        tag = detalle[tag].get("padre")
    return False


def _feeder(acometida: dict, board: dict, bar_in: int, limit_pct: float) -> dict:
    """The cable that feeds the board, as the memo has it: with its section when the upstream board gave it, pending when it did not."""
    length = acometida.get("length_m") or board.get("feeder_length_m") or 0
    known = not acometida.get("dato_faltante") and acometida.get("S_mm2")
    du = acometida.get("du_pct")
    return {"length_m": length, "pending": not known, "S_mm2": acometida.get("S_mm2") if known else None, "du_pct": du if known else None, "from": acometida.get("desde", ""),
            "ok": CHECK_PENDING if not known or du is None else du <= limit_pct + 1e-9, "limit_pct": limit_pct, "bar_in_a": bar_in}


def build(board: dict, datos: Dict[str, dict], detalle: Dict[str, dict], limites: dict, rcd_ma, acometida: dict) -> dict:
    """{"bar", "feeder", "checks": [{"text", "ok"}], "lines": [...], "note", "rcd_ma"}; `ok` is True, False or None (pending)."""
    icc, volt, fp = float(board.get("icc_ka") or 0), float(board.get("voltage_v") or 380), float(board.get("fp_default") or 0.85)
    roots = _roots(detalle)
    ib_total = sum(datos[t]["Ib"] for t in roots)
    p_total = sum(detalle[t]["p_kw"] for t in roots)
    bar_in = P._primero(P.SERIE_IN_A, ib_total) or P.SERIE_IN_A[-1]
    feeder = _feeder(acometida, board, bar_in, limites["seccional"])
    leaves = [t for t, d in detalle.items() if not any(x.get("padre") == t for x in detalle.values())]
    du_max = max((detalle[t]["du_propia_pct"] for t in leaves), default=0.0)
    motors = [t for t, d in detalle.items() if d["topologia"] in P.TOPOLOGIAS_MOTOR]
    pending = [t for t in leaves if detalle[t]["fases"] == 1 and not _has_differential(t, detalle)]
    checks = [
        {"text": "Icu >= Icc en todos los dispositivos", "ok": all(d["icu"] >= icc for d in datos.values())},
        {"text": "In >= Ib en todos los circuitos", "ok": all(d["In"] >= d["Ib"] for d in datos.values())},
        {"text": "Iz del cable >= In (seccion por tabla)", "ok": all(d["iz_a"] is None or d["iz_a"] >= d["in_a"] for d in detalle.values())},
        {"text": f"ΔU maxima {du_max:.2f} % (limite {limites['terminal']:g} % / {limites['motor']:g} % motores)", "ok": all(detalle[t]["du_propia_pct"] <= detalle[t]["limite_pct"] + 1e-9 for t in leaves)},
        {"text": "In >= 1,25·Ib en motores", "ok": all(datos[t]["In"] >= P.MARGIN_MOTOR * datos[t]["Ib"] - 1e-9 for t in motors)},
        {"text": f"Diferencial {rcd_ma:g} mA en circuitos 1F", "ok": not pending},
        {"text": (f"ΔU acometida {feeder['du_pct']:.2f} % (limite {limites['seccional']:g} %)" if feeder["du_pct"] is not None else "Acometida: seccion y proteccion pendientes (tablero superior)"), "ok": feeder["ok"]},
    ]
    feeder_text = (f"Acometida: seccion y proteccion pendientes (se definen en el tablero superior) · L {feeder['length_m']:g} m" if feeder["pending"] else
                   f"Acometida: {feeder['S_mm2']} mm² · L {feeder['length_m']:g} m · ΔU {feeder['du_pct']:.2f} % (máx. {limites['seccional']:g} %)")
    sistema, freq = board.get("system", ""), int(board.get("frequency_hz") or 50)
    lines = [f"Tension nominal {volt:.0f} V · sistema {sistema} · {freq} Hz", f"Icc en barras {icc:g} kA · FP por defecto {fp:g}",
             f"Potencia activa de circuitos raiz: {p_total:.1f} kW", f"Suma aritmetica de Ib de circuitos raiz: {ib_total:.0f} A", feeder_text,
             "In >= 1,25·Ib (motores) o >= Ib (resto), serie comercial", "Icu = Icc redondeada al comercial superior",
             f"S por Iz >= In (AEA 771.16, segun el metodo de cada circuito), ΔU <= {limites['terminal']:g} % ({limites['motor']:g} % motores)"]
    note = ("Notas: calculo referencial para revision del diagrama (no reemplaza la memoria de calculo). Ib segun CARGA/UNIDAD y FP; In comercial >= 1,25·Ib en motores y >= Ib en el resto; "
            f"Icu >= Icc; Iz segun AEA 90364-7-771; limite {limites['terminal']:g} % ({limites['motor']:g} % motores); PE segun AEA 90364 (S/2 si S>35 mm²).")
    return {"bar": {"in_a": bar_in, "ib_total_a": ib_total, "p_total_kw": round(p_total, 3), "voltage_v": volt}, "feeder": feeder, "checks": checks, "differential_missing": pending,
            "lines": lines, "note": note, "rcd_ma": float(rcd_ma)}
