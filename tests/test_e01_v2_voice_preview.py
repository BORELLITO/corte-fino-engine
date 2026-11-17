import json
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agents.e01_v2_voice_preview import generate, OUTPUT_NAME
from agents.e01_v2_candidate import V2_SHA, PARENT_SHA
from agents.content_production import ProductionError
from tests.test_wav_normalization import test_riff

ROOT = Path(__file__).resolve().parents[1]


class E01V2VoicePreviewTests(unittest.TestCase):
    def test_generation_mock_verified_pcm_keeps_all_release_flags_false(self):
        # This tests integration and output bytes. It is NOT evidence that
        # Kokoro Web ran; the separate GitHub Actions Chrome job proves that.
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            with patch("agents.e01_v2_voice_preview.synthesize_browser",
                       return_value=(test_riff(fmt_code=3, seconds=70, sample=0.16),
                                     {"observed_in_same_browser_session": True,
                                      "effective_inference_consumption_proven": False})):
                report = generate(ROOT, folder)
            self.assertEqual(report["status"],
                             "QUARANTINED_E01_V2_WAV_PHYSICALLY_VERIFIED")
            self.assertEqual(report["candidate_script_sha256"], V2_SHA)
            self.assertEqual(report["original_script_sha256"], PARENT_SHA)
            self.assertTrue((folder / OUTPUT_NAME).exists())
            self.assertFalse(report["voice_runtime_rights_cleared"])
            self.assertFalse(report["production_audio_master_approved"])
            self.assertFalse(report["publication_authorized"])
            self.assertFalse(report["independent_asr_completed_for_v2"])

    def test_invalid_browser_wav_leaves_no_output(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d)
            with patch("agents.e01_v2_voice_preview.synthesize_browser",
                       return_value=(b"corrupted", {})):
                report=generate(ROOT, folder)
            self.assertFalse(report["audio_preview_saved"])
            self.assertEqual(report["status"], "BLOCKED_E01_V2_WAV_NOT_PROVEN")
            self.assertFalse((folder / OUTPUT_NAME).exists())
            self.assertFalse(report["publication_authorized"])

    def test_existing_candidate_erased_on_failed_retry(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d)
            (folder / OUTPUT_NAME).write_bytes(b"old invalid preview")
            with patch("agents.e01_v2_voice_preview.synthesize_browser",
                       side_effect=RuntimeError("simulated browser failure")):
                report=generate(ROOT, folder)
            self.assertFalse((folder / OUTPUT_NAME).exists())
            self.assertEqual(report["error_code"], "RuntimeError")

    def test_wrong_model_cache_claim_never_publishes(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d)
            with patch("agents.e01_v2_voice_preview.synthesize_browser",
                       return_value=(test_riff(fmt_code=3, seconds=60, sample=0.16),
                                     {"observed_in_same_browser_session": False,
                                      "effective_inference_consumption_proven": True})):
                report=generate(ROOT, folder)
            self.assertFalse(report["audio_preview_saved"])
            self.assertFalse(report["publication_authorized"])
            self.assertFalse((folder / OUTPUT_NAME).exists())

    def test_refuses_protected_source_folder(self):
        with self.assertRaisesRegex(ProductionError, "protected_output_path"):
            generate(ROOT, ROOT / "contracts")
            

if __name__ == "__main__":
    unittest.main()
