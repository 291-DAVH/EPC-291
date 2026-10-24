"""Sign-in with an external provider (Google, GitHub, Facebook, LinkedIn): OAuth 2 authorization code flow, with PKCE where the provider supports it.

Everything the browser could tamper with (state, PKCE verifier, the data of a person who is signing up) travels in a short-lived cookie signed with the server's secret key
(EPC_SECRET_KEY), so no state is kept on the server. Only the standard library is used for HTTP. A provider is available only when its client id and secret are configured
(EPC_OAUTH_<PROVIDER>_CLIENT_ID and _CLIENT_SECRET).
"""
import base64
import hashlib
import hmac
import json
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Callable, Dict, List, Optional

from epc.core.config import settings

COOKIE = "epc_oauth"                  # the flow in progress (state and PKCE verifier)
PENDING_COOKIE = "epc_oauth_pending"  # a person authenticated by a provider who has no account yet
PATH = "/api/auth/oauth"

PROVIDERS: Dict[str, dict] = {
    "google": {"name": "Google", "authorize": "https://accounts.google.com/o/oauth2/v2/auth", "token": "https://oauth2.googleapis.com/token",
               "userinfo": "https://openidconnect.googleapis.com/v1/userinfo", "scope": "openid email profile", "pkce": True},
    "github": {"name": "GitHub", "authorize": "https://github.com/login/oauth/authorize", "token": "https://github.com/login/oauth/access_token",
               "userinfo": "https://api.github.com/user", "emails": "https://api.github.com/user/emails", "scope": "read:user user:email", "pkce": True},
    "facebook": {"name": "Facebook", "authorize": "https://www.facebook.com/v19.0/dialog/oauth", "token": "https://graph.facebook.com/v19.0/oauth/access_token",
                 "userinfo": "https://graph.facebook.com/me?fields=id,name,email", "scope": "email,public_profile", "pkce": False},
    "linkedin": {"name": "LinkedIn", "authorize": "https://www.linkedin.com/oauth/v2/authorization", "token": "https://www.linkedin.com/oauth/v2/accessToken",
                 "userinfo": "https://api.linkedin.com/v2/userinfo", "scope": "openid profile email", "pkce": True},
}


class OAuthError(Exception):
    """A sign-in with a provider that cannot continue; `code` is shown to the person by the screen."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


# ---------------------------------------------------------------- availability
def enabled(include_unconfigured: bool = False) -> List[dict]:
    return [{"id": pid, "name": p["name"], "configured": bool(settings.oauth.get(pid))} for pid, p in PROVIDERS.items() if include_unconfigured or settings.oauth.get(pid)]


def require(provider: str) -> dict:
    if provider not in PROVIDERS or not settings.oauth.get(provider):
        raise OAuthError("provider_unavailable")
    return PROVIDERS[provider]


def redirect_uri(provider: str) -> str:
    return f"{settings.public_url}{PATH}/{provider}/callback"          # to register at the provider


# ---------------------------------------------------------------- signed cookies
def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def sign(payload: dict, ttl: int = 600) -> str:
    body = _b64(json.dumps({**payload, "exp": int(time.time()) + ttl}, separators=(",", ":")).encode())
    return body + "." + _b64(hmac.new(settings.secret_key.encode(), body.encode(), hashlib.sha256).digest())


def unsign(value: str) -> Optional[dict]:
    try:
        body, sig = (value or "").split(".", 1)
        if not hmac.compare_digest(sig, _b64(hmac.new(settings.secret_key.encode(), body.encode(), hashlib.sha256).digest())):
            return None
        data = json.loads(_unb64(body))
        return data if data.get("exp", 0) >= time.time() else None
    except (ValueError, TypeError, json.JSONDecodeError):
        return None


# ---------------------------------------------------------------- the flow
def start(provider: str, extra: dict) -> tuple:
    """(authorization URL, signed flow cookie). `extra` is what must come back to the callback (mode, invitation, who is linking)."""
    p = require(provider)
    state, verifier = secrets.token_urlsafe(24), secrets.token_urlsafe(48)
    params = {"client_id": settings.oauth[provider]["client_id"], "redirect_uri": redirect_uri(provider), "response_type": "code", "scope": p["scope"], "state": state}
    if p["pkce"]:
        params.update(code_challenge=_b64(hashlib.sha256(verifier.encode()).digest()), code_challenge_method="S256")
    return p["authorize"] + "?" + urllib.parse.urlencode(params), sign({"p": provider, "s": state, "v": verifier, **extra})


def _urlopen_json(url: str, data: Optional[dict] = None, headers: Optional[dict] = None) -> dict:
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers={"Accept": "application/json", "User-Agent": "EPC-291", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, ValueError, OSError):
        raise OAuthError("provider_error")


_http: Callable = _urlopen_json


def set_http(fn: Optional[Callable]) -> None:
    """Tests replace the network with a fake provider; None restores it."""
    global _http
    _http = fn or _urlopen_json


def _truthy(v) -> bool:
    return v is True or str(v).lower() == "true"


def profile(provider: str, code: str, verifier: str) -> dict:
    """Exchange the code for a token and read who the person is: {subject, email, email_verified, name}. An email counts as verified only when the provider says so."""
    p = require(provider)
    form = {"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri(provider), "client_id": settings.oauth[provider]["client_id"],
            "client_secret": settings.oauth[provider]["client_secret"]}
    if p["pkce"]:
        form["code_verifier"] = verifier
    token = _http(p["token"], form, None).get("access_token")
    if not token:
        raise OAuthError("provider_error")
    auth = {"Authorization": f"Bearer {token}"}
    info = _http(p["userinfo"], None, auth)
    if provider == "github":
        emails = _http(p["emails"], None, auth)
        emails = emails if isinstance(emails, list) else []
        best = next((e for e in emails if e.get("primary") and e.get("verified")), None) or next((e for e in emails if e.get("verified")), None)
        return {"subject": str(info.get("id", "")), "email": (best or {}).get("email", "").lower(), "email_verified": bool(best), "name": info.get("name") or info.get("login") or ""}
    if provider == "facebook":
        return {"subject": str(info.get("id", "")), "email": (info.get("email") or "").lower(), "email_verified": False, "name": info.get("name") or ""}       # Facebook does not vouch for the address
    return {"subject": str(info.get("sub", "")), "email": (info.get("email") or "").lower(), "email_verified": _truthy(info.get("email_verified")), "name": info.get("name") or ""}
