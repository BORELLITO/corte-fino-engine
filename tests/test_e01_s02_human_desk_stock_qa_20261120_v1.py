"""Offline adversarial guardrail tests — S02 human/desk Pexels visual research."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agents import e01_s02_human_desk_stock_qa_20261120_v1 as qa


class E01S02HumanDeskResearchTests(unittest.TestCase):
    def setUp(self):
        self.root=qa.ROOT
        self.plan=json.loads((self.root/qa.CONTRACT).read_text(encoding="utf8"))

    def test_storyboard_and_prior_s01_approval_scoped(self):
        p=qa.validate_contract()
        self.assertEqual(p["id"],9903488)
        self.assertEqual(p["creator"],"Ron Lach")
        self.assertEqual((p["listing_width"],p["listing_height"]),(2160,4096))
        self.assertEqual(qa.FRAMES,147)
        self.assertEqual(qa.SAMPLES,(.5,2.4,4.5))
        self.assertFalse(p["artistic_approval"])
        self.assertFalse(self.plan["approval_scope"]["s02_visual_approved"])
        self.assertFalse(self.plan["approval_scope"]["publication_authorized"])

    def test_rejects_approval_rights_id_or_source_drift(self):
        forbidden=[
           ("project_id","CORTE_FINO"),("scene_id","VNC-E01V2-S01"),
           ("purpose","PROMOTE_TO_MASTER"),("source_limit_bytes",500000000),
           ("locked_story_sha256","0"*64),
           ("initial_state","EDITORIAL_APPROVED"),
        ]
        for key,val in forbidden:
            bad=copy.deepcopy(self.plan)
            bad[key]=val
            with self.subTest(key=key),self.assertRaises(qa.S02HandDeskError):
                qa.validate_contract(data=bad)
        for key,val in [
          ("id",7034348),("page_url","https://unknown.example/movie.mp4"),
          ("creator","Another Person"),("listing_width",1080),
          ("listing_height",1024),("listing_fps",60),
          ("media_physically_downloaded",True),("artistic_approval",True),
          ("rights_cleared",True),("real_camera_origin_independently_proven",True),
          ("subject_same_as_s01_proven",True),
        ]:
            bad=copy.deepcopy(self.plan)
            bad["candidate"][key]=val
            with self.subTest(key=key),self.assertRaises(qa.S02HandDeskError):
                qa.validate_contract(data=bad)

    def test_invariants_for_watermark_frames_and_no_audio(self):
        invalid=[
           ("width",1080),("height",1920),("fps",25),("frames",125),
           ("cut_start_seconds",5),("samples_seconds",[0,1,2]),
           ("watermark",""),("audio",True),("captions",True),
           ("full_preview_decode_required",False),
           ("compare_against_s01_approved_sha256","0"*64),
        ]
        for key,val in invalid:
            bad=copy.deepcopy(self.plan)
            bad["output"][key]=val
            with self.subTest(key=key),self.assertRaises(qa.S02HandDeskError):
                qa.validate_contract(data=bad)

    def test_no_automatic_s02_promotion_or_s01_replacement(self):
        for key,val in [
            ("s01_visual_approved",False),("s02_visual_approved",True),
            ("dont_replace_existing_s02_candidate",False),
            ("rights_cleared",True),("master_allowed",True),
            ("publication_authorized",True),
            ("new_spending_authorized",True),("merge_authorized",True),
        ]:
            bad=copy.deepcopy(self.plan)
            bad["approval_scope"][key]=val
            with self.subTest(key=key),self.assertRaises(qa.S02HandDeskError):
                qa.validate_contract(data=bad)
        bad=copy.deepcopy(self.plan)
        bad["historical_candidate_to_preserve"]["source_id"]=9903488
        with self.assertRaises(qa.S02HandDeskError):
            qa.validate_contract(data=bad)

    def test_failed_download_does_not_create_fake_mp4(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)
            with patch.object(qa,"download_source",side_effect=OSError("provider offline")):
                status=qa.produce(out)
            self.assertEqual(status,2)
            state=json.loads((out/qa.REPORT_NAME).read_text(encoding="utf8"))
            self.assertEqual(state["status"],"BLOCKED_SOURCE_OR_PHYSICAL_QA")
            self.assertFalse(state["rights_cleared"] if "rights_cleared" in state else state["media_license_individually_verified"])
            self.assertFalse(state["master_allowed"])
            self.assertFalse(state["publication_authorized"])
            self.assertFalse((out/qa.PREVIEW_NAME).exists())

    def test_canonical_story_rejects_disguised_static_image_intent(self):
        original=json.loads((self.root/qa.STORY).read_text(encoding="utf8"))
        self.assertIn("same anonymous adult hand",original["scenes"][1]["visual_prompt"])
        self.assertIn("no numbers emphasized",original["scenes"][1]["visual_prompt"])
        self.assertIn("subtle side dolly",original["scenes"][1]["camera_motion"])
        self.assertNotEqual(self.plan["historical_candidate_to_preserve"]["source_id"],
                            self.plan["candidate"]["id"])
        self.assertEqual(self.plan["initial_state"],
                         "SOURCE_PAGE_VERIFIED_MP4_NOT_DOWNLOADED")


if __name__=="__main__":
    unittest.main()
