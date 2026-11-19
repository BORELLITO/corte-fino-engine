"""No paid-plan quote or zero-file GPU failure can be called a finished S01."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from agents import e01_s01_provider_feasibility_gate as gate


class TestFeasibility(unittest.TestCase):
    def test_real_evidence_reports_blocked_not_completed(self):
        result = gate.assess()
        self.assertEqual(result["providers_evaluated"], 6)
        self.assertFalse(result["physically_approved_full_scene_video"])
        self.assertFalse(result["generation_or_publication_authorized"])

    def test_forged_release_and_replay_are_rejected(self):
        source = json.loads((gate.ROOT / gate.EVIDENCE).read_text(encoding="utf-8"))
        variants = []
        x = copy.deepcopy(source); x["actual_full_scene_mp4_verified"] = True; variants.append(x)
        x = copy.deepcopy(source); x["publication_authorized"] = True; variants.append(x)
        x = copy.deepcopy(source); x["providers"][0]["automatic_retry_allowed"] = True; variants.append(x)
        x = copy.deepcopy(source); x["providers"][2]["credits_deducted"] = 6; variants.append(x)
        x = copy.deepcopy(source); x["providers"][3]["result"] = "AVAILABLE_ON_FREE"; variants.append(x)
        for i, value in enumerate(variants):
            with self.subTest(index=i), tempfile.TemporaryDirectory() as temp:
                path = Path(temp) / gate.EVIDENCE
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(value), encoding="utf-8")
                with self.assertRaises(ValueError):
                    gate.assess(Path(temp))


if __name__ == "__main__":
    unittest.main()
