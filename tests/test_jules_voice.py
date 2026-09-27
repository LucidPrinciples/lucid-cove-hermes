"""House Jules voice: same-origin proxy when JULES_VOICE_WS is unset."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TEAM = ROOT / "team-page"
JULES_HTML = TEAM / "static" / "jules.html"
if str(TEAM) not in sys.path:
    sys.path.insert(0, str(TEAM))


class JulesHtmlVoiceFallbackTests(unittest.TestCase):
    def test_connect_uses_same_origin_jules_voice_when_inject_empty(self) -> None:
        html = JULES_HTML.read_text(encoding="utf-8")
        self.assertIn("/jules-voice", html)
        self.assertNotIn('connStatus.textContent = "no voice URL"', html)


class JulesVoiceUrlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            import fastapi  # noqa: F401
            import httpx  # noqa: F401
        except ImportError:
            raise unittest.SkipTest("fastapi not installed in overlay unittest env")

    def test_empty_env_uses_same_origin_proxy_path(self) -> None:
        import app as team_app

        with patch.dict(os.environ, {"JULES_VOICE_WS": ""}, clear=False):
            self.assertEqual(team_app._jules_voice_ws("example.com"), "/jules-voice")
            self.assertEqual(team_app._jules_voice_ws("127.0.0.1"), "/jules-voice")

    def test_explicit_env_still_wins(self) -> None:
        import app as team_app

        with patch.dict(os.environ, {"JULES_VOICE_WS": "wss://voice.example"}, clear=False):
            self.assertEqual(team_app._jules_voice_ws("example.com"), "wss://voice.example")

    def test_upstream_ws_from_internal_http(self) -> None:
        import app as team_app

        with patch.dict(os.environ, {"JULES_VOICE_HTTP": ""}, clear=False):
            self.assertEqual(team_app._jules_voice_upstream_ws(), "ws://127.0.0.1:8302/ws")
        with patch.dict(os.environ, {"JULES_VOICE_HTTP": "http://127.0.0.1:8302"}, clear=False):
            self.assertEqual(team_app._jules_voice_upstream_ws(), "ws://127.0.0.1:8302/ws")

    def test_jules_voice_ws_route_exists(self) -> None:
        import app as team_app

        paths = [getattr(r, "path", "") for r in team_app.app.routes]
        self.assertIn("/jules-voice/ws", paths)


if __name__ == "__main__":
    unittest.main()
