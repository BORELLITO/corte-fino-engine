"""S04 second candidate is measured, never promoted from stock metadata."""
import unittest
import inspect
from agents import e01_s04_pexels_11137423_physical_qa as q

class TestCandidate2(unittest.TestCase):
    def test_canonical_scene_and_distinct_public_id(self):
        self.assertEqual(q.SCENE,"VNC-E01V2-S04")
        self.assertEqual(q.VIDEO_ID,11137423)
        self.assertAlmostEqual(q.SECONDS,5.82)
        self.assertIn("/11137423/",q.DOWNLOAD)
    def test_at_least_two_real_time_windows(self):
        self.assertGreater(20,2*q.SECONDS)
    def test_source_not_master_or_licensed(self):
        source=inspect.getsource(q.inspect)
        for gate in ['"rights_cleared":False','"editorial_approved":False',
                     '"allowed_in_master":False','"publication_authorized":False']:
            self.assertIn(gate,source)
        self.assertNotIn("client.submit(",source)
    def test_center_crop_requires_true_native_resolution(self):
        source=inspect.getsource(q.inspect)
        self.assertIn('crop_w < 1080',source)
        self.assertIn('"sufficient_native_resolution":True',source)

if __name__=="__main__":
    unittest.main()
