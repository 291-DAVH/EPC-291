"""Files of the issuing step: deliverables/transmittals/TR-nnn.json and the stamped copies, plus helpers that run the engine exporters."""
import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from epc.core import engine
from epc.core.fsutil import read_json, write_json
from epc.core.hashing import sha256_file as sha256


def transmittals_dir(d: Path) -> Path:
    return d / "deliverables" / "transmittals"


def list_transmittals(d: Path) -> List[dict]:
    out = []
    for f in sorted(transmittals_dir(d).glob("TR-*.json")):
        data = read_json(f, None)
        if data:
            out.append(data)
    return out


def load_transmittal(d: Path, tr: str) -> Optional[dict]:
    return read_json(transmittals_dir(d) / f"{tr}.json", None)


def save_transmittal(d: Path, data: dict) -> None:
    write_json(transmittals_dir(d) / f"{data['id']}.json", data)


def next_transmittal_number(d: Path) -> int:
    nums = [int(m.group(1)) for f in transmittals_dir(d).glob("TR-*.json") if (m := re.match(r"TR-(\d+)$", f.stem))]
    return max(nums, default=0) + 1


def write_ledger(d: Path, event: dict) -> None:
    folder = d / ".epc" / "ledger"
    folder.mkdir(parents=True, exist_ok=True)
    n = len(list(folder.glob("*.json"))) + 1
    write_json(folder / f"{n:04d}_{event['event']}.json", event)


def plugins_locked(d: Path) -> Dict[str, str]:
    lock = read_json(d / ".epc" / "plugins.lock", {}) or {}
    return {k: v.get("version", "") for k, v in lock.get("plugins", {}).items()}


def engine_version() -> str:
    from importlib.metadata import PackageNotFoundError, version
    try:
        return version("epc-drawing")
    except PackageNotFoundError:
        return "unknown"


def stamp_dxf(src: Path, dst: Path, props: Dict[str, str]) -> None:
    """Delivered DXF = copy of the master with the issue data written in its header (master untouched), via the engine exporter."""
    res = engine.run_module("epc_drawing.export.stamp", [src, dst] + [f"{k}={v}" for k, v in props.items()], timeout=300)
    if res.returncode != 0:
        raise RuntimeError(f"could not stamp {src.name}: {engine.tail(res, 300)}")


def render_transmittal_pdf(data: dict, dst: Path) -> None:
    """Transmittal document (A4 PDF) through the engine exporter."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "transmittal.json"
        src.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        res = engine.run_module("epc_drawing.export.transmittal_pdf", [src, dst], timeout=120)
    if res.returncode != 0:
        raise RuntimeError(f"could not render the transmittal document: {engine.tail(res, 300)}")


def render_pdf(dxf: Path, dst: Path) -> None:
    res = engine.run_module("epc_drawing.export.pdf", [dxf, dst], timeout=300)
    if res.returncode != 0:
        raise RuntimeError(f"could not render the PDF of {dxf.name}: {engine.tail(res, 300)}")
