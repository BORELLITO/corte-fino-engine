"""Do not allow declined stock footage to re-enter the E01 master by metadata edits."""
import copy
import json
import unittest
from agents.e01_stock_editorial_decision import ROOT, PATH, review
from agents.e01_stock_candidates import StockIntakeError

class TestE01StockEditorialDecision(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=json.loads((ROOT/PATH).read_text(encoding="utf-8"))
    def amended(self,callback):
        document=copy.deepcopy(self.source);callback(document);return document
    def test_review_preserves_three_rejections_and_zero_approvals(self):
        result=review(ROOT)
        self.assertEqual(result["rejected"],3)
        self.assertEqual(result["conditional"],1)
        self.assertEqual(result["assets_approved_for_master"],0)
        self.assertFalse(result["publication_authorized"])
    def test_media_only_sampling_cannot_claim_full_review(self):
        for field in ("reviewed_video_full_playback","rights_cleared",
                      "first_party_music_license_cleared","voice_runtime_license_cleared",
                      "editorial_release_authorized","master_rendered","publication_authorized"):
            with self.subTest(field=field):
                x=self.amended(lambda y:y.update({field:True}))
                with self.assertRaises(StockIntakeError):review(ROOT,x)
    def test_cannot_launder_rejected_or_conditional_as_approved(self):
        for i in range(4):
            x=self.amended(lambda y:y["decisions"][i].update(
                decision="APPROVED",allowed_for_master=True))
            with self.assertRaises(StockIntakeError):review(ROOT,x)
    def test_missing_or_duplicate_candidate_fails(self):
        x=self.amended(lambda y:y["decisions"].pop())
        with self.assertRaises(StockIntakeError):review(ROOT,x)
        x=self.amended(lambda y:y["decisions"][1].update(
            asset_id=y["decisions"][0]["asset_id"]))
        with self.assertRaises(StockIntakeError):review(ROOT,x)
    def test_invalid_contact_sheet_sha_rejected(self):
        x=self.amended(lambda y:y.update(contact_sheet_sha256="a"*64))
        with self.assertRaises(StockIntakeError):review(ROOT,x)

if __name__=="__main__":
    unittest.main()
