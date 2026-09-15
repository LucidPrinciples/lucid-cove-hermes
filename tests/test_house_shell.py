"""House routes share one document so the Tuner mini-player is not torn down."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "team-page" / "static"
APP = ROOT / "team-page" / "app.py"


class HouseShellTests(unittest.TestCase):
    def test_house_pages_serve_the_same_shell(self) -> None:
        src = APP.read_text(encoding="utf-8")
        self.assertIn("house.html", src)
        for name in ("index.html", "tuner.html", "work.html", "observer.html"):
            self.assertNotIn(
                f'STATIC / "{name}"',
                src,
                msg=f"{name} must not be a full-page navigation target",
            )

    def test_house_html_keeps_player_team_work_and_mini_bar(self) -> None:
        html = (STATIC / "house.html").read_text(encoding="utf-8")
        self.assertIn('id="house-shell"', html)
        self.assertIn('id="miniPlayer"', html)
        self.assertIn("otTogglePlay()", html)
        self.assertIn("otPrev()", html)
        self.assertIn("otNext()", html)
        self.assertIn('id="pane-team"', html)
        self.assertIn('id="pane-tuner"', html)
        self.assertIn('id="pane-work"', html)
        self.assertIn('id="pane-observer"', html)
        self.assertIn('id="pane-app"', html)
        self.assertIn('id="pc-frame"', html)
        self.assertIn('id="action-pane"', html)
        self.assertIn('id="roster"', html)
        self.assertEqual(html.count('id="drop-frame"'), 1)
        self.assertIn("/static/house.js", html)
        self.assertNotIn("location.href='/playlists'", html)
        self.assertNotIn('location.href="/tune"', html)

    def test_house_js_stays_in_document_for_nav_and_keeps_audio(self) -> None:
        js = (STATIC / "house.js").read_text(encoding="utf-8")
        self.assertIn("preventDefault", js)
        self.assertIn("history.pushState", js)
        self.assertIn("popstate", js)
        self.assertIn("lchGoto", js)
        self.assertNotRegex(
            js,
            r"location\.href\s*=",
            msg="house nav must not reload and kill otAudio",
        )
        self.assertLess(
            js.find("history.pushState"),
            js.find("loadObserver()"),
            msg="pushState must land before loadObserver reads location.pathname",
        )
        self.assertIn('path === "/"', js)
        self.assertIn('path === "/app"', js)
        self.assertNotIn('route.area === "team"', js.split("function isHousePath")[1][:500])
        self.assertIn('e.target.closest(".mp-btn")', js)
        self.assertIn("_otSyncQueueToAudio", js)
        self.assertIn('"/playlists"', js)

    def test_playlists_tab_restores_playing_track(self) -> None:
        playlists = (STATIC / "tuner" / "playlists.js").read_text(encoding="utf-8")
        panel = (STATIC / "tuner" / "tuning-panel.js").read_text(encoding="utf-8")
        self.assertIn("function _plRestoreNowPlaying", playlists)
        self.assertIn("_plRestoreNowPlaying()", playlists)
        self.assertIn("if (_playlistsLoaded)", playlists)
        loaded_idx = playlists.find("if (_playlistsLoaded)")
        restore_idx = playlists.find("_plRestoreNowPlaying()", loaded_idx)
        self.assertGreater(
            restore_idx,
            loaded_idx,
            msg="already-built Playlists tab must restore the live track, not return empty",
        )
        self.assertIn("function _otSyncQueueToAudio", panel)
        self.assertIn("_otActiveQueue", panel)
        self.assertNotIn(
            "otSetPlaylist(",
            playlists[
                playlists.find("function _plRestoreNowPlaying") : playlists.find(
                    "async function loadPlaylistsTab"
                )
            ],
        )

    def test_tune_flow_does_not_reshuffle_while_playing(self) -> None:
        src = (STATIC / "tuner" / "tune-flow.js").read_text(encoding="utf-8")
        start = src.find("async function loadTuneFlow()")
        self.assertGreater(start, -1)
        chunk = src[start : start + 900]
        self.assertIn("_otSource === 'tune'", chunk)
        self.assertIn("!otAudio.paused", chunk)
        self.assertIn("return;", chunk)

    def test_mini_player_uses_bigger_type_and_lp_freq_color(self) -> None:
        css = (STATIC / "house.css").read_text(encoding="utf-8")
        js = (STATIC / "house.js").read_text(encoding="utf-8")
        self.assertIn("font-size: 1.05rem", css)
        self.assertIn("font-size: 0.82rem", css)
        self.assertIn("--mp-freq-color", css)
        self.assertIn("function mpLookupColor", js)
        self.assertIn("window._otFreqColor", js)
        self.assertIn("lpColor", js)
        self.assertIn("lpSignalColor", js)
        self.assertIn("lpPrincipleColor", js)
        self.assertNotIn("animation: pulse", css)
        self.assertNotIn("@keyframes pulse", css)
        self.assertNotIn("formatDecodeText", js)

    def test_in_pane_player_and_tune_copy_use_bigger_type(self) -> None:
        css = (STATIC / "house.css").read_text(encoding="utf-8")
        js = (STATIC / "house.js").read_text(encoding="utf-8")
        self.assertIn("body.house .ot-track-title", css)
        self.assertIn("body.house .ot-track-signal", css)
        self.assertIn("font-size: 1.2rem", css)
        self.assertIn("body.house .ot-pl-track", css)
        self.assertIn("font-size: 0.92rem", css)
        self.assertIn("body.house .tf-coaching-text", css)
        self.assertIn("body.house .tf-practice-step", css)
        self.assertIn("body.house .tf-key-quote", css)
        self.assertIn("font-size: 1.2rem", css)
        self.assertIn("document.body.style.setProperty(\"--mp-freq-color\"", js)
        self.assertIn("removeProperty(\"--mp-freq-color\")", js)
        self.assertNotIn("@keyframes pulse", css)
        self.assertNotIn("formatDecodeText", js)
        self.assertNotIn("formatDecodeText", css)

    def test_tune_header_logo_and_titles_are_bigger(self) -> None:
        css = (STATIC / "house.css").read_text(encoding="utf-8")
        self.assertIn("body.house .tf-logo-img", css)
        self.assertIn("width: 64px", css)
        self.assertIn("body.house .tf-complete-title", css)
        self.assertIn("body.house .tf-complete-freq", css)
        self.assertIn("body.house .tf-complete-principle", css)
        self.assertIn("font-size: 1.45rem", css)
        self.assertIn("body.house .tf-question", css)
        self.assertIn("#pane-tuner .tuner-main", css)
        self.assertNotIn("@keyframes pulse", css)
        self.assertNotIn("formatDecodeText", css)

    def test_coaching_skim_tints_signed_word_map(self) -> None:
        css = (STATIC / "house.css").read_text(encoding="utf-8")
        js = (STATIC / "house.js").read_text(encoding="utf-8")
        self.assertIn("body.house .tf-skim-old", css)
        self.assertIn("body.house .tf-skim-active", css)
        self.assertIn("body.house .tf-skim-action", css)
        self.assertIn("function paintCoachSkim", js)
        self.assertIn("function skimCoachHtml", js)
        self.assertIn("escapeCoachText", js)
        self.assertIn(".tf-coaching-text", js)
        self.assertIn("threat detection", js)
        self.assertIn("kinetic interrupt", js)
        self.assertNotIn("formatDecodeText", js)
        tune = (STATIC / "tuner" / "tune-flow.js").read_text(encoding="utf-8")
        panel = (STATIC / "tuner" / "tuning-panel.js").read_text(encoding="utf-8")
        self.assertNotIn("paintCoachSkim", tune)
        self.assertNotIn("formatDecodeText", tune)
        self.assertNotIn("formatDecodeText", panel)

    def test_lock_screen_maps_seek_to_skip_tracks(self) -> None:
        panel = (STATIC / "tuner" / "tuning-panel.js").read_text(encoding="utf-8")
        start = panel.find("function _otBindMediaSessionHandlers")
        self.assertGreater(start, -1)
        chunk = panel[start : start + 1600]
        self.assertIn("setActionHandler('previoustrack'", chunk)
        self.assertIn("setActionHandler('nexttrack'", chunk)
        self.assertIn("setActionHandler('seekbackward', () => otPrev())", chunk)
        self.assertIn("setActionHandler('seekforward', () => otNext())", chunk)
        self.assertNotIn("setActionHandler('seekbackward', null)", chunk)

    def test_player_does_not_skip_storm_on_load_error(self) -> None:
        panel = (STATIC / "tuner" / "tuning-panel.js").read_text(encoding="utf-8")
        start = panel.index("otAudio.addEventListener('error'")
        err = panel[start : panel.index("otAudio.addEventListener('playing'")]
        self.assertIn("not skipping", err)
        self.assertNotIn("setTimeout(() => otNext(), 1500)", err)


if __name__ == "__main__":
    unittest.main()
