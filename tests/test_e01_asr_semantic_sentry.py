import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agents.content_production import ProductionError
from agents.e01_asr_semantic_sentry import (
    CRITICAL_WORDS, EXPECTED_REPORT_SHA, EXPECTED_REPORT_BYTES,
    evaluate_wording, validate_original_asr, main,
)


class CriticalASRSemanticSentryTests(unittest.TestCase):
    def test_doi_versus_dou_is_critical_even_when_meaning_similar(self):
        r = evaluate_wording(
            "Às vezes, dói esperar. Dói ainda mais ver injustiças.",
            "Às vezes, dou esperar. Dói ainda mais ver injustiças.")
        self.assertEqual(r["status"], "BLOCKED_CRITICAL_WORDING_NEEDS_AUDIO_RECHECK")
        self.assertEqual(r["critical_word_alerts"][0]["word"], "doi")
        self.assertEqual(r["critical_word_alerts"][0]["missing_instances"], 1)
        self.assertFalse(r["tts_defect_proven"])
        self.assertFalse(r["publication_authorized"])

    def test_negation_loss_cannot_hide_behind_wer(self):
        r = evaluate_wording("Deus não garante isso.", "Deus garante isso.")
        self.assertTrue(any(w["word"] == "nao" for w in r["critical_word_alerts"]))
        self.assertTrue(r["requires_secondary_evidence_for_disambiguation"])

    def test_sentence_ending_on_preposition_is_flagged(self):
        r = evaluate_wording(
            "É bom ajudar em favor de alguém. E pode orar.",
            "É bom ajudar em favor de. Alguém pode orar.")
        self.assertGreaterEqual(r["number_of_sentence_boundary_alerts"], 1)
        self.assertFalse(r["production_audio_master_approved"])

    def test_punctuation_mere_pause_not_always_flag(self):
        r = evaluate_wording("A fé não precisa fingir.", "A fé não precisa fingir.")
        self.assertEqual(r["status"], "NO_CRITICAL_WORDING_ALERTS_IN_THIS_GATE")
        self.assertFalse(r["human_listening_qa_completed"])
        self.assertFalse(r["voice_rights_cleared"])

    def test_habacuque_silent_h_is_not_false_hard_critical(self):
        self.assertNotIn("habacuque", CRITICAL_WORDS)
        r = evaluate_wording("Habacuque denuncia violência.", "Abacuque denuncia violência.")
        self.assertEqual(r["number_of_critical_word_alerts"], 0)
        self.assertEqual(r["number_of_sentence_boundary_alerts"], 0)

    def test_missing_divine_or_contextual_terms_block(self):
        original = "Deus denuncia violência, a injustiça e a falta de esperança."
        recognized = "denuncia a falta"
        r = evaluate_wording(original, recognized)
        labels = {x["word"] for x in r["critical_word_alerts"]}
        self.assertTrue({"deus", "violencia", "injustica", "esperanca"} <= labels)

    def test_never_auto_approves_master_even_when_strings_match(self):
        r = evaluate_wording("Verdade e esperança.", "Verdade e esperança.")
        self.assertFalse(r["production_audio_master_approved"])
        self.assertFalse(r["publication_authorized"])
        self.assertFalse(r["tts_defect_proven"])

    def test_forged_untethered_json_report_cannot_pass_source_sha(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = root / "report.json"
            src.write_text('{"status":"ASR_PROVISIONAL_SCRIPT_MATCH_QUARANTINED"}',
                           encoding="utf-8")
            with self.assertRaisesRegex(ProductionError, "source_report_size"):
                validate_original_asr(root, src)

    def test_correct_size_but_wrong_bytes_must_fail_sha(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = root / "report.json"
            src.write_bytes(b"x" * EXPECTED_REPORT_BYTES)
            with self.assertRaisesRegex(ProductionError, "source_report_digest"):
                validate_original_asr(root, src)

    def test_pinned_first_asr_provenance_cannot_claim_full_audio_qa(self):
        root = Path(__file__).resolve().parents[1]
        j = json.loads((root / "contracts/e01_asr_real_evidence_v1.json")
                       .read_text(encoding="utf-8"))
        self.assertEqual(j["source_workflow_run_id"], 44201071884)
        self.assertEqual(j["source_report_sha256"], EXPECTED_REPORT_SHA)
        self.assertEqual(j["source_report_bytes"], EXPECTED_REPORT_BYTES)
        self.assertEqual(j["asr_model_repository"], "Systran/faster-whisper-small")
        self.assertEqual(j["word_error_rate"], 0.02747)
        self.assertFalse(j["critical_semantic_recheck_completed"])
        self.assertFalse(j["production_audio_master_approved"])
        self.assertFalse(j["publication_authorized"])

    def test_entrypoint_persists_truthful_blocked_report_on_missing_source(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "result.json"
            with patch.object(sys, "argv", [
                "asr_sentry", "--root", str(Path(d)),
                "--input-file", str(Path(d) / "missing.json"),
                "--output", str(out),
            ]):
                self.assertEqual(main(), 2)
            record = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(record["status"], "BLOCKED_SEMANTIC_ASR_EVIDENCE_INVALID")
            self.assertFalse(record["publication_authorized"])
            self.assertFalse(record["production_audio_master_approved"])


if __name__ == "__main__":
    unittest.main()
