import json
import unittest
from pathlib import Path

DECISION = Path(__file__).resolve().parents[1] / "contracts" / "pilot_source_decision.json"


class PilotSourceDecisionTests(unittest.TestCase):
    def test_literal_quote_is_blocked_until_license_is_clear(self):
        payload = json.loads(DECISION.read_text(encoding="utf-8"))
        self.assertEqual(payload["passage"], "Salmo 13")
        self.assertEqual(payload["source_mode"], "reference_and_paraphrase")
        self.assertIsNone(payload["selected_translation"])
        self.assertEqual(payload["verbatim_quote_status"], "BLOCKED_PENDING_LICENSE")

    def test_decision_has_multiple_evidence_records(self):
        payload = json.loads(DECISION.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(payload["evidence"]), 3)


if __name__ == "__main__":
    unittest.main()
