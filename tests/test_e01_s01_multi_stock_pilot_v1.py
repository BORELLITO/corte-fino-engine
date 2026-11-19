"""No-AI video-source montage: fast offline adversarial coverage."""
import unittest
from unittest.mock import patch
from agents import e01_s01_multi_stock_pilot_v1 as m


class TestS01RealStock(unittest.TestCase):
    def test_storyboard_unchanged(self):
        self.assertTrue(m.verify_story())
        self.assertTrue(m.assert_inputs())

    def test_exact_original_sources_three(self):
        self.assertEqual([x["id"] for x in m.INPUTS],[8860242,4458845])
        self.assertEqual(m.FRAME_COUNT,173)
        self.assertEqual(m.CANVAS,(720,1280))
        self.assertLess(abs(m.FRAME_COUNT/m.FPS-m.TARGET),0.03)

    def test_untrusted_redirect_rejected_before_download(self):
        class Fake:pass
        h=m.StrictPexels(4458845)
        for url in (
            "https://not-pexels.example/video-files/4458845/a.mp4",
            "https://videos.pexels.com/video-files/999/a.mp4",
            "http://videos.pexels.com/video-files/4458845/a.mp4",
            "https://videos.pexels.com/video-files/4458845/a.pdf",
        ):
            with self.subTest(url=url),self.assertRaises(m.PilotError):
                h.redirect_request(Fake(),None,302,"",{},url)

    def test_forged_timeline_or_license_path_rejected(self):
        with patch.object(m,"FRAME_COUNT",180),self.assertRaises(m.PilotError):
            m.assert_inputs()
        altered=[dict(x) for x in m.INPUTS]
        altered[1]["page"]="https://evil.example/4458845/"
        with patch.object(m,"INPUTS",altered),self.assertRaises(m.PilotError):
            m.assert_inputs()

    def test_never_publish_or_fabricate_missing_media(self):
        with patch.object(m,"download_source",side_effect=m.PilotError("test_no_media")):
            with patch.object(m,"OUTPUT", __import__("pathlib").Path(__import__("tempfile").mkdtemp())):
                status=m.main()
        self.assertEqual(status,2)


if __name__=="__main__":
    unittest.main()
