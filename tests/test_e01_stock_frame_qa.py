"""Offline negative tests for the E01 stock frame-QA contact sheet."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
try:
    from PIL import Image
except ImportError:
    Image = None
from agents.e01_stock_frame_qa import (
    THUMB_W, THUMB_H, image_metrics, contact_sheet, sample_frame, StockIntakeError
)

@unittest.skipUnless(Image is not None, "Pillow is tested in the dedicated stock frame QA workflow")
class TestE01StockFrameQa(unittest.TestCase):
    def test_metrics_do_not_claim_semantic_approval(self):
        images=[Image.new("RGB", (THUMB_W, THUMB_H), color)
                for color in ("red", "green", "blue")]
        result=image_metrics(images)
        self.assertEqual(result["sample_frames"],3)
        self.assertEqual(len(result["frames"]),3)
        self.assertFalse(result["human_frame_review_complete"])
        self.assertFalse(result["logo_face_text_and_narrative_review_complete"])
        self.assertGreater(result["sequential_sample_luma_difference"][0],1)

    def test_identical_frames_flag_potential_static_footage(self):
        images=[Image.new("RGB", (THUMB_W, THUMB_H), "black") for _ in range(3)]
        result=image_metrics(images)
        self.assertTrue(result["potential_very_dark_frame"])
        self.assertTrue(result["potential_static_footage"])

    def test_contact_sheet_dimensions_and_sha(self):
        images=[Image.new("RGB", (THUMB_W, THUMB_H), color)
                for color in ("red", "green", "blue")]
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/"sheet.jpg"
            report=contact_sheet([(f"S{i}",images) for i in range(4)],target)
            self.assertEqual((report["width"],report["height"]),(648,1696))
            self.assertTrue(target.is_file())
            self.assertEqual(len(report["sha256"]),64)

    def test_bad_missing_or_wrong_frame_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(StockIntakeError):
                contact_sheet([("bad",[])],Path(d)/"bad.jpg")
        with self.assertRaises(StockIntakeError):
            image_metrics([Image.new("RGB",(100,100),"red")]*3)

    def test_no_video_frames_without_real_source(self):
        with self.assertRaises(StockIntakeError):
            sample_frame(Path("/never-exists.mp4"),0.5,"ffmpeg")

    def test_invalid_time_and_failed_decoder_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"fake.mp4"
            f.write_bytes(b"fake")
            with self.assertRaises(StockIntakeError):
                sample_frame(f,float("nan"),"ffmpeg")
            with patch("agents.e01_stock_frame_qa.subprocess.run") as run:
                run.return_value.returncode=1
                run.return_value.stdout=b""
                with self.assertRaises(StockIntakeError):
                    sample_frame(f,0.5,"ffmpeg")

if __name__=="__main__":
    unittest.main()
