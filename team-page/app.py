"""
Lucid Cove on Hermes — Team page (tunings / process records).
Reads Paperclip agents API + vault/ for Drop + per-agent latest.json.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

VAULT = Path(os.environ.get("LCH_VAULT", Path(__file__).resolve().parent.parent / "vault"))
PAPERCLIP_URL = os.environ.get("PAPERCLIP_URL", "http://127.0.0.1:3100").rstrip("/")
COMPANY_ID = os.environ.get("PAPERCLIP_COMPANY_ID", "7a9194f9-00ad-486d-87bc-be8a80669e65")
PAPERCLIP_PUBLIC = os.environ.get("PAPERCLIP_PUBLIC_URL", "http://127.0.0.1:3100").rstrip("/")
HERMES_PUBLIC = os.environ.get("HERMES_PUBLIC_URL", "http://127.0.0.1:9119").rstrip("/")
# Local Jules on this Team page (WebDAV → stewart NC). Override to external if needed.
JULES_URL = os.environ.get("JULES_URL", "/jules").rstrip("/") or "/jules"

STATIC = Path(__file__).resolve().parent / "static"

# Display order: Steward, PA, then team
ORDER = [
    "stewart", "alfred", "mercer", "gabe", "arthur", "archimedes",
    "julian", "iris", "vera", "ezra", "soren",
]
DISPLAY = {
    "stewart": "Stewart", "alfred": "Alfred", "mercer": "Mercer", "gabe": "Gabe",
    "arthur": "Arthur", "archimedes": "Archimedes", "julian": "Julian", "iris": "Iris",
    "vera": "Vera", "ezra": "Ezra", "soren": "Soren",
}

FREQ_COLORS = {
    "Peace": {"primary": "#5ce1e6", "secondary": "#7c5cff", "glow": "rgba(92,225,230,0.45)"},
    "Clarity": {"primary": "#a0ebff", "secondary": "#5ce1e6", "glow": "rgba(160,235,255,0.45)"},
    "Momentum": {"primary": "#ff6b5c", "secondary": "#ffb86c", "glow": "rgba(255,107,92,0.45)"},
    "Trust": {"primary": "#b8c6db", "secondary": "#7c5cff", "glow": "rgba(184,198,219,0.45)"},
    "Joy": {"primary": "#ffd700", "secondary": "#ffb86c", "glow": "rgba(255,215,0,0.45)"},
    "Connection": {"primary": "#e0b0ff", "secondary": "#ff6b5c", "glow": "rgba(224,176,255,0.45)"},
    "Presence": {"primary": "#7b7394", "secondary": "#7c5cff", "glow": "rgba(123,115,148,0.45)"},
    "Resilience": {"primary": "#d2691e", "secondary": "#8b4513", "glow": "rgba(210,105,30,0.45)"},
    "Courage": {"primary": "#ff8c00", "secondary": "#ff6347", "glow": "rgba(255,140,0,0.45)"},
    "Gratitude": {"primary": "#e8b830", "secondary": "#ffb347", "glow": "rgba(232,184,48,0.45)"},
    "Release": {"primary": "#9370db", "secondary": "#ba55d3", "glow": "rgba(147,112,219,0.45)"},
    "Integration": {"primary": "#20b2aa", "secondary": "#48d1cc", "glow": "rgba(32,178,170,0.45)"},
    "Boundary": {"primary": "#4682b4", "secondary": "#708090", "glow": "rgba(70,130,180,0.45)"},
}

app = FastAPI(title="Lucid Cove Team", version="0.1.0")
app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


DROP_BASE = os.environ.get("LTP_DROP_URL", "https://drop.lucidprinciples.com").rstrip("/")


def _freq_key(name: str | None) -> str:
    if not name:
        return "Peace"
    return next((k for k in FREQ_COLORS if k.lower() == str(name).lower()), "Peace")


def _fetch_live_drop() -> dict[str, Any] | None:
    """Best-effort public Drop for badge (prefer vault after morning_tune)."""
    try:
        with httpx.Client(
            timeout=8.0,
            headers={
                "User-Agent": "LucidCoveHermes-team-page/0.1",
                "Accept": "application/json",
            },
        ) as client:
            r = client.get(f"{DROP_BASE}/latest.json")
            r.raise_for_status()
            raw = r.json()
    except Exception:
        return None
    freq = (raw.get("frequency") or {})
    name = freq.get("name") or "Peace"
    tk = raw.get("tuning_key") or {}
    echo = raw.get("echo") or {}
    return {
        "date": raw.get("drop_date"),
        "frequency": name,
        "frequency_number": freq.get("number"),
        "signal_type": raw.get("signal_type"),
        # Principle = Canon song name (source_song), not the CC BY attribution line
        "principle": tk.get("source_song") or raw.get("tuning_key_source_song") or "",
        "attribution": tk.get("attribution") or raw.get("tuning_key_attribution"),
        "tuning_key": tk.get("text") or raw.get("tuning_key_text"),
        "drop_id": raw.get("sequence"),
        "echo_id": echo.get("id") or raw.get("echo_id"),
        "echo_audio_url": echo.get("audio_url") or raw.get("echo_audio_url"),
        "source": "live",
    }


def _today_drop() -> dict[str, Any]:
    vault = _read_json(VAULT / "drop" / "today.json") or {}
    live = _fetch_live_drop()
    # Prefer live frequency/date when present so badge matches drop.lucidprinciples.com
    data = {**vault, **{k: v for k, v in (live or {}).items() if v is not None}}
    if live and not vault.get("frequency"):
        data["note"] = data.get("note") or "Live Drop (run morning_tune.py to persist vault + agent records)"
    key = _freq_key(data.get("frequency"))
    data["frequency"] = key
    data["colors"] = FREQ_COLORS[key]
    data["player_url"] = f"{DROP_BASE}/"
    return data


def _ltp_store():
    try:
        import ltp_store  # type: ignore

        return ltp_store
    except ImportError:
        return None


def _agent_tune(slug: str) -> dict[str, Any]:
    data = _read_json(VAULT / "team" / slug / "latest.json") or {
        "agent": DISPLAY.get(slug, slug.title()),
        "status": "not_tuned",
    }
    md = VAULT / "team" / slug / "process_record.md"
    rec_path = data.get("process_record_path")
    if rec_path:
        p = VAULT / rec_path if not str(rec_path).startswith("/") else Path(rec_path)
        if p.is_file():
            md = p
    if md.is_file():
        try:
            full = md.read_text(encoding="utf-8")
            data["process_record"] = full
            data["process_record_preview"] = full[:1200]
            try:
                data["process_record_path"] = str(md.relative_to(VAULT))
            except ValueError:
                data["process_record_path"] = str(md)
        except OSError:
            pass

    # Prefer SQLite history (Cove-shaped); fall back to echoes.json sidecar
    store = _ltp_store()
    echoes: list = []
    if store is not None:
        try:
            echoes = store.list_echoes(slug, vault=VAULT)
        except Exception:
            echoes = []
    if not echoes:
        raw = _read_json(VAULT / "team" / slug / "echoes.json")
        echoes = raw if isinstance(raw, list) else []
    data["echoes"] = echoes
    if echoes and data.get("echo_num") is None:
        data["echo_num"] = echoes[0].get("echo_num")
    return data


async def _paperclip_agents() -> list[dict[str, Any]]:
    url = f"{PAPERCLIP_URL}/api/companies/{COMPANY_ID}/agents"
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(url)
            r.raise_for_status()
            raw = r.json()
    except Exception as e:
        return [{"_error": str(e)}]
    agents = raw if isinstance(raw, list) else (raw.get("agents") or raw.get("items") or raw.get("data") or [])
    return agents if isinstance(agents, list) else []


def _slug(name: str) -> str:
    return "".join(c for c in name.lower() if c.isalnum() or c in "-_")


@app.get("/")
async def index():
    """Team page — tunings roster."""
    return FileResponse(STATIC / "index.html")


@app.get("/work")
async def work():
    """Daily driver: Paperclip iframe + frequency badge → Drop player overlay."""
    return FileResponse(STATIC / "work.html")


@app.get("/tools")
async def tools():
    """Action Board (Actions / Links / Flows / Tools) — Jules card live."""
    return FileResponse(STATIC / "tools.html")


def _jules_voice_ws(request_host: str = "") -> str:
    """Prefer localhost voice tunnel when browsing via Mac SSH tunnel."""
    host = (request_host or "").split(":")[0].lower()
    if host in ("127.0.0.1", "localhost"):
        return (os.environ.get("JULES_VOICE_WS_LOCAL") or "ws://127.0.0.1:8302").rstrip("/")
    return (os.environ.get("JULES_VOICE_WS") or "wss://voice.cove.lucidcove.org").rstrip("/")


def _jules_voice_http(request_host: str = "") -> str:
    # Team page runs on P620 (host network) — talk to local voice publish port.
    return (
        os.environ.get("JULES_VOICE_HTTP")
        or os.environ.get("VOICE_INTERNAL_URL")
        or "http://127.0.0.1:8302"
    ).rstrip("/")


@app.middleware("http")
async def _permissions_policy(request, call_next):
    response = await call_next(request)
    response.headers["Permissions-Policy"] = "microphone=(self), camera=()"
    return response


@app.get("/jules")
async def jules_page(request: Request):
    """Real Cove Jules HTML, voice URL injected; saves → stewart NC Inbox."""
    path = STATIC / "jules.html"
    html = path.read_text(encoding="utf-8")
    host = request.headers.get("host") or ""
    voice = _jules_voice_ws(host)
    html = html.replace("__VOICE_SERVER_URL__", voice)
    # Soften Cove-only 403 copy for this overlay
    html = html.replace(
        "reopen Jules from this Cove (session missing)",
        "check Team page / STEWART_NC_PASSWORD",
    )
    html = html.replace("reopen Jules from Mission Control", "check stewart NC app password on Team page")
    return HTMLResponse(html)


@app.get("/api/tools")
async def tools_meta():
    drop = _today_drop()
    import jules_nc

    url = JULES_URL if JULES_URL.startswith("http") else "/jules"
    return JSONResponse({
        "jules_url": url,
        "frequency": drop.get("frequency"),
        "nc_configured": jules_nc.configured(),
        "note": "Cove Jules UI → stewart Inbox. Backlog=auto; Hold=discuss first.",
    })


@app.get("/api/jules/status")
async def jules_status():
    import jules_nc

    url, user, _ = jules_nc.nc_config()
    return JSONResponse({
        "configured": jules_nc.configured(),
        "nc_url": url,
        "nc_user": user,
        "inbox": jules_nc.JULES_NC_PATH,
        "voice_ws": _jules_voice_ws(),
    })


@app.get("/api/config")
async def jules_config_stub():
    """Minimal stub so Cove Jules dest chips work (Backlog + Hold only)."""
    return JSONResponse({
        "ok": True,
        "family_name": "Lucid Cove",
        "instance": {"family_name": "Lucid Cove"},
        "chat_agents": [],
        "agents": [],
        "voice_url": _jules_voice_ws(),
    })


@app.get("/api/presence/me")
async def jules_presence_stub():
    return JSONResponse({"ok": True, "agent_name": "Stewart"})


@app.post("/api/jules/save")
async def jules_save(body: dict[str, Any]):
    import jules_nc

    text = (body.get("text") or "").strip()
    filename = (body.get("filename") or "").strip()
    hold = bool(body.get("hold")) or ("hold" in filename.lower())
    result = await jules_nc.save_transcript(text, filename=filename, hold=hold)
    code = 200 if result.get("ok") else 400
    if result.get("error") and "PASSWORD" in str(result.get("error")):
        code = 503
    return JSONResponse(result, status_code=code)


@app.post("/api/jules/save-audio")
async def jules_save_audio(
    audio: UploadFile = File(...),
    filename: str = Form(""),
):
    import jules_nc

    if not filename:
        from datetime import datetime, timezone

        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
        filename = f"jules-{ts}.webm"
    if not filename.endswith(".webm"):
        filename = filename + ".webm"
    content = await audio.read()
    if not content:
        return JSONResponse({"ok": False, "error": "Empty audio"}, status_code=400)
    ok, err = await jules_nc.save_bytes(filename, content, audio.content_type or "audio/webm")
    if ok:
        return JSONResponse({"ok": True, "path": f"{jules_nc.JULES_NC_PATH}/{filename}"})
    return JSONResponse({"ok": False, "error": err}, status_code=500)


@app.post("/api/jules/transcribe-and-save")
async def jules_transcribe_and_save(
    audio: UploadFile = File(...),
    filename: str = Form(""),
):
    """Reuse Cove voice STT, then save transcript (+ audio) to stewart Inbox."""
    import jules_nc

    if not filename:
        from datetime import datetime, timezone

        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
        filename = f"jules-{ts}"
    audio_content = await audio.read()
    if not audio_content:
        return JSONResponse({"ok": False, "error": "Empty audio"}, status_code=400)

    voice_http = _jules_voice_http()
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            files = {"audio": ("recording.webm", audio_content, audio.content_type or "audio/webm")}
            resp = await client.post(
                f"{voice_http}/api/transcribe-and-save",
                files=files,
                data={"filename": filename},
            )
            voice_result = resp.json() if resp.content else {}
    except Exception as e:
        return JSONResponse({"ok": False, "error": f"Transcription failed: {e}"}, status_code=502)

    if not voice_result.get("ok"):
        return JSONResponse(
            {"ok": False, "error": voice_result.get("error", "Transcription failed")},
            status_code=502,
        )

    transcript = (voice_result.get("transcript") or voice_result.get("text") or "").strip()
    if not transcript:
        return JSONResponse({"ok": False, "error": "Empty transcription"}, status_code=502)

    hold = "hold" in filename.lower()
    result = await jules_nc.save_transcript(transcript, filename=filename, hold=hold)
    if not result.get("ok"):
        return JSONResponse(result, status_code=500)

    webm_name = filename.replace(".md", "") + ".webm"
    if not webm_name.endswith(".webm"):
        webm_name += ".webm"
    ok_audio, _ = await jules_nc.save_bytes(webm_name, audio_content, "audio/webm")
    result["transcript"] = transcript
    result["audio_saved"] = ok_audio
    return JSONResponse(result)


@app.get("/api/health")
async def health():
    return {"ok": True, "vault": str(VAULT), "vault_exists": VAULT.is_dir()}


def _ltp_config_path() -> Path:
    return VAULT / "ltp_config.json"


def _read_ltp_config() -> dict[str, Any]:
    defaults = {
        "enabled": True,
        "model": "qwen3:8b",
        "ollama_base_url": "http://127.0.0.1:11434/v1",
        "max_rounds": 3,
        "retry_sleep_sec": 30,
        "note": "Tuning model is independent of Paperclip/Hermes orchestrator models.",
    }
    path = _ltp_config_path()
    if path.is_file():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                defaults.update(raw)
        except (json.JSONDecodeError, OSError):
            pass
    return defaults


@app.get("/api/ltp/config")
async def get_ltp_config():
    """Dedicated morning-tuning settings (not orchestrator model)."""
    return JSONResponse(_read_ltp_config())


@app.get("/api/kb/search")
async def kb_search(q: str = "", k: int = 5):
    """Semantic search over Lucid Principles KB (vault/kb_index.sqlite)."""
    q = (q or "").strip()
    if not q:
        return JSONResponse({"error": "q required"}, status_code=400)
    k = max(1, min(int(k or 5), 20))
    try:
        import kb_retrieve  # type: ignore

        hits = kb_retrieve.search(q, k=k, vault=VAULT)
        return JSONResponse({"query": q, "hits": hits})
    except FileNotFoundError as e:
        return JSONResponse({"error": str(e), "hint": "run scripts/kb_index.py on host"}, status_code=503)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.put("/api/ltp/config")
async def put_ltp_config(body: dict[str, Any]):
    """Update tuning on/off + model. Morning cron/runner read this file."""
    cfg = _read_ltp_config()
    if "enabled" in body:
        cfg["enabled"] = bool(body["enabled"])
    if "model" in body and str(body["model"]).strip():
        cfg["model"] = str(body["model"]).strip()
    if "ollama_base_url" in body and str(body["ollama_base_url"]).strip():
        cfg["ollama_base_url"] = str(body["ollama_base_url"]).strip()
    if "max_rounds" in body:
        try:
            cfg["max_rounds"] = max(1, int(body["max_rounds"]))
        except (TypeError, ValueError):
            pass
    if "retry_sleep_sec" in body:
        try:
            cfg["retry_sleep_sec"] = max(0, int(body["retry_sleep_sec"]))
        except (TypeError, ValueError):
            pass
    path = _ltp_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    return JSONResponse(cfg)


@app.get("/api/agents/{slug}")
async def agent_detail(slug: str):
    slug = "".join(c for c in slug.lower() if c.isalnum() or c in "-_")
    tune = _agent_tune(slug)
    return JSONResponse({
        "slug": slug,
        "name": DISPLAY.get(slug, slug.title()),
        "tune": tune,
        "drop": _today_drop(),
    })


@app.get("/api/agents/{slug}/echoes")
async def agent_echoes(slug: str):
    """Echo history for Paperclip-styled Team UI / future plugin."""
    slug = "".join(c for c in slug.lower() if c.isalnum() or c in "-_")
    tune = _agent_tune(slug)
    return JSONResponse({
        "slug": slug,
        "name": DISPLAY.get(slug, slug.title()),
        "echoes": tune.get("echoes") or [],
    })


@app.get("/api/agents/{slug}/echoes/{echo_num}")
async def agent_echo_record(slug: str, echo_num: int):
    """Full Process Record for one Echo (DB first, then latest.md fallback)."""
    slug = "".join(c for c in slug.lower() if c.isalnum() or c in "-_")
    store = _ltp_store()
    if store is not None:
        try:
            row = store.get_process_record(slug, echo_num, vault=VAULT)
            if row:
                return JSONResponse({"slug": slug, "name": DISPLAY.get(slug, slug.title()), **row})
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)
    # Fallback: only if requesting latest echo and md exists
    tune = _agent_tune(slug)
    if tune.get("echo_num") == echo_num and tune.get("process_record"):
        return JSONResponse({
            "slug": slug,
            "name": DISPLAY.get(slug, slug.title()),
            "echo_num": echo_num,
            "record_text": tune["process_record"],
            "frequency": tune.get("frequency"),
            "principle": tune.get("principle"),
            "love_equation_value": tune.get("love_equation_value"),
            "when": tune.get("drop_date"),
            "source": "latest.md",
        })
    return JSONResponse({"error": "not_found", "slug": slug, "echo_num": echo_num}, status_code=404)


@app.get("/api/team")
async def team():
    drop = _today_drop()
    agents_raw = await _paperclip_agents()
    if agents_raw and agents_raw[0].get("_error"):
        pc_error = agents_raw[0]["_error"]
        agents_raw = []
    else:
        pc_error = None

    by_slug: dict[str, dict[str, Any]] = {}
    for a in agents_raw:
        name = str(a.get("name") or "")
        slug = _slug(name)
        by_slug[slug] = {
            "id": a.get("id"),
            "name": name,
            "role": a.get("role"),
            "title": a.get("title"),
            "status": a.get("status"),
            "urlKey": a.get("urlKey"),
            "paperclip_url": f"{PAPERCLIP_PUBLIC}/agents/{a.get('urlKey') or a.get('id')}",
            "tune": _agent_tune(slug),
        }

    # Ensure pack roster slots exist even if Paperclip briefly unreachable
    for slug in ORDER:
        if slug not in by_slug:
            by_slug[slug] = {
                "id": None,
                "name": DISPLAY.get(slug, slug.title()),
                "role": None,
                "title": None,
                "status": "missing",
                "urlKey": None,
                "paperclip_url": PAPERCLIP_PUBLIC,
                "tune": _agent_tune(slug),
            }

    ordered = [by_slug[s] for s in ORDER if s in by_slug]
    # append any unexpected agents
    for slug, card in by_slug.items():
        if slug not in ORDER:
            ordered.append(card)

    return JSONResponse({
        "drop": drop,
        "paperclip_error": pc_error,
        "links": {
            "paperclip": PAPERCLIP_PUBLIC,
            "hermes": HERMES_PUBLIC,
        },
        "agents": ordered,
    })
