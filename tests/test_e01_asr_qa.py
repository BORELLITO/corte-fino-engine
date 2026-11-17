"""Offline regression suite: accuracy metrics, adversarial ASR and release locks."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agents.content_production import ProductionError
from agents.e01_asr_qa import (
    DURATION, SCRIPT_HASH, WAV_SHA, REPORT_SHA,
    tokenize, edit_distance, compare_text, validate_timecodes, check_source,
    audit, MAX_WORD_ERROR_RATE, MAX_CHAR_ERROR_RATE, safe_stage_error,
)
from agents.e01_voice_preview import approved_source

ROOT = Path(__file__).resolve().parents[1]


def long_reference() -> str:
    text, _ = approved_source(ROOT)
    return text


def synthetic_timed_words(n: int = 20):
    return [{
        "start": 1.0, "end": 18.0,
        "text": " ".join(["palavra"] * n),
        "words": [
            {"start": round(1.0 + i*0.8, 3),
             "end": round(1.4 + i*0.8, 3),
             "word": "palavra", "probability": 0.91}
            for i in range(n)
        ],
    }]


class E01ASRTests(unittest.TestCase):
    def test_expected_wav_reference_is_pinned(self):
        self.assertEqual(len(WAV_SHA), 64)
        self.assertEqual(len(REPORT_SHA), 64)
        self.assertEqual(SCRIPT_HASH, approved_source(ROOT)[1]["script_sha256"])
        self.assertEqual(DURATION, 70.075)

    def test_accent_case_and_punctuation_normalization(self):
        self.assertEqual(tokenize("Você já? NÃo, É! 2026."), 
                         ["voce", "ja", "nao", "e", "2026"])

    def test_token_normalizer_does_not_discard_meaningful_negation(self):
        self.assertNotEqual(tokenize("não existe cura"), tokenize("existe cura"))

    def test_true_levenshtein_is_not_sequence_similarity(self):
        self.assertEqual(edit_distance(["eu", "não", "sei"], ["eu", "sei"]), 1)
        self.assertEqual(edit_distance("abc", "acb"), 2)
        self.assertEqual(edit_distance([], ["a", "b"]), 2)

    def test_exact_transcript_passes_provisional_only(self):
        q = compare_text(long_reference(), long_reference())
        self.assertEqual(q["word_error_rate"], 0)
        self.assertEqual(q["character_error_rate"], 0)
        self.assertEqual(q["potential_discrepancies"], [])
        self.assertTrue(q["thresholds_passed"])

    def test_ignores_case_and_accents_but_not_missing_words(self):
        ref = long_reference()
        same = ref.upper().replace("É", "E").replace("À", "A")
        self.assertTrue(compare_text(ref, same)["thresholds_passed"])
        missing = " ".join(tokenize(ref)[25:])
        self.assertFalse(compare_text(ref, missing)["thresholds_passed"])

    def test_long_consecutive_omission_blocks_despite_average_wer(self):
        tokens = tokenize(long_reference())
        # Losing 7 words out of ~200 can be below WER threshold but is still unsafe.
        changed = tokens[:33] + tokens[40:]
        quality = compare_text(long_reference(), " ".join(changed))
        self.assertGreaterEqual(quality["worst_potential_omission_words"], 7)
        self.assertFalse(quality["thresholds_passed"])

    def test_recognized_short_hallucination_is_not_falsely_approved(self):
        q = compare_text(long_reference(), "Deus prometeu dinheiro amanhã")
        self.assertFalse(q["thresholds_passed"])
        self.assertGreater(q["word_error_rate"], MAX_WORD_ERROR_RATE)
        self.assertGreater(q["character_error_rate"], MAX_CHAR_ERROR_RATE)

    def test_empty_or_huge_transcript_fails_closed(self):
        for hypo in ("", "a " * 1200):
            with self.subTest(hypo_len=len(hypo)):
                with self.assertRaises(ProductionError):
                    compare_text(long_reference(), hypo)

    def test_20_word_timecodes_are_valid_structure_only(self):
        q = validate_timecodes(synthetic_timed_words(), DURATION)
        self.assertTrue(q["word_timecodes_structurally_valid"])
        self.assertFalse(q["synced_final_caption_track"])
        self.assertEqual(q["words_with_timecodes"], 20)

    def test_missing_word_timestamps_fails(self):
        seg = synthetic_timed_words()
        seg[0]["words"] = []
        with self.assertRaisesRegex(ProductionError, "word_level_timecodes_missing"):
            validate_timecodes(seg, DURATION)

    def test_word_out_of_audio_bounds_fails(self):
        seg = synthetic_timed_words()
        seg[0]["words"][5]["end"] = DURATION + 4
        with self.assertRaisesRegex(ProductionError, "invalid_word_timing_or_probability"):
            validate_timecodes(seg, DURATION)

    def test_nan_and_out_of_range_probabilities_fail(self):
        for value in (-0.1, 1.2, float("nan")):
            seg = synthetic_timed_words()
            seg[0]["words"][3]["probability"] = value
            with self.subTest(value=value):
                with self.assertRaisesRegex(ProductionError, "invalid_word_timing_or_probability"):
                    validate_timecodes(seg, DURATION)

    def test_inverted_segment_time_fails(self):
        seg = synthetic_timed_words()
        seg[0]["end"] = seg[0]["start"] - 1
        with self.assertRaisesRegex(ProductionError, "invalid_segment_time"):
            validate_timecodes(seg, DURATION)

    def test_backend_failures_disclose_stage_not_private_error_text(self):
        unsafe = RuntimeError("unable to open file /home/runner/token=SECRET")
        x = safe_stage_error("model_load", unsafe)
        self.assertIn("asr:model_load:MODEL_FILE_UNAVAILABLE", str(x))
        self.assertNotIn("SECRET", str(x))
        self.assertNotIn("/home/", str(x))

    def test_missing_real_audio_artifact_fails(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ProductionError, "source_artifact_missing"):
                check_source(ROOT, Path(d))

    def test_wrong_audio_and_report_bytes_never_activate_asr(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p/"e01-preview-only.wav").write_bytes(b"RIFF fake")
            (p/"report.json").write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ProductionError, "source_artifact_sha256_or_size_mismatch"):
                check_source(ROOT, p)

    def test_mismatched_asr_inference_does_not_unlock_release(self):
        with patch("agents.e01_asr_qa.check_source", return_value=(Path("/tmp/dummy.wav"), long_reference())), \
             patch("agents.e01_asr_qa.run_independent_asr", return_value=(
                 synthetic_timed_words(), {"repository": "dummy", "language_detected_independently": False}
             )):
            out = audit(ROOT, Path("/tmp"), Path("/tmp"))
        self.assertEqual(out["status"], "BLOCKED_ASR_DISCREPANCIES")
        self.assertFalse(out["production_audio_master_approved"])
        self.assertFalse(out["publication_authorized"])
        self.assertTrue(out["blockers"])

    def test_even_perfect_asr_not_final_master_or_license(self):
        reference = long_reference()
        words = tokenize(reference)
        segs = synthetic_timed_words(len(words))
        # Mark synthetic words against real script: ASR text matches, but timestamps
        # require placement inside the real audio; allocate a safe time grid.
        n = len(words)
        for i, w in enumerate(segs[0]["words"]):
            w["start"] = round(1.0 + i * 63 / n, 3)
            w["end"] = round(1.0 + (i+0.8) * 63 / n, 3)
            w["word"] = words[i]
        segs[0]["text"] = reference
        segs[0]["end"] = DURATION
        with patch("agents.e01_asr_qa.check_source", return_value=(Path("/tmp/dummy.wav"), reference)), \
             patch("agents.e01_asr_qa.run_independent_asr", return_value=(
                 segs, {"repository": "mock", "initial_prompt_used": False}
             )):
            out = audit(ROOT, Path("/tmp"), Path("/tmp"))
        self.assertEqual(out["status"], "ASR_PROVISIONAL_SCRIPT_MATCH_QUARANTINED")
        self.assertTrue(out["asr_fidelity_provisionally_passed"])
        self.assertFalse(out["human_listening_completed"])
        self.assertFalse(out["pronunciation_quality_fully_cleared"])
        self.assertFalse(out["final_caption_sync_approved"])
        self.assertFalse(out["voice_rights_cleared"])
        self.assertFalse(out["production_audio_master_approved"])
        self.assertFalse(out["rendered_final_video_exists"])
        self.assertFalse(out["publication_authorized"])


if __name__ == "__main__":
    unittest.main()
