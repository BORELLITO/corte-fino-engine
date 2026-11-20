"""Never silently upgrade a free Agnes Flash run to a paid service."""
import unittest
from unittest.mock import patch
from agents.e01_agnes_flash_free_only import MODEL,payload,validate
from agents.e01_stock_candidates import StockIntakeError

class TestAgnesFreeOnly(unittest.TestCase):
 def test_real_storyboard_request_shape_720p_six_seconds(self):
  p=payload()
  self.assertEqual(p["model"],"agnes-video-2.5-flash")
  self.assertEqual(p["seconds"],"6")
  self.assertEqual(p["aspect_ratio"],"9:16")
  self.assertEqual(p["size"],"720P")
  self.assertEqual(p["mode"],"text")
  self.assertEqual(p["n"],1)
  self.assertNotIn("videos",p)
  self.assertIn("closed dark notebook",p["prompt"])
 def test_always_dry_run_even_with_key(self):
  with patch.dict("os.environ",{"AGNES_API_KEY":"test-secret"},clear=False):
   info=validate()
   self.assertTrue(info["secret_configured_from_environment"])
   self.assertTrue(info["request_not_sent"])
   self.assertTrue(info["provider_access_unverified"])
   self.assertTrue(info["commercial_use_rights_not_cleared"])
   self.assertFalse(info["publication_authorized"])
  with patch.dict("os.environ",{"AGNES_API_KEY":""},clear=False):
   info=validate()
   self.assertFalse(info["secret_configured_from_environment"])
 def test_payload_never_chooses_paid_models_or_wrong_size(self):
  p=payload()
  self.assertNotEqual(p["model"],"agnes-video-2.5")
  self.assertNotEqual(p["size"],"1080P")
if __name__=="__main__":
 unittest.main()
