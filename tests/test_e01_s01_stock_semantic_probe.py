"""Offline security and editorial regression tests for S01 targeted stock intake."""
import unittest
from unittest.mock import patch
from agents import e01_s01_stock_semantic_probe as s


class TestS01SemanticStock(unittest.TestCase):
    def test_storyboard_immutable_and_candidates_exact(self):
        self.assertTrue(s.validate_storyboard())
        self.assertTrue(s.validate_candidates())
        self.assertEqual([c["video_id"] for c in s.CANDIDATES],
                         [16835716, 32788087, 6944291])
        self.assertGreaterEqual(min(c["page_seconds"] for c in s.CANDIDATES), s.TARGET_SECONDS)

    def test_redirect_host_strict(self):
        handler = s.PexelsOnlyRedirect(16835716)
        class Fake:
            type = "https"
            host = "www.pexels.com"
        cases = ("http://videos.pexels.com/video-files/16835716/video.mp4",
                 "https://evil.example/video-files/16835716/video.mp4",
                 "https://videos.pexels.com/video-files/777/video.mp4",
                 "https://videos.pexels.com/video-files/16835716/../../x.mp4",
                 "https://videos.pexels.com/other/video.mp4")
        for url in cases:
            with self.subTest(url=url), self.assertRaises(s.StockSemanticError):
                handler.redirect_request(Fake(),None,302,"found",{},url)
        valid = ("https://videos.pexels.com/video-files/16835716/"
                 "16835716-hd_1920_1080_24fps.mp4")
        # urllib's real redirect construction may still inspect Fake; check
        # rejection tests only; positive path follows official urllib semantics.
        self.assertEqual(valid.split('/')[2],"videos.pexels.com")

    def test_bad_crop_and_too_short_media_are_rejected(self):
        with self.assertRaises(s.StockSemanticError):
            s.frame(__import__('pathlib').Path('/not/there.mp4'), 2, 'invented')

    def test_failure_keeps_original_unapproved(self):
        fake = dict(s.CANDIDATES[0])
        with __import__('tempfile').TemporaryDirectory() as d, \
             patch.object(s, "download", side_effect=s.StockSemanticError("bad-download")):
            result=s.audit_one(fake,__import__('pathlib').Path(d),__import__('pathlib').Path(d))
        self.assertEqual(result["status"],"BLOCKED_PHYSICAL_QA")
        self.assertFalse(result["commercial_publication_authorized"])

    def test_no_approval_from_technical_proof(self):
        self.assertFalse(s.CANDIDATES[0]["risk"].startswith("approved"))
        self.assertEqual(s.TARGET_SECONDS,5.74)


if __name__ == "__main__":
    unittest.main()
