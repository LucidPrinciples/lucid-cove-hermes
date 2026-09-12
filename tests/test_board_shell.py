"""Attention | Action share one shell so the Drop iframe is not torn down."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "team-page" / "static"
APP = ROOT / "team-page" / "app.py"


class BoardShellTests(unittest.TestCase):
    def test_work_shell_keeps_paperclip_and_action_board(self) -> None:
        html = (STATIC / "house.html").read_text(encoding="utf-8")
        self.assertIn('id="pc-frame"', html)
        self.assertIn('id="action-pane"', html)
        self.assertIn('id="ab-tools-list"', html)
        self.assertIn('id="ab-links-list"', html)
        self.assertEqual(html.count('id="drop-frame"'), 1)
        self.assertIn("/static/action-board.css", html)
        self.assertIn("/static/action-board.js", html)

    def test_work_and_tools_routes_serve_the_same_shell(self) -> None:
        src = APP.read_text(encoding="utf-8")
        work = re.search(
            r'@app\.get\("/work"\)\s*\nasync def work\(\):.*?return FileResponse\(([^)]+)\)',
            src,
            re.S,
        )
        tools = re.search(
            r'@app\.get\("/tools"\)\s*\nasync def tools\(\):.*?return FileResponse\(([^)]+)\)',
            src,
            re.S,
        )
        self.assertIsNotNone(work, "missing /work FileResponse")
        self.assertIsNotNone(tools, "missing /tools FileResponse")
        assert work is not None and tools is not None
        self.assertEqual(work.group(1).strip(), tools.group(1).strip())
        self.assertIn("HOUSE", work.group(1))

    def test_board_switch_stays_in_document_and_keeps_drop_src(self) -> None:
        js = (STATIC / "work.js").read_text(encoding="utf-8")
        self.assertIn("preventDefault", js)
        self.assertIn("history.pushState", js)
        self.assertIn("popstate", js)
        self.assertNotRegex(
            js,
            r"dropFrame\.src\s*=\s*[\"']about:blank[\"']",
            msg="switching boards must not unload the Drop iframe",
        )


if __name__ == "__main__":
    unittest.main()
