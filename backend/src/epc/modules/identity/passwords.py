"""Password hashing and verification, and the rules a password must meet."""

import base64
import hashlib
import hmac
import os
from typing import Optional

from epc.core.errors import Invalid


MIN_PASSWORD = 10


_DUMMY_HASH = None


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    h = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2 ** 14, r=8, p=1, dklen=32)
    return "scrypt$16384$8$1$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(h).decode()


def verify_password(password: str, stored: Optional[str]) -> bool:
    global _DUMMY_HASH
    if not stored:                                   # same work as a real check: no timing difference between unknown and wrong
        _DUMMY_HASH = _DUMMY_HASH or hash_password("x")
        verify_password(password, _DUMMY_HASH)
        return False
    try:
        _, n, r, p, salt, want = stored.split("$")
        got = hashlib.scrypt(password.encode("utf-8"), salt=base64.b64decode(salt), n=int(n), r=int(r), p=int(p), dklen=32)
        return hmac.compare_digest(got, base64.b64decode(want))
    except (ValueError, TypeError):
        return False


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _check_password(password: str, email: str = "") -> None:
    if len(password or "") < MIN_PASSWORD:
        raise Invalid({"password": f"at least {MIN_PASSWORD} characters"})
    if email and password.lower() == email.lower():
        raise Invalid({"password": "must not be the email"})
