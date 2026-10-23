import datetime as dt
import re
import threading
from pathlib import Path
from typing import Dict

from epc.core.errors import Conflict, Invalid
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


def view(d: Path) -> dict:
    saved = repository.load_input(d)
    meta = projects.read_meta(d)
    if saved:
        data = {k: saved[k] for k in ("board", "circuits", "titleblock") if k in saved}
        data.setdefault("titleblock", Titleblock().model_dump())
    else:
        volt = engineering.criterion_value(d, "nominal_voltage_v") or 380
        org = masterdata.organization()
        cl = masterdata.client(meta.get("client_code", "")) or {}
        data = {"board": Board(voltage_v=volt, project=meta.get("project_code", ""), name="").model_dump(), "circuits": [],
                "titleblock": Titleblock(company=org.get("legal_name", ""), company_cuit=org.get("tax_id", ""),
                                         client=cl.get("name") or meta.get("client", ""), client_cuit=cl.get("tax_id", ""),
                                         description=meta.get("project_name", "")).model_dump()}
    return {"input": data, "saved": bool(saved), "options": OPTIONS, "status": status(d),
            "people": [p["name"] for p in masterdata.people()],
            "logos": {"company": masterdata.logo_path("organization") is not None, "client": masterdata.logo_path("client-" + meta.get("client_code", "-")) is not None}}


def save(d: Path, body: SldIn) -> dict:
    data = body.model_dump()
    for c in data["circuits"]:
        c["tag"], c["parent_tag"] = c["tag"].strip(), c["parent_tag"].strip()
    errors = validate(data)
    if errors:
        raise Invalid(errors)
    repository.save_input(d, data)
    return view(d)


def example() -> dict:
    ex = repository.example_data()
    return {"board": Board(**ex["board"]).model_dump(), "circuits": [Circuit(**c).model_dump() for c in ex["circuits"]]}


def status(d: Path) -> dict:
    return repository.load_status(d)


def calculation(d: Path) -> dict:
    """Result of the last calculation: one row per circuit (what the diagram was drawn from) and the criteria that governed it."""
    st = status(d)
    name = st.get("name")
    base = repository.pkg(d) / "calc"
    calc = read_json(base / f"{name}_dimensionado.json", None) if name else None
    if not calc:
        return {"rows": [], "criteria": None}
    detail = read_json(base / f"{name}_dimensionado_detalle.json", {}) or {}
    crit = read_json(base / f"{name}_criterios.json", {}) or {}
    saved = repository.load_input(d) or {"circuits": []}
    desc = {c["tag"]: c.get("description", "") for c in saved.get("circuits", [])}
    rows = [{"tag": t, "description": desc.get(t, ""), **v, **{k: detail.get(t, {}).get(k) for k in ("tipo", "limite_pct", "du_propia_pct", "iz_a", "cumple")}} for t, v in calc.items()]
    return {"rows": rows, "criteria": {"limits_pct": crit.get("limites_pct"), "conductor": crit.get("conductor"), "rcd_ma": crit.get("rcd_ma")}}


def _lock(d: Path) -> threading.Lock:
    return _LOCKS.setdefault(str(d.resolve()), threading.Lock())


def _job(d: Path, data: dict, name: str, diagrams: str = "sld") -> None:
    prior = repository.load_status(d)
    previous, previous_name = prior.get("outputs", []), prior.get("name")
    st = {"state": "running", "name": name, "started": dt.datetime.now().replace(microsecond=0).isoformat(), "outputs": previous, "log": []}
    repository.save_status(d, st)
    try:
        work = repository.work_dir(d)
        out = work / "out"
        if out.exists():
            import shutil
            shutil.rmtree(out)
        code = projects.read_meta(d).get("client_code", "-")
        logos = {k: p for k, p in (("provider", masterdata.logo_path("organization")), ("client", masterdata.logo_path("client-" + code))) if p}
        criteria = engineering.criteria_values(d)
        res = repository.run_design(work, name, data, criteria, logos, diagrams)
        summary = repository.read_summary(work)
        log = list(summary.get("log", [])) + [f"AVISO {a}" for a in summary.get("avisos", [])]
        if res.returncode != 0 or not summary.get("ok"):
            st.update(state="failed", log=log, error=(summary.get("error") or res.stderr or res.stdout).strip()[-600:])
        else:
            log += repository.render_pdfs(out, "SLD_" + name) if "sld" in diagrams else []
            log += repository.render_pdfs(out, "MLD_" + name) if "mld" in diagrams else []
            st.update(state="done", log=log, outputs=repository.publish(d, out, name, previous, previous_name), name=name,
                      calculation={"limits_pct": summary.get("limites_pct"), "conductor": summary.get("conductor"), "non_compliant": summary.get("non_compliant", [])})
    except Exception as exc:                                         # noqa: BLE001 - reported to the user through the status
        st.update(state="failed", error=str(exc)[:600])
    st["finished"] = dt.datetime.now().replace(microsecond=0).isoformat()
    repository.save_status(d, st)


def generate(d: Path, wait: bool = False, diagrams: str = "sld") -> dict:
    if diagrams not in ("sld", "mld", "sld,mld"):
        raise Invalid({"diagrams": "sld, mld or sld,mld"})
    saved = repository.load_input(d)
    if not saved:
        raise Invalid({"input": "save the SLD data first"})
    errors = validate(saved)
    if errors:
        raise Invalid(errors)
    lock = _lock(d)
    if not lock.acquire(blocking=False):
        raise Conflict({"status": "a generation is already running"})

    def run():
        try:
            _job(d, saved, _name(saved["board"]["name"]), diagrams)
        finally:
            lock.release()

    t = threading.Thread(target=run, daemon=True)
    t.start()
    if wait:
        t.join()
    return status(d)
