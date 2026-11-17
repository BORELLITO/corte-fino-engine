import json
import unittest
from pathlib import Path


FIXTURE = Path(__file__).resolve().parents[1] / "contracts" / "pilot_voice_decision.json"


class VoiceDecisionTests(unittest.TestCase):
    def test_voice_baseline_is_selected_but_gate_remains_open(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "APPROVED_VOICE_PENDING_RUNTIME_VALIDATION")
        self.assertEqual(payload["engine"], "Kokoro-82M")
        self.assertEqual(payload["language"], "pt-BR")
        self.assertEqual(payload["selected_voice"], "pm_alex")
        self.assertEqual(payload["voice_selection_scope"], "PROVISIONAL_BASELINE")
        self.assertEqual(payload["voice_license_status"], "PENDING_EXACT_VOICE_PACK_AUDIT")
        self.assertEqual(payload["runtime_license_status"], "PENDING_DEPENDENCY_NOTICE_REVIEW")

    def test_audio_and_publication_remain_blocked(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertFalse(payload["audio_generated"])
        self.assertFalse(payload["publication_authorized"])


if __name__ == "__main__":
    unittest.main()
