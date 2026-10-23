import datetime as dt
import re
import threading
from pathlib import Path
from typing import Dict

from epc.core.errors import Conflict, Invalid
from epc.modules.engineering import public as engineering
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
    return "SLD_" + (re.sub(r"[^A-Za-z0-9]+", "-", board_name).strip("-")[:30] or "TABLERO")


def view(d: Path) -> dict:
    saved = repository.load_input(d)
    meta = projects.read_meta(d)
    if saved:
        data = {k: saved[k] for k in ("board", "circuits", "titleblock") if k in saved}
        data.setdefault("titleblock", Titleblock().model_dump())
    else:
        volt = engineering.criterion_value(d, "nominal_voltage_v") or 380
        data = {"board": Board(voltage_v=volt, project=meta.get("project_code", ""), name="").model_dump(), "circuits": [],
                "titleblock": Titleblock(client=meta.get("client", ""), description=meta.get("project_name", "")).model_dump()}
    return {"input": data, "saved": bool(saved), "options": OPTIONS, "status": status(d)}


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


def _lock(d: Path) -> threading.Lock:
    return _LOCKS.setdefault(str(d.resolve()), threading.Lock())


def _job(d: Path, data: dict, name: str) -> None:
    previous = repository.load_status(d).get("outputs", [])
    st = {"state": "running", "name": name, "started": dt.datetime.now().replace(microsecond=0).isoformat(), "outputs": previous, "log": []}
    repository.save_status(d, st)
    try:
        work = repository.work_dir(d)
        out = work / "out"
        if out.exists():
            import shutil
            shutil.rmtree(out)
        repository.write_excel(work / "input_for_sld.xlsx", data)
        repository.write_titleblock(work / "titleblock", {**data["titleblock"]})
        res = repository.run_generator(work / "input_for_sld.xlsx", out, name, work / "titleblock")
        log = [ln for ln in (res.stdout.splitlines() + res.stderr.splitlines()) if ln.startswith(("OK", "AVISO"))]
        if res.returncode != 0:
            st.update(state="failed", log=log, error=(res.stderr or res.stdout).strip()[-600:])
        else:
            log += repository.render_pdfs(out, name)
            st.update(state="done", log=log, outputs=repository.publish(d, out, name, previous))
    except Exception as exc:                                         # noqa: BLE001 - reported to the user through the status
        st.update(state="failed", error=str(exc)[:600])
    st["finished"] = dt.datetime.now().replace(microsecond=0).isoformat()
    repository.save_status(d, st)


def generate(d: Path, wait: bool = False) -> dict:
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
            _job(d, saved, _name(saved["board"]["name"]))
        finally:
            lock.release()

    t = threading.Thread(target=run, daemon=True)
    t.start()
    if wait:
        t.join()
    return status(d)
