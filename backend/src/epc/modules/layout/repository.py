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


def save_drawing(d: Path, level: str, data: dict) -> None:
    previous = load_drawing(d, level)
    if previous is not None and previous != data:
        _remember(d, level, previous)
    write_json(level_dir(d, level) / "src" / "drawing.json", data)


def history(d: Path, level: str) -> List[str]:
    """Ids of the kept snapshots, newest first."""
    folder = history_dir(d, level)
    return [p.stem for p in sorted(folder.glob("*.json"), reverse=True)] if folder.is_dir() else []


def load_snapshot(d: Path, level: str, snapshot: str) -> Optional[dict]:
    return read_json(history_dir(d, level) / f"{snapshot}.json", None) if snapshot.replace("T", "").isdigit() else None


def delete_level(d: Path, level: str) -> None:
    shutil.rmtree(level_dir(d, level), ignore_errors=True)


def underlay_file(d: Path, level: str) -> Optional[Path]:
    src = level_dir(d, level) / "src"
    return next((p for ext in UNDERLAY_EXT for p in [src / f"underlay{ext}"] if p.is_file()), None)


def save_underlay(d: Path, level: str, ext: str, data: bytes) -> Path:
    src = level_dir(d, level) / "src"
    src.mkdir(parents=True, exist_ok=True)
    for old in src.glob("underlay.*"):
        old.unlink()
    dest = src / f"underlay{ext}"
    dest.write_bytes(data)
    return dest


def _pdf_with_pdfium(pdf: bytes, max_side: int = 3000) -> Optional[bytes]:
    """First page of a PDF as a PNG with pypdfium2 (Apache-2.0 / BSD-3, the library of Chrome's PDF viewer); None when it is not installed or cannot read the file."""
    try:
        import io
        import pypdfium2
    except ImportError:
        return None
    try:
        page = pypdfium2.PdfDocument(pdf)[0]
        width, height = page.get_size()
        image = page.render(scale=min(2.5, max_side / max(width, height, 1))).to_pil()
        out = io.BytesIO()
        image.save(out, format="PNG")
        return out.getvalue()
    except Exception:                                         # noqa: BLE001 - a broken or protected PDF is reported by the caller as "cannot open"
        return None


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
