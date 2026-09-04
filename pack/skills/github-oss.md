# Skill — git clones on this house

Work from clones inside the write fence. Two kinds of remote — do not mix.

## Where

| Path (Hermes) | Repo | Kind |
|---------------|------|------|
| `/opt/data/repos/lucid-cove` | `LucidPrinciples/lucid-cove` | Public product |
| `/opt/data/repos/ltp-core` | `LucidPrinciples/ltp-core` | Public product |
| `/opt/data/repos/ltp-drop` | `LucidPrinciples/ltp-drop` | Public product |
| `/opt/data/repos/lucid-cove-hermes` | `LucidTunerAI/lucid-cove-hermes` | **Private overlay** (this house’s code) |

House **backup** is a different remote (`LucidCoveHermes-Backups`). Never push overlay work there.

**Tuner habit door** lives in the overlay (`/tune` `/playlists` `/deeper`) but the wizard + player are **lucid-cove** files. See `pack/skills/tuner-surface.md`. Do not invent a new Tune flow.

## Ship (locked)

1. New branch off `main`  
2. Commit (corporate product tone — no hostnames, home paths, family names)  
3. `git push -u origin BRANCH`  
4. Open a PR against `main`  
5. **Stop.** Board (Chords) merges. Do not merge. Do not force-push.

If git/push is fenced, emit a Mac-safe host pack — do not invent a bypass.

## Do not

- Push to `main`
- Use the house-backup remote (`LucidCoveHermes-Backups`)
- Put tokens in commit messages, remotes, or chat
- Treat these clones as live Cove deploys — merge then pull on the install
