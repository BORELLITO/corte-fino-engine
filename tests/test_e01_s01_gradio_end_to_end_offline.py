"""Offline end-to-end rehearsal of the actual S01 provider/render/anchor handoff.

This intentionally creates a colorful *synthetic test pattern*, NOT a visual
candidate for VERBO NO CHÃO. Mocked Gradio provider means zero GPU, zero
provider credits, zero login, zero account access.
"""
from __future__ import annotations
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from agents import e01_ltx23_s01_v2_render as render
from agents.e01_s01_video_anchor import make_candidate_frames
from agents.e01_stock_candidates import StockIntakeError

@unittest.skipUnless(
    shutil.which("ffmpeg") and shutil.which("ffprobe"),
    "FFmpeg required for offline physical integration rehearsal"
)
class TestS01GradioOfflineEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture_dir=tempfile.TemporaryDirectory()
        cls.fixture=Path(cls.fixture_dir.name)/"synthetic_pattern_NEVER_E01_ASSET.mp4"
        command=[
           "ffmpeg","-nostdin","-y","-v","error",
           "-f","lavfi","-i","testsrc2=size=480x848:rate=24",
           "-t","5.85","-an","-threads","2",
           "-c:v","libx264","-preset","ultrafast","-crf","37",
           "-pix_fmt","yuv420p",str(cls.fixture)]
        subprocess.run(command,check=True,capture_output=True,timeout=100)
        assert cls.fixture.exists() and cls.fixture.stat().st_size>20000
    @classmethod
    def tearDownClass(cls):
        cls.fixture_dir.cleanup()

    def test_mocked_gradio_returns_video_full_report_and_five_reference_frames(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination=Path(tmp)/"preview"
            report_file=destination/"report.json"
            provider_calls=[]
            fixture=self.fixture

            class FakeClient:
                def __init__(self,space,verbose=False):
                    self.space=space
                    self.verbose=verbose
                def predict(self,*args,**kwargs):
                    provider_calls.append((self.space,args,kwargs))
                    return [str(fixture),"test metadata",42251]
            fake_module=types.ModuleType("gradio_client")
            fake_module.Client=FakeClient
            with patch.dict(sys.modules,{"gradio_client":fake_module}), \
                 patch.object(render,"OUT",destination), \
                 patch.object(render,"REPORT",report_file), \
                 patch.object(render,"preflight",return_value=(True,"RUNNING")):
                code=render.run()
            self.assertEqual(code,0)
            self.assertEqual(len(provider_calls),1)
            space,args,kwargs=provider_calls[0]
            self.assertEqual(space,"Lightricks/LTX-2-3")
            self.assertIsNone(args[0])
            self.assertEqual(args[1],render.PROMPT)
            self.assertEqual(args[2],5.8)
            self.assertEqual(args[-2:],[render.HEIGHT,render.WIDTH])
            self.assertEqual(kwargs,{"api_name":"/generate_video"})
            metadata=json.loads(report_file.read_text(encoding="utf-8"))
            self.assertEqual(metadata["status"],
                "PHYSICAL_AI_PREVIEW_ELIGIBLE_FOR_EDITORIAL_REVIEW_ONLY")
            self.assertTrue(metadata["technically_eligible_for_editorial"])
            self.assertFalse(metadata["approved_for_master"])
            self.assertFalse(metadata["publication_authorized"])
            self.assertFalse(metadata["rights_cleared"])
            self.assertGreaterEqual(metadata["sampled_jpeg_count"],5)
            self.assertGreaterEqual(metadata["media"]["duration_seconds"],5.74)
            self.assertTrue(metadata["media"]["full_stream_decoded"])
            clip=destination/metadata["video_file"]
            self.assertEqual(metadata["media"]["sha256"],
                hashlib.sha256(clip.read_bytes()).hexdigest())
            anchors=make_candidate_frames(
                clip,report_file,destination/"continuity_reference_review")
            self.assertTrue(anchors["motion_check"]["motion_signal_detected"])
            self.assertEqual(len(anchors["samples"]),5)
            self.assertFalse(anchors["reference_promoted_to_i2v"])
            self.assertFalse(anchors["reference_for_other_scenes_approved"])
            self.assertFalse(anchors["publication_authorized"])
            self.assertEqual(anchors["source_sha256"],metadata["media"]["sha256"])
            for sample in anchors["samples"]:
                self.assertTrue((destination/"continuity_reference_review"/sample["name"]).is_file())
            self.assertTrue((destination/"continuity_reference_review"/anchors["contact_sheet_file"]).is_file())

    def test_provider_no_file_result_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination=Path(tmp)/"blocked"
            file=destination/"report.json"
            class FakeClient:
                def __init__(self,*a,**kw):pass
                def predict(self,*a,**kw):return [None]
            fake_module=types.ModuleType("gradio_client")
            fake_module.Client=FakeClient
            with patch.dict(sys.modules,{"gradio_client":fake_module}), \
                 patch.object(render,"OUT",destination), \
                 patch.object(render,"REPORT",file), \
                 patch.object(render,"preflight",return_value=(True,"RUNNING")):
                code=render.run()
            self.assertEqual(code,2)
            metadata=json.loads(file.read_text(encoding="utf-8"))
            self.assertEqual(metadata["status"],"BLOCKED_PROVIDER_OR_TECHNICAL_RUNTIME")
            self.assertEqual(metadata["error_reason"],"provider_returned_no_video")
            self.assertFalse(metadata["publication_authorized"])
            self.assertFalse((destination/"continuity_reference_review").exists())

    def test_provider_not_running_makes_no_gradio_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination=Path(tmp)/"unavailable"
            file=destination/"report.json"
            fake_module=types.ModuleType("gradio_client")
            class ForbiddenClient:
                def __init__(self,*a,**kw):
                    raise AssertionError("No provider call allowed")
            fake_module.Client=ForbiddenClient
            with patch.dict(sys.modules,{"gradio_client":fake_module}), \
                 patch.object(render,"OUT",destination), \
                 patch.object(render,"REPORT",file), \
                 patch.object(render,"preflight",return_value=(False,"PAUSED")):
                code=render.run()
            self.assertEqual(code,2)
            metadata=json.loads(file.read_text(encoding="utf-8"))
            self.assertEqual(metadata["status"],"BLOCKED_PUBLIC_SPACE_NOT_RUNNING")
            self.assertFalse(metadata["publication_authorized"])
            self.assertFalse(any(destination.glob("*.mp4")))

if __name__=="__main__":
    unittest.main()
