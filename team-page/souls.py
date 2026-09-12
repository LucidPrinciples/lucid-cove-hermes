"""Public observer profile fields from pack/souls/*.Cove.md.

Do not expose Identity (hard), Boundaries, or other operational SOUL sections.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_ROLE_RE = re.compile(r"^\*\*Role:\*\*\s*(.+)$", re.MULTILINE)
_NAME_RE = re.compile(r"^\*\*Name:\*\*\s*(.+)$", re.MULTILINE)
_FREQ_RE = re.compile(r"\*\*Frequency:\*\*\s*([^|\n]+)")
_ARCH_RE = re.compile(r"\*\*Archetype:\*\*\s*([^\n]+)")
_SECTION_RE = re.compile(r"^## ([^\n]+)\s*\n(.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)
_SOUL_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")


def parse_soul(text: str) -> dict[str, Any]:
    role = ""
    m = _ROLE_RE.search(text or "")
    if m:
        role = m.group(1).strip()
    display_name = ""
    m = _NAME_RE.search(text or "")
    if m:
        display_name = m.group(1).strip()
    frequency = ""
    m = _FREQ_RE.search(text or "")
    if m:
        frequency = m.group(1).strip()
    archetype = ""
    m = _ARCH_RE.search(text or "")
    if m:
        archetype = m.group(1).strip()
    who = ""
    for title, body in _SECTION_RE.findall(text or ""):
        if title.strip().lower() == "who":
            who = body.strip()
            break
    return {
        "name": display_name,
        "role": role,
        "frequency": frequency,
        "archetype": archetype,
        "who": who,
    }


def load_soul(pack: Path, display_name: str) -> dict[str, Any] | None:
    if not _SOUL_NAME_RE.match(display_name or ""):
        return None
    souls_dir = (pack / "souls").resolve()
    path = (souls_dir / f"{display_name}.Cove.md").resolve()
    try:
        path.relative_to(souls_dir)
    except ValueError:
        return None
    if not path.is_file():
        return None
    try:
        return parse_soul(path.read_text(encoding="utf-8"))
    except OSError:
        return None


def avatar_url(static: Path, slug: str) -> str | None:
    if not slug or any(c in slug for c in "/\\"):
        return None
    avatars_dir = (static / "avatars").resolve()
    path = (avatars_dir / f"{slug}.png").resolve()
    try:
        path.relative_to(avatars_dir)
    except ValueError:
        return None
    if path.is_file():
        return f"/static/avatars/{slug}.png"
    return None
