# House backup intent — Lucid Cove on Hermes

Private off-site copy of **this house**, not the public product repos.

**Remote:** `https://github.com/LucidTunerAI/LucidCoveHermes-Backups`  
**Script:** `scripts/house_backup.sh`  
**Runbook:** `runbooks/RB-hermes-house-backup.md`

## What is in

| Tree | Why |
|------|-----|
| `vault/` | House brain: LTP sqlite, Echoes, process records, KB, playbooks |
| `data/memories/` | Hermes MEMORY + decaying TUNING_* |
| `data/sessions` (and session-like dirs) | Chat/session history if Hermes wrote it |
| `data/SOUL.md`, `config.yaml` (redacted), souls/skills/worldview | Identity + safety config |
| `paperclip/data/` | Tickets / company state |
| Overlay compose + `pack/` + `scripts/` + `docs/` + `caddy/` | Restore shape of the box |

## What is never in

- `.env` / `.env.*` / `*.pat` / `*.pem` / `*.key`
- GitHub PAT (lives only at `~/.config/lucid-cove-hermes/github-backup.pat` on P620)
- `team-page/.env`, `docker/.env`, `paperclip/.env`, `data/.env`
- `upstream/` (Nous clone), `.venv`, `__pycache__`
- Any single file over 90 MB (GitHub blob limit)

Secrets stay on the host. Restore still needs the live `.env` files (or re-create them).

## Cadence

Daily **08:30** host time (after 06:15 morning LTP). Cron is on the **host** (not in the git snapshot). Manual: `scripts/house_backup.sh`.

## Restore from a new box (what this is / isn’t)

This backup is the **house** — brain, tickets, overlay — not a disk image and not the public product git.

### Comes back from GitHub

Vault (Echoes, process records, `ltp.sqlite`, KB), Hermes memories/SOUL/skills/worldview, session-like dirs + `data/logs`, Paperclip `data/` + SQL dumps, overlay `pack/` `scripts/` `docs/` compose files, `caddy/hermes.cove.caddy` snippet.

### Recreate (never in the repo)

| Piece | Where it lives now | How you get it back |
|-------|--------------------|---------------------|
| Secrets | `docker/.env`, `data/.env`, `paperclip/.env`, `team-page/.env` | Password manager. `API_SERVER_KEY`, `BETTER_AUTH_SECRET`, `MATRIX_*`, dashboard session token, Stewart NC app password |
| Backup PAT | `~/.config/lucid-cove-hermes/github-backup.pat` | New fine-grained token |
| `config.yaml` secret values | redacted in snapshot | Re-enter any API keys after restore |
| Upstream Hermes | `upstream/` clone + Docker image | `git clone` Nous + `docker compose build` |
| Python venv | `~/lucid-cove-hermes/.venv` | `python3 -m venv` + `lucid-tuner-protocol` |
| Ollama models | host Ollama | `ollama pull` (tuning model + `nomic-embed-text`) — tens of GB, on purpose |
| Crontab | `crontab -l` | Re-install from `RB-hermes-house-backup.md` + `RB-morning-tune.md` |
| Live Caddy site | `~/.lucidcove/caddy/conf.d/hermes.cove.caddy` | Copy snippet from backup/`caddy/` then reload `lucidcove-caddy` |
| Mac desk | `Start Lucid Cove.command` + Desktop token | AgentWorkspace + `RB-mac-lucid-cove-desk.md` |
| Matrix users | founder Dendrite | Existing Cove; not this snapshot |
| Jules Inbox files | Nextcloud `stewart` | NC, not Hermes |

### Not a full `data/` clone

The script copies known house paths under `data/` (memories, souls, skills, sessions/logs, top-level SOUL/config). It does **not** dump every Hermes cache/runtime file. If a new-install restore ever misses a Hermes-internal DB, widen the include list (still exclude `.env`).

## Auth

Fine-grained PAT, **Contents: Read and write**, this repo only. Injected only for `git clone` / `git push`; `origin` URL on disk is always the clean https remote.
