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
    "e01-v2-captions-v3.srt": "666f08f1a3fb151f0fbdb77cc1d52336418c45c6918a1cd7392048998537f171",
    "e01-v2-captions-v3.vtt": "07ca5a703731dfd4a304abba1f0e87ce3bdc5da91ce4d2281e818a7ccd6dbbc6",
    "e01-v2-karaoke-v3-qa.ass": "936988d60638e056d5d5a28853e87b6cf3f56aa6d0494081abb8630d87750ee3"
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
