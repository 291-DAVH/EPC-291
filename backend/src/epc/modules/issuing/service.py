import csv
import datetime as dt
import io
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from epc.core import clock
from epc.core.errors import Conflict, Failure, Invalid, NotFound
from epc.core.fsutil import is_inside
from epc.modules.deliverables import public as deliverables
from epc.modules.engineering import public as engineering
from epc.modules.issuing import repository, texts
from epc.modules.masterdata import public as masterdata
from epc.modules.issuing.models import IssueIn
from epc.modules.projects import public as projects

EMISSIONS = {"ifa": "IFA", "ifc": "IFC", "as-built": "AS-BUILT"}       # client-facing emissions (IFR is internal and never delivered)
CLIENT_REV = re.compile(r"^\d{2}$")
INTERNAL_REV = re.compile(r"^\d{2}\.\d+\.\d+$")


def _allowed_formats() -> set:
    return {k for k, v in deliverables.format_policy().get("formats", {}).items() if v.get("deliver")}


def candidates(d: Path) -> dict:
    """Engineering outputs that can be issued, with the revision each one was last issued in."""
    issued: Dict[str, str] = {}
    for tr in repository.list_transmittals(d):
        for it in tr["items"]:
            issued[it["source"]] = f"{tr['id']} · Rev {tr['client_rev']} ({tr['status']})"
    ok = _allowed_formats()
    items = []
    for c in engineering.issuable(d):
        formats = [f for f in c["files"] if f in ok]
        if formats:
            items.append({"id": c["id"], "name": c["name"], "discipline": c["discipline"], "package": c["package"], "kind": c["kind"],
                          "formats": formats, "pdf_will_be_rendered": c["kind"] == "drawing" and "pdf" not in c["files"], "last_issue": issued.get(c["id"])})
    trs = repository.list_transmittals(d)
    return {"candidates": items, "emissions": list(EMISSIONS), "next_transmittal": f"TR-{repository.next_transmittal_number(d):03d}",
            "transmittals": [{k: t[k] for k in ("id", "emission", "client_rev", "internal_rev", "status", "created", "sent_on")} | {"items": len(t["items"])} for t in trs]}


def _validate(body: IssueIn) -> None:
    e: Dict[str, str] = {}
    if body.emission not in EMISSIONS:
        e["emission"] = "one of " + ", ".join(EMISSIONS)
    if not CLIENT_REV.match(body.client_rev):
        e["client_rev"] = "two digits, e.g. 00"
    if not INTERNAL_REV.match(body.internal_rev):
        e["internal_rev"] = "form 00.R.C, e.g. 00.0.1"
    if not body.items:
        e["items"] = "choose at least one"
    if len(body.notes) > 500:
        e["notes"] = "up to 500 characters"
    if e:
        raise Invalid(e)


def issue(d: Path, body: IssueIn) -> dict:
    _validate(body)
    cands = {c["id"]: c for c in engineering.issuable(d)}
    missing = [i.source for i in body.items if i.source not in cands]
    if missing:
        raise Invalid({"items": f"not available: {', '.join(missing)}"})
    if len({i.source for i in body.items}) != len(body.items):
        raise Invalid({"items": "duplicated"})
    ok = _allowed_formats()
    meta = projects.read_meta(d)
    project_code = meta.get("project_code") or d.name
    number = repository.next_transmittal_number(d)
    tr_id = f"TR-{number:03d}"
    folder_rel = f"{body.emission}/{tr_id}_Rev{body.client_rev}"
    created = clock.now_local()
    plugins = repository.plugins_locked(d)
    engine = repository.engine_version()
    stamp = {"CLIENT_REV": f"Rev {body.client_rev}", "INTERNAL_REV": body.internal_rev, "TRANSMITTAL": tr_id, "EMISSION": EMISSIONS[body.emission],
             "ISSUED_ON": created[:10], "ENGINE_VERSION": engine, "PLUGINS": ",".join(f"{k}@{v}" for k, v in sorted(plugins.items()))}
    base = d / "deliverables"
    written: List[Path] = []
    tr_items, new_items = [], []
    try:
        for it in body.items:
            c = cands[it.source]
            disc = c["discipline"]
            prefix = f"{project_code}-{disc[:3].upper()}-"
            code = f"{prefix}{deliverables.next_code_number(d, prefix) + len([x for x in new_items if x['code'].startswith(prefix)]):03d}"
            target = base / folder_rel / disc
            target.mkdir(parents=True, exist_ok=True)
            files: List[dict] = []
            for fmt, src in c["files"].items():
                if fmt not in ok:
                    continue
                dst = target / f"{code}.{fmt}"
                if fmt == "dxf":
                    repository.stamp_dxf(src, dst, stamp)
                else:
                    shutil.copy2(src, dst)
                written.append(dst)
                files.append({"format": fmt, "rel": dst.relative_to(base).as_posix(), "sha256": repository.sha256(dst)})
            if c["kind"] == "drawing" and not any(f["format"] == "pdf" for f in files):      # the PDF is rendered from the stamped DXF at issue time
                dxf = target / f"{code}.dxf"
                pdf = target / f"{code}.pdf"
                repository.render_pdf(dxf, pdf)
                written.append(pdf)
                files.append({"format": "pdf", "rel": pdf.relative_to(base).as_posix(), "sha256": repository.sha256(pdf)})
            primary = next(f for f in files if f["format"] == ("dxf" if c["kind"] == "drawing" else files[0]["format"]))
            name = (it.name or c["name"]).strip()[:200] or c["name"]
            new_items.append({"code": code, "name": name, "discipline": disc, "format": primary["format"], "revision": f"Rev {body.client_rev}", "status": "in_review",
                              "file": primary["rel"], "sha256": primary["sha256"], "source": it.source, "transmittal": tr_id, "emission": EMISSIONS[body.emission]})
            tr_items.append({"code": code, "name": name, "discipline": disc, "source": it.source, "files": files})
    except Exception as exc:                                       # leave nothing half-issued
        for f in written:
            f.unlink(missing_ok=True)
        raise Failure(f"could not prepare the issue: {exc}")
    registered = deliverables.add_items(d, new_items)
    for r, t in zip(registered, tr_items):
        t["deliverable_id"] = r["id"]
    tr = {"schema_version": "1.0", "id": tr_id, "emission": body.emission, "client_rev": body.client_rev, "internal_rev": body.internal_rev, "status": "prepared",
          "created": created, "sent_on": None, "notes": body.notes.strip(), "engine_version": engine, "plugins": plugins, "items": tr_items}
    repository.save_transmittal(d, tr)
    repository.write_ledger(d, {"event": "issue_prepared", "at": created, "transmittal": tr_id, "emission": body.emission, "client_rev": body.client_rev,
                                "internal_rev": body.internal_rev, "files": [f["rel"] for t in tr_items for f in t["files"]]})
    return tr


def mark_sent(d: Path, tr_id: str) -> dict:
    tr = repository.load_transmittal(d, tr_id) if re.match(r"^TR-\d+$", tr_id) else None
    if not tr:
        raise NotFound("transmittal not found")
    if tr["status"] == "sent":
        raise Conflict({"status": "already sent"})
    today = dt.date.today().isoformat()
    deliverables.set_delivered(d, [t["deliverable_id"] for t in tr["items"]], today)
    tr.update(status="sent", sent_on=today)
    repository.save_transmittal(d, tr)
    repository.write_ledger(d, {"event": "issue_sent", "at": clock.now_local(), "transmittal": tr_id})
    return tr


def get(d: Path, tr_id: str) -> dict:
    tr = repository.load_transmittal(d, tr_id) if re.match(r"^TR-\d+$", tr_id) else None
    if not tr:
        raise NotFound("transmittal not found")
    return tr


# ---- delivery documents: package (ZIP), transmittal document (PDF) and the email message ----
def _project_info(d: Path) -> dict:
    meta = projects.read_meta(d)
    return {"name": meta.get("project_name") or meta.get("project_code") or d.name, "code": meta.get("project_code") or d.name,
            "client": meta.get("client", ""), "locale": meta.get("locale", "es")}


def _issuer(d: Path) -> str:
    try:
        return (masterdata.issuer_name(d) or "").strip()      # the company this project issues in the name of
    except Exception:                                   # noqa: BLE001 - no master data yet: the generic wording is used
        return ""


def _lang(d: Path, lang: Optional[str]) -> str:
    return lang if lang in texts.T else texts.lang_of(_project_info(d)["locale"])


def package_name(d: Path, tr: dict) -> str:
    return f"{_project_info(d)['code']}_{EMISSIONS[tr['emission']]}_{tr['id']}_Rev{tr['client_rev']}.zip"


def message(d: Path, tr_id: str, lang: Optional[str] = None) -> dict:
    tr = get(d, tr_id)
    return texts.email(_lang(d, lang), tr, _project_info(d), package_name(d, tr), _issuer(d))


def transmittal_pdf(d: Path, tr_id: str, lang: Optional[str] = None) -> Tuple[Path, str]:
    tr = get(d, tr_id)
    out = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    out.close()
    try:
        repository.render_transmittal_pdf(texts.document(_lang(d, lang), tr, _project_info(d), _issuer(d)), Path(out.name))
    except Exception as exc:
        Path(out.name).unlink(missing_ok=True)
        raise Failure(str(exc))
    return Path(out.name), f"TRANSMITTAL_{tr['id']}_Rev{tr['client_rev']}.pdf"


def package(d: Path, tr_id: str, lang: Optional[str] = None) -> Tuple[Path, str]:
    """ZIP to attach to the email: the files of the transmittal (folder structure kept), the transmittal document and INDICE.csv."""
    tr = get(d, tr_id)
    base = d / "deliverables"
    pdf, pdf_name = transmittal_pdf(d, tr_id, lang)
    index = io.StringIO()
    w = csv.writer(index, delimiter=";")
    w.writerow(["codigo", "nombre", "disciplina", "revision", "formato", "archivo", "sha256"])
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    tmp.close()
    try:
        with zipfile.ZipFile(tmp.name, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(pdf, pdf_name)
            for it in tr["items"]:
                for f in it["files"]:
                    path = base / f["rel"]
                    if not is_inside(base, f["rel"]):
                        raise Failure(f"file missing from the transmittal: {f['rel']}")
                    z.write(path, f["rel"])
                    w.writerow([it["code"], it["name"], it.get("discipline") or it["source"].split("/")[0], f"Rev {tr['client_rev']}", f["format"], f["rel"], f["sha256"]])
            z.writestr("INDICE.csv", "﻿" + index.getvalue())
    except Exception:
        Path(tmp.name).unlink(missing_ok=True)
        raise
    finally:
        pdf.unlink(missing_ok=True)
    return Path(tmp.name), package_name(d, tr)

