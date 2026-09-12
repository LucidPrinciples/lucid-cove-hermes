"""WebDAV save/list/read of Jules notes into Nextcloud user `stewart` → AgentSkills/Inbox."""
from __future__ import annotations

import logging
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import quote, unquote

log = logging.getLogger("jules_nc")

JULES_NC_PATH = "AgentSkills/Inbox"
JULES_ARCHIVE_PATH = "AgentSkills/Inbox/Archive"
_DAV_NS = "{DAV:}"
_INBOX_MARKER = "AgentSkills/Inbox"

IMAGE_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".heic", ".heif", ".bmp", ".tif", ".tiff",
}
TEXT_SUFFIXES = {
    ".md", ".txt", ".json", ".js", ".css", ".html", ".htm", ".svg", ".xml",
    ".yml", ".yaml", ".csv", ".map", ".gitignore",
}
_IMAGE_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".heic": "image/heic",
    ".heif": "image/heif",
    ".bmp": "image/bmp",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
}


def nc_config() -> tuple[str, str, str]:
    url = (os.environ.get("STEWART_NC_URL") or os.environ.get("NEXTCLOUD_URL") or "").rstrip("/")
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
    import httpx

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


def _quote_path(path: str) -> str:
    return "/".join(quote(p, safe="") for p in path.split("/") if p)


def _suffix(name: str) -> str:
    base = name.rsplit("/", 1)[-1]
    if "." not in base or base.startswith("."):
        return base.lower() if base.startswith(".") else ""
    return "." + base.rsplit(".", 1)[-1].lower()


def safe_inbox_rel(name: str) -> Optional[str]:
    """Relative path under Inbox, or None if traversal / empty / absolute."""
    if not name or not isinstance(name, str):
        return None
    if any(c in name for c in "\x00\r\n") or len(name) > 1024:
        return None
    cleaned = name.replace("\\", "/").strip()
    if not cleaned or cleaned.startswith("/") or cleaned.startswith("~"):
        return None
    parts = [p for p in cleaned.split("/") if p and p != "."]
    if not parts:
        return None
    if any(p == ".." or p == "~" for p in parts):
        return None
    return "/".join(parts)


def content_disposition_inline(filename: str) -> str:
    """latin-1-safe Content-Disposition (RFC 5987 filename* for non-ASCII)."""
    raw = (filename or "file").replace("\\", "/").rsplit("/", 1)[-1]
    if not raw or any(c in raw for c in "\x00\r\n"):
        raw = "file"
    ascii_name = "".join(
        ch if (32 <= ord(ch) < 127 and ch != '"') else "_" for ch in raw
    )
    fallback = ascii_name.strip("._") or "file"
    encoded = quote(raw, safe="")
    return f'inline; filename="{fallback}"; filename*=UTF-8\'\'{encoded}'


def inbox_rel_from_href(href: str) -> Optional[str]:
    href = unquote(href or "").replace("\\", "/")
    idx = href.find(_INBOX_MARKER)
    if idx < 0:
        return None
    rest = href[idx + len(_INBOX_MARKER) :].lstrip("/")
    return rest or None


def skip_listed(rel: str) -> bool:
    parts = rel.split("/")
    if not parts:
        return True
    if parts[0] == "Archive":
        return True
    if ".git" in parts:
        return True
    return False


def parse_inbox_propfind(xml_text: str) -> list[str]:
    root = ET.fromstring(xml_text)
    files: list[str] = []
    for resp in root.findall(f"{_DAV_NS}response"):
        href = unquote(resp.findtext(f"{_DAV_NS}href") or "")
        rel = inbox_rel_from_href(href)
        if not rel:
            continue
        rel = safe_inbox_rel(rel)
        if not rel:
            continue
        if resp.find(f".//{_DAV_NS}collection") is not None:
            continue
        if skip_listed(rel):
            continue
        files.append(rel)
    return files


def is_image(name: str) -> bool:
    return _suffix(name) in IMAGE_SUFFIXES


def is_text(name: str) -> bool:
    suf = _suffix(name)
    return suf in TEXT_SUFFIXES or suf == ".gitignore"


def guess_media_type(name: str) -> str:
    suf = _suffix(name)
    if suf in _IMAGE_TYPES:
        return _IMAGE_TYPES[suf]
    if suf in {".md", ".txt"}:
        return "text/plain; charset=utf-8"
    if suf == ".json":
        return "application/json"
    if suf == ".js":
        return "text/javascript"
    if suf in {".html", ".htm"}:
        return "text/html; charset=utf-8"
    if suf == ".css":
        return "text/css"
    if suf == ".svg":
        return "image/svg+xml"
    if suf == ".webm":
        return "audio/webm"
    if suf == ".mp3":
        return "audio/mpeg"
    return "application/octet-stream"


async def list_inbox() -> dict:
    url, user, password = nc_config()
    if not url or not user or not password:
        return {"ok": False, "error": "STEWART_NC_PASSWORD not set on Team page", "files": []}
    import httpx

    dav = f"{url}/remote.php/dav/files/{quote(user, safe='')}/{_quote_path(JULES_NC_PATH)}"
    try:
        async with httpx.AsyncClient(auth=(user, password), timeout=60.0, follow_redirects=True) as client:
            r = await client.request("PROPFIND", dav, headers={"Depth": "infinity"})
            if r.status_code != 207:
                r = await client.request("PROPFIND", dav, headers={"Depth": "1"})
            if r.status_code != 207:
                return {"ok": False, "error": f"WebDAV PROPFIND HTTP {r.status_code}", "files": []}
            xml_text = r.text
        files = parse_inbox_propfind(xml_text)
    except ET.ParseError as exc:
        return {"ok": False, "error": f"PROPFIND XML: {exc}", "files": []}
    except Exception as e:
        return {"ok": False, "error": str(e), "files": []}
    return {
        "ok": True,
        "inbox": JULES_NC_PATH,
        "archive": JULES_ARCHIVE_PATH,
        "files": files,
    }


async def fetch_bytes(rel: str) -> tuple[Optional[bytes], Optional[str], int]:
    safe = safe_inbox_rel(rel)
    if not safe:
        return None, "invalid path", 400
    url, user, password = nc_config()
    if not url or not user or not password:
        return None, "STEWART_NC_PASSWORD not set on Team page", 503
    import httpx

    dav = (
        f"{url}/remote.php/dav/files/{quote(user, safe='')}/"
        f"{_quote_path(JULES_NC_PATH)}/{_quote_path(safe)}"
    )
    try:
        async with httpx.AsyncClient(auth=(user, password), timeout=60.0, follow_redirects=True) as client:
            r = await client.get(dav)
        if r.status_code == 404:
            return None, "not found", 404
        if r.status_code != 200:
            return None, f"WebDAV GET HTTP {r.status_code}", 502
        return r.content, None, 200
    except Exception as e:
        return None, str(e), 502
