"""Shared helpers for the standard-ingest scripts (stdlib only, except pypdf/pypdfium2 where noted)."""
import json
import re
import unicodedata
from pathlib import Path

PLATFORM = Path(__file__).resolve().parents[3]            # .../platform
WORKSPACE = PLATFORM.parent
DEV_KNOWLEDGE = WORKSPACE / "local" / "dev-knowledge"
SCHEMAS = WORKSPACE / "shared" / "schemas"
SHINGLE = 12                                              # consecutive words that count as verbatim copying


def read_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8-sig"))


def write_json(p, obj):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def norm_words(text):
    t = unicodedata.normalize("NFKD", text.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.findall(r"[a-z0-9]+", t)


def shingles(words, n=SHINGLE):
    return {" ".join(words[i:i + n]) for i in range(max(0, len(words) - n + 1))}


def standard_dir(arg):
    """Accept a folder path or '<CC>/<ID>' / '<ID>' (searched under dev-knowledge/standards)."""
    p = Path(arg)
    if p.is_dir():
        return p.resolve()
    base = DEV_KNOWLEDGE / "standards"
    for cand in (base / arg, *base.glob(f"*/{arg}")):
        if cand.is_dir():
            return cand
    raise SystemExit(f"standard folder not found: {arg}")


def source_text_words(sdir):
    """All words of the extracted text layer of a standard, or None when it has no text."""
    pages = sorted(Path(sdir).glob("extracted/*/pages/p*.txt"))
    if not pages:
        return None
    words = []
    for f in pages:
        words.extend(norm_words(f.read_text(encoding="utf-8")))
    return words or None
