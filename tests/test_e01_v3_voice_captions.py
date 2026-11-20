"""Voice candidate (Johnes Bittar) timing contract and caption build."""
import json
import tempfile
import unittest
from pathlib import Path

from agents.content_production import ProductionError
from agents.e01_v3_voice_captions import CONTRACT, SPEECH_DURATION, build, load

try:
    from PIL import ImageFont as _PIL
except ImportError:
    _PIL = None

ROOT = Path(__file__).resolve().parents[1]


class VoiceCandidateTests(unittest.TestCase):
    def test_contract_is_candidate_only(self):
        d = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertFalse(d["voice_rights_cleared"])
        self.assertFalse(d["production_audio_master_approved"])
        self.assertFalse(d["publication_authorized"])
        self.assertEqual(d["word_count"], 182)
        self.assertEqual(d["speech_duration_seconds"], 76.72)

    def test_words_equal_canonical_script_and_are_ordered(self):
        words, duration = load()
        self.assertEqual(len(words), 182)
        self.assertEqual(duration, SPEECH_DURATION)
        self.assertEqual(words[-1]["text"], "esperança.")
        self.assertTrue(all(a["end"] <= b["start"] + 0.001
                            for a, b in zip(words, words[1:])))

    def test_tampered_text_is_refused(self):
        d = json.loads(CONTRACT.read_text(encoding="utf-8"))
        d["words"][3]["text"] = "outra"
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "x.json"
            p.write_text(json.dumps(d), encoding="utf-8")
            with self.assertRaisesRegex(ProductionError, "differs_from_canonical"):
                load(p)

    @unittest.skipUnless(_PIL is not None, "Pillow is installed in the dedicated caption workflow")
    def test_builds_karaoke_with_exact_word_times(self):
        import re
        with tempfile.TemporaryDirectory() as t:
            build(Path(t))
            ass = (Path(t) / "e01-v3-johnes-karaoke-qa.ass").read_text(encoding="utf-8")
            srt = (Path(t) / "e01-v3-johnes-captions.srt").read_text(encoding="utf-8")
        self.assertIn("Atkinson Hyperlegible Next", ass)
        n_kf = len(re.findall(r"\{\\kf\d+\}", ass))
        self.assertEqual(n_kf, 182)
        self.assertIn("00:01:16", srt)  # last caption near 76.7 s


if __name__ == "__main__":
    unittest.main()
