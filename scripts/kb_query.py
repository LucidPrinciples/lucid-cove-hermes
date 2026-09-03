#!/usr/bin/env python3
"""Semantic search over vault/kb_index.sqlite (Lucid Principles KB).

Usage:
  .venv/bin/python scripts/kb_query.py "Love Equation coherence"
  .venv/bin/python scripts/kb_query.py -k 5 --json "Canon Protectorate"
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
from pathlib import Path

ROOT = Path(os.environ.get("LCH_ROOT", Path(__file__).resolve().parent.parent))
VAULT = Path(os.environ.get("LCH_VAULT", ROOT / "vault"))
sys.path.insert(0, str(ROOT))
import kb_retrieve  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Query Lucid Principles KB (vector)")
    ap.add_argument("query", nargs="+", help="search text")
    ap.add_argument("-k", type=int, default=5)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    q = " ".join(args.query)
    try:
        hits = kb_retrieve.search(q, k=args.k, vault=VAULT)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        print(f"ERROR: Ollama embed failed: {e}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps({"query": q, "hits": hits}, indent=2, ensure_ascii=False))
        return 0
    if not hits:
        print("No hits.")
        return 0
    for i, h in enumerate(hits, 1):
        print(f"--- {i}. {h['doc_name']} · {h['section']} (score={h['score']}) ---")
        print(h["text"][:1200])
        if len(h["text"]) > 1200:
            print("…")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
