"""Editorial QA: real stock bytes are not automatic E01 footage."""
import json
import unittest
from pathlib import Path
from agents.e01_stock_candidates import ROOT

REPORT=Path("contracts/e01_v2_pexels_real_camera_fallback_qa_v1.json")
EXPECTED={
 "left":"63bdd2bf5683a190d3febb3a9f4dff1a1623db2c4966ba6dd328318a9a06fec9",
 "center":"7c2a17113defbc58ff739f098d659bcd6eca3ad56996aa6afa34d2810cd71a2c",
 "right":"0bf3ed1d18a0f2c0d51394f4469a2535f309e75196e8ef41f7ffd7cef6b68821"
}
def gate(r):
 if not isinstance(r,dict) or r.get("schema_version")!="1.0.0":
  raise ValueError("bad schema")
 if r.get("classification")!="TECHNICAL_DOWNLOAD_AND_DECODE_SUCCEEDED_EDITORIAL_REJECTED":
  raise ValueError("editorial override")
 if r.get("scene_id")!="VNC-E01V2-S01" or r.get("source",{}).get("original_sha256")!="60073bc4a45f816ca4a4e6cce3b7039299ca6ff8824f222aa98ef923dde267e5":
  raise ValueError("source drift")
 if r.get("source",{}).get("license_url")!="https://www.pexels.com/license/":
  raise ValueError("license provenance absent")
 for field in ("title_provenance_cleared","individual_rights_cleared",
               "source_can_be_implied_to_endorse_faith",
               "accepted_as_character_continuity","accepted_for_e01_s01",
               "master_1080x1920_30fps","publication_authorized"):
  if r.get(field) is not False:raise ValueError("false release flag: "+field)
 items=r.get("candidate_previews")
 if not isinstance(items,list) or len(items)!=3:raise ValueError("preview count")
 if set(x.get("name") for x in items)!=set(EXPECTED):raise ValueError("missing crop")
 for x in items:
  if (x.get("sha256")!=EXPECTED[x["name"]] or x.get("duration_seconds")!=6.12
   or x.get("fps")!="25/1" or x.get("width")!=720 or x.get("height")!=1280
   or not isinstance(x.get("editorial_violation"),list)
   or "CLOSED_NOTEBOOK_NOT_PRESENT" not in x["editorial_violation"]):
   raise ValueError("invalid physical scene preview")
 return True

class TestPexelsEditorialGate(unittest.TestCase):
 def setUp(self):
  self.report=json.loads((ROOT/REPORT).read_text(encoding="utf-8"))
 def test_report_is_properly_rejected_and_immutable(self):
  self.assertTrue(gate(self.report))
  self.assertEqual(self.report["proof"]["github_run"],44296778066)
 def test_cannot_promote_any_crop_to_master(self):
  import copy
  for flag in ("accepted_for_e01_s01","publication_authorized",
               "individual_rights_cleared","master_1080x1920_30fps"):
   x=copy.deepcopy(self.report)
   x[flag]=True
   with self.subTest(flag=flag),self.assertRaises(ValueError):gate(x)
 def test_cannot_omit_metadata_or_relabel_actor(self):
  import copy
  for key in ("sha256","duration_seconds","fps"):
   x=copy.deepcopy(self.report)
   x["candidate_previews"][0][key]=0
   with self.subTest(key=key),self.assertRaises(ValueError):gate(x)
  x=copy.deepcopy(self.report)
  x["candidate_previews"].pop()
  with self.assertRaises(ValueError):gate(x)
if __name__=="__main__":
 unittest.main()
