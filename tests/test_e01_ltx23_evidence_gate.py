"""Real motion report is evidence of *preview only*, never rights or master."""
import copy
import json
import unittest
from agents.e01_ltx23_evidence_gate import EVIDENCE,ROOT,validate
from agents.e01_stock_candidates import StockIntakeError

class TestE01Ltx23Evidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=json.loads((ROOT/EVIDENCE).read_text(encoding="utf-8"))
    def rejected(self,edit):
        data=copy.deepcopy(self.base)
        edit(data)
        with self.assertRaises(StockIntakeError):
            validate(ROOT,data)
    def test_source_is_verified_and_release_still_denied(self):
        s=validate(ROOT)
        self.assertEqual(s["source_sha256"],
                         "d682edd7c783ac0c527e05548b83e654437cdfbff0d7b641478e1bf3bd895738")
        self.assertFalse(s["rights_and_master_release"])
        self.assertFalse(s["publication_authorized"])
    def test_fake_sha_size_or_source_denied(self):
        self.rejected(lambda d:d["media"].update(sha256="a"*64))
        self.rejected(lambda d:d["media"].update(bytes=1))
        self.rejected(lambda d:d.update(source_model="other_model"))
        self.rejected(lambda d:d.update(generation_type="CAMERA_CAPTURED"))
    def test_cannot_promote_without_real_authorization(self):
        for k in ["rights_cleared","editorially_approved","visual_scene_complete",
                  "approved_for_master","publication_authorized"]:
            with self.subTest(k=k):
                self.rejected(lambda d:d.update({k:True}))
        self.rejected(lambda d:d["media"].update(native_master_1080x1920=True))
    def test_mismatch_and_original_script_locks(self):
        self.rejected(lambda d:d.update(requested_scene_end_seconds=2.04))
        self.rejected(lambda d:d.update(correct_e01_audio_sha256="0"*64))
        self.rejected(lambda d:d["frame_evaluation"].update(violations=[]))
        self.rejected(lambda d:d["frame_evaluation"].update(editorial_decision="APPROVED"))
if __name__=="__main__":
    unittest.main()
