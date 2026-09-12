"""House tuning-model helpers (stdlib). Independent of Hermes orchestrator."""
from __future__ import annotations

import json
import re
from typing import Any, Callable
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

MODEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
LOOPBACK = frozenset({"127.0.0.1", "localhost", "::1"})


def normalize_model(raw: Any) -> str | None:
    name = str(raw or "").strip()
    if not name or len(name) > 128:
        return None
    if "/" in name or "\\" in name or ".." in name:
        return None
    if not MODEL_RE.fullmatch(name):
        return None
    return name


def tags_url(ollama_base_url: str) -> str | None:
    parsed = urlparse(str(ollama_base_url or "").strip())
    if parsed.scheme not in ("http", "https"):
        return None
    host = (parsed.hostname or "").lower()
    if host not in LOOPBACK:
        return None
    return f"{parsed.scheme}://{parsed.netloc}/api/tags"


def default_fetch_tags(url: str) -> list[str]:
    req = Request(url, headers={"User-Agent": "LucidCove-Cove/1.0"})
    with urlopen(req, timeout=2) as resp:
        data = json.loads(resp.read().decode("utf-8", "replace") or "{}")
    names: list[str] = []
    for item in data.get("models") or []:
        if isinstance(item, dict):
            names.append(str(item.get("name") or item.get("model") or ""))
        else:
            names.append(str(item))
    return names


def list_models(
    *,
    current: str,
    ollama_base_url: str,
    fetch_tags: Callable[[str], list[str]] | None = None,
) -> list[str]:
    current_n = normalize_model(current) or "qwen3:8b"
    out = [current_n]
    url = tags_url(ollama_base_url)
    if not url:
        return out
    fetch = fetch_tags or default_fetch_tags
    try:
        raw = fetch(url)
    except (URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError):
        return out
    except Exception:
        return out
    for name in raw or []:
        n = normalize_model(name)
        if n and n not in out:
            out.append(n)
    return out
