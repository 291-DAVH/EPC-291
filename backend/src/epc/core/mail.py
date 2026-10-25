"""Outgoing e-mail, with the standard library only (smtplib).

Configuration (environment): EPC_SMTP_HOST, EPC_SMTP_PORT (587), EPC_SMTP_USER, EPC_SMTP_PASSWORD, EPC_SMTP_FROM, EPC_SMTP_TLS (starttls | ssl | none, default starttls).
Without EPC_SMTP_HOST: in development (EPC_ENV=dev) the message is written to the log and to an `outbox` folder next to the data folder, so the developer can read the code
that would have been mailed; in any other environment sending fails with a clear error (nothing is silently dropped). Tests replace the transport with `set_transport`.
"""
import logging
import os
import smtplib
import ssl
import time
from email.message import EmailMessage
from pathlib import Path
from typing import Callable, Optional

from epc.core.config import settings
from epc.core.errors import Failure

log = logging.getLogger("epc.mail")
_transport: Optional[Callable[[str, str, str], None]] = None


def set_transport(fn: Optional[Callable[[str, str, str], None]]) -> None:
    """Replace the delivery (tests): `fn(to, subject, body)`; None restores the configured one."""
    global _transport
    _transport = fn


def configured() -> bool:
    return bool(os.environ.get("EPC_SMTP_HOST", "").strip())


def _smtp(to: str, subject: str, body: str) -> None:
    host, port = os.environ["EPC_SMTP_HOST"].strip(), int(os.environ.get("EPC_SMTP_PORT", "587"))
    user, password = os.environ.get("EPC_SMTP_USER", ""), os.environ.get("EPC_SMTP_PASSWORD", "")
    sender, mode = os.environ.get("EPC_SMTP_FROM", user or "no-reply@localhost"), os.environ.get("EPC_SMTP_TLS", "starttls").lower()
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = sender, to, subject
    msg.set_content(body)
    ctx = ssl.create_default_context()
    try:
        with (smtplib.SMTP_SSL(host, port, context=ctx, timeout=20) if mode == "ssl" else smtplib.SMTP(host, port, timeout=20)) as s:
            if mode == "starttls":
                s.starttls(context=ctx)
            if user:
                s.login(user, password)
            s.send_message(msg)
    except (OSError, smtplib.SMTPException) as e:
        log.warning("mail to %s failed: %s", to, e)
        raise Failure("the e-mail could not be sent: try again later")


def _outbox(to: str, subject: str, body: str) -> None:
    folder = Path(settings.data_dir).parent / "outbox"
    folder.mkdir(parents=True, exist_ok=True)
    safe = "".join(c if c.isalnum() else "_" for c in to)[:60]
    (folder / f"{int(time.time())}-{safe}.txt").write_text(f"To: {to}\nSubject: {subject}\n\n{body}\n", encoding="utf-8")
    log.warning("DEV MAIL to %s | %s | %s", to, subject, body.replace("\n", " ")[:200])


def send(to: str, subject: str, body: str) -> None:
    if _transport is not None:
        return _transport(to, subject, body)
    if configured():
        return _smtp(to, subject, body)
    if settings.env == "dev":
        return _outbox(to, subject, body)
    raise Failure("e-mail delivery is not configured (EPC_SMTP_HOST)")
