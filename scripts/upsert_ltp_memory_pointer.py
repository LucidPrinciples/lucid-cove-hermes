#!/usr/bin/env python3
"""Upsert a short LTP pointer into Hermes memories/MEMORY.md (≤2200 char store).

Hermes only auto-injects MEMORY.md + USER.md — not TUNING_*.md.
Keep this pointer tiny; full Process Records stay in the vault.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

ROOT = Path(os.environ.get("LCH_ROOT", Path(__file__).resolve().parent.parent))
HERMES_DATA = Path(os.environ.get("HERMES_DATA", ROOT / "data"))
MEM = HERMES_DATA / "memories" / "MEMORY.md"
CHAR_LIMIT = int(os.environ.get("HERMES_MEMORY_CHAR_LIMIT", "2200"))

MARKER = "LTP morning tune"
POINTER = (
    "LTP morning tune: read memories/TUNING_ACTIVE.md (and TUNING_<NAME>.md) for "
    "today's frequency/principle/love equation — fades ~3 days. Full Process "
    "Records live in vault/team/<slug>/ (durable). Do not paste full records here."
)


def main() -> int:
    MEM.parent.mkdir(parents=True, exist_ok=True)
    text = MEM.read_text(encoding="utf-8") if MEM.is_file() else ""
    parts = [p.strip() for p in re.split(r"\s*§\s*", text) if p.strip()]
    parts = [p for p in parts if not p.startswith(MARKER)]
    parts.insert(0, POINTER)
    out = "\n§\n".join(parts).strip() + "\n"
    if len(out) > CHAR_LIMIT:
        # Drop oldest non-pointer entries until under limit
        while len(out) > CHAR_LIMIT and len(parts) > 1:
            parts.pop()
            out = "\n§\n".join(parts).strip() + "\n"
        if len(out) > CHAR_LIMIT:
            out = POINTER[: CHAR_LIMIT - 1] + "\n"
    MEM.write_text(out, encoding="utf-8")
    print(f"MEMORY.md pointer ok ({len(out)}/{CHAR_LIMIT} chars) → {MEM}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
