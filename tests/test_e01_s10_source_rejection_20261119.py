"""Regression suite: physically reviewed S10 education footage cannot reenter."""
import json
import unittest

from agents.e01_source_precision_gate import (
    ROOT, POLICY, EXCLUDED_PEXELS, preflight_stock,
    s10_rejected_for_scene, verify, S10_REJECTIONS,
)
from agents.e01_stock_candidates import StockIntakeError


class S10DirectorRejection(unittest.TestCase):
    def test_rejected_real_4k_footage_is_blocked_only_for_s10(self):
        plan = json.loads((ROOT / POLICY).read_text(encoding="utf-8"))
        term = plan["scenes"][9]["locked_search_queries_en"][0]
        url = "https://www.pexels.com/video/a-woman-talking-to-her-friend-while-sitting-at-a-table-9490306/"
        with self.assertRaisesRegex(StockIntakeError,
                                    "source_precision:s10_real_frame_editorially_rejected"):
            preflight_stock("VNC-E01V2-S10", 9490306, url, term)
        self.assertTrue(s10_rejected_for_scene(ROOT, "VNC-E01V2-S10", 9490306))
        self.assertFalse(s10_rejected_for_scene(ROOT, "VNC-E01V2-S04", 9490306))

    def test_historical_exclusion_contract_unchanged(self):
        self.assertNotIn(9490306, EXCLUDED_PEXELS)
        result = verify(ROOT)
        self.assertEqual(result["scene_briefs"], 12)
        self.assertEqual(result["previously_rejected_pexels_ids_blocked"], 12)

    def test_physical_provenance_and_release_deny_all_present(self):
        ledger = json.loads((ROOT / S10_REJECTIONS).read_text(encoding="utf-8"))
        self.assertEqual(ledger["project_id"], "VERBO_NO_CHAO_EXCLUSIVO")
        self.assertEqual(ledger["scene_id"], "VNC-E01V2-S10")
        self.assertFalse(ledger["publication_authorized"])
        self.assertFalse(ledger["allowed_in_master"])
        self.assertFalse(ledger["commercial_rights_cleared"])
        self.assertEqual(len(ledger["decisions"]), 1)
        record = ledger["decisions"][0]
        self.assertTrue(record["full_source_decoded"])
        self.assertTrue(record["real_frame_review"])
        self.assertEqual(record["source_video_id"], 9490306)
        self.assertEqual(record["full_original_sha256"],
                         "cfecb6aa945c25258728a5155840ae03a1ca636866a4719137c29c8dec75c35e")
        self.assertEqual(len(record["sheets"]), 3)
        self.assertTrue(all(len(x["sha256"]) == 64 for x in record["sheets"]))
        self.assertFalse(record["allowed_for_s10_master"])

    def test_unrelated_new_s10_video_can_be_researched_but_not_approved(self):
        plan = json.loads((ROOT / POLICY).read_text(encoding="utf-8"))
        term = plan["scenes"][9]["locked_search_queries_en"][0]
        result = preflight_stock(
            "VNC-E01V2-S10", 99999983,
            "https://www.pexels.com/video/quiet-mutual-listening-99999983/",
            term,
        )
        self.assertEqual(result["status"], "ELIGIBLE_FOR_PHYSICAL_MEDIA_REVIEW_ONLY")
        self.assertFalse(result["editorially_approved"])
        self.assertFalse(result["publication_authorized"])


if __name__ == "__main__":
    unittest.main()
