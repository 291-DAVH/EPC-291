"""Files of the plan-drawing editor inside workspace/02-engineering/layout/<level>/: src (drawing and underlay), out (result, DXF, PDF)."""
import datetime as dt
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

from epc.core import engine
from epc.core.fsutil import read_json, write_json

ROOT = ("workspace", "02-engineering", "layout")
UNDERLAY_EXT = (".png", ".jpg", ".jpeg", ".svg")


def base(d: Path) -> Path:
    return d.joinpath(*ROOT)


def level_dir(d: Path, level: str) -> Path:
    return base(d) / level


def levels(d: Path) -> List[str]:
    b = base(d)
    return sorted((p.name for p in b.iterdir() if p.is_dir() and (p / "src" / "drawing.json").is_file()), key=_order) if b.is_dir() else []


def split(sheet: str):
    """A sheet is a level (`L0`) or a level with the discipline it belongs to (`L0@sanitaria_cloacas`): one level can hold one drawing per discipline."""
    level, _, discipline = sheet.partition("@")
    return level, discipline


def parts(sheet: str):
    """A sheet is `L0`, `L0@<discipline>` or `L0@<discipline>.<plan>`: the level, the discipline and the plan of that discipline on it. A discipline can have several plans on a level (lighting and
    sockets of the electrical one); the first one has no plan in its key."""
    level, suffix = split(sheet)
    discipline, _, plan = suffix.partition(".")
    return level, discipline, plan


def _order(sheet: str):
    level, discipline = split(sheet)
    return (int(level[1:]), discipline)


def load_drawing(d: Path, level: str) -> Optional[dict]:
    return read_json(level_dir(d, level) / "src" / "drawing.json", None)


HISTORY_EVERY_S = 300                                          # a snapshot of the previous state at most every five minutes of work
HISTORY_KEEP = 40


def history_dir(d: Path, level: str) -> Path:
    return level_dir(d, level) / "history"


def _remember(d: Path, level: str, previous: dict) -> None:
    """Keep what the drawing was before this save, unless a snapshot was kept a moment ago; the oldest go when there are too many."""
    folder = history_dir(d, level)
    old = sorted(folder.glob("*.json")) if folder.is_dir() else []
    now = dt.datetime.now()
    if old and (now - dt.datetime.strptime(old[-1].stem, "%Y%m%dT%H%M%S")).total_seconds() < HISTORY_EVERY_S:
        return
    write_json(folder / f"{now.strftime('%Y%m%dT%H%M%S')}.json", previous)
    for extra in old[: max(0, len(old) + 1 - HISTORY_KEEP)]:
        extra.unlink(missing_ok=True)


def _remember_if_changed(d: Path, level: str, data: dict) -> None:
    previous = load_drawing(d, level)
    if previous is not None and previous != data:
        _remember(d, level, previous)


def save_drawing(d: Path, level: str, data: dict) -> None:
    _remember_if_changed(d, level, data)
    write_json(level_dir(d, level) / "src" / "drawing.json", data)


def history(d: Path, level: str) -> List[str]:
    """Ids of the kept snapshots, newest first."""
    folder = history_dir(d, level)
    return [p.stem for p in sorted(folder.glob("*.json"), reverse=True)] if folder.is_dir() else []


def load_snapshot(d: Path, level: str, snapshot: str) -> Optional[dict]:
    return read_json(history_dir(d, level) / f"{snapshot}.json", None) if snapshot.replace("T", "").isdigit() else None


SHARED_PLAN = ("underlay.*", "original.*", "architecture.*")


def _strip_to_shared_plan(folder: Path) -> None:
    """Empty a sheet's folder but for the architectural plan the other disciplines of the level still use."""
    for item in folder.iterdir():
        if item.name != "src":
            shutil.rmtree(item, ignore_errors=True) if item.is_dir() else item.unlink()
    for item in (folder / "src").iterdir():
        if not any(item.match(pattern) for pattern in SHARED_PLAN):
            item.unlink()


def _remove_sheet(d: Path, level: str) -> None:
    """The architectural plan stays while another discipline is drawn on the same level: it is shared (see `_plan_homes`)."""
    shared = "@" not in level and any(s != level and split(s)[0] == level for s in levels(d))
    _strip_to_shared_plan(level_dir(d, level)) if shared else shutil.rmtree(level_dir(d, level), ignore_errors=True)


def delete_level(d: Path, level: str) -> None:
    """Delete a sheet (its drawing, files and history)."""
    _remove_sheet(d, level)


def _plan_homes(d: Path, level: str) -> List[Path]:
    """Where the architectural plan of a sheet lives: with the level, shared by every discipline drawn on it (the plan is one; the disciplines are layers over it). A sheet that kept its own
    copy before that (`L0@hvac`) still finds it, after the level's."""
    return [level_dir(d, key) / "src" for key in dict.fromkeys([split(level)[0], level])]


def _plan_file(d: Path, level: str, pattern: str) -> Optional[Path]:
    return next((p for home in _plan_homes(d, level) if home.is_dir() for p in sorted(home.glob(pattern))), None)


def underlay_file(d: Path, level: str) -> Optional[Path]:
    return next((p for ext in UNDERLAY_EXT for p in [_plan_file(d, level, f"underlay{ext}")] if p), None)


def _clear_plan(d: Path, level: str, patterns: tuple) -> None:
    for home in _plan_homes(d, level):
        for pattern in patterns:
            for old in home.glob(pattern):
                old.unlink()


def save_underlay(d: Path, level: str, ext: str, data: bytes) -> Path:
    _clear_plan(d, level, ("underlay.*",))
    src = _plan_homes(d, level)[0]
    src.mkdir(parents=True, exist_ok=True)
    dest = src / f"underlay{ext}"
    dest.write_bytes(data)
    return dest


def _pdf_with_pdfium(pdf: bytes) -> Optional[bytes]:
    """First page of a PDF as a PNG: the architecture engine does it (one place, so the picture shown and the picture it reads have the same pixels); None when it cannot."""
    try:
        from epc_arch import pdf_to_png
    except ImportError:
        return None
    return pdf_to_png(pdf)


def _pdf_with_poppler(pdf: bytes, tmp: Path) -> Optional[bytes]:
    """The same through poppler's `pdftocairo`, called as a separate command (GPL, never linked); None when it is not installed."""
    exe = shutil.which("pdftocairo")
    if not exe:
        return None
    tmp.mkdir(parents=True, exist_ok=True)
    src = tmp / "in.pdf"
    src.write_bytes(pdf)
    res = subprocess.run([exe, "-png", "-singlefile", "-r", "110", "-f", "1", "-l", "1", str(src), str(tmp / "page")], capture_output=True, text=True, timeout=120)
    out = tmp / "page.png"
    return out.read_bytes() if res.returncode == 0 and out.is_file() else None


def pdf_to_png(pdf: bytes, tmp: Path) -> Optional[bytes]:
    """First page of a PDF as an image for the plan underlay: pypdfium2 first, poppler as a fallback; None when neither can."""
    return _pdf_with_pdfium(pdf) or _pdf_with_poppler(pdf, tmp)


ORIGINAL_EXT = (".dxf", ".pdf", ".png", ".jpg", ".jpeg")
ARCHITECTURE = ("architecture.json", "architecture.svg")


def save_original(d: Path, level: str, name: str, data: bytes) -> None:
    """Keep the file as the person sent it (the underlay is a converted copy): what architecture recognition reads."""
    _clear_plan(d, level, ("original.*",))
    src = _plan_homes(d, level)[0]
    src.mkdir(parents=True, exist_ok=True)
    ext = Path(name or "").suffix.lower()
    if ext in ORIGINAL_EXT:
        (src / f"original{ext}").write_bytes(data)


def load_original(d: Path, level: str) -> Optional[Path]:
    return _plan_file(d, level, "original.*")


def _plan_json(d: Path, level: str, name: str) -> Optional[dict]:
    f = _plan_file(d, level, name)
    return read_json(f, None) if f else None


def load_architecture(d: Path, level: str) -> Optional[dict]:
    return _plan_json(d, level, ARCHITECTURE[0])


def save_architecture(d: Path, level: str, data: dict, svg: str) -> None:
    _clear_plan(d, level, ARCHITECTURE)
    src = _plan_homes(d, level)[0]
    src.mkdir(parents=True, exist_ok=True)
    write_json(src / ARCHITECTURE[0], data)
    (src / ARCHITECTURE[1]).write_text(svg, encoding="utf-8")


def delete_architecture(d: Path, level: str) -> None:
    _clear_plan(d, level, ARCHITECTURE)


def out_dir(d: Path, level: str) -> Path:
    return level_dir(d, level) / "out"


def load_result(d: Path, level: str) -> Optional[dict]:
    return read_json(out_dir(d, level) / "result.json", None)


def load_made_from(d: Path, level: str) -> Optional[dict]:
    """The drawing the last DXF and PDF were made from."""
    return read_json(out_dir(d, level) / "drawing.json", None)


def render_pdf(dxf: Path, dst: Path) -> Optional[str]:
    """PDF of the DXF through the engine exporter; the reason in text when it could not be made."""
    res = engine.run_module("epc_drawing.export.pdf", [dxf, dst], timeout=300)
    return None if res.returncode == 0 else engine.tail(res, 200)
