# Lucid Cove on Hermes

Overlay for [Hermes Agent](https://github.com/NousResearch/hermes-agent): Team, Tune / Playlists, Attention | Action, and a latch to a **Lucid Tuner** account.

This is not a fork of Hermes or Paperclip. Classic [`lucid-cove`](https://github.com/LucidPrinciples/lucid-cove) is the online app / Mission Control. This repo is the house overlay you run on **your** computer.

Never send people to someone else's house URL.

## Install (computer)

1. Install [Hermes](https://hermes-agent.nousresearch.com/docs) (`hermes setup`). You bring your own model keys.
2. Optional: [Paperclip](https://paperclip.ing) if you want Attention as a ticket spine. Skip it and the house still runs (Team, Action, habit floor). Attention then uses Hermes Kanban, or stays empty.
3. Clone this repo (`https://github.com/LucidPrinciples/lucid-cove-hermes`). Start the team UI (`team-page/`) and run `scripts/sync_pack_to_hermes.sh` so SOULs / skills land in Hermes.
4. Create or sign in at [app.lucidtuner.com](https://app.lucidtuner.com) → Settings → **Get my connect key** → paste it in **this** house Gear.

Connect is a latch, not an installer. The Lucid Tuner account is created on the public Tuner, not by this overlay.

## Layout

| Path | Purpose |
|------|---------|
| `team-page/` | House UI (port 3200) |
| `pack/` | SOULs, skills, Lucid Principles spine |
| `scripts/` | Pack sync, morning LTP helpers |
| `tests/` | stdlib unittest |
| `vault/` | Empty placeholder — your house brain stays local, never this git |

## License

Code: Apache-2.0. Lucid Principles Canon materials: CC BY 4.0. Hermes is MIT (Nous).
