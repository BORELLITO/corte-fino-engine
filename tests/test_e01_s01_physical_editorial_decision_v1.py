"""S01 editorial decision ledger must preserve physical vs aesthetic distinctions."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FILE=ROOT/"contracts/e01_s01_single_take_physical_editorial_decisions_20261119_v1.json"


class TestPhysicalEditorialReview(unittest.TestCase):
    def setUp(self):
        self.doc=json.loads(FILE.read_text(encoding="utf-8"))
        self.sources={r["video_id"]:r for r in self.doc["sources"]}

    def test_no_release_rights_or_master_can_be_inferred(self):
        self.assertEqual(self.doc["project_id"],"VERBO_NO_CHAO_EXCLUSIVO")
        self.assertEqual(self.doc["scene_id"],"VNC-E01V2-S01")
        self.assertIs(self.doc["publication_authorized"],False)
        self.assertIs(self.doc["master_allowed"],False)
        self.assertIs(self.doc["commercial_rights_cleared"],False)
        self.assertEqual(set(self.sources),{4510748,28174743,7026683})
        for source in self.sources.values():
            self.assertIs(source["rights_cleared"],False)
            self.assertTrue(source["source_url"].startswith("https://www.pexels.com/video/"))

    def test_genuine_source_bytes_and_rejections_stay_pinned(self):
        pinned={
            4510748:("c9893c53a3c51d9e6244e772ad16553ff3319db8b7bd070a9744800f316a2fa0",27473889),
            7026683:("53bc1ff9d0a34528b12c7f0095e2ed61797943391ddf900ab740b1949c38a7dc",25994187),
        }
        for ident,(sha,amount) in pinned.items():
            row=self.sources[ident]
            self.assertEqual(row["decision"],"REJECTED_FOR_S01_EDITORIAL")
            self.assertEqual(row["source_sha256"],sha)
            self.assertEqual(row["bytes"],amount)
            self.assertIs(row["physical_full_video_decode"],True)
            self.assertEqual(row["sampled_frame_seconds"],[0.5,2.8,5.4])
            self.assertEqual(len(row["contact_sheet_sha256"]),64)

    def test_oversized_source_is_not_falsely_labeled_as_editorial_reject(self):
        row=self.sources[28174743]
        self.assertEqual(row["decision"],"TECHNICAL_INTAKE_BLOCKED_EDITORIAL_UNASSESSED")
        self.assertEqual(row["failure_code"],"oversized_source")
        self.assertIsNone(row["source_sha256"])
        self.assertIsNone(row["bytes"])
        self.assertIs(row["physical_full_video_decode"],False)
        self.assertEqual(row["sampled_frame_seconds"],[])

    def test_newer_post_qa_decision_overrides_pre_qa_search_state(self):
        research=json.loads((ROOT/"contracts/e01_s01_single_take_stock_candidates_20261119_v2.json").read_text(encoding="utf-8"))
        self.assertEqual(research["candidates"][0]["video_id"],7026683)
        self.assertEqual(research["candidates"][0]["editorial_status"],"PENDING_PHYSICAL_AND_FRAME_QA")
        self.assertEqual(self.sources[7026683]["decision"],"REJECTED_FOR_S01_EDITORIAL")


if __name__=="__main__":
    unittest.main()
