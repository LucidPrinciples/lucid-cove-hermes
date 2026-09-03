#!/usr/bin/env bash
# Sync curated Lucid Principles KB into vault/kb for Hermes agents to read.
# Source of truth: ltp-drop/kb-source (or LTP_KB_SOURCE override).
set -euo pipefail

SCRIPT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [[ -n "${LCH_ROOT:-}" ]]; then
  ROOT="$LCH_ROOT"
elif [[ -d /home/lphomebase/lucid-cove-hermes ]]; then
  ROOT=/home/lphomebase/lucid-cove-hermes
else
  ROOT="$SCRIPT_ROOT"
fi
VAULT="${LCH_VAULT:-$ROOT/vault}"
DEST="$VAULT/kb"

DEFAULT_SRC=""
for cand in \
  "${LTP_KB_SOURCE:-}" \
  "$ROOT/../ltp-drop/kb-source" \
  "/Users/mymac/Documents/AgentWorkspace/projects/ltp-drop/kb-source" \
  "$ROOT/pack/kb-cache"
do
  if [[ -n "$cand" && -d "$cand" ]]; then
    DEFAULT_SRC="$cand"
    break
  fi
done

if [[ -z "$DEFAULT_SRC" ]]; then
  echo "ERROR: kb-source not found. Set LTP_KB_SOURCE or clone ltp-drop beside lucid-cove-hermes." >&2
  exit 1
fi

mkdir -p "$DEST/worldview"
FILES=(
  manifesto.md
  lucid-canon.md
  love-equation-cross-substrate.md
  ltp-protocol-spec.md
  digital-extension.md
  one-field-architecture.md
  sycophancy-nash-equilibrium.md
)

copied=0
for f in "${FILES[@]}"; do
  if [[ -f "$DEFAULT_SRC/$f" ]]; then
    cp -a "$DEFAULT_SRC/$f" "$DEST/$f"
    copied=$((copied + 1))
  else
    echo "warn: missing $f in $DEFAULT_SRC"
  fi
done

cp -a "$ROOT/pack/worldview/." "$DEST/worldview/"

cat >"$DEST/README.md" <<'EOF'
# Lucid Principles KB (curated)

On-disk reference for Lucid Cove on Hermes agents. **Not** auto-injected into the prompt — open files when needed (skill: `lp-worldview`).

Naming: never bare “Lucid” — say Lucid Principles / LP, Lucid Cove, or Lucid Tuner.

Synced from `ltp-drop/kb-source` via `scripts/sync_kb.sh`.
EOF

echo "synced $copied KB files → $DEST (from $DEFAULT_SRC)"
