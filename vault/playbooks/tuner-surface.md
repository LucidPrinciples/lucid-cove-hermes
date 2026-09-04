# Tuner surface — reuse, do not rewrite

The public habit door is already built in **lucid-cove** as the **Tuner-tier Home**:

**Tune · Playlists · Go Deeper** (not Approvals).

Operator+ Cove home hid those tabs and showed Pending Approvals. We are putting the Tuner door on this overlay. Later it is what a new account is (`lucidtuner.com` / `app.lucidtuner.com`). Accounts stay on `app.lucidcove.org` until that flip.

## Do not

- Write a new tuning wizard, player, or playlist model
- Clone `lucidcove-shared` or rework Operator tier / VPS accounts
- Touch Socrates / LT from this overlay

## Source of truth (lucid-cove)

| Piece | File |
|-------|------|
| Tuner Home (three buttons) | `src/dashboard/static/js/panels.js` (`MC.tier.level < 10`) |
| Tune flow (LTP 8 steps) | `src/dashboard/static/js/tune-flow.js` |
| Playlists (signals + genres) | `src/dashboard/static/js/playlists.js` |
| **The player** (`otSetPlaylist` / `otRenderPlayer`) | `src/dashboard/static/js/tuning-panel.js` |
| Onboarding | `src/dashboard/static/js/onboarding.js` |
| Go Deeper copy | `panels.js` `case 'go-deeper'` |
| Audio CDN | `https://audio.lucidtuner.com/Lucid_Tuner` |
| Tabs / Free tier | `config/shared-agent.yaml`, `permissions.py` |

Hermes clone: `/opt/data/repos/lucid-cove/` + work in `/opt/data/repos/lucid-cove-hermes/`.

## Overlay job

1. Host Tune / Playlists / Go Deeper as the **front** of this house UI (Team / Work / Action Board stay ops).
2. **Mount** the files above (thin adapter for `MC` / `/api/tuning/*`). Copies live in `team-page/static/tuner/` — re-copy from lucid-cove when those files change; do not fork the flow.
3. House sessions: `vault/tuner/sessions.json` (gitignored). LLM coaching not required — JS static fallbacks.
4. Ship: branch → PR on `LucidTunerAI/lucid-cove-hermes`.

Public account + `app.lucidtuner.com` is **after** this door works here.
