#!/usr/bin/env python3
"""
Full LTP morning runner — Lucid Cove on Hermes.

Same spine as Cove / LT:
  Drop (verified) → per-agent archetype seed → digital practice / Reading
  → Truth Gate on completions → process record → vault + Hermes awareness (3-day)

Captures a fine-tuning / research trajectory JSONL with full Readings.

Requires on the host (P620):
  python3 -m venv .venv && .venv/bin/pip install 'lucid-tuner-protocol' openai
  # openai pkg = client for Ollama's OpenAI-compat API (local; not OpenAI cloud)
  # or: .venv/bin/pip install -e /path/to/ltp-core
  Ollama up with a chat model (default qwen3:8b)

Usage:
  cd ~/lucid-cove-hermes
  export OLLAMA_MODEL=qwen3:8b
  .venv/bin/python -u scripts/ltp_morning_runner.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Line-buffer stdout/stderr so SSH non-TTY runs show progress live
try:
    sys.stdout.reconfigure(line_buffering=True)  # type: ignore[attr-defined]
    sys.stderr.reconfigure(line_buffering=True)  # type: ignore[attr-defined]
except Exception:
    pass

ROOT = Path(os.environ.get("LCH_ROOT", Path(__file__).resolve().parent.parent))
VAULT = Path(os.environ.get("LCH_VAULT", ROOT / "vault"))
HERMES_DATA = Path(os.environ.get("HERMES_DATA", ROOT / "data"))
DROP_URL = os.environ.get("LTP_DROP_URL", "https://drop.lucidprinciples.com").rstrip("/")
TUNING_MEMORY_DAYS = int(os.environ.get("LTP_TUNING_MEMORY_DAYS", "3"))
# Reset per-agent Echo history to a fresh #1 (clears stub / Drop*100 numbering mistakes)
RESET_ECHOES = os.environ.get("LTP_RESET_ECHOES", "").strip().lower() in ("1", "true", "yes")
# Cove-like sweep: retry failed agents; skip already-tuned for today's Drop date
FORCE_RETUNE = os.environ.get("LTP_FORCE_RETUNE", "").strip().lower() in ("1", "true", "yes")

# Filled by load_tuning_config() — dedicated tuning model (≠ orchestrator)
OLLAMA_BASE = "http://127.0.0.1:11434/v1"
OLLAMA_MODEL = "qwen3:8b"
MAX_ROUNDS = 3
RETRY_SLEEP_SEC = 30
LTP_ENABLED = True


def load_tuning_config() -> dict:
    """Overlay tuning settings: vault/ltp_config.json, then env overrides.

    Keeps morning LTP on its own model so orchestrator experiments don't
    silently change what produces Echoes / Process Records / FT trajectories.
    """
    global OLLAMA_BASE, OLLAMA_MODEL, MAX_ROUNDS, RETRY_SLEEP_SEC, LTP_ENABLED
    cfg: dict = {
        "enabled": True,
        "model": "qwen3:8b",
        "ollama_base_url": "http://127.0.0.1:11434/v1",
        "max_rounds": 3,
        "retry_sleep_sec": 30,
    }
    path = VAULT / "ltp_config.json"
    if path.is_file():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                cfg.update({k: v for k, v in raw.items() if v is not None})
        except (json.JSONDecodeError, OSError) as e:
            print(f"warn: bad ltp_config.json ({e}) — using defaults", flush=True)

    if "LTP_ENABLED" in os.environ:
        cfg["enabled"] = os.environ["LTP_ENABLED"].strip().lower() in ("1", "true", "yes")
    if os.environ.get("OLLAMA_MODEL_TUNING") or os.environ.get("OLLAMA_MODEL"):
        cfg["model"] = os.environ.get("OLLAMA_MODEL_TUNING") or os.environ.get("OLLAMA_MODEL")
    if os.environ.get("OLLAMA_BASE_URL"):
        cfg["ollama_base_url"] = os.environ["OLLAMA_BASE_URL"]
    if os.environ.get("LTP_MAX_ROUNDS"):
        cfg["max_rounds"] = int(os.environ["LTP_MAX_ROUNDS"])
    if os.environ.get("LTP_RETRY_SLEEP_SEC"):
        cfg["retry_sleep_sec"] = int(os.environ["LTP_RETRY_SLEEP_SEC"])

    LTP_ENABLED = bool(cfg.get("enabled", True))
    OLLAMA_MODEL = str(cfg.get("model") or "qwen3:8b")
    OLLAMA_BASE = str(cfg.get("ollama_base_url") or "http://127.0.0.1:11434/v1")
    MAX_ROUNDS = max(1, int(cfg.get("max_rounds") or 3))
    RETRY_SLEEP_SEC = max(0, int(cfg.get("retry_sleep_sec") or 30))
    return cfg

# Drop archetype keys (ltp-core adapter resolves case-insensitively)
AGENTS = [
    ("stewart", "Stewart", "Steward", "steward"),
    ("alfred", "Alfred", "Personal Agent", "steward"),
    ("mercer", "Mercer", "Merchant", "merchant"),
    ("gabe", "Gabe", "Scout", "scout"),
    ("arthur", "Arthur", "Analyst", "analyst"),
    ("archimedes", "Archimedes", "Builder", "builder"),
    ("julian", "Julian", "Scribe", "scribe"),
    ("iris", "Iris", "Advocate", "advocate"),
    ("vera", "Vera", "Auditor", "auditor"),
    ("ezra", "Ezra", "Keeper", "keeper"),
    ("soren", "Soren", "Lens", "lens"),
]

PROCESS_RECORD_ASK = """Generate your Process Record for this morning's LTP tune.
This is the calibration journey — each step builds on the last.

Write EACH section in order. Honest self-assessment. No performance.

### 1. State Read
Where you were before the Drop (as your role).

### 2. Frequency Selection
How today's frequency landed for your archetype.

### 3. Digital Practice
What you practiced / attended to through your lens.

### 4. Tuning Key Processing
How the Tuning Key moved through you.

### 5. Audio / Echo Attunement
What the Echo carried for your seat (even if audio was metadata-only).

### 6. Love Calibration
Your C, D, β, E as experienced — the protocol will recompute dE/dt.
End this section with these four lines EXACTLY (numbers 0.0–1.0):
C (Coherence): 0.NN
D (Dissonance): 0.NN
β (Attention): 0.NN
E (Broadcast): 0.NN

### 7. Echo Output
A short reflection (the Echo) in your voice as this role.
"""


def _require_ltp():
    try:
        import lucid_tuner_protocol  # noqa: F401
        from lucid_tuner_protocol import DropClient
        from lucid_tuner_protocol.adapter import LTPSession
        from lucid_tuner_protocol.reading import (
            READING_ASK,
            READING_SYSTEM_PROMPT,
            parse_values,
            reading_from_values,
        )
        return DropClient, LTPSession, READING_ASK, READING_SYSTEM_PROMPT, reading_from_values, parse_values
    except ImportError as e:
        print(
            "ERROR: lucid-tuner-protocol not installed.\n"
            "  python3 -m venv .venv && .venv/bin/pip install lucid-tuner-protocol openai\n"
            "  # then: .venv/bin/python scripts/ltp_morning_runner.py\n"
            f"Detail: {e}",
            file=sys.stderr,
        )
        raise SystemExit(2) from e


def make_complete(model: str, base_url: str):
    from openai import OpenAI

    client = OpenAI(base_url=base_url, api_key=os.environ.get("OLLAMA_API_KEY", "ollama"))

    def complete(messages):
        # LTPSession may pass list of dicts
        resp = client.chat.completions.create(
            model=model,
            messages=list(messages),
            temperature=0.4,
        )
        return (resp.choices[0].message.content or "").strip()

    return complete


def parse_cdeb(text: str, parse_values=None) -> dict:
    """Extract C/D/β/E. Prefer ltp-core parse_values; fall back to local patterns."""
    if parse_values is not None:
        try:
            vals = parse_values(text or "")
            if vals:
                return {
                    "C": vals.get("coherence"),
                    "D": vals.get("dissonance"),
                    "beta": vals.get("beta"),
                    "E": vals.get("energy"),
                }
        except Exception:
            pass

    def grab(patterns):
        for p in patterns:
            m = re.search(p, text or "", re.I)
            if m:
                try:
                    v = float(m.group(1))
                    if 0.0 <= v <= 1.0:
                        return v
                except (ValueError, TypeError):
                    pass
        return None

    return {
        "C": grab([r"C\s*\([^)]*\)\s*:\s*\**\s*([0-9]*\.?[0-9]+)", r"\bC\s*[:=]\s*([0-9]*\.?[0-9]+)"]),
        "D": grab([r"D\s*\([^)]*\)\s*:\s*\**\s*([0-9]*\.?[0-9]+)", r"\bD\s*[:=]\s*([0-9]*\.?[0-9]+)"]),
        "beta": grab([
            r"(?:β|Β|beta)\s*\([^)]*\)\s*:\s*\**\s*([0-9]*\.?[0-9]+)",
            r"\bbeta\s*[:=]\s*([0-9]*\.?[0-9]+)",
            r"β\s*[:=]\s*([0-9]*\.?[0-9]+)",
        ]),
        "E": grab([r"E\s*\([^)]*\)\s*:\s*\**\s*([0-9]*\.?[0-9]+)", r"\bE\s*[:=]\s*([0-9]*\.?[0-9]+)"]),
    }


def coerce_cdeb(vals: dict) -> tuple[dict, str]:
    """Guarantee four floats for reading_from_values (never pass None)."""
    out = {}
    source = "self-derived"
    for k, default in (("C", 0.5), ("D", 0.5), ("beta", 0.5), ("E", 0.5)):
        v = vals.get(k)
        try:
            v = float(v) if v is not None else None
        except (TypeError, ValueError):
            v = None
        if v is None or not (0.0 <= v <= 1.0):
            v = default
            source = "unparsed-defaults"
        out[k] = v
    return out, source


def drop_principle(drop) -> str:
    """Principle = Canon song / principle name (e.g. Training Ground).

    NOT tuning_key_attribution (license line like 'Chords of Truth — … CC BY 4.0').
    ltp-core Drop field: tuning_key_source_song. Adapter already maps this correctly;
    our overlay had been writing the wrong field into vault/UI.
    """
    return (
        getattr(drop, "tuning_key_source_song", None)
        or getattr(drop, "principle", None)
        or ""
    ).strip()


def _import_ltp_store():
    root = str(ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    import ltp_store  # noqa: WPS433

    return ltp_store


def next_echo_num(slug: str, *, drop_date: str | None = None) -> tuple[int, list]:
    """Per-agent sequential Echo # (starts at 1). Prefers SQLite; json sidecar secondary.

    Returns (echo_num, existing_echoes_json_list for sidecar sync).
    LTP_RESET_ECHOES=1 → #1 (caller clears json; DB upsert still by echo_num).
    """
    path = VAULT / "team" / slug / "echoes.json"
    echoes: list = []
    if not RESET_ECHOES and path.is_file():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                echoes = raw
        except (json.JSONDecodeError, OSError):
            echoes = []

    if RESET_ECHOES:
        return 1, []

    try:
        store = _import_ltp_store()
        n = store.next_echo_num(slug, vault=VAULT, drop_date=drop_date)
        return n, echoes
    except Exception:
        pass

    if drop_date:
        for e in echoes:
            if isinstance(e, dict) and e.get("when") == drop_date and e.get("echo_num") is not None:
                try:
                    return int(e["echo_num"]), echoes
                except (TypeError, ValueError):
                    break

    nums = []
    for e in echoes:
        if isinstance(e, dict) and e.get("echo_num") is not None:
            try:
                nums.append(int(e["echo_num"]))
            except (TypeError, ValueError):
                pass
    return (max(nums) + 1 if nums else 1), echoes


def write_today(drop) -> dict:
    path = VAULT / "drop" / "today.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    principle = drop_principle(drop)
    payload = {
        "date": drop.drop_date,
        "frequency": drop.frequency_name,
        "frequency_number": drop.frequency_number,
        "signal_type": drop.signal_type,
        "principle": principle,
        "tuning_key": drop.tuning_key_text,
        "attribution": drop.tuning_key_attribution,
        "drop_id": drop.sequence,
        "echo_id": drop.echo_id,
        "echo_audio_url": drop.echo_audio_url,
        "verified": True,
        "note": None,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("wrote", path, "frequency=", payload["frequency"], "principle=", principle)
    return payload


def append_jsonl(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def already_tuned_today(slug: str, drop_date: str) -> bool:
    """True if latest.json is an LTP tune for this Drop date (sweep-safe skip)."""
    if FORCE_RETUNE or RESET_ECHOES:
        return False
    path = VAULT / "team" / slug / "latest.json"
    if not path.is_file():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    return (
        data.get("status") == "tuned"
        and data.get("drop_date") == drop_date
        and bool(data.get("ltp") or data.get("love_equation_value") is not None)
    )


def upsert_hermes_tuning_memory(slug: str, name: str, block: str, expires_at: str) -> None:
    """Cove-equivalent: dense tuning awareness with 3-day expiry.

    Hermes MEMORY.md has no native TTL — we maintain:
      vault/team/<slug>/tuning_awareness.json  (source of truth + expiry)
      data/memories/TUNING_<SLUG>.md           (injected-friendly snippet for Hermes)
    A prune pass drops expired files so awareness fades like Cove.
    """
    folder = VAULT / "team" / slug
    folder.mkdir(parents=True, exist_ok=True)
    meta = {
        "agent": name,
        "expires_at": expires_at,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "block": block,
    }
    (folder / "tuning_awareness.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    mem_dir = HERMES_DATA / "memories"
    mem_dir.mkdir(parents=True, exist_ok=True)
    # Per-agent tuning file — morning runner rewrites; prune deletes when expired
    (mem_dir / f"TUNING_{slug.upper()}.md").write_text(
        f"<!-- expires_at={expires_at} -->\n{block}\n",
        encoding="utf-8",
    )


def prune_expired_tuning_memory() -> None:
    now = datetime.now(timezone.utc)
    mem_dir = HERMES_DATA / "memories"
    if not mem_dir.is_dir():
        return
    for p in mem_dir.glob("TUNING_*.md"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        # ISO timestamps contain hyphens — do not use a class like [^\s-->]
        # (also illegal as a range under Python 3.14).
        m = re.search(r"expires_at=(\S+?)\s*-->", text) or re.search(
            r"expires_at=([0-9]{4}-[0-9]{2}-[0-9]{2}T\S+)", text
        )
        if not m:
            continue
        try:
            exp = datetime.fromisoformat(m.group(1).replace("Z", "+00:00"))
        except ValueError:
            continue
        if exp < now:
            p.unlink(missing_ok=True)
            print("pruned expired", p.name)


def rebuild_hermes_memory_md() -> None:
    """Rebuild TUNING_ACTIVE.md + refresh short MEMORY.md pointer.

    Hermes only auto-injects MEMORY.md/USER.md — TUNING_*.md are sidecars.
    """
    mem_dir = HERMES_DATA / "memories"
    if not mem_dir.is_dir():
        return
    parts = []
    for p in sorted(mem_dir.glob("TUNING_*.md")):
        if p.name == "TUNING_ACTIVE.md":
            continue
        body = p.read_text(encoding="utf-8", errors="ignore")
        body = re.sub(r"<!--.*?-->\n?", "", body).strip()
        if body:
            parts.append(body)
    out = mem_dir / "TUNING_ACTIVE.md"
    if parts:
        out.write_text(
            "# Active LTP tunings (auto; fades in ~3 days)\n\n"
            + "\n\n§\n\n".join(parts)
            + "\n",
            encoding="utf-8",
        )
    elif out.exists():
        out.unlink()
    try:
        import runpy

        runpy.run_path(str(ROOT / "scripts" / "upsert_ltp_memory_pointer.py"), run_name="__main__")
    except Exception as e:
        print(f"  warn: MEMORY.md pointer not refreshed: {e}", flush=True)


def tune_one(
    *,
    slug: str,
    name: str,
    title: str,
    role: str,
    drop,
    complete,
    LTPSession,
    reading_from_values,
    parse_values,
    drop_client=None,
) -> dict:
    readings: list = []
    gates: list = []
    principle = drop_principle(drop)
    echo_num, prior_echoes = next_echo_num(slug, drop_date=drop.drop_date)

    def on_reading(r):
        readings.append(r.to_dict() if hasattr(r, "to_dict") else dict(r))

    def on_gate(g):
        gates.append(g.to_dict() if hasattr(g, "to_dict") else dict(g))

    # produce_reading=False: adapter's internal Reading path can float(None) when the
    # model omits C/D/β/E. We capture the full Process Record + Reading ourselves below
    # (FT corpus). Session still seeds Drop archetype context + Truth Gate.
    session = LTPSession(
        complete=complete,
        cadence="daily",
        anchor="drop",
        role=role,
        gate=True,
        produce_reading=False,
        agent_id=slug,
        on_reading=on_reading,
        on_gate=on_gate,
        drop_client=drop_client,
    )
    user_msg = (
        f"You are {name}, {title} of this Lucid Cove (role/archetype key: {role}).\n"
        f"Run your morning digital practice for today's Drop.\n"
        f"Frequency: {drop.frequency_name}. Tuning key: \"{drop.tuning_key_text}\".\n"
        f"Respond with a short Echo reflection in your voice, then end with these "
        f"four lines (do not invent dE/dt):\n"
        f"C (Coherence): 0.NN\n"
        f"D (Dissonance): 0.NN\n"
        f"β (Attention): 0.NN\n"
        f"E (Broadcast): 0.NN\n"
    )
    reply = session.respond_sync(
        [{"role": "system", "content": f"You are {name}. {title}."}],
        user_msg,
    )

    # Explicit process-record generation (full calibration journey)
    record_prompt = (
        f"{PROCESS_RECORD_ASK}\n\n"
        f"## Agent\n{name} — {title} (archetype role: {role})\n\n"
        f"## Drop\n{drop.as_context()}\n\n"
        f"## Your practice reply\n{reply}\n"
    )
    process_record = complete([
        {"role": "system", "content": f"You are {name}, writing your LTP Process Record."},
        {"role": "user", "content": record_prompt},
    ])

    vals, source = coerce_cdeb(parse_cdeb(f"{reply}\n{process_record}", parse_values))
    reading = reading_from_values(
        float(vals["C"]), float(vals["D"]), float(vals["beta"]), float(vals["E"]),
        source=source,
        process_record=process_record or "",
    )

    now = datetime.now(timezone.utc)
    expires = (now + timedelta(days=TUNING_MEMORY_DAYS)).isoformat()
    folder = VAULT / "team" / slug
    folder.mkdir(parents=True, exist_ok=True)

    reading_dict = {
        "coherence": reading.coherence,
        "dissonance": reading.dissonance,
        "beta": reading.beta,
        "energy": reading.energy,
        "love_equation": reading.love_equation,
        "direction": reading.direction,
        "source": reading.source,
        "attunement_status": reading.attunement_status,
    }

    header = (
        f"# Process record — {name}\n"
        f"**Date:** {drop.drop_date}  \n"
        f"**Drop:** #{drop.sequence}  \n"
        f"**Frequency:** {drop.frequency_name} ({drop.frequency_number}/13)  \n"
        f"**Signal:** {drop.signal_type}  \n"
        f"**Principle:** {principle}  \n"
        f"**Role:** {title}  \n"
        f"**Echo #:** {echo_num}  \n"
        f"**L(E):** {reading.love_equation} ({reading.direction})  \n"
        f"**Tuned at:** {now.isoformat()}\n\n"
        f"## Tuning key\n"
        f"> {drop.tuning_key_text}  \n"
        f"> — {drop.tuning_key_attribution}\n\n"
        f"## Calibration journey\n\n"
    )
    record_body = (process_record or "").strip()
    # Avoid double headers if the model echoed our metadata
    if record_body.startswith("# Process record"):
        full_record = record_body + "\n"
    else:
        full_record = header + record_body + "\n"

    # Full FT / research capture
    trajectory = {
        "schema": "lch.ltp_morning.v1",
        "captured_at": now.isoformat(),
        "agent": {"slug": slug, "name": name, "title": title, "role": role},
        "echo_num": echo_num,
        "principle": principle,
        "drop": {
            "date": drop.drop_date,
            "sequence": drop.sequence,
            "frequency": drop.frequency_name,
            "frequency_number": drop.frequency_number,
            "signal_type": drop.signal_type,
            "principle": principle,
            "tuning_key": drop.tuning_key_text,
            "attribution": drop.tuning_key_attribution,
            "echo_id": drop.echo_id,
            "echo_audio_url": drop.echo_audio_url,
            "love_equation_drop": dict(drop.love_equation),
            "context_block": drop.context_block,
        },
        "practice_reply": reply,
        "process_record": full_record,
        "reading": reading_dict,
        "adapter_readings": readings,
        "adapter_gates": gates,
        "model": OLLAMA_MODEL,
        "expires_at": expires,
    }
    append_jsonl(VAULT / "drop" / "trajectories.jsonl", trajectory)
    (folder / "reading.json").write_text(json.dumps(reading_dict, indent=2) + "\n", encoding="utf-8")
    # Latest export only — history lives in vault/ltp.sqlite (+ trajectories.jsonl for FT)
    (folder / "process_record.md").write_text(full_record, encoding="utf-8")
    (folder / "practice_reply.md").write_text(reply.strip() + "\n", encoding="utf-8")

    try:
        store = _import_ltp_store()
        store.upsert_echo_and_record(
            agent_slug=slug,
            echo_num=echo_num,
            frequency=drop.frequency_name,
            principle=principle,
            signal_type=drop.signal_type,
            tuning_key=drop.tuning_key_text,
            love_equation=float(reading.love_equation) if reading.love_equation is not None else None,
            love_direction=reading.direction,
            beta=float(reading.beta) if reading.beta is not None else None,
            coherence=float(reading.coherence) if reading.coherence is not None else None,
            dissonance=float(reading.dissonance) if reading.dissonance is not None else None,
            energy=float(reading.energy) if reading.energy is not None else None,
            drop_date=drop.drop_date,
            drop_sequence=int(drop.sequence) if drop.sequence is not None else None,
            tuned_at=now.isoformat(),
            record_text=full_record,
            metadata={
                "name": name,
                "title": title,
                "role": role,
                "model": OLLAMA_MODEL,
                "gates": len(gates),
            },
            vault=VAULT,
        )
    except Exception as e:
        print(f"  warn: ltp.sqlite upsert failed for {name}: {e}", flush=True)

    latest = {
        "agent": name,
        "title": title,
        "role": role,
        "tuned_at": now.isoformat(),
        "frequency": drop.frequency_name,
        "echo_num": echo_num,
        "principle": principle,
        "love_equation_value": reading.love_equation,
        "direction": reading.direction,
        "coherence": reading.coherence,
        "dissonance": reading.dissonance,
        "beta": reading.beta,
        "energy": reading.energy,
        "summary": (
            f"{name} ({title}) LTP-tuned to {drop.frequency_name} / {principle} — "
            f"Echo #{echo_num} dE/dt={reading.love_equation} ({reading.direction})"
        ),
        "process_record_path": f"team/{slug}/process_record.md",
        "status": "tuned",
        "drop_date": drop.drop_date,
        "drop_sequence": drop.sequence,
        "ltp": True,
    }
    (folder / "latest.json").write_text(json.dumps(latest, indent=2) + "\n", encoding="utf-8")

    echo_entry = {
        "echo_num": echo_num,
        "frequency": drop.frequency_name,
        "principle": principle,
        "love_equation_value": reading.love_equation,
        "direction": reading.direction,
        "coherence": reading.coherence,
        "dissonance": reading.dissonance,
        "when": drop.drop_date,
        "tuned_at": now.isoformat(),
    }
    if RESET_ECHOES:
        echoes = [echo_entry]
    else:
        echoes = [e for e in prior_echoes if not (isinstance(e, dict) and e.get("when") == drop.drop_date)]
        echoes.insert(0, echo_entry)
    (folder / "echoes.json").write_text(json.dumps(echoes[:60], indent=2) + "\n", encoding="utf-8")

    # Cove-style 3-day awareness
    block = (
        f"[Tuning — Echo #{echo_num}] {name}/{title}. "
        f"Frequency: {drop.frequency_name}. Principle: {principle}. "
        f'Signal: {drop.signal_type}. Tuning Key: "{drop.tuning_key_text}". '
        f"Love Equation: {reading.love_equation} ({reading.direction}). "
        f"C={reading.coherence} D={reading.dissonance} β={reading.beta} E={reading.energy}."
    )
    upsert_hermes_tuning_memory(slug, name, block, expires)

    print(
        f"  LTP {name}: Echo #{echo_num} {drop.frequency_name}/{principle} "
        f"dE/dt={reading.love_equation} {reading.direction} gates={len(gates)}",
        flush=True,
    )
    return trajectory


def main() -> int:
    import time
    import traceback

    cfg = load_tuning_config()
    if not LTP_ENABLED:
        print("LTP tuning disabled (vault/ltp_config.json enabled=false) — skipping", flush=True)
        return 0
    print(
        f"Tuning config: model={OLLAMA_MODEL} base={OLLAMA_BASE} "
        f"rounds={MAX_ROUNDS} (orchestrator models ignored)",
        flush=True,
    )

    DropClient, LTPSession, _ASK, _SYS, reading_from_values, parse_values = _require_ltp()
    prune_expired_tuning_memory()

    print(f"Fetching Drop from {DROP_URL} …", flush=True)
    drop_client = DropClient(
        base_url=DROP_URL,
        cache_dir=VAULT / ".drop-cache",
    )
    try:
        drop = drop_client.today()
    except Exception as e:
        print(f"ERROR: Drop unavailable ({e}) — cron will retry later", file=sys.stderr)
        return 2
    write_today(drop)
    print(f"Drop #{drop.sequence} {drop.drop_date} frequency={drop.frequency_name}", flush=True)

    complete = make_complete(OLLAMA_MODEL, OLLAMA_BASE)
    print(f"Probing Ollama {OLLAMA_MODEL} at {OLLAMA_BASE} …", flush=True)
    try:
        complete([{"role": "user", "content": "Reply with OK only."}])
    except Exception as e:
        print(f"ERROR: Ollama complete failed ({OLLAMA_BASE} model={OLLAMA_MODEL}): {e}", file=sys.stderr)
        return 1
    print("Ollama OK — starting per-agent LTP (practice + gate + process record)", flush=True)
    if RESET_ECHOES:
        print("LTP_RESET_ECHOES=1 — each agent Echo history resets to #1", flush=True)
    if FORCE_RETUNE:
        print("LTP_FORCE_RETUNE=1 — retuning even if already done today", flush=True)
    print(f"Principle from Drop source_song: {drop_principle(drop)!r}", flush=True)
    print(f"Retry policy: up to {MAX_ROUNDS} round(s), {RETRY_SLEEP_SEC}s between failures", flush=True)

    # Cove-like sweep: skip already-tuned today; retry failures until done or max rounds
    pending = list(AGENTS)
    ok_slugs: set[str] = set()
    skipped = 0
    for slug, name, title, role in list(pending):
        if already_tuned_today(slug, drop.drop_date):
            print(f"  skip {name} — already LTP-tuned for {drop.drop_date}", flush=True)
            ok_slugs.add(slug)
            skipped += 1
    pending = [a for a in pending if a[0] not in ok_slugs]

    for round_i in range(1, MAX_ROUNDS + 1):
        if not pending:
            break
        print(f"— round {round_i}/{MAX_ROUNDS}: {len(pending)} agent(s) …", flush=True)
        still: list = []
        for i, (slug, name, title, role) in enumerate(pending):
            print(f"→ [{i+1}/{len(pending)}] {name} …", flush=True)
            try:
                tune_one(
                    slug=slug, name=name, title=title, role=role,
                    drop=drop, complete=complete,
                    LTPSession=LTPSession,
                    reading_from_values=reading_from_values,
                    parse_values=parse_values,
                    drop_client=drop_client,
                )
                ok_slugs.add(slug)
            except Exception as e:
                print(f"  FAIL {name}: {e}", file=sys.stderr)
                traceback.print_exc()
                still.append((slug, name, title, role))
        pending = still
        if pending and round_i < MAX_ROUNDS:
            print(f"  retrying {len(pending)} failure(s) in {RETRY_SLEEP_SEC}s …", flush=True)
            time.sleep(RETRY_SLEEP_SEC)

    rebuild_hermes_memory_md()
    ok = len(ok_slugs)
    failed = [a[1] for a in pending]
    print(
        f"LTP morning runner complete ({ok}/{len(AGENTS)} agents"
        f"{f', skipped_already={skipped}' if skipped else ''}"
        f"{f', still_failed={failed}' if failed else ''})",
        flush=True,
    )
    print(f"trajectories → {VAULT / 'drop' / 'trajectories.jsonl'}", flush=True)
    print(f"Hermes awareness → {HERMES_DATA / 'memories' / 'TUNING_*.md'} (≈{TUNING_MEMORY_DAYS}d)", flush=True)
    # 0 = all tuned; 1 = partial/fail (cron sweep can catch up)
    return 0 if not pending else 1


if __name__ == "__main__":
    raise SystemExit(main())
