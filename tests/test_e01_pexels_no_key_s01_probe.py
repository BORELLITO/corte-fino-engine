"""Pure hard gates for one public no-login cinematic stock proof."""
import unittest
from agents.e01_pexels_no_key_s01_probe import (
    allow_media_url,BASE,MAX_BYTES,TARGET_SECONDS,PREVIEW_SECONDS)

class TestE01PexelsNoKey(unittest.TestCase):
    def test_only_pexels_owned_https_mp4_media_is_allowed(self):
        self.assertTrue(allow_media_url(
          "https://videos.pexels.com/video-files/8860242/8860242-uhd_4096_2160_25fps.mp4"))
        for value in [
          "http://videos.pexels.com/video-files/a.mp4",
          "https://videos.pexels.com.evil.test/video-files/a.mp4",
          "https://www.pexels.com/download/video/8860242/",
          "https://videos.pexels.com/private/a.mp4",
          "https://example.com/video-files/a.mp4",
          "file:///tmp/private.mp4"]:
            with self.subTest(value=value):
                self.assertFalse(allow_media_url(value))
    def test_no_false_rights_or_master(self):
        for name in [
          "individual_releases_evaluated","rights_cleared",
          "scene_meets_script_narrative","same_actor_as_other_scenes",
          "notebook_closed_verified","rain_visible_verified",
          "actual_camera_footage_proven_beyond_source_claim",
          "approved_for_master","publication_authorized"]:
            self.assertIs(BASE[name],False,name)
        self.assertTrue(BASE["no_api_key"])
        self.assertTrue(BASE["no_payment"])
        self.assertTrue(BASE["no_authentication"])
    def test_scene_duration_and_size_limit(self):
        self.assertEqual(TARGET_SECONDS,5.74)
        self.assertGreater(PREVIEW_SECONDS,TARGET_SECONDS)
        self.assertLessEqual(MAX_BYTES,500_000_000)

if __name__=="__main__":
    unittest.main()
