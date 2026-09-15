"""House Help contact forward to the public inbox."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "team-page" / "static"
DOCKERFILE = ROOT / "team-page" / "Dockerfile"


class HelpContactTests(unittest.TestCase):
    def test_help_form_is_present(self) -> None:
        html = (STATIC / "house.html").read_text(encoding="utf-8")
        js = (STATIC / "house.js").read_text(encoding="utf-8")
        css = (STATIC / "house.css").read_text(encoding="utf-8")
        self.assertIn('id="help-contact-form"', html)
        self.assertIn('id="help-contact-message"', html)
        self.assertNotIn('id="help-contact-email"', html)
        self.assertIn("/api/contact", js)
        self.assertIn("help-contact-form", css)
        self.assertNotIn("sendFeedback", html)
        self.assertNotIn("sendFeedback", js)
        self.assertNotIn("LUCID_TUNER_APP", html)
        self.assertNotIn("GTM-NGS9TV67", html)

    def test_dockerfile_copies_contact(self) -> None:
        self.assertIn("COPY team-page/contact.py", DOCKERFILE.read_text(encoding="utf-8"))

    def test_ingest_url_allowlist(self) -> None:
        import sys

        team = str(ROOT / "team-page")
        if team not in sys.path:
            sys.path.insert(0, team)
        import contact as lch_contact

        self.assertEqual(
            lch_contact.ingest_url("https://app.lucidtuner.com/api/contact/submit"),
            "https://app.lucidtuner.com/api/contact/submit",
        )
        self.assertIsNone(lch_contact.ingest_url("https://evil.example/api/contact/submit"))
        self.assertIsNone(lch_contact.ingest_url("http://app.lucidtuner.com/api/contact/submit"))
        self.assertIsNone(lch_contact.ingest_url("https://app.lucidtuner.com/api/other"))

    def test_forward_payload_labels_house(self) -> None:
        import sys

        team = str(ROOT / "team-page")
        if team not in sys.path:
            sys.path.insert(0, team)
        import contact as lch_contact

        payload = lch_contact.build_forward_payload(
            {"message": "Hi", "email": "a@example.com", "name": "Jay"},
            host="house.example",
            path="/app",
            handle="jagcot",
            connected=True,
        )
        self.assertEqual(payload["product"], "lucid-cove-hermes")
        self.assertEqual(payload["host"], "house.example")
        self.assertEqual(payload["path"], "/app")
        self.assertEqual(payload["handle"], "jagcot")
        self.assertEqual(payload["connected"], "yes")
        self.assertEqual(payload["message"], "Hi")


if __name__ == "__main__":
    unittest.main()
