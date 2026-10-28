"""The plan-drawing editor: what the person drew over a plan, what the engine derives from it (graph, tags, lengths, schedule) and the DXF and PDF it produces.

One drawing per level of the project (L0 ground, L1.. up, L-1.. down). The engine part (`epc_plan`) is pure; this module stores, checks who may do what and calls it.
"""
import re
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Optional, Tuple

from epc.core import clock, engine
from epc.core.errors import Invalid, NotFound
from epc.core.fsutil import is_inside, read_json
from epc.modules.catalogs import public as catalogs
from epc.modules.identity import public as identity
from epc.modules.layout import changes, repository
from epc.modules.layout.models import DrawingIn
from epc.modules.projects import public as projects
from epc.modules.sld import public as sld

MAX_UPLOAD = 25 * 1024 * 1024
RASTER = {b"\x89PNG\r\n\x1a\n": ".png", b"\xff\xd8\xff": ".jpg"}
MEDIA = {".png": "image/png", ".jpg": "image/jpeg", ".svg": "image/svg+xml"}


def _no_guard(d: Path, discipline: str) -> None:
    return None


_edit_guard = _no_guard


def set_edit_guard(fn) -> None:
    """Who may change the drawings of a discipline is decided by the coordination module, which depends on this one: it registers its rule here (as the board does for lengths)."""
    global _edit_guard
    _edit_guard = fn


def _engine():
    import epc_plan                                           # the engine owns the rules of the drawing (single source)
    from epc_plan import core, dxfout, jobs, underlay
    return core, dxfout, jobs, underlay


def _check_base(core, base: str) -> None:
    try:
        core.parse_level(base)
    except core.PlanError as e:
        raise Invalid({"level": str(e)})


PLAN_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,23}$")


def _check_plan(discipline: str) -> None:
    plan = discipline.partition(".")[2]
    if "." in discipline and not PLAN_SLUG.match(plan):
        raise Invalid({"level": f"the plan {plan!r} of a sheet is lowercase letters, digits and hyphens (up to 24)"})


def _check_suffix(core, level: str, discipline: str) -> None:
    profile = discipline.partition(".")[0]
    if "@" in level and profile not in core.profiles():
        raise Invalid({"level": f"unknown discipline {profile!r}: profiles are {', '.join(core.profiles())}"})
    _check_plan(discipline)


def _level(level: str) -> str:
    """The key of a sheet: a valid level, optionally followed by `@` and the discipline of a second drawing on that level."""
    core = _engine()[0]
    base, discipline = repository.split(level)
    _check_base(core, base)
    _check_suffix(core, level, discipline)
    return level


def _discipline_of(d: Path, level: str) -> str:
    return (repository.load_drawing(d, level) or {}).get("discipline", "electrica_BT")


def _document(level: str, data: dict, version: str = "") -> dict:
    base = repository.split(level)[0]
    return {"schema_version": "1.0", "plan": {"id": "PLAN_" + level.replace("@", "_"), "level": base, "scale": data["scale"], "origin": data["origin"]}, "discipline": data["discipline"],
            "nodes": [{k: v for k, v in n.items() if v not in ("", None)} for n in data["nodes"]],
            "lines": [{k: v for k, v in ln.items() if v not in ("", None)} for ln in data["lines"]],
            "circuits": data.get("circuits", []),
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


def _offered(profile: dict, pid: str, chosen: set, used: set) -> bool:
    """A profile is offered when the project chose its discipline, it is always there (architecture), the sheet already exists, or the project chose none."""
    return not chosen or bool(profile.get("siempre")) or profile.get("disciplina_proyecto") in chosen or pid in used


def _profiles(d: Path, core, used: set) -> list:
    """The drawing profiles, in the order a project is worked (architecture, civil, mechanical, electrical...). `offered` tells whether the project chose that discipline when it was created
    (or already draws in it): those are the ones the editor lists to add a sheet; a project that chose none is offered all of them."""
    from epc_dxf import layers as dxf_layers
    order = [g["profile"] for g in dxf_layers.disciplines() if g.get("profile")]
    chosen = set(projects.read_meta(d).get("disciplines") or [])
    out = []
    for pid in sorted(core.profiles(), key=lambda x: order.index(x) if x in order else len(order)):
        p = core.load_profile(pid)
        symbols = {k["simbolo_2d"]: core.SYMBOLS[k["simbolo_2d"]]["prims"] for k in p["nodos"] if k.get("simbolo_2d") in core.SYMBOLS}          # the editor draws what the engine draws
        offered = _offered(p, pid, chosen, used)
        out.append({"id": pid, "name": p["nombre"], "project_discipline": p.get("disciplina_proyecto", ""), "offered": offered, "subdisciplines": [{"id": s["id"], "name": s["nombre"], "kinds": s["tipos"]} for s in p.get("subdisciplinas", [])], "lines": p["tramos"], "nodes": p["nodos"], "shortcuts": p.get("atajos_teclado", {}), "symbols": symbols})
    return out


def _sheet_item(d: Path, lv: str) -> dict:
    dr = repository.load_drawing(d, lv) or {}
    return {"level": lv, "base": repository.split(lv)[0], "discipline": dr.get("discipline", "electrica_BT"), "plan": repository.parts(lv)[2], "plan_name": dr.get("plan_name", ""), "subdiscipline": dr.get("subdiscipline", ""),
            "nodes": len(dr.get("nodes", [])), "lines": len(dr.get("lines", [])), "underlay": repository.underlay_file(d, lv) is not None, "has_files": bool((repository.load_result(d, lv) or {}).get("files"))}


def overview(d: Path) -> dict:
    core, dxfout, _, _ = _engine()
    items = [_sheet_item(d, lv) for lv in repository.levels(d)]
    return {"levels": items, "profiles": _profiles(d, core, {i["discipline"] for i in items}), "circuits": sld.circuits(d), "boards": sld.boards(d), "dxf_versions": dxfout.versions(), "default_dxf_version": core.PARAMS["dxf"]["default_version"]}


def _blank() -> dict:
    return {"discipline": "electrica_BT", "subdiscipline": "", "plan_name": "", "scale": None, "origin": [0.0, 0.0], "nodes": [], "lines": [], "circuits": [], "outlet": "", "outlet_invert_m": None, "dxf_version": "", "underlay_opts": {}, "rooms": [], "lighting_settings": {}}


def view(d: Path, level: str) -> dict:
    level = _level(level)
    saved = repository.load_drawing(d, level)
    data = {**_blank(), **saved} if saved else _blank()                # a drawing saved before a field existed gets its default
    result = repository.load_result(d, level)
    up = repository.underlay_file(d, level)
    return {"level": level, "saved": saved is not None, "scale_locked": data["discipline"] != repository.ARCH_DISCIPLINE, "drawing": data, "result": derive_data(level, data) if saved else None,
            "underlay": {"kind": up.suffix.lstrip("."), "version": int(up.stat().st_mtime)} if up else None, "architecture": _architecture_summary(d, level),
            "files": (result or {}).get("files") if result else None, "generated_at": (result or {}).get("generated_at")}


def _circuits_by_level(d: Path) -> Dict[str, list]:
    """Every circuit routed on any drawing: tag -> [(level, route)]."""
    seen: Dict[str, list] = {}
    for lv in repository.levels(d):
        saved = repository.load_drawing(d, lv)
        try:
            res = derive_data(lv, {**_blank(), **saved}) if saved else {}
        except Invalid:
            continue
        for tag, r in (res.get("circuits") or {}).items():
            seen.setdefault(tag, []).append((lv, r))
    return seen


def _measure(found: list) -> dict:
    lv, r = found[0]
    complete = bool(r.get("found")) and not r.get("unreached") and r.get("moment_length_m", 0) > 0
    return {"levels": [x[0] for x in found], "usable": complete and len(found) == 1, "reason": "levels" if len(found) > 1 else "" if complete else "incomplete",
            "loads_n": len(r.get("loads_detail", [])), "moment_length_m": r.get("moment_length_m", 0.0), "max_distance_m": r.get("max_distance_m", 0.0), "length_m": r.get("length_m", 0.0)}


def plan_lengths(d: Path) -> Dict[str, dict]:
    """What the drawings measured for each circuit, by tag, for the board to use as its length (see `sld.lengths`). A circuit is usable when it is routed completely on
    one level and reaches at least one load or destination; one drawn over several levels is not (the way between levels is not measured yet)."""
    return {tag: _measure(found) for tag, found in _circuits_by_level(d).items()}


sld.set_plan_lengths(plan_lengths)                              # the board reads its lengths through this (the dependency stays layout -> sld)


def _plan_of(d: Path, lv: str) -> tuple:
    """The discipline and the plan a sheet holds: the discipline is what is drawn in it, the plan what its key says."""
    return (repository.load_drawing(d, lv) or {}).get("discipline", "electrica_BT"), repository.parts(lv)[2]


def _check_subdiscipline(data: dict) -> None:
    """The subdiscipline of a plan is one the profile of its discipline has (or none: every kind is offered)."""
    chosen = data.get("subdiscipline", "")
    allowed = {s["id"] for s in _engine()[0].load_profile(data["discipline"]).get("subdisciplinas", [])}
    if chosen and chosen not in allowed:
        raise Invalid({"subdiscipline": f"{data['discipline']} has no subdiscipline {chosen!r}: {', '.join(sorted(allowed)) or 'none'}"})


def _check_sheet(d: Path, level: str, data: dict) -> None:
    """A level holds one drawing per discipline and plan: a second sheet carries its discipline (and its plan) in its name, and no two sheets of a level are the same plan of the same discipline."""
    base, suffix = repository.split(level)
    if suffix and data["discipline"] != repository.parts(level)[1]:
        raise Invalid({"discipline": f"this sheet is for {repository.parts(level)[1]}"})
    taken = [_plan_of(d, lv) for lv in repository.levels(d) if lv != level and repository.split(lv)[0] == base]
    if (data["discipline"], repository.parts(level)[2]) in taken:
        raise Invalid({"discipline": f"{base} already has that plan of {data['discipline']}: give the new plan another name"})


def _with_plan_scale(d: Path, level: str, data: dict) -> dict:
    """The drawing with the scale of the plan: the Architecture sheet of the level is the only one that sets it, the others work with it."""
    return data if data["discipline"] == repository.ARCH_DISCIPLINE else {**data, "scale": repository.architecture_scale(d, level)}


def save(d: Path, level: str, body: DrawingIn) -> dict:
    level = _level(level)
    data = _with_plan_scale(d, level, body.model_dump(by_alias=True))
    _check_sheet(d, level, data)
    _check_subdiscipline(data)
    _edit_guard(d, data["discipline"])
    derive_data(level, data)                                    # refuse what the engine refuses before storing it
    repository.save_drawing(d, level, data)
    return view(d, level)


def derive(d: Path, level: str, body: DrawingIn) -> dict:
    level = _level(level)
    return derive_data(level, _with_plan_scale(d, level, body.model_dump(by_alias=True)))


def remove(d: Path, level: str) -> dict:
    level = _level(level)
    if repository.load_drawing(d, level) is None and not repository.level_dir(d, level).exists():
        raise NotFound("level not found")
    _edit_guard(d, _discipline_of(d, level))
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


def _architecture_only(d: Path, level: str) -> None:
    """The architectural plan is put in, recognized and taken out from the Architecture sheet of the level; the other disciplines only draw over it."""
    if _discipline_of(d, level) != "arquitectura":
        raise Invalid({"discipline": "the plan is managed from the Architecture sheet of the level"})


def upload_underlay(d: Path, level: str, name: str, data: bytes) -> dict:
    level = _level(level)
    _architecture_only(d, level)
    if not data:
        raise Invalid({"file": "the file is empty"})
    if len(data) > MAX_UPLOAD:
        raise Invalid({"file": f"the file is too big (up to {MAX_UPLOAD // (1024 * 1024)} MB)"})
    original = data
    data, ext = _underlay_content(name, data)
    _edit_guard(d, _discipline_of(d, level))
    repository.save_underlay(d, level, ext, data)
    repository.save_original(d, level, name, original)
    repository.delete_architecture(d, level)                   # what was recognized belonged to the earlier plan
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
        result = jobs.run(_document(level, saved, version or saved.get("dxf_version", "")), out, layers_file=catalogs.files(d)["layers"])
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
    write_json(out / "drawing.json", saved)                       # what the files were made from, to show later what changed
    identity.audit_event("layout_generated", target=f"{projects.project_id(d)}:{level}", org_slug=projects.read_meta(d).get("org", ""), detail={"dxf_version": files["dxf_version"]})
    return view(d, level)


def output_file(d: Path, level: str, name: str) -> Tuple[Path, str]:
    level = _level(level)
    out = repository.out_dir(d, level)
    if not name or not is_inside(out, name) or name not in ((repository.load_result(d, level) or {}).get("files") or {}).values():
        raise NotFound("file not found")
    return out / name, "application/pdf" if name.endswith(".pdf") else "application/dxf"


# ---------------------------------------------------------------- history
def history(d: Path, level: str) -> list:
    level = _level(level)
    out = []
    for snap in repository.history(d, level):
        data = repository.load_snapshot(d, level, snap) or {}
        out.append({"id": snap, "at": f"{snap[:4]}-{snap[4:6]}-{snap[6:8]}T{snap[9:11]}:{snap[11:13]}:{snap[13:15]}", "nodes": len(data.get("nodes", [])), "lines": len(data.get("lines", []))})
    return out


def snapshot(d: Path, level: str, snap: str) -> dict:
    level = _level(level)
    data = repository.load_snapshot(d, level, snap)
    if data is None:
        raise NotFound("snapshot not found")
    return {**_blank(), **data}


def restore(d: Path, level: str, snap: str) -> dict:
    """Go back to a kept state; what was there is kept too, so the restore itself can be undone."""
    data = snapshot(d, level, snap)
    _edit_guard(d, data["discipline"])
    repository.save_drawing(d, _level(level), data)
    identity.audit_event("layout_restored", target=f"{projects.project_id(d)}:{level}", org_slug=projects.read_meta(d).get("org", ""), detail={"snapshot": snap})
    return view(d, level)


# ---------------------------------------------------------------- what other modules read
def sheets(d: Path) -> list:
    """Every sheet of the project: its key, its level and its discipline."""
    return [{"sheet": lv, "level": repository.split(lv)[0], "discipline": (repository.load_drawing(d, lv) or {}).get("discipline", "electrica_BT")} for lv in repository.levels(d)]


def documents(d: Path) -> list:
    """The drawing document of each sheet (the engine's input), for the sheets that have a scale: what coordination compares."""
    out = []
    for lv in repository.levels(d):
        saved = repository.load_drawing(d, lv)
        if saved and saved.get("scale"):
            out.append((lv, _document(lv, {**_blank(), **saved})))
    return out


def saved_drawing(d: Path, level: str) -> Optional[dict]:
    """The drawing of a sheet as it was last saved (None when the sheet has none): what a study made from it is compared with."""
    return repository.load_drawing(d, _level(level))


def source_file(d: Path, level: str, name: str) -> Path:
    """A file of what is kept with the sheet (`<sheet>/src/<name>`): another module keeps there what it made from the sheet."""
    return repository.level_dir(d, _level(level)) / "src" / name


def changes_since_files(d: Path, level: str) -> dict:
    """What changed in the drawing since the DXF and PDF were last made (nothing to compare with when they were never made, or were made before this was kept)."""
    level = _level(level)
    made = repository.load_made_from(d, level)
    saved = repository.load_drawing(d, level)
    if made is None or saved is None:
        return {"has_snapshot": False}
    return changes.diff(made, saved)


# ---------------------------------------------------------------- architecture of the plan (walls, doors, windows)
def _architecture_summary(d: Path, level: str) -> Optional[dict]:
    a = repository.load_architecture(d, level)
    return None if a is None else {k: a[k] for k in ("source", "counts", "wall_thickness", "units_per_metre", "scale_hint", "warnings")}


def _recognize_file(src: Path, units_per_metre: Optional[float]) -> Tuple[dict, str]:
    """Run the architecture engine on a file, as a process of its own (it reads files of any size and quality: it gets a time limit and cannot take the server down)."""
    with tempfile.TemporaryDirectory() as tmp:
        args = [src, "--out", tmp] + (["--units-per-metre", units_per_metre] if units_per_metre else [])
        res = engine.run_module("epc_arch", args, timeout=180)
        if res.returncode != 0:
            raise Invalid({"file": engine.tail(res, 300) or "the plan could not be recognized"})
        out = Path(tmp)
        return read_json(out / f"{src.stem}.architecture.json", {}), (out / f"{src.stem}.architecture.svg").read_text(encoding="utf-8")


def recognize_architecture(d: Path, level: str, units_per_metre: Optional[float]) -> dict:
    """Find the walls, doors and windows of the plan the person uploaded (their file, as they sent it), keep them with the sheet and, when the plan was vector (a DXF or a PDF made from CAD), show the recognized SVG as the underlay: the engine draws it, so its frame is the one the findings are in.
    An image keeps its own underlay: the findings are in its pixels."""
    level = _level(level)
    _architecture_only(d, level)
    original = repository.load_original(d, level)
    if original is None:
        raise Invalid({"file": "upload the plan first: a DXF, a PDF or an image"})
    _edit_guard(d, _discipline_of(d, level))
    arch, svg = _recognize_file(original, units_per_metre)
    repository.save_architecture(d, level, arch, svg)
    replaced = arch.get("source") in ("dxf", "pdf")
    if replaced:
        repository.save_underlay(d, level, ".svg", svg.encode("utf-8"))
    identity.audit_event("layout_architecture", target=f"{projects.project_id(d)}:{level}", org_slug=projects.read_meta(d).get("org", ""), detail={"source": arch.get("source"), **(arch.get("counts") or {})})
    return {"architecture": arch, "underlay_replaced": replaced, "view": view(d, level)}


def architecture(d: Path, level: str) -> dict:
    a = repository.load_architecture(d, _level(level))
    if a is None:
        raise NotFound("no architecture was recognized on this sheet")
    return a


def remove_architecture(d: Path, level: str) -> dict:
    level = _level(level)
    _architecture_only(d, level)
    _edit_guard(d, _discipline_of(d, level))
    repository.delete_architecture(d, level)
    return view(d, level)


# ---------------------------------------------------------------- the layers of each discipline
def _kinds_by_layer() -> Dict[str, list]:
    """What the plan editor draws in each layer: layer name -> the kinds of line and node of every profile that use it."""
    core = _engine()[0]
    out: Dict[str, list] = {}
    for pid in core.profiles():
        p = core.load_profile(pid)
        for kind_type, items in (("line", p["tramos"]), ("node", p["nodos"])):
            for k in items:
                out.setdefault(k.get("capa_dxf", ""), []).append({"profile": pid, "id": k["id"], "type": kind_type, "name": k["etiqueta"]})
    return out


def layers_by_discipline(d: Path) -> dict:
    """The catalog of DXF layers in force for this project (default, global, company, project) grouped by discipline, each layer with the kinds the editor draws in it, and which disciplines
    already have a drawing in the project."""
    from epc_dxf import layers as dxf_layers
    effective = catalogs.layers_view("project", d)["layers"]
    kinds = _kinds_by_layer()
    drawn = {s["discipline"] for s in sheets(d)}
    groups = dxf_layers.by_discipline(effective)
    return {"disciplines": [{**g, "drawn": g["profile"] in drawn if g["profile"] else False, "layers": [{**x, "kinds": kinds.get(x["name"], [])} for x in g["layers"]]} for g in groups]}


# ---------------------------------------------------------------- automatic design of circuits and runs
def design_runs(d: Path, level: str, body) -> dict:
    """Step 1 of the automatic design: the straight trunks (trays) and the conduits to each load (see `epc_plan.design`). Nothing is saved: the person looks at the preview and accepts it."""
    from epc_plan import design
    core = _engine()[0]
    data = body.drawing.model_dump(by_alias=True)
    try:
        return design.propose_runs(_document(_level(level), data), {"board": body.board})
    except core.PlanError as e:
        raise Invalid({"drawing": str(e)})


def design_wiring(d: Path, level: str, body) -> dict:
    """Step 2: the circuits by room over the runs that are already drawn, checked by routing each one with the engine. Nothing is saved."""
    from epc_plan import design
    core = _engine()[0]
    data = body.drawing.model_dump(by_alias=True)
    taken = {c["tag"] for c in sld.circuits(d)} | {c["tag"] for c in data["circuits"] if c.get("tag")}
    try:
        return design.propose_wiring(_document(_level(level), data), data["rooms"], {"taken": sorted(taken), "board": body.board, "families": body.families})
    except core.PlanError as e:
        raise Invalid({"drawing": str(e)})


def accept_circuits(d: Path, level: str, circuits: list, board: str = "") -> dict:
    """Create in the board the circuits the person accepted from a proposal (the drawing refers to them by tag)."""
    level = _level(level)
    _edit_guard(d, _discipline_of(d, level))
    out = sld.add_circuits(d, [c.model_dump() for c in circuits], board)
    identity.audit_event("layout_circuits_created", target=f"{projects.project_id(d)}:{level}", org_slug=projects.read_meta(d).get("org", ""), detail={"added": len(out["added"])})
    return out
