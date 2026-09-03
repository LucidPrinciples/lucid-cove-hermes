# Ship path — Lucid Cove on Hermes overlay

Same shape as Clearfield + AgentWorkspace on `lucid-cove`.

## Two GitHub homes (do not mix)

| Repo | Role |
|------|------|
| **`LucidTunerAI/lucid-cove-hermes`** (private) | Working overlay. Both benches PR here. |
| **`LucidTunerAI/LucidCoveHermes-Backups`** | Nightly **house snapshot** (vault, memories). Not a dev remote. |
| **`LucidPrinciples/lucid-cove`** (and `ltp-core`, `ltp-drop`) | Public product. Unrelated to this overlay until a feature is promoted. |

Later, when the overlay is ready to open: **fresh-history export** to `LucidPrinciples/lucid-cove-hermes` (clean tree, no hostnames/secrets). Do not just flip this private repo public.

## Benches

| Bench | Worktree |
|-------|----------|
| Board (this Mac / AgentWorkspace) | `projects/lucid-cove-hermes` |
| Hermes agents | `/opt/data/repos/lucid-cove-hermes` |
| Live P620 stack | `~/lucid-cove-hermes` — **install**, not a second origin of truth |

```
edit in a bench clone  →  branch  →  PR  →  Chords merges  →  live tree pulls overlay files  →  restart if needed
```

Live pull must **not** overwrite `data/`, `vault/` house files, `.env`, `upstream/`, `paperclip/data/`.

## Do not

- Push overlay work to the backup repo
- Commit `.env`, PATs, `data/`, Echo sqlite
- Treat an unmerged bench edit as live on the P620
