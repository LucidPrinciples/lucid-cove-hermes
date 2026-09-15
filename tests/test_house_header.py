"""Stdlib tests for the shared house header chrome."""
from __future__ import annotations

import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "team-page" / "static"

HOUSE_PAGES = (
    "index.html",
    "tuner.html",
    "tools.html",
    "observer.html",
    "work.html",
    "house.html",
)

NAV_ORDER = (
    ("Team", "/"),
    ("Home", "/app"),
    ("Tune", "/tune"),
    ("Playlists", "/playlists"),
)


class _HeaderParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_top_nav = False
        self.in_switch = False
        self._href: str | None = None
        self._text: list[str] = []
        self._bucket: str | None = None
        self.nav_links: list[tuple[str, str]] = []
        self.switch_links: list[tuple[str, str]] = []
        self.has_nav_gap = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        cls = dict(attrs).get("class") or ""
        classes = cls.split()
        if "nav-gap" in classes:
            self.has_nav_gap = True
        if tag == "nav" and "top-nav" in classes:
            self.in_top_nav = True
        if tag in ("div", "nav") and "board-switch" in classes:
            self.in_switch = True
        if tag == "a" and (self.in_top_nav or self.in_switch):
            self._href = dict(attrs).get("href") or ""
            self._text = []
            self._bucket = "nav" if self.in_top_nav else "switch"

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._bucket:
            text = re.sub(r"\s+", " ", "".join(self._text)).strip()
            pair = (text, self._href or "")
            if self._bucket == "nav":
                self.nav_links.append(pair)
            else:
                self.switch_links.append(pair)
            self._bucket = None
            self._href = None
        if tag == "nav" and self.in_top_nav:
            self.in_top_nav = False
        if tag == "div" and self.in_switch:
            self.in_switch = False

    def handle_data(self, data: str) -> None:
        if self._bucket:
            self._text.append(data)


def _parse(name: str) -> _HeaderParser:
    parser = _HeaderParser()
    parser.feed((STATIC / name).read_text(encoding="utf-8"))
    return parser


class HouseHeaderTests(unittest.TestCase):
    def test_house_pages_share_standard_nav_order(self) -> None:
        for name in HOUSE_PAGES:
            with self.subTest(page=name):
                parsed = _parse(name)
                self.assertEqual(parsed.nav_links, list(NAV_ORDER), msg=name)
                self.assertFalse(parsed.has_nav_gap, msg=f"{name} still has nav-gap")

    def test_house_pages_have_attention_action_switch(self) -> None:
        for name in HOUSE_PAGES:
            with self.subTest(page=name):
                parsed = _parse(name)
                labels = [label for label, _ in parsed.switch_links]
                hrefs = [href for _, href in parsed.switch_links]
                self.assertEqual(labels, ["Attention", "Action"], msg=name)
                self.assertEqual(hrefs[0], "/work", msg=name)
                self.assertIn("tab=actions", hrefs[1], msg=name)
                self.assertTrue(hrefs[1].startswith("/tools"), msg=name)

    def test_top_nav_does_not_repeat_attention(self) -> None:
        for name in HOUSE_PAGES:
            with self.subTest(page=name):
                parsed = _parse(name)
                labels = [label for label, _ in parsed.nav_links]
                self.assertNotIn("Attention", labels, msg=name)
                self.assertNotIn("Go Deeper", labels, msg=name)

    def test_go_deeper_is_app_door_not_header(self) -> None:
        html = (STATIC / "house.html").read_text(encoding="utf-8")
        self.assertIn('id="btn-go-deeper"', html)
        self.assertIn("Go Deeper", html)
        self.assertNotIn('data-nav="deeper"', html)
        self.assertIn('href="/app"', html)
        self.assertIn("top-home", html)

    def test_header_badge_is_frequency_not_tuning_hub(self) -> None:
        for name in HOUSE_PAGES:
            with self.subTest(page=name):
                html = (STATIC / name).read_text(encoding="utf-8")
                self.assertNotIn("hub-label", html, msg=name)
                self.assertNotIn("hub-badge", html, msg=name)
                self.assertNotIn(">Tuning Hub<", html, msg=name)
                self.assertIn('id="freq-badge"', html, msg=name)
                self.assertIn('id="freq-text"', html, msg=name)

    def test_thin_header_packs_end_icons_right(self) -> None:
        css = (STATIC / "house.css").read_text(encoding="utf-8")
        start = css.find("@media (max-width: 800px)")
        self.assertGreater(start, -1)
        block = css[start : start + 700]
        self.assertIn("body.house .top-end", block)
        self.assertIn("justify-content: flex-end", block)
        self.assertIn("margin-left: auto", block)
        self.assertNotIn("justify-content: space-between", block)
        self.assertNotIn("flex: 1 0 100%", block.split("body.house .top-end", 1)[-1])

    def test_phone_header_stays_in_grid_row(self) -> None:
        css = (STATIC / "house.css").read_text(encoding="utf-8")
        self.assertIn("grid-template-rows: auto minmax(0, 1fr)", css)
        self.assertIn("z-index: 5000", css)
        self.assertNotIn("html, body.house", css)
        panes = css[css.index("#pane-team") : css.index("#pane-work {")]
        self.assertIn("overflow: visible", panes)

    def test_playlists_scroll_shell_not_viewport(self) -> None:
        js = (STATIC / "tuner" / "playlists.js").read_text(encoding="utf-8")
        self.assertNotIn(".scrollIntoView(", js)
        self.assertNotIn("scrollTo(", js)
        self.assertIn("function _plRevealPlayerMount", js)

    def test_action_board_honors_tab_query(self) -> None:
        js = (STATIC / "action-board.js").read_text(encoding="utf-8")
        self.assertIn("URLSearchParams", js)
        self.assertIn('get("tab")', js)
        self.assertNotRegex(
            js,
            r"start\s*=\s*localStorage\.getItem\(\"lch-ab-tab\"\)",
            msg="query tab must win over leftover localStorage",
        )


if __name__ == "__main__":
    unittest.main()
