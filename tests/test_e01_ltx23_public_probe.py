"""Pure gate tests: no generation, no HuggingFace network requests."""
import unittest
from agents.e01_ltx23_public_probe import BASE,stage_is_running

class TestE01Ltx23PublicProbe(unittest.TestCase):
    def test_only_running_provider_is_eligible(self):
        self.assertTrue(stage_is_running({"runtime":{"stage":"RUNNING"}}))
        self.assertTrue(stage_is_running({"runtime":{"stage":"running"}}))
        for obj in [{},{"runtime":{"stage":"PAUSED"}},
                    {"runtime":{"stage":"BUILDING"}},
                    {"runtime":{"stage":"RUNNING_ERROR"}},
                    {"runtime":{}},
                    {"runtime":None},[],None]:
            with self.subTest(payload=obj):
                self.assertFalse(stage_is_running(obj))
    def test_no_false_release_by_default(self):
        for key in ("third_party_rights_cleared",
                    "commercial_release_authorized",
                    "source_copyright_review_complete",
                    "native_master_resolution",
                    "matches_full_scene_duration",
                    "approved_for_master","publication_authorized",
                    "master_rendered"):
            self.assertIs(BASE[key],False,key)
    def test_cost_free_and_scope_limited(self):
        self.assertEqual(BASE["source"],"Lightricks/LTX-2-3")
        self.assertEqual(BASE["requested_seconds"],2.0)
        self.assertEqual(BASE["requested_resolution"],[576,1024])
        self.assertEqual(BASE["target_scene_seconds"],5.74)
        self.assertTrue(BASE["no_account_login"])
        self.assertTrue(BASE["no_credit_card_or_paid_plan"])
        self.assertNotEqual(BASE["generation_origin"],"CAMERA_CAPTURED")
if __name__=="__main__":
    unittest.main()
