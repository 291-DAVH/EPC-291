"""What a file is as a document, for people: its kind (single-line diagram, calculation memo...), what it is about and its place in the sequence engineering develops it."""
import re
from typing import Dict

# The kinds of document in the order engineering develops them (the calculation first, the drawings that come from it after), and the disciplines in the order they usually work.
DOC_TYPES = (("memo", r"(.+)[_-]MC"), ("summary", r"(.+)[_-]SP"), ("lighting", r"LIGHTING[_-](.+)"), ("receptacles", r"RECEPTACLES[_-](.+)"), ("sld", r"SLD[_-](.+)"), ("mld", r"MLD[_-](.+)"), ("layout", r"PLAN[_-](.+)"))
DISCIPLINE_ORDER = ("civil", "mechanical", "electrical", "instrumentation", "hvac", "fire", "telecom")


def document_of(name: str, discipline: str = "") -> Dict:
    """`doc_type` ("other" when the name is not one of the known kinds: it is then shown as it is), `subject` and `order` (discipline first, then the sequence of development)."""
    kind, subject = "other", name
    for key, pattern in DOC_TYPES:
        m = re.fullmatch(pattern, name, re.IGNORECASE)
        if m:
            kind, subject = key, m.group(1)
            break
    rank = DISCIPLINE_ORDER.index(discipline) if discipline in DISCIPLINE_ORDER else len(DISCIPLINE_ORDER)
    step = [k for k, _ in DOC_TYPES].index(kind) if kind != "other" else len(DOC_TYPES)
    return {"doc_type": kind, "subject": subject, "order": rank * 100 + step}
