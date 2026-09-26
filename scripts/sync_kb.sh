#!/usr/bin/env bash
# Sync Lucid Principles KB into vault/kb for Hermes agents to read.
# Prefer a local ltp-drop/kb-source tree when present. Otherwise pull the
# signed KB from https://drop.lucidprinciples.com/kb/ the same way Coves
# kb_sync does (Ed25519 manifest + per-file sha256, fail closed).
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
  "$ROOT/../ltp-drop/kb-source"
do
  if [[ -n "$cand" && -d "$cand" ]]; then
    DEFAULT_SRC="$cand"
    break
  fi
done

mkdir -p "$DEST/worldview"
copied=0

copy_local() {
  local src="$1"
  shopt -s nullglob
  for f in "$src"/*.md; do
    cp -a "$f" "$DEST/$(basename "$f")"
    copied=$((copied + 1))
  done
  shopt -u nullglob
}

pull_signed() {
  # Cove-equivalent: GET manifest, verify Ed25519, GET each file, verify sha256.
  python3 - "$DEST" <<'PY'
from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import urllib.parse
from pathlib import Path

dest = Path(sys.argv[1])
manifest_url = os.environ.get(
    "LP_KB_MANIFEST_URL", "https://drop.lucidprinciples.com/kb/manifest.json"
).strip()
public_key = os.environ.get(
    "LP_KB_PUBLIC_KEY",
    "MCowBQYDK2VwAyEAMtpeQ7Gae3YUwzUVjh2fyToF/oGi2OBWUWipXia0BeM=",
).strip()
ua = os.environ.get("LP_KB_USER_AGENT", "LucidCove-Cove/1.0")

if not manifest_url.startswith("https://"):
    print("ERROR: LP_KB_MANIFEST_URL must be https", file=sys.stderr)
    sys.exit(1)
if not public_key:
    print("ERROR: LP_KB_PUBLIC_KEY not set — refusing to sync unverified KB.", file=sys.stderr)
    sys.exit(1)


def fetch(url: str) -> bytes:
    # Cove kb_sync uses httpx; Drop's edge 403s a bare Python User-Agent.
    r = subprocess.run(
        ["curl", "-fsSL", "-A", ua, "--max-time", "30", url],
        capture_output=True,
    )
    if r.returncode != 0:
        err = (r.stderr or r.stdout or b"").decode("utf-8", "replace").strip()
        raise SystemExit(f"ERROR: fetch failed ({r.returncode}): {url} {err}")
    return r.stdout


def canonical_json(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def verify_manifest(manifest: dict) -> None:
    sig_b64 = manifest.get("signature")
    if not sig_b64:
        raise SystemExit("ERROR: Manifest has no signature — refusing.")
    pem = public_key.replace("\\n", "\n").strip()
    if "BEGIN PUBLIC KEY" not in pem:
        pem = "-----BEGIN PUBLIC KEY-----\n" + pem + "\n-----END PUBLIC KEY-----\n"
    unsigned = {k: v for k, v in manifest.items() if k != "signature"}
    payload = canonical_json(unsigned)
    try:
        sig = base64.b64decode(sig_b64)
    except Exception as e:
        raise SystemExit(f"ERROR: Manifest signature invalid: {e}") from e
    with tempfile.TemporaryDirectory() as td:
        pub = Path(td) / "pub.pem"
        pay = Path(td) / "payload.bin"
        sigf = Path(td) / "sig.bin"
        pub.write_text(pem, encoding="utf-8")
        pay.write_bytes(payload)
        sigf.write_bytes(sig)
        r = subprocess.run(
            [
                "openssl",
                "pkeyutl",
                "-verify",
                "-pubin",
                "-inkey",
                str(pub),
                "-rawin",
                "-in",
                str(pay),
                "-sigfile",
                str(sigf),
            ],
            capture_output=True,
            text=True,
        )
    if r.returncode != 0:
        err = (r.stderr or r.stdout or "openssl verify failed").strip()
        raise SystemExit(f"ERROR: Signature verification FAILED: {err}")


raw = fetch(manifest_url)
try:
    manifest = json.loads(raw.decode("utf-8"))
except json.JSONDecodeError as e:
    raise SystemExit(f"ERROR: manifest is not JSON: {e}") from e
if not isinstance(manifest, dict):
    raise SystemExit("ERROR: manifest is not an object")
verify_manifest(manifest)

base = manifest_url.rsplit("/", 1)[0]
files = manifest.get("files") or []
written = 0
for item in files:
    if not isinstance(item, dict):
        raise SystemExit("ERROR: manifest file entry is not an object")
    rel = (item.get("path") or "").lstrip("/")
    want = item.get("sha256") or ""
    if not rel:
        continue
    if ".." in Path(rel).parts or rel.startswith("/") or "\\" in rel:
        raise SystemExit(f"ERROR: refusing path {rel!r}")
    if not want:
        raise SystemExit(f"ERROR: {rel}: missing sha256 — refusing.")
    body = fetch(f"{base}/files/{urllib.parse.quote(rel, safe='/')}")
    if hashlib.sha256(body).hexdigest() != want:
        raise SystemExit(f"ERROR: {rel}: hash mismatch — skipped nothing, refusing.")
    out = dest / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(body)
    written += 1

if written < 15:
    raise SystemExit(f"ERROR: expected full signed KB (>=15 files), got {written}.")
print(f"SIGNED_COPIED={written}")
PY
}

if [[ -n "$DEFAULT_SRC" ]]; then
  copy_local "$DEFAULT_SRC"
  echo "synced $copied KB files → $DEST (from $DEFAULT_SRC)"
else
  echo "no local ltp-drop/kb-source; pulling signed KB from ${LP_KB_MANIFEST_URL:-https://drop.lucidprinciples.com/kb/manifest.json}"
  signed_out="$(pull_signed)"
  copied="${signed_out##*SIGNED_COPIED=}"
  copied="${copied%%$'\n'*}"
  echo "synced $copied KB files → $DEST (signed Drop KB)"
fi

cp -a "$ROOT/pack/worldview/." "$DEST/worldview/"

cat >"$DEST/README.md" <<EOF
# Lucid Principles KB

On-disk reference for Lucid Cove on Hermes. **Not** auto-injected — open files when needed (skill: \`lp-worldview\`).

Naming: never bare “Lucid” — Lucid Principles / LP, Lucid Cove, or Lucid Tuner.

Synced **all** \`*.md\` via \`scripts/sync_kb.sh\` (${copied} files). Local \`ltp-drop/kb-source\` wins when present; otherwise the signed KB at https://drop.lucidprinciples.com/kb/.
EOF

echo "KB files now: $(ls -1 "$DEST"/*.md 2>/dev/null | wc -l | tr -d ' ')"
if [[ "$copied" -lt 15 ]]; then
  echo "ERROR: expected full kb-source (>=15 md files), got $copied." >&2
  exit 1
fi
if [[ ! -f "$DEST/lucid-field-theory.md" ]]; then
  echo "ERROR: lucid-field-theory.md missing in vault/kb after sync." >&2
  exit 1
fi
