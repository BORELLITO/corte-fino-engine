import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agents.content_production import ProductionError
from agents.e01_v2_asr_attestation import verify_report, REPORT_BYTES, REPORT_SHA, EVIDENCE


class E01V2ASRAttestationTests(unittest.TestCase):
    def test_immutable_source_expected_sha_is_full_length(self):
        self.assertEqual(len(REPORT_SHA), 64)
        self.assertEqual(REPORT_BYTES, 72475)
        self.assertEqual(EVIDENCE, "contracts/e01_v2_dual_asr_real_evidence_v1.json")

    def test_missing_report_does_not_pass(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ProductionError, "source_report_size_mismatch"):
                verify_report(Path(d), Path(d)/"missing.json")

    def test_equal_length_fake_report_blocked_by_hash(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"report.json"
            path.write_bytes(b"x"*REPORT_BYTES)
            with self.assertRaisesRegex(ProductionError, "source_report_sha_mismatch"):
                verify_report(Path(d),path)

    def test_source_contract_always_preserves_nonrelease(self):
        root=Path(__file__).resolve().parents[1]
        val=json.loads((root/EVIDENCE).read_text(encoding="utf-8"))
        self.assertEqual(val["report_sha256"], REPORT_SHA)
        self.assertEqual(val["models"][0]["replacement_phrase_exact_match"], True)
        self.assertEqual(val["models"][1]["replacement_phrase_exact_match"], False)
        self.assertTrue(val["both_models_pass_aggregate_wer_cer"])
        self.assertFalse(val["audio_master_approved"])
        self.assertFalse(val["voice_rights_cleared"])
        self.assertFalse(val["publication_authorized"])

    def test_no_untrusted_other_run_can_claim_exact_evidence(self):
        root=Path(__file__).resolve().parents[1]
        val=json.loads((root/EVIDENCE).read_text(encoding="utf-8"))
        self.assertEqual(val["source_workflow_run_id"], 44204868327)
        self.assertEqual(val["report_bytes"], REPORT_BYTES)
        self.assertEqual(val["status"],
                         "V2_TEXT_HIGH_SIMILARITY_SINGLE_MODEL_PHONETIC_BOUNDARY_WARNING_REMAINS_QUARANTINED")


if __name__ == "__main__":
    unittest.main()
