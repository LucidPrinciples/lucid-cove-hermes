"""Action / Links / Flows / Tools are exclusive panels — not one stacked pile."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "team-page" / "static"
CSS = STATIC / "action-board.css"
JS = STATIC / "action-board.js"
HOUSE = STATIC / "house.html"


class ActionBoardTabIsolationTests(unittest.TestCase):
    def test_hidden_act_panels_cannot_display_as_grid(self) -> None:
        css = CSS.read_text(encoding="utf-8")
        self.assertRegex(
            css,
            r"\.ab-act-panel\[hidden\][^}]*display:\s*none",
            "display:grid on .ab-act-panel overrides [hidden] and stacks Links under Actions",
        )
        self.assertRegex(
            css,
            r"\.ab-panel\[hidden\][^}]*display:\s*none",
        )

    def test_house_keeps_four_exclusive_panels(self) -> None:
        html = HOUSE.read_text(encoding="utf-8")
        actions = re.search(
            r'<section id="panel-actions"[^>]*>(.*?)</section>', html, re.S
        )
        links = re.search(
            r'<section id="panel-links"[^>]*>(.*?)</section>', html, re.S
        )
        flows = re.search(
            r'<section id="panel-flows"[^>]*>(.*?)</section>', html, re.S
        )
        tools = re.search(
            r'<section id="panel-tools"[^>]*>(.*?)</section>', html, re.S
        )
        self.assertIsNotNone(actions)
        self.assertIsNotNone(links)
        self.assertIsNotNone(flows)
        self.assertIsNotNone(tools)
        assert actions and links and flows and tools
        self.assertIn('id="ab-actions-list"', actions.group(1))
        self.assertNotIn('id="ab-links-list"', actions.group(1))
        self.assertNotIn('id="ab-tools-list"', actions.group(1))
        self.assertIn('id="ab-links-list"', links.group(1))
        self.assertNotIn('id="ab-actions-list"', links.group(1))
        self.assertIn("No flows yet", flows.group(1))
        self.assertIn('id="ab-tools-list"', tools.group(1))
        self.assertNotIn('id="ab-actions-list"', tools.group(1))
        self.assertNotIn('id="ab-links-list"', tools.group(1))

    def test_show_tab_hides_sibling_panels(self) -> None:
        js = JS.read_text(encoding="utf-8")
        self.assertIn('["actions", "links", "flows", "tools"]', js)
        self.assertIn("panel.hidden = name !== id", js)
        paint = js[js.index("function paintActions") : js.index("function showTab")]
        self.assertIn("ab-actions-list", paint)
        self.assertNotIn("ab-links-list", paint)
        self.assertNotIn("ab-tools-list", paint)
        links_fn = js[js.index("function renderLinks") : js.index("function renderTools")]
        self.assertIn("ab-links-list", links_fn)
        self.assertNotIn("ab-actions-list", links_fn)
        tools_fn = js[js.index("function renderTools") : js.index("function actionCard")]
        self.assertIn("ab-tools-list", tools_fn)
        self.assertNotIn("ab-actions-list", tools_fn)
        self.assertNotIn("ab-links-list", tools_fn)
        self.assertNotIn("Connect Lucid Tuner", tools_fn)


if __name__ == "__main__":
    unittest.main()
