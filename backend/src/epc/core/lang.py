"""Interface and document language (`es` or `en`) of a project."""
from typing import Optional

LANGS = ("es", "en")


def from_locale(locale: Optional[str]) -> str:
    """`es` for any Spanish locale (or none), `en` otherwise."""
    return "es" if (locale or "es").lower().startswith("es") else "en"


def pick(lang: Optional[str], locale: Optional[str]) -> str:
    """The requested language when it is one of ours, else the one of the project's locale."""
    return lang if lang in LANGS else from_locale(locale)
