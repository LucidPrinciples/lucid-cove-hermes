<p align="center">
  <img src="docs/assets/hero.svg" alt="Lucid Cove on Hermes — house overlay for Hermes Agent" width="100%">
</p>

# Lucid Cove on Hermes

**House overlay for [Hermes Agent](https://github.com/NousResearch/hermes-agent).** Team, Tune / Playlists, Attention | Action, and a latch to a Lucid Tuner account — on a computer you own.

[![License: Apache 2.0](https://img.shields.io/badge/code-Apache%202.0-blue.svg)](./LICENSE)
[![Canon: CC BY 4.0](https://img.shields.io/badge/Canon-CC%20BY%204.0-lightgrey.svg)](#license)
[![Runtime: Hermes](https://img.shields.io/badge/runtime-Hermes%20Agent-7c5cff.svg)](https://github.com/NousResearch/hermes-agent)
[![App: Lucid Tuner](https://img.shields.io/badge/app-lucidtuner.com-5ce1e6.svg)](https://app.lucidtuner.com)

Not a fork of Hermes or [Paperclip](https://paperclip.ing). Classic [`lucid-cove`](https://github.com/LucidPrinciples/lucid-cove) is the original self-hosted Cove / Mission Control. This repo is the **Hermes-class overlay**: same Lucid Principles practice, same Tuner identity, different harness.

> **Status: public pack (v1).** Install on your Hermes. The free habit app is [app.lucidtuner.com](https://app.lucidtuner.com).

## Family of repos

| Repo | What it is |
|------|------------|
| [`lucid-cove`](https://github.com/LucidPrinciples/lucid-cove) | Original Lucid Cove — self-hosted family home, Mission Control |
| [`lucid-cove-hermes`](https://github.com/LucidPrinciples/lucid-cove-hermes) | This overlay — Lucid Cove **on Hermes** |
| [`ltp-core`](https://github.com/LucidPrinciples/ltp-core) | Lucid Tuner Protocol runtime (Drop client, Love Equation, Truth Gate) |
| [`ltp-drop`](https://github.com/LucidPrinciples/ltp-drop) | Daily signed Drop archive — `curl` is the integration |

## Install (computer)

1. Install [Hermes](https://hermes-agent.nousresearch.com/docs) (`hermes setup`). Bring your own model keys.
2. Optional: [Paperclip](https://paperclip.ing) if you want Attention as a ticket spine. Skip it and the house still runs (Team, Action, habit floor). Attention then uses Hermes Kanban, or stays empty.
3. Clone this repo. Start the team UI (`team-page/`) and run `scripts/sync_pack_to_hermes.sh` so SOULs / skills land in Hermes.
4. Create or sign in at [app.lucidtuner.com](https://app.lucidtuner.com) → Settings → **Get my connect key** → paste it in **this** house Gear.

Connect is a latch, not an installer. The Lucid Tuner account is created on the public Tuner, not by this overlay. Pro (unlimited Tune) is a separate Stripe door on the app.

```bash
git clone https://github.com/LucidPrinciples/lucid-cove-hermes.git
cd lucid-cove-hermes
```

See [docs/install.md](docs/install.md) for compose and env.

## Layout

| Path | Purpose |
|------|---------|
| `team-page/` | House UI (port 3200) |
| `pack/` | SOULs, skills, Lucid Principles spine |
| `scripts/` | Pack sync, morning LTP helpers |
| `tests/` | stdlib unittest |
| `vault/` | Empty placeholder — your house brain stays local, never this git |

## License

- **Code:** Apache License 2.0 — see [`LICENSE`](./LICENSE).
- **Canon content** (the 22 Lucid Principles and quoted framework text): Creative Commons Attribution 4.0 (CC BY 4.0). Canon is quoted exactly and never generated or modified.
- **Hermes Agent** is MIT (Nous Research).

## Links

- **Lucid Principles framework** — https://lucidprinciples.com
- **The Lucid Path books** — [*The Lucid Path: Framework*](https://www.amazon.com/dp/B0H5T1HDFC) and [*The Lucid Path: Origins*](https://www.amazon.com/dp/B0H5TKL2WD)
- **Papers** — https://jasongarriotte.com/papers/ · [Sycophancy as Nash Equilibrium](https://zenodo.org/records/20616512) · [One Field](https://zenodo.org/records/18826966)
- **The app** — daily tuning, free: https://app.lucidtuner.com
- **Lucid Cove (site)** — https://lucidcove.org
- **The daily Drop** — https://drop.lucidprinciples.com
- **The Canon** — https://lucidprinciples.com/canon/
- **Chords of Truth (YouTube)** — https://www.youtube.com/@LucidPrinciplesStories
- **Self-host the original Cove** — https://lucidprinciples.com/open
- **Support the work** — https://github.com/sponsors/LucidPrinciples

## Built by Lucid Principles

Free and open. If it's useful to you, here's where it leads — the things that keep the work alive:

- **Research** — [Sycophancy as Nash Equilibrium](https://zenodo.org/records/20616512) · [One Field](https://zenodo.org/records/18826966)
- **Books** — *The Lucid Path*: [Framework](https://www.amazon.com/dp/B0H5T1HDFC) · [Origins](https://www.amazon.com/dp/B0H5TKL2WD)
- **The app** — daily tuning, free: [app.lucidtuner.com](https://app.lucidtuner.com)
- **Self-host the platform** — [lucidprinciples.com/open](https://lucidprinciples.com/open)
- **Support the work** — [GitHub Sponsors](https://github.com/sponsors/LucidPrinciples)

*Lucid Principles Canon by Chords of Truth, CC BY 4.0.*

---

<p align="center">
  <a href="https://lucidprinciples.com/vision/"><img src="https://lucidprinciples.com/images/lp-mark.png" width="72" alt="Lucid Principles"></a>
</p>

<p align="center"><b>Lucid Principles</b><br>
<sub>A private, self-hosted home for your family and its intelligence. Where everyone is tuning.</sub></p>

<p align="center">
  <a href="https://lucidprinciples.com/vision/"><b>The Vision — every door in</b></a><br>
  <sub><a href="https://lucidcove.org">Lucid Cove</a> · <a href="https://app.lucidtuner.com">The App</a> · <a href="https://drop.lucidprinciples.com">The Daily Drop</a> · <a href="https://jasongarriotte.com/papers/">Research</a> · <a href="https://lucidprinciples.com/canon/">The Canon</a></sub>
</p>
