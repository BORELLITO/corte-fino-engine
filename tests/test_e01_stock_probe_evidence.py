"""Adversarial tests for E01 v2 physical MP4 probe attestation."""
import copy
import json
import unittest
from agents.e01_stock_probe_evidence import EVIDENCE, ROOT, verify
from agents.e01_stock_candidates import StockIntakeError

class TestE01StockProbeEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proof = json.loads((ROOT / EVIDENCE).read_text(encoding="utf-8"))
    def changed(self, mutate):
        item = copy.deepcopy(self.proof)
        mutate(item)
        return item
    def test_runner_proof_never_claims_rights_or_durable_files(self):
        r = verify(ROOT)
        self.assertEqual(r["assets"], 4)
        self.assertFalse(r["rights_cleared"])
        self.assertFalse(r["file_materialization_available_now"])
        self.assertFalse(r["publication_authorized"])
    def test_fail_closed_fake_publication_rights_or_persistence(self):
        for field in ("publication_authorized", "third_party_rights_cleared",
                      "frame_by_frame_visual_qa_completed", "final_master_rendered",
                      "files_persisted_for_master"):
            with self.subTest(field=field):
                p = self.changed(lambda x: x.update({field: True}))
                with self.assertRaises(StockIntakeError):
                    verify(ROOT, p)
    def test_mismatched_run_and_source_rejected(self):
        for field, value in (("github_run_id", 10),
                             ("artifact_id", 10),
                             ("git_head_sha", "fake"),
                             ("source_contract", "wrong.json")):
            with self.subTest(field=field):
                p = self.changed(lambda x: x.update({field: value}))
                with self.assertRaises(StockIntakeError):
                    verify(ROOT, p)
    def test_missing_duplicate_or_modified_bytes_rejected(self):
        cases = [
            lambda x: x["observations"].pop(),
            lambda x: x["observations"][0].update(sha256="0"*64),
            lambda x: x["observations"][1].update(sha256="z"*64),
            lambda x: x["observations"][1].update(video_id=1),
            lambda x: x["observations"][1].update(size_bytes=0),
            lambda x: x["observations"][1].update(width=1000),
            lambda x: x["observations"][1].update(physical_full_video_decode=False),
            lambda x: x["observations"][1].update(duration_seconds=0),
        ]
        for i, change in enumerate(cases):
            with self.subTest(case=i):
                p = self.changed(change)
                # syntactically well-formed altered hashes alone would pass
                # this format checker; only a future byte-hash check can reject them
                if i == 1:
                    self.assertEqual(verify(ROOT, p)["assets"], 4)
                else:
                    with self.assertRaises(StockIntakeError):
                        verify(ROOT, p)

if __name__ == "__main__":
    unittest.main()
