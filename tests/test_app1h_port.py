"""APP1-H markers the house shell tests do not already lock."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "team-page" / "static"
TUNER = STATIC / "tuner"


class App1HPortTests(unittest.TestCase):
    def test_house_links_icons_and_keeps_its_name(self) -> None:
        html = (STATIC / "house.html").read_text(encoding="utf-8")
        self.assertIn('<title>Lucid Cove on Hermes</title>', html)
        self.assertIn('href="/static/tuner/favicon.svg"', html)
        self.assertIn('href="/static/tuner/apple-touch-icon.png"', html)
        self.assertNotIn("apple-mobile-web-app-title", html)
        self.assertNotIn("manifest", html)
        for name in (
            "favicon.svg",
            "apple-touch-icon.png",
            "icon-192.png",
            "icon-512.png",
        ):
            self.assertTrue((TUNER / name).is_file(), name)

    def test_header_keeps_the_status_bar_clear(self) -> None:
        team = (STATIC / "team.css").read_text(encoding="utf-8")
        house = (STATIC / "house.css").read_text(encoding="utf-8")
        top = team[team.index(".top {") : team.index(".top-nav")]
        self.assertIn("safe-area-inset-top", top)
        self.assertIn("safe-area-inset-left", top)
        self.assertIn("safe-area-inset-right", top)
        phone = house[house.index("@media (max-width: 800px)") : house.index(".help-panel")]
        self.assertIn("safe-area-inset-top", phone)
        self.assertIn("safe-area-inset-left", phone)
        self.assertIn("safe-area-inset-right", phone)
        self.assertNotIn("padding: 0.7rem 0.85rem", phone)

    def test_daily_tune_drops_the_shaped_line_and_cleans_coaching(self) -> None:
        flow = (TUNER / "tune-flow.js").read_text(encoding="utf-8")
        css = (TUNER / "tune-flow.css").read_text(encoding="utf-8")
        self.assertIn("function _tfReadCoaching", flow)
        self.assertIn("signal_before", flow)
        self.assertNotIn("tuneShaped", flow)
        self.assertNotIn("shaped by your answers", flow)
        self.assertNotIn(".tf-shaped", css)
        self.assertIn("feats.mirror === false", flow)
        self.assertIn("'/api/mirrors/today?'", flow)

    def test_player_shows_loading_and_warms_on_timeupdate(self) -> None:
        panel = (TUNER / "tuning-panel.js").read_text(encoding="utf-8")
        mount = (TUNER / "tuner-mount.css").read_text(encoding="utf-8")
        self.assertIn("is-loading", panel)
        self.assertIn("otAudio.addEventListener('timeupdate'", panel)
        self.assertIn("_otMaybeWarm", panel)
        self.assertIn("@keyframes ot-load-pulse", mount)
        self.assertIn("#mpPlayBtn.is-loading", mount)

    def test_playlists_start_at_a_random_index(self) -> None:
        playlists = (TUNER / "playlists.js").read_text(encoding="utf-8")
        self.assertEqual(playlists.count("startIndex:"), 3)
        self.assertNotIn("// Shuffle", playlists)
        self.assertIn("function _plRestoreNowPlaying", playlists)
        self.assertIn("function _plRevealPlayerMount() {}", playlists)
