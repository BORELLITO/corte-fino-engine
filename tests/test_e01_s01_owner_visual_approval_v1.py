"""S01 owner approval is visual and SHA-scoped; never infer master or publication."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
APPROVAL=ROOT/"contracts/e01_s01_owner_visual_approval_20261119_v1.json"
EVIDENCE=ROOT/"contracts/e01_s01_night_rain_physical_visual_review_20261119_v1.json"
ORIGINAL=ROOT/"contracts/e01_v2_12_scene_visual_plan_v1.json"

class TestS01UserVisualApproval(unittest.TestCase):
    def setUp(self):
        self.approval=json.loads(APPROVAL.read_text(encoding="utf-8"))
        self.proof=json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.original=json.loads(ORIGINAL.read_text(encoding="utf-8"))

    def test_owner_approval_applies_only_to_one_exact_preview_and_concept(self):
        a=self.approval
        self.assertEqual(a["project_id"],"VERBO_NO_CHAO_EXCLUSIVO")
        self.assertEqual(a["episode_id"],"VNC-W01-E1")
        self.assertEqual(a["approval_status"],"APPROVED_S01_VISUAL_DIRECTION_ONLY")
        scope=a["approval_scope"]
        self.assertEqual(scope["scene_id"],"VNC-E01V2-S01")
        self.assertEqual(scope["concept"],"NIGHT_RAIN_WINDOW_SINGLE_TAKE_SYMBOLIC_VISUAL_ALTERNATIVE")
        self.assertEqual(scope["source_video_id"],31069867)
        self.assertTrue(scope["visual_style_approved"])
        self.assertTrue(scope["symbolic_replacement_of_literal_room_a_for_s01_approved"])
        self.assertFalse(scope["extend_to_other_scenes_automatically"])
        self.assertEqual(scope["preview_sha256"],self.proof["derived_preview"]["output_sha256"])
        self.assertTrue(scope["preview_is_watermarked"])

    def test_user_approval_does_not_unlock_rights_master_audio_or_release(self):
        flags=self.approval["non_authorizations"]
        self.assertEqual(len(flags),10)
        self.assertTrue(all(x is False for x in flags.values()))
        self.assertFalse(self.proof["rights_clearance"])
        self.assertFalse(self.proof["master_allowed"])
        self.assertFalse(self.proof["publication_authorized"])

    def test_original_twelve_scene_storyboard_is_not_mutated(self):
        self.assertEqual(len(self.original["scenes"]),12)
        self.assertAlmostEqual(self.original["duration_seconds"],70.425)
        s1=self.original["scenes"][0]
        s2=self.original["scenes"][1]
        self.assertEqual(s1["id"],"VNC-E01V2-S01")
        self.assertEqual(s1["end_seconds"],5.74)
        self.assertEqual(s1["rights"],"PENDING")
        self.assertFalse(s1["approved_for_export"])
        self.assertIn("notebook closed",s1["visual_prompt"])
        self.assertEqual(s2["id"],"VNC-E01V2-S02")
        self.assertEqual((s2["start_seconds"],s2["end_seconds"]),(5.74,10.62))
        self.assertFalse(s2["approved_for_export"])

    def test_historical_qa_snapshot_is_immutable_not_overwritten(self):
        self.assertFalse(self.proof["concept_owner_approved"])
        self.assertEqual(self.proof["editorial_decision"],
            "CANDIDATE_FOR_OWNER_AESTHETIC_REVIEW_ONLY")
        self.assertTrue(self.approval["preserve_prior_qa_snapshots"])
        self.assertEqual(self.proof["source"]["source_sha256"],
            "fc36bb6b4039e307828d9ad0acabdb54a1baa4cb6e9d41f2889d2278be7c6df8")

if __name__=="__main__":
    unittest.main()
