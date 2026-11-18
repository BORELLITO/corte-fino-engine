"""Adversarial review assertions: no alternate stock becomes publishable by metadata edits."""
import copy
import json
import unittest
from agents.e01_stock_alt_review_gate import ROOT,EVIDENCE,verify
from agents.e01_stock_candidates import StockIntakeError

class TestE01StockAltReviewGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=json.loads((ROOT/EVIDENCE).read_text(encoding="utf-8"))
    def mod(self,edit):
        c=copy.deepcopy(self.original);edit(c);return c
    def test_physical_evidence_is_not_clearance(self):
        r=verify(ROOT)
        self.assertEqual(r["source_assets_verified"],4)
        self.assertEqual(r["editorially_rejected"],3)
        self.assertEqual(r["conditionally_retained"],1)
        self.assertEqual(r["approved_for_master"],0)
        self.assertFalse(r["publication_authorized"])
    def test_fake_releases_are_impossible(self):
        for key in ("reviewed_full_video_playback","visual_editorial_authorized_for_master",
                    "third_party_rights_cleared","narration_license_cleared",
                    "music_license_cleared","master_rendered","publication_authorized"):
            with self.subTest(key=key):
                p=self.mod(lambda x:x.update({key:True}))
                with self.assertRaises(StockIntakeError):verify(ROOT,p)
    def test_changed_hash_or_decision_is_rejected(self):
        for field,value in (("sha256","a"*64),
                            ("decision","APPROVED_FOR_MASTER"),
                            ("allowed_for_master",True),
                            ("rights_cleared",True),
                            ("video_id",1234),
                            ("full_stream_decoded",False),
                            ("duration_seconds",6.66)):
            with self.subTest(field=field):
                p=self.mod(lambda x:x["review_decisions"][0].update({field:value}))
                with self.assertRaises(StockIntakeError):verify(ROOT,p)
    def test_missing_and_duplicate_evidence_rejected(self):
        p=self.mod(lambda x:x["review_decisions"].pop())
        with self.assertRaises(StockIntakeError):verify(ROOT,p)
        p=self.mod(lambda x:x["review_decisions"][1].update(asset_id="E01V2-ALT-S03-B"))
        with self.assertRaises(StockIntakeError):verify(ROOT,p)
    def test_provenance_alteration_rejected(self):
        for field,value in (("source_run_id",10),("source_contact_sha256","a"*64),
                            ("source_samples",9),("source_artifact_id",100)):
            p=self.mod(lambda x:x.update({field:value}))
            with self.assertRaises(StockIntakeError):verify(ROOT,p)
if __name__=="__main__":
    unittest.main()
