"""NIGHT RAIN / S01 - explicit distinction between physical video and unapproved art."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "contracts/e01_s01_night_rain_physical_visual_review_20261119_v1.json"


class NightRainEvidenceLockTests(unittest.TestCase):
    def setUp(self):
        self.e = json.loads(LEDGER.read_text(encoding="utf8"))

    def test_identity_and_nonrelease(self):
        e=self.e
        self.assertEqual(e["project_id"],"VERBO_NO_CHAO_EXCLUSIVO")
        self.assertEqual(e["episode_id"],"VNC-W01-E1")
        self.assertEqual(e["scene_id"],"VNC-E01V2-S01")
        self.assertFalse(e["concept_owner_approved"])
        self.assertFalse(e["rights_clearance"])
        self.assertFalse(e["master_allowed"])
        self.assertFalse(e["publication_authorized"])
        self.assertTrue(e["parent_storyboard_unchanged"])
        self.assertEqual(e["editorial_decision"],"CANDIDATE_FOR_OWNER_AESTHETIC_REVIEW_ONLY")

    def test_pinned_physically_decoded_source_and_video(self):
        s=self.e["source"]
        self.assertEqual(s["id"],31069867)
        self.assertEqual(s["source_width"],2160)
        self.assertEqual(s["source_height"],3840)
        self.assertEqual(s["source_bytes"],93575530)
        self.assertEqual(s["source_sha256"],
            "fc36bb6b4039e307828d9ad0acabdb54a1baa4cb6e9d41f2889d2278be7c6df8")
        self.assertTrue(s["source_full_ffmpeg_decode_success"])
        self.assertFalse(s["camera_capture_origin_independently_proven"])
        self.assertFalse(s["source_raw_mp4_distributed_or_committed"])
        p=self.e["derived_preview"]
        self.assertEqual((p["output_width"],p["output_height"]),(720,1280))
        self.assertEqual((p["frames"],p["fps"]),(173,30))
        self.assertEqual(p["output_sha256"],
            "724ae91368af7d843f39195b34f77db50341aa7f92b0e5960a17061e9da3f961")
        self.assertFalse(p["contains_audio"])
        self.assertTrue(p["has_watermark"])
        self.assertTrue(p["full_decode_success"])
        self.assertFalse(p["target_1080x1920_master_created"])

    def test_three_samples_do_not_auto_approve(self):
        c=self.e["contact_sheet"]
        self.assertEqual(c["samples_s"],[0.5,2.8,5.4])
        self.assertEqual(c["mean_frame_difference"],[14.09,12.57])
        self.assertEqual(c["sha256"],
            "35638af1e60c9c450140175965033a809e2ade83b6893cb28ff82cf2d10147ba")
        self.assertFalse(c["full_sequence_human_review_done"])
        r=self.e["editorial_review_summary"]
        self.assertFalse(r["editorial_approval"])
        self.assertFalse(r["user_visual_direction_approval"])
        self.assertFalse(r["license_individual_cleared"])
        self.assertTrue(any("ROOM_A" in item for item in r["structural_deviations"]))

    def test_exact_library_evidence_and_no_raw_source(self):
        p=self.e["assets_preserved_to_personal_library"]
        self.assertEqual(len(p),3)
        self.assertEqual(len(set(p)),3)
        self.assertTrue(all(a.startswith("S01_31069867_") for a in p))
        self.assertTrue(self.e["personal_library_dir"].startswith("/VERBO_NO_CHAO/"))
        self.assertEqual(self.e["source"]["page"],
            "https://www.pexels.com/video/raindrop-reflections-on-nighttime-metro-glass-31069867/")

    def test_research_contract_does_not_override_original_s01(self):
        r=json.loads((ROOT/"contracts/e01_s01_night_rain_motif_probe_20261119_v1.json").read_text(encoding="utf8"))
        self.assertEqual(r["approval_status"],"CONCEPT_RESEARCH_ONLY_NOT_USER_APPROVED")
        self.assertFalse(r["master_allowed"])
        self.assertFalse(r["publication_authorized"])
        self.assertEqual(r["experimental_preview"]["frames"],173)
        self.assertEqual(r["source_id"],31069867)


if __name__=="__main__":
    unittest.main()
