"""Customer input: free-form information sent by the user (voice of customer, user stories, notes, documents)."""
import re
from pathlib import Path
from typing import Dict, List, Tuple

from epc.core.errors import Invalid, TooLarge
from epc.core.fsutil import today
from epc.modules.intake import repository

KINDS = {"voice_of_customer", "user_story", "document", "meeting_note", "report"}
ALLOWED_EXT = {".pdf", ".docx", ".xlsx", ".csv", ".txt", ".md", ".png", ".jpg", ".jpeg", ".dxf", ".dwg", ".eml", ".msg", ".pptx"}
MAX_FILE = 25 * 1024 * 1024
MAX_FILES = 10


def list_inputs(d: Path) -> List[dict]:
    return sorted(repository.read_all(d), key=lambda x: x.get("created", ""), reverse=True)


def clean_name(name: str) -> str:
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(name).name).strip("._") or "file"
    return base[:96]


def add_input(d: Path, kind: str, title: str, text: str, source: str, files: List[Tuple[str, bytes]]) -> dict:
    errors: Dict[str, str] = {}
    if kind not in KINDS:
        errors["kind"] = "invalid"
    if not title.strip():
        errors["title"] = "required"
    if not text.strip() and not files:
        errors["text"] = "write something or attach a file"
    if len(files) > MAX_FILES:
        errors["files"] = f"at most {MAX_FILES} files"
    for name, _ in files:
        if Path(name).suffix.lower() not in ALLOWED_EXT:
            errors["files"] = f"file type not allowed: {Path(name).suffix or name}"
    if errors:
        raise Invalid(errors)
    intake_id = repository.next_id(d)
    saved = []
    for name, data in files:
        if len(data) > MAX_FILE:
            raise TooLarge({"files": f"{name} is larger than 25 MB"})
        clean = clean_name(name)
        repository.save_attachment(d, intake_id, clean, data)
        saved.append({"name": clean, "size": len(data)})
    record = {"id": intake_id, "kind": kind, "title": title.strip(), "text": text.strip(), "source": source.strip() or "Formulario web",
              "author": "", "created": today().isoformat(), "status": "received", "attachments": saved}
    repository.save_record(d, record)
    return record


def input_counts(d: Path) -> dict:
    items = repository.read_all(d)
    return {"total": len(items), "open": sum(1 for x in items if x.get("status") in ("received", "analyzing"))}


def titles_by_id(d: Path) -> Dict[str, str]:
    return {r["id"]: r.get("title", "") for r in repository.read_all(d) if r}
