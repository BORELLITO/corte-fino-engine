"""Fail-closed tests for bounded E01 six-second render; do not call provider."""
import math
import unittest
from agents.e01_ltx23_s01_v2_render import (
    FRAME_RATE,EXPECTED_FRAMES,REQUEST_SECONDS,SCENE_SECONDS,
    SEED,WIDTH,HEIGHT,STATUS_BASE,provider_running,classify_public_gpu_quota
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
