"""Team page today's Drop: presentation, no header-duplicate links."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "team-page" / "static"
HOUSE = STATIC / "house.html"
CSS = STATIC / "team.css"
JS = STATIC / "team.js"


def _pane_team(html: str) -> str:
    m = re.search(
        r'<div id="pane-team"[^>]*>(.*?)</div>\s*<div id="pane-tuner"',
        html,
        re.S,
    )
    assert m, "pane-team not found in house.html"
    return m.group(1)


def _drop_section(pane: str) -> str:
    m = re.search(r'<section id="drop"[^>]*>(.*?)</section>', pane, re.S)
    assert m, "Team Drop section missing"
    return m.group(0)


class TeamDropPresentationTests(unittest.TestCase):
    def test_drop_section_has_no_header_duplicate_links(self) -> None:
        drop = _drop_section(_pane_team(HOUSE.read_text(encoding="utf-8")))
        self.assertNotIn("drop-links", drop)
        self.assertNotIn("Attention (Paperclip", drop)
        self.assertNotIn("Paperclip raw", drop)
        self.assertNotIn(">Hermes<", drop)
        self.assertNotIn('href="/work"', drop)
        self.assertNotIn('href="/tools"', drop)

    def test_drop_section_presents_signal_principle_and_key(self) -> None:
        drop = _drop_section(_pane_team(HOUSE.read_text(encoding="utf-8")))
        self.assertIn('id="drop-freq"', drop)
        self.assertIn('id="drop-signal"', drop)
        self.assertIn('id="drop-principle"', drop)
        self.assertIn('id="drop-key"', drop)
        self.assertIn('id="drop-meta"', drop)
        self.assertIn("Today", drop)

    def test_apply_drop_paints_signal_type(self) -> None:
        js = JS.read_text(encoding="utf-8")
        apply = js[js.index("function applyDrop") : js.index("function renderRoster")]
        self.assertIn("drop-signal", apply)
        self.assertIn("signal_type", apply)
        self.assertIn("drop-principle", apply)
        self.assertIn("drop-key", apply)
        self.assertIn("tuning_key", apply)
        self.assertNotIn("drop-links", apply)

    def test_css_lays_drop_out_as_column(self) -> None:
        css = CSS.read_text(encoding="utf-8")
        self.assertIn(".drop-signal", css)
        self.assertIn(".drop-principle", css)
        self.assertIn(".drop-key", css)
        self.assertNotRegex(css, r"\.drop-links\s*\{")


if __name__ == "__main__":
    unittest.main()
