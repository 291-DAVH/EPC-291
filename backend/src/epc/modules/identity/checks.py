"""Checks on the e-mail, the alias and the slug of a new account or organization."""

import re
from typing import Optional

from epc.core.errors import Conflict, Invalid
from epc.core.text import slugify
from epc.modules.identity import repository as repo


EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


USERNAME = re.compile(r"^[a-z0-9][a-z0-9._-]{2,29}$")


RESERVED_ALIASES = {"admin", "administrator", "root", "support", "staff", "system", "soporte", "ayuda", "help", "null", "none", "me", "api"}


def _check_email(email: str) -> str:
    email = (email or "").strip().lower()
    if not EMAIL.match(email) or len(email) > 254:
        raise Invalid({"email": "not a valid email address"})
    if email.endswith("@dev.invalid"):
        raise Invalid({"email": "this address is reserved"})                      # the development MASTER account can never be registered
    return email


def _check_username(raw: Optional[str], exclude=None) -> Optional[str]:
    """An optional alias to sign in with instead of the email: lowercase, 3 to 30 characters, never an '@' (that is how the two are told apart)."""
    u = (raw or "").strip().lower()
    if not u:
        return None
    if "@" in u or not USERNAME.match(u) or u in RESERVED_ALIASES:
        raise Invalid({"username": "3 to 30 letters, digits, dot, dash or underscore, starting with a letter or digit, no @"})
    other = repo.user_by_username(u)
    if other and str(other["id"]) != str(exclude):
        raise Conflict({"username": "this alias is already taken"})
    return u


def _slug(name: str) -> str:
    base = slugify(name, 40, "org")
    slug, n = base, 1
    while repo.org_by_slug(slug):
        n += 1
        slug = f"{base}-{n}"
    return slug
