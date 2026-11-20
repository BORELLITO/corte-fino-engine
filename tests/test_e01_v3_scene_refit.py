import json
import unittest
from pathlib import Path

try:
    from PIL import ImageFont as _PIL
except ImportError:
    _PIL = None

from agents.e01_v3_scene_refit import MAX_SCENE, MIN_SCENE, OUT, STARTS, build
from agents.e01_v3_voice_captions import SPEECH_DURATION, load

needs_pillow = unittest.skipUnless(_PIL is not None, "Pillow is installed in the dedicated caption workflow")


class SceneRefitTests(unittest.TestCase):
    def setUp(self):
        self.c = json.loads(OUT.read_text(encoding="utf-8"))
        self.words, _ = load()

    def test_contiguous_and_covers_whole_voice(self):
        s = self.c["scenes"]
        self.assertEqual(len(s), 12)
        self.assertEqual(s[0]["start_seconds"], 0)
        self.assertEqual(s[-1]["end_seconds"], round(SPEECH_DURATION, 3))
        for a, b in zip(s, s[1:]):
            self.assertEqual(a["end_seconds"], b["start_seconds"])
        self.assertAlmostEqual(sum(x["duration_seconds"] for x in s), SPEECH_DURATION, places=2)

    def test_no_cut_inside_a_spoken_word_and_each_scene_starts_a_sentence(self):
        for n, i in enumerate(STARTS[1:], start=1):
            cut = self.c["scenes"][n]["start_seconds"]
            for w in self.words:
                self.assertFalse(w["start"] < cut < w["end"], (w["text"], cut))
            self.assertIn(self.words[i - 1]["text"][-1], ".?!")

    def test_scene_lengths_bounded_and_ids_preserved(self):
        old = json.loads(Path("contracts/e01_v2_12_scene_visual_plan_v1.json").read_text(encoding="utf-8"))["scenes"]
        self.assertEqual([x["id"] for x in self.c["scenes"]], [x["id"] for x in old])
        for x in self.c["scenes"]:
            self.assertGreaterEqual(x["duration_seconds"], MIN_SCENE)
            self.assertLessEqual(x["duration_seconds"], MAX_SCENE)
            self.assertEqual(x["needs_internal_shot_change"], x["duration_seconds"] >= 8.0)

    def test_timing_only_nothing_approved(self):
        for k in ("media_changed", "rights_changed", "approved_for_export", "publication_authorized"):
            self.assertIs(self.c[k], False)

    @needs_pillow
    def test_stored_contract_is_reproducible(self):
        self.assertEqual(build(), self.c)


if __name__ == "__main__":
    unittest.main()
