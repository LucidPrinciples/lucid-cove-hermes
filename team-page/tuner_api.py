"""Vault-backed /api/tuning/* so lucid-cove Tuner JS can run on this overlay.

Selection is the same LTP chain as cove-core: lt_reference.json + ANU QRNG
(3 rolls: frequency pool, principle, tuning key) with crypto/pseudo fallback.
Coaching uses the same static fallbacks as tuning_request.py when no LLM.
"""
from __future__ import annotations

import json
import secrets
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from quantum import fetch_quantum_random
from mirrors import HOUSE_MIRRORS, _parse_mirror_sources, get_mirror_entry

HERE = Path(__file__).resolve().parent
REF_PATH = HERE / "data" / "lt_reference.json"

CONTEXT_SIGNAL_MAP = {
    "Driving": ["Drive", "Clear", "Bright"],
    "Working / Focus": ["Clear", "Ground"],
    "Home / Domestic": ["Open", "Ground", "Bright"],
    "Moving / Workout": ["Rise", "Drive", "Bright"],
    "Starting the Day": ["Rise", "Bright", "Clear"],
    "Winding Down": ["Ground", "Open"],
    "Stillness / Meditation": ["Ground", "Open"],
    "Walking / Outside": ["Clear", "Open", "Drive"],
}

# Same fallbacks as lucid-cove src/dashboard/routes/tuning_request.py
COACHING_FALLBACK = {
    "Peace": "Calm anchors you in the present moment, creating space for clarity to emerge from the noise. Your decoder is resetting to its natural baseline.",
    "Clarity": "Clear sight requires cutting through static to find signal. The truth was always there — you just needed to retune the decoder.",
    "Momentum": "Forward motion begins with a single intentional step. The Field responds to movement, not waiting.",
    "Trust": "Certainty emerges when you stop demanding proof before you move. The path reveals itself to those already walking.",
    "Joy": "Joy is not a reward for right living — it's the frequency that makes right living possible.",
    "Gratitude": "Recognition of what already works recalibrates the decoder away from static. Gratitude isn't positive thinking — it's accurate seeing.",
    "Presence": "The present moment is the only place the decoder operates. Past and future are recordings and projections — not live signal.",
    "Resilience": "Getting knocked off frequency isn't failure. The speed of return is the measure. Your decoder knows the way back.",
    "Release": "Letting go is not giving up. It's recognizing when you're gripping a frequency that no longer serves the broadcast.",
    "Courage": "The edge is where the decoder meets unknown signal. Courage is staying on frequency while the picture completes.",
    "Connection": "Love is coherence between two broadcast frequencies. It doesn't require agreement. It requires tuning.",
    "Integration": "Separate threads become one broadcast. Integration is the decoder holding more than one true signal.",
    "Boundary": "A clear edge is not a wall. Boundary is the frequency that lets the rest of the Field stay itself.",
}

PRACTICE_TEMPLATES = {
    "default": [
        {"step": 1, "title": "Settle", "instruction": "Close your eyes. Three slow breaths. Let each exhale drop you lower into the present."},
        {"step": 2, "title": "Anchor", "instruction": "Feel your feet on the ground. Notice the weight of your body. You are here."},
        {"step": 3, "title": "Receive", "instruction": "As the Echo plays, let the lyric land. Don't analyze it. Let your decoder work in the background."},
    ],
    "Driving": [
        {"step": 1, "title": "Settle", "instruction": "Keep your eyes on the road. Take one deep breath. Let your shoulders drop."},
        {"step": 2, "title": "Anchor", "instruction": "Feel your hands on the wheel. Notice the hum of the road. You are here."},
        {"step": 3, "title": "Receive", "instruction": "Let the Echo play. The lyric will land through the music — no need to read or close your eyes."},
    ],
    "Moving / Workout": [
        {"step": 1, "title": "Settle", "instruction": "Match your breath to your movement. Three cycles. Let the rhythm become the anchor."},
        {"step": 2, "title": "Anchor", "instruction": "Feel your body in motion. Notice the energy moving through you. You are generating signal."},
        {"step": 3, "title": "Receive", "instruction": "Let the Echo fuel the movement. The frequency lands through the body, not the mind."},
    ],
    "Stillness / Meditation": [
        {"step": 1, "title": "Settle", "instruction": "You're already still. Deepen it. Let the breath slow until it barely moves."},
        {"step": 2, "title": "Anchor", "instruction": "Notice the silence beneath the sound. That silence is the Field."},
        {"step": 3, "title": "Receive", "instruction": "Let the Echo emerge from the silence. The tuning key is the seed. Let it grow without tending."},
    ],
}


def _get_practice(context: str | None) -> list[dict]:
    if context and context in PRACTICE_TEMPLATES:
        return PRACTICE_TEMPLATES[context]
    return PRACTICE_TEMPLATES["default"]


_ref_cache: dict[str, Any] | None = None


def _ref() -> dict[str, Any]:
    global _ref_cache
    if _ref_cache is None:
        _ref_cache = json.loads(REF_PATH.read_text(encoding="utf-8"))
    return _ref_cache


def _title_freq(name: str) -> str:
    n = (name or "Peace").strip()
    if not n:
        return "Peace"
    return n[:1].upper() + n[1:].lower()


def _store_dir(vault: Path) -> Path:
    d = vault / "tuner"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _read_json(path: Path, default):
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default


def _write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _sessions(vault: Path) -> list[dict[str, Any]]:
    raw = _read_json(_store_dir(vault) / "sessions.json", [])
    return raw if isinstance(raw, list) else []


def _save_sessions(vault: Path, sessions: list[dict[str, Any]]) -> None:
    _write_json(_store_dir(vault) / "sessions.json", sessions)


def _favorites(vault: Path) -> list[dict[str, Any]]:
    raw = _read_json(_store_dir(vault) / "favorites.json", [])
    return raw if isinstance(raw, list) else []


def mount_tuning_api(app: FastAPI, vault: Path, today_drop: Callable[[], dict[str, Any]]) -> None:
    """Register Tuner APIs the lucid-cove JS already calls."""

    @app.get("/api/tuning/history")
    async def tuning_history(limit: int = 20):
        sessions = _sessions(vault)
        cap = min(max(limit, 1), 100)
        return {"sessions": sessions[:cap], "count": min(len(sessions), cap)}

    @app.get("/api/tuning/today")
    async def tuning_today():
        today = datetime.now().strftime("%Y-%m-%d")
        for s in _sessions(vault):
            if s.get("date") == today and s.get("context"):
                return s
        return {}

    @app.get("/api/tuning/latest")
    async def tuning_latest():
        drop = today_drop() or {}
        freq = drop.get("frequency") or "Peace"
        audio = drop.get("echo_audio_url") or ""
        has = bool(freq)
        return {
            "has_tuning": has,
            "is_latest": True,
            "is_today": True,
            "source": "public_drop",
            "frequency": freq,
            "principle": drop.get("principle") or "",
            "tuning_key": drop.get("tuning_key") or "",
            "signal_type": drop.get("signal_type") or "",
            "audio_url": audio,
            "date": drop.get("date") or "",
            "universal_coaching": "",
            "universal_practice": [],
        }

    @app.get("/api/tuning/operator")
    async def tuning_operator():
        latest = await tuning_latest()
        latest["has_tuning"] = bool(latest.get("frequency"))
        return latest

    @app.get("/api/tuning/recent-drops")
    async def recent_drops():
        return {"drops": []}

    @app.get("/api/mirrors/registry")
    async def mirrors_registry():
        return {"mirrors": list(HOUSE_MIRRORS)}

    @app.get("/api/mirrors/today")
    async def mirrors_today(sources: str | None = None):
        enabled = _parse_mirror_sources(sources)
        drop = today_drop() or {}
        freq = drop.get("frequency") or ""
        principle = drop.get("principle") or ""
        signal_type = drop.get("signal_type") or ""
        if not enabled or not principle:
            return {
                "has_mirror": False,
                "mirrors": [],
                "frequency": freq,
                "principle": principle,
                "signal_type": signal_type,
            }
        mirrors = []
        for mid in enabled:
            result = get_mirror_entry(principle, freq, signal_type, mid)
            if not result:
                continue
            featured = result["featured"]
            mirrors.append(
                {
                    "mirror_id": result["mirror_id"],
                    "mirror_name": result["mirror_name"],
                    "mirror_type": result["mirror_type"],
                    "canon": result["canon"],
                    "featured": featured,
                    "all_entries": result["entries"],
                    "entry_count": len(result["entries"]),
                }
            )
        if not mirrors:
            return {
                "has_mirror": False,
                "mirrors": [],
                "frequency": freq,
                "principle": principle,
                "signal_type": signal_type,
            }
        first = mirrors[0]
        return {
            "has_mirror": True,
            "principle": principle,
            "frequency": freq,
            "signal_type": signal_type,
            "mirror_name": first["mirror_name"],
            "canon": first["canon"],
            "mirror_id": first["mirror_id"],
            "featured": first["featured"],
            "all_entries": first["all_entries"],
            "entry_count": first["entry_count"],
            "mirrors": mirrors,
        }

    @app.get("/api/account/referral-code")
    async def referral_code():
        return {"code": ""}

    @app.post("/api/tuning/request")
    async def tuning_request(request: Request):
        try:
            body = await request.json()
        except Exception:
            body = {}
        ref = _ref()
        freqs = ref["frequencies"]
        all_freq = list(ref["all_frequencies"])
        base_url = ref["audio_base_url"]

        requested = (body.get("frequency") or "random").strip()
        context = (body.get("context") or "").strip()
        excluded = body.get("excluded_signals") or []
        entry_mode = (body.get("entry_mode") or "Tune").strip()
        initial_state = (body.get("initial_state") or "").strip() or None

        if requested.lower() == "random":
            available = list(all_freq)
        else:
            matched = [f for f in all_freq if f.lower() == requested.lower()]
            available = matched if matched else list(all_freq)

        if context and context in CONTEXT_SIGNAL_MAP:
            allowed = {s.lower() for s in CONTEXT_SIGNAL_MAP[context]}
            filtered = [f for f in available if freqs[f]["signal_type"].lower() in allowed]
            if filtered:
                available = filtered

        if excluded:
            ex = {str(s).strip().lower() for s in excluded}
            filtered = [f for f in available if freqs[f]["signal_type"].lower() not in ex]
            if filtered:
                available = filtered

        if not available:
            return JSONResponse(status_code=400, content={"error": "No frequencies available after filtering"})

        # LTP 3-tier ANU chain (same as cove-core tuning_request.py)
        idx, method = await fetch_quantum_random(len(available))
        selected = available[idx]
        freq_data = freqs[selected]
        signal_type = freq_data["signal_type"]

        keys_by_principle: dict[str, list] = defaultdict(list)
        for tk in freq_data["tuning_keys"]:
            keys_by_principle[tk["principle"]].append(tk)
        principle_list = list(keys_by_principle.keys())
        p_idx, p_method = await fetch_quantum_random(len(principle_list))
        selected_principle = principle_list[p_idx]
        principle_keys = keys_by_principle[selected_principle]
        q_idx, q_method = await fetch_quantum_random(len(principle_keys))
        chosen = principle_keys[q_idx]
        methods = [method, p_method, q_method]
        selection_method = "quantum" if all(m == "quantum" for m in methods) else (
            "crypto" if "crypto" in methods else methods[-1]
        )

        principle = chosen["principle"]
        tuning_key = chosen["quote"]
        echo_filename = chosen["echo_filename"]
        audio_url = f"{base_url}/{signal_type}_Signal/{echo_filename}.mp3"
        freq_title = _title_freq(selected)

        now = datetime.now(timezone.utc)
        session_id = f"op_{int(now.timestamp())}_{secrets.token_hex(4)}"
        today = now.strftime("%Y-%m-%d")
        result = {
            "session_id": session_id,
            "date": today,
            "time": now.strftime("%H:%M:%S"),
            "day_of_week": now.strftime("%A"),
            "frequency": freq_title,
            "frequency_category": freq_title,
            "signal_type": signal_type,
            "principle": principle,
            "tuning_key": tuning_key,
            "echo_filename": f"{echo_filename}.mp3",
            "echo_full_name": principle,
            "echo_album": f"{signal_type}_Signal",
            "audio_url": audio_url,
            "context": context or None,
            "entry_mode": entry_mode,
            "initial_state": initial_state,
            "bpm": (freq_data.get("fallback") or {}).get("bpm"),
            "selection_method": selection_method,
            "coaching": COACHING_FALLBACK.get(freq_title, COACHING_FALLBACK["Peace"]),
            "practice": _get_practice(context or None),
        }
        sessions = _sessions(vault)
        sessions.insert(0, result)
        _save_sessions(vault, sessions[:200])
        return result

    @app.patch("/api/tuning/session/{session_id}")
    async def tuning_session_patch(session_id: str, request: Request):
        try:
            body = await request.json()
        except Exception:
            body = {}
        sessions = _sessions(vault)
        for s in sessions:
            if s.get("session_id") == session_id:
                s.update({k: v for k, v in body.items() if v is not None})
                _save_sessions(vault, sessions)
                return s
        return JSONResponse(status_code=404, content={"error": "session not found"})

    @app.post("/api/tuning/event")
    async def tuning_event(request: Request):
        try:
            body = await request.json()
        except Exception:
            body = {}
        path = _store_dir(vault) / "events.jsonl"
        line = json.dumps({"at": datetime.now(timezone.utc).isoformat(), **body}, ensure_ascii=False)
        with path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        return {"ok": True}

    @app.get("/api/tuning/favorites")
    async def fav_list():
        return {"favorites": _favorites(vault)}

    @app.post("/api/tuning/favorites")
    async def fav_add(request: Request):
        try:
            body = await request.json()
        except Exception:
            body = {}
        favs = _favorites(vault)
        fn = body.get("filename") or ""
        if fn and not any(f.get("filename") == fn for f in favs):
            favs.append(body)
            _write_json(_store_dir(vault) / "favorites.json", favs)
        return {"favorites": favs}

    @app.delete("/api/tuning/favorites/{filename}")
    async def fav_del(filename: str):
        favs = [f for f in _favorites(vault) if f.get("filename") != filename]
        _write_json(_store_dir(vault) / "favorites.json", favs)
        return {"favorites": favs}
