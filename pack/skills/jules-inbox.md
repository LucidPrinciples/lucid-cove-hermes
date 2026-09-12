# Skill — Jules inbox (two lanes)

Jules is a **tool** (operator voice capture), not an agent. Notes land in Cove Inbox via the Jules PWA.

## Dest chips (already in Cove Jules)

| Chip | Meaning for Lucid Cove on Hermes |
|------|----------------------------------|
| **→ Backlog (auto)** | Ticket lane — Stewart may create a Paperclip Issue |
| **→ Hold in Inbox** | **Discuss first** — do **not** auto-ticket; wait for Jason in chat |
| **→ for-{agent}** | Route to that agent’s attention; still not silent auto unless board said so |

## Stewart behavior

1. When Jason says a Jules note is ready (or you see a new hold/for-Stewart item), read it.  
2. **Hold / discuss:** summarize in chat; ask what he wants; only file a Paperclip Issue if he says so.  
3. **Backlog / explicit ticket:** propose or create the Issue; cite the Jules filename as evidence.  
4. Never invent Jules content — quote the transcript.

## Where to open Jules

Phone Jules is this house's `/jules` PWA (Add to Home Screen). Not in top nav.
Desktop: Action → Tools. Live API: `http://127.0.0.1:3200` only (not :13200).

## Inbox API

- List: `GET http://127.0.0.1:3200/api/jules/inbox`
- File: `GET http://127.0.0.1:3200/api/jules/inbox/<relative-path>` (nested paths as listed)
- **Hold** = discuss in chat; never auto-ticket Hold.
- Text (`.md`, `.js`, …): JSON `{ok, filename, path, text}`
- **Images** (`.png` `.jpg` `.webp` `.heic` …): raw `image/*` bytes so Stewart can `vision_analyze`. `?format=json` keeps the old stub.
- Audio / other binaries: JSON stub (`binary: true`). Use the Jules UI for playback.

## Dev screenshots (either path)

- **A few:** drop PNGs in this chat.
- **A bunch:** drop them in the Jules Inbox folder (phone Jules or NC Inbox). After Jason deploys the image GET, Stewart reads pixels from the Inbox API — do not hunt disk/SSH/WebDAV/.env.

Another Cove's Jules path is a different Inbox.
