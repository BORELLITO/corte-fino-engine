"""Cross-check the independent physically decoded Mixkit #99890 S09 QA receipt.

Contract-only tests; do NOT claim this CI re-downloads original media.
"""
import json
import unittest
from pathlib import Path
from agents import e01_mixkit_s09_physical_qa_20261120_v1 as qa

ROOT=Path(__file__).resolve().parents[1]
RECEIPT=ROOT/"contracts/e01_s09_mixkit_99890_physical_qa_receipt_20261120_v1.json"


class E01S09ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.q=json.loads(RECEIPT.read_text(encoding="utf8"))
        self.m=json.loads(qa.CONTRACT.read_text(encoding="utf8"))

    def test_source_4k_with_exact_sha_is_real_download_not_listing(self):
        s=self.q["source"]
        self.assertEqual(s["provider_id"],99890)
        self.assertEqual(s["video_size_bytes"],42005370)
        self.assertEqual(s["sha256"],
           "c401cd9b6dd78e2a482ef60a355a777d537ee2a5876f9b53f4f25d023c0e8ab8")
        self.assertEqual(s["true_dimensions"],[3840,2160])
        self.assertEqual(s["listing_dimensions"],[4096,2160])
        self.assertEqual(s["observed_fps"],"24000/1001")
        self.assertEqual(s["license_label"],"Mixkit Stock Video Free License")
        self.assertTrue(s["downloaded_from_https_host_allowlist"])
        self.assertFalse(s["source_full_decode_claimed"])
        self.assertFalse(s["physical_camera_authenticity_independently_proven"])

    def test_real_preview_proof_is_not_master_rights_or_owner_approval(self):
        p=self.q["preview"]
        self.assertEqual(p["sha256"],
          "3eb7c59dbeed9d36fd52ea131f52c3fb670849a53d9cf4722b7b5ee0773094d4")
        self.assertEqual(p["size_bytes"],693859)
        self.assertEqual((p["width"],p["height"],p["frames"],p["fps"]),
                         (720,1280,173,30))
        self.assertEqual(p["audio_streams"],0)
        self.assertTrue(p["full_decode_in_github_actions"])
        self.assertTrue(p["full_decode_independent_local"])
        self.assertFalse(p["captions_burned"])
        self.assertTrue(p["review_watermark_present"])
        self.assertFalse(self.q["master_allowed"])
        self.assertFalse(self.q["s09_visual_owner_approved"])
        self.assertFalse(self.q["publication_authorized"])
        self.assertFalse(self.q["person_and_property_release_verified"])
        self.assertFalse(self.q["merge_authorized"])

    def test_review_tracks_nine_real_frames_and_prior_failed_then_fixed_ci(self):
        self.assertEqual(self.q["evidence_run_id"],44717869759)
        self.assertEqual(self.q["evidence_run_head"],"68b43b954816ac6d760a5318e553f6927e637a1c")
        self.assertEqual(self.q["previous_attempt"]["run_id"],44717362393)
        self.assertEqual(self.q["previous_attempt"]["conclusion"],"failure")
        sheet=self.q["nine_frame_contact_sheet"]
        self.assertEqual(sheet["sha256"],
                         "0bf8c18064c742742df9cb1789e0328cf9016d7474be04c6565ded73effdb8e3")
        self.assertEqual(sheet["samples_seconds"],[0.5,2.4,5.25])
        self.assertEqual(sheet["crop_options"],["LEFT","CENTER","RIGHT"])
        self.assertTrue(sheet["measured_frame_drift_confirmed"])

    def test_12_scene_plan_prohibits_promoting_s09_or_s02(self):
        self.assertEqual(self.q["scene_id"],"VNC-E01V2-S09")
        self.assertEqual(self.q["episode_id"],"VNC-W01-E1")
        self.assertEqual(self.q["project_id"],"VERBO_NO_CHAO_EXCLUSIVO")
        self.assertEqual(self.m["scenes"][8]["primary_candidate_id"],99890)
        self.assertEqual(self.m["scenes"][8]["owner_visual_approved"],False)
        self.assertEqual(self.m["scenes"][1]["owner_visual_approved"],False)
        self.assertEqual(self.m["scenes"][0]["owner_visual_approved"],True)
        self.assertTrue(self.q["original_s01_visual_owner_approved_unchanged"])
        self.assertFalse(self.q["spending_authorized"])


if __name__=="__main__":
    unittest.main()
