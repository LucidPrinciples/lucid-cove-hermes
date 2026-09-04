# Skill — Tuner surface (habit door)

The product people log into is **Tune · Playlists · Go Deeper**, already built in `lucid-cove`. This overlay **hosts** it. Do not rewrite the wizard or the player.

## Read first

`vault/playbooks/tuner-surface.md`

Then the lucid-cove files listed there (`tune-flow.js`, `playlists.js`, `tuning-panel.js`, Tuner home in `panels.js`).

## Work

- Overlay repo: `/opt/data/repos/lucid-cove-hermes`
- Copy/mount existing JS + player CSS; add a thin adapter only
- No new 8-step flow. No new audio engine. `otSetPlaylist` stays the player.
- Operator Approvals UI is **not** this door
- Branch → PR → stop for board merge

## Later (not this ticket)

Accounts, `app.lucidtuner.com`, retiring Operator, VPS shared compose.
