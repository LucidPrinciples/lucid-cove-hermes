"""Canon mirror lookup — principle × frequency × signal.

Mined from classic Cove mirrors.py. JSON files live in data/mirrors/.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
MIRRORS_DIR = HERE / "data" / "mirrors"

HOUSE_MIRRORS = (
    {
        "id": "scripture-tpt",
        "name": "Scripture — The Passion Translation",
        "type": "text",
        "canon": "Bible (The Passion Translation)",
    },
    {
        "id": "music-mirror",
        "name": "Music Mirror",
        "type": "music",
        "canon": "Popular Music",
    },
    {
        "id": "tao-mirror",
        "name": "Tao Te Ching",
        "type": "text",
        "canon": "Tao Te Ching (Lao Tzu)",
    },
)
HOUSE_MIRROR_BY_ID = {m["id"]: m for m in HOUSE_MIRRORS}
DEFAULT_MIRROR_SOURCES = ("scripture-tpt", "music-mirror")
_mirror_cache: dict[str, dict[str, Any]] = {}


def _parse_mirror_sources(raw: str | None) -> list[str]:
    if raw is None:
        return list(DEFAULT_MIRROR_SOURCES)
    out: list[str] = []
    for part in str(raw).split(","):
        mid = part.strip().lower()
        if mid == "scripture":
            mid = "scripture-tpt"
        if mid in HOUSE_MIRROR_BY_ID and mid not in out:
            out.append(mid)
    return out


def _to_mirror_key(name: str) -> str:
    return (name or "").strip().lower().replace(" ", "_")


def _signal_to_key(signal_type: str) -> str:
    return (
        (signal_type or "")
        .strip()
        .lower()
        .replace("_signal", "")
        .replace(" signal", "")
        .replace(" ", "_")
    )


def _load_mirror(mirror_id: str) -> dict[str, Any] | None:
    if mirror_id not in HOUSE_MIRROR_BY_ID:
        return None
    if mirror_id in _mirror_cache:
        return _mirror_cache[mirror_id]
    path = (MIRRORS_DIR / f"{mirror_id}.json").resolve()
    try:
        path.relative_to(MIRRORS_DIR.resolve())
    except ValueError:
        return None
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    _mirror_cache[mirror_id] = data
    return data


def _collect_all_entries(principle_data: dict) -> list[dict]:
    entries: list[dict] = []
    for freq_data in principle_data.values():
        if not isinstance(freq_data, dict):
            continue
        for entry in freq_data.values():
            if isinstance(entry, dict) and "ref" in entry:
                entries.append(entry)
    return entries


def _entry_dict(entry: dict) -> dict[str, Any]:
    out: dict[str, Any] = {
        "ref": entry.get("ref", ""),
        "text": entry.get("text", ""),
        "thread": entry.get("thread", ""),
    }
    for key in ("artist", "title", "spotify_id", "youtube_id"):
        if entry.get(key):
            out[key] = entry[key]
    return out


def get_mirror_entry(
    principle: str,
    frequency: str | None = None,
    signal_type: str | None = None,
    mirror_id: str | None = None,
) -> dict[str, Any] | None:
    """Look up a canon passage for principle × frequency × signal."""
    mid = mirror_id or ""
    data = _load_mirror(mid)
    if not data:
        return None
    p_key = _to_mirror_key(principle)
    principle_data = data.get(p_key)
    if not principle_data or not isinstance(principle_data, dict):
        return None
    meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
    house = HOUSE_MIRROR_BY_ID.get(mid) or {}
    featured = None
    all_entries: list[dict] = []
    if frequency and signal_type:
        freq_data = principle_data.get(_to_mirror_key(frequency))
        if isinstance(freq_data, dict):
            entry = freq_data.get(_signal_to_key(signal_type))
            if isinstance(entry, dict) and "ref" in entry:
                featured = entry
            all_entries = [v for v in freq_data.values() if isinstance(v, dict) and "ref" in v]
    if not all_entries:
        all_entries = _collect_all_entries(principle_data)
    if not featured and all_entries:
        featured = all_entries[0]
    if not featured:
        return None
    name = (meta.get("name") if isinstance(meta, dict) else None) or house.get("name") or mid
    mtype = (meta.get("type") if isinstance(meta, dict) else None) or house.get("type") or "text"
    canon = (meta.get("canon") if isinstance(meta, dict) else None) or house.get("canon") or ""
    return {
        "mirror_id": mid,
        "mirror_name": name,
        "mirror_type": mtype,
        "canon": canon,
        "principle_key": p_key,
        "featured": _entry_dict(featured),
        "entries": [_entry_dict(e) for e in all_entries],
    }
