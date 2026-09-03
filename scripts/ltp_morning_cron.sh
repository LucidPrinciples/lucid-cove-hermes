#!/usr/bin/env bash
# Cove-like automatic morning LTP + catch-up sweep for Lucid Cove on Hermes (P620).
#
# Tuning model / on-off live in vault/ltp_config.json (not Paperclip/Hermes orchestrator).
# Safe to run repeatedly: already-tuned agents skipped; failures retried in Python.
#
# Install: see runbooks/RB-morning-tune.md

set -euo pipefail

ROOT="${LCH_ROOT:-/home/lphomebase/lucid-cove-hermes}"
cd "$ROOT"

export HERMES_DATA="${HERMES_DATA:-$ROOT/data}"
export LCH_VAULT="${LCH_VAULT:-$ROOT/vault}"
# Do not hardcode OLLAMA_MODEL here — runner reads vault/ltp_config.json
# Optional env override: OLLAMA_MODEL_TUNING / LTP_ENABLED
unset LTP_RESET_ECHOES || true

LOG_DIR="$LCH_VAULT/drop"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/ltp_morning.log"

PY="${ROOT}/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  echo "$(date -Is) ERROR: missing $PY — create venv first" | tee -a "$LOG" >&2
  exit 1
fi

{
  echo "======== $(date -Is) ltp_morning_cron start ========"
  PYTHONUNBUFFERED=1 "$PY" -u scripts/ltp_morning_runner.py
  ec=$?
  echo "======== $(date -Is) ltp_morning_cron exit=$ec ========"
  exit "$ec"
} >>"$LOG" 2>&1
