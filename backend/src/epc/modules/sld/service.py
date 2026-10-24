import datetime as dt
import re
import threading
from pathlib import Path
from typing import Dict, Optional

from epc.core.errors import Conflict, Invalid, NotFound
from epc.core.fsutil import read_json
from epc.modules.engineering import public as engineering
from epc.modules.masterdata import public as masterdata
from epc.modules.projects import public as projects
from epc.modules.sld import repository
from epc.modules.sld.models import Board, Circuit, SldIn, Titleblock

UNITS = ("A", "W", "kW", "MW", "VA", "kVA", "MVA", "HP")
TOPOLOGIES = ("single", "dol", "dol_ol", "star_delta", "softstarter", "vfd", "dol_rcd", "manual")
PHASES = ("3F", "1F", "3F+N")
KINDS = ("auto", "mcb", "mccb", "mccb_motorized", "rcbo", "rccb")
CABLE_TYPES = ("tetra_sep", "tetra_inc", "unifilar")
SYSTEMS = ("TN-S", "TN-C-S", "IT")
OPTIONS = {"units": UNITS, "topologies": TOPOLOGIES, "phases": PHASES, "kinds": KINDS, "cable_types": CABLE_TYPES, "systems": SYSTEMS}
MAX_CIRCUITS = 150
_LOCKS: Dict[str, threading.Lock] = {}


def validate(data: dict) -> Dict[str, str]:
    e: Dict[str, str] = {}
    b = data["board"]
    if not b["name"].strip():
        e["board.name"] = "required"
    if not 50 <= b["voltage_v"] <= 1000:
        e["board.voltage_v"] = "between 50 and 1000 V"
    if b["system"] not in SYSTEMS:
        e["board.system"] = "one of " + ", ".join(SYSTEMS)
    if not 0.1 <= b["icc_ka"] <= 100:
        e["board.icc_ka"] = "between 0.1 and 100 kA"
    if not 0.1 <= b["fp_default"] <= 1:
        e["board.fp_default"] = "between 0.1 and 1"
    if b["frequency_hz"] not in (50, 60):
        e["board.frequency_hz"] = "50 or 60"
    if b["feeder_length_m"] < 0:
        e["board.feeder_length_m"] = "must be >= 0"
    cs = data["circuits"]
    if not cs:
        e["circuits"] = "at least one circuit"
    if len(cs) > MAX_CIRCUITS:
        e["circuits"] = f"up to {MAX_CIRCUITS} circuits"
    tags = [c["tag"].strip() for c in cs]
    parents = {c["parent_tag"].strip() for c in cs if c["parent_tag"].strip()}
    for i, c in enumerate(cs):
        t = c["tag"].strip()
        k = f"circuit:{t or i + 1}"
        if not t or "," in t:
            e[f"{k}.tag"] = "required, without commas"
        elif tags.count(t) > 1:
            e[f"{k}.tag"] = "duplicated"
        if c["unit"] not in UNITS:
            e[f"{k}.unit"] = "one of " + ", ".join(UNITS)
        if c["topology"] not in TOPOLOGIES:
            e[f"{k}.topology"] = "invalid"
        if c["phase"] not in PHASES:
            e[f"{k}.phase"] = "one of " + ", ".join(PHASES)
        if c["kind"] not in KINDS:
            e[f"{k}.kind"] = "invalid"
        if c["cable_type"] not in CABLE_TYPES:
            e[f"{k}.cable_type"] = "invalid"
        if c["load"] is None and t not in parents:
            e[f"{k}.load"] = "required (a parent device may leave it empty)"
        if c["load"] is not None and c["load"] <= 0:
            e[f"{k}.load"] = "must be > 0"
        if c["length_m"] < 0:
            e[f"{k}.length_m"] = "must be >= 0"
        for fld in ("fp", "efficiency"):
            if c[fld] is not None and not 0 < c[fld] <= 1:
                e[f"{k}.{fld}"] = "between 0 and 1"
        p = c["parent_tag"].strip()
        if p and (p == t or p not in tags):
            e[f"{k}.parent_tag"] = "unknown or self parent"
    if not e:                                                         # cycles
        par = {c["tag"].strip(): c["parent_tag"].strip() for c in cs}
        for t in par:
            seen, cur = set(), t
            while cur and cur in par:
                if cur in seen:
                    e["circuits"] = f"parent cycle at {t}"
                    break
                seen.add(cur)
                cur = par[cur]
    return e


def _name(board_name: str) -> str:
    """Base name of the outputs: SLD_<base>.*, MLD_<base>.* and <base>_dimensionado*.json."""
    return re.sub(r"[^A-Za-z0-9]+", "-", board_name).strip("-")[:30] or "TABLERO"


def _resolve(d: Path, bid: str) -> str:
    """The board asked for; without one, the first board of the project ("" when the project has none yet)."""
    ids = repository.board_ids(d)
    if bid:
        if bid not in ids:
            raise NotFound("board not found")
        return bid
    return ids[0] if ids else ""


def _blank(d: Path, name: str = "") -> dict:
    meta = projects.read_meta(d)
    volt = engineering.criterion_value(d, "nominal_voltage_v") or 380
    org = masterdata.organization()
    cl = masterdata.client(meta.get("client_code", "")) or {}
    return {"board": Board(voltage_v=volt, project=meta.get("project_code", ""), name=name).model_dump(), "circuits": [],
            "titleblock": Titleblock(company=org.get("legal_name", ""), company_cuit=org.get("tax_id", ""),
                                     client=cl.get("name") or meta.get("client", ""), client_cuit=cl.get("tax_id", ""),
                                     description=meta.get("project_name", "")).model_dump()}


def view(d: Path, bid: str = "") -> dict:
    bid = _resolve(d, bid)
    saved = repository.load_input(d, bid) if bid else None
    meta = projects.read_meta(d)
    if saved:
        data = {k: saved[k] for k in ("board", "circuits", "titleblock") if k in saved}
        data.setdefault("titleblock", Titleblock().model_dump())
        data["board"] = {**Board().model_dump(), **data["board"]}
    else:
        data = _blank(d)
    return {"input": data, "saved": bool(saved), "board_id": bid, "options": OPTIONS, "status": status(d, bid),
            "boards": [{"id": b["id"], "name": b["name"]} for b in boards(d)],
            "people": [p["name"] for p in masterdata.people()],
            "logos": {"company": masterdata.logo_path("organization") is not None, "client": masterdata.logo_path("client-" + meta.get("client_code", "-")) is not None}}


def boards(d: Path) -> list:
    """The boards of the project with their state; each one has its own data, calculation, memo and diagrams."""
    out = []
    for bid in repository.board_ids(d):
        data = repository.load_input(d, bid) or {}
        b = {**Board().model_dump(), **(data.get("board") or {})}
        st = repository.load_status(d, bid)
        out.append({"id": bid, "name": b["name"] or bid, "voltage_v": b["voltage_v"], "system": b["system"], "icc_ka": b["icc_ka"], "circuits": len(data.get("circuits") or []),
                    "supplied_from": b["supplied_from"], "supply_tag": b["supply_tag"], "state": st.get("state", "idle"), "finished": st.get("finished")})
    return out


def _supply_errors(d: Path, bid: str, board: dict) -> Dict[str, str]:
    up = (board.get("supplied_from") or "").strip()
    if not up:
        return {}
    ids = repository.board_ids(d)
    if up not in ids or up == bid:
        return {"board.supplied_from": "unknown board or itself"}
    seen, cur = {bid}, up                                                   # an upstream chain must not come back to this board
    while cur:
        if cur in seen:
            return {"board.supplied_from": "the supply chain would be a loop"}
        seen.add(cur)
        cur = ((repository.load_input(d, cur) or {}).get("board") or {}).get("supplied_from", "")
    tag = (board.get("supply_tag") or "").strip()
    tags = {c["tag"] for c in (repository.load_input(d, up) or {}).get("circuits", [])}
    if tag and tags and tag not in tags:
        return {"board.supply_tag": "that circuit does not exist in the upstream board"}
    return {}


def save(d: Path, body: SldIn, bid: str = "") -> dict:
    data = body.model_dump()
    for c in data["circuits"]:
        c["tag"], c["parent_tag"] = c["tag"].strip(), c["parent_tag"].strip()
    bid = _resolve(d, bid)
    errors = validate(data)
    errors.update(_supply_errors(d, bid, data["board"]))
    if errors:
        raise Invalid(errors)
    if not bid:
        bid = repository.new_id(d, data["board"]["name"])
    repository.save_input(d, bid, data)
    return view(d, bid)


def create_board(d: Path, name: str, supplied_from: str = "", supply_tag: str = "") -> dict:
    name = (name or "").strip()
    if not name or len(name) > 60:
        raise Invalid({"name": "required, up to 60 characters"})
    if name.lower() in {b["name"].lower() for b in boards(d)}:
        raise Conflict({"name": "a board with that name already exists"})
    data = _blank(d, name)
    data["board"].update(supplied_from=supplied_from.strip(), supply_tag=supply_tag.strip())
    errors = _supply_errors(d, "", data["board"])
    if errors:
        raise Invalid(errors)
    bid = repository.new_id(d, name)
    repository.save_input(d, bid, data)                                    # a draft: it has no circuits yet, so it cannot be generated until they are added
    return view(d, bid)


def remove_board(d: Path, bid: str) -> list:
    bid = _resolve(d, bid)
    if not bid:
        raise NotFound("board not found")
    if any(b["supplied_from"] == bid for b in boards(d)):
        raise Conflict({"board": "another board is supplied from this one: change its supply first"})
    if repository.load_status(d, bid).get("state") == "running":
        raise Conflict({"status": "a generation is running"})
    repository.delete_board(d, bid)
    return boards(d)


def example() -> dict:
    ex = repository.example_data()
    return {"board": Board(**ex["board"]).model_dump(), "circuits": [Circuit(**c).model_dump() for c in ex["circuits"]]}


def status(d: Path, bid: str = "") -> dict:
    bid = _resolve(d, bid)
    return repository.load_status(d, bid) if bid else {"state": "idle", "outputs": [], "log": []}


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
    rows = [{"tag": t, "description": desc.get(t, ""), **v, **{k: detail.get(t, {}).get(k) for k in ("tipo", "limite_pct", "du_propia_pct", "iz_a", "cumple")}} for t, v in calc.items()]
    return {"rows": rows, "criteria": {"limits_pct": crit.get("limites_pct"), "conductor": crit.get("conductor"), "rcd_ma": crit.get("rcd_ma")}}


def _hash(data: dict) -> str:
    import hashlib
    import json
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


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
    if tag and tag in calc:
        circ = next((c for c in data.get("circuits", []) if c["tag"] == tag), {})
        info.update(calc[tag], length_m=circ.get("length_m"))
    return info


def memo(d: Path, bid: str = "") -> dict:
    """Calculation memo and summary of the board (what the last calculation produced) and whether the data changed since."""
    bid = _resolve(d, bid)
    st = status(d, bid)
    saved = repository.load_input(d, bid) if bid else None
    base = repository.pkg(d) / "calc"
    m = read_json(base / f"{st.get('name')}_memoria.json", None) if st.get("name") and st.get("state") == "done" else None
    if not m or not saved:
        return {"available": False, "stale": False, "memo": None, "files": []}
    stale = st.get("input_hash") != _hash(saved)
    files = [f for f in (f"docs/{st['name']}_MC.md", f"docs/{st['name']}_SP.md") if (repository.pkg(d) / f).is_file()]
    return {"available": True, "stale": stale, "memo": m, "files": files, "finished": st.get("finished")}


def _lock(d: Path, bid: str) -> threading.Lock:
    return _LOCKS.setdefault(f"{d.resolve()}::{bid}", threading.Lock())


def _job(d: Path, bid: str, data: dict, name: str, diagrams: str = "sld") -> None:
    prior = repository.load_status(d, bid)
    previous, previous_name = prior.get("outputs", []), prior.get("name")
    st = {"state": "running", "name": name, "started": dt.datetime.now().replace(microsecond=0).isoformat(), "outputs": previous, "log": []}
    repository.save_status(d, bid, st)
    try:
        work = repository.work_dir(d, bid)
        out = work / "out"
        if out.exists():
            import shutil
            shutil.rmtree(out)
        code = projects.read_meta(d).get("client_code", "-")
        logos = {k: p for k, p in (("provider", masterdata.logo_path("organization")), ("client", masterdata.logo_path("client-" + code))) if p}
        criteria = engineering.criteria_values(d)
        res = repository.run_design(work, name, {**data, "upstream": _upstream(d, data["board"]), "validated": engineering.criteria_validated(d)}, criteria, logos, diagrams)
        summary = repository.read_summary(work)
        log = list(summary.get("log", [])) + [f"AVISO {a}" for a in summary.get("avisos", [])]
        if res.returncode != 0 or not summary.get("ok"):
            st.update(state="failed", log=log, error=(summary.get("error") or res.stderr or res.stdout).strip()[-600:])
        else:
            log += repository.render_pdfs(out, "SLD_" + name) if "sld" in diagrams else []
            log += repository.render_pdfs(out, "MLD_" + name) if "mld" in diagrams else []
            st.update(state="done", log=log, outputs=repository.publish(d, out, name, previous, previous_name), name=name, input_hash=_hash(data),
                      calculation={"limits_pct": summary.get("limites_pct"), "conductor": summary.get("conductor"), "non_compliant": summary.get("non_compliant", [])})
    except Exception as exc:                                         # noqa: BLE001 - reported to the user through the status
        st.update(state="failed", error=str(exc)[:600])
    st["finished"] = dt.datetime.now().replace(microsecond=0).isoformat()
    repository.save_status(d, bid, st)


def generate(d: Path, wait: bool = False, diagrams: str = "sld", bid: str = "") -> dict:
    if diagrams not in ("sld", "mld", "sld,mld", "none"):
        raise Invalid({"diagrams": "sld, mld, sld,mld or none (calculation and memo only)"})
    bid = _resolve(d, bid)
    saved = repository.load_input(d, bid) if bid else None
    if not saved:
        raise Invalid({"input": "save the SLD data first"})
    errors = validate(saved)
    if errors:
        raise Invalid(errors)
    if diagrams != "none":                                       # the memo and summary come before the diagram, calculated on the data as they are now
        m = memo(d, bid)
        if not m["available"] or m["stale"]:
            raise Conflict({"memo": "calculate the memo and summary of the board first"})
    lock = _lock(d, bid)
    if not lock.acquire(blocking=False):
        raise Conflict({"status": "a generation is already running"})

    def run():
        try:
            _job(d, bid, saved, _name(saved["board"]["name"]), diagrams)
        finally:
            lock.release()

    repository.save_status(d, bid, {**repository.load_status(d, bid), "state": "running"})        # visible at once: whoever polls next does not read the previous result
    t = threading.Thread(target=run, daemon=True)
    t.start()
    if wait:
        t.join()
    return status(d, bid)
