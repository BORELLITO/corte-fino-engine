"""Fail-closed tests for bounded E01 six-second render; do not call provider."""
import math
import unittest
from agents.e01_ltx23_s01_v2_render import (
    FRAME_RATE,EXPECTED_FRAMES,REQUEST_SECONDS,SCENE_SECONDS,
    SEED,WIDTH,HEIGHT,STATUS_BASE,provider_running,classify_public_gpu_quota,assess_video_eligibility
)

class TestE01Ltx23S01V2(unittest.TestCase):
    def test_real_duration_covers_scene(self):
        self.assertEqual(REQUEST_SECONDS,5.8)
        self.assertEqual(SCENE_SECONDS,5.74)
        self.assertEqual(EXPECTED_FRAMES,145)
        self.assertGreater((EXPECTED_FRAMES-1)/FRAME_RATE,SCENE_SECONDS)
        self.assertEqual((WIDTH,HEIGHT),(480,848))
        self.assertLess(abs(WIDTH/HEIGHT-9/16),0.02)
    def test_original_creator_and_storyboard_not_replaced(self):
        self.assertEqual(STATUS_BASE["episode_id"],"VNC-W01-E1")
        self.assertEqual(STATUS_BASE["scene_id"],"VNC-E01V2-S01")
        self.assertEqual(STATUS_BASE["media_origin"],"AI_GENERATED_FICTIONAL_VIDEO")
        self.assertEqual(STATUS_BASE["requested_seed"],SEED)
    def test_fail_closed_without_release(self):
        for k in ("origin_and_usage_license_review_complete",
                  "visual_continuity_verified",
                  "closed_notebook_and_rain_visually_verified",
                  "native_master_1080x1920_30fps",
                  "rights_cleared","full_episode_completed",
                  "approved_for_master","publication_authorized",
                  "paid_service_used","human_login_performed"):
            self.assertIs(STATUS_BASE[k],False,k)
    def test_one_shot_trigger_only_and_no_cron(self):
        from pathlib import Path
        yaml=(Path(".github/workflows/verbo-no-chao-e01-s01-v2-probe.yml")
              .read_text(encoding="utf-8"))
        self.assertIn("e01_ltx23_s01_one_shot_trigger_20261118.json",yaml)
        self.assertIn("vnc-e01-s01-one-shot-free-retest-20261118",yaml)
        self.assertNotIn("workflow_dispatch:",yaml)
        self.assertIn("github.event_name == 'push'",yaml)
        self.assertIn("git diff-tree --no-commit-id --name-status",yaml)
        self.assertIn("git rev-list --count",yaml)
        self.assertIn("persist-credentials: false",yaml)
        self.assertIn("publication_authorized",yaml)
        self.assertNotIn("schedule:",yaml)
        self.assertNotIn("pull_request:",yaml)
        self.assertIn("cancel-in-progress: false",yaml)
    def test_physical_qa_rejects_partial_or_wrong_video(self):
        valid={
            "full_stream_decoded":True,"covers_requested_scene":True,
            "portrait_within_2pct":True,"codec":"h264",
            "width":480,"height":848,"frame_rate":"24/1",
            "reported_frames":"145","sha256":"a"*64
        }
        self.assertEqual(assess_video_eligibility(valid),
            "PHYSICAL_AI_PREVIEW_ELIGIBLE_FOR_EDITORIAL_REVIEW_ONLY")
        failures=[
            ("covers_requested_scene",False,"BLOCKED_VIDEO_SHORTER_THAN_SCENE"),
            ("portrait_within_2pct",False,"BLOCKED_VIDEO_WRONG_ASPECT"),
            ("width",320,"BLOCKED_VIDEO_BELOW_PREVIEW_RESOLUTION"),
            ("height",480,"BLOCKED_VIDEO_BELOW_PREVIEW_RESOLUTION"),
            ("frame_rate","0/0","BLOCKED_VIDEO_INVALID_FPS"),
            ("frame_rate","1/1","BLOCKED_VIDEO_INVALID_FPS"),
            ("reported_frames","30","BLOCKED_VIDEO_TOO_FEW_FRAMES"),
            ("codec","mpeg4","BLOCKED_VIDEO_UNSUPPORTED_CODEC"),
            ("full_stream_decoded",False,"BLOCKED_VIDEO_NOT_FULLY_DECODED"),
            ("sha256","bad","BLOCKED_VIDEO_MISSING_SHA256"),
        ]
        for key,value,expect in failures:
            with self.subTest(key=key,value=value):
                mutated=dict(valid)
                mutated[key]=value
                self.assertEqual(assess_video_eligibility(mutated),expect)
    def test_provider_quota_report_is_explicit_and_without_urls(self):
        text=("You have exceeded your ZeroGPU quota (112s requested vs. 9s left). "
              "Try again in 7:21:22. Authenticate with a token URL.")
        q=classify_public_gpu_quota(text)
        self.assertEqual(q["requested_gpu_seconds"],112)
        self.assertEqual(q["available_gpu_seconds"],9)
        self.assertEqual(q["provider_reset_hint_seconds"],26482)
        self.assertFalse(q["retry_without_approval"])
        self.assertNotIn("http",str(q))
        self.assertIsNone(classify_public_gpu_quota("Some unrelated error"))
    def test_provider_not_running_is_no_op(self):
        self.assertTrue(provider_running({"runtime":{"stage":"RUNNING"}}))
        for obj in [{},{"runtime":{"stage":"SLEEPING"}},
                    {"runtime":{"stage":"BUILDING"}},{"runtime":{}},
                    {"runtime":None},None,[],{"runtime":{"stage":"NOT_RUNNING"}}]:
            with self.subTest(obj=obj):
                self.assertFalse(provider_running(obj))
if __name__=="__main__":
 unittest.main()
