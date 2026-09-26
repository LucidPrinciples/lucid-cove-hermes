"""Guard scripts/sync_kb.sh: signed Drop KB by default, no pack cache, no auto local clone."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SyncKbScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = (ROOT / "scripts" / "sync_kb.sh").read_text(encoding="utf-8")
        cls.ingest = (ROOT / "pack" / "skills" / "kb-ingest.md").read_text(encoding="utf-8")

    def test_no_hardcoded_mac_path(self) -> None:
        self.assertNotIn("/Users/mymac", self.script)

    def test_no_pack_kb_cache(self) -> None:
        self.assertNotIn("pack/kb-cache", self.script)
        self.assertNotIn("pack/kb-cache", self.ingest)
        self.assertFalse((ROOT / "pack" / "kb-cache").exists())

    def test_no_automatic_ltp_drop_clone(self) -> None:
        self.assertNotIn('"$ROOT/data/repos/ltp-drop/kb-source"', self.script)
        self.assertNotIn('"$ROOT/../ltp-drop/kb-source"', self.script)
        self.assertIn("LTP_KB_SOURCE", self.script)
        self.assertIn("OVERRIDE_SRC", self.script)

    def test_signed_kb_is_default(self) -> None:
        self.assertIn("https://drop.lucidprinciples.com/kb/manifest.json", self.script)
        self.assertIn("sha256", self.script)
        self.assertIn("signature", self.script)
        self.assertIn("pkeyutl", self.script)
        self.assertIn("LucidCove-Cove/1.0", self.script)
        self.assertIn("pulling signed KB from", self.script)

    def test_kb_ingest_points_at_signed_drop(self) -> None:
        self.assertIn("drop.lucidprinciples.com/kb/", self.ingest)
        self.assertIn("sync_kb.sh", self.ingest)
        self.assertIn("LTP_KB_SOURCE", self.ingest)
        self.assertNotIn("when present, otherwise", self.ingest)
