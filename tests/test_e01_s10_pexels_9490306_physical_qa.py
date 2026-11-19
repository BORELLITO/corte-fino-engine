"""Guardrails for S10 external stock research, without network or GPU calls."""
import inspect
import json
import unittest
from pathlib import Path

from agents import e01_s10_pexels_9490306_physical_qa as q


class S10PhysicalCandidateContract(unittest.TestCase):
    def test_exact_project_and_shot_scope(self):
        self.assertEqual(q.PROJECT, "VERBO_NO_CHAO_EXCLUSIVO")
        self.assertEqual(q.EPISODE, "VNC-W01-E1")
        self.assertEqual(q.SCENE, "VNC-E01V2-S10")
        self.assertEqual(q.SOURCE_ID, 9490306)
        self.assertEqual(q.REQUIRED_SECONDS, 6.6)
        self.assertEqual(q.WINDOW_STARTS, (0.0, 8.0))

    def test_2_review_windows_are_distinct_and_fit_public_source_metadata(self):
        self.assertGreaterEqual(17, max(q.WINDOW_STARTS) + q.REQUIRED_SECONDS)
        self.assertEqual(len(q.WINDOW_STARTS), 2)

    def test_no_claim_of_rights_approval_or_master(self):
        code = inspect.getsource(q.audit)
        for phrase in ('"editorial_approved": False',
                       '"people_context_rights_cleared": False',
                       '"allowed_in_master": False',
                       '"publication_authorized": False',
                       '"paid_generation_calls": 0'):
            self.assertIn(phrase, code)
        for forbidden in ("client.submit(", "workflow_dispatch", "publish_video("):
            self.assertNotIn(forbidden, code)

    def test_real_full_file_decode_and_original_hash_mandatory(self):
        code = inspect.getsource(q.audit)
        self.assertIn('"source_sha256"', code)
        self.assertIn('"full_original_decode_pass"', code)
        self.assertIn("full_original_video_decode_failed", code)
        self.assertIn("insufficient_original_portrait_dimensions", code)

    def test_original_contract_frozen_unchanged(self):
        root = Path(__file__).resolve().parents[1]
        plan = json.loads((root / "contracts/e01_v2_12_scene_visual_plan_v1.json").read_text(encoding="utf-8"))
        shot = plan["scenes"][9]
        self.assertEqual(shot["id"], q.SCENE)
        self.assertEqual(shot["start_seconds"], 55.56)
        self.assertEqual(shot["end_seconds"], 62.16)
        self.assertEqual(shot["caption_cues"], [22,23,24])
        self.assertIsNone(shot["asset_sha256"])
        self.assertFalse(shot["approved_for_export"])


if __name__ == "__main__":
    unittest.main()
