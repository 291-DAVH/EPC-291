"""Structured requirements derived from customer input. The analysis step writes them; people answer their open questions here."""
from pathlib import Path
from typing import List

from epc.core import clock
from epc.core.errors import Invalid, NotFound
from epc.modules.identity import public as identity
from epc.modules.intake import public as intake
from epc.modules.requirements import repository

MAX_ANSWER = 2000


def _view(d: Path, r: dict, titles: dict) -> dict:
    return {**r, "answered_questions": r.get("answered_questions", []), "source_titles": [titles.get(i, i) for i in r.get("source_intake", [])]}


def list_requirements(d: Path) -> List[dict]:
    titles = intake.titles_by_id(d)
    return [_view(d, r, titles) for r in repository.read_all(d)]


def count(d: Path) -> int:
    return len(repository.read_all(d))


def answer_question(d: Path, req_id: str, question: str, answer: str) -> dict:
    """Record who answered an open question and when; the question leaves the open list (the requirement is defined once none is left)."""
    answer = (answer or "").strip()
    if not answer:
        raise Invalid({"answer": "required"})
    if len(answer) > MAX_ANSWER:
        raise Invalid({"answer": f"at most {MAX_ANSWER} characters"})
    reqs = repository.read_all(d)
    req = next((r for r in reqs if r.get("id") == req_id), None)
    if req is None:
        raise NotFound("requirement not found")
    if question not in req.get("open_questions", []):
        raise NotFound("question not found (already answered?)")
    who = identity.current_user()
    req["open_questions"] = [q for q in req["open_questions"] if q != question]
    req.setdefault("answered_questions", []).append({"question": question, "answer": answer, "by": who.get("name") or who.get("email") or "-",
                                                      "by_email": who.get("email", ""), "at": clock.now_aware()})
    if not req["open_questions"] and req.get("status") == "abierto":
        req["status"] = "definido"
    repository.write_all(d, reqs)
    return _view(d, req, intake.titles_by_id(d))
