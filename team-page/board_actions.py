"""Generated Action list from house state. Finished artifacts live on Links."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import connect as lch_connect
import watch_links

TUNER_HREF = "https://app.lucidtuner.com"
GOALS_REL = Path("playbooks") / "goals-brief.md"
GOALS_TEMPLATE = """# Goals Brief

Standing goals for this house. Creating this file from Action moves it to Links.

## Now

-

## Next

-
"""


def _vault_file(vault: Path, rel: Path) -> Path:
    vault_r = vault.resolve()
    path = (vault_r / rel).resolve()
    path.relative_to(vault_r)
    return path


def _connected(vault: Path) -> bool:
    return bool(lch_connect.load_state(vault).get("connected"))


def _brief_exists(vault: Path) -> bool:
    try:
        return _vault_file(vault, GOALS_REL).is_file()
    except ValueError:
        return False


def list_actions(vault: Path) -> dict[str, list[dict[str, Any]]]:
    standing: list[dict[str, Any]] = []
    if not _connected(vault):
        standing.append(
            {
                "id": "connect-lucid-tuner",
                "kind": "standing",
                "title": "Connect Lucid Tuner",
                "href": TUNER_HREF,
                "cta": "Create account or sign in",
            }
        )
    if not _brief_exists(vault):
        standing.append(
            {
                "id": "create-goals-brief",
                "kind": "standing",
                "title": "Create Goals Brief",
                "cta": "Create brief",
            }
        )
    return {"standing": standing, "daily": []}


def present_links(vault: Path) -> list[dict[str, Any]]:
    links = [rec for rec in watch_links.list_links(vault) if rec.get("exists")]
    if _connected(vault):
        links.insert(
            0,
            {
                "id": "open-lucid-tuner",
                "title": "Open Lucid Tuner",
                "agent": "Lucid Tuner",
                "description": "This house is latched. Open the Lucid Tuner account.",
                "relpath": "",
                "exists": True,
                "href": TUNER_HREF,
                "kind": "external",
            },
        )
    return links


def create_goals_brief(vault: Path) -> dict[str, Any]:
    path = _vault_file(vault, GOALS_REL)
    if path.is_file():
        return {"ok": True, "created": False}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(GOALS_TEMPLATE, encoding="utf-8")
    return {"ok": True, "created": True}
