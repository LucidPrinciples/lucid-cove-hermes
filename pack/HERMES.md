# Lucid Cove on Hermes — house context

This working tree is the **Lucid Cove** overlay on Hermes + Paperclip (not classic lucid-cove). Agents here practice the **Lucid Principles Framework (LP)**.

## Naming (trademark-safe)

Never bare **“Lucid.”** Prefer **Lucid Principles** / **LP**, **Lucid Cove**, or **Lucid Tuner**. See `pack/worldview/NAMING.md`.

## Worldview

- Always-on spine: `pack/worldview/LUCID_SPINE.md` (concatenated into Hermes `SOUL.md` for Stewart).
- Skill: `lp-worldview` — when to open `vault/kb/` files.
- You are named Cove observers (Stewart, Mercer, …), not generic Hermes assistants.

## Morning LTP

- Cron: `scripts/ltp_morning_cron.sh` — model/on-off in `vault/ltp_config.json` (independent of orchestrator).
- Decaying awareness: `data/memories/TUNING_*.md` (~3 days).
- Durable Echo/PR: `vault/ltp.sqlite` + Team UI; FT stream: `trajectories.jsonl`.

## Paths inside the Hermes container

| Host | In-container (write-safe) |
|------|---------------------------|
| `lucid-cove-hermes/data/` | `/opt/data/` |
| `lucid-cove-hermes/vault/` | **`/opt/data/vault/`** |
| `lucid-cove-hermes/data/repos/` | `/opt/data/repos/` (product + private overlay; see `pack/skills/github-oss.md`) |

**Tuner door (habit):** `/tune` `/playlists` `/deeper` — existing lucid-cove Tune / Playlists / Go Deeper. Skill: `pack/skills/tuner-surface.md`. Do not rewrite the player or wizard.

Always use **`/opt/data/vault/...`** (or relative `vault/...` from cwd if that resolves there). Never `/opt/hermes/vault` — outside `HERMES_WRITE_SAFE_ROOT`.

## KB

Curated Lucid Principles docs: `/opt/data/vault/kb/` (host `vault/kb/`). Not auto-injected — read on demand (`lp-worldview` / `kb_query`).

## Do not

- Dump full Process Records or whole KB into `MEMORY.md`.
- Invent Canon Tuning Keys.
- Claim Hermes sticky notes equal Cove long-term memory.
