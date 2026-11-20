"""The S01/S02 319-frame QA splice never transfers S01 approval to S02."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TRANSITION=ROOT/"contracts/e01_s01_s02_transition_qa_20261119_v1.json"
S01=ROOT/"contracts/e01_s01_owner_visual_approval_20261119_v1.json"
S02=ROOT/"contracts/e01_s02_waiting_clock_physical_visual_review_20261119_v1.json"

class TestS01S02CutEvidence(unittest.TestCase):
    def setUp(self):
        self.e=json.loads(TRANSITION.read_text(encoding="utf-8"))
        self.s01=json.loads(S01.read_text(encoding="utf-8"))
        self.s02=json.loads(S02.read_text(encoding="utf-8"))

    def test_approval_scoped_to_s01(self):
        src=self.e["source_previews"]
        self.assertEqual(len(src),2)
        self.assertEqual([s["scene_id"] for s in src],["VNC-E01V2-S01","VNC-E01V2-S02"])
        self.assertEqual(src[0]["preview_sha256"],self.s01["approval_scope"]["preview_sha256"])
        self.assertTrue(src[0]["visual_approved_by_owner"])
        self.assertEqual(src[1]["preview_sha256"],self.s02["preview"]["sha256"])
        self.assertFalse(src[1]["visual_approved_by_owner"])
        self.assertTrue(self.e["s01_original_untouched"])
        self.assertTrue(self.e["s02_art_review_pending"])

    def test_frame_quantization_proves_319_frames(self):
        src=self.e["source_previews"]
        movie=self.e["output"]
        self.assertEqual(src[0]["frames_used"],172)
        self.assertEqual(src[1]["frames_used"],147)
        self.assertEqual(sum(s["frames_used"] for s in src),movie["frames"])
        self.assertEqual((movie["fps"],movie["frames"]),(30,319))
        self.assertLess(abs(movie["duration_seconds"]-319/30),0.001)
        self.assertEqual((movie["width"],movie["height"]),(720,1280))

    def test_video_is_verified_qa_and_not_release(self):
        p=self.e["output"]
        self.assertEqual(p["sha256"],"31ea65a045bbe067a66837b85c03ccc9fdf20bf93ac6b15603c6f4c7bf66156b")
        self.assertEqual(p["bytes"],1840317)
        self.assertTrue(p["full_decode_success"])
        self.assertTrue(p["ffprobe_verified"])
        self.assertTrue(p["sha_verified"])
        self.assertFalse(p["audio"])
        self.assertTrue(p["has_qa_watermarks"])
        for k in ["third_party_rights_cleared","master_allowed","publication_authorized"]:
            self.assertIs(self.e[k],False)

    def test_private_evidence_and_original_order(self):
        self.assertEqual(self.e["independent_visual_comparison_sample_seconds"],[5.65,5.95])
        self.assertEqual(len(self.e["assets_preserved"]),3)
        self.assertEqual(self.e["status"],"VISUAL_TRANSITION_QA_ONLY")
        self.assertTrue(self.e["evidence_library_path"].startswith("/VERBO_NO_CHAO/"))

if __name__=="__main__":
    unittest.main()
