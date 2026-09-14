"""Links brief modal renders formatted markdown, not a raw <pre> dump."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "team-page" / "static" / "action-board.js"
CSS = ROOT / "team-page" / "static" / "action-board.css"


class BriefModalTests(unittest.TestCase):
    def test_drawer_uses_prose_article_not_pre(self) -> None:
        js = JS.read_text(encoding="utf-8")
        self.assertIn('article class="ab-brief-body md-prose"', js)
        self.assertNotIn('<pre class="ab-brief-body"', js)
        self.assertIn("function formatVaultMarkdown", js)
        self.assertIn("body.innerHTML = formatVaultMarkdown", js)
        self.assertIn("esc(s)", js)

    def test_prose_styles_use_frequency_color(self) -> None:
        css = CSS.read_text(encoding="utf-8")
        self.assertIn(".md-prose h1", css)
        self.assertIn(".md-prose strong", css)
        self.assertIn(".md-prose table", css)
        self.assertIn("var(--freq-primary", css)
        self.assertNotIn("white-space: pre-wrap", css)


if __name__ == "__main__":
    unittest.main()
