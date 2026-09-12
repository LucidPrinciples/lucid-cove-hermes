"""Default Action card: latch a Lucid Tuner account. Overlay does not mint it."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "team-page" / "static"
ACTION_PAGES = ("house.html", "tools.html", "work.html")


class ActionConnectTunerTests(unittest.TestCase):
    def test_actions_panel_hosts_a_list_not_empty_placeholder(self) -> None:
        for name in ACTION_PAGES:
            with self.subTest(page=name):
                html = (STATIC / name).read_text(encoding="utf-8")
                self.assertIn('id="ab-actions-list"', html)
                self.assertNotIn("No actions yet", html)

    def test_action_board_js_paints_connect_lucid_tuner_card(self) -> None:
        js = (STATIC / "action-board.js").read_text(encoding="utf-8")
        self.assertIn("function paintActions", js)
        self.assertIn("ab-actions-list", js)
        self.assertIn("Connect Lucid Tuner", js)
        self.assertIn("https://app.lucidtuner.com", js)
        self.assertIn("Create a Lucid Tuner account", js)
        self.assertIn("Get my connect key", js)
        self.assertIn("Gear", js)
        self.assertIn("shown once", js)
        self.assertNotIn("/api/signup", js)
        self.assertNotIn("create-account", js)

    def test_connected_house_flips_off_signup_to_open_tuner(self) -> None:
        js = (STATIC / "action-board.js").read_text(encoding="utf-8")
        self.assertIn('fetch("/api/actions")', js)
        self.assertIn("Open Lucid Tuner", js)
        self.assertIn("open-lucid-tuner", js)
        house = (STATIC / "house.js").read_text(encoding="utf-8")
        self.assertIn("paintActions", house)
        self.assertIn("loadLinks", house)

    def test_connect_card_is_not_on_tools_or_links_lists(self) -> None:
        js = (STATIC / "action-board.js").read_text(encoding="utf-8")
        tools_start = js.index("const TOOLS")
        tools_end = js.index("function esc")
        tools_block = js[tools_start:tools_end]
        self.assertNotIn("Connect Lucid Tuner", tools_block)
        self.assertNotIn("app.lucidtuner.com", tools_block)
        links_fn = js[js.index("function renderLinks") : js.index("function renderTools")]
        self.assertNotIn("Connect Lucid Tuner", links_fn)
        self.assertNotIn("app.lucidtuner.com", links_fn)


if __name__ == "__main__":
    unittest.main()
