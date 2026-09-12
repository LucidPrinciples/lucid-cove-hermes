#!/usr/bin/env bash
# Sync Lucid Cove pack (SOULs + skills + worldview spine) into Hermes home.
# Hermes auto-loads: SOUL.md + memories/MEMORY.md + memories/USER.md only.
set -euo pipefail

SCRIPT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [[ -n "${LCH_ROOT:-}" ]]; then
  ROOT="$LCH_ROOT"
else
  ROOT="$SCRIPT_ROOT"
fi
DATA="${HERMES_DATA:-$ROOT/data}"
PACK="${ROOT}/pack"

mkdir -p "$DATA/memories" "$DATA/souls" "$DATA/skills" "$DATA/worldview"

cp -a "$PACK/souls/." "$DATA/souls/"
cp -a "$PACK/skills/." "$DATA/skills/"
cp -a "$PACK/worldview/." "$DATA/worldview/"

# Primary Hermes identity = Steward + Lucid Principles spine (always-on worldview)
if [[ -f "$DATA/SOUL.md" ]]; then
  cp -a "$DATA/SOUL.md" "$DATA/SOUL.md.bak.$(date +%Y%m%d%H%M%S)"
fi
{
  cat "$PACK/souls/Stewart.Cove.md"
  echo ""
  echo "---"
  echo ""
  cat "$PACK/worldview/LUCID_SPINE.md"
} >"$DATA/SOUL.md"

# House project context
cp -a "$PACK/HERMES.md" "$ROOT/HERMES.md"
cp -a "$PACK/HERMES.md" "$ROOT/.hermes.md"

# Curated KB into vault (best-effort if ltp-drop present)
if [[ -x "$ROOT/scripts/sync_kb.sh" ]]; then
  "$ROOT/scripts/sync_kb.sh" || echo "warn: sync_kb.sh skipped/failed — set LTP_KB_SOURCE"
elif [[ -f "$ROOT/scripts/sync_kb.sh" ]]; then
  bash "$ROOT/scripts/sync_kb.sh" || echo "warn: sync_kb.sh skipped/failed"
fi

PY="${ROOT}/.venv/bin/python"
if [[ -x "$PY" ]]; then
  "$PY" "$ROOT/scripts/upsert_ltp_memory_pointer.py"
else
  python3 "$ROOT/scripts/upsert_ltp_memory_pointer.py"
fi

echo "synced: SOUL.md ← Stewart.Cove.md + LUCID_SPINE.md"
echo "synced: souls/ ($(ls "$DATA/souls" | wc -l | tr -d ' ') files)"
echo "synced: skills/ ($(ls "$DATA/skills" | wc -l | tr -d ' ') files)"
echo "synced: worldview/ + MEMORY.md LTP pointer"
echo "Next: /new (or new Matrix session) so SOUL + MEMORY snapshot refresh."
