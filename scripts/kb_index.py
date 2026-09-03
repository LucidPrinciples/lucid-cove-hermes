#!/usr/bin/env python3
"""Index vault/kb markdown into vault/kb_index.sqlite (Ollama nomic-embed-text).

Cove-like behavior without Postgres: chunk by ## headers, embed locally, store vectors.
Re-run after KB sync. Safe to re-run (replaces index).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import struct
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(os.environ.get("LCH_ROOT", Path(__file__).resolve().parent.parent))
VAULT = Path(os.environ.get("LCH_VAULT", ROOT / "vault"))
KB_DIR = VAULT / "kb"
INDEX_PATH = VAULT / "kb_index.sqlite"
OLLAMA = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
EMBED_MODEL = os.environ.get("LTP_EMBED_MODEL", "nomic-embed-text")
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
DIM = 768


def chunk_document(text: str, doc_name: str) -> list[dict]:
    chunks: list[dict] = []
    sections = re.split(r"(?=^## )", text, flags=re.MULTILINE)
    for section in sections:
        section = section.strip()
        if not section:
            continue
        header_match = re.match(r"^##\s+(.+?)$", section, re.MULTILINE)
        header = header_match.group(1).strip() if header_match else "Introduction"
        if len(section) <= CHUNK_SIZE:
            chunks.append({"text": section, "section": header, "doc_name": doc_name})
            continue
        paragraphs = section.split("\n\n")
        current = ""
        for para in paragraphs:
            if len(current) + len(para) > CHUNK_SIZE and current:
                chunks.append({"text": current.strip(), "section": header, "doc_name": doc_name})
                current = current[-CHUNK_OVERLAP:] + "\n\n" + para
            else:
                current = current + ("\n\n" + para if current else para)
        if current.strip():
            chunks.append({"text": current.strip(), "section": header, "doc_name": doc_name})
    return chunks


def embed(text: str) -> list[float]:
    payload = json.dumps({"model": EMBED_MODEL, "prompt": text}).encode()
    req = urllib.request.Request(
        f"{OLLAMA}/api/embeddings",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode())
    vec = data.get("embedding")
    if not isinstance(vec, list) or not vec:
        raise RuntimeError(f"empty embedding from {EMBED_MODEL}")
    return [float(x) for x in vec]


def pack_vec(vec: list[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


def main() -> int:
    ap = argparse.ArgumentParser(description="Index Lucid Principles KB for semantic search")
    ap.add_argument("--kb", type=Path, default=KB_DIR)
    ap.add_argument("--index", type=Path, default=INDEX_PATH)
    args = ap.parse_args()

    if not args.kb.is_dir():
        print(f"ERROR: KB dir missing: {args.kb}", file=sys.stderr)
        return 1

    # Probe embed model
    try:
        embed("ping")
    except urllib.error.URLError as e:
        print(f"ERROR: Ollama unreachable at {OLLAMA}: {e}", file=sys.stderr)
        print(f"  Hint: ollama pull {EMBED_MODEL}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: embed failed ({e}). Try: ollama pull {EMBED_MODEL}", file=sys.stderr)
        return 1

    docs = sorted(p for p in args.kb.glob("*.md") if p.name != "README.md")
    if not docs:
        print(f"ERROR: no .md files in {args.kb}", file=sys.stderr)
        return 1

    args.index.parent.mkdir(parents=True, exist_ok=True)
    if args.index.exists():
        args.index.unlink()

    conn = sqlite3.connect(str(args.index))
    conn.execute(
        """
        CREATE TABLE chunks (
          id INTEGER PRIMARY KEY,
          doc_name TEXT NOT NULL,
          section TEXT,
          chunk_index INTEGER,
          text TEXT NOT NULL,
          content_hash TEXT,
          dim INTEGER,
          embedding BLOB NOT NULL
        )
        """
    )
    conn.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
    conn.execute(
        "INSERT INTO meta(key,value) VALUES ('embed_model', ?), ('ollama', ?)",
        (EMBED_MODEL, OLLAMA),
    )

    total = 0
    for path in docs:
        text = path.read_text(encoding="utf-8", errors="ignore")
        pieces = chunk_document(text, path.name)
        print(f"  {path.name}: {len(pieces)} chunk(s)", flush=True)
        for i, ch in enumerate(pieces):
            vec = embed(ch["text"])
            h = hashlib.sha256(ch["text"].encode()).hexdigest()[:16]
            conn.execute(
                """
                INSERT INTO chunks(doc_name, section, chunk_index, text, content_hash, dim, embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (ch["doc_name"], ch["section"], i, ch["text"], h, len(vec), pack_vec(vec)),
            )
            total += 1

    conn.commit()
    conn.close()
    print(f"indexed {total} chunks → {args.index} (model={EMBED_MODEL})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
