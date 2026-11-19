import json
import unittest
from pathlib import Path
M=Path(__file__).resolve().parents[1]/"contracts/e01_s01_google_flow_free_preflight_v1.json"
class TestGoogleFlowS01(unittest.TestCase):
 def setUp(self): self.m=json.loads(M.read_text(encoding="utf-8"))
 def test_project_baseline(self):
  self.assertEqual(self.m["project_id"],"VERBO_NO_CHAO_EXCLUSIVO")
  self.assertEqual(self.m["episode_id"],"VNC-W01-E1")
  self.assertEqual(self.m["scene_id"],"VNC-E01V2-S01")
  self.assertEqual(self.m["canonical_scene_duration_seconds"],5.74)
 def test_free_provider_documented_params(self):
  self.assertEqual((self.m["provider"],self.m["model"]),("Google Flow","Veo 3.1 Lite"))
  self.assertEqual(self.m["proposed_video_seconds"],6)
  self.assertEqual(self.m["aspect_ratio"],"9:16")
  self.assertEqual(self.m["requested_outputs"],1)
  self.assertEqual(self.m["public_documented_6s_credit_cost"],10)
 def test_no_unapproved_budget_or_remote_upload(self):
  self.assertFalse(self.m["credit_spending_authorized"])
  self.assertFalse(self.m["external_image_upload_authorized"])
  self.assertFalse(self.m["account_credit_balance_verified"])
  self.assertFalse(self.m["generator_job_submitted"])
  self.assertTrue(self.m["no_automatic_retry"])
 def test_unverified_cinematic_output_cannot_be_released(self):
  for k in ("source_image_editorially_approved","actual_mp4_exists","video_motion_qa_passed","rights_verified","scene_approved","master_created","publication_authorized"):
   self.assertFalse(self.m[k],k)
 def test_source_private_and_no_legacy_stock_reconsideration(self):
  self.assertEqual(self.m["source_image_location"],"PRIVATE_LIBRARY_NOT_GITHUB")
  self.assertEqual(len(self.m["source_image_sha256"]),64)
  self.assertIn("PEXELS_8860242_PREVIOUSLY_REJECTED",self.m["source_constraints"])
 def test_higgsfield_fallback_is_quote_only_and_never_release(self):
  alt=self.m["fallback_higgsfield_quote"]
  self.assertEqual((alt["provider"],alt["model"]),("Higgsfield","seedance_2_0_mini"))
  self.assertEqual((alt["duration_seconds"],alt["aspect_ratio"],alt["resolution"],alt["requested_outputs"]),(6,"9:16","720p",1))
  self.assertEqual(alt["quoted_credits"],6)
  for key in ("quote_is_not_generation","account_balance_not_persisted_publicly","free_tier_visible_watermark_possible"):
   self.assertIs(alt[key],True,key)
  for key in ("source_first_frame_uploaded","credit_spending_authorized","generator_job_submitted","allowed_in_master","publication_authorized"):
   self.assertIs(alt[key],False,key)
  self.assertIs(self.m["provider_route_comparison"]["no_generation_without_user_specific_credit_permission"],True)
  self.assertEqual(alt["free_tier_model_access_at_submission"],"NOT_VERIFIED")
if __name__=="__main__": unittest.main()
