"""Automatic groups of differentials: the circuits that have no differential of their own are put behind one, as many as are needed.

The rules live in the document of standard solutions (`groups`): which circuits they take (`when`, the same conditions as a solution), how they are split (`by`: circuits of the same type, phase...),
how many circuits (`max_circuits`) and how much current (`max_ib_a`) one differential may serve, and how the group is named. A circuit that already has a differential (its own devices include one) or sits in a group
that was written by hand is left alone. Nothing here draws: it returns the groups, and `apply_rows` adds them to the circuits so that calculation, memo and diagrams see them like any other group.
"""
import copy
from typing import Dict, Iterable, List, Optional

from epc_calc import aea_pipeline as P
from epc_calc import solutions as SOL

DIFFERENTIAL = ("lv_rccb", "lv_rcbo")
BY_KEYS = ("type", "phase", "kind", "topology")


def _tag(pattern: str, n: int, taken: set) -> tuple:
    """(tag, number): the first tag of the pattern, counting from n, that no circuit has."""
    while pattern.format(n=n) in taken:
        n += 1
    return pattern.format(n=n), n


def _candidates(tablero: dict, rows: List[dict], criteria, doc: dict) -> List[dict]:
    """The circuits a group may take: leaves without a parent whose own solution has no differential. Each one with its facts."""
    u, fp_def = float(tablero.get("TENSION_V", 380)), float(tablero.get("FP_DEFAULT", 0.85))
    icc = float(tablero.get("ICC_KA", 10))
    icu = P._primero(P.SERIE_ICU_KA, icc) or P.SERIE_ICU_KA[-1]
    rcd_ma = P.resolver_criterios(criteria)[4]
    parents = {str(r.get("PARENT_TAG") or "").strip() for r in rows}
    out = []
    for row in rows:
        ib = P.corriente_proyecto(row, u, fp_def)
        if ib is None or str(row.get("PARENT_TAG") or "").strip() or row["TAG"] in parents:
            continue
        top = str(row.get("TOPOLOGY") or "single").strip().lower()
        motor = top in P.TOPOLOGIAS_MOTOR
        in_a = P._primero(P.SERIE_IN_A, ib * (P.MARGIN_MOTOR if motor else 1.0)) or P.SERIE_IN_A[-1]
        f = SOL.facts(row["TAG"], str(row.get("DESCRIPCION") or ""), str(row.get("NOTAS") or ""), top, str(row.get("KIND") or "auto").strip().lower() or "auto",
                      str(row.get("FASE") or "3F").strip().upper(), P.type_circuit(row, False), in_a, ib, icu, rcd_ma, False, motor)
        if not any(i["symbol"] in DIFFERENTIAL for i in SOL.resolve(f, doc)["chain"]):
            out.append({"row": row, "facts": f, "ib": ib})
    return out


def _split(items: List[dict], rule: dict) -> List[List[dict]]:
    """Fill groups in order of appearance until one more circuit would pass the circuits or the current the rule allows."""
    groups: List[List[dict]] = []
    for it in items:
        if not groups or len(groups[-1]) >= rule.get("max_circuits", 6) or sum(x["ib"] for x in groups[-1]) + it["ib"] > rule.get("max_ib_a", 40):
            groups.append([])
        groups[-1].append(it)
    return groups


def plan(tablero: dict, rows: List[dict], criteria: Optional[dict] = None, documento: Optional[dict] = None) -> List[dict]:
    """The groups the enabled rules ask for: [{"rule", "tag", "members": [tags], "phase", "type", "ib_a", "description"}], in the order of the first member of each."""
    doc = SOL.resolve_doc(documento)
    rules = [(i, r) for i, r in (doc.get("groups") or {}).items() if r.get("enabled", True)]
    if not rules:
        return []
    pool = _candidates(tablero, rows, criteria, doc)
    taken = {r["TAG"] for r in rows}
    made: List[dict] = []
    for rid, rule in rules:
        mine = [c for c in pool if SOL.matches(rule.get("when", {}), c["facts"])]
        pool = [c for c in pool if c not in mine]
        buckets: Dict[tuple, List[dict]] = {}
        for c in mine:
            buckets.setdefault(tuple(c["facts"][k] for k in rule.get("by", [])), []).append(c)
        n = 1
        for bucket in buckets.values():
            for members in _split(bucket, rule):
                tag, number = _tag(rule["tag"], n, taken)
                taken.add(tag)
                n = number + 1
                f = members[0]["facts"]
                made.append({"rule": rid, "tag": tag, "members": [m["row"]["TAG"] for m in members], "phase": f["phase"], "type": f["type"], "ib_a": round(sum(m["ib"] for m in members), 3),
                             "description": (rule.get("description") or {}).get("es", "Diferencial de grupo").format(n=number, type=f["type"], phase=f["phase"])})
    order = {r["TAG"]: i for i, r in enumerate(rows)}
    return sorted(made, key=lambda g: min(order[t] for t in g["members"]))


def group_row(group: dict) -> dict:
    """The circuit of a group in the form the calculation reads: a differential behind which its members hang (it has no load of its own: it sums theirs)."""
    return {"TAG": group["tag"], "DESCRIPCION": group["description"], "CARGA": None, "UNIDAD_CARGA": "A", "DESTINO": "", "PARENT_TAG": None, "TOPOLOGY": "single", "FASE": group["phase"],
            "LONGITUD_m": 0, "FP": None, "RENDIMIENTO": None, "KIND": "rccb", "NOTAS": "", "CABLE_TIPO": "tetra_sep"}


def apply_rows(rows: Iterable[dict], groups: List[dict]) -> List[dict]:
    """The circuits with the groups added: each group just before its first member, and its members hanging from it."""
    rows = list(rows)
    out: List[dict] = []
    parent = {m: g["tag"] for g in groups for m in g["members"]}
    first = {min(g["members"], key=[r["TAG"] for r in rows].index): g for g in groups}
    for row in rows:
        if row["TAG"] in first:
            out.append(group_row(first[row["TAG"]]))
        out.append({**row, "PARENT_TAG": parent[row["TAG"]]} if row["TAG"] in parent else copy.copy(row))
    return out
