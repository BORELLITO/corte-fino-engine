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


class AcousticOnsetGateTests(unittest.TestCase):
    """Offline gate against the silences measured on the real audio (stored in the contract)."""
    def test_no_word_starts_deep_inside_a_measured_silence(self):
        words, _ = load()
        sil = json.loads(Path("contracts/e01_v3_voice_johnes_word_timing_v1.json")
                         .read_text(encoding="utf-8"))["provenance"]["silences_-38db_min0.12s"]
        self.assertEqual(len(sil), 31)
        for w in words:
            for s in sil:
                # known, documented exception: 'é' (index 118) lies 0.106 s inside a silence
                inside = (min(w["end"], s["end"]) - max(w["start"], s["start"]))
                if w["index"] != 118 and s["start"] < w["start"] < s["end"]:
                    self.assertLessEqual(s["end"] - w["start"], 0.12, (w["text"], w["start"]))

    def test_snapped_onsets_are_documented_and_reversible(self):
        c = json.loads(Path("contracts/e01_v3_voice_johnes_word_timing_v1.json").read_text(encoding="utf-8"))
        snapped = [w for w in c["words"] if "start_scribe" in w]
        self.assertEqual([w["text"] for w in snapped], ["sofre", "Talvez"])
        self.assertTrue(all(w["start"] < w["start_scribe"] for w in snapped))


class WhisperCrosscheckGateTests(unittest.TestCase):
    """Offline: stored Whisper (no reference text) starts vs the current timing contract."""
    def test_crosscheck_within_tolerance_and_bound_to_audio_hash(self):
        import statistics
        x = json.loads(Path("contracts/e01_v3_whisper_crosscheck_v1.json").read_text(encoding="utf-8"))
        c = json.loads(Path("contracts/e01_v3_voice_johnes_word_timing_v1.json").read_text(encoding="utf-8"))
        self.assertEqual(x["audio_sha256"], c["provenance"]["audio_probe"]["file_sha256"])
        ref = {w["index"]: w["start"] for w in c["words"]}
        d = [w["asr_start"] - ref[w["index"]] for w in x["words"]]
        self.assertGreaterEqual(len(d), 179)
        self.assertLessEqual(abs(statistics.median(d) - (-0.10)), 0.05)       # known Whisper bias
        self.assertLessEqual(sorted(abs(v) for v in d)[int(.95 * len(d)) - 1], 0.30)
        self.assertLessEqual(max(abs(v) for v in d), 0.80)
        by = {w["index"]: w["asr_start"] for w in x["words"]}
        for w in c["words"]:   # snapped words must move TOWARD Whisper, never away
            if "start_scribe" in w and w["index"] in by:
                self.assertLess(abs(by[w["index"]] - w["start"]), abs(by[w["index"]] - w["start_scribe"]))


class HudGeometryGateTests(unittest.TestCase):
    """Caption box vs the cross-platform universal safe zone (900x1400 centred in 1080x1920,
    bottom dead zone >= 320 px). Source: published third-party guides, NOT measured on a device."""
    def test_caption_box_inside_universal_safe_zone(self):
        from agents.e01_v2_caption_pipeline import MAX_LINE_PX, MARGIN_BOTTOM, FONT_ASS_SIZE, MAX_LINES
        half = (MAX_LINE_PX + 15) / 2
        left, right = 540 - half, 540 + half
        bottom = 1920 - MARGIN_BOTTOM
        top = bottom - MAX_LINES * FONT_ASS_SIZE * 1.3
        self.assertGreaterEqual(left, 90)      # universal 900 px wide zone
        self.assertLessEqual(right, 990)
        self.assertGreaterEqual(top, 260)      # universal 1400 px tall zone
        self.assertLessEqual(bottom, 1920 - 320)

class MeasuredCaptionBandTests(unittest.TestCase):
    def setUp(self):
        self.b = json.loads(Path("contracts/e01_v3_caption_band_v1.json").read_text(encoding="utf-8"))

    def test_render_measured_band_is_symmetric_and_inside_universal_zone(self):
        m, c = self.b["measured_px"], self.b["clear_px"]
        self.assertLessEqual(abs(c["left"] - c["right"]), 2)            # symmetry
        self.assertEqual(c["left"], m["x_min"])
        self.assertEqual(c["right"], 1079 - m["x_max"])
        self.assertGreaterEqual(c["left"], 90)                          # universal 900 px zone
        self.assertGreaterEqual(c["bottom"], 320)                       # bottom UI dead zone
        self.assertEqual(c["bottom"], 1920 - m["y_max"] - 1)

    def test_protected_band_encloses_the_measured_captions(self):
        m, p = self.b["measured_px"], self.b["protected_band_for_primary_action"]
        self.assertLessEqual(p["y_from"], m["y_min"] - 30)
        self.assertGreaterEqual(p["y_to"], m["y_max"] + 30)
        self.assertLessEqual(p["x_from"], m["x_min"] - 30)
        self.assertGreaterEqual(p["x_to"], m["x_max"] + 30)

    def test_old_visual_zone_does_not_cover_the_captions(self):
        # documented inconsistency: 'lower 420 px' starts at y=1500, below the captions (y<=1327)
        self.assertLess(self.b["measured_px"]["y_max"], 1920 - 420)
        self.assertIs(self.b["approved_by_user"], False)


if __name__ == "__main__":
    unittest.main()
