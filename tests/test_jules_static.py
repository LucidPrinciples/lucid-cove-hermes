"""Jules page must ship the header/PWA assets it references."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JULES_HTML = ROOT / "team-page" / "static" / "jules.html"
STATIC = ROOT / "team-page" / "static"


class JulesStaticTests(unittest.TestCase):
    def test_jules_html_static_assets_exist(self):
        html = JULES_HTML.read_text(encoding="utf-8")
        refs = sorted(set(re.findall(r"/static/([A-Za-z0-9._/-]+\.(?:png|jpg|svg|ico|webp))", html)))
        self.assertIn("julian-icon.png", refs)
        missing = [name for name in refs if not (STATIC / name).is_file()]
        self.assertEqual(missing, [], f"jules.html references missing static files: {missing}")


if __name__ == "__main__":
    unittest.main()
