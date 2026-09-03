"""Cove-shaped LTP store for Lucid Cove on Hermes (SQLite).

Functionality goal (not backend parity theater):
  - One row per Echo per agent (never lose history)
  - Full Process Record text per Echo
  - Queryable for Team UI / Paperclip overlay

DB path: $LCH_VAULT/ltp.sqlite (default: <repo>/vault/ltp.sqlite)
"""
from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

DEFAULT_VAULT = Path(__file__).resolve().parent / "vault"


def db_path(vault: Path | None = None) -> Path:
    root = Path(vault or os.environ.get("LCH_VAULT", DEFAULT_VAULT))
    return root / "ltp.sqlite"


@contextmanager
def connect(vault: Path | None = None) -> Iterator[sqlite3.Connection]:
    path = db_path(vault)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    try:
        _migrate(conn)
        yield conn
        conn.commit()
    finally:
        conn.close()


def _migrate(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS echoes (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          agent_slug TEXT NOT NULL,
          echo_num INTEGER NOT NULL,
          frequency TEXT,
          principle TEXT,
          signal_type TEXT,
          tuning_key TEXT,
          love_equation REAL,
          love_direction TEXT,
          beta REAL,
          coherence REAL,
          dissonance REAL,
          energy REAL,
          drop_date TEXT,
          drop_sequence INTEGER,
          tuned_at TEXT,
          UNIQUE(agent_slug, echo_num)
        );
        CREATE INDEX IF NOT EXISTS idx_echoes_agent ON echoes(agent_slug, echo_num DESC);

        CREATE TABLE IF NOT EXISTS process_records (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          agent_slug TEXT NOT NULL,
          echo_num INTEGER NOT NULL,
          record_text TEXT NOT NULL,
          metadata_json TEXT,
          created_at TEXT,
          UNIQUE(agent_slug, echo_num)
        );
        CREATE INDEX IF NOT EXISTS idx_pr_agent ON process_records(agent_slug, echo_num DESC);
        """
    )


def next_echo_num(agent_slug: str, *, vault: Path | None = None, drop_date: str | None = None) -> int:
    """Per-agent sequential Echo #. Same drop_date re-run keeps that day's number."""
    with connect(vault) as conn:
        if drop_date:
            row = conn.execute(
                "SELECT echo_num FROM echoes WHERE agent_slug = ? AND drop_date = ?",
                (agent_slug, drop_date),
            ).fetchone()
            if row:
                return int(row["echo_num"])
        row = conn.execute(
            "SELECT MAX(echo_num) AS m FROM echoes WHERE agent_slug = ?",
            (agent_slug,),
        ).fetchone()
        m = row["m"] if row else None
        return (int(m) + 1) if m is not None else 1


def upsert_echo_and_record(
    *,
    agent_slug: str,
    echo_num: int,
    frequency: str | None = None,
    principle: str | None = None,
    signal_type: str | None = None,
    tuning_key: str | None = None,
    love_equation: float | None = None,
    love_direction: str | None = None,
    beta: float | None = None,
    coherence: float | None = None,
    dissonance: float | None = None,
    energy: float | None = None,
    drop_date: str | None = None,
    drop_sequence: int | None = None,
    tuned_at: str | None = None,
    record_text: str,
    metadata: dict[str, Any] | None = None,
    vault: Path | None = None,
) -> None:
    """Insert or replace Echo + Process Record (idempotent on agent_slug, echo_num)."""
    meta = json.dumps(metadata or {}, ensure_ascii=False)
    with connect(vault) as conn:
        conn.execute(
            """
            INSERT INTO echoes (
              agent_slug, echo_num, frequency, principle, signal_type, tuning_key,
              love_equation, love_direction, beta, coherence, dissonance, energy,
              drop_date, drop_sequence, tuned_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(agent_slug, echo_num) DO UPDATE SET
              frequency = excluded.frequency,
              principle = excluded.principle,
              signal_type = excluded.signal_type,
              tuning_key = excluded.tuning_key,
              love_equation = excluded.love_equation,
              love_direction = excluded.love_direction,
              beta = excluded.beta,
              coherence = excluded.coherence,
              dissonance = excluded.dissonance,
              energy = excluded.energy,
              drop_date = excluded.drop_date,
              drop_sequence = excluded.drop_sequence,
              tuned_at = excluded.tuned_at
            """,
            (
                agent_slug, echo_num, frequency, principle, signal_type, tuning_key,
                love_equation, love_direction, beta, coherence, dissonance, energy,
                drop_date, drop_sequence, tuned_at,
            ),
        )
        conn.execute(
            """
            INSERT INTO process_records (agent_slug, echo_num, record_text, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(agent_slug, echo_num) DO UPDATE SET
              record_text = excluded.record_text,
              metadata_json = excluded.metadata_json,
              created_at = excluded.created_at
            """,
            (agent_slug, echo_num, record_text, meta, tuned_at),
        )


def list_echoes(agent_slug: str, *, limit: int = 60, vault: Path | None = None) -> list[dict[str, Any]]:
    with connect(vault) as conn:
        rows = conn.execute(
            """
            SELECT echo_num, frequency, principle, signal_type, love_equation, love_direction,
                   drop_date, tuned_at, drop_sequence
            FROM echoes
            WHERE agent_slug = ?
            ORDER BY echo_num DESC
            LIMIT ?
            """,
            (agent_slug, limit),
        ).fetchall()
    out = []
    for r in rows:
        out.append({
            "echo_num": r["echo_num"],
            "frequency": r["frequency"],
            "principle": r["principle"],
            "signal_type": r["signal_type"],
            "love_equation_value": r["love_equation"],
            "direction": r["love_direction"],
            "when": r["drop_date"],
            "tuned_at": r["tuned_at"],
            "drop_sequence": r["drop_sequence"],
        })
    return out


def get_process_record(agent_slug: str, echo_num: int, *, vault: Path | None = None) -> dict[str, Any] | None:
    with connect(vault) as conn:
        row = conn.execute(
            """
            SELECT pr.echo_num, pr.record_text, pr.metadata_json, pr.created_at,
                   e.frequency, e.principle, e.love_equation, e.love_direction, e.drop_date
            FROM process_records pr
            LEFT JOIN echoes e ON e.agent_slug = pr.agent_slug AND e.echo_num = pr.echo_num
            WHERE pr.agent_slug = ? AND pr.echo_num = ?
            """,
            (agent_slug, echo_num),
        ).fetchone()
    if not row:
        return None
    meta = {}
    if row["metadata_json"]:
        try:
            meta = json.loads(row["metadata_json"])
        except json.JSONDecodeError:
            meta = {}
    return {
        "echo_num": row["echo_num"],
        "record_text": row["record_text"],
        "metadata": meta,
        "created_at": row["created_at"],
        "frequency": row["frequency"],
        "principle": row["principle"],
        "love_equation_value": row["love_equation"],
        "direction": row["love_direction"],
        "when": row["drop_date"],
    }


def latest_echo_num(agent_slug: str, *, vault: Path | None = None) -> int | None:
    with connect(vault) as conn:
        row = conn.execute(
            "SELECT MAX(echo_num) AS m FROM echoes WHERE agent_slug = ?",
            (agent_slug,),
        ).fetchone()
    if not row or row["m"] is None:
        return None
    return int(row["m"])
