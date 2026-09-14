"""Action Board Links catalog — vault paths only, no CMS."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "team-page"))

import watch_links  # noqa: E402


class WatchLinksTests(unittest.TestCase):
    def test_catalog_is_the_watch_cards(self) -> None:
        ids = [item["id"] for item in watch_links.WATCH_LINKS]
        self.assertEqual(ids, ["goals-brief", "tuner-surface", "tuner-growth", "stewart-handoff"])
        self.assertTrue(all(item["relpath"].endswith(".md") for item in watch_links.WATCH_LINKS))

    def test_list_marks_missing_and_present(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            (vault / "playbooks").mkdir()
            (vault / "playbooks" / "tuner-surface.md").write_text("# Tuner\n", encoding="utf-8")
            rows = watch_links.list_links(vault)
            by_id = {row["id"]: row for row in rows}
            self.assertTrue(by_id["tuner-surface"]["exists"])
            self.assertFalse(by_id["goals-brief"]["exists"])
            self.assertFalse(by_id["stewart-handoff"]["exists"])
            self.assertNotIn("markdown", by_id["tuner-surface"])

    def test_get_link_returns_body_and_rejects_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            dest = vault / "team" / "stewart"
            dest.mkdir(parents=True)
            (dest / "handoff.md").write_text("next: links\n", encoding="utf-8")
            rec = watch_links.get_link(vault, "stewart-handoff")
            assert rec is not None
            self.assertTrue(rec["exists"])
            self.assertEqual(rec["markdown"], "next: links\n")
            self.assertIsNone(watch_links.get_link(vault, "not-a-card"))
            self.assertIsNone(watch_links.get_link(vault, "../etc/passwd"))

    def test_safe_file_blocks_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            (vault / "playbooks").mkdir()
            self.assertIsNone(watch_links._safe_file(vault, "../goals-brief.md"))
            self.assertIsNone(watch_links._safe_file(vault, "playbooks/../../etc/passwd"))
            self.assertIsNone(watch_links._safe_file(vault, "/etc/passwd"))
            self.assertIsNone(watch_links._safe_file(vault, "playbooks/foo/../goals-brief.md"))
            ok = watch_links._safe_file(vault, "playbooks/goals-brief.md")
            self.assertEqual(ok, (vault / "playbooks" / "goals-brief.md").resolve())


if __name__ == "__main__":
    unittest.main()
