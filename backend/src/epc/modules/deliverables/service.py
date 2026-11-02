"""Deliverables of a project: list, safe downloads, counters used by dashboards."""
import csv
import io
import re
import tempfile
import zipfile
from pathlib import Path
from typing import List, Optional, Tuple

from epc.core import ids
from epc.core.config import settings
from epc.core.errors import Invalid, NotFound, first_or_404
from epc.core.fsutil import is_inside, read_json, safe_file, today
from epc.core.hashing import sha256_file
from epc.modules.deliverables import repository
from epc.modules.projects import public as projects


# The kinds of document in the order engineering develops them (the calculation first, the drawings that come from it after), and the disciplines in the order they usually work.
DOC_TYPES = (("memo", r"(.+)_MC"), ("summary", r"(.+)_SP"), ("lighting", r"LIGHTING_(.+)"), ("sld", r"SLD_(.+)"), ("mld", r"MLD_(.+)"), ("layout", r"PLAN_(.+)"))
DISCIPLINE_ORDER = ("civil", "mechanical", "electrical", "instrumentation", "hvac", "fire", "telecom")


def document_of(item: dict) -> dict:
    """What the deliverable is, for people: its kind of document (`doc_type`), what it is about (`subject`) and its place in the sequence of development (`order`).
    A name the person typed at issue time that does not follow the file name stays as it is (`doc_type` is "other")."""
    name = str(item.get("name") or "")
    kind, subject = "other", name
    for key, pattern in DOC_TYPES:
        m = re.fullmatch(pattern, name)
        if m:
            kind, subject = key, m.group(1)
            break
    disc = str(item.get("discipline") or "")
    rank = DISCIPLINE_ORDER.index(disc) if disc in DISCIPLINE_ORDER else len(DISCIPLINE_ORDER)
    step = [k for k, _ in DOC_TYPES].index(kind) if kind != "other" else len(DOC_TYPES)
    return {"doc_type": kind, "subject": subject, "order": rank * 100 + step}


def list_items(d: Path) -> list:
    base, now = repository.deliverables_dir(d), today().isoformat()
    out = []
    for x in repository.read_items(d):
        f = x.get("file")
        ok = bool(f and is_inside(base, f))
        out.append({**x, **document_of(x), "downloadable": ok, "formats": _formats(base, x) if ok else [],
                    "overdue": x.get("status") != "delivered" and bool(x.get("due")) and x["due"] < now})
    return sorted(out, key=lambda x: (x["order"], x["subject"].lower(), x.get("revision", "")))


def _deliverable_exts() -> set:
    """Extensions allowed to leave the workspace (policy `deliver: true`); .svg and the like never appear."""
    return {"." + k for k, v in format_policy().get("formats", {}).items() if v.get("deliver")}


def _alternatives(base: Path, file: str) -> List[Path]:
    """Same-name files next to the primary one in other deliverable formats (e.g. the .pdf of a .dxf drawing)."""
    p = (base / file)
    return [s for s in sorted(p.parent.glob(p.stem + ".*")) if s != p and s.suffix.lower() in _deliverable_exts() and is_inside(base, s.relative_to(base).as_posix())]


def _formats(base: Path, item: dict) -> List[str]:
    primary = Path(item["file"]).suffix.lstrip(".").lower() or item.get("format", "")
    return [primary] + [s.suffix.lstrip(".").lower() for s in _alternatives(base, item["file"])]


def file_for(d: Path, item_id: str, fmt: Optional[str] = None) -> Tuple[Path, str]:
    item = next((x for x in repository.read_items(d) if x.get("id") == item_id), None)
    if not item or not item.get("file"):
        raise NotFound("file not found")
    base = repository.deliverables_dir(d)
    path = safe_file(base, item["file"])
    ext = path.suffix.lstrip(".").lower()
    if fmt and fmt.lower() != ext:
        alt = first_or_404((s for s in _alternatives(base, item["file"]) if s.suffix.lstrip(".").lower() == fmt.lower()), "format not available")
        return alt, f"{item.get('code', item_id)}.{fmt.lower()}"
    return path, f"{item.get('code', item_id)}.{item.get('format', ext)}"


def counts(d: Path) -> dict:
    items, now = repository.read_items(d), today().isoformat()
    return {"total": len(items), "delivered": sum(1 for x in items if x.get("status") == "delivered"),
            "overdue": sum(1 for x in items if x.get("status") != "delivered" and x.get("due") and x["due"] < now)}


def due_soon(d: Path, limit_iso: str) -> int:
    return sum(1 for x in repository.read_items(d) if x.get("status") != "delivered" and x.get("due") and x["due"] <= limit_iso)


def format_policy() -> dict:
    return read_json(settings.schemas_dir / "deliverable-policy.json", {"formats": {}})


# ---- packages (ZIP of what was delivered) ----
REV_RE = re.compile(r"_(Rev\d+)$")


def _delivered_files(d: Path) -> List[dict]:
    """One entry per file that was delivered (primary and alternative formats), with its group (emission/transmittal_Rev)."""
    base = repository.deliverables_dir(d)
    out = []
    for x in repository.read_items(d):
        f = x.get("file")
        if x.get("status") != "delivered" or not f or not is_inside(base, f):
            continue
        parts = Path(f).parts
        group = "/".join(parts[:2]) if len(parts) >= 3 else ""
        for p in [base / f] + _alternatives(base, f):
            rel = p.relative_to(base).as_posix()
            out.append({"item": x, "path": p, "rel": rel, "group": group})
    return out


def _group_info(group: str) -> dict:
    emission, _, tr = group.partition("/")
    m = REV_RE.search(tr)
    return {"id": group, "emission": emission.upper(), "transmittal": REV_RE.sub("", tr), "rev": m.group(1) if m else ""}


def packages(d: Path) -> dict:
    files = _delivered_files(d)
    groups = {}
    for f in files:
        if f["group"]:
            groups.setdefault(f["group"], 0)
            groups[f["group"]] += 1
    revs = [m.group(1) for g in groups if (m := REV_RE.search(g))]
    return {"count": len(files), "rev": max(revs) if revs else "Rev00",
            "groups": [{**_group_info(g), "count": n} for g, n in sorted(groups.items())]}


def package_zip(d: Path, group: Optional[str] = None) -> Tuple[Path, str]:
    """ZIP with the delivered files (folder structure kept) and an INDICE.csv. `group` limits it to one transmittal."""
    files = _delivered_files(d)
    info = packages(d)
    if group:
        if group not in {g["id"] for g in info["groups"]}:
            raise Invalid({"group": "unknown package"})
        files = [f for f in files if f["group"] == group]
    if not files:
        raise NotFound("nothing delivered yet")
    meta = projects.read_meta(d)
    code = meta.get("project_code") or d.name
    if group:
        g = _group_info(group)
        name = f"{code}_{g['emission']}_{g['transmittal']}_{g['rev']}.zip"
    else:
        name = f"{code}_Paquete_{info['rev']}.zip"
    index = io.StringIO()
    w = csv.writer(index, delimiter=";")
    w.writerow(["codigo", "nombre", "disciplina", "revision", "formato", "fecha_entrega", "archivo", "sha256"])
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    tmp.close()
    with zipfile.ZipFile(tmp.name, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(files, key=lambda f: f["rel"]):
            z.write(f["path"], f["rel"])
            it = f["item"]
            w.writerow([it.get("code", ""), it.get("name", ""), it.get("discipline", ""), it.get("revision", ""), f["path"].suffix.lstrip("."),
                        it.get("delivered_on", ""), f["rel"], sha256_file(f["path"])])
        z.writestr("INDICE.csv", "\ufeff" + index.getvalue())
    return Path(tmp.name), name


# ---- registering issued deliverables (used by the issuing module through public.py) ----
def add_items(d: Path, new: List[dict]) -> List[dict]:
    """Append deliverables (ids ENT-nnn are assigned here) and return them."""
    items = repository.read_items(d)
    n = ids.max_seq(items, "ENT-")
    out = []
    for it in new:
        n += 1
        out.append({"id": f"ENT-{n:03d}", **it})
    repository.write_items(d, items + out)
    return out


def next_code_number(d: Path, prefix: str) -> int:
    """Next number for deliverable codes that start with `prefix` (e.g. 'P-1-ELE-')."""
    nums = [int(m.group(1)) for x in repository.read_items(d) if (m := re.match(re.escape(prefix) + r"(\d+)$", str(x.get("code", ""))))]
    return max(nums, default=0) + 1


def set_delivered(d: Path, item_ids: List[str], date_iso: str) -> None:
    items = repository.read_items(d)
    for x in items:
        if x.get("id") in item_ids:
            x["status"], x["delivered_on"] = "delivered", date_iso
    repository.write_items(d, items)
