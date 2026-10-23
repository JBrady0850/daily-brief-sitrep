"""Sends the newsletter by SMTP (any email provider that offers it).

Mail settings come from environment variables or from smtp.json in your own
data folder, never from the repository:

    SMTP_HOST      smtp.gmail.com, for example
    SMTP_PORT      587 (STARTTLS, the default) or 465 (SSL)
    SMTP_USER      the account name, usually your address
    SMTP_PASSWORD  an app password, not your normal password
    SMTP_SECURITY  starttls, ssl or none (none only for a local test server)
    MAIL_FROM      sender address (defaults to SMTP_USER)
    MAIL_TO        one or more recipients, separated by commas

The password is never printed, logged or sent back to the app.
"""
from __future__ import annotations

import os
import re
import smtplib
import ssl
from dataclasses import dataclass, field
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid
from typing import Callable, Mapping, Optional

from . import store

_ADDR = re.compile(r"^[^@\s,;]+@[^@\s,;]+\.[^@\s,;]+$")


class MailConfigError(ValueError):
    pass


@dataclass
class SmtpSettings:
    host: str
    port: int
    user: str
    password: str = field(repr=False)
    security: str
    sender: str
    recipients: list
    from_name: str = ""

    def describe(self) -> str:
        return f"{self.host}:{self.port} ({self.security}), {len(self.recipients)} recipient(s)"


def split_addresses(v: object) -> list:
    if isinstance(v, (list, tuple)):
        parts = [str(x) for x in v]
    else:
        parts = re.split(r"[,;\s]+", str(v or ""))
    return [p.strip() for p in parts if p.strip()]


def load_settings(env: Optional[Mapping[str, str]] = None, saved: Optional[dict] = None,
                  to_override: Optional[list] = None, from_name: str = "") -> SmtpSettings:
    """Environment variables win over smtp.json; to_override wins over both."""
    env = os.environ if env is None else env
    if saved is None:
        saved = store.read_json(store.path(store.SMTP), {}) or {}

    def pick(key: str, saved_key: str) -> str:
        v = env.get(key, "")
        return str(v).strip() if str(v).strip() else str(saved.get(saved_key, "") or "").strip()

    host = pick("SMTP_HOST", "host")
    port_raw = pick("SMTP_PORT", "port") or "587"
    user = pick("SMTP_USER", "user")
    password = env.get("SMTP_PASSWORD", "") or str(saved.get("password", "") or "")
    security = (pick("SMTP_SECURITY", "security") or "").lower()
    sender = pick("MAIL_FROM", "sender") or user
    recipients = split_addresses(to_override) if to_override else split_addresses(
        env.get("MAIL_TO", "") or saved.get("to", []))
    missing = [name for name, val in (("SMTP_HOST", host), ("SMTP_USER", user), ("SMTP_PASSWORD", password),
                                      ("MAIL_TO", recipients)) if not val]
    if missing:
        raise MailConfigError("Mail is not set up. Missing: " + ", ".join(missing) + ".")
    try:
        port = int(port_raw)
    except ValueError as exc:
        raise MailConfigError("SMTP_PORT must be a number.") from exc
    if not security:
        security = "ssl" if port == 465 else "starttls"
    if security not in ("starttls", "ssl", "none"):
        raise MailConfigError("SMTP_SECURITY must be starttls, ssl or none.")
    bad = [a for a in recipients + [sender] if not _ADDR.match(a)]
    if bad:
        raise MailConfigError("These do not look like email addresses: " + ", ".join(bad))
    return SmtpSettings(host, port, user, password, security, sender, recipients,
                        from_name or str(saved.get("from_name", "") or ""))


def build_message(subject: str, text: str, html: str, sender: str, recipients: list,
                  from_name: str = "") -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr((from_name, sender)) if from_name else sender
    msg["To"] = ", ".join(recipients)
    msg["Date"] = formatdate(localtime=False)
    msg["Message-ID"] = make_msgid(domain=sender.split("@")[-1])
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")
    return msg


def send(msg: EmailMessage, s: SmtpSettings, smtp_factory: Callable = smtplib.SMTP,
         ssl_factory: Callable = smtplib.SMTP_SSL, timeout: int = 30) -> None:
    context = ssl.create_default_context()
    if s.security == "ssl":
        with ssl_factory(s.host, s.port, timeout=timeout, context=context) as conn:
            conn.login(s.user, s.password)
            conn.send_message(msg, from_addr=s.sender, to_addrs=s.recipients)
        return
    with smtp_factory(s.host, s.port, timeout=timeout) as conn:
        conn.ehlo()
        if s.security == "starttls":
            conn.starttls(context=context)
            conn.ehlo()
        if s.user and s.password and s.security != "none":
            conn.login(s.user, s.password)
        conn.send_message(msg, from_addr=s.sender, to_addrs=s.recipients)


def save_settings(values: dict) -> None:
    """Stores mail settings in smtp.json (owner-only where the system allows).

    An empty password keeps the saved one, so the app never needs to read it back,
    but only while the server, port, security and user stay the same: a saved
    password is never sent to a server it was not typed for.
    """
    p = store.path(store.SMTP)
    current = store.read_json(p, {}) or {}
    out = {k: current.get(k, "") for k in ("host", "port", "user", "password", "security", "sender", "to", "from_name")}
    for k in ("host", "user", "security", "sender", "from_name"):
        if k in values:
            out[k] = str(values.get(k) or "").strip()
    if "port" in values:
        out["port"] = str(values.get("port") or "").strip()
    if "to" in values:
        out["to"] = split_addresses(values.get("to"))
    if values.get("password"):
        out["password"] = str(values["password"])
    elif any(str(out[k]) != str(current.get(k, "")) for k in ("host", "port", "security", "user")):
        out["password"] = ""
    store.write_json(p, out, private=True)


def public_settings() -> dict:
    """Mail settings without the password, for the app's settings page."""
    saved = store.read_json(store.path(store.SMTP), {}) or {}
    env_keys = [k for k in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD", "MAIL_TO") if os.environ.get(k)]
    problem = ""
    try:
        configured = bool(load_settings(saved=saved))
    except MailConfigError as exc:
        configured, problem = False, str(exc)
    return {"host": saved.get("host", ""), "port": saved.get("port", ""), "user": saved.get("user", ""),
            "security": saved.get("security", ""), "sender": saved.get("sender", ""), "to": saved.get("to", []),
            "from_name": saved.get("from_name", ""), "has_password": bool(saved.get("password")),
            "env_overrides": env_keys, "configured": configured, "problem": problem}
