import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agents.content_production import ProductionError
from agents.e01_asr_qa import REPO, SECOND_OPINION_REPO
from agents.e01_v2_dual_asr import (
    REQUIRED_CORRECTION, ORIGINAL_PRODUCER_RUN_ID,
    SOURCE_CONTRACT, contains_phrase, adjudicate, source_check,
)
from agents.e01_v2_candidate import V2_SHA, PARENT_SHA


def model_result(repository, phrase=True, pass_text=True, warnings=None):
    return {
        "model": {"repository": repository, "model_bin_sha256": "0"*64},
        "new_pronunciation_safe_phrase_recognized": phrase,
        "fidelity_estimates": {"thresholds_passed": pass_text, "word_error_rate": 0.025},
        "timecodes": {"word_timecodes_structurally_valid": True},
        "critical_word_alerts": {
            "critical_word_alerts": [{"word": x} for x in (warnings or [])],
            "sentence_boundary_alerts": [],
        },
    }


class V2DualASRTests(unittest.TestCase):
    def test_replacement_phrase_recognizer_strict_but_accents_normalized(self):
        self.assertTrue(contains_phrase("Às vezes, esperar machuca. Dói ainda mais."))
        self.assertFalse(contains_phrase("Às vezes, esperar machucou. Dói ainda mais."))
        self.assertFalse(contains_phrase("Às vezes, machuca esperar."))

    def test_two_model_correct_phrase_text_triage_passes_not_release(self):
        models=[model_result(REPO), model_result(SECOND_OPINION_REPO)]
        result=adjudicate(models)
        self.assertEqual(result["status"], "ASR_V2_TWO_MODEL_TEXT_TRIAGE_PASS_STILL_QUARANTINED")
        self.assertTrue(result["both_models_recognized_exact_replacement"])
        self.assertTrue(result["provisional_text_gate_passed"])
        self.assertFalse(result["production_audio_master_approved"])
        self.assertFalse(result["voice_rights_cleared"])
        self.assertFalse(result["publication_authorized"])

    def test_one_model_misses_replacement_blocks(self):
        models=[model_result(REPO), model_result(SECOND_OPINION_REPO, phrase=False)]
        r=adjudicate(models)
        self.assertEqual(r["status"], "BLOCKED_V2_TEXT_OR_CRITICAL_WORD_DISCREPANCY")
        self.assertFalse(r["provisional_text_gate_passed"])

    def test_one_model_global_text_mismatch_blocks(self):
        models=[model_result(REPO), model_result(SECOND_OPINION_REPO, pass_text=False)]
        self.assertFalse(adjudicate(models)["provisional_text_gate_passed"])

    def test_shared_critical_words_block_even_with_low_wer(self):
        models=[model_result(REPO,warnings=["doi"]),
                model_result(SECOND_OPINION_REPO,warnings=["doi"])]
        r=adjudicate(models)
        self.assertFalse(r["provisional_text_gate_passed"])
        self.assertEqual(r["shared_critical_word_warnings"], ["doi"])

    def test_one_asr_warning_does_not_claim_proven_error(self):
        models=[model_result(REPO,warnings=["doi"]),
                model_result(SECOND_OPINION_REPO)]
        r=adjudicate(models)
        self.assertTrue(r["provisional_text_gate_passed"])
        self.assertFalse(r["practical_pronunciation_or_prosody_quality_guaranteed"])

    def test_two_identical_weight_sets_rejected(self):
        models=[model_result(REPO), model_result(REPO)]
        with self.assertRaisesRegex(ProductionError, "not_two_distinct_model_weights"):
            adjudicate(models)

    def test_no_pinned_v2_wav_contract_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            with self.assertRaisesRegex(ProductionError, "missing_physical_voice_artifact"):
                source_check(root, root)

    def test_v2_asr_requires_separate_contract_after_real_wav(self):
        self.assertEqual(SOURCE_CONTRACT, "contracts/e01_v2_voice_preview_evidence_v1.json")
        self.assertEqual(ORIGINAL_PRODUCER_RUN_ID, 44204100486)
        self.assertNotEqual(V2_SHA, PARENT_SHA)
        self.assertEqual(REQUIRED_CORRECTION, ["esperar", "machuca"])


if __name__ == "__main__":
    unittest.main()
