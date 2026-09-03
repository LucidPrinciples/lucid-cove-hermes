#!/usr/bin/env bash
# Lucid Cove on Hermes — private house backup → GitHub.
# Spec: vault/playbooks/backup-intent.md
# PAT is never written into the snapshot or the git remote URL on disk.
set -euo pipefail
# Never print commands (would leak the push URL).
set +x

DRY_RUN=0
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
fi

ROOT="${LCH_ROOT:-/home/lphomebase/lucid-cove-hermes}"
DATA="${HERMES_DATA:-$ROOT/data}"
STAGING="${BACKUP_STAGING:-$ROOT/backup-staging}"
PAT_FILE="${BACKUP_PAT_FILE:-$HOME/.config/lucid-cove-hermes/github-backup.pat}"
REMOTE="${BACKUP_REMOTE:-https://github.com/LucidTunerAI/LucidCoveHermes-Backups.git}"
# Strip .git for building the authenticated URL; keep REMOTE as the clean origin.
REMOTE_CLEAN="${REMOTE%.git}.git"
LOG_DIR="$ROOT/vault/drop"
LOG="$LOG_DIR/house_backup.log"
MAX_BYTES=$((90 * 1024 * 1024))

mkdir -p "$LOG_DIR"

log() { printf '%s %s\n' "$(date -Is)" "$*" | tee -a "$LOG"; }

die() { log "ERROR: $*"; exit 1; }

# rsync excludes applied to every copy into staging
RSYNC_EX=(
  --exclude '.git'
  --exclude '.env'
  --exclude '.env.*'
  --exclude '*.pat'
  --exclude '*.pem'
  --exclude '*.key'
  --exclude 'id_rsa'
  --exclude 'id_ed25519'
  --exclude 'credentials.json'
  --exclude 'secrets.json'
  --exclude '.venv'
  --exclude '__pycache__'
  --exclude '*.pyc'
  --exclude '.DS_Store'
  --exclude 'backup-staging'
  --exclude 'upstream'
  --exclude 'repos'
  --exclude '.secrets'
  --exclude '.git-credentials'
  --exclude 'node_modules'
  --max-size=90m
)

sync_dir() {
  local src="$1" dest="$2"
  if [[ -d "$src" ]]; then
    mkdir -p "$dest"
    rsync -a --delete "${RSYNC_EX[@]}" "$src/" "$dest/"
    log "sync dir  $src -> $dest"
  else
    log "skip missing dir $src"
  fi
}

sync_file() {
  local src="$1" dest="$2"
  if [[ -f "$src" ]]; then
    mkdir -p "$(dirname "$dest")"
    rsync -a "${RSYNC_EX[@]}" "$src" "$dest"
    log "sync file $src"
  fi
}

redact_yaml() {
  local f="$1"
  [[ -f "$f" ]] || return 0
  python3 - "$f" <<'PY'
import re, sys
from pathlib import Path
p = Path(sys.argv[1])
text = p.read_text(encoding="utf-8", errors="replace")
key_re = re.compile(
    r"^(\s*)([A-Za-z0-9_.\-]*(?:token|secret|password|api_key|apikey|pat|authorization|private_key)[A-Za-z0-9_.\-]*)(\s*:\s*)(\S.*)$",
    re.I,
)
out = []
for line in text.splitlines():
    m = key_re.match(line)
    if m and m.group(4).strip() not in ("", "|", ">", "{}", "[]", "__REDACTED__"):
        out.append(f"{m.group(1)}{m.group(2)}{m.group(3)}__REDACTED__")
    else:
        out.append(line)
p.write_text("\n".join(out) + ("\n" if text.endswith("\n") else ""), encoding="utf-8")
PY
  log "redacted $f"
}

read_pat() {
  [[ -f "$PAT_FILE" ]] || die "PAT file missing: $PAT_FILE"
  local mode
  mode=$(stat -c '%a' "$PAT_FILE" 2>/dev/null || stat -f '%OLp' "$PAT_FILE")
  if [[ "$mode" != "600" && "$mode" != "400" ]]; then
    chmod 600 "$PAT_FILE" || true
  fi
  TOKEN=$(tr -d '\n\r\t ' < "$PAT_FILE")
  [[ -n "$TOKEN" ]] || die "PAT file is empty"
}

auth_url() {
  # Fine-grained PAT over HTTPS. Never echo this.
  printf 'https://x-access-token:%s@github.com/LucidTunerAI/LucidCoveHermes-Backups.git' "$TOKEN"
}

ensure_staging_git() {
  if [[ -d "$STAGING/.git" ]]; then
    git -C "$STAGING" remote set-url origin "$REMOTE_CLEAN"
    return 0
  fi
  if [[ -d "$STAGING" && -n "$(ls -A "$STAGING" 2>/dev/null || true)" ]]; then
    mv "$STAGING" "${STAGING}.pregit.$(date +%s)"
  fi
  mkdir -p "$(dirname "$STAGING")"
  log "cloning backup remote into staging (empty repo is OK)"
  GIT_TERMINAL_PROMPT=0 git clone "$(auth_url)" "$STAGING"
  git -C "$STAGING" remote set-url origin "$REMOTE_CLEAN"
}

write_meta() {
  cat >"$STAGING/.gitignore" <<'EOF'
.env
.env.*
*.pat
*.pem
*.key
id_rsa
id_ed25519
credentials.json
secrets.json
.venv/
__pycache__/
*.pyc
.DS_Store
EOF

  cat >"$STAGING/README.md" <<EOF
# Lucid Cove on Hermes — house backup

Private snapshot of the P620 house. **Not** the product repo.

- Intent: \`vault/playbooks/backup-intent.md\` (inside this snapshot)
- Last run: $(date -Is)
- Host tree: \`/home/lphomebase/lucid-cove-hermes\`
- Restore: rsync \`vault/\` and selected \`data/\` back onto the host; recreate \`.env\` files from a password manager (they are never stored here).
EOF
}

skip_oversize() {
  local n=0
  while IFS= read -r -d '' f; do
    rm -f "$f"
    log "dropped oversized $(realpath --relative-to="$STAGING" "$f" 2>/dev/null || echo "$f")"
    n=$((n + 1))
  done < <(find "$STAGING" -type f -size +90M -print0 2>/dev/null || true)
  if [[ "$n" -gt 0 ]]; then
    log "dropped $n file(s) over 90MB"
  fi
}

snapshot() {
  log "snapshot start root=$ROOT dry_run=$DRY_RUN"

  sync_dir "$ROOT/vault" "$STAGING/vault"
  sync_dir "$DATA/memories" "$STAGING/data/memories"
  sync_dir "$DATA/souls" "$STAGING/data/souls"
  sync_dir "$DATA/skills" "$STAGING/data/skills"
  sync_dir "$DATA/worldview" "$STAGING/data/worldview"

  # Session-like dirs Hermes may create — copy whatever exists.
  local d
  for d in sessions session_logs logs chats transcripts conversation_history; do
    sync_dir "$DATA/$d" "$STAGING/data/$d"
  done
  # Extra session dirs one level down (best-effort, no delete of siblings).
  if [[ -d "$DATA" ]]; then
    while IFS= read -r -d '' sdir; do
      local rel="${sdir#"$DATA"/}"
      case "$rel" in
        memories|souls|skills|worldview|sessions|session_logs|logs|chats|transcripts|conversation_history) continue ;;
      esac
      sync_dir "$sdir" "$STAGING/data/$rel"
    done < <(find "$DATA" -maxdepth 2 -type d \( -iname '*session*' -o -iname '*transcript*' -o -iname '*chatlog*' \) -print0 2>/dev/null || true)
  fi

  sync_file "$DATA/SOUL.md" "$STAGING/data/SOUL.md"
  sync_file "$DATA/USER.md" "$STAGING/data/USER.md"
  sync_file "$DATA/HEARTBEAT.md" "$STAGING/data/HEARTBEAT.md"
  sync_file "$DATA/config.yaml" "$STAGING/data/config.yaml"
  sync_file "$ROOT/HERMES.md" "$STAGING/HERMES.md"
  sync_file "$ROOT/.hermes.md" "$STAGING/.hermes.md"

  redact_yaml "$STAGING/data/config.yaml"

  sync_dir "$ROOT/pack" "$STAGING/pack"
  sync_dir "$ROOT/scripts" "$STAGING/scripts"
  sync_dir "$ROOT/docs" "$STAGING/docs"
  sync_dir "$ROOT/caddy" "$STAGING/caddy"
  sync_file "$ROOT/docker/docker-compose.yml" "$STAGING/docker/docker-compose.yml"
  sync_file "$ROOT/paperclip/docker-compose.yml" "$STAGING/paperclip/docker-compose.yml"
  sync_dir "$ROOT/paperclip/data" "$STAGING/paperclip/data"
  sync_dir "$ROOT/team-page" "$STAGING/team-page"

  write_meta
  skip_oversize
}

commit_push() {
  git -C "$STAGING" config user.email "backup@lucidcove.internal"
  git -C "$STAGING" config user.name "Lucid Cove Hermes Backup"
  git -C "$STAGING" remote set-url origin "$REMOTE_CLEAN"

  git -C "$STAGING" add -A

  if git -C "$STAGING" diff --cached --quiet; then
    log "no new files to commit"
  else
    git -C "$STAGING" diff --cached --stat | tee -a "$LOG"
    local msg="house backup $(date '+%Y-%m-%d %H:%M:%S %Z')"
    git -C "$STAGING" commit -m "$msg"
    log "committed: $msg"
  fi

  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "dry-run — not pushing"
    return 0
  fi

  if ! git -C "$STAGING" rev-parse --verify HEAD >/dev/null 2>&1; then
    log "no commits — nothing to push"
    return 0
  fi

  log "pushing to origin main"
  GIT_TERMINAL_PROMPT=0 git -C "$STAGING" push --porcelain "$(auth_url)" HEAD:main
  git -C "$STAGING" remote set-url origin "$REMOTE_CLEAN"
  git -C "$STAGING" branch --set-upstream-to=origin/main >/dev/null 2>&1 || true
  log "push ok"
}

main() {
  [[ -d "$ROOT" ]] || die "ROOT missing: $ROOT"
  command -v git >/dev/null || die "git not installed"
  command -v rsync >/dev/null || die "rsync not installed"
  read_pat
  ensure_staging_git
  snapshot
  commit_push
  log "done"
}

main
