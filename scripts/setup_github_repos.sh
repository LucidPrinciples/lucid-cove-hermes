#!/usr/bin/env bash
# Clone work remotes into Hermes write-safe data/repos.
# Two PATs (different orgs) — never mix with the house-backup token.
# PAT never goes in remotes or logs.
set -euo pipefail
set +x

ROOT="${LCH_ROOT:-/home/lphomebase/lucid-cove-hermes}"
DATA="${HERMES_DATA:-$ROOT/data}"
REPOS_DIR="${DATA}/repos"
PAT_OSS="${GITHUB_AGENT_PAT_FILE:-$HOME/.config/lucid-cove-hermes/github-agent.pat}"
PAT_OVERLAY="${GITHUB_OVERLAY_PAT_FILE:-$HOME/.config/lucid-cove-hermes/github-overlay.pat}"
STORE="${DATA}/.secrets/github-agent"
STORE_IN_CONTAINER="/opt/data/.secrets/github-agent"

REPOS=(
  "LucidPrinciples/lucid-cove"
  "LucidPrinciples/ltp-core"
  "LucidPrinciples/ltp-drop"
  "LucidTunerAI/lucid-cove-hermes"
)

log() { printf '%s %s\n' "$(date -Is)" "$*"; }
die() { log "ERROR: $*"; exit 1; }

read_pat() {
  local f="$1"
  [[ -f "$f" ]] || { printf ''; return 0; }
  tr -d '\n\r\t ' < "$f"
}

token_for() {
  local slug="$1"
  case "$slug" in
    LucidTunerAI/*) printf '%s' "$TOKEN_OVERLAY" ;;
    *) printf '%s' "$TOKEN_OSS" ;;
  esac
}

[[ -d "$DATA" ]] || die "Hermes data dir missing: $DATA"
command -v git >/dev/null || die "git not installed"

OWNER=$(stat -c '%u:%g' "$DATA" 2>/dev/null || stat -f '%u:%g' "$DATA")
mkdir -p "$REPOS_DIR" "$(dirname "$STORE")"
chmod 700 "$(dirname "$STORE")"

TOKEN_OSS=$(read_pat "$PAT_OSS")
TOKEN_OVERLAY=$(read_pat "$PAT_OVERLAY")

umask 077
: >"$STORE"
if [[ -n "$TOKEN_OSS" ]]; then
  printf 'https://x-access-token:%s@github.com/LucidPrinciples/lucid-cove.git\n' "$TOKEN_OSS" >>"$STORE"
  printf 'https://x-access-token:%s@github.com/LucidPrinciples/ltp-core.git\n' "$TOKEN_OSS" >>"$STORE"
  printf 'https://x-access-token:%s@github.com/LucidPrinciples/ltp-drop.git\n' "$TOKEN_OSS" >>"$STORE"
fi
if [[ -n "$TOKEN_OVERLAY" ]]; then
  printf 'https://x-access-token:%s@github.com/LucidTunerAI/lucid-cove-hermes.git\n' "$TOKEN_OVERLAY" >>"$STORE"
fi
chmod 600 "$STORE"
if [[ -s "$STORE" ]]; then
  log "credential store written (per-repo URLs, mode 600)"
else
  log "no PAT files yet — public clones only"
fi

configure_repo() {
  local dir="$1"
  git -C "$dir" config --local user.name "Lucid Cove Hermes"
  git -C "$dir" config --local user.email "hermes@users.noreply.github.com"
  git -C "$dir" config --local push.default current
  git -C "$dir" config --local credential.useHttpPath true
  git -C "$dir" remote set-url origin "https://github.com/${2}.git"
  if [[ -s "$STORE" ]]; then
    # Same .git/config on host and in Hermes; only one store file exists in each view.
    git -C "$dir" config --local --unset-all credential.helper >/dev/null 2>&1 || true
    git -C "$dir" config --local credential.helper '!f() { s=/opt/data/.secrets/github-agent; [ -f "$s" ] || s=/home/lphomebase/lucid-cove-hermes/data/.secrets/github-agent; git credential-store --file "$s" "$@"; }; f'
  fi
}

for slug in "${REPOS[@]}"; do
  name="${slug##*/}"
  dest="${REPOS_DIR}/${name}"
  url="https://github.com/${slug}.git"
  tok="$(token_for "$slug")"
  if [[ -d "${dest}/.git" ]]; then
    configure_repo "$dest" "$slug"
    log "fetch $slug"
    GIT_TERMINAL_PROMPT=0 git -C "$dest" fetch --prune origin || log "WARN: fetch failed $slug"
  else
    log "clone $slug"
    clone_from="$url"
    if [[ -n "$tok" ]]; then
      clone_from="https://x-access-token:${tok}@github.com/${slug}.git"
    fi
    if ! GIT_TERMINAL_PROMPT=0 git clone "$clone_from" "$dest"; then
      log "WARN: skip $slug (missing remote or no access yet)"
      rm -rf "$dest"
      continue
    fi
    git -C "$dest" remote set-url origin "$url"
    configure_repo "$dest" "$slug"
  fi
  log "ok $dest  $(git -C "$dest" rev-parse --abbrev-ref HEAD)@$(git -C "$dest" rev-parse --short HEAD)"
done

if [[ -d "${REPOS_DIR}/lucid-cove/.git" && -n "$TOKEN_OSS" ]]; then
  log "auth check (ls-remote lucid-cove)"
  GIT_TERMINAL_PROMPT=0 git -C "${REPOS_DIR}/lucid-cove" ls-remote --heads origin main >/dev/null
  log "auth check oss ok"
fi
if [[ -d "${REPOS_DIR}/lucid-cove-hermes/.git" && -n "$TOKEN_OVERLAY" ]]; then
  log "auth check (ls-remote lucid-cove-hermes)"
  GIT_TERMINAL_PROMPT=0 git -C "${REPOS_DIR}/lucid-cove-hermes" ls-remote --heads origin main >/dev/null
  log "auth check overlay ok"
fi

chown -R "$OWNER" "$REPOS_DIR" "$(dirname "$STORE")" 2>/dev/null || true
chmod 700 "$(dirname "$STORE")"
[[ -f "$STORE" ]] && chmod 600 "$STORE"

log "done — in Hermes: /opt/data/repos/{lucid-cove,ltp-core,ltp-drop,lucid-cove-hermes}"
log "ship: branch → PR → human merge. Do not push main. Do not force-push."
