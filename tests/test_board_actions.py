"""Generated Action list: standing setup, then Links once the artifact exists."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "team-page" / "static"
APP = ROOT / "team-page" / "app.py"
DOCKERFILE = ROOT / "team-page" / "Dockerfile"
BOARD_JS = STATIC / "action-board.js"


class BoardActionsSurfaceTests(unittest.TestCase):
    def test_actions_api_and_module_are_wired(self) -> None:
        app = APP.read_text(encoding="utf-8")
        df = DOCKERFILE.read_text(encoding="utf-8")
        js = BOARD_JS.read_text(encoding="utf-8")
        self.assertIn("import board_actions", app)
        self.assertIn("/api/actions", app)
        self.assertIn("/api/actions/goals-brief", app)
        self.assertIn("COPY team-page/board_actions.py", df)
        self.assertTrue((ROOT / "team-page" / "board_actions.py").is_file())
        self.assertIn("fetch(\"/api/actions\")", js)
        self.assertIn("create-goals-brief", js)
        self.assertIn("Standing", js)
        self.assertIn("Daily", js)
        self.assertNotIn("create-goals-brief", STATIC.joinpath("tools.html").read_text(encoding="utf-8"))

    def test_connect_leaves_action_open_tuner_is_a_link(self) -> None:
        js = BOARD_JS.read_text(encoding="utf-8")
        self.assertIn("function paintActions", js)
        self.assertIn("Connect Lucid Tuner", js)
        self.assertIn("https://app.lucidtuner.com", js)
        self.assertIn("open-lucid-tuner", js)
        self.assertIn("data-link-href", js)
        self.assertNotIn("No daily actions yet", STATIC.joinpath("tools.html").read_text(encoding="utf-8"))


class BoardActionsLogicTests(unittest.TestCase):
    def setUp(self) -> None:
        sys.path.insert(0, str(ROOT / "team-page"))
        import board_actions as ba

        self.ba = ba

    def test_disconnected_and_no_brief_yields_two_standing_actions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            out = self.ba.list_actions(vault)
        ids = [a["id"] for a in out["standing"]]
        self.assertEqual(ids, ["connect-lucid-tuner", "create-goals-brief"])
        self.assertEqual(out["daily"], [])
        self.assertEqual(out["standing"][0]["href"], "https://app.lucidtuner.com")

    def test_connected_drops_connect_action(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            (vault / "tuner").mkdir()
            (vault / "tuner" / "operator.json").write_text(
                json.dumps({"handle": "jagcot"}), encoding="utf-8"
            )
            out = self.ba.list_actions(vault)
        ids = [a["id"] for a in out["standing"]]
        self.assertNotIn("connect-lucid-tuner", ids)
        self.assertIn("create-goals-brief", ids)

    def test_existing_brief_leaves_action_and_lands_on_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            path = vault / "playbooks" / "goals-brief.md"
            path.parent.mkdir(parents=True)
            path.write_text("# Goals Brief\n\nHouse copy.\n", encoding="utf-8")
            actions = self.ba.list_actions(vault)
            links = self.ba.present_links(vault)
        self.assertNotIn("create-goals-brief", [a["id"] for a in actions["standing"]])
        self.assertIn("goals-brief", [link["id"] for link in links])
        missing = [link for link in links if not link.get("exists")]
        self.assertEqual(missing, [])

    def test_create_writes_template_once_and_does_not_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            first = self.ba.create_goals_brief(vault)
            path = vault / "playbooks" / "goals-brief.md"
            self.assertTrue(first["created"])
            self.assertTrue(path.is_file())
            original = path.read_text(encoding="utf-8")
            path.write_text("# Goals Brief\n\nKeep me.\n", encoding="utf-8")
            second = self.ba.create_goals_brief(vault)
            self.assertFalse(second["created"])
            self.assertEqual(path.read_text(encoding="utf-8"), "# Goals Brief\n\nKeep me.\n")
            self.assertIn("Goals Brief", original)
            actions = self.ba.list_actions(vault)
            links = self.ba.present_links(vault)
        self.assertNotIn("create-goals-brief", [a["id"] for a in actions["standing"]])
        self.assertIn("goals-brief", [link["id"] for link in links])

    def test_links_add_open_tuner_only_when_connected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            cold = [link["id"] for link in self.ba.present_links(vault)]
            (vault / "tuner").mkdir()
            (vault / "tuner" / "operator.json").write_text(
                json.dumps({"handle": "jagcot"}), encoding="utf-8"
            )
            hot = self.ba.present_links(vault)
        self.assertNotIn("open-lucid-tuner", cold)
        self.assertNotIn("tuner-action-working", cold)
        match = next(link for link in hot if link["id"] == "open-lucid-tuner")
        self.assertEqual(match["href"], "https://app.lucidtuner.com")
        self.assertTrue(match["exists"])
        working = next(link for link in hot if link["id"] == "tuner-action-working")
        self.assertEqual(
            working["href"],
            "https://github.com/LucidPrinciples/lucid-cove/tree/feat/tuner-action",
        )
        self.assertEqual(working["kind"], "external")
        ids = [link["id"] for link in hot]
        self.assertEqual(ids[0], "open-lucid-tuner")
        self.assertEqual(ids[1], "tuner-action-working")

    def test_create_cannot_escape_vault(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "vault"
            vault.mkdir()
            out = self.ba.create_goals_brief(vault)
            self.assertTrue(out["created"])
            self.assertTrue((vault / "playbooks" / "goals-brief.md").is_file())
            self.assertFalse((Path(tmp) / "goals-brief.md").exists())


if __name__ == "__main__":
    unittest.main()
