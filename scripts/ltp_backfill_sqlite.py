#!/usr/bin/env python3
"""Backfill vault/ltp.sqlite from trajectories.jsonl + per-agent process_record.md.

Safe to re-run (upsert by agent_slug, echo_num).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.environ.get("LCH_ROOT", Path(__file__).resolve().parent.parent))
VAULT = Path(os.environ.get("LCH_VAULT", ROOT / "vault"))
sys.path.insert(0, str(ROOT))
import ltp_store  # noqa: E402


def main() -> int:
    n_traj = 0
    n_md = 0
    traj = VAULT / "drop" / "trajectories.jsonl"
    if traj.is_file():
        for line in traj.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            agent = obj.get("agent") or {}
            slug = agent.get("slug")
            echo_num = obj.get("echo_num")
            record = obj.get("process_record") or ""
            if not slug or echo_num is None or not record.strip():
                continue
            drop = obj.get("drop") or {}
            reading = obj.get("reading") or {}
            ltp_store.upsert_echo_and_record(
                agent_slug=slug,
                echo_num=int(echo_num),
                frequency=drop.get("frequency") or reading.get("frequency"),
                principle=obj.get("principle") or drop.get("principle"),
                signal_type=drop.get("signal_type"),
                tuning_key=drop.get("tuning_key"),
                love_equation=reading.get("love_equation"),
                love_direction=reading.get("direction"),
                beta=reading.get("beta"),
                coherence=reading.get("coherence"),
                dissonance=reading.get("dissonance"),
                energy=reading.get("energy"),
                drop_date=drop.get("date"),
                drop_sequence=drop.get("sequence"),
                tuned_at=obj.get("captured_at"),
                record_text=record,
                metadata={"source": "trajectories.jsonl"},
                vault=VAULT,
            )
            n_traj += 1

    # Latest md only if DB missing that echo
    for folder in (VAULT / "team").glob("*"):
        if not folder.is_dir():
            continue
        slug = folder.name
        latest = folder / "latest.json"
        md = folder / "process_record.md"
        if not latest.is_file() or not md.is_file():
            continue
        try:
            meta = json.loads(latest.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        echo_num = meta.get("echo_num")
        if echo_num is None:
            continue
        if ltp_store.get_process_record(slug, int(echo_num), vault=VAULT):
            continue
        ltp_store.upsert_echo_and_record(
            agent_slug=slug,
            echo_num=int(echo_num),
            frequency=meta.get("frequency"),
            principle=meta.get("principle"),
            love_equation=meta.get("love_equation_value"),
            love_direction=meta.get("direction"),
            drop_date=meta.get("drop_date"),
            drop_sequence=meta.get("drop_sequence"),
            tuned_at=meta.get("tuned_at"),
            record_text=md.read_text(encoding="utf-8"),
            metadata={"source": "process_record.md"},
            vault=VAULT,
        )
        n_md += 1

    print(f"backfill ok: trajectories={n_traj} latest_md={n_md} db={ltp_store.db_path(VAULT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
