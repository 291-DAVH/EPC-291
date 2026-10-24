"""Master data files of an organization: <EPC_DATA>/orgs/<slug>/{issuers,clients,people}.json and logos/.
The platform team outside any organization keeps its own at the root of <EPC_DATA> (what existed before organizations had their own)."""
import contextlib
import contextvars
from pathlib import Path
from typing import Dict, List, Optional

from epc.core.config import settings
from epc.core.fsutil import read_json, write_json

LOGO_EXT = (".svg", ".png")


_SCOPE: contextvars.ContextVar = contextvars.ContextVar("masterdata_scope", default=None)


def current_scope() -> str:
    """Organization whose data is being read: the one a project belongs to when code asks for it (`scope`), else the one the caller works in."""
    s = _SCOPE.get()
    if s is not None:
        return s
    from epc.modules.identity import public as identity
    return identity.active_org_slug()


@contextlib.contextmanager
def scope(slug: str):
    token = _SCOPE.set(slug or "")
    try:
        yield
    finally:
        _SCOPE.reset(token)


def base() -> Path:
    s = current_scope()
    return settings.data_dir / "orgs" / s if s else settings.data_dir


def _file(name: str) -> Path:
    return base() / name


def load_organization() -> Dict:
    return read_json(_file("organization.json"), {}) or {}


def save_organization(data: Dict) -> None:
    write_json(_file("organization.json"), {"schema_version": "1.0", **data})


def exists(name: str) -> bool:
    return _file(name).is_file()


def load_list(name: str) -> List[Dict]:
    data = read_json(_file(f"{name}.json"), {}) or {}
    return data.get("items", []) if isinstance(data, dict) else []


def save_list(name: str, items: List[Dict]) -> None:
    write_json(_file(f"{name}.json"), {"schema_version": "1.0", "items": items})


def logos_dir() -> Path:
    return base() / "logos"


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


def move_logo(old: str, new: str) -> None:
    for ext in LOGO_EXT:
        src = logos_dir() / f"{old}{ext}"
        if src.is_file():
            src.replace(logos_dir() / f"{new}{ext}")


# ---- project parties: who issues (issuer) and who designs, checks and approves each discipline ----
def parties_file(d: Path) -> Path:
    return d / "workspace" / "00-setup" / "parties.json"


def load_parties(d: Path) -> Dict:
    data = read_json(parties_file(d), {}) or {}
    data.setdefault("issuer", "")
    data.setdefault("team", {})
    return data


def save_parties(d: Path, data: Dict) -> None:
    write_json(parties_file(d), {"schema_version": "1.0", **data})

