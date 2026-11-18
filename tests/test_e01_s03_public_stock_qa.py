"""Strict preflight of S03 source and no automatic rights/master promotion."""
import unittest
from agents.e01_s03_public_stock_physical_qa import (
    SOURCE_ID, SOURCE_URL, SOURCE_FILE_URL,
    SCENE_DURATION, source_to_vertical_crop, probe_with_ffmpeg,
)


class S03PreflightTests(unittest.TestCase):
    def test_pinned_non_rejected_source(self):
        self.assertEqual(SOURCE_ID, 19381590)
        self.assertIn("/19381590/", SOURCE_URL)
        self.assertIn("19381590-uhd_3840_2160_25fps.mp4", SOURCE_FILE_URL)
        self.assertEqual(SCENE_DURATION, 6.14)

    def test_landscape_4k_has_native_portrait_crop(self):
        crop = source_to_vertical_crop(3840, 2160)
        self.assertTrue(crop["vertical_source_resolution_ok"])
        self.assertGreaterEqual(crop["crop_width"], 1080)
        self.assertGreaterEqual(crop["crop_height"], 1920)
        self.assertLessEqual(crop["crop_left"] + crop["crop_width"], 3840)

    def test_low_res_source_does_not_get_pretend_upscaled(self):
        for dims in [(640, 360), (1920, 1080), (1080, 1080), (1080, 1600)]:
            with self.subTest(dimensions=dims):
                with self.assertRaisesRegex(ValueError, "source_cannot_native_crop"):
                    source_to_vertical_crop(*dims)

    def test_portrait_input_preserves_full_native_frames(self):
        crop = source_to_vertical_crop(1080, 1920)
        self.assertEqual(crop["crop_width"], 1080)
        self.assertEqual(crop["crop_height"], 1920)
        self.assertEqual(crop["crop_left"], 0)


if __name__ == "__main__":
    unittest.main()
