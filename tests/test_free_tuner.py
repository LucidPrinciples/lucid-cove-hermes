"""Free Tuner habit floor at /app — house shell, four doors. Overlay Tune stays the wizard."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "team-page" / "static"
APP = ROOT / "team-page" / "app.py"
HOUSE = STATIC / "house.html"
CSS = STATIC / "free-tuner.css"
JS = STATIC / "free-tuner.js"
HOUSE_CSS = STATIC / "house.css"
HOUSE_JS = STATIC / "house.js"


class FreeTunerHomeTests(unittest.TestCase):
    def test_files_exist(self) -> None:
        self.assertTrue(HOUSE.is_file())
        self.assertTrue(CSS.is_file())
        self.assertTrue(JS.is_file())

    def test_route_serves_house_same_as_tune(self) -> None:
        src = APP.read_text(encoding="utf-8")
        route = re.search(
            r'@app\.get\("/app"\)\s*\nasync def \w+\(\):.*?return FileResponse\(([^)]+)\)',
            src,
            re.S,
        )
        self.assertIsNotNone(route, "missing /app FileResponse")
        assert route is not None
        self.assertIn("HOUSE", route.group(1))
        self.assertNotIn("FREE_TUNER", route.group(1))
        tune = re.search(
            r'@app\.get\("/tune"\).*?return FileResponse\(([^)]+)\)',
            src,
            re.S,
        )
        self.assertIsNotNone(tune)
        assert tune is not None
        self.assertIn("HOUSE", tune.group(1))

    def test_home_copy_matches_signed_floor(self) -> None:
        html = HOUSE.read_text(encoding="utf-8")
        self.assertIn("Align Your Broadcast", html)
        self.assertIn("You're always broadcasting. Tune in, or trust the Field.", html)
        self.assertIn("class=\"home-grid\"", html)
        self.assertIn("class=\"home-tile\"", html)
        self.assertIn(">Field<", html)
        self.assertIn("Latest Tuning", html)
        self.assertIn(">Tune<", html)
        self.assertIn("Context + Desired State", html)
        self.assertIn("Playlists", html)
        self.assertIn("Positive lyrics", html)
        self.assertIn("Go Deeper", html)
        self.assertIn("Framework &amp; philosophy", html)
        self.assertNotIn("button-stack", html)
        self.assertNotIn("Field-Selected Tuning", html)
        self.assertNotIn("tuneProBadge", html)
        self.assertNotIn("lt-pro-overlay", html)
        self.assertIn("Lucid Principles, LLC", html)
        self.assertNotIn("Set your frequency", html)
        self.assertNotIn("Today's alignment", html)

    def test_free_chrome_hides_team_attention_action(self) -> None:
        html = HOUSE.read_text(encoding="utf-8")
        css = HOUSE_CSS.read_text(encoding="utf-8")
        js = HOUSE_JS.read_text(encoding="utf-8")
        self.assertIn("board-switch", html)
        self.assertIn(">Team<", html)
        self.assertIn(">Attention<", html)
        self.assertIn(">Action<", html)
        self.assertIn('id="help-btn"', html)
        self.assertNotIn('id="signal-log-btn"', html)
        self.assertIn('id="settings-btn"', html)
        self.assertIn('id="pane-app"', html)
        self.assertIn("house-free", css)
        self.assertIn('.top-nav a[href="/"]', css)
        self.assertIn(".board-switch", css)
        self.assertIn('pathname === "/app"', js)
        self.assertIn('path === "/app"', js)

    def test_doors_use_house_goto_not_a_second_player(self) -> None:
        js = JS.read_text(encoding="utf-8")
        self.assertIn('lchGoto("/tune")', js)
        self.assertIn('lchGoto("/playlists")', js)
        self.assertIn('lchGoto("/deeper")', js)
        self.assertIn('getElementById("freq-badge")', js)
        self.assertNotIn("Audio(", js)
        self.assertNotIn("new Audio", js)
        self.assertNotIn("otSetPlaylist", js)
        html = HOUSE.read_text(encoding="utf-8")
        self.assertIn('id="miniPlayer"', html)
        self.assertNotIn("LUCID_TUNER_APP", html)

    def test_http_app_and_tune_are_house_document(self) -> None:
        import sys

        try:
            from fastapi.testclient import TestClient
        except ImportError:
            self.skipTest("fastapi not installed in overlay unittest env")

        team = str(ROOT / "team-page")
        if team not in sys.path:
            sys.path.insert(0, team)
        import app as team_app

        client = TestClient(team_app.app)
        r_app = client.get("/app")
        r_tune = client.get("/tune")
        self.assertEqual(r_app.status_code, 200)
        self.assertEqual(r_tune.status_code, 200)
        self.assertIn(b'id="house-shell"', r_app.content)
        self.assertIn(b'id="miniPlayer"', r_app.content)
        self.assertIn(b'id="pane-app"', r_app.content)
        self.assertIn(b'id="house-shell"', r_tune.content)
        self.assertIn(b'id="miniPlayer"', r_tune.content)

    def test_app_hero_is_plain_logo_tight_to_title(self) -> None:
        html = HOUSE.read_text(encoding="utf-8")
        css = CSS.read_text(encoding="utf-8")
        self.assertIn("LUCID_TUNER_ICON_HERO.png", html)
        self.assertNotIn("signal-wave", html)
        self.assertNotIn("signal-container", html)
        self.assertIn("width: 176px", css)
        self.assertNotIn("width: 88px", css)
        self.assertNotIn("width: 148px", css)
        self.assertNotIn("width: 260px", css)
        self.assertNotIn("@keyframes pulse-wave", css)
        self.assertNotIn("formatDecodeText", css)
        self.assertNotIn("Audio(", JS.read_text(encoding="utf-8"))

    def test_tagline_has_gap_before_first_button(self) -> None:
        css = CSS.read_text(encoding="utf-8")
        self.assertIn("margin-top: 1.25rem", css)
        self.assertIn("#pane-app .home-grid", css)
        self.assertIn("grid-template-columns: 1fr 1fr", css)
        self.assertNotIn("#pane-app .button-stack", css)

    def test_help_overlay_comes_from_tuner_help(self) -> None:
        html = HOUSE.read_text(encoding="utf-8")
        js = HOUSE_JS.read_text(encoding="utf-8")
        self.assertIn('id="help-overlay"', html)
        self.assertIn('id="help-btn"', html)
        self.assertIn("The Decoder Manual", html)
        self.assertIn("Broadcast", html)
        self.assertIn("432Hz", html)
        self.assertIn("help-btn", js)
        self.assertIn("openHelp", js)
        self.assertNotIn("LUCID_TUNER_APP", html)
        self.assertNotIn("sendFeedback", html)
        self.assertNotIn("GTM-NGS9TV67", html)

    def test_settings_overlays_without_signal_log(self) -> None:
        html = HOUSE.read_text(encoding="utf-8")
        js = HOUSE_JS.read_text(encoding="utf-8")
        self.assertNotIn('id="signal-log-overlay"', html)
        self.assertNotIn('id="signal-log-btn"', html)
        self.assertNotIn("openSignalLog", js)
        self.assertIn('id="settings-overlay"', html)
        self.assertIn('id="settings-btn"', html)
        self.assertIn('id="settings-email"', html)
        self.assertIn('id="settings-signal-filters"', html)
        self.assertIn('id="settings-mirrors"', html)
        self.assertIn('id="settings-streaming-service"', html)
        self.assertIn('id="drop-mirrors"', html)
        self.assertIn('id="reflectModal"', html)
        self.assertIn('id="music-player-overlay"', html)
        self.assertIn('data-settings-scope="tuner"', html)
        self.assertIn('data-settings-scope="house"', html)
        self.assertIn("openSettings", js)
        self.assertIn("applyHouseSettingsToMC", js)
        self.assertIn("loadDropMirrors", js)
        self.assertIn("lch_house_settings", js)
        self.assertIn("streamingService", js)
        self.assertIn("window._openMusicPlayer", js)
        self.assertIn("drop-mirror-header", js)
        self.assertIn("Listen →", js)
        self.assertIn("Reflect →", js)
        self.assertIn("/api/mirrors/today", js)
        self.assertIn("dropMirrorsGen", js)
        self.assertIn("safeSpotifyId", js)
        self.assertIn("open.spotify.com/embed/track/", js)
        self.assertIn("www.youtube.com/embed/", js)
        css = (STATIC / "house.css").read_text(encoding="utf-8")
        self.assertIn("justify-content: space-between", css)
        self.assertIn(".home-mirror-header", css)
        self.assertIn(".drop-mirror-header", css)
        self.assertIn(".home-mirror-reflect", css)
        html_order = html
        self.assertLess(html_order.find('id="drop-frame"'), html_order.find('id="drop-mirrors"'))
        self.assertNotIn("LUCID_TUNER_APP", html)
        self.assertNotIn("sendFeedback", html)
        self.assertNotIn("showUpgradeModal", html)
        self.assertNotIn("GTM-NGS9TV67", js)
        self.assertNotIn("settings.js", html)
        self.assertNotIn("/api/settings/features", js)
        tune = (STATIC / "tuner" / "tune-flow.js").read_text(encoding="utf-8")
        panel = (STATIC / "tuner" / "tuning-panel.js").read_text(encoding="utf-8")
        self.assertIn("_tfLoadMirror", tune)
        self.assertIn("_openMusicPlayer", tune)
        self.assertNotIn("formatDecodeText", js)
        self.assertNotIn("@keyframes pulse", css)
        self.assertIn("setActionHandler('seekbackward'", panel)

    def test_mirrors_today_allowlists_sources(self) -> None:
        import sys

        try:
            from fastapi.testclient import TestClient
        except ImportError:
            self.skipTest("fastapi not installed in overlay unittest env")

        team = str(ROOT / "team-page")
        if team not in sys.path:
            sys.path.insert(0, team)
        import app as team_app
        from mirrors import _parse_mirror_sources

        self.assertEqual(_parse_mirror_sources(None), ["scripture-tpt", "music-mirror"])
        self.assertEqual(
            _parse_mirror_sources("scripture-tpt,../etc,music-mirror,scripture-tpt"),
            ["scripture-tpt", "music-mirror"],
        )
        self.assertEqual(_parse_mirror_sources(""), [])

        client = TestClient(team_app.app)
        registry = client.get("/api/mirrors/registry")
        self.assertEqual(registry.status_code, 200)
        self.assertEqual(len(registry.json().get("mirrors") or []), 3)

        r = client.get("/api/mirrors/today?sources=scripture-tpt,../etc,music-mirror")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("has_mirror", data)
        ids = [m.get("mirror_id") for m in data.get("mirrors") or []]
        self.assertTrue(set(ids) <= {"scripture-tpt", "music-mirror"})
        empty = client.get("/api/mirrors/today?sources=")
        self.assertEqual(empty.status_code, 200)
        self.assertFalse(empty.json().get("has_mirror"))

    def test_mirror_combo_lookup_uses_canon_files(self) -> None:
        import sys

        team = str(ROOT / "team-page")
        if team not in sys.path:
            sys.path.insert(0, team)
        from mirrors import get_mirror_entry

        scripture = get_mirror_entry("Pattern", "Clarity", "Clear", "scripture-tpt")
        self.assertIsNotNone(scripture)
        self.assertEqual(scripture["featured"]["ref"], "Proverbs 23:7")
        self.assertTrue(scripture["featured"]["text"])
        self.assertNotEqual(scripture["featured"]["text"], "Pattern")
        self.assertNotIn("Today’s Drop", scripture["featured"].get("artist") or "")

        music = get_mirror_entry("Pattern", "Peace", "Bright", "music-mirror")
        self.assertIsNotNone(music)
        self.assertEqual(music["mirror_type"], "music")
        self.assertEqual(music["featured"]["title"], "Patterns")
        self.assertTrue(music["featured"].get("spotify_id"))
        self.assertTrue(music["featured"].get("youtube_id"))

        missing = get_mirror_entry("Pattern", "Clarity", "Clear", "../scripture-tpt")
        self.assertIsNone(missing)

    def test_lock_screen_skips_tracks_not_ten_seconds(self) -> None:
        panel = (STATIC / "tuner" / "tuning-panel.js").read_text(encoding="utf-8")
        self.assertIn("setActionHandler('seekbackward'", panel)
        self.assertIn("setActionHandler('seekforward'", panel)
        self.assertIn("otPrev()", panel)
        self.assertIn("otNext()", panel)
        self.assertNotIn("setActionHandler('seekbackward', null)", panel)
        self.assertNotIn("setActionHandler('seekforward', null)", panel)


if __name__ == "__main__":
    unittest.main()
