"""Real byte QA via generated codec fixture; never treats fixture as production."""
import tempfile
import subprocess
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch
from agents.e01_candidate_media_intake import verify_policy,inspect,_ffprobe
from agents.e01_stock_candidates import ROOT, StockIntakeError

class TestE01CandidateMediaIntake(unittest.TestCase):
    def test_policy_is_pending_rights(self):
        p=verify_policy(ROOT)
        self.assertFalse(p["rights_review_completed"])
        self.assertFalse(p["user_publication_approval"])

    def test_missing_and_origin_spoof_rejected(self):
        with self.assertRaises(StockIntakeError):
            inspect(Path("/no-clip.mp4"),"VNC-E01V2-S01","camera_original")
        with self.assertRaises(StockIntakeError):
            inspect(Path("/no-clip.mp4"),"VNC-E01V2-S01","fictitious")

    def test_file_with_fake_mp4_bytes_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"invalid.mp4"
            path.write_bytes(b"U"*20000)
            with self.assertRaises(StockIntakeError):
                inspect(path,"VNC-E01V2-S01","ai_generated_video")

    def test_ffprobe_failure_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            f=Path(folder)/"invalid.mov"
            f.write_bytes(b"U"*20000)
            with patch("agents.e01_candidate_media_intake.subprocess.run") as run:
                run.return_value.returncode=1
                with self.assertRaises(StockIntakeError):_ffprobe(f)

    def test_synthetic_video_proves_only_decoder_not_release(self):
        ff=shutil.which("ffmpeg");probe=shutil.which("ffprobe")
        if not ff or not probe:
            self.skipTest("ffmpeg not installed in runtime")
        with tempfile.TemporaryDirectory() as folder:
            f=Path(folder)/"test_pattern_not_for_publication.mp4"
            a=subprocess.run([ff,"-nostdin","-v","error",
               "-f","lavfi","-i","testsrc2=size=360x640:rate=15",
               "-t","6","-c:v","libx264","-threads","1",
               "-preset","ultrafast","-pix_fmt","yuv420p",str(f)],
               capture_output=True,timeout=60,check=False)
            if a.returncode!=0:
                self.skipTest("libx264 unavailable")
            result=inspect(f,"VNC-E01V2-S01","ai_generated_video")
            self.assertEqual(result["status"],"VIDEO_BYTES_VERIFIED_NO_RIGHTS_RELEASE")
            self.assertTrue(result["full_video_decode_completed"])
            self.assertTrue(result["scene_length_covered"])
            self.assertFalse(result["native_resolution_sufficient"])
            self.assertTrue(result["preview_only"])
            self.assertFalse(result["approved_for_master"])
            self.assertFalse(result["publication_authorized"])
            self.assertFalse(result["filmed_in_real_world_claimed"])
            self.assertEqual(len(result["sha256"]),64)
            # The same physically decodable file must be denied when the
            # historical rejection registry marks its SHA as disallowed.
            with patch("agents.e01_candidate_media_intake.rejected_sha",
                       return_value=True) as rejected:
                with self.assertRaisesRegex(
                    StockIntakeError,"previously_rejected_sha256"):
                    inspect(f,"VNC-E01V2-S01","stock_licensed_candidate")
                rejected.assert_called_once_with(result["sha256"])

if __name__=="__main__":
    unittest.main()
