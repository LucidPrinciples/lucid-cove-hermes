"""Shared Lucid Principles KB vector retrieve (SQLite + Ollama embeddings)."""
from __future__ import annotations

import json
import math
import os
import sqlite3
import struct
import urllib.request
from pathlib import Path

DEFAULT_VAULT = Path(__file__).resolve().parent / "vault"


def _index_path(vault: Path | None = None) -> Path:
    root = Path(vault or os.environ.get("LCH_VAULT", DEFAULT_VAULT))
    return root / "kb_index.sqlite"


def embed(text: str, *, model: str | None = None, ollama: str | None = None) -> list[float]:
    model = model or os.environ.get("LTP_EMBED_MODEL", "nomic-embed-text")
    ollama = (ollama or os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")).rstrip("/")
    payload = json.dumps({"model": model, "prompt": text}).encode()
    req = urllib.request.Request(
        f"{ollama}/api/embeddings",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode())
    return [float(x) for x in data["embedding"]]


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1e-9
    nb = math.sqrt(sum(y * y for y in b)) or 1e-9
    return dot / (na * nb)


def search(query: str, *, k: int = 5, vault: Path | None = None) -> list[dict]:
    index = _index_path(vault)
    if not index.is_file():
        raise FileNotFoundError(f"missing {index} — run scripts/kb_index.py")
    conn = sqlite3.connect(str(index))
    conn.row_factory = sqlite3.Row
    model_row = conn.execute("SELECT value FROM meta WHERE key='embed_model'").fetchone()
    model = model_row["value"] if model_row else os.environ.get("LTP_EMBED_MODEL", "nomic-embed-text")
    qvec = embed(query, model=model)
    rows = conn.execute(
        "SELECT doc_name, section, chunk_index, text, dim, embedding FROM chunks"
    ).fetchall()
    conn.close()
    scored = []
    for r in rows:
        dim = int(r["dim"])
        vec = list(struct.unpack(f"{dim}f", r["embedding"]))
        m = min(len(vec), len(qvec))
        score = cosine(qvec[:m], vec[:m])
        scored.append({
            "score": round(score, 4),
            "doc_name": r["doc_name"],
            "section": r["section"],
            "chunk_index": r["chunk_index"],
            "text": r["text"],
            "path": f"vault/kb/{r['doc_name']}",
        })
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:k]
