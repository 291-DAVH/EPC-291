"""The plan-drawing editor: what the person drew over a plan, what the engine derives from it (graph, tags, lengths, schedule) and the DXF and PDF it produces.

One drawing per level of the project (L0 ground, L1.. up, L-1.. down). The engine part (`epc_plan`) is pure; this module stores, checks who may do what and calls it.
"""
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Optional, Tuple

from epc.core import clock
from epc.core.errors import Invalid, NotFound
from epc.core.fsutil import is_inside
from epc.modules.identity import public as identity
from epc.modules.layout import repository
from epc.modules.layout.models import DrawingIn
from epc.modules.projects import public as projects

MAX_UPLOAD = 25 * 1024 * 1024
RASTER = {b"\x89PNG\r\n\x1a\n": ".png", b"\xff\xd8\xff": ".jpg"}
MEDIA = {".png": "image/png", ".jpg": "image/jpeg", ".svg": "image/svg+xml"}


def _engine():
    import epc_plan                                           # the engine owns the rules of the drawing (single source)
    from epc_plan import core, dxfout, jobs, underlay
    return core, dxfout, jobs, underlay


def _level(level: str) -> str:
    core = _engine()[0]
    try:
        core.parse_level(level)
    except core.PlanError as e:
        raise Invalid({"level": str(e)})
    return level


def _document(level: str, data: dict, version: str = "") -> dict:
    return {"schema_version": "1.0", "plan": {"id": f"PLAN_{level}", "level": level, "scale": data["scale"], "origin": data["origin"]}, "discipline": data["discipline"],
            "nodes": [{k: v for k, v in n.items() if v not in ("", None)} for n in data["nodes"]],
            "lines": [{k: v for k, v in ln.items() if v not in ("", None)} for ln in data["lines"]],
            **({"outlet": data["outlet"]} if data.get("outlet") else {}), **({"outlet_invert_m": data["outlet_invert_m"]} if data.get("outlet_invert_m") is not None else {}),
            "dxf_version": version or data.get("dxf_version", "")}


def derive_data(level: str, data: dict) -> dict:
    """What the engine derives from a drawing; `{"ready": false}` while there is no scale yet (nothing can be measured)."""
    core = _engine()[0]
    if not data.get("scale"):
        return {"ready": False, "reason": "scale"}
    try:
        return {"ready": True, **core.process(_document(level, data))}
    except core.PlanError as e:
        raise Invalid({"drawing": str(e)})


def overview(d: Path) -> dict:
    core, dxfout, _, _ = _engine()
    items = []
    for lv in repository.levels(d):
        dr = repository.load_drawing(d, lv) or {}
        items.append({"level": lv, "nodes": len(dr.get("nodes", [])), "lines": len(dr.get("lines", [])), "underlay": repository.underlay_file(d, lv) is not None,
                      "has_files": bool((repository.load_result(d, lv) or {}).get("files"))})
    profiles = []
    for pid in core.profiles():
        p = core.load_profile(pid)
        profiles.append({"id": pid, "name": p["nombre"], "lines": p["tramos"], "nodes": p["nodos"], "shortcuts": p.get("atajos_teclado", {})})
    return {"levels": items, "profiles": profiles, "dxf_versions": dxfout.versions(), "default_dxf_version": core.PARAMS["dxf"]["default_version"]}


def _blank() -> dict:
    return {"discipline": "electrica_BT", "scale": None, "origin": [0.0, 0.0], "nodes": [], "lines": [], "outlet": "", "outlet_invert_m": None, "dxf_version": ""}


def view(d: Path, level: str) -> dict:
    level = _level(level)
    saved = repository.load_drawing(d, level)
    data = saved or _blank()
    result = repository.load_result(d, level)
    up = repository.underlay_file(d, level)
    return {"level": level, "saved": saved is not None, "drawing": data, "result": derive_data(level, data) if saved else None,
            "underlay": {"kind": up.suffix.lstrip("."), "version": int(up.stat().st_mtime)} if up else None,
            "files": (result or {}).get("files") if result else None, "generated_at": (result or {}).get("generated_at")}


def save(d: Path, level: str, body: DrawingIn) -> dict:
    level = _level(level)
    data = body.model_dump()
    derive_data(level, data)                                    # refuse what the engine refuses before storing it
    repository.save_drawing(d, level, data)
    return view(d, level)


def derive(d: Path, level: str, body: DrawingIn) -> dict:
    level = _level(level)
    return derive_data(level, body.model_dump())


def remove(d: Path, level: str) -> dict:
    level = _level(level)
    if repository.load_drawing(d, level) is None and not repository.level_dir(d, level).exists():
        raise NotFound("level not found")
    repository.delete_level(d, level)
    identity.audit_event("layout_deleted", target=f"{projects.project_id(d)}:{level}", org_slug=projects.read_meta(d).get("org", ""))
    return overview(d)


# ---------------------------------------------------------------- the plan underlay
def _raster_ext(data: bytes) -> Optional[str]:
    return next((e for magic, e in RASTER.items() if data.startswith(magic)), None)


def _from_dxf(data: bytes) -> Tuple[bytes, str]:
    try:
        return _engine()[3].dxf_to_svg(data).encode("utf-8"), ".svg"
    except ValueError as e:
        raise Invalid({"file": str(e)})


def _from_pdf(data: bytes) -> Tuple[bytes, str]:
    with tempfile.TemporaryDirectory() as tmp:
        png = repository.pdf_to_png(data, Path(tmp))
    if png is None:
        raise Invalid({"file": "the PDF could not be read as a plan (it may be damaged or protected): export it as an image (PNG or JPG) or as a DXF"})
    return png, ".png"


def _underlay_content(name: str, data: bytes) -> Tuple[bytes, str]:
    """What is stored for an uploaded plan and its extension: images and SVG as they come (shown only through <img>), a DXF as an SVG view, a PDF as an image."""
    lower = (name or "").lower()
    ext = _raster_ext(data)
    if ext:
        return data, ext
    if lower.endswith(".svg") and b"<svg" in data[:4096].lower():
        return data, ".svg"
    if lower.endswith(".dxf"):
        return _from_dxf(data)
    if lower.endswith(".pdf") or data.startswith(b"%PDF"):
        return _from_pdf(data)
    raise Invalid({"file": "use a PNG or JPG image, an SVG, a DXF or a PDF"})


def upload_underlay(d: Path, level: str, name: str, data: bytes) -> dict:
    level = _level(level)
    if not data:
        raise Invalid({"file": "the file is empty"})
    if len(data) > MAX_UPLOAD:
        raise Invalid({"file": f"the file is too big (up to {MAX_UPLOAD // (1024 * 1024)} MB)"})
    data, ext = _underlay_content(name, data)
    repository.save_underlay(d, level, ext, data)
    identity.audit_event("layout_underlay", target=f"{projects.project_id(d)}:{level}", org_slug=projects.read_meta(d).get("org", ""), detail={"kind": ext.lstrip(".")})
    return view(d, level)


def underlay_file(d: Path, level: str) -> Tuple[Path, str]:
    level = _level(level)
    up = repository.underlay_file(d, level)
    if up is None:
        raise NotFound("this level has no plan underlay")
    return up, MEDIA[up.suffix]


# ---------------------------------------------------------------- DXF and PDF
def generate(d: Path, level: str, version: str = "") -> dict:
    level = _level(level)
    core, dxfout, jobs, _ = _engine()
    saved = repository.load_drawing(d, level)
    if saved is None:
        raise NotFound("nothing is drawn on this level yet")
    if not saved.get("scale"):
        raise Invalid({"scale": "calibrate the scale of the plan first"})
    if version and version not in dxfout.versions():
        raise Invalid({"version": "one of " + ", ".join(dxfout.versions())})
    out = repository.out_dir(d, level)
    if out.exists():
        shutil.rmtree(out)
    try:
        result = jobs.run(_document(level, saved, version or saved.get("dxf_version", "")), out)
    except core.PlanError as e:
        raise Invalid({"drawing": str(e)})
    dxf = out / result["files"]["dxf"]
    problem = repository.render_pdf(dxf, dxf.with_suffix(".pdf"))
    files = {"dxf": dxf.name, "dxf_version": result["files"]["dxf_version"]}
    if problem is None:
        files["pdf"] = dxf.with_suffix(".pdf").name
    else:
        result["warnings"].append(f"the PDF could not be made: {problem}")
    result["files"], result["generated_at"] = files, clock.now_local()
    from epc.core.fsutil import write_json
    write_json(out / "result.json", result)
    identity.audit_event("layout_generated", target=f"{projects.project_id(d)}:{level}", org_slug=projects.read_meta(d).get("org", ""), detail={"dxf_version": files["dxf_version"]})
    return view(d, level)


def output_file(d: Path, level: str, name: str) -> Tuple[Path, str]:
    level = _level(level)
    out = repository.out_dir(d, level)
    if not name or not is_inside(out, name) or name not in ((repository.load_result(d, level) or {}).get("files") or {}).values():
        raise NotFound("file not found")
    return out / name, "application/pdf" if name.endswith(".pdf") else "application/dxf"
