"""Fail-closed dual Mixkit S03/S10 source, narrative and release tests."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from agents import e01_mixkit_s03_s10_two_source_qa_20261120_v1 as qa

class S03S10DualIntakeTest(unittest.TestCase):
 def setUp(self): self.plan=json.loads((qa.ROOT/qa.CONTRACT).read_text(encoding="utf8"))
 def test_exact_scopes_license_and_independent_sources(self):
  self.assertTrue(qa.verify())
  self.assertEqual(set(qa.SOURCES),{"S03","S10"})
  self.assertEqual([qa.SOURCES[s]["id"] for s in ("S03","S10")],[4331,8748])
  self.assertEqual(qa.SOURCES["S03"]["frames"],184)
  self.assertEqual(qa.SOURCES["S10"]["frames"],198)
  self.assertTrue(all(item["page"].startswith("https://mixkit.co/free-stock-video/") and
            item["url"].startswith("https://assets.mixkit.co/videos/") for item in qa.SOURCES.values()))
 def test_manifest_mutation_rejected_without_download(self):
  for key,value in (("project_id","OTHER"),("no_full_master",False),("no_publication",False),("no_paid_sources",False)):
   with self.subTest(key=key),tempfile.TemporaryDirectory() as t:
    d=copy.deepcopy(self.plan);d[key]=value
    root=Path(t);(root/"contracts").mkdir()
    (root/qa.CONTRACT).write_text(json.dumps(d),encoding="utf8")
    with self.assertRaises(qa.IntakeError):qa.verify(root)
  for id in (4331,8748):
   with self.subTest(id=id),tempfile.TemporaryDirectory() as t:
    d=copy.deepcopy(self.plan)
    row=next(r for r in d["source_candidates"] if r["video_id"]==id)
    row["page_license"]="Mixkit Restricted License"
    root=Path(t);(root/"contracts").mkdir()
    (root/qa.CONTRACT).write_text(json.dumps(d),encoding="utf8")
    with self.assertRaises(qa.IntakeError):qa.verify(root)
 def test_wrong_scene_approval_must_fail(self):
  for scene in ("S03","S10"):
   with self.subTest(scene=scene),tempfile.TemporaryDirectory() as t:
    d=copy.deepcopy(self.plan);d["scenes"][int(scene[1:])-1]["owner_visual_approved"]=True
    root=Path(t);(root/"contracts").mkdir()
    (root/qa.CONTRACT).write_text(json.dumps(d),encoding="utf8")
    with self.assertRaises(qa.IntakeError):qa.verify(root)
 def test_network_failure_does_not_create_master_or_fake_video(self):
  with tempfile.TemporaryDirectory() as t,patch.object(qa,"download",side_effect=OSError("unavailable")):
   out=Path(t);code=qa.run(out)
   self.assertEqual(code,2)
   report=json.loads((out/"S03_S10_MIXKIT_QA_REPORT.json").read_text(encoding="utf8"))
   self.assertEqual(report["status"],"PARTIAL_OR_ALL_BLOCKED_PHYSICAL")
   self.assertFalse(report["publication_authorized"])
   self.assertFalse(report["master_allowed"])
   self.assertFalse(list(out.glob("*MOTION*.mp4")))
 def test_video_proofs_not_release(self):
  self.assertLessEqual(qa.LIMIT_BYTES,155_000_000)
  self.assertEqual((qa.W,qa.H,qa.FPS),(540,960,30))
  self.assertNotEqual(qa.SOURCES["S03"]["id"],qa.SOURCES["S10"]["id"])

if __name__=="__main__":unittest.main()
