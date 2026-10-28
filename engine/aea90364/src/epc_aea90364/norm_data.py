"""Where the data of the AEA 90364 norm lives: one folder, `data/`, inside this package, so it travels with the engine (also inside a built plugin).

  design-criteria.json   the catalog of base design criteria (the norm reviewer corrects the values there; a project overrides them)
  review.json            who approved which point of the norm data, when, and the fingerprint of the approved value
  review-log.jsonl       every review action, appended
  standard-solutions.json, ../aea_tables.json, ../rules/*.json   the solutions, tables, constants and rules the calculation reads

The backend and the drawing engine ask here instead of building the path themselves.
"""
from pathlib import Path
from typing import Optional

DATA = Path(__file__).resolve().parent / "data"
REVIEW = DATA / "review.json"
REVIEW_LOG = DATA / "review-log.jsonl"
CRITERIA = {"electrical": DATA / "design-criteria.json"}          # AEA 90364 is an electrical norm: one catalog


def criteria_file(discipline: str = "electrical") -> Optional[Path]:
    """The design-criteria catalog of a discipline of this norm, or None when the norm has none for it."""
    f = CRITERIA.get(discipline)
    return f if f and f.is_file() else None
