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
        self.assertEqual(d["speech_duration_seconds"], 76.67)
        self.assertEqual(d["provenance"]["audio_probe"]["file_sha256"],
                         "35f435199df54f6380d80d129ddd95b04ddb0ff5f97ede97a74da856995b5685")

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
        # exactly one lilac word per highlight event, never accumulated fill
        self.assertNotIn(r"\kf", ass)
        evs=[l for l in ass.splitlines() if l.startswith("Dialogue: 0")]
        self.assertTrue(all(l.count(r"{\1c&H00F2B0C4&}") <= 1 for l in evs))
        self.assertEqual(sum(l.count(r"{\1c&H00F2B0C4&}") for l in evs) >= 182, True)
        self.assertIn("00:01:16", srt)  # last caption near 76.7 s

    @unittest.skipUnless(_PIL is not None, "Pillow is installed in the dedicated caption workflow")
    def test_typography_rules_flag_known_residual_cues_only(self):
        from agents.e01_v2_caption_pipeline import make_cues
        words, duration = load()
        flagged=[c["index"] for c in make_cues(words, duration) if c.get("rule_violations")]
        # known residual cases are listed in docs/REGRAS_LEGENDA_VNC_V1.md
        self.assertLessEqual(len(flagged), 4)  # heuristic proposal quality floor

    @unittest.skipUnless(_PIL is not None, "Pillow is installed in the dedicated caption workflow")
    def test_curated_plan_matches_script_and_only_known_residual_is_flagged(self):
        from agents.e01_v2_caption_pipeline import make_cues_from_plan, text_width, MAX_LINE_PX
        from agents.e01_v3_voice_captions import PLAN
        words, duration = load()
        plan = json.loads(PLAN.read_text(encoding="utf-8"))["cues"]
        cues = make_cues_from_plan(words, plan, duration)
        self.assertEqual(sum(len(c["words"]) for c in cues), 182)
        self.assertTrue(all(text_width(l) <= MAX_LINE_PX for c in cues for l in c["lines"]))
        self.assertTrue(all(len(c["lines"]) <= 2 for c in cues))
        flagged = [(c["lines"], c["rule_violations"]) for c in cues if c.get("rule_violations")]
        self.assertEqual(flagged, [(["diante de uma", "sociedade ferida"],
                                    ["line_ends_on_function_word"])])

    @unittest.skipUnless(_PIL is not None, "Pillow is installed in the dedicated caption workflow")
    def test_displayed_text_has_only_necessary_punctuation(self):
        import re
        from agents.e01_v2_caption_pipeline import make_cues_from_plan
        from agents.e01_v3_voice_captions import PLAN
        words, duration = load()
        plan = json.loads(PLAN.read_text(encoding="utf-8"))["cues"]
        for c in make_cues_from_plan(words, plan, duration):
            text = " ".join(c["lines"])
            self.assertNotIn(".", text)                       # periods never shown
            self.assertFalse(re.search(r"[,:;]$", text))       # caption never ends with , : ;
            self.assertFalse(re.search(r"[—–\-…]", text))      # no dashes or ellipsis
            self.assertNotIn("  ", text)
            for line in c["lines"]:
                self.assertEqual(line, line.strip())
                self.assertFalse(re.match(r"^[,.:;?!]", line)) # no line starts with punctuation
        self.assertIn("estava ouvindo?", [" ".join(c["lines"]) for c in make_cues_from_plan(words, plan, duration)])


if __name__ == "__main__":
    unittest.main()
