"""E01 replacements do not inherit rights from metadata or samples."""
import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch
from agents.e01_stock_alternatives import ROOT,PATH,check,execute
from agents.e01_stock_candidates import StockIntakeError

class TestE01StockAlternatives(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=json.loads((ROOT/PATH).read_text(encoding="utf-8"))

    def mutated(self,fn):
        c=copy.deepcopy(self.catalog);fn(c);return c

    def test_all_four_research_replacements_are_unapproved(self):
        r=check(ROOT)
        self.assertEqual(r["candidate_count"],4)
        self.assertFalse(r["rights_cleared"])
        self.assertFalse(r["publication_authorized"])

    def test_forged_release_rejected(self):
        for key in ("third_party_rights_cleared","master_rendered",
                    "publication_authorized","full_video_review_completed"):
            with self.subTest(key=key):
                c=self.mutated(lambda x:x.update({key:True}))
                with self.assertRaises(StockIntakeError):check(ROOT,c)
        for key,val in (("physical_media_checked",True),("physical_sha256","f"*64),
                        ("allowed_for_final_master",True),("rights_status","CLEARED"),
                        ("editorial_status","APPROVED")):
            with self.subTest(key=key):
                c=self.mutated(lambda x:x["candidates"][0].update({key:val}))
                with self.assertRaises(StockIntakeError):check(ROOT,c)

    def test_rejected_original_and_duplicate_video_blocked(self):
        for val in (40417800,13017069,0):
            c=self.mutated(lambda x:x["candidates"][0].update(video_id=val))
            with self.assertRaises(StockIntakeError):check(ROOT,c)

    def test_untrusted_host_and_url_blocked(self):
        c=self.mutated(lambda x:x["candidates"][0].update(
            download_url="https://evil.invalid/video-files/34479513/foo.mp4"))
        with self.assertRaises(StockIntakeError):check(ROOT,c)
        c=self.mutated(lambda x:x["candidates"][1].update(
            download_url="https://videos.pexels.com/video-files/6860448/x.mp4?token=1"))
        with self.assertRaises(StockIntakeError):check(ROOT,c)

    def test_short_or_horizontal_clip_blocked(self):
        for patch_data in ({"duration_page_seconds":1},{"width":1920,"height":1080}):
            c=self.mutated(lambda x:x["candidates"][0].update(patch_data))
            with self.assertRaises(StockIntakeError):check(ROOT,c)

    def test_fake_physical_probe_cannot_be_reported_as_success(self):
        with patch("agents.e01_stock_alternatives.probe_item",side_effect=StockIntakeError("no bytes")):
            import tempfile
            with tempfile.TemporaryDirectory() as d:
                report=execute(ROOT,Path(d))
                self.assertEqual(report["status"],"BLOCKED_ALTERNATIVES_QA_INCOMPLETE")
                self.assertFalse(report["publication_authorized"])
                self.assertFalse(report["visual_clearance"])

if __name__=="__main__":
    unittest.main()
