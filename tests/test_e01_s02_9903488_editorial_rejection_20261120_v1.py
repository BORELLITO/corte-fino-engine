"""Editorial-veto proof for Pexels #9903488 E01 S02; passing media != scene approval."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REJECT=ROOT/"contracts/e01_s02_9903488_editorial_rejection_20261120_v1.json"
PREFLIGHT=ROOT/"contracts/e01_s02_human_desk_stock_preflight_20261120_v1.json"
STORY=ROOT/"contracts/e01_v2_12_scene_visual_plan_v1.json"

class E01S02StockRejectionTest(unittest.TestCase):
    def setUp(self):
        self.d=json.loads(REJECT.read_text(encoding="utf8"))
        self.p=json.loads(PREFLIGHT.read_text(encoding="utf8"))
        self.story=json.loads(STORY.read_text(encoding="utf8"))

    def test_correct_source_scene_scope_and_artistic_veto(self):
        d=self.d
        self.assertEqual(d["project_id"],"VERBO_NO_CHAO_EXCLUSIVO")
        self.assertEqual(d["episode_id"],"VNC-W01-E1")
        self.assertEqual(d["scene_id"],"VNC-E01V2-S02")
        self.assertEqual(d["source_scope"],"ONLY_PEXELS_9903488_FOR_E01_S02")
        self.assertEqual(d["decision"],"REJECTED_FOR_S02_SCENE_FIDELITY")
        self.assertEqual(d["decision_authority"],"EDITORIAL_QA_ONLY_NOT_OWNER_APPROVAL")
        self.assertEqual(d["editorial_analysis"]["editorial_score_status"],"FAIL_STORY_AND_PALETTE_FIT")
        self.assertFalse(d["s02_owner_approved"])

    def test_physical_clip_evidence_is_not_master_evidence(self):
        src=self.d["observed_source"]
        prv=self.d["qa_preview"]
        self.assertEqual(src["video_id"],self.p["candidate"]["id"])
        self.assertEqual(src["source_sha256"],
                         "ab34b60af5d700e94fc70fc19982ff974a3c52c3a6484ce4a48ce07c965d1d86")
        self.assertEqual(src["source_bytes"],60515189)
        self.assertEqual(src["portrait_native_crop"],[2160,3840])
        self.assertFalse(src["source_full_decode_claimed"])
        self.assertFalse(src["individual_rights_cleared"])
        self.assertEqual(prv["sha256"],"af604d62cc899206e341dd569897a5f5dc82d724f9cd1170cff9948e903a5107")
        self.assertEqual((prv["width"],prv["height"],prv["frames"],prv["fps"]),(720,1280,147,30))
        self.assertTrue(prv["full_preview_decode_pass"])
        self.assertFalse(self.d["master_allowed"])

    def test_motion_is_confirmed_but_story_not_fixed_by_grading(self):
        x=self.d["qa_frames"]
        self.assertEqual(x["sha256"],"0802ca9e6a566c9c0c5cb0d0b8df9a3e9c2cb06c3690b5cf06adf043d64186e3")
        self.assertEqual(x["times_s"],[0.5,2.4,4.5])
        self.assertTrue(x["motion_in_samples_confirmed"])
        self.assertGreater(min(x["frame_difference_means"]),0.5)
        self.assertIn("dark charcoal jacket",self.story["scenes"][1]["visual_prompt"])
        self.assertIn("same anonymous adult hand",self.story["scenes"][1]["visual_prompt"])
        self.assertTrue(any("Mustard-brown" in m for m in self.d["editorial_analysis"]["mismatches"]))

    def test_prior_candidate_and_approved_s01_are_untouched(self):
        d=self.d["preserved_reference"]
        self.assertTrue(d["s01_unchanged"])
        self.assertTrue(d["previous_s02_still_not_discarded"])
        self.assertFalse(d["previous_s02_owner_approved"])
        self.assertEqual(d["s01_owner_visual_approval_sha256"],
                         "724ae91368af7d843f39195b34f77db50341aa7f92b0e5960a17061e9da3f961")
        self.assertEqual(d["previous_s02_grade_a_sha256"],
                         self.p["historical_candidate_to_preserve"]["grade_a_preview_sha256"])
        for flag in ("s02_owner_approved","rights_cleared","master_allowed",
                     "publication_authorized","merge_authorized","new_spending_authorized"):
            self.assertFalse(self.d[flag],flag)


if __name__=="__main__":
    unittest.main()
