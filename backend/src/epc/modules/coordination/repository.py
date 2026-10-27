"""Files of the coordination between disciplines inside workspace/02-engineering/coordination/: what each discipline issued, the state of each clash, the threads, the data exchanged
and the rules of the project. Nothing here is a drawing: the drawings stay in the layout module, each in its own discipline."""
import re
from pathlib import Path
from typing import Any, List, Optional

from epc.core.config import settings
from epc.core.errors import Invalid
from epc.core.fsutil import read_json, write_json

ROOT = ("workspace", "02-engineering", "coordination")
DISCIPLINE = re.compile(r"^[A-Za-z0-9_]{1,48}$")


def base(d: Path) -> Path:
    return d.joinpath(*ROOT)


def read(d: Path, name: str, default: Any) -> Any:
    return read_json(base(d) / name, default)


def write(d: Path, name: str, data: Any) -> None:
    write_json(base(d) / name, data)


def discipline_id(value: str) -> str:
    if not DISCIPLINE.match(value or ""):
        raise Invalid({"discipline": "a discipline is a name of letters, digits and underscores"})
    return value


def emission_dir(d: Path, discipline: str) -> Path:
    return base(d) / "emissions" / discipline_id(discipline)


def emission_revs(d: Path, discipline: str) -> List[int]:
    folder = emission_dir(d, discipline)
    return sorted(int(p.stem) for p in folder.glob("*.json")) if folder.is_dir() else []


def save_emission(d: Path, discipline: str, data: dict) -> int:
    rev = (emission_revs(d, discipline) or [0])[-1] + 1
    write_json(emission_dir(d, discipline) / f"{rev:04d}.json", {**data, "rev": rev})
    return rev


def load_emission(d: Path, discipline: str, rev: Optional[int] = None) -> Optional[dict]:
    revs = emission_revs(d, discipline)
    pick = rev if rev is not None else (revs[-1] if revs else None)
    return read_json(emission_dir(d, discipline) / f"{pick:04d}.json", None) if pick in revs else None


def emitted_disciplines(d: Path) -> List[str]:
    folder = base(d) / "emissions"
    return sorted(p.name for p in folder.iterdir() if p.is_dir() and emission_revs(d, p.name)) if folder.is_dir() else []


def company_rules_file(slug: str) -> Path:
    return settings.data_dir / "orgs" / slug / "clash-rules.json"
