"""Physical-candidate contract checks, no download and no external generation."""
import inspect
import unittest
from agents import e01_s04_pexels_7977614_physical_qa as qa


class TestS04PexelsContract(unittest.TestCase):
    def test_exact_scene_and_source(self):
        self.assertEqual(qa.SCENE, "VNC-E01V2-S04")
        self.assertEqual(qa.VIDEO_ID, 7977614)
        self.assertAlmostEqual(qa.REQUIRED_SECONDS, 5.82)
        self.assertIn("/7977614/", qa.DOWNLOAD)

    def test_two_full_windows_need_more_than_11_seconds(self):
        self.assertGreater(14, 2 * qa.REQUIRED_SECONDS)

    def test_physical_validator_has_no_release_claim(self):
        code = inspect.getsource(qa.analyze)
        for phrase in ('"editorial_approved": False',
                       '"commercial_rights_cleared": False',
                       '"allowed_in_master": False',
                       '"publication_authorized": False'):
            self.assertIn(phrase, code)
        self.assertNotIn("client.submit(", code)
        self.assertNotIn("workflow_dispatch", code)

    def test_real_frames_not_presented_as_originals(self):
        code = inspect.getsource(qa.analyze)
        self.assertIn('"is_original_unchanged": False', code)
        self.assertIn('"full_source_video_decoded"', code)


if __name__ == "__main__":
    unittest.main()
