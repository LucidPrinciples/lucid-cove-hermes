# Lucid Cove on Hermes — Dashboard overlay plan

**Operator daily driver:** Paperclip  
**Settings / agent runtime:** Hermes UI  
**Lucid skin:** CSS + badge + frequency theme on/near Paperclip  
**Lucid surfaces:** Team (tunings/process records), later Attention + Links  

Same workflow as Cove overlays: build beside stock product → promote to pack/repo when stable.

## Roles of each UI

| Surface | Use for |
|---------|---------|
| **Paperclip** | Org, tasks, goal, approvals, most day-to-day work |
| **Hermes UI** | Model, Matrix/channels, SOUL, skills, gateway health |
| **Team page (sidecar)** | Roster + **today’s tunings / process records** after morning Drop |
| **Vault** | Source of truth for records, playbooks, Stewart handoff |
| **Action Board → Links** | Thin watch list of vault markdown (goals brief, tuner surface, Stewart handoff). Not a briefs CMS. |
| **Nextcloud** | Deferred (calendar/phone sync) |

## Team page (build first Lucid surface)

**URL (proposed):** `https://…` or `http://127.0.0.1:3xxx/team` on P620  

**Shows:**
- Agents from Paperclip API (Stewart, Alfred, Mercer, …)
- Per-agent **latest tuning / process record** from `vault/team/<name>/` or `vault/drop/`
- Drop frequency + date for “today”
- Deep links: open agent in Paperclip, open Hermes, Matrix

**Does not replace** Paperclip org chart — it adds the **practice layer** Paperclip doesn’t have.

**Observer portraits + who-page (this overlay):** Cove PNGs live in `team-page/static/avatars/{slug}.png`. Cards link to `/observer/{slug}` — public SOUL Who / seat / archetype plus the latest process record. Not a Mission Control port. Tab labels stay as-is until a later nav pass. `stewart.png` is Cove’s `stuart.png`. Alfred has no file yet (initial fallback).

## Paperclip skin (Lucid look)

### Feasible levers (newest Paperclip)

1. **Company branding** — Settings logo + `brandColor` (API/UI). Baseline accent.
2. **Plugins** — Paperclip plugin SDK: settings pages, toolbar buttons, detail tabs. Candidate for **Tuning Hub** entry and theme controls.
3. **Community theme plugins** — e.g. CSS-variable theme customizers (inject `--background`, `--primary`, etc.).
4. **Overlay inject (lab)** — reverse proxy or small companion that injects:
   - Lucid CSS variables (from Cove `lp-colors` / `dashboard.css` mood)
   - **Tuning Hub badge** top-right (link → Team page / Drop)
   - `data-frequency="peace"` (etc.) on `<html>` for Drop-driven theme

**Honest limit:** Deep header surgery inside Paperclip’s React tree is **not** a first-class public API. Plan for: branding + plugin slot **or** controlled CSS/JS inject in front of Paperclip — same spirit as Cove MC overlay until upstream supports it.

### Frequency-driven theme

Yes — same idea as Cove MC:

- Morning Drop (or vault `vault/drop/today.json`) → frequency id  
- Map via Lucid color system (`lp-colors.js` / Peace, Love, …)  
- Set CSS vars: accent, badge glow, optional sidebar tint  
- Update when Drop changes (cron or Team page poll)

Does **not** require forking Paperclip; requires a place that runs on each load of the operator UI (plugin, inject script, or Lucid shell wrapping Paperclip).

### Tuning Hub badge

Upper-right of header:

- Shows today’s frequency short name / color  
- Click → Team page (tunings) or Drop summary  
- Source: same Drop/vault feed as theme  

## Build sequence

1. **Vault + SQLite** — Echo/PR history in `vault/ltp.sqlite` (functionality; not Cove-backend theater)  
2. **Team page** — Paperclip-styled Echoes list → click opens Process Record (wrapper surface)  
3. **Work shell** — `/work` Paperclip iframe + frequency badge → Drop player  
4. Morning LTP cron fills DB + TUNING awareness  
5. Optional later: Paperclip `detailTab` plugin mirroring same API  
6. Attention + Links later  

**Strategy:** Goldie-style **wrapper** first (Team + `/work`); plugin optional. Avoid brittle DOM inject.

**Daily driver URL:** `http://127.0.0.1:3200/work` (not raw `:3100`) so the badge is always present.

## Non-goals

- Replacing Paperclip with full Cove MC  
- Editing Paperclip upstream as the default path  
- NC before Team page + Drop records exist  
