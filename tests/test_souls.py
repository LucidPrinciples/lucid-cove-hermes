"""Stdlib tests for public observer SOUL fields (no FastAPI required)."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "team-page"))

from souls import avatar_url, load_soul, parse_soul  # noqa: E402

STEWART = (ROOT / "pack" / "souls" / "Stewart.Cove.md").read_text(encoding="utf-8")
ALFRED = (ROOT / "pack" / "souls" / "Alfred.Cove.md").read_text(encoding="utf-8")


class ParseSoulTests(unittest.TestCase):
    def test_stewart_who_role_frequency(self):
        p = parse_soul(STEWART)
        self.assertEqual(p["name"], "Stewart")
        self.assertIn("Steward", p["role"])
        self.assertEqual(p["frequency"], "Peace")
        self.assertIn("Training Ground", p["archetype"])
        self.assertIn("coordinates the house team", p["who"])
        self.assertNotIn("Identity (hard)", p["who"])
        self.assertNotIn("Never claim to be Jason", p["who"])
        self.assertNotIn("Boundaries", p["who"])

    def test_alfred_without_frequency(self):
        p = parse_soul(ALFRED)
        self.assertEqual(p["name"], "")
        self.assertIn("Personal agent", p["role"])
        self.assertEqual(p["frequency"], "")
        self.assertEqual(p["archetype"], "")
        self.assertIn("personal agent inside this Cove", p["who"])
        self.assertNotIn("Does not pretend to be Stewart", p["who"])

    def test_load_soul_from_pack(self):
        soul = load_soul(ROOT / "pack", "Stewart")
        self.assertIsNotNone(soul)
        self.assertEqual(soul["name"], "Stewart")
        self.assertIsNone(load_soul(ROOT / "pack", "Nobody"))

    def test_load_soul_rejects_path_traversal(self):
        pack = ROOT / "pack"
        self.assertIsNone(load_soul(pack, "../x"))
        self.assertIsNone(load_soul(pack, "foo/bar"))
        self.assertIsNone(load_soul(pack, "Stewart/../Alfred"))
        soul = load_soul(pack, "Stewart")
        self.assertIsNotNone(soul)
        self.assertEqual(soul["name"], "Stewart")

    def test_avatar_url_present_and_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            static = Path(tmp)
            (static / "avatars").mkdir()
            (static / "avatars" / "stewart.png").write_bytes(b"png")
            self.assertEqual(avatar_url(static, "stewart"), "/static/avatars/stewart.png")
            self.assertIsNone(avatar_url(static, "alfred"))
            self.assertIsNone(avatar_url(static, "../etc/passwd"))

    def test_every_pack_soul_has_public_who(self):
        missing = []
        for path in sorted((ROOT / "pack" / "souls").glob("*.Cove.md")):
            who = parse_soul(path.read_text(encoding="utf-8"))["who"].strip()
            if not who:
                missing.append(path.name)
            else:
                self.assertNotIn("Identity (hard)", who, path.name)
        self.assertEqual(missing, [], "observer Who is empty without a ## Who section")

    def test_archimedes_who_is_public_builder(self):
        text = (ROOT / "pack" / "souls" / "Archimedes.Cove.md").read_text(encoding="utf-8")
        who = parse_soul(text)["who"]
        self.assertIn("builder", who.lower())
        self.assertNotIn("You are Archimedes", who)
        self.assertNotIn("Identity (hard)", who)


if __name__ == "__main__":
    unittest.main()
