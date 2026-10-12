"""Guards for honest sonic attunement in the overlay morning runner."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = (ROOT / "scripts" / "ltp_morning_runner.py").read_text(encoding="utf-8")


class MorningAttuneSourceTests(unittest.TestCase):
    def test_metadata_only_clause_removed(self):
        self.assertNotIn("metadata-only", RUNNER)

    def test_attune_sync_wired(self):
        self.assertIn("def attune_today_echo", RUNNER)
        self.assertIn("attune_sync", RUNNER)
        self.assertIn("render_experience", RUNNER)
        self.assertIn("attunement_status=attune_status", RUNNER)
        self.assertIn("## Sonic attunement", RUNNER)

    def test_sonic_in_practice_prompt_not_only_record(self):
        start = RUNNER.index("def tune_one(")
        respond = RUNNER.index("session.respond_sync", start)
        practice = RUNNER[start:respond]
        self.assertIn("## Sonic attunement", practice)
        self.assertIn("audio_block", practice)
        record = RUNNER[respond : RUNNER.index("\ndef main(")]
        self.assertIn("## Sonic attunement", record)

    def test_attune_once_per_run_not_per_agent(self):
        start = RUNNER.index("def tune_one(")
        body = RUNNER[start : RUNNER.index("\ndef main(")]
        self.assertNotIn("attune_today_echo(", body)
        main = RUNNER[RUNNER.index("\ndef main(") :]
        self.assertEqual(main.count("attune_today_echo("), 1)


if __name__ == "__main__":
    unittest.main()
