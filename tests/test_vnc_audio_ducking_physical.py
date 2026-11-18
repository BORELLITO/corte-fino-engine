"""No-provider FFmpeg sound-chain smoke; synthetic audio only."""
import inspect
import math
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from orchestrator.render import RenderError, render_package


class TestRenderHardening(unittest.TestCase):
    def test_existing_output_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "existing.mp4"
            output.write_bytes(b"protected baseline")
            with self.assertRaisesRegex(RenderError, "refuse_overwrite_existing_output"):
                render_package(root, {"assets": [{"path": "unread.mp4"}], "output": {"file": "existing.mp4"}})
            self.assertEqual(output.read_bytes(), b"protected baseline")

    def test_nonfinite_asset_timing_cannot_enter_ffmpeg(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "dummy.mp4"
            video.write_bytes(b"synthetic source placeholder")
            for bad in (float("nan"), float("inf"), -float("inf")):
                with self.subTest(bad=bad):
                    with self.assertRaisesRegex(RenderError, "interval_invalid"):
                        render_package(root, {
                            "assets": [{"path": "dummy.mp4", "in": 0, "out": bad}],
                            "output": {"file": "never-created.mp4"},
                        })
                    self.assertFalse((root / "never-created.mp4").exists())

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "FFmpeg and FFprobe required for real source duration QA")
    def test_short_real_footage_cannot_be_auto_looped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "short_source.mp4"
            command = [
                "ffmpeg", "-nostdin", "-y", "-v", "error",
                "-f", "lavfi", "-i", "testsrc2=size=160x284:rate=24",
                "-t", "0.55", "-an", "-c:v", "mpeg4", str(source),
            ]
            build = subprocess.run(command, capture_output=True, text=True,
                                   timeout=30, check=False)
            self.assertEqual(build.returncode, 0, build.stderr[:300])
            with self.assertRaisesRegex(RenderError, "source_too_short_no_loops"):
                render_package(root, {
                    "assets": [{"path": source.name, "in": 0, "out": 2.0}],
                    "output": {"file": "should_not_exist.mp4"},
                })
            self.assertFalse((root / "should_not_exist.mp4").exists())

    def test_audio_engine_does_not_call_fixed_volume_ducking(self):
        source = inspect.getsource(render_package)
        self.assertIn("sidechaincompress=threshold", source)
        self.assertIn("asplit=2[voice][duckkey]", source)
        self.assertIn("alimiter=limit=0.96", source)
        self.assertNotIn("[voice][music]amix=", source)

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg required for real filter execution")
    def test_real_audio_filter_graph_decodes_without_errors(self):
        graph = (
            "[0:a]aresample=24000,volume=1.0,asplit=2[voice][duckkey];"
            "[1:a]aresample=24000,volume=0.12[music];"
            "[music][duckkey]sidechaincompress=threshold=0.035:ratio=8:"
            "attack=20:release=250[ducked];"
            "[voice][ducked]amix=inputs=2:duration=first:"
            "dropout_transition=2,alimiter=limit=0.96[aout]"
        )
        run = subprocess.run(
            ["ffmpeg", "-nostdin", "-hide_banner", "-v", "error",
             "-f", "lavfi", "-i", "sine=frequency=280:duration=1.2:sample_rate=24000",
             "-f", "lavfi", "-i", "sine=frequency=110:duration=1.2:sample_rate=24000",
             "-filter_complex", graph, "-map", "[aout]", "-f", "null", "-"],
            capture_output=True, text=True, timeout=30, check=False,
        )
        self.assertEqual(run.returncode, 0, run.stderr[:500])


if __name__ == "__main__":
    unittest.main()
