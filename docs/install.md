# Install Lucid Cove on Hermes

Computer-first. Phone-only cannot run Hermes + this overlay.

## 1. Hermes

Follow the official Nous installer and `hermes setup`. Bring your own model keys.

## 2. This overlay

```bash
git clone https://github.com/LucidPrinciples/lucid-cove-hermes.git
cd lucid-cove-hermes
```

Copy `team-page/.env.example` to `team-page/.env` and fill only what you use (Nextcloud Jules is optional).

From `team-page/`:

```bash
docker compose up -d --build
```

Open `http://127.0.0.1:3200/`.

Then, from the repo root (adjust if your Hermes home is not `./data`):

```bash
./scripts/sync_pack_to_hermes.sh
```

Start a new Hermes session so SOUL + skills load.

## 3. Lucid Tuner account

1. Sign in at https://app.lucidtuner.com
2. Settings → Get my connect key
3. Paste in **this** house Gear (Settings)

Same Lucid Tuner account, your house. Pro (unlimited Tune) is a separate Stripe door on the app — not required to connect.

## 4. Paperclip (optional)

If Paperclip is on loopback `:3100`, Attention can embed it. If not, Attention uses Hermes Kanban or an empty pane. Do not point a browser at `127.0.0.1` from a phone; the team page proxies Attention.

## Not in this repo

House-only ops (this operator's deploy host, backups, mesh hostnames) stay out of git. Do not copy another house's Caddy or compose secrets into yours.
