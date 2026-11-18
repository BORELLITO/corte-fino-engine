"""One-time local full decode evidence does not become a fake CI/master pass."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


class VisualFullDecodeEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.j=json.loads((ROOT/"contracts/e01_v2_visual_full_decode_evidence_v1.json")
                         .read_text(encoding="utf-8"))

    def test_whole_video_physically_decoded_without_error_in_local_tool(self):
        v=self.j
        self.assertEqual(v["actual_process_returncode"],0)
        self.assertEqual(v["ffmpeg_error_output"],"")
        self.assertTrue(v["all_audio_video_packets_decoded_without_ffmpeg_error"])
        self.assertEqual(v["input_dimensions"],[720,1280])
        self.assertEqual(v["input_frame_count"],2113)

    def test_hash_exactly_matches_real_roughcut_evidence(self):
        proof=json.loads((ROOT/"contracts/e01_v2_12_real_visual_roughcut_evidence_v1.json")
                         .read_text(encoding="utf-8"))
        self.assertEqual(self.j["source_video_sha256"],proof["real_local_preview"]["sha256"])
        self.assertEqual(self.j["source_video_bytes"],proof["real_local_preview"]["size_bytes"])

    def test_not_claimed_as_github_actions_execution(self):
        self.assertEqual(self.j["evidence_origin"],
                         "CHATGPT_CONVERSATION_CONTAINER_NOT_GITHUB_ACTIONS")
        self.assertFalse(self.j["whole_video_manual_listening_and_frame_by_frame_qa_completed"])
        self.assertFalse(self.j["visual_assets_all_native_1080p"])

    def test_all_commercial_and_release_flags_still_false(self):
        v=self.j
        for flag in ("music_included","voice_rights_commercially_cleared",
                     "full_hd_master_approved","publication_authorized",
                     "youtube_publication_authorized",
                     "tiktok_publication_authorized"):
            with self.subTest(flag=flag):
                self.assertIs(v[flag],False)


if __name__=="__main__":
    unittest.main()
