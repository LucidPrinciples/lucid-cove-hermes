"""WebDAV save of Jules notes into Nextcloud user `stewart` → AgentSkills/Inbox."""
from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import quote

import httpx

log = logging.getLogger("jules_nc")

JULES_NC_PATH = "AgentSkills/Inbox"


def nc_config() -> tuple[str, str, str]:
    url = (os.environ.get("STEWART_NC_URL") or os.environ.get("NEXTCLOUD_URL") or "https://cloud.cove.lucidcove.org").rstrip("/")
    user = os.environ.get("STEWART_NC_USER", "stewart")
    password = os.environ.get("STEWART_NC_PASSWORD") or os.environ.get("STEWART_NC_APP_PASSWORD") or ""
    return url, user, password


def configured() -> bool:
    url, user, password = nc_config()
    return bool(url and user and password)


def collapse_consecutive_duplicates(text: str) -> str:
    if not text:
        return text
    parts = re.split(r"\n\s*\n", text)
    out: list[str] = []
    prev_norm = None
    for p in parts:
        norm = re.sub(r"\s+", " ", p).strip().lower()
        if norm and prev_norm is not None:
            if norm == prev_norm:
                continue
            if norm.startswith(prev_norm) and len(prev_norm) >= 8:
                out[-1] = p
                prev_norm = norm
                continue
        out.append(p)
        if norm:
            prev_norm = norm
    return "\n\n".join(out)


async def save_bytes(filename: str, content: bytes, content_type: str) -> tuple[bool, Optional[str]]:
    url, user, password = nc_config()
    if not password:
        return False, "STEWART_NC_PASSWORD not set on Team page"
    base = f"{url}/remote.php/dav/files/{quote(user, safe='')}"
    webdav_url = f"{base}/{JULES_NC_PATH}/{quote(filename, safe='')}"
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            for rel in ("AgentSkills", JULES_NC_PATH):
                try:
                    mk = await client.request("MKCOL", f"{base}/{rel}", auth=(user, password))
                    if mk.status_code not in (201, 405, 409, 301, 200):
                        log.debug("MKCOL %s → %s", rel, mk.status_code)
                except Exception as e:
                    log.debug("MKCOL %s: %s", rel, e)
            resp = await client.put(
                webdav_url,
                auth=(user, password),
                content=content,
                headers={"Content-Type": content_type},
            )
            if resp.status_code in (200, 201, 204):
                return True, None
            return False, f"WebDAV PUT {resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        return False, str(e)


async def save_transcript(text: str, filename: str = "", *, hold: bool = False) -> dict:
    text = collapse_consecutive_duplicates((text or "").strip())
    if not text:
        return {"ok": False, "error": "Empty transcript"}
    # Cove Jules sends baseName like "jules-hold-2026-…" or "jules-2026-…" (no .md yet)
    if not filename:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
        filename = f"jules-hold-{ts}" if hold else f"jules-{ts}"
    if hold and "hold" not in filename.lower():
        if filename.startswith("jules-"):
            filename = "jules-hold-" + filename[len("jules-") :]
        else:
            filename = f"jules-hold-{filename}"
    if not filename.endswith(".md"):
        filename += ".md"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lane = "hold (discuss first)" if "hold" in filename else "auto (may ticket)"
    content = (
        f"jules by Julian — {now} (transcribed from voice)\n"
        f"lane: {lane}\n"
        f"nc: stewart / {JULES_NC_PATH}\n\n---\n\n{text}\n"
    )
    ok, err = await save_bytes(filename, content.encode("utf-8"), "text/markdown")
    if ok:
        return {"ok": True, "path": f"{JULES_NC_PATH}/{filename}", "filename": filename, "lane": lane}
    return {"ok": False, "error": err or "save failed"}
