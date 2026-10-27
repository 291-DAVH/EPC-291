"""What the calculation of a board gave: the table, the upstream board it hangs from and the memo."""

from pathlib import Path
from typing import Optional

from epc.core.fsutil import read_json
from epc.core.hashing import sha256_json
from epc.modules.sld import lengths, repository
from epc.modules.sld.boards import _resolve, status


def _description(tag: str, saved: dict, detail: dict) -> str:
    """The description of a circuit: the one in the saved data, or the one the calculation carried (a group the standard solutions added has none saved)."""
    return saved.get(tag) or detail.get(tag, {}).get("descripcion", "")


def calculation(d: Path, bid: str = "") -> dict:
    """Result of the last calculation: one row per circuit (what the diagram was drawn from) and the criteria that governed it."""
    bid = _resolve(d, bid)
    st = status(d, bid)
    name = st.get("name")
    base = repository.pkg(d) / "calc"
    calc = read_json(base / f"{name}_dimensionado.json", None) if name else None
    if not calc:
        return {"rows": [], "criteria": None}
    detail = read_json(base / f"{name}_dimensionado_detalle.json", {}) or {}
    crit = read_json(base / f"{name}_criterios.json", {}) or {}
    saved = (repository.load_input(d, bid) if bid else None) or {"circuits": []}
    desc = {c["tag"]: c.get("description", "") for c in saved.get("circuits", [])}
    rows = [{"tag": t, "description": _description(t, desc, detail), **v, **{k: detail.get(t, {}).get(k) for k in ("tipo", "limite_pct", "du_propia_pct", "iz_a", "cumple")}} for t, v in calc.items()]
    return {"rows": rows, "criteria": {"limits_pct": crit.get("limites_pct"), "conductor": crit.get("conductor"), "rcd_ma": crit.get("rcd_ma")}}


def _hash(d: Path, data: dict) -> str:
    """Fingerprint of what a calculation was made from: the board data and the document of standard solutions in force for the project (a change in either makes the memo stale)."""
    return sha256_json([data, repository.solutions_digest(d)])[:16]


def _upstream(d: Path, board: dict) -> Optional[dict]:
    """The circuit of the upstream board that feeds this one (its cable, protection and drop), when that board was already calculated."""
    up, tag = (board.get("supplied_from") or "").strip(), (board.get("supply_tag") or "").strip()
    if not up or up not in repository.board_ids(d):
        return None
    data = repository.load_input(d, up) or {}
    name = ((data.get("board") or {}).get("name")) or up
    info = {"board": name, "tag": tag, "length_m": None}
    st = repository.load_status(d, up)
    calc = read_json(repository.pkg(d) / "calc" / f"{st.get('name')}_dimensionado.json", {}) if st.get("name") else {}
    detail = read_json(repository.pkg(d) / "calc" / f"{st.get('name')}_dimensionado_detalle.json", {}) if st.get("name") else {}
    if tag and tag in calc:
        circ = next((c for c in data.get("circuits", []) if c["tag"] == tag), {})
        info.update(calc[tag], length_m=circ.get("length_m"), ruta=(detail.get(tag) or {}).get("ruta") or [], ruta_limitante=(detail.get(tag) or {}).get("ruta_limitante"))
    return info


def _outdated(st: dict, d: Path, saved: Optional[dict]) -> bool:
    """Whether the last generation (memo or diagram) was made from other data than the board has now. It does not depend on the memo file being there: files generated before the memo existed are told apart too."""
    return bool(saved) and st.get("state") == "done" and bool(st.get("input_hash")) and st["input_hash"] != _hash(d, lengths.apply(d, saved))


def memo(d: Path, bid: str = "") -> dict:
    """Calculation memo and summary of the board (what the last calculation produced) and whether the data changed since."""
    bid = _resolve(d, bid)
    st = status(d, bid)
    saved = repository.load_input(d, bid) if bid else None
    base = repository.pkg(d) / "calc"
    m = read_json(base / f"{st.get('name')}_memoria.json", None) if st.get("name") and st.get("state") == "done" else None
    if not m or not saved:
        return {"available": False, "stale": False, "outdated": _outdated(st, d, saved), "memo": None, "files": []}
    stale = st.get("input_hash") != _hash(d, lengths.apply(d, saved))                # a change in the plan that alters a length makes the memo stale
    files = [f for f in (f"docs/{st['name']}_MC.md", f"docs/{st['name']}_SP.md") if (repository.pkg(d) / f).is_file()]
    return {"available": True, "stale": stale, "outdated": stale, "memo": m, "files": files, "finished": st.get("finished")}
