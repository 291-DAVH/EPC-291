"""Generating the drawings of a board in the background and reporting how it is going."""

import threading
from pathlib import Path
from typing import Dict

from epc.core import clock
from epc.core.errors import Conflict, Invalid
from epc.modules.catalogs import public as catalogs
from epc.modules.engineering import public as engineering
from epc.modules.masterdata import public as masterdata
from epc.modules.projects import public as projects
from epc.modules.sld import lengths, repository
from epc.modules.sld.boards import _resolve, status, titleblock
from epc.modules.sld.results import _hash, _upstream, memo
from epc.modules.sld.validation import _name, validate


_LOCKS: Dict[str, threading.Lock] = {}


def _lock(d: Path, bid: str) -> threading.Lock:
    return _LOCKS.setdefault(f"{d.resolve()}::{bid}", threading.Lock())


def _fingerprint(d: Path, data: dict, diagrams: str, prior: dict):
    """What a run says it was made from. A calculation alone does not renew it: the memo and the diagrams of the run before are still of the data they were made from."""
    return prior.get("input_hash") if diagrams == "calc" else _hash(d, data)


def _job(d: Path, bid: str, data: dict, name: str, diagrams: str = "sld") -> None:
    prior = repository.load_status(d, bid)
    previous, previous_name = prior.get("outputs", []), prior.get("name")
    st = {"state": "running", "name": name, "started": clock.now_local(), "outputs": previous, "log": []}
    repository.save_status(d, bid, st)
    try:
        work = repository.work_dir(d, bid)
        out = work / "out"
        if out.exists():
            import shutil
            shutil.rmtree(out)
        code = projects.read_meta(d).get("client_code", "-")
        logos = {k: p for k, p in masterdata.logos(d).items() if p}
        criteria = engineering.criteria_values(d)
        data = lengths.apply(d, data)                                  # the length each circuit uses: the plan's or the board's
        res = repository.run_design(work, name, {**data, "titleblock": titleblock(d, data.get("titleblock")), "upstream": _upstream(d, data["board"]),
                                                 "validated": engineering.criteria_validated(d)}, criteria, logos, diagrams, catalogs.files(d))
        summary = repository.read_summary(work)
        log = list(summary.get("log", [])) + [f"AVISO {a}" for a in summary.get("avisos", [])]
        if res.returncode != 0 or not summary.get("ok"):
            st.update(state="failed", log=log, error=(summary.get("error") or res.stderr or res.stdout).strip()[-600:])
        else:
            log += repository.render_pdfs(out, "SLD_" + name) if "sld" in diagrams else []
            log += repository.render_pdfs(out, "MLD_" + name) if "mld" in diagrams else []
            st.update(state="done", log=log, outputs=repository.publish(d, out, name, previous, previous_name, exact=diagrams == "calc"), name=name, input_hash=_fingerprint(d, data, diagrams, prior),
                      calculation={"limits_pct": summary.get("limites_pct"), "conductor": summary.get("conductor"), "non_compliant": summary.get("non_compliant", [])})
    except Exception as exc:                                         # noqa: BLE001 - reported to the user through the status
        st.update(state="failed", error=str(exc)[:600])
    st["finished"] = clock.now_local()
    repository.save_status(d, bid, st)


def generate(d: Path, wait: bool = False, diagrams: str = "sld", bid: str = "") -> dict:
    if diagrams not in ("sld", "mld", "sld,mld", "none", "calc"):
        raise Invalid({"diagrams": "sld, mld, sld,mld, none (calculation and memo only) or calc (the calculation alone)"})
    bid = _resolve(d, bid)
    saved = repository.load_input(d, bid) if bid else None
    if not saved:
        raise Invalid({"input": "save the SLD data first"})
    errors = validate(saved)
    if errors:
        raise Invalid(errors)
    if diagrams not in ("none", "calc"):                         # the memo and summary come before the diagram, calculated on the data as they are now
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
