import unittest
from agents.e01_two_real_stock_support import SOURCES,BASE,media_host

class TestTwoSupportStock(unittest.TestCase):
 def test_sources_are_specific_and_mapped(self):
  self.assertEqual([(x["scene_id"],x["video_id"]) for x in SOURCES],
   [("VNC-E01V2-S10",4828603),("VNC-E01V2-S05",37340388)])
  self.assertTrue(all(x["seconds"]>x["minimum"] for x in SOURCES))
 def test_allowlist(self):
  self.assertTrue(media_host("https://videos.pexels.com/video-files/1234/a.mp4"))
  for x in ["http://videos.pexels.com/video-files/1234/a.mp4",
   "https://videos.pexels.com.attacker.net/video-files/1234/a.mp4",
   "https://www.pexels.com/download/video/1234/",
   "file:///tmp/foo.mp4","https://videos.pexels.com/video-files/abc/a.mov"]:
   with self.subTest(url=x): self.assertFalse(media_host(x))
 def test_no_false_release_flags(self):
  for k in ("visual_story_approved","individual_rights_cleared",
    "historical_accuracy_cleared","master_created","publication_authorized"):
   self.assertIs(BASE[k],False)
  self.assertTrue(BASE["login_required"] is False and BASE["api_key_required"] is False)
if __name__=="__main__":
 unittest.main()
