"""S02 evidence is physical, but remains an unapproved visual choice."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/"contracts/e01_s02_waiting_clock_physical_visual_review_20261119_v1.json"
S01_DECISION=ROOT/"contracts/e01_s01_owner_visual_approval_20261119_v1.json"
ORIGINAL=ROOT/"contracts/e01_v2_12_scene_visual_plan_v1.json"

class TestS02WaitingClockPhysicalEvidence(unittest.TestCase):
    def setUp(self):
        self.e=json.loads(EVIDENCE.read_text(encoding="utf8"))
        self.a=json.loads(S01_DECISION.read_text(encoding="utf8"))
        self.story=json.loads(ORIGINAL.read_text(encoding="utf8"))

    def test_rights_and_publication_never_inferred_from_decode(self):
        e=self.e
        self.assertEqual((e["project_id"],e["scene_id"]),("VERBO_NO_CHAO_EXCLUSIVO","VNC-E01V2-S02"))
        self.assertTrue(e["s01_user_visual_approval_preserved"])
        self.assertEqual(e["s01_approved_preview_sha256"],self.a["approval_scope"]["preview_sha256"])
        self.assertFalse(e["editorial_approved"])
        self.assertFalse(e["rights_cleared"])
        self.assertFalse(e["master_allowed"])
        self.assertFalse(e["publication_authorized"])
        self.assertFalse(e["production_merged"])

    def test_physical_source_sha_and_video_really_pinned(self):
        e=self.e
        s=e["source"]
        p=e["preview"]
        self.assertEqual(s["video_id"],7034348)
        self.assertEqual(s["source_sha256"],"6a8f877c0e57a1397f4eb96ffc9a86d25e173019fb298ec0a6945b73973f2a40")
        self.assertEqual(s["source_bytes"],6202873)
        self.assertEqual((s["native_width"],s["native_height"]),(1080,1920))
        self.assertTrue(s["full_stream_decode_pass"])
        self.assertFalse(s["commercial_release_individual_cleared"])
        self.assertEqual(p["sha256"],"31d9500f8d5d321d14f6da9b6c65c1a96eb230354c62f03ece51abf955813786")
        self.assertEqual(p["bytes"],203410)
        self.assertEqual((p["width"],p["height"],p["frames"],p["fps"]),(720,1280,147,30))
        self.assertEqual(p["duration_seconds"],4.9)
        self.assertTrue(p["independent_local_full_video_decode_pass"])
        self.assertFalse(p["audio_present"])
        self.assertFalse(p["captions_present"])

    def test_visual_contact_is_not_approval(self):
        q=self.e["visual_frame_sample"]
        self.assertEqual(q["sha256"],"28a0284ab8106274a60b937921f309572746c66ac44e3e342362b1712ad854b2")
        self.assertEqual(q["samples_s"],[0.5,2.4,4.5])
        self.assertEqual(q["frame_mean_difference"],[24.84,25.69])
        self.assertFalse(q["scene_suitability_approved"])
        self.assertFalse(q["owner_review_approved"])
        self.assertFalse(q["full_frame_visual_qa_complete"])

    def test_original_biblical_storyboard_and_cut_marks_preserved(self):
        e=self.e
        self.assertEqual(len(self.story["scenes"]),12)
        self.assertEqual(self.story["duration_seconds"],70.425)
        self.assertTrue(e["s02_original_storyboard_unchanged"])
        original=self.story["scenes"][1]
        self.assertEqual(original["id"],"VNC-E01V2-S02")
        self.assertEqual((original["start_seconds"],original["end_seconds"]),(5.74,10.62))
        self.assertFalse(original["approved_for_export"])
        self.assertEqual(e["frame_boundary_plan"]["s01_end_frame_exclusive"],172)
        self.assertEqual(e["frame_boundary_plan"]["s02_end_frame_exclusive"],319)
        self.assertEqual(e["frame_boundary_plan"]["s02_frame_count"],147)

if __name__=="__main__":
    unittest.main()
