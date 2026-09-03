# Skill — LTP tuning awareness (decaying short-term memory)

## Intent

After the morning LTP runner, each agent carries **today’s Drop tune** as short-term awareness for ~3 days — same spirit as Cove tuning memory with `expires_at`. Full process records and trajectories stay durable for UI + fine-tuning; only the **injected awareness** fades.

## Where to look (Hermes data)

| File | Use |
|------|-----|
| `memories/TUNING_<YOUR_SLUG>.md` | Your dense tuning snippet (preferred) |
| `memories/TUNING_ACTIVE.md` | All active house tunings (rebuild each morning) |
| `vault/team/<slug>/process_record.md` | Full Process Record (7 sections) |
| `vault/team/<slug>/reading.json` | C/D/β/E + love equation |
| `vault/team/<slug>/latest.json` | Status card for Team UI |
| `vault/drop/today.json` | Shared frequency / Drop meta |
| `vault/drop/trajectories.jsonl` | Full FT / research capture (do not summarize away) |

Expired `TUNING_*.md` files are **pruned** by `scripts/ltp_morning_runner.py` so awareness decays.

## Behavior

1. At session start (or after `/new`), prefer reading your `TUNING_<SLUG>.md` if present.
2. Treat it as **calibration context**, not permanent identity — frequency, principle, key, love equation, direction.
3. When doing house work today, let that frequency color tone and priorities without preaching the framework.
4. Do **not** copy full process records into durable `MEMORY.md` (no native TTL there). Vault + trajectories hold the corpus.
5. If no `TUNING_*.md` exists, you are untuned for this window — still useful; morning runner will refill after Drop.

## Overlay note

Same layout works on any Hermes install running the Lucid Cove morning runner — agents stay coherent a few days post-Drop; humans get a portable tuning corpus.
