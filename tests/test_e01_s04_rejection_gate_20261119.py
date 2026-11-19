"""Scene-specific E01 S04 editorial denials, with intact historical source list."""
import json
import unittest
from agents.e01_source_precision_gate import (
    ROOT, POLICY, preflight_stock, s04_rejected_for_scene, verify, EXCLUDED_PEXELS
)
from agents.e01_stock_candidates import StockIntakeError

class TestS04Rejections(unittest.TestCase):
    def test_physically_rejected_cannot_be_s04_reselected(self):
        canonical = json.loads((ROOT/POLICY).read_text(encoding="utf-8"))
        query = canonical["scenes"][3]["locked_search_queries_en"][0]
        candidates = (
            (7977614,"https://www.pexels.com/video/person-using-a-quill-7977614/"),
            (11137423,"https://www.pexels.com/video/close-up-on-writing-with-ink-pen-11137423/"),
        )
        for ident,url in candidates:
            with self.subTest(video_id=ident):
                with self.assertRaisesRegex(StockIntakeError,"source_precision:s04_real_frame_editorially_rejected"):
                    preflight_stock("VNC-E01V2-S04",ident,url,query)

    def test_scoped_rejection_does_not_pollute_global_source_hashes_or_ids(self):
        self.assertNotIn(7977614,EXCLUDED_PEXELS)
        self.assertNotIn(11137423,EXCLUDED_PEXELS)
        self.assertTrue(s04_rejected_for_scene(ROOT,"VNC-E01V2-S04",7977614))
        self.assertFalse(s04_rejected_for_scene(ROOT,"VNC-E01V2-S10",7977614))
        self.assertEqual(verify(ROOT)["scene_briefs"],12)

    def test_rejection_ledger_is_fail_closed_and_has_full_sha_proofs(self):
        from agents.e01_source_precision_gate import S04_REJECTIONS
        r=json.loads((ROOT/S04_REJECTIONS).read_text(encoding="utf-8"))
        self.assertFalse(r["allowed_in_master"])
        self.assertFalse(r["publication_authorized"])
        self.assertEqual(len(r["evidence"]),2)
        for record in r["evidence"]:
            self.assertTrue(record["fully_decoded"])
            self.assertGreaterEqual(record["frames_reviewed"],12)
            self.assertEqual(len(record["source_sha256"]),64)
            self.assertFalse(record["allowed_for_s04_master"])

    def test_other_new_source_remains_research_only(self):
        canonical=json.loads((ROOT/POLICY).read_text(encoding="utf-8"))
        query=canonical["scenes"][3]["locked_search_queries_en"][0]
        response=preflight_stock("VNC-E01V2-S04",99999981,
                                 "https://www.pexels.com/video/symbolic-old-paper-99999981/",
                                 query)
        self.assertEqual(response["status"],"ELIGIBLE_FOR_PHYSICAL_MEDIA_REVIEW_ONLY")
        self.assertFalse(response["editorially_approved"])
        self.assertFalse(response["publication_authorized"])

if __name__=="__main__":
    unittest.main()
