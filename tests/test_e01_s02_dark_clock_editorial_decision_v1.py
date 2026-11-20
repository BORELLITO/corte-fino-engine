"""Physical success != artistic approval; S02 source 29862379 rejected only for E01 S02."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LEDGER=ROOT/"contracts/e01_s02_dark_clock_29862379_editorial_decision_20261119_v1.json"
S01_APPROVAL=ROOT/"contracts/e01_s01_owner_visual_approval_20261119_v1.json"
GRADE=ROOT/"contracts/e01_s02_color_continuity_qa_20261119_v1.json"

class TestS02RejectedDarkClockV1(unittest.TestCase):
    def setUp(self):
        self.e=json.loads(LEDGER.read_text(encoding="utf-8"))
        self.s01=json.loads(S01_APPROVAL.read_text(encoding="utf-8"))
        self.grade=json.loads(GRADE.read_text(encoding="utf-8"))

    def test_only_rejected_for_s02_and_not_global_ban(self):
        e=self.e
        self.assertEqual(e["project_id"],"VERBO_NO_CHAO_EXCLUSIVO")
        self.assertEqual(e["episode_id"],"VNC-W01-E1")
        self.assertEqual(e["scene_id"],"VNC-E01V2-S02")
        self.assertEqual(e["decision"],"REJECTED_FOR_S02_EDITORIAL")
        self.assertEqual(e["scope"],"S02_ONLY_SOURCE_SPECIFIC_EDITORIAL_REJECTION_NOT_GLOBAL_ID_BAN")
        self.assertEqual(e["alt_source"]["video_id"],29862379)
        self.assertFalse(e["s02_editorial_approved"])

    def test_source_is_real_downloaded_and_native_crop_valid(self):
        s=self.e["alt_source"]
        self.assertEqual((s["width"],s["height"]),(3840,2160))
        self.assertEqual(s["native_crop"],[1214,2160])
        self.assertTrue(s["full_video_decode_pass"])
        self.assertEqual(s["source_bytes"] if "source_bytes" in s else s["source_bytes"],57975096)
        self.assertEqual(s["sha256"],"a6058b295f21cbfa5381d6a19263a1ed5606dcfb87a6579ae0aa4611e5130052")
        self.assertFalse(s["camera_original_proven"])

    def test_contact_brightness_change_disqualifies_for_s02(self):
        f=self.e["frame_contact"]
        self.assertEqual(f["samples_seconds"],[0.5,2.4,4.5])
        self.assertEqual(f["luma_means"],[7.12,10.07,39.03])
        self.assertEqual(f["frame_difference_means"],[3.25,28.99])
        self.assertEqual(f["sha256"],"09b71d78c6d4a42dc95138bb4f99daad10ebef91c82b9e38951123f720fbfe43")
        self.assertGreater(f["luma_means"][-1]/f["luma_means"][0],5)
        p=self.e["derived_preview"]
        self.assertEqual((p["width"],p["height"],p["frames"],p["fps"]),(720,1280,147,30))
        self.assertEqual(p["sha256"],"3bb1c6efced29fbd5d48b235aec69af20d7e5c7bebf0b03fc8d09488d020ae94")
        self.assertTrue(p["full_decode_pass"])
        self.assertFalse(p.get("contains_audio",True) if "contains_audio" in p else True is False)

    def test_s01_and_prior_grade_a_are_preserved_not_approved_for_s02(self):
        self.assertTrue(self.e["approved_scene_s01_preserved"])
        self.assertFalse(self.e["owner_approval_for_s02"])
        self.assertEqual(self.s01["approval_status"],"APPROVED_S01_VISUAL_DIRECTION_ONLY")
        b=self.e["baseline_s02_grade_a"]
        self.assertEqual(b["graded_preview_sha256"],self.grade["observed_physical_results"]["s02_graded_sha256"])
        self.assertEqual(b["editorial_approval_status"],"PENDING_OWNER_REVIEW")
        self.assertTrue(b["full_nine_frame_review_composed"])
        self.assertEqual(b["audit_sheet_sha256"],"a589e5c417840ba9db31e665adf1a7c23ab6142b5dfde9db7108234563cf2b8c")

    def test_no_unapproved_release_or_paid_action(self):
        for k in ("rights_cleared","s02_editorial_approved","master_allowed","publication_authorized","merge_authorized","spend_authorized"):
            self.assertFalse(self.e[k])
        self.assertTrue(self.e["existing_original_storyboard_unchanged"])
        self.assertTrue(self.e["script_audio_subtitle_cues_unchanged"])


if __name__ == "__main__":
    unittest.main()
