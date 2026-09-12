"""Inbox path safety + PROPFIND parse (no live Nextcloud)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "team-page"))

import jules_nc  # noqa: E402

DAV_XML = """<?xml version="1.0"?>
<d:multistatus xmlns:d="DAV:">
  <d:response>
    <d:href>/remote.php/dav/files/stewart/AgentSkills/Inbox</d:href>
    <d:propstat><d:prop><d:resourcetype><d:collection/></d:resourcetype></d:prop></d:propstat>
  </d:response>
  <d:response>
    <d:href>/remote.php/dav/files/stewart/AgentSkills/Inbox/note.md</d:href>
    <d:propstat><d:prop><d:resourcetype/></d:prop></d:propstat>
  </d:response>
  <d:response>
    <d:href>/remote.php/dav/files/stewart/AgentSkills/Inbox/Screenshot%202026-09-06%20at%209.46.03.png</d:href>
    <d:propstat><d:prop><d:resourcetype/></d:prop></d:propstat>
  </d:response>
  <d:response>
    <d:href>/remote.php/dav/files/stewart/AgentSkills/Inbox/LUCID_TUNER_APP/api.js</d:href>
    <d:propstat><d:prop><d:resourcetype/></d:prop></d:propstat>
  </d:response>
  <d:response>
    <d:href>/remote.php/dav/files/stewart/AgentSkills/Inbox/LUCID_TUNER_APP/.git/HEAD</d:href>
    <d:propstat><d:prop><d:resourcetype/></d:prop></d:propstat>
  </d:response>
  <d:response>
    <d:href>/remote.php/dav/files/stewart/AgentSkills/Inbox/Archive/old.md</d:href>
    <d:propstat><d:prop><d:resourcetype/></d:prop></d:propstat>
  </d:response>
  <d:response>
    <d:href>/remote.php/dav/files/stewart/AgentSkills/Inbox/../etc/passwd</d:href>
    <d:propstat><d:prop><d:resourcetype/></d:prop></d:propstat>
  </d:response>
  <d:response>
    <d:href>/remote.php/dav/files/stewart/AgentSkills/Inbox/shots</d:href>
    <d:propstat><d:prop><d:resourcetype><d:collection/></d:resourcetype></d:prop></d:propstat>
  </d:response>
</d:multistatus>
"""


class InboxPathTests(unittest.TestCase):
    def test_safe_rel_accepts_nested_and_screenshot(self):
        self.assertEqual(jules_nc.safe_inbox_rel("note.md"), "note.md")
        self.assertEqual(jules_nc.safe_inbox_rel("LUCID_TUNER_APP/api.js"), "LUCID_TUNER_APP/api.js")
        self.assertEqual(
            jules_nc.safe_inbox_rel("Screenshot 2026-09-06 at 9.46.03 PM.png"),
            "Screenshot 2026-09-06 at 9.46.03 PM.png",
        )

    def test_safe_rel_rejects_traversal(self):
        self.assertIsNone(jules_nc.safe_inbox_rel("../x"))
        self.assertIsNone(jules_nc.safe_inbox_rel("foo/bar/../etc"))
        self.assertIsNone(jules_nc.safe_inbox_rel("Name/../Other"))
        self.assertIsNone(jules_nc.safe_inbox_rel("/etc/passwd"))
        self.assertIsNone(jules_nc.safe_inbox_rel(""))
        self.assertIsNone(jules_nc.safe_inbox_rel("foo/../../etc/passwd"))
        self.assertIsNone(jules_nc.safe_inbox_rel("~/secret"))
        self.assertIsNone(jules_nc.safe_inbox_rel("a.png\r\nSet-Cookie: x"))
        self.assertIsNone(jules_nc.safe_inbox_rel("foo\nbar.md"))

    def test_parse_propfind_skips_git_archive_dirs(self):
        files = jules_nc.parse_inbox_propfind(DAV_XML)
        self.assertEqual(
            files,
            [
                "note.md",
                "Screenshot 2026-09-06 at 9.46.03.png",
                "LUCID_TUNER_APP/api.js",
            ],
        )

    def test_image_and_text_types(self):
        self.assertTrue(jules_nc.is_image("shot.PNG"))
        self.assertTrue(jules_nc.is_image("a/b/c.webp"))
        self.assertFalse(jules_nc.is_image("note.md"))
        self.assertTrue(jules_nc.is_text("LUCID_TUNER_APP/api.js"))
        self.assertTrue(jules_nc.is_text(".gitignore"))
        self.assertFalse(jules_nc.is_text("clip.webm"))
        self.assertEqual(jules_nc.guess_media_type("x.png"), "image/png")

    def test_quote_path_keeps_slashes(self):
        quoted = jules_nc._quote_path("LUCID_TUNER_APP/api.js")
        self.assertEqual(quoted, "LUCID_TUNER_APP/api.js")
        spaced = jules_nc._quote_path("Screenshot 1.png")
        self.assertEqual(spaced, "Screenshot%201.png")
        self.assertNotIn("..", jules_nc._quote_path("a/b"))

    def test_content_disposition_latin1_and_rfc5987(self):
        name = "Screenshot 2026-09-06 at 9.45.45\u202fPM.png"
        header = jules_nc.content_disposition_inline(name)
        header.encode("latin-1")
        self.assertIn('filename="Screenshot 2026-09-06 at 9.45.45_PM.png"', header)
        self.assertIn("filename*=UTF-8''", header)
        self.assertIn("%E2%80%AF", header)
        ascii_header = jules_nc.content_disposition_inline("IMG_8149.PNG")
        ascii_header.encode("latin-1")
        self.assertIn('filename="IMG_8149.PNG"', ascii_header)
        self.assertNotIn("\r", header)
        self.assertNotIn("\n", header)


if __name__ == "__main__":
    unittest.main()
