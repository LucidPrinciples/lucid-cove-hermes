"""Forward house Help messages to the public contact inbox (Haven MC)."""
from __future__ import annotations

import os
from urllib.parse import urlparse

ALLOWED_INGEST_HOSTS = frozenset({"app.lucidtuner.com", "app.lucidcove.org"})
ALLOWED_INGEST_PATHS = frozenset({"/api/contact", "/api/contact/submit"})
DEFAULT_INGEST_URL = "https://app.lucidtuner.com/api/contact/submit"


def ingest_url(raw: str | None = None) -> str | None:
    value = (raw if raw is not None else os.environ.get("LCH_CONTACT_INGEST_URL", DEFAULT_INGEST_URL)).strip()
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    path = parsed.path.rstrip("/") or "/api/contact/submit"
    if parsed.scheme != "https" or host not in ALLOWED_INGEST_HOSTS:
        return None
    if path not in ALLOWED_INGEST_PATHS:
        return None
    return f"https://{host}{path}"


def build_forward_payload(body: dict, *, host: str, path: str, handle: str, connected) -> dict:
    message = str(body.get("message") or "").strip()
    email = str(body.get("email") or "").strip()
    name = str(body.get("name") or body.get("display_name") or "").strip()
    conn = connected
    if conn is True:
        conn = "yes"
    elif conn is False:
        conn = "no"
    return {
        "message": message,
        "email": email,
        "name": name,
        "handle": str(handle or body.get("handle") or "").strip(),
        "product": "lucid-cove-hermes",
        "host": str(host or "").strip(),
        "path": str(path or body.get("path") or "").strip(),
        "connected": conn,
    }
