# Lucid Cove on Hermes — pack

Apply onto an existing Hermes + Paperclip install (container or host).

## Naming

- **Stewart** = Steward (house).
- **Alfred** = personal agent for the board operator.
- Display form with Cove last name: `Stewart.Cove`, `Mercer.Cove`, `Alfred.Cove` (this lab last name: **Cove**).

## Contents

| Path | Purpose |
|------|---------|
| `souls/` | SOUL.md sources for Hermes profiles / Paperclip prompts |
| `skills/` | `ltp-tuning-awareness`, `lp-worldview` |
| `worldview/` | `LUCID_SPINE.md` + `NAMING.md` (trademark-safe) |
| `ORG.md` / `MISSION.md` / `HERMES.md` | Org, mission, house context |

## Apply (P620)

```bash
# from Mac — sync pack + scripts, then on host:
rsync -az --exclude '.venv' pack scripts docs \
  lphomebase@lp-homebase.mesh.lucidcove.org:/home/lphomebase/lucid-cove-hermes/
ssh lphomebase@lp-homebase.mesh.lucidcove.org \
  'chmod +x ~/lucid-cove-hermes/scripts/sync_pack_to_hermes.sh && ~/lucid-cove-hermes/scripts/sync_pack_to_hermes.sh'
```

What that does:

1. `data/SOUL.md` ← `Stewart.Cove.md` **+** `LUCID_SPINE.md` (Lucid Principles worldview)
2. `data/souls/` / `skills/` / `worldview/`
3. `vault/kb/` from `ltp-drop/kb-source` or `pack/kb-cache`
4. Short `MEMORY.md` LTP pointer; `.hermes.md` house context

Naming: never bare “Lucid” — Lucid Principles / LP, Lucid Cove, Lucid Tuner.

Then **`/new`** so SOUL + MEMORY refresh. Paperclip roster: `ORG.md` + hire runbooks.
