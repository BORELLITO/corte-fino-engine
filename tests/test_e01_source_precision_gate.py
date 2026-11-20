"""Adversarial precision: wrong, old, unapproved, stock actor cannot enter E01."""
import copy
import json
import unittest
from agents.e01_source_precision_gate import (
    ROOT,POLICY,EXCLUDED_PEXELS,EXCLUDED_SHA,verify,preflight_stock,rejected_sha
)
from agents.e01_stock_candidates import StockIntakeError

class TestE01SourcePrecisionGate(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.plan=json.loads((ROOT/POLICY).read_text(encoding="utf-8"))
 def fails(self,fn):
  with self.assertRaises(StockIntakeError):fn()
 def mutation(self,fn):
  data=copy.deepcopy(self.plan)
  fn(data)
  self.fails(lambda:verify(ROOT,data))
 def test_all_twelve_queries_match_storyboard_and_rejection_archive(self):
  output=verify(ROOT)
  self.assertEqual(output["scene_briefs"],12)
  self.assertEqual(output["previously_rejected_pexels_ids_blocked"],12)
  self.assertEqual(output["previously_rejected_media_hashes_blocked"],13)
  self.assertFalse(output["publication_authorized"])
 def test_prior_rejected_pages_cannot_reenter_any_scene(self):
  q=self.plan["scenes"][9]["locked_search_queries_en"][0]
  for video_id in EXCLUDED_PEXELS:
   with self.subTest(video_id=video_id):
    page="https://www.pexels.com/video/another-candidate-%d/"%video_id
    self.fails(lambda:preflight_stock("VNC-E01V2-S10",video_id,page,q))
 def test_known_bad_media_hashes_blocked(self):
  for hash_ in EXCLUDED_SHA:
   self.assertTrue(rejected_sha(hash_))
  self.assertFalse(rejected_sha("b"*64))
 def test_cross_scene_or_unverified_page_cannot_scout(self):
  q=self.plan["scenes"][9]["locked_search_queries_en"][0]
  url="https://www.pexels.com/video/example-shot-99999999/"
  self.fails(lambda:preflight_stock("VNC-E01V2-S01",99999999,url,q))
  self.fails(lambda:preflight_stock("VNC-E01V2-S10",99999999,url,"nice stock video"))
  self.fails(lambda:preflight_stock("VNC-E01V2-S10",99999999,
                                    "https://pexels.com/video/example-shot-99999999/",q))
  self.fails(lambda:preflight_stock("VNC-E01V2-S10",99999999,
                                    "https://www.pexels.com/video/example-shot-99999998/",q))
  self.fails(lambda:preflight_stock("VNC-E01V2-S10",99999999,
                                    url+"?source=ads",q))
  self.fails(lambda:preflight_stock("VNC-E01V2-S10",True,url,q))
  self.fails(lambda:preflight_stock("VNC-E01V2-S99",99999999,url,q))
 def test_a_new_candidate_is_only_allowed_to_be_inspected(self):
  q=self.plan["scenes"][9]["locked_search_queries_en"][0]
  url="https://www.pexels.com/video/example-shot-99999999/"
  result=preflight_stock("VNC-E01V2-S10",99999999,url,q)
  self.assertEqual(result["status"],"ELIGIBLE_FOR_PHYSICAL_MEDIA_REVIEW_ONLY")
  self.assertFalse(result["source_page_verified_live"])
  self.assertFalse(result["actual_video_frames_reviewed"])
  self.assertFalse(result["editorially_approved"])
  self.assertFalse(result["publication_authorized"])
 def test_mutation_rejects_story_or_rejection_rewrite(self):
  self.mutation(lambda d:d["scenes"][0].update(continuity_group="COMMUNITY_D"))
  self.mutation(lambda d:d["scenes"][1].update(
       allowed_acquisition_lane="LICENSED_STOCK_EDITORIAL"))
  self.mutation(lambda d:d["scenes"][9].update(
       locked_search_queries_en=["coffee friends video"]))
  self.mutation(lambda d:d["scenes"][0].update(source_video_id=99999))
  self.mutation(lambda d:d["scenes"][0].update(editorial_approved=True))
  self.mutation(lambda d:d["scenes"][1].update(requires_approved_s01_actor_anchor=False))
  self.mutation(lambda d:d.update(excluded_pexels_video_ids=[]))
  self.mutation(lambda d:d.update(auto_web_source_acquisition=True))
  self.mutation(lambda d:d.update(publication_authorized=True))
  self.mutation(lambda d:d.update(selected_candidates=[{"video_id":99999}]))
if __name__=="__main__":
 unittest.main()
