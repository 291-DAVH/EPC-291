"""Files of the reporting step: the methodology's report catalog, the generated reports and their log."""
from pathlib import Path
from typing import List, Optional

from epc.core import engine
from epc.core.config import settings
from epc.core.fsutil import read_json, write_json

MGMT = Path("workspace") / "05-management"


def catalog(methodology: str) -> Optional[dict]:
    return read_json(settings.methodologies_dir / methodology / "reports.json", None)


def mgmt(d: Path) -> Path:
    return d / MGMT


# ---- generated reports
def generated(d: Path) -> List[dict]:
    return read_json(mgmt(d) / "reports" / "generated.json", []) or []


def save_generated(d: Path, items: List[dict]) -> None:
    write_json(mgmt(d) / "reports" / "generated.json", items)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def render_pdf(doc: dict, dst: Path) -> None:
    """PDF through the engine exporter."""
    engine.render_report_pdf(doc, dst)
