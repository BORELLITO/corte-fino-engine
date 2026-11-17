import copy
import json
import tempfile
import unittest
from pathlib import Path

from agents.content_production import ProductionError
from agents.e01_second_asr_opinion import (
    SECOND_OPINION_REPO, FIRST_SENTRY_SHA, FIRST_SENTRY_BYTES,
    adjudicate, load_first_sentry,
)


def flags(words=None, boundaries=0):
    return {
        "critical_word_alerts": [{"word": word} for word in (words or [])],
        "sentence_boundary_alerts": [{"asr_excerpt": "stub"}] * boundaries,
    }


class SecondOpinionTests(unittest.TestCase):
    def test_base_repo_is_multilingual_not_english_only(self):
        self.assertEqual(SECOND_OPINION_REPO, "Systran/faster-whisper-base")
        self.assertNotIn(".en", SECOND_OPINION_REPO)

    def test_second_model_reproduces_doi_warning(self):
        record = adjudicate(flags(["doi"], 0), flags(["doi"], 0))
        self.assertEqual(record["status"], "POSSIBLE_VOICE_ISSUE_CORROBORATED_BY_SECOND_ASR")
        self.assertEqual(record["shared_critical_word_alerts"], ["doi"])
        self.assertFalse(record["corroboration_does_not_prove_tts_defect"] is False)
        self.assertFalse(record["publication_authorized"])

    def test_same_bad_sentence_boundary_is_recheck_only(self):
        record = adjudicate(flags(boundaries=1), flags(boundaries=1))
        self.assertEqual(record["status"], "POSSIBLE_VOICE_ISSUE_CORROBORATED_BY_SECOND_ASR")
        self.assertFalse(record["master_approved"])

    def test_secondary_model_recognizes_expected_phrase_but_disagreement_remains(self):
        record = adjudicate(flags(["doi"], 1), flags([], 0))
        self.assertEqual(record["status"], "SECOND_ASR_HEARD_CRITICAL_WORDS_SMALL_MODEL_DISAGREES")
        self.assertTrue(record["disagreement_does_not_prove_tts_is_correct"])
        self.assertFalse(record["extra_video_or_audio_rights_granted"])

    def test_nonoverlapping_critical_errors_remain_uncertain(self):
        record = adjudicate(flags(["doi"]), flags(["esperanca"]))
        self.assertEqual(record["status"], "DIFFERENT_ASR_ERRORS_NO_CONFIDENT_RESOLUTION")
        self.assertFalse(record["master_approved"])

    def test_both_clean_status_does_not_authorize_publication(self):
        record = adjudicate(flags(), flags())
        self.assertEqual(record["status"], "NO_CRITICAL_WORDING_ALERTS_BOTH_MODELS")
        self.assertFalse(record["publication_authorized"])

    def test_missing_sentry_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ProductionError, "original_sentry_size"):
                load_first_sentry(Path(tmp)/"missing.json")

    def test_fake_sentry_equal_length_is_blocked_by_sha(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"report.json"
            path.write_bytes(b"0" * FIRST_SENTRY_BYTES)
            with self.assertRaisesRegex(ProductionError, "original_sentry_sha"):
                load_first_sentry(path)

    def test_first_sentry_hash_is_full_64_lower_hex(self):
        self.assertEqual(len(FIRST_SENTRY_SHA), 64)
        self.assertEqual(FIRST_SENTRY_SHA, FIRST_SENTRY_SHA.lower())


if __name__ == "__main__":
    unittest.main()
