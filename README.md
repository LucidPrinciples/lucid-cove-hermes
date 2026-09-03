# Lucid Cove on Hermes

**Product name:** Lucid Cove on Hermes  
**Repo (private working):** `LucidTunerAI/lucid-cove-hermes`  
**Public later:** clean export to `LucidPrinciples/lucid-cove-hermes` (not a visibility flip).

Lucid Cove practice + team org **on** [Hermes Agent](https://github.com/NousResearch/hermes-agent) and [Paperclip](https://paperclip.ing) — not a fork of either. Classic `lucid-cove` stays the reference Cove product; this repo is the overlay / rebuild lane (Clearfield-style).

> Trademark: always **Lucid Cove** / **Lucid Principles** (never bare “Lucid”).

## Org shape (Phase-1 family Cove)

```text
Board (Jason)
  └── Stewart — Steward (coordinates the house team)
        ├── Team (Mercer, …)
        └── Alfred — Jason’s personal agent (Presence lane)
```

| Name | Role |
|------|------|
| **Stewart** | Steward of **this** Cove (Paperclip top seat). |
| **Alfred** | Operator’s personal agent — not above the house |
| **Hermes** | Runtime / engine only |
| **Cove last name** | Household surname for training (this lab: **Cove** → e.g. Stewart.Cove) |

**One Hermes per Cove.** Presences = Bot/profiles + isolated chats — not one Hermes container per person.  
**Haven** (agent above many Coves) = later — not Stewart’s job.

## Layout

| Path | Purpose |
|------|---------|
| `docker/` | Hermes Compose (P620) |
| `paperclip/` | Paperclip Compose beside Hermes |
| `pack/` | SOULs, skills, apply scripts |
| `vault/` | Shared markdown brain (Phase-1; no Nextcloud yet) |
| `team-page/` | Lucid Team UI — roster + tunings (port 3200) |
| `upstream/` | On host: Hermes git clone (not vendored in git) |

## Runbooks (AgentWorkspace)

| Runbook | Use |
|---------|-----|
| `runbooks/RB-hermes-paperclip-start-stop.md` | Daily start/stop/tunnels |
| `runbooks/RB-matrix-cove-users.md` | Dendrite users (`lucidcove-6f6f-dendrite`) |
| `runbooks/RB-paperclip-hermes-gateway-bootstrap.md` | Gateway hire / wizard bypass |

## License

Pack / Lucid materials: Lucid Principles licenses (protocol Apache-2.0; Canon CC BY 4.0). Hermes MIT (Nous). Paperclip per its license.
