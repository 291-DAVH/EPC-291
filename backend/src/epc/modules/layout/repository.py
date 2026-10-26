"""Files of the plan-drawing editor inside workspace/02-engineering/layout/<level>/: src (drawing and underlay), out (result, DXF, PDF)."""
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


def _order(level: str) -> int:
    return int(level[1:])


def load_drawing(d: Path, level: str) -> Optional[dict]:
    return read_json(level_dir(d, level) / "src" / "drawing.json", None)


def save_drawing(d: Path, level: str, data: dict) -> None:
    write_json(level_dir(d, level) / "src" / "drawing.json", data)


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


def pdf_to_png(pdf: bytes, tmp: Path) -> Optional[bytes]:
    """First page of a PDF as an image through poppler's `pdftocairo`, called as a separate command (GPL, never linked). None when it is not installed."""
    exe = shutil.which("pdftocairo")
    if not exe:
        return None
    tmp.mkdir(parents=True, exist_ok=True)
    src = tmp / "in.pdf"
    src.write_bytes(pdf)
    res = subprocess.run([exe, "-png", "-singlefile", "-r", "110", "-f", "1", "-l", "1", str(src), str(tmp / "page")], capture_output=True, text=True, timeout=120)
    out = tmp / "page.png"
    return out.read_bytes() if res.returncode == 0 and out.is_file() else None


def out_dir(d: Path, level: str) -> Path:
    return level_dir(d, level) / "out"


def load_result(d: Path, level: str) -> Optional[dict]:
    return read_json(out_dir(d, level) / "result.json", None)


def render_pdf(dxf: Path, dst: Path) -> Optional[str]:
    """PDF of the DXF through the engine exporter; the reason in text when it could not be made."""
    res = engine.run_module("epc_drawing.export.pdf", [dxf, dst], timeout=300)
    return None if res.returncode == 0 else engine.tail(res, 200)
