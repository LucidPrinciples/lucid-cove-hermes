"""Hermes-connect: reuse Cove connect-key + CF-65 carry into this house."""
from __future__ import annotations

import json
import logging
import os
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger("lch.connect")

HUB_URL = (
    os.environ.get("LP_REGISTRY_URL")
    or os.environ.get("LCH_HUB_URL")
    or "https://app.lucidcove.org"
)
HUB_UA = "LucidCove-Cove/1.0"


def _hub_headers(extra: dict[str, str] | None = None) -> dict[str, str]:
    headers = {"Content-Type": "application/json", "User-Agent": HUB_UA}
    if extra:
        headers.update(extra)
    return headers


def parse_connect_key(raw: str) -> tuple[str, str]:
    t = (raw or "").strip()
    if not t:
        return "", ""
    if ":" in t:
        handle, token = t.split(":", 1)
        return handle.lstrip("@").strip().lower(), token.strip()
    return "", t


def operator_dir(vault: Path) -> Path:
    return vault / "tuner"


def operator_token_path(vault: Path) -> Path:
    return operator_dir(vault) / "operator.token"


def operator_state_path(vault: Path) -> Path:
    return operator_dir(vault) / "operator.json"


def load_state(vault: Path) -> dict[str, Any]:
    path = operator_state_path(vault)
    if not path.is_file():
        return {"connected": False}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"connected": False}
    if not isinstance(data, dict):
        return {"connected": False}
    handle = str(data.get("handle") or "").lstrip("@").strip().lower()
    data["handle"] = handle
    data["connected"] = bool(handle)
    return data


def save_operator(vault: Path, handle: str, token: str) -> None:
    d = operator_dir(vault)
    d.mkdir(parents=True, exist_ok=True)
    token_path = operator_token_path(vault)
    token_path.write_text(token, encoding="utf-8")
    token_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    state = load_state(vault)
    state["connected"] = True
    state["handle"] = handle
    state["connected_at"] = datetime.now(timezone.utc).isoformat()
    operator_state_path(vault).write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def _write_carry(vault: Path, carry: dict[str, Any]) -> dict[str, Any]:
    state = load_state(vault)
    state["carry"] = carry
    operator_state_path(vault).write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    return state


async def verify_claim(
    handle: str,
    token: str,
    *,
    hub_url: str | None = None,
    client: Any = None,
) -> dict[str, Any]:
    url = (hub_url or HUB_URL).rstrip("/") + "/api/registry/verify-claim"
    own = client is None
    if own:
        import httpx
        client = httpx.AsyncClient(timeout=20)
    try:
        resp = await client.post(
            url,
            json={"handle": handle, "token": token},
            headers=_hub_headers(),
        )
        data = resp.json() if resp.content else {}
        if not isinstance(data, dict):
            return {"ok": False, "reason": "verify-claim failed"}
        return data
    except Exception:
        log.warning("verify-claim transport failed")
        return {"ok": False, "reason": "Could not reach the hub to verify that connect key."}
    finally:
        if own:
            await client.aclose()


async def carry_export(
    token: str,
    *,
    hub_url: str | None = None,
    client: Any = None,
) -> dict[str, Any]:
    url = (hub_url or HUB_URL).rstrip("/") + "/api/registry/carry-export"
    own = client is None
    if own:
        import httpx
        client = httpx.AsyncClient(timeout=60)
    try:
        sessions: list[dict[str, Any]] = []
        after = 0
        while True:
            resp = await client.post(
                url,
                json={"after": after},
                headers=_hub_headers({"X-Operator-Token": token}),
            )
            data = resp.json() if resp.content else {}
            if not isinstance(data, dict) or not data.get("ok"):
                reason = "carry-export failed"
                if isinstance(data, dict):
                    reason = str(data.get("reason") or data.get("error") or reason)
                return {"ok": False, "reason": reason, "sessions": sessions}
            batch = data.get("sessions") or []
            if not isinstance(batch, list):
                batch = []
            sessions.extend(row for row in batch if isinstance(row, dict))
            nxt = data.get("next_after")
            if not batch or nxt is None:
                break
            after = int(nxt)
        return {"ok": True, "sessions": sessions, "total": len(sessions)}
    except Exception:
        log.warning("carry-export transport failed")
        return {"ok": False, "reason": "Could not reach the hub to carry tunings.", "sessions": []}
    finally:
        if own:
            await client.aclose()


def map_hub_session(row: dict[str, Any]) -> dict[str, Any]:
    sid = str(row.get("session_id") or row.get("id") or "").strip()
    return {
        "session_id": sid,
        "date": row.get("date") or "",
        "time": row.get("time") or "",
        "day_of_week": row.get("day_of_week") or "",
        "frequency": row.get("frequency") or "",
        "signal_type": row.get("signal_type") or "",
        "principle": row.get("principle") or "",
        "tuning_key": row.get("tuning_key") or "",
        "echo_filename": row.get("echo_filename") or "",
        "audio_url": row.get("audio_url") or "",
        "context": row.get("context") or "",
        "entry_mode": row.get("entry_mode") or "tuner",
        "initial_state": row.get("initial_state") or "",
        "carried": True,
    }


def merge_sessions(vault: Path, incoming: list[dict[str, Any]]) -> int:
    path = operator_dir(vault) / "sessions.json"
    existing: list[dict[str, Any]] = []
    if path.is_file():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                existing = [row for row in raw if isinstance(row, dict)]
        except (json.JSONDecodeError, OSError):
            existing = []
    by_id = {str(row.get("session_id")): row for row in existing if row.get("session_id")}
    added = 0
    for row in incoming:
        mapped = map_hub_session(row)
        if not mapped["session_id"]:
            continue
        if mapped["session_id"] in by_id:
            continue
        by_id[mapped["session_id"]] = mapped
        added += 1
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(list(by_id.values()), indent=2) + "\n", encoding="utf-8")
    return added


async def connect_operator(
    vault: Path,
    handle: str,
    token: str,
    *,
    hub_url: str | None = None,
    http: Any = None,
) -> dict[str, Any]:
    handle = (handle or "").lstrip("@").strip().lower()
    token = (token or "").strip()
    if not handle or not token:
        return {"ok": False, "reason": "handle and token are required"}
    claim = await verify_claim(handle, token, hub_url=hub_url, client=http)
    if not claim.get("ok"):
        return {
            "ok": False,
            "reason": claim.get("reason") or "That connect key doesn't match this handle.",
        }
    save_operator(vault, handle, token)
    carry = await carry_export(token, hub_url=hub_url, client=http)
    if carry.get("ok"):
        imported = merge_sessions(vault, carry.get("sessions") or [])
        _write_carry(vault, {"status": "complete", "imported": imported})
        return {"ok": True, "handle": handle, "carry": {"status": "complete", "imported": imported}}
    _write_carry(vault, {"status": "error", "reason": carry.get("reason")})
    return {
        "ok": True,
        "handle": handle,
        "carry": {"status": "error", "reason": carry.get("reason")},
    }
