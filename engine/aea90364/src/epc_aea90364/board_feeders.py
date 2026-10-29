"""Acometidas de un tablero: el o los cables que lo alimentan, dimensionados como cualquier circuito.

Un tablero puede alimentarse desde la red, desde otro tablero que no es parte del proyecto o desde varias fuentes a la vez (red y grupo electrógeno, por ejemplo). Cada acometida lleva sus datos
(fase, largo, instalación, aislación, conductor) y su corriente; si no se da la corriente, es la suma de la de los circuitos de cabecera del tablero (los que no cuelgan de otro), la que debe llevar el cable.
Se calcula con el mismo `aea_pipeline` que los circuitos (Iz ≥ In y caída de tensión del seccional), de modo que una acometida se dimensiona igual que cualquier alimentador.

NORMA DE REFERENCIA
    AEA 90364-7-771 (los mismos criterios que los circuitos del tablero).  [VERIFICAR]
"""
from typing import Dict, List, Optional

from epc_aea90364 import aea_pipeline as P

__version__ = "0.1.0"

#: columnas de instalación que la acometida lleva a la fila del pipeline (vacío: el criterio de diseño del proyecto)
_WIRING = (("METODO", "method"), ("AISLACION", "insulation"), ("MATERIAL", "material"))


def head_current(datos: Dict[str, dict], detalle: Dict[str, dict]) -> float:
    """Ib [A] de la cabecera del tablero: la suma de los circuitos que no cuelgan de otro (un grupo con diferencial ya suma el de sus hijos)."""
    return round(sum(datos[t]["Ib"] for t, d in detalle.items() if not d.get("padre")), 3)


def _row(f: dict, i: int, ib_a: float, board_name: str) -> dict:
    row = {"TAG": str(f.get("name") or "").strip() or f"ACOMETIDA-{i}", "DESCRIPCION": f"ACOMETIDA - TABLERO {board_name}".strip(), "CARGA": ib_a, "UNIDAD_CARGA": "A",
           "LONGITUD_m": float(f.get("length_m") or 0), "FASE": f.get("phase") or "3F", "TOPOLOGY": "single", "KIND": "auto"}
    row.update({col: f[key] for col, key in _WIRING if f.get(key)})
    return row


def _one(tablero: dict, row: dict, criterios: Optional[dict]) -> dict:
    detail: Dict[str, dict] = {}
    datos, avisos = P.calculate(tablero, [row], criterios=criterios, detalle=detail)
    d, r = detail[row["TAG"]], datos[row["TAG"]]
    return {"S_mm2": r["S"], "In": r["In"], "Ib": r["Ib"], "du_pct": r["dU"], "disp": r["disp"], "iz_a": d.get("iz_a"), "limite_pct": d.get("limite_pct"), "cumple": d.get("cumple"),
            "metodo": d.get("metodo"), "aislacion": d.get("aislacion"), "material": d.get("material"), "avisos": list(avisos)}


def calculate(tablero: dict, feeders: List[dict], head_a: float, criterios: Optional[dict] = None, board_name: str = "") -> List[dict]:
    """Una entrada por acometida: lo que se pidió (nombre, fuente, fase, largo, corriente) y lo que dio el cálculo (sección, In, caída, protección, si cumple)."""
    out = []
    for i, f in enumerate(feeders, 1):
        ib_a = float(f.get("load_a") or head_a)
        row = _row(f, i, ib_a, board_name)
        out.append({"name": row["TAG"], "source": str(f.get("source") or "").strip(), "phase": row["FASE"], "length_m": row["LONGITUD_m"], "load_given": bool(f.get("load_a")), **_one(tablero, row, criterios)})
    return out
