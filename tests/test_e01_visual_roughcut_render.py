"""Rendering can proceed only with verified raw bytes; paper tests are not video."""
import tempfile
import unittest
from pathlib import Path

from agents.content_production import ProductionError
from agents.e01_visual_roughcut_render import (
    FPS,SIZE,EXPECTED_DURATION,OUTPUT_NAME,
    ffmpeg_command,ensure_sources,run,
)


class VisualRenderSafetyTests(unittest.TestCase):
    def test_output_cannot_be_confused_with_finished_video(self):
        self.assertIn("NOT_FOR_PUBLICATION",OUTPUT_NAME)
        self.assertEqual(SIZE,"720x1280")
        self.assertEqual(FPS,30)
        self.assertEqual(EXPECTED_DURATION,70.425)

    def test_scene_command_uses_true_frame_count_not_approximate_seconds(self):
        cmd=ffmpeg_command("/usr/bin/ffmpeg",Path("E01V2_SCENE_03.jpg"),
                           Path("seg_03.mp4"),184)
        self.assertIn("-frames:v",cmd)
        self.assertEqual(cmd[cmd.index("-frames:v")+1],"184")
        self.assertIn("-an",cmd)
        self.assertIn("libx264",cmd)
        self.assertIn("720x1280",cmd[cmd.index("-vf")+1])

    def test_segment_boundaries_reject_invalid_frame_count(self):
        for n in (0,-10,1000):
            with self.subTest(n=n):
                with self.assertRaisesRegex(ProductionError,"invalid_clip_params"):
                    ffmpeg_command("ffmpeg",Path("E01V2_SCENE_01.jpg"),
                                   Path("seg_01.mp4"),n)

    def test_source_paths_are_strictly_named(self):
        with self.assertRaisesRegex(ProductionError,"invalid_clip_params"):
            ffmpeg_command("ffmpeg",Path("other.jpg"),Path("seg_01.mp4"),170)
        with self.assertRaisesRegex(ProductionError,"invalid_clip_params"):
            ffmpeg_command("ffmpeg",Path("E01V2_SCENE_01.jpg"),Path("final.mp4"),170)

    def test_missing_assets_always_block_real_render(self):
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp:
            d=Path(temp)
            with self.assertRaisesRegex(ProductionError,"zip_sha_or_size_not_exact"):
                ensure_sources(root,d/"missing.zip",d/"wav.wav",d/"cap.ass")

    def test_cannot_overwrite_repo_contract_directories(self):
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp:
            d=Path(temp)
            with self.assertRaisesRegex(ProductionError,"protected_output"):
                run(root,d/"missing.zip",d/"audio.wav",d/"cap.ass",root/"contracts")

    def test_rendering_does_not_use_paid_or_publisher_api(self):
        import inspect
        from agents import e01_visual_roughcut_render as module
        code=inspect.getsource(module)
        for blocked in ("youtube.upload","tiktok.publish","stripe.checkout",
                        "HTTP POST","openai.api_key"):
            self.assertNotIn(blocked,code)

    def test_positive_release_status_does_not_exist_in_renderer(self):
        import inspect
        from agents import e01_visual_roughcut_render as module
        code=inspect.getsource(module)
        self.assertIn('"publication_authorized":False',code)
        self.assertIn('"commercial_licenses_cleared":False',code)
        self.assertIn('"full_1080x1920_master_approved":False',code)
        self.assertIn("LOCAL_12_SCENE_ROUGHCUT_REBUILT_DECODED_NOT_MASTER",code)


if __name__=="__main__":
    unittest.main()
