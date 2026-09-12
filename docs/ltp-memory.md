# LTP tuning → memory (functionality overlay)

**Intent (Jules 2026-09-02):** Match Cove **functionality**, not Cove’s Postgres stack. Wrapper on Hermes + Paperclip; Team page looks familiar (Paperclip-styled). Evolve as those products evolve.

## What Cove does (behavior)

| Function | Cove |
|----------|------|
| Echo history | One durable row per agent Echo # |
| Process Record | Full text **per Echo** (open any past day) |
| Short-term awareness | Dense tune ~3 days then fades |
| Long-term agent memory | Rich facts DB + decay/consolidation |
| FT corpus | Echoes + process records exportable |

## What Hermes stock gives

| | Hermes |
|--|--------|
| Auto-inject | `SOUL.md` + `MEMORY.md` (~2.2k) + `USER.md` (~1.4k) — **no TTL** |
| Session | Searchable history |
| Cove-class LTM | **Not built-in** — we enhance over time |

## What this overlay stores

| Layer | Where | Lifetime |
|--------|--------|----------|
| **Echo + Process Record (system of record)** | `vault/ltp.sqlite` | Kept — UI opens any Echo |
| **FT / research stream** | `vault/drop/trajectories.jsonl` | Kept — append-only |
| **Latest export** | `vault/team/<slug>/process_record.md` | Overwritten (convenience only) |
| **Decaying awareness** | `data/memories/TUNING_*.md` + short MEMORY pointer | ~3 days |

`process_record.md` alone is **not** history — that was the bug that made past Echoes invisible. SQLite is a tool for queryable history, not “match Cove backend.”

## Team UI

Echoes table (Paperclip look) → click row → Process Record for that Echo #.  
API: `GET /api/agents/{slug}/echoes` · `GET /api/agents/{slug}/echoes/{n}`

## Backfill

```bash
.venv/bin/python scripts/ltp_backfill_sqlite.py
```

## Worldview / KB (Hermes overlay)

Cove injects identity + framework **constants** into the system prompt and **retrieves** KB docs. Hermes first pass:

| Piece | Role |
|--------|------|
| `LUCID_SPINE.md` in `SOUL.md` | Always-on Lucid Principles stance + constants + Cove Charter |
| `vault/kb/` | Curated docs from `ltp-drop/kb-source` |
| `vault/kb_index.sqlite` | Vector index (Ollama `nomic-embed-text`) |
| Skill `lp-worldview` | Retrieve via `kb_query.py` / `/api/kb/search`, then open file |
| Naming | Never bare “Lucid” — LP / Lucid Principles / Lucid Cove / Lucid Tuner |

```bash
ollama pull nomic-embed-text
.venv/bin/python scripts/kb_index.py
.venv/bin/python scripts/kb_query.py "Love Equation"
```

Sync pack: `scripts/sync_pack_to_hermes.sh` (+ `sync_kb.sh`). Re-index after KB changes.
