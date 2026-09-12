"""Allowlisted Action Board Links — vault markdown as the watch surface.

Not a briefs CMS. Catalog ids only; no arbitrary path reads.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

WATCH_LINKS: tuple[dict[str, str], ...] = (
    {
        "id": "goals-brief",
        "title": "Goals brief",
        "agent": "Hold",
        "description": "Plans Hold — watch for drift. Discuss before ticketing.",
        "relpath": "playbooks/goals-brief.md",
    },
    {
        "id": "tuner-surface",
        "title": "Tuner surface",
        "agent": "Stewart",
        "description": "Free Tuner vs overlay Tune — host, do not rewrite the wizard.",
        "relpath": "playbooks/tuner-surface.md",
    },
    {
        "id": "stewart-handoff",
        "title": "Stewart handoff",
        "agent": "Stewart",
        "description": "Current house next-slice. Compare against the goals brief.",
        "relpath": "team/stewart/handoff.md",
    },
)


def _safe_file(vault: Path, relpath: str) -> Path | None:
    if not relpath or relpath.startswith("/") or "\\" in relpath:
        return None
    parts = Path(relpath).parts
    if not parts or any(p in ("", ".", "..") for p in parts):
        return None
    try:
        root = vault.resolve()
        target = (root / relpath).resolve()
        target.relative_to(root)
    except (OSError, ValueError):
        return None
    return target


def get_item(link_id: str) -> dict[str, str] | None:
    for item in WATCH_LINKS:
        if item["id"] == link_id:
            return item
    return None


def record(vault: Path, item: dict[str, str], *, body: bool = False) -> dict[str, Any]:
    path = _safe_file(vault, item["relpath"])
    exists = bool(path is not None and path.is_file())
    rec: dict[str, Any] = {
        "id": item["id"],
        "title": item["title"],
        "agent": item["agent"],
        "description": item["description"],
        "relpath": item["relpath"],
        "exists": exists,
        "mtime": None,
        "bytes": None,
    }
    if exists and path is not None:
        st = path.stat()
        rec["mtime"] = int(st.st_mtime)
        rec["bytes"] = st.st_size
        if body:
            rec["markdown"] = path.read_text(encoding="utf-8")
    elif body:
        rec["markdown"] = None
    return rec


def list_links(vault: Path) -> list[dict[str, Any]]:
    return [record(vault, item) for item in WATCH_LINKS]


def get_link(vault: Path, link_id: str) -> dict[str, Any] | None:
    item = get_item(link_id)
    if item is None:
        return None
    return record(vault, item, body=True)
