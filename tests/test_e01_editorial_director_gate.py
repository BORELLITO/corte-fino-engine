"""Adversarial checks: reject footage despite passing codec and rights metadata."""
from __future__ import annotations
import copy,json,unittest
from agents.e01_editorial_director_gate import ROOT,FILE,PINNED,validate
from agents.e01_stock_candidates import StockIntakeError

class TestE01DirectorEditorialGate(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.original=json.loads((ROOT/FILE).read_text(encoding="utf-8"))
 def fail(self,mutate):
  data=copy.deepcopy(self.original)
  mutate(data)
  with self.assertRaises((StockIntakeError,ValueError,KeyError,TypeError)):
   validate(ROOT,data)
 def test_real_director_rejected_seven_sources_and_no_publication(self):
  result=validate(ROOT)
  self.assertEqual(result["reviewed_sources"],7)
  self.assertEqual(result["rejected_for_canonical_e01"],7)
  self.assertEqual(result["e01_clips_approved_for_cut"],0)
  self.assertFalse(result["publication_authorized"])
 def test_prior_conditional_is_not_approval(self):
  for item in self.original["decisions"]:
   if item["asset_id"]=="E01-S10-PEXELS-6381001":
    self.assertTrue(item["prior_conditional_superseded"])
    self.assertEqual(item["verdict"],"REJECTED_FOR_E01_CANONICAL_SHOT")
  self.fail(lambda d:d["decisions"][-1].update(verdict="APPROVED"))
  self.fail(lambda d:d["decisions"][-1].update(can_enter_e01_edit=True))
  self.fail(lambda d:d["decisions"][-1].update(prior_conditional_superseded=False))
 def test_historic_conditional_s05_and_s08_explicitly_rejected(self):
  d={x["asset_id"]:x for x in self.original["decisions"]}
  self.assertEqual(len(d),7)
  for asset in ("E01-S05-PEXELS-6010698","E01-S08-PEXELS-6860448"):
   with self.subTest(asset=asset):
    self.assertTrue(d[asset]["prior_conditional_superseded"])
    self.assertFalse(d[asset]["can_enter_e01_edit"])
    self.assertEqual(d[asset]["verdict"],"REJECTED_FOR_E01_CANONICAL_SHOT")
  self.fail(lambda m:m["decisions"][4].update(can_enter_e01_edit=True))
  self.fail(lambda m:m["decisions"][5].update(prior_conditional_superseded=False))
  self.fail(lambda m:m.update(predecessor_second_stock_review=""))
 def test_no_rights_or_master_promotion(self):
  for key in ("ready_for_full_12_scene_master","soundtrack_license_cleared",
      "voice_runtime_license_cleared","commercial_publication_authorized",
      "production_cost_authorized","publishing_action_authorized"):
   with self.subTest(key=key):
    self.fail(lambda d:d.update({key:True}))
  self.fail(lambda d:d.update(approved_for_e01_shots=["E01-S10-PEXELS-6381001"]))
 def test_pin_original_physical_provenance(self):
  self.fail(lambda d:d["decisions"][0].update(source_sha256="f"*64))
  self.fail(lambda d:d["decisions"][2].update(scene_id="VNC-E01V2-S04"))
  self.fail(lambda d:d["decisions"][3].update(source_type="AI_GENERATED_FICTIONAL_VIDEO"))
  self.fail(lambda d:d["decisions"][4].update(physical_source_verified=False))
  self.fail(lambda d:d["decisions"].pop())
  self.fail(lambda d:d["decisions"].append(copy.deepcopy(d["decisions"][0])))
 def test_decision_requires_actual_visual_review_not_only_metadata(self):
  self.fail(lambda d:d["decisions"][3].update(reviewed_frame_samples=False))
  self.fail(lambda d:d["decisions"][4].update(exact_video_reviewed_end_to_end=True))
  self.fail(lambda d:d["decisions"][4].update(editorial_scores_0_5={
        "story":5,"continuity":5,"visual":5,"authenticity":5}))
  self.fail(lambda d:d["decisions"][4].update(rationale="ok"))
  self.fail(lambda d:d["decisions"][4].update(evidence_run_url="https://phishing.test/clip"))
 def test_avoid_accidental_reapproval_by_prior_report(self):
  self.fail(lambda d:d["policy"].update(conditional_or_technically_passed_is_not_approval=False))
  self.fail(lambda d:d.update(min_world_continuity_0_5=2))
  self.fail(lambda d:d["decisions"][4].update(approved_for_master=True))
if __name__=="__main__":
 unittest.main()
