import json
import unittest
from pathlib import Path


FIXTURE = Path(__file__).resolve().parents[1] / "docs" / "PILOT_SALMO_13_VOICE_BENCHMARK.json"


class VoiceBenchmarkTests(unittest.TestCase):
    def test_all_pt_br_candidates_pass_simplified_smoke_test(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "PARTIAL_SMOKE_PASS_RUNTIME_BLOCKER")
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


if __name__ == "__main__":
    unittest.main()
