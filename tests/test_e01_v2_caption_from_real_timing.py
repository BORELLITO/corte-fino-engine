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
    "e01-v2-captions-v3.srt": "65d72e3fe4a0b58e92b33e344dafe2c5686f467c82e94e883816df4e2e35e10c",
    "e01-v2-captions-v3.vtt": "9e8aaa699564572b9be999157d19268c4204d8105616d46844c7b360fee496be",
    "e01-v2-karaoke-v3-qa.ass": "21a362e0854af64d727757f083cbff0bce8479f09078baf5525efac261f27d40",
}


class RealTimingCaptionBuildTests(unittest.TestCase):
    @needs_pillow
    def test_outputs_pinned_and_complete(self):
        with tempfile.TemporaryDirectory() as d:
            digests = build(Path(d))
            self.assertEqual(digests, EXPECTED)
            ass = (Path(d) / "e01-v2-karaoke-v3-qa.ass").read_text(encoding="utf-8")
            self.assertIn("PRÉVIA TÉCNICA - NÃO PUBLICAR", ass)
            self.assertEqual(ass.count("{\\kf"), 182)


if __name__ == "__main__":
    unittest.main()
