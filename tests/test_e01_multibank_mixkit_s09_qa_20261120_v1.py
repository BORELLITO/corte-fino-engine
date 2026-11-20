"""Offline guards for VNC multi-bank scene curation and single 4K Mixkit S09."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agents import e01_mixkit_s09_physical_qa_20261120_v1 as qa


class E01MultibankS09Tests(unittest.TestCase):
    def setUp(self):
        self.plan=json.loads(qa.CONTRACT.read_text(encoding="utf-8"))

    def test_12_scene_coverage_and_canonical_originals_locked(self):
        candidate=qa.check_manifest(data=self.plan)
        self.assertEqual(candidate["video_id"],99890)
        self.assertEqual([x["scene_id"] for x in self.plan["scenes"]],
                         [f"VNC-E01V2-S{i:02d}" for i in range(1,13)])
        self.assertEqual(self.plan["root_baseline_commit"],
                         "db6e1d4acf23e82793f6230535a1716842ba5cd0")
        self.assertTrue(self.plan["scenes"][0]["owner_visual_approved"])
        self.assertEqual(sum(1 for s in self.plan["scenes"] if s["owner_visual_approved"]),1)
        self.assertEqual(self.plan["scenes"][8]["primary_candidate_id"],99890)
        self.assertEqual(self.plan["scenes"][11]["status"],"UNSOURCED_BOOKEND_MUST_RETURN_TO_S01")

    def test_only_exact_free_license_source_and_browser_provenance(self):
        c=qa.check_manifest(data=self.plan)
        self.assertEqual(c["page_license"],"Mixkit Stock Video Free License")
        self.assertEqual(c["page_url"],qa.SOURCE_PAGE)
        self.assertEqual(c["browser_probe"]["download_final_url"],qa.SOURCE_URL)
        self.assertFalse(c["individual_rights_cleared"])
        self.assertFalse(c["preview_physically_decoded"])
        self.assertFalse(c["visual_approved"])
        self.assertFalse(c["publication_authorized"])

    def test_rejects_tampered_project_rights_media_and_duration(self):
        for key,value in [
          ("project_id","CORTE-FINO"),("episode_id","VNC-W01-E2"),
          ("root_baseline_commit","0"*40),("narration_seconds",75.0),
          ("no_full_master",False),("no_publication",False),
          ("no_paid_sources",False),("no_auto_approval_after_technical_tests",False),
          ("no_replacement_of_original_s01",False),
        ]:
            data=copy.deepcopy(self.plan)
            data[key]=value
            with self.subTest(k=key),self.assertRaises(qa.IntakeError):
                qa.check_manifest(data=data)
        for key,value in [
          ("page_license","Restricted License"),("visual_approved",True),
          ("individual_rights_cleared",True),("publication_authorized",True),
          ("preview_physically_decoded",True),("page_url","http://evil.example/test"),
        ]:
            data=copy.deepcopy(self.plan)
            data["source_candidates"][8][key]=value
            with self.subTest(k=key),self.assertRaises(qa.IntakeError):
                qa.check_manifest(data=data)
        for key,value in [
          ("download_final_url","https://assets.mixkit.co/another.mp4"),
          ("observed_http_status",302),("observed_content_type","text/html"),
          ("listed_resolution",[1920,1080]),("listed_seconds",4),
          ("physical_file_sha256","0"*64)
        ]:
            data=copy.deepcopy(self.plan)
            data["source_candidates"][8]["browser_probe"][key]=value
            with self.subTest(k=key),self.assertRaises(qa.IntakeError):
                qa.check_manifest(data=data)

    def test_no_accidental_release_or_duplicate_clip_use(self):
        sources=self.plan["source_candidates"]
        self.assertEqual(len(sources),10)
        self.assertEqual(len({x["video_id"] for x in sources}),10)
        self.assertTrue(all(x["page_license"]=="Mixkit Stock Video Free License" for x in sources))
        self.assertTrue(all(not x["publication_authorized"] and not x["individual_rights_cleared"] for x in sources))
        self.assertTrue(all(not s["master_allowed"] and not s["publication_authorized"] for s in self.plan["scenes"]))
        self.assertTrue(self.plan["strict_quality_policy"]["no_still_photo_as_video"])

    def test_redirect_denied_even_if_http_302(self):
        handler=qa.NoRedirect()
        request=__import__("urllib.request",fromlist=["Request"]).Request(qa.SOURCE_URL)
        with self.assertRaises(qa.IntakeError):
            handler.redirect_request(request,None,302,"moved",{},"https://other.example/asset.mp4")

    def test_missing_remote_video_is_blocked_without_faked_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            with patch.object(qa,"download_original",side_effect=OSError("not reachable")):
                state=qa.run(p)
            self.assertEqual(state,2)
            d=json.loads((p/qa.REPORT).read_text(encoding="utf-8"))
            self.assertEqual(d["status"],"BLOCKED_NO_PHYSICAL_CANDIDATE_YET")
            self.assertFalse(d["rights_cleared"])
            self.assertFalse(d["master_allowed"])
            self.assertFalse((p/qa.PREVIEW).exists())


if __name__=="__main__":
    unittest.main()
