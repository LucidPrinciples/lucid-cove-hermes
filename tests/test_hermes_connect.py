"""Paste Tuner connect-key into this house; CF-65 carry; chrome lights up."""
from __future__ import annotations

import json
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "team-page" / "static"
HOUSE = STATIC / "house.html"
HOUSE_JS = STATIC / "house.js"
APP = ROOT / "team-page" / "app.py"
DOCKERFILE = ROOT / "team-page" / "Dockerfile"
CONNECT = ROOT / "team-page" / "connect.py"


class HermesConnectSurfaceTests(unittest.TestCase):
    def test_house_settings_has_paste_connect_key(self) -> None:
        html = HOUSE.read_text(encoding="utf-8")
        self.assertIn('id="settings-house"', html)
        self.assertIn('id="settings-connect-key"', html)
        self.assertIn('id="settings-connect-handle-input"', html)
        self.assertIn('id="settings-connect-btn"', html)
        self.assertIn("/api/onboarding/connect-operator", HOUSE_JS.read_text(encoding="utf-8"))
        self.assertNotIn("after Hermes-connect", html)

    def test_house_js_reuses_connect_key_parser_and_gates_chrome(self) -> None:
        js = HOUSE_JS.read_text(encoding="utf-8")
        self.assertIn("function parseConnectKey", js)
        self.assertIn("/api/onboarding/connect-operator", js)
        self.assertIn("/api/onboarding/carry-status", js)
        self.assertIn("__lchConnected", js)
        self.assertIn("pathname === \"/app\"", js)
        self.assertNotIn("HERMES_HOUSE_URL", js)
        self.assertNotIn("connect-operator-v2", js)
        self.assertNotIn("self-host-token", js)

    def test_connect_module_is_copied_in_dockerfile(self) -> None:
        df = DOCKERFILE.read_text(encoding="utf-8")
        self.assertIn("COPY team-page/connect.py", df)
        self.assertTrue(CONNECT.is_file())


class ParseConnectKeyTests(unittest.TestCase):
    def test_parse_handle_colon_token(self) -> None:
        sys.path.insert(0, str(ROOT / "team-page"))
        import connect as lch_connect

        handle, token = lch_connect.parse_connect_key("jag:abc.def-ghi")
        self.assertEqual(handle, "jag")
        self.assertEqual(token, "abc.def-ghi")

    def test_parse_bare_token(self) -> None:
        sys.path.insert(0, str(ROOT / "team-page"))
        import connect as lch_connect

        handle, token = lch_connect.parse_connect_key("only-the-token")
        self.assertEqual(handle, "")
        self.assertEqual(token, "only-the-token")


class ConnectOperatorLogicTests(unittest.TestCase):
    def test_reject_empty(self) -> None:
        sys.path.insert(0, str(ROOT / "team-page"))
        import connect as lch_connect
        import asyncio

        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            out = asyncio.run(lch_connect.connect_operator(vault, "", ""))
        self.assertFalse(out["ok"])
        self.assertIn("required", out["reason"])

    def test_verify_fail_does_not_write_token(self) -> None:
        sys.path.insert(0, str(ROOT / "team-page"))
        import connect as lch_connect
        import asyncio

        async def fake_verify(handle, token, **kwargs):
            return {"ok": False, "reason": "That connect key doesn't match this handle."}

        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            with patch.object(lch_connect, "verify_claim", side_effect=fake_verify):
                out = asyncio.run(lch_connect.connect_operator(vault, "jag", "bad-token"))
            self.assertFalse(out["ok"])
            self.assertFalse((vault / "tuner" / "operator.token").is_file())

    def test_success_writes_token_0600_and_merges_sessions(self) -> None:
        sys.path.insert(0, str(ROOT / "team-page"))
        import connect as lch_connect
        import asyncio

        async def fake_verify(handle, token, **kwargs):
            return {"ok": True, "handle": handle}

        async def fake_carry(token, **kwargs):
            return {
                "ok": True,
                "sessions": [
                    {
                        "session_id": "s1",
                        "date": "2026-09-09",
                        "frequency": "Peace",
                        "principle": "Love",
                        "tuning_key": "k",
                    }
                ],
            }

        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            with patch.object(lch_connect, "verify_claim", side_effect=fake_verify):
                with patch.object(lch_connect, "carry_export", side_effect=fake_carry):
                    out = asyncio.run(lch_connect.connect_operator(vault, "jag", "good-token"))
            self.assertTrue(out["ok"])
            self.assertEqual(out["handle"], "jag")
            token_path = vault / "tuner" / "operator.token"
            self.assertTrue(token_path.is_file())
            mode = stat.S_IMODE(token_path.stat().st_mode)
            self.assertEqual(mode, 0o600)
            self.assertEqual(token_path.read_text(encoding="utf-8"), "good-token")
            sessions = json.loads((vault / "tuner" / "sessions.json").read_text(encoding="utf-8"))
            self.assertEqual(sessions[0]["session_id"], "s1")
            self.assertTrue(sessions[0]["carried"])
            state = json.loads((vault / "tuner" / "operator.json").read_text(encoding="utf-8"))
            self.assertTrue(state["connected"])
            self.assertEqual(state["handle"], "jag")
            self.assertEqual(state["carry"]["status"], "complete")

    def test_merge_sessions_keeps_local_row(self) -> None:
        sys.path.insert(0, str(ROOT / "team-page"))
        import connect as lch_connect

        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            (vault / "tuner").mkdir()
            (vault / "tuner" / "sessions.json").write_text(
                json.dumps([{"session_id": "s1", "frequency": "local"}]),
                encoding="utf-8",
            )
            added = lch_connect.merge_sessions(
                vault,
                [{"session_id": "s1", "frequency": "hub"}, {"session_id": "s2", "frequency": "Peace"}],
            )
            rows = json.loads((vault / "tuner" / "sessions.json").read_text(encoding="utf-8"))
            by_id = {r["session_id"]: r for r in rows}
            self.assertEqual(added, 1)
            self.assertEqual(by_id["s1"]["frequency"], "local")
            self.assertEqual(by_id["s2"]["frequency"], "Peace")


class HubClientContractTests(unittest.TestCase):
    def test_verify_claim_and_carry_export_use_cove_ua_and_after_cursor(self) -> None:
        sys.path.insert(0, str(ROOT / "team-page"))
        import connect as lch_connect
        import asyncio

        calls = []

        class FakeResp:
            def __init__(self, payload):
                self.content = b"{}"
                self._payload = payload

            def json(self):
                return self._payload

        class FakeClient:
            async def post(self, url, json=None, headers=None):
                calls.append({"url": url, "json": json, "headers": headers or {}})
                if "verify-claim" in url:
                    return FakeResp({"ok": True, "handle": "jag"})
                after = (json or {}).get("after")
                if after in (0, None):
                    return FakeResp({
                        "ok": True,
                        "sessions": [{"session_id": "a", "id": 1}],
                        "next_after": 1,
                    })
                if after == 1:
                    return FakeResp({
                        "ok": True,
                        "sessions": [{"session_id": "b", "id": 2}],
                        "next_after": 2,
                    })
                return FakeResp({"ok": True, "sessions": [], "next_after": None})

            async def aclose(self):
                return None

        async def run():
            client = FakeClient()
            claim = await lch_connect.verify_claim("jag", "tok", client=client)
            carry = await lch_connect.carry_export("tok", client=client)
            return claim, carry

        claim, carry = asyncio.run(run())
        self.assertTrue(claim["ok"])
        self.assertTrue(carry["ok"])
        self.assertEqual([s["session_id"] for s in carry["sessions"]], ["a", "b"])
        self.assertTrue(all(c["headers"].get("User-Agent") == "LucidCove-Cove/1.0" for c in calls))
        carry_calls = [c for c in calls if "carry-export" in c["url"]]
        self.assertEqual([c["json"].get("after") for c in carry_calls], [0, 1, 2])
        self.assertTrue(all("offset" not in (c["json"] or {}) for c in carry_calls))
        self.assertTrue(all(c["headers"].get("X-Operator-Token") == "tok" for c in carry_calls))


class ConnectRoutesTests(unittest.TestCase):
    def test_presence_me_reports_connected(self) -> None:
        try:
            from fastapi.testclient import TestClient
        except ImportError:
            self.skipTest("fastapi not installed in overlay unittest env")

        team = str(ROOT / "team-page")
        if team not in sys.path:
            sys.path.insert(0, team)
        import app as team_app
        import connect as lch_connect

        client = TestClient(team_app.app)
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            with patch.object(team_app, "VAULT", vault):
                with patch.object(lch_connect, "VAULT", vault, create=True):
                    r = client.get("/api/presence/me")
                    self.assertEqual(r.status_code, 200)
                    body = r.json()
                    self.assertTrue(body.get("ok"))
                    self.assertFalse(body.get("connected"))
                    (vault / "tuner").mkdir(parents=True)
                    (vault / "tuner" / "operator.json").write_text(
                        json.dumps({"connected": True, "handle": "jag"}),
                        encoding="utf-8",
                    )
                    r2 = client.get("/api/presence/me")
                    self.assertTrue(r2.json().get("connected"))
                    self.assertEqual(r2.json().get("handle"), "jag")

    def test_connect_operator_route_reuses_verify_claim(self) -> None:
        try:
            from fastapi.testclient import TestClient
        except ImportError:
            self.skipTest("fastapi not installed in overlay unittest env")

        team = str(ROOT / "team-page")
        if team not in sys.path:
            sys.path.insert(0, team)
        import app as team_app
        import connect as lch_connect

        async def fake_connect(vault, handle, token, **kwargs):
            self.assertEqual(handle, "jag")
            self.assertEqual(token, "tok")
            return {"ok": True, "handle": "jag", "carry": {"status": "complete", "imported": 0}}

        client = TestClient(team_app.app)
        with patch.object(lch_connect, "connect_operator", side_effect=fake_connect):
            r = client.post(
                "/api/onboarding/connect-operator",
                json={"connect_key": "jag:tok"},
            )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["ok"])

        src = APP.read_text(encoding="utf-8")
        self.assertIn("/api/onboarding/connect-operator", src)
        self.assertIn("/api/onboarding/carry-status", src)
        self.assertIn("verify-claim", CONNECT.read_text(encoding="utf-8"))
        self.assertIn("carry-export", CONNECT.read_text(encoding="utf-8"))
        self.assertNotIn("SHARED_CONTAINER_SECRET", CONNECT.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
