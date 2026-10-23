"""Structured requirements derived from customer input (written by the analysis step, read-only here)."""
from pathlib import Path
from typing import List

from epc.modules.intake import public as intake
from epc.modules.requirements import repository


def list_requirements(d: Path) -> List[dict]:
    titles = intake.titles_by_id(d)
    return [{**r, "source_titles": [titles.get(i, i) for i in r.get("source_intake", [])]} for r in repository.read_all(d)]


def count(d: Path) -> int:
    return len(repository.read_all(d))
