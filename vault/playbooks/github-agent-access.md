# Agent GitHub access — Lucid Cove on Hermes

Scoped **work** credentials for public OSS repos. **Not** the house-backup PAT.

**Runbook:** `runbooks/RB-hermes-github-repos.md`  
**Script:** `scripts/setup_github_repos.sh`

## Repos (v1)

| Clone on the house | GitHub | Kind |
|--------------------|--------|------|
| `/opt/data/repos/lucid-cove` | `LucidPrinciples/lucid-cove` | Public product |
| `/opt/data/repos/ltp-core` | `LucidPrinciples/ltp-core` | Public product |
| `/opt/data/repos/ltp-drop` | `LucidPrinciples/ltp-drop` | Public product |
| `/opt/data/repos/lucid-cove-hermes` | `LucidTunerAI/lucid-cove-hermes` | Private overlay |

Host path: `~/lucid-cove-hermes/data/repos/` (same files; Hermes write fence).

Do **not** clone `LucidCoveHermes-Backups` here (that is the nightly house snapshot). Do **not** put Socrates / Presence-backup repos on this PAT.

Public later: fresh export of the overlay to `LucidPrinciples/lucid-cove-hermes` — not a visibility flip.

## Auth (blast radius)

- **Separate** fine-grained PAT from the backup token.
- Resource owner: **LucidPrinciples**.
- Only the four work repos above (three public + private overlay).
- Permissions: **Contents** Read and write, **Pull requests** Read and write. Nothing else (no admin, no workflows, no org).
- Store: host `~/.config/lucid-cove-hermes/github-agent.pat` → copied to `/opt/data/.secrets/github-agent` for git-inside-Hermes. Never in compose `.env`, never in the backup snapshot.
- `main` is protected on GitHub — agents push branches and open PRs; **Chords merges**.

## Ship path (same as every Cove)

```
edit in data/repos/<repo>  →  commit  →  PR  →  Chords merges  →  installs pull main
```

Public commit voice: product-repo tone only (no personal names, home paths, hostnames, family ids).

## Do not

- Reuse the backup PAT.
- Force-push (`approvals.deny` already blocks `git push --force*`).
- Merge `main` from the agent.
- Backup `data/repos/` (those clones live on GitHub already).
