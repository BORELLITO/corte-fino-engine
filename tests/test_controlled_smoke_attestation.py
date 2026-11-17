import copy
import json
import tempfile
import unittest
from pathlib import Path

from agents.content_production import ProductionError, produce as produce_plan
from agents.first_batch_production import produce as produce_scripts
from agents.audio_preflight import produce as produce_audio
from agents.controlled_smoke_evidence import validate_smoke_attestation, REPORT_SHA

ROOT = Path(__file__).resolve().parents[1]


class ControlledSmokeAttestationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads(
            (ROOT / "contracts/kokoro_controlled_smoke_evidence_v1.json").read_text(encoding="utf-8")
        )

    def test_exact_original_browser_report_recorded(self):
        result = validate_smoke_attestation(self.evidence)
        self.assertEqual(result["result"], "HISTORICAL_TEST_AUDIO_AND_CACHE_SHA_OBSERVED")
        self.assertEqual(result["source_workflow_run_id"], 44179520750)
        self.assertEqual(result["source_report_sha256"], REPORT_SHA)
        self.assertEqual(result["test_audio_duration_seconds"], 5.875)
        self.assertEqual(result["cached_voice_bytes"], 522240)
        self.assertTrue(result["cache_matches_upstream"])
        self.assertFalse(result["effective_runtime_asset_usage_proven"])
        self.assertFalse(result["publication_authorized"])

    def test_fake_observed_duration_rejected(self):
        bad = copy.deepcopy(self.evidence)
        bad["test_audio_duration_seconds"] = 20
        with self.assertRaisesRegex(ProductionError, "browser_observations"):
            validate_smoke_attestation(bad)

    def test_fake_source_report_sha_rejected(self):
        bad = copy.deepcopy(self.evidence)
        bad["source"]["original_report_sha256"] = "0" * 64
        with self.assertRaisesRegex(ProductionError, "source_provenance"):
            validate_smoke_attestation(bad)

    def test_fake_inference_consumption_or_rights_rejected(self):
        for path, val in [
            (("cached_voice_observation", "proves_effective_inference_use"), True),
            (("owner_script_approval",), True),
            (("exact_dependencies_and_rights_cleared",), True),
            (("publication_authorized",), True),
        ]:
            bad = copy.deepcopy(self.evidence)
            if len(path) == 1:
                bad[path[0]] = val
            else:
                bad[path[0]][path[1]] = val
            with self.subTest(path=path):
                with self.assertRaises(ProductionError):
                    validate_smoke_attestation(bad)

    def test_preflight_exposes_historical_smoke_without_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            produce_plan(ROOT, folder)
            produce_scripts(ROOT, folder, upstream_root=folder)
            report = produce_audio(ROOT, folder, folder)
            rendered = json.loads((folder / "audio-preflight/preflight.json").read_text(encoding="utf-8"))
            historical = json.loads((folder / "audio-preflight/historical_smoke.json").read_text(encoding="utf-8"))
        self.assertTrue(report["historical_smoke_evidence_verified"])
        self.assertEqual(report["historical_smoke_source_report_sha256"], REPORT_SHA)
        self.assertEqual(historical["cached_voice_filename"], "pm_alex.bin")
        self.assertTrue(rendered["voice"]["historical_browser_cache_pm_alex_bin_sha256_matched"])
        self.assertFalse(rendered["voice"]["effective_inference_voice_asset_consumption_proven"])
        self.assertFalse(rendered["publication_authorized"])
        self.assertEqual(report["status"], "BLOCKED")
        self.assertFalse(report["audio_generated"])

    def test_attestation_remains_historical_only(self):
        self.assertTrue(self.evidence["historical_observation_only"])
        self.assertEqual(self.evidence["human_listening_review"], "PENDING")
        self.assertFalse(self.evidence["test_audio_saved"])
        self.assertFalse(self.evidence["binary_pack_saved"])
        self.assertFalse(self.evidence["production_audio_generated"])


if __name__ == "__main__":
    unittest.main()
