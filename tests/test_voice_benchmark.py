import json
import unittest
from pathlib import Path


FIXTURE = Path(__file__).resolve().parents[1] / "docs" / "PILOT_SALMO_13_VOICE_BENCHMARK.json"


class VoiceBenchmarkTests(unittest.TestCase):
    def test_all_pt_br_candidates_pass_simplified_smoke_test(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "FULL_SCRIPT_SEGMENTED_PERSISTED_PASS_PREVIEW_ONLY")
        self.assertEqual(
            {item["voice_id"] for item in payload["voices"]},
            {"pm_alex", "pm_santa", "pf_dora"},
        )
        self.assertTrue(all(item["generated"] for item in payload["voices"]))

    def test_canonical_text_remains_blocked_without_mutation(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(payload["canonical_text_result"]["status"], "NO_GO_BROWSER_RUNTIME")
        self.assertIn("silêncio", payload["canonical_text_sample"])
        self.assertIn("Você", payload["canonical_text_sample"])

    def test_segmented_canonical_text_passes_with_editorial_text_preserved(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        result = payload["segmented_canonical_result"]
        self.assertEqual(result["status"], "FULL_SCRIPT_SEGMENTED_PERSISTED_PASS_PREVIEW_ONLY")
        self.assertTrue(result["editorial_text_preserved"])
        self.assertTrue(result["pronunciation_layer_required"])
        self.assertEqual(len(result["segments"]), 8)
        self.assertTrue(all(item["generated"] for item in result["segments"]))
        self.assertEqual(payload["audio_format"], "WAV 24 kHz")

    def test_full_local_runtime_attempt_is_explicitly_blocked(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        attempt = payload["local_runtime_attempt"]
        self.assertEqual(attempt["status"], "BLOCKED_CONTAINER_RESOURCE")
        self.assertEqual(attempt["exit_status"], 137)
        self.assertFalse(attempt["audio_generated"])


if __name__ == "__main__":
    unittest.main()
