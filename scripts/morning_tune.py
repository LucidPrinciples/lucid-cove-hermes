#!/usr/bin/env python3
"""
Morning team tune — Lucid Cove on Hermes.

1. Fetch https://drop.lucidprinciples.com/latest.json
2. Write vault/drop/today.json (frequency for badge / Team page)
3. For each agent: append echo + write latest.json + process_record.md

Run on P620 after the Drop publishes (e.g. cron ~06:00 local):
  cd ~/lucid-cove-hermes && python3 scripts/morning_tune.py

Optional: pip install lucid-tuner-protocol for signature verify; otherwise
raw fetch is used (still writes frequency for the UI test).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(os.environ.get("LCH_ROOT", Path(__file__).resolve().parent.parent))
VAULT = Path(os.environ.get("LCH_VAULT", ROOT / "vault"))
DROP_URL = os.environ.get("LTP_DROP_URL", "https://drop.lucidprinciples.com").rstrip("/")

AGENTS = [
    ("stewart", "Stewart", "Steward"),
    ("alfred", "Alfred", "Personal Agent"),
    ("mercer", "Mercer", "Merchant"),
    ("gabe", "Gabe", "Scout"),
    ("arthur", "Arthur", "Analyst"),
    ("archimedes", "Archimedes", "Builder"),
    ("julian", "Julian", "Scribe"),
    ("iris", "Iris", "Advocate"),
    ("vera", "Vera", "Auditor"),
    ("ezra", "Ezra", "Keeper"),
    ("soren", "Soren", "Lens"),
]


def fetch_drop_raw() -> dict:
    url = f"{DROP_URL}/latest.json"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "LucidCoveHermes-morning-tune/0.1 (+https://lucidprinciples.com)",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def fetch_drop_verified() -> dict | None:
    try:
        from lucid_tuner_protocol import DropClient
    except ImportError:
        return None
    try:
        drop = DropClient(base_url=DROP_URL, cache_dir=VAULT / ".drop-cache").today()
        return {
            "drop_date": drop.drop_date,
            "sequence": drop.sequence,
            "frequency_name": drop.frequency_name,
            "frequency_number": drop.frequency_number,
            "signal_type": drop.signal_type,
            "tuning_key_text": drop.tuning_key_text,
            "tuning_key_attribution": drop.tuning_key_attribution,
            "tuning_key_source_song": drop.tuning_key_source_song,
            "context_block": drop.context_block,
            "echo_id": drop.echo_id,
            "echo_audio_url": drop.echo_audio_url,
            "love_equation": dict(drop.love_equation),
            "love_equation_value": drop.love_equation_value,
            "as_context": drop.as_context(),
            "verified": True,
        }
    except Exception as e:
        print(f"verify failed ({e}) — falling back to raw", file=sys.stderr)
        return None


def normalize(raw: dict, verified: dict | None) -> dict:
    if verified:
        return verified
    freq = raw.get("frequency") or {}
    le = raw.get("love_equation") or {}
    echo = raw.get("echo") or {}
    tk = raw.get("tuning_key") or {}
    name = freq.get("name") or "Peace"
    ctx = raw.get("context_block") or raw.get("context") or ""
    return {
        "drop_date": raw.get("drop_date"),
        "sequence": raw.get("sequence"),
        "frequency_name": name,
        "frequency_number": freq.get("number"),
        "signal_type": raw.get("signal_type") or freq.get("signal"),
        "tuning_key_text": tk.get("text") or raw.get("tuning_key_text"),
        "tuning_key_attribution": tk.get("attribution") or raw.get("tuning_key_attribution"),
        "tuning_key_source_song": tk.get("source_song") or raw.get("tuning_key_source_song") or "",
        "context_block": ctx,
        "echo_id": echo.get("id") or raw.get("echo_id"),
        "echo_audio_url": echo.get("audio_url") or raw.get("echo_audio_url"),
        "love_equation": le,
        "love_equation_value": None,
        "as_context": ctx,
        "verified": False,
    }


def write_today(d: dict) -> None:
    path = VAULT / "drop" / "today.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "date": d.get("drop_date"),
        "frequency": d.get("frequency_name"),
        "frequency_number": d.get("frequency_number"),
        "signal_type": d.get("signal_type"),
        "principle": d.get("tuning_key_source_song") or d.get("principle") or "",
        "tuning_key": d.get("tuning_key_text"),
        "attribution": d.get("tuning_key_attribution"),
        "drop_id": d.get("sequence"),
        "echo_id": d.get("echo_id"),
        "echo_audio_url": d.get("echo_audio_url"),
        "verified": d.get("verified"),
        "note": None,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("wrote", path, "frequency=", payload["frequency"], "principle=", payload["principle"])


def _next_echo_num(slug: str, drop_date: str | None) -> int:
    """Per-agent sequential Echo # (Cove-style). Stub path mirrors full runner."""
    reset = os.environ.get("LTP_RESET_ECHOES", "").strip().lower() in ("1", "true", "yes")
    path = VAULT / "team" / slug / "echoes.json"
    echoes: list = []
    if not reset and path.is_file():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                echoes = raw
        except (json.JSONDecodeError, OSError):
            echoes = []
    if drop_date:
        for e in echoes:
            if isinstance(e, dict) and e.get("when") == drop_date and e.get("echo_num") is not None:
                try:
                    return int(e["echo_num"])
                except (TypeError, ValueError):
                    break
    nums = []
    for e in echoes:
        if isinstance(e, dict) and e.get("echo_num") is not None:
            try:
                nums.append(int(e["echo_num"]))
            except (TypeError, ValueError):
                pass
    return max(nums) + 1 if nums else 1


def tune_agent(slug: str, name: str, title: str, d: dict, echo_num: int) -> None:
    folder = VAULT / "team" / slug
    folder.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    freq = d.get("frequency_name") or "Peace"
    principle = d.get("tuning_key_source_song") or d.get("principle") or ""
    le_val = d.get("love_equation_value")
    if le_val is None and d.get("love_equation"):
        le = d["love_equation"]
        try:
            le_val = round(float(le["beta"]) * (float(le["C"]) - float(le["D"])) * float(le["E"]), 4)
        except (KeyError, TypeError, ValueError):
            le_val = None

    summary = (
        f"{name} ({title}) tuned to {freq} / {principle} from Drop {d.get('drop_date')} "
        f"#{d.get('sequence')} — Echo #{echo_num}. Key: “{d.get('tuning_key_text') or '—'}”"
    )

    record = f"""# Process record — {name}
**Date:** {d.get('drop_date')}  
**Drop:** #{d.get('sequence')}  
**Frequency:** {freq} ({d.get('frequency_number')}/13)  
**Signal:** {d.get('signal_type')}  
**Principle:** {principle}  
**Role:** {title}  
**Echo #:** {echo_num}  
**L(E):** {le_val}  
**Tuned at:** {now}

## Tuning key
> {d.get('tuning_key_text') or '—'}  
> — {d.get('tuning_key_attribution') or ''}

## Context
{d.get('context_block') or d.get('as_context') or '—'}

## Steward note
Morning team tune for Lucid Cove on Hermes. Full archetype dispatch can deepen this record later.
"""
    (folder / "process_record.md").write_text(record, encoding="utf-8")

    latest = {
        "agent": name,
        "title": title,
        "tuned_at": now,
        "frequency": freq,
        "echo_num": echo_num,
        "principle": principle,
        "love_equation_value": le_val,
        "summary": summary,
        "process_record_path": f"team/{slug}/process_record.md",
        "status": "tuned",
        "drop_date": d.get("drop_date"),
        "drop_sequence": d.get("sequence"),
    }
    (folder / "latest.json").write_text(json.dumps(latest, indent=2) + "\n", encoding="utf-8")

    echoes_path = folder / "echoes.json"
    reset = os.environ.get("LTP_RESET_ECHOES", "").strip().lower() in ("1", "true", "yes")
    echoes = []
    if not reset and echoes_path.is_file():
        try:
            echoes = json.loads(echoes_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            echoes = []
    if not isinstance(echoes, list):
        echoes = []
    drop_date = d.get("drop_date") or now[:10]
    echoes = [e for e in echoes if not (isinstance(e, dict) and e.get("when") == drop_date)]
    echoes.insert(0, {
        "echo_num": echo_num,
        "frequency": freq,
        "principle": principle,
        "love_equation_value": le_val,
        "when": drop_date,
        "tuned_at": now,
    })
    echoes_path.write_text(json.dumps(echoes[:60], indent=2) + "\n", encoding="utf-8")
    print(f"  tuned {name} echo#{echo_num} principle={principle}")


def main() -> int:
    VAULT.mkdir(parents=True, exist_ok=True)
    verified = fetch_drop_verified()
    raw = fetch_drop_raw() if verified is None else {}
    d = normalize(raw, verified)
    if not d.get("frequency_name"):
        print("ERROR: no frequency in drop", file=sys.stderr)
        return 1
    write_today(d)
    for slug, name, title in AGENTS:
        echo_num = _next_echo_num(slug, d.get("drop_date"))
        tune_agent(slug, name, title, d, echo_num)
    print("morning tune complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
