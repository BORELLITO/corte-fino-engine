"""Deterministic v3 caption outputs built from the pinned real word timing."""
import tempfile
import unittest
from pathlib import Path

try:
    from PIL import ImageFont as _PIL
except ImportError:
    _PIL = None
needs_pillow = unittest.skipUnless(
    _PIL is not None, "Pillow is installed in the dedicated caption workflow")
from agents.e01_v2_caption_from_real_timing import build

EXPECTED = {
    "e01-v2-captions-v3.srt": "bfee8ca546e9a536c1ddc2592d3e6c241fb254c8116c83215456561c83ea8a99",
    "e01-v2-captions-v3.vtt": "40be595a620ce70635e046a449ec9065ca5c7a4c1fbea6980998d8e19a2bc986",
    "e01-v2-karaoke-v3-qa.ass": "609127a8ac74eca1c9e1fcc407509c084f11fea8f9db312934301d27294277b3"
}


class RealTimingCaptionBuildTests(unittest.TestCase):
    @needs_pillow
    def test_outputs_pinned_and_complete(self):
        with tempfile.TemporaryDirectory() as d:
            digests = build(Path(d))
            self.assertEqual(digests, EXPECTED)
            ass = (Path(d) / "e01-v2-karaoke-v3-qa.ass").read_text(encoding="utf-8")
            self.assertIn("PRÉVIA TÉCNICA - NÃO PUBLICAR", ass)
            self.assertNotIn("\\kf", ass)  # no accumulated fill: one lilac word at a time
            self.assertGreaterEqual(ass.count("{\\1c&H00F2B0C4&}"), 182)


if __name__ == "__main__":
    unittest.main()
