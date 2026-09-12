"""Settings: Tune Now signal sliders, ordered mirrors, house tuning model."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "team-page" / "static"
HOUSE = STATIC / "house.html"
HOUSE_JS = STATIC / "house.js"
HOUSE_CSS = STATIC / "house.css"
TEAM_JS = STATIC / "team.js"
DOCKERFILE = ROOT / "team-page" / "Dockerfile"


class SettingsPrefsTests(unittest.TestCase):
    def test_signal_filters_are_colored_toggles_for_tune_now(self) -> None:
        html = HOUSE.read_text(encoding="utf-8")
        js = HOUSE_JS.read_text(encoding="utf-8")
        css = HOUSE_CSS.read_text(encoding="utf-8")
        self.assertIn('id="settings-signal-filters"', html)
        self.assertIn("Tune Now", html)
        self.assertNotIn("Checked signals stay out of Field-selected Tune.", html)
        self.assertIn("Field-selected", html)
        self.assertIn("settings-slider-row", html)
        self.assertIn('role="switch"', html)
        self.assertIn("data-signal=", html)
        self.assertIn("#5ce1e6", html)
        self.assertIn("settings-toggle", css)
        self.assertIn("aria-checked", js)
        self.assertIn("collectExcludedSignals", js)
        self.assertIn("ALLOWED_SIGNALS.length", js)

    def test_mirrors_keep_checkbox_and_dom_order(self) -> None:
        html = HOUSE.read_text(encoding="utf-8")
        js = HOUSE_JS.read_text(encoding="utf-8")
        self.assertIn("settings-mirror-row", html)
        self.assertIn("mirror-drag-handle", html)
        self.assertIn('name="tuning-mirror"', html)
        self.assertIn("drag to reorder", html.lower())
        self.assertIn("collectMirrorsInOrder", js)
        self.assertIn("settings-mirror-row", js)
        self.assertIn("dragstart", js)

    def test_tuning_model_is_dropdown_on_team_and_settings(self) -> None:
        html = HOUSE.read_text(encoding="utf-8")
        team = TEAM_JS.read_text(encoding="utf-8")
        js = HOUSE_JS.read_text(encoding="utf-8")
        self.assertIn('id="ltp-model"', html)
        self.assertIn("<select", html)
        self.assertNotIn('<input type="text" id="ltp-model"', html)
        self.assertIn('id="settings-ltp-model"', html)
        self.assertIn("/api/ltp/models", team)
        self.assertIn("/api/ltp/models", js)
        self.assertIn("/api/ltp/config", js)
        self.assertIn("COPY team-page/ltp_settings.py", DOCKERFILE.read_text(encoding="utf-8"))


class LtpSettingsHelpersTests(unittest.TestCase):
    def test_normalize_model_rejects_paths(self) -> None:
        import sys

        team = str(ROOT / "team-page")
        if team not in sys.path:
            sys.path.insert(0, team)
        from ltp_settings import normalize_model

        self.assertEqual(normalize_model("qwen3:8b"), "qwen3:8b")
        self.assertEqual(normalize_model("  grok-4.6  "), "grok-4.6")
        self.assertIsNone(normalize_model("../etc/passwd"))
        self.assertIsNone(normalize_model("foo/bar"))
        self.assertIsNone(normalize_model(""))
        self.assertIsNone(normalize_model("a" * 200))

    def test_list_models_allowlists_names_and_keeps_current(self) -> None:
        import sys

        team = str(ROOT / "team-page")
        if team not in sys.path:
            sys.path.insert(0, team)
        from ltp_settings import list_models

        names = list_models(
            current="qwen3:8b",
            ollama_base_url="http://127.0.0.1:11434/v1",
            fetch_tags=lambda _url: ["llama3:8b", "../x", "qwen3:8b"],
        )
        self.assertEqual(names[0], "qwen3:8b")
        self.assertIn("llama3:8b", names)
        self.assertNotIn("../x", names)

        empty = list_models(
            current="qwen3:8b",
            ollama_base_url="http://evil.example/v1",
            fetch_tags=lambda _url: ["should-not-run"],
        )
        self.assertEqual(empty, ["qwen3:8b"])


if __name__ == "__main__":
    unittest.main()
