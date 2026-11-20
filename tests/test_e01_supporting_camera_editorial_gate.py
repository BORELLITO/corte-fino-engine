"""Fail-closed S10/S05 camera footage editorial decisions and original hashes."""
from __future__ import annotations
import copy,json,unittest
from pathlib import Path
from agents.e01_stock_candidates import ROOT,StockIntakeError

FILE=Path("contracts/e01_v2_supporting_camera_editorial_qa_v1.json")
SHA_V2="7d094a12d8fb3a9bcfcdc9e98895f97191b392258a7cfd94f219b49b7a3a0e9a"
SHA_GRADED="996cacfe98ed8169ef0931f45ea336ee520441c7b5b545c07178857d2fea5a35"

def validate(report):
 if report.get("schema_version")!="1.0.0" or report.get("episode_id")!="VNC-W01-E1":
  raise ValueError("identity_changed")
 if report.get("source_license")!="https://www.pexels.com/license/":
  raise ValueError("license_link_changed")
 prior=report.get("prior_sources")
 if not isinstance(prior,list) or len(prior)!=2:
  raise ValueError("source_count_changed")
 if [(x.get("scene_id"),x.get("video_id"),x.get("decision")) for x in prior]!=[
    ("VNC-E01V2-S10",4828603,"REJECTED_NARRATIVE"),
    ("VNC-E01V2-S05",37340388,"REJECTED_HISTORICAL_CONTEXT")]:
  raise ValueError("prior_rejections_changed")
 for x in prior:
  if x.get("technical_decode") is not True or x.get("actual_preview_duration")!=8:
   raise ValueError("invalid_physical_qa")
  if len(x.get("source_sha256",""))!=64 or len(x.get("preview_sha256",""))!=64:
   raise ValueError("hash_deleted")
 s=report.get("s10_candidate") or {}
 if (s.get("video_id")!=6381001 or
     s.get("scene_id")!="VNC-E01V2-S10" or
     s.get("preview_sha256")!=SHA_V2 or
     s.get("second_graded_preview_sha256")!=SHA_GRADED or
     s.get("preview_duration_seconds")!=8 or
     s.get("source_original_dimensions")!=[1440,2560] or
     s.get("condition")!="CONDITIONAL_SYMBOLIC_SUPPORT_ONLY" or
     s.get("hands_on_table") is not False or
     s.get("accepted_for_locked_storyboard") is not False or
     s.get("license_rights_reviewed_for_specific_usage") is not False or
     s.get("graded_local_preview_only") is not True or
     s.get("graded_backup_in_drive") is not False):
  raise ValueError("s10_false_editorial_promotion")
 for flag in ("source_licence_legal_review_complete",
              "participant_endorsement_authorized","full_editorial_review_completed",
              "rights_cleared","final_master_produced","publication_authorized"):
  if report.get(flag) is not False:raise ValueError("false_master_or_rights_claim")
 return True

class TestCameraSupportingEditorial(unittest.TestCase):
 def setUp(self):
  self.r=json.loads((ROOT/FILE).read_text(encoding="utf-8"))
 def test_immutable_review(self):
  self.assertTrue(validate(self.r))
 def test_prevent_false_release(self):
  for flag in ("rights_cleared","publication_authorized","full_editorial_review_completed"):
   d=copy.deepcopy(self.r);d[flag]=True
   with self.subTest(flag=flag),self.assertRaises(ValueError):validate(d)
  for key,val in (("accepted_for_locked_storyboard",True),
                  ("preview_sha256","bad"),("graded_backup_in_drive",True),
                  ("condition","APPROVED"),("hands_on_table",True)):
   d=copy.deepcopy(self.r);d["s10_candidate"][key]=val
   with self.subTest(key=key),self.assertRaises(ValueError):validate(d)
 def test_protect_prior_rejected_assets(self):
  d=copy.deepcopy(self.r);d["prior_sources"][0]["decision"]="APPROVED"
  with self.assertRaises(ValueError):validate(d)

if __name__=="__main__":
 unittest.main()
