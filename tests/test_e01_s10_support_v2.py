import unittest
from agents.e01_s10_support_v2 import SOURCE,BASE

class TestSupportS10V2(unittest.TestCase):
 def test_scene_identity_and_same_account_free_path(self):
  self.assertEqual(SOURCE["scene_id"],"VNC-E01V2-S10")
  self.assertEqual(SOURCE["video_id"],6381001)
  self.assertGreater(SOURCE["seconds"],SOURCE["minimum"])
  self.assertEqual(BASE["license_url"],"https://www.pexels.com/license/")
  self.assertTrue(BASE["no_api_key"] and BASE["zero_payment"])
 def test_no_false_release(self):
  for field in ("source_has_same_recurring_protagonist",
    "private_model_release_verified","right_to_imply_subject_endorses_religion",
    "editorial_acceptance","master_approved","publication_authorized"):
   self.assertIs(BASE[field],False,field)
if __name__=="__main__":
 unittest.main()
