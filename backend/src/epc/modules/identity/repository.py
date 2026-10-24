"""Database access of the identity module. Rows are returned as plain dicts; no policy lives here."""
import datetime as dt
import uuid
from typing import List, Optional

import sqlalchemy as sa

from epc.core import db
from epc.modules.identity.models import MASTER_EMAIL, audit_log, identities, invitations, memberships, organizations, sessions, user_assignments, users


def now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def as_utc(x: Optional[dt.datetime]) -> Optional[dt.datetime]:
    """SQLite returns naive datetimes: they were stored as UTC."""
    if x is not None and x.tzinfo is None:
        return x.replace(tzinfo=dt.timezone.utc)
    return x


def uid(x) -> uuid.UUID:
    """Ids arrive as text from URLs and sessions; a malformed one matches nothing."""
    if isinstance(x, uuid.UUID):
        return x
    try:
        return uuid.UUID(str(x))
    except (ValueError, AttributeError):
        return uuid.UUID(int=0)


def _row(r) -> Optional[dict]:
    return dict(r._mapping) if r is not None else None


def _one(query) -> Optional[dict]:
    with db.engine().connect() as cx:
        return _row(cx.execute(query).first())


def _all(query) -> List[dict]:
    with db.engine().connect() as cx:
        return [dict(r._mapping) for r in cx.execute(query)]


def _write(stmt):
    with db.engine().begin() as cx:
        return cx.execute(stmt)


# ---- users
def user_by_email(email: str) -> Optional[dict]:
    return _one(sa.select(users).where(sa.func.lower(users.c.email) == email.lower()))


def user_by_username(username: str) -> Optional[dict]:
    return _one(sa.select(users).where(users.c.username == (username or "").lower()))


def user_by_login(identifier: str) -> Optional[dict]:
    """The person is found by email or by alias: an alias never contains '@'."""
    ident = (identifier or "").strip()
    return user_by_email(ident) if "@" in ident else user_by_username(ident)


def user_by_id(user_id) -> Optional[dict]:
    return _one(sa.select(users).where(users.c.id == uid(user_id)))


def list_users() -> List[dict]:
    return _all(sa.select(users).order_by(users.c.email))


def insert_user(email: str, name: str, password_hash: Optional[str], platform_role: str = "user", locale: str = "es-AR", username: Optional[str] = None) -> dict:
    row = {"id": uuid.uuid4(), "email": email.lower(), "username": username, "display_name": name, "password_hash": password_hash, "platform_role": platform_role,
           "locale": locale, "active": True, "created_at": now()}
    _write(sa.insert(users).values(**row))
    return row


def update_user(user_id, **values) -> None:
    _write(sa.update(users).where(users.c.id == uid(user_id)).values(**values))


def count_staff() -> int:
    with db.engine().connect() as cx:
        return cx.execute(sa.select(sa.func.count()).select_from(users).where(users.c.platform_role == "admin", users.c.active.is_(True), users.c.email != MASTER_EMAIL)).scalar() or 0


# ---- organizations
def org_by_slug(slug: str) -> Optional[dict]:
    return _one(sa.select(organizations).where(organizations.c.slug == slug))


def org_by_id(org_id) -> Optional[dict]:
    return _one(sa.select(organizations).where(organizations.c.id == uid(org_id)))


def insert_org(slug: str, name: str, kind: str, seats: int) -> dict:
    row = {"id": uuid.uuid4(), "slug": slug, "name": name, "kind": kind, "seats": seats, "active": True, "created_at": now()}
    _write(sa.insert(organizations).values(**row))
    return row


def update_org(org_id, **values) -> None:
    _write(sa.update(organizations).where(organizations.c.id == uid(org_id)).values(**values))


def list_orgs() -> List[dict]:
    m = sa.select(memberships.c.organization_id, sa.func.count().label("members")).where(memberships.c.active.is_(True)).group_by(memberships.c.organization_id).subquery()
    q = sa.select(organizations, sa.func.coalesce(m.c.members, 0).label("members")).select_from(organizations.outerjoin(m, m.c.organization_id == organizations.c.id)).order_by(organizations.c.name)
    return _all(q)


# ---- memberships
def memberships_of_user(user_id) -> List[dict]:
    q = (sa.select(memberships.c.role, memberships.c.active.label("member_active"), organizations)
         .select_from(memberships.join(organizations, organizations.c.id == memberships.c.organization_id))
         .where(memberships.c.user_id == uid(user_id)).order_by(memberships.c.created_at))
    return _all(q)


def membership(org_id, user_id) -> Optional[dict]:
    return _one(sa.select(memberships).where(memberships.c.organization_id == uid(org_id), memberships.c.user_id == uid(user_id)))


def members(org_id) -> List[dict]:
    q = (sa.select(users.c.id.label("user_id"), users.c.email, users.c.display_name, users.c.last_login_at, memberships.c.role, memberships.c.active)
         .select_from(memberships.join(users, users.c.id == memberships.c.user_id)).where(memberships.c.organization_id == uid(org_id)).order_by(users.c.email))
    return _all(q)


def insert_membership(org_id, user_id, role: str) -> None:
    _write(sa.insert(memberships).values(id=uuid.uuid4(), organization_id=uid(org_id), user_id=uid(user_id), role=role, active=True, created_at=now()))


def update_membership(org_id, user_id, **values) -> None:
    _write(sa.update(memberships).where(memberships.c.organization_id == uid(org_id), memberships.c.user_id == uid(user_id)).values(**values))


def delete_membership(org_id, user_id) -> None:
    _write(sa.delete(memberships).where(memberships.c.organization_id == uid(org_id), memberships.c.user_id == uid(user_id)))


def count_members(org_id, active_only: bool = True, role: Optional[str] = None) -> int:
    q = sa.select(sa.func.count()).select_from(memberships).where(memberships.c.organization_id == uid(org_id))
    if active_only:
        q = q.where(memberships.c.active.is_(True))
    if role:
        q = q.where(memberships.c.role == role)
    with db.engine().connect() as cx:
        return cx.execute(q).scalar() or 0


# ---- sessions
def insert_session(user_id, org_id, token_hash: str, expires: dt.datetime) -> None:
    _write(sa.insert(sessions).values(id=uuid.uuid4(), user_id=uid(user_id), organization_id=uid(org_id) if org_id else None, token_hash=token_hash, created_at=now(), expires_at=expires))


def session_by_hash(token_hash: str) -> Optional[dict]:
    return _one(sa.select(sessions).where(sessions.c.token_hash == token_hash))


def update_session_org(token_hash: str, org_id) -> None:
    _write(sa.update(sessions).where(sessions.c.token_hash == token_hash).values(organization_id=uid(org_id) if org_id else None))


def delete_session(token_hash: str) -> None:
    _write(sa.delete(sessions).where(sessions.c.token_hash == token_hash))


def delete_user_sessions(user_id, keep_hash: Optional[str] = None) -> None:
    q = sa.delete(sessions).where(sessions.c.user_id == uid(user_id))
    if keep_hash:
        q = q.where(sessions.c.token_hash != keep_hash)
    _write(q)


def delete_org_user_sessions(org_id, user_id) -> None:
    _write(sa.delete(sessions).where(sessions.c.user_id == uid(user_id), sessions.c.organization_id == uid(org_id)))


def delete_org_sessions(org_id) -> None:
    _write(sa.delete(sessions).where(sessions.c.organization_id == uid(org_id)))


def purge_expired_sessions() -> None:
    _write(sa.delete(sessions).where(sessions.c.expires_at < now()))


# ---- invitations
def insert_invitation(org_id, email: str, role: str, token_hash: str, invited_by, expires: dt.datetime) -> dict:
    row = {"id": uuid.uuid4(), "organization_id": uid(org_id), "email": email.lower(), "role": role, "token_hash": token_hash, "invited_by": uid(invited_by) if invited_by else None,
           "created_at": now(), "expires_at": expires, "accepted_at": None}
    _write(sa.insert(invitations).values(**row))
    return row


def invitation_by_hash(token_hash: str) -> Optional[dict]:
    return _one(sa.select(invitations).where(invitations.c.token_hash == token_hash))


def invitation_by_id(org_id, inv_id) -> Optional[dict]:
    return _one(sa.select(invitations).where(invitations.c.organization_id == uid(org_id), invitations.c.id == uid(inv_id)))


def pending_invitations(org_id) -> List[dict]:
    return _all(sa.select(invitations).where(invitations.c.organization_id == uid(org_id), invitations.c.accepted_at.is_(None), invitations.c.expires_at > now())
                .order_by(invitations.c.created_at))


def accept_invitation(inv_id) -> None:
    _write(sa.update(invitations).where(invitations.c.id == uid(inv_id)).values(accepted_at=now()))


def delete_invitation(inv_id) -> None:
    _write(sa.delete(invitations).where(invitations.c.id == uid(inv_id)))


# ---- audit log
def insert_audit(actor_id, actor_email: str, action: str, target: str, org_id, detail: dict, ip: str) -> None:
    _write(sa.insert(audit_log).values(id=uuid.uuid4(), organization_id=uid(org_id) if org_id else None, actor_id=uid(actor_id) if actor_id else None, actor_email=actor_email or "",
                                       action=action, target=(target or "")[:300], detail=detail or {}, ip=ip or "", at=now()))


def list_audit(limit: int = 100, action: Optional[str] = None, actor: Optional[str] = None, org_id=None) -> List[dict]:
    q = sa.select(audit_log).order_by(audit_log.c.at.desc()).limit(limit)
    if action:
        q = q.where(audit_log.c.action == action)
    if actor:
        q = q.where(sa.func.lower(audit_log.c.actor_email) == actor.lower())
    if org_id:
        q = q.where(audit_log.c.organization_id == uid(org_id))
    return _all(q)


# ---- assignments of inspectors and auditors
def assigned_orgs(user_id) -> List[dict]:
    q = (sa.select(organizations).select_from(user_assignments.join(organizations, organizations.c.id == user_assignments.c.organization_id))
         .where(user_assignments.c.user_id == uid(user_id)).order_by(organizations.c.name))
    return _all(q)


def set_assignments(user_id, org_ids, granted_by) -> None:
    with db.engine().begin() as cx:
        cx.execute(sa.delete(user_assignments).where(user_assignments.c.user_id == uid(user_id)))
        for o in org_ids:
            cx.execute(sa.insert(user_assignments).values(id=uuid.uuid4(), user_id=uid(user_id), organization_id=uid(o), granted_by=uid(granted_by) if granted_by else None, granted_at=now()))


# ---- linked identities (sign-in with an external provider)
def identity_find(provider: str, subject: str) -> Optional[dict]:
    return _one(sa.select(identities).where(identities.c.provider == provider, identities.c.subject == subject))


def identities_of(user_id) -> List[dict]:
    return _all(sa.select(identities).where(identities.c.user_id == uid(user_id)).order_by(identities.c.created_at))


def insert_identity(user_id, provider: str, subject: str, email: str) -> None:
    _write(sa.insert(identities).values(id=uuid.uuid4(), user_id=uid(user_id), provider=provider, subject=subject, email=(email or "").lower(), created_at=now()))


def delete_identity(user_id, provider: str) -> None:
    _write(sa.delete(identities).where(identities.c.user_id == uid(user_id), identities.c.provider == provider))


def delete_all_accounts(include_audit: bool = False) -> dict:
    """Development only: every account, organization, membership, session, invitation, assignment and linked identity."""
    counts = {}
    with db.engine().begin() as cx:
        tables = [sessions, invitations, user_assignments, identities, memberships] + ([audit_log] if include_audit else []) + [users, organizations]
        for tb in tables:
            counts[tb.name] = cx.execute(sa.delete(tb)).rowcount
    return counts

