"""Regression tests for read-only S04 no-cost ZeroGPU metadata preflight."""
import inspect
import unittest

from agents.e01_s04_public_space_readonly_probe import (
    REQUIRED_DURATION_S, SCENE_ID, PUBLIC_SPACES, summarize_config, inspect_space
)


class TestS04FreeProviderReadiness(unittest.TestCase):
    def sample(self, maximum):
        return {
            "components":[
                {"id":1,"type":"slider","props":{"label":"Duration (seconds)","minimum":1,"maximum":maximum}},
                {"id":2,"type":"textbox","props":{"label":"Prompt"}},
                {"id":3,"type":"image","props":{"label":"Input image (optional)"}},
            ],
            "dependencies":[{"api_name":"run","inputs":[2,3,1]}],
        }

    def test_canonical_s04_duration(self):
        self.assertEqual(SCENE_ID,"VNC-E01V2-S04")
        self.assertEqual(REQUIRED_DURATION_S,5.82)

    def test_five_second_space_is_rejected_for_full_s04(self):
        summary=summarize_config("dummy",self.sample(5))
        self.assertFalse(summary["s04_5_82_seconds_in_visible_slider"])
        self.assertFalse(summary["source_video_generated"])

    def test_six_second_space_is_only_potential_not_master(self):
        summary=summarize_config("dummy",self.sample(6))
        self.assertTrue(summary["s04_5_82_seconds_in_visible_slider"])
        self.assertTrue(summary["possible_video_generation_endpoint"])
        self.assertEqual(summary["video_generation_compatible"],
                         "UNKNOWN_REQUIRES_EXACT_ENDPOINT_ROLE_DURATION_LICENSE_QA")
        self.assertFalse(summary["cost_authorized"])

    def test_frame_count_controls_are_not_mistaken_for_seconds(self):
        cfg=self.sample(5)
        cfg["components"].append({"id":4,"type":"slider",
            "props":{"label":"Number of Frames (more frames = longer video)",
                     "minimum":1,"maximum":145}})
        summary=summarize_config("sample",cfg)
        self.assertFalse(summary["s04_5_82_seconds_in_visible_slider"])
        self.assertTrue(summary["s04_possible_by_frame_control"])
        self.assertTrue(summary["visible_frame_controls"][0]["fps_unverified"])
        self.assertNotEqual(summary["video_generation_compatible"],"PASS")

    def test_all_endpoints_are_allowlisted_hf_space_config(self):
        self.assertEqual(len(PUBLIC_SPACES),3)
        for _,url in PUBLIC_SPACES:
            self.assertEqual(url.count("/config"),1)
            self.assertTrue(url.startswith("https://"))
            self.assertTrue(url.endswith(".hf.space/config"))

    def test_probe_never_posts_uploads_generates_or_publishes(self):
        source=inspect.getsource(inspect_space)
        self.assertIn('method="GET"',source)
        self.assertNotIn("POST",source)
        self.assertNotIn("queue/join",source)
        self.assertNotIn("generate_video(",source)
        self.assertNotIn("handle_file(",source)


if __name__=="__main__":
    unittest.main()
