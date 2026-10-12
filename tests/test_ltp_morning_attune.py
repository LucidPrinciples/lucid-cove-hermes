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


if __name__ == "__main__":
    unittest.main()
