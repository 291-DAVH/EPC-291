"""What each kind of account may do, written once as data (the server enforces it on every request; the screens only use it to hide what is not allowed).

An account kind is worked out from the account itself:
  staff                the engineering team (platform administrator)
  reviewer             the norm reviewer
  inspector            internal inspector: sees only the organizations assigned to them, can record observations
  auditor              external auditor: sees only the organizations assigned to them, read-only, can record observations
  individual           independent professional (an organization of one person)
  corporate_owner      owner of a company subscription
  corporate_admin      administrator of a company subscription (manages people, cannot touch the owners)
  corporate_member     member of a company subscription

Subjects: `app` (projects, deliverables, inputs, reports of the customer surface), `org` (people of the organization), `observation` (inspection and audit observations),
`norms` (norm review), `identity` (accounts, organizations, assignments, audit log), `console` (the technical console).
Actions: `read` (GET), `write` (any other method), `respond` (answer an observation: a customer's reply, not creating or editing it).
"""
import re
from typing import Dict, Optional, Set

READ, WRITE, RESPOND = "read", "write", "respond"
RW = {READ, WRITE}

ABILITIES: Dict[str, Dict[str, Set[str]]] = {
    "staff": {"*": set(RW)},
    "reviewer": {"norms": set(RW)},
    "inspector": {"app": {READ}, "observation": set(RW)},
    "auditor": {"app": {READ}, "observation": set(RW)},
    "individual": {"app": set(RW), "org": set(RW), "observation": {READ, RESPOND}},
    "corporate_owner": {"app": set(RW), "org": set(RW), "observation": {READ, RESPOND}},
    "corporate_admin": {"app": set(RW), "org": set(RW), "observation": {READ, RESPOND}},
    "corporate_member": {"app": set(RW), "observation": {READ}},
}
SUBJECTS = ("app", "org", "observation", "norms", "identity", "console")
OBSERVATIONS = re.compile(r"^/api/app/projects/[^/]+/[^/]+/observations(/|$)")


def can(kind: str, subject: str, action: str) -> bool:
    ab = ABILITIES.get(kind, {})
    return action in ab.get(subject, set()) or action in ab.get("*", set())


def abilities_of(kind: str) -> Dict[str, list]:
    """For the screens: subject -> allowed actions."""
    return {s: sorted(a for a in (READ, WRITE, RESPOND) if can(kind, s, a)) for s in SUBJECTS if any(can(kind, s, a) for a in (READ, WRITE, RESPOND))}


def subject_of(path: str, method: str, app_paths: Set[str], app_post_paths: Set[str]) -> Optional[str]:
    """The resource a request touches; None for the paths that need only a session (`/api/auth/*`)."""
    if path.startswith("/api/auth/"):
        return None
    if path.startswith("/api/norms/"):
        return "norms"
    if path.startswith("/api/identity/"):
        return "identity"
    if path == "/api/app/org" or path.startswith("/api/app/org/"):
        return "org"
    if OBSERVATIONS.match(path):
        return "observation"
    if path.startswith("/api/app/") or path in app_paths or (path in app_post_paths and method == "POST"):
        return "app"
    return "console"


def allowed(kind: str, subject: str, method: str) -> bool:
    action = READ if method in ("GET", "HEAD", "OPTIONS") else WRITE
    if can(kind, subject, action):
        return True
    return subject == "observation" and method in ("PATCH", "PUT") and can(kind, subject, RESPOND)       # a customer answers an observation
