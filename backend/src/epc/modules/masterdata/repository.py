"""Master data files: <EPC_DATA>/{organization,clients,people}.json and logos/."""
from pathlib import Path
from typing import Dict, List, Optional

from epc.core.config import settings
from epc.core.fsutil import read_json, write_json

LOGO_EXT = (".svg", ".png")


def _file(name: str) -> Path:
    return settings.data_dir / name


def load_organization() -> Dict:
    return read_json(_file("organization.json"), {}) or {}


def save_organization(data: Dict) -> None:
    write_json(_file("organization.json"), {"schema_version": "1.0", **data})


def load_list(name: str) -> List[Dict]:
    data = read_json(_file(f"{name}.json"), {}) or {}
    return data.get("items", []) if isinstance(data, dict) else []


def save_list(name: str, items: List[Dict]) -> None:
    write_json(_file(f"{name}.json"), {"schema_version": "1.0", "items": items})


def logos_dir() -> Path:
    return settings.data_dir / "logos"


def logo_path(key: str) -> Optional[Path]:
    """key = 'organization' or 'client-<ID>'; the file may be svg or png."""
    for ext in LOGO_EXT:
        p = logos_dir() / f"{key}{ext}"
        if p.is_file():
            return p
    return None


def save_logo(key: str, ext: str, content: bytes) -> Path:
    delete_logo(key)
    logos_dir().mkdir(parents=True, exist_ok=True)
    p = logos_dir() / f"{key}{ext}"
    p.write_bytes(content)
    return p


def delete_logo(key: str) -> None:
    for ext in LOGO_EXT:
        (logos_dir() / f"{key}{ext}").unlink(missing_ok=True)
