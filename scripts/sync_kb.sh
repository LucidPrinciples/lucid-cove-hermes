#!/usr/bin/env bash
# Sync Lucid Principles KB into vault/kb for Hermes agents to read.
# Source of truth: full ltp-drop/kb-source (not a 7-file subset).
set -euo pipefail

SCRIPT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [[ -n "${LCH_ROOT:-}" ]]; then
  ROOT="$LCH_ROOT"
else
  ROOT="$SCRIPT_ROOT"
fi
VAULT="${LCH_VAULT:-$ROOT/vault}"
DEST="$VAULT/kb"

DEFAULT_SRC=""
for cand in \
  "${LTP_KB_SOURCE:-}" \
  "$ROOT/data/repos/ltp-drop/kb-source" \
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
  echo "ERROR: kb-source not found. Set LTP_KB_SOURCE or clone ltp-drop (house: data/repos/ltp-drop)." >&2
  exit 1
fi

mkdir -p "$DEST/worldview"
copied=0
shopt -s nullglob
for f in "$DEFAULT_SRC"/*.md; do
  base="$(basename "$f")"
  cp -a "$f" "$DEST/$base"
  copied=$((copied + 1))
done
shopt -u nullglob

cp -a "$ROOT/pack/worldview/." "$DEST/worldview/"

cat >"$DEST/README.md" <<EOF
# Lucid Principles KB

On-disk reference for Lucid Cove on Hermes. **Not** auto-injected — open files when needed (skill: \`lp-worldview\`).

Naming: never bare “Lucid” — Lucid Principles / LP, Lucid Cove, or Lucid Tuner.

Synced **all** \`*.md\` from \`${DEFAULT_SRC}\` via \`scripts/sync_kb.sh\` (${copied} files).
EOF

echo "synced $copied KB files → $DEST (from $DEFAULT_SRC)"
echo "KB files now: $(ls -1 "$DEST"/*.md 2>/dev/null | wc -l | tr -d ' ')"
if [[ "$copied" -lt 15 ]]; then
  echo "ERROR: expected full kb-source (>=15 md files), got $copied. Installer would miss Field Theory etc." >&2
  exit 1
fi
if [[ ! -f "$DEST/lucid-field-theory.md" ]]; then
  echo "ERROR: lucid-field-theory.md missing in vault/kb after sync." >&2
  exit 1
fi
