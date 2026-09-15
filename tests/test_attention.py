"""Attention target: Paperclip first, else Hermes Kanban, else empty pane."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TEAM = ROOT / "team-page"
STATIC = TEAM / "static"
if str(TEAM) not in sys.path:
    sys.path.insert(0, str(TEAM))

from attention import (  # noqa: E402
    FRAME_HM_KANBAN,
    FRAME_PC,
    PREFIX_PC,
    hop_skip_request,
    join_backend,
    is_house_reserved,
    pick_attention_frame,
    paperclip_org_frame,
    referer_attn_kind,
    rewrite_html,
    rewrite_location,
    rewrite_referer_to_backend,
    strip_proxy_prefix,
)


class PickAttentionFrameTests(unittest.TestCase):
    def test_paperclip_wins_even_if_hermes_is_up(self) -> None:
        frame = pick_attention_frame(
            paperclip_ok=True,
            hermes_ok=True,
            paperclip_url="http://127.0.0.1:3100/",
            hermes_url="http://127.0.0.1:9119",
        )
        self.assertEqual(frame["source"], "paperclip")
        self.assertEqual(frame["url"], FRAME_PC)
        self.assertNotIn("127.0.0.1", frame["url"])

    def test_paperclip_org_prefix_opens_full_dashboard(self) -> None:
        frame = pick_attention_frame(
            paperclip_ok=True,
            hermes_ok=True,
            issue_prefix="LUC",
        )
        self.assertEqual(frame["url"], "/attn/pc/LUC/dashboard")
        self.assertNotIn("127.0.0.1", frame["url"])
        self.assertEqual(paperclip_org_frame("LUC"), "/attn/pc/LUC/dashboard")
        self.assertEqual(paperclip_org_frame("../x"), FRAME_PC)
        self.assertEqual(paperclip_org_frame(""), FRAME_PC)

    def test_hermes_kanban_when_paperclip_is_down(self) -> None:
        frame = pick_attention_frame(
            paperclip_ok=False,
            hermes_ok=True,
            paperclip_url="http://127.0.0.1:3100",
            hermes_url="http://127.0.0.1:9119/",
        )
        self.assertEqual(frame["source"], "hermes")
        self.assertEqual(frame["url"], FRAME_HM_KANBAN)
        self.assertNotIn("127.0.0.1", frame["url"])

    def test_empty_when_neither_is_up(self) -> None:
        frame = pick_attention_frame(
            paperclip_ok=False,
            hermes_ok=False,
            paperclip_url="http://127.0.0.1:3100",
            hermes_url="http://127.0.0.1:9119",
        )
        self.assertEqual(frame["source"], "none")
        self.assertEqual(frame["url"], "")


class SameOriginProxyHelpersTests(unittest.TestCase):
    def test_join_backend_keeps_loopback_origin(self) -> None:
        self.assertEqual(
            join_backend("http://127.0.0.1:3100", "api/companies"),
            "http://127.0.0.1:3100/api/companies",
        )

    def test_join_backend_rejects_escape(self) -> None:
        self.assertIsNone(join_backend("http://127.0.0.1:3100", "http://evil.example/"))
        self.assertIsNone(join_backend("http://127.0.0.1:3100", "//evil.example/"))
        self.assertEqual(
            join_backend("http://127.0.0.1:3100", "../"),
            "http://127.0.0.1:3100/",
        )

    def test_strip_proxy_prefix_drops_attn_pc(self) -> None:
        self.assertEqual(strip_proxy_prefix("/attn/pc/", PREFIX_PC), "/")
        self.assertEqual(strip_proxy_prefix("/attn/pc/inbox", PREFIX_PC), "/inbox")
        self.assertEqual(strip_proxy_prefix("attn/pc/", PREFIX_PC), "/")
        self.assertEqual(strip_proxy_prefix("/api/companies", PREFIX_PC), "/api/companies")

    def test_join_backend_does_not_forward_attn_prefix(self) -> None:
        self.assertEqual(
            join_backend("http://127.0.0.1:3100", "/attn/pc/"),
            "http://127.0.0.1:3100/",
        )
        self.assertEqual(
            join_backend("http://127.0.0.1:3100", "attn/pc/inbox"),
            "http://127.0.0.1:3100/inbox",
        )

    def test_rewrite_location_prefixes_backend(self) -> None:
        self.assertEqual(
            rewrite_location("http://127.0.0.1:3100/login", "http://127.0.0.1:3100", "/attn/pc"),
            "/attn/pc/login",
        )
        self.assertEqual(
            rewrite_location("/foo", "http://127.0.0.1:3100", "/attn/pc"),
            "/attn/pc/foo",
        )

    def test_rewrite_html_injects_base_and_rewrites_backend(self) -> None:
        html = rewrite_html(
            "<html><head></head><body>http://127.0.0.1:3100/x</body></html>",
            "/attn/pc",
            "http://127.0.0.1:3100",
        )
        self.assertIn('<base href="/attn/pc/">', html)
        self.assertIn("window.fetch", html)
        self.assertIn("Location.prototype", html)
        self.assertIn("History.prototype.pushState", html)
        self.assertIn("masked", html)
        self.assertIn("history.state", html)
        self.assertIn("seed(history.state)", html)
        self.assertNotIn("seed(history.state,p+'/')", html)
        self.assertIn("/attn/pc/x", html)
        self.assertNotIn("http://127.0.0.1:3100", html)

    def test_house_api_not_stolen_by_referer_passthrough(self) -> None:
        self.assertTrue(is_house_reserved("/api/attention"))
        self.assertTrue(is_house_reserved("/api/team"))
        self.assertTrue(is_house_reserved("/static/house.css"))
        self.assertFalse(is_house_reserved("/assets/index.js"))
        self.assertFalse(is_house_reserved("/api/companies/x"))

    def test_hop_skip_strips_house_identity_headers(self) -> None:
        self.assertTrue(hop_skip_request("X-Forwarded-Host"))
        self.assertTrue(hop_skip_request("x-forwarded-proto"))
        self.assertTrue(hop_skip_request("X-Real-IP"))
        self.assertTrue(hop_skip_request("Forwarded"))
        self.assertTrue(hop_skip_request("Origin"))
        self.assertTrue(hop_skip_request("host"))
        self.assertFalse(hop_skip_request("Accept"))
        self.assertFalse(hop_skip_request("Authorization"))

    def test_referer_kind_and_backend_referer(self) -> None:
        self.assertEqual(referer_attn_kind("https://house.example.test/attn/pc/"), "pc")
        self.assertEqual(referer_attn_kind("https://house.example.test/attn/hm/kanban"), "hm")
        self.assertIsNone(referer_attn_kind("https://house.example.test/work"))
        self.assertEqual(
            rewrite_referer_to_backend(
                "https://house.example.test/attn/pc/inbox",
                "/attn/pc",
                "http://127.0.0.1:3100",
            ),
            "http://127.0.0.1:3100/inbox",
        )


class AttentionApiTests(unittest.TestCase):
    def test_api_attention_returns_hermes_when_paperclip_probe_fails(self) -> None:
        try:
            from fastapi.testclient import TestClient
        except ImportError:
            self.skipTest("fastapi not installed in overlay unittest env")

        import app as team_app

        async def fake_probe(url: str) -> bool:
            return "/api/status" in url

        client = TestClient(team_app.app)
        with patch.object(team_app, "_probe_http", side_effect=fake_probe):
            r = client.get("/api/attention")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["source"], "hermes")
        self.assertEqual(body["url"], FRAME_HM_KANBAN)
        self.assertFalse(body["paperclip_ok"])
        self.assertTrue(body["hermes_ok"])

    def test_api_attention_paperclip_is_same_origin_path(self) -> None:
        try:
            from fastapi.testclient import TestClient
        except ImportError:
            self.skipTest("fastapi not installed in overlay unittest env")

        import app as team_app

        async def fake_probe(url: str) -> bool:
            return True

        async def fake_prefix() -> str:
            return "LUC"

        client = TestClient(team_app.app)
        with patch.object(team_app, "_probe_http", side_effect=fake_probe), patch.object(
            team_app, "_paperclip_issue_prefix", side_effect=fake_prefix
        ):
            r = client.get("/api/attention")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["source"], "paperclip")
        self.assertEqual(body["url"], "/attn/pc/LUC/dashboard")
        self.assertNotIn("127.0.0.1", body["url"])

    def test_attn_proxy_does_not_forward_house_host(self) -> None:
        try:
            from fastapi.testclient import TestClient
        except ImportError:
            self.skipTest("fastapi not installed in overlay unittest env")

        import app as team_app

        captured: dict = {}

        class FakeResp:
            status_code = 200
            content = b"<html><head></head><body>ok</body></html>"
            headers = {"content-type": "text/html"}
            charset_encoding = "utf-8"
            encoding = "utf-8"

        class FakeClient:
            def __init__(self, *a, **k):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return None

            async def request(self, method, url, headers=None, content=None):
                captured["headers"] = dict(headers or {})
                captured["url"] = url
                return FakeResp()

        client = TestClient(team_app.app)
        with patch.object(team_app.httpx, "AsyncClient", FakeClient):
            r = client.get(
                "/attn/pc/",
                headers={
                    "Host": "house.example.test",
                    "X-Forwarded-Host": "house.example.test",
                    "X-Forwarded-Proto": "https",
                    "Origin": "https://house.example.test",
                },
            )
        self.assertEqual(r.status_code, 200)
        names = {k.lower() for k in captured["headers"]}
        self.assertNotIn("x-forwarded-host", names)
        self.assertNotIn("x-forwarded-proto", names)
        origin = ""
        for k, v in captured["headers"].items():
            if k.lower() == "origin":
                origin = v
        self.assertTrue(origin)
        self.assertNotIn("house.example.test", origin.lower())


class AttentionChromeTests(unittest.TestCase):
    def test_work_js_probes_before_setting_iframe(self) -> None:
        js = (STATIC / "work.js").read_text(encoding="utf-8")
        self.assertIn("/api/attention", js)
        self.assertIn("loadAttention", js)
        self.assertNotIn("pcFrame.src = PAPERCLIP_URL", js)
        self.assertIn("pc-embed--hermes", js)
        self.assertIn("pc-empty", js)
        loaded = js.index("attentionLoaded = true")
        src = js.index("pcFrame.src = url")
        self.assertLess(src, loaded)

    def test_house_keeps_header_over_attention_embed(self) -> None:
        html = (STATIC / "house.html").read_text(encoding="utf-8")
        self.assertIn('id="pc-embed"', html)
        self.assertIn('id="pc-empty"', html)
        self.assertIn('id="pc-frame"', html)
        css = (STATIC / "work.css").read_text(encoding="utf-8")
        self.assertIn(".pc-embed--hermes", css)
        self.assertIn("--hermes-chrome-top", css)
        self.assertIn("position: relative", css)

    def test_phone_header_forces_two_rows(self) -> None:
        css = (STATIC / "house.css").read_text(encoding="utf-8")
        self.assertIn("@media (max-width: 800px)", css)
        self.assertIn("body.house .top-nav", css)
        self.assertIn("flex: 1 0 100%", css)
        self.assertIn("body.house .top-end", css)
        self.assertIn("margin-left: 0", css)


if __name__ == "__main__":
    unittest.main()
