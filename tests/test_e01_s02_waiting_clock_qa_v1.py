"""S02 clock QA remains strictly no-master and does not inherit S01 approval."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agents import e01_s02_waiting_clock_qa_v1 as m


class S02ClockQA(unittest.TestCase):
    def setUp(self):
        self.contract=json.loads((m.ROOT/m.CONTRACT).read_text(encoding="utf8"))

    def test_s01_user_approval_scoped_and_s02_pending(self):
        src=m.validate()
        self.assertEqual(src["video_id"],7034348)
        self.assertEqual(m.FRAMES,147)
        self.assertEqual(m.FPS,30)
        self.assertEqual(m.SAMPLES,(0.5,2.4,4.5))
        p=self.contract["previous_scene"]
        self.assertEqual(p["approved_preview_sha256"],m.ACCEPTED_S01_SHA)
        self.assertFalse(self.contract["editorial_approved"])
        self.assertFalse(self.contract["owner_approved_for_s02"])
        self.assertFalse(self.contract["master_allowed"])
        self.assertFalse(self.contract["publication_authorized"])

    def test_frame_boundaries_match_original_audio_timeline(self):
        t=self.contract["cut_frame_plan_30fps"]
        self.assertEqual(t["s01_last_exclusive"],172)
        self.assertEqual(t["s02_last_exclusive"],319)
        self.assertEqual(t["s02_frames"],147)
        self.assertEqual(147/30,4.9)
        self.assertAlmostEqual(172/30,5.733333333333333)
        self.assertLess(abs(172/30-5.74),1/60)
        self.assertLess(abs(319/30-10.62),1/60)

    def test_release_and_project_forgery_are_rejected(self):
        for key,val in [
          ("project_id","CORTE_FINO"),("episode_id","VNC-W01-E2"),
          ("scene_id","VNC-E01V2-S01"),("editorial_approved",True),
          ("owner_approved_for_s02",True),("rights_cleared",True),
          ("s01_reference_modified",True),("master_allowed",True),
          ("publication_authorized",True),("spending_authorized",True),
          ("source_original_persisted",True),
        ]:
            data=copy.deepcopy(self.contract)
            data[key]=val
            with self.subTest(key=key),self.assertRaises(m.S02StockGateError):
                m.validate(data=data)

    def test_source_redirect_identity_and_license_forgery_rejected(self):
        for key,val in [
            ("video_id",4458845),("video_id",True),("page_url","https://evil.invalid/video"),
            ("license_label","Unlimited"),("source_sha256","f"*64),
            ("physical_source_acquired",True),
            ("third_party_rights_clearance",True),
            ("scene_specific_release_cleared",True)
        ]:
            data=copy.deepcopy(self.contract)
            data["source"][key]=val
            with self.subTest(key=key),self.assertRaises(m.S02StockGateError):
                m.validate(data=data)

    def test_s02_false_audio_captions_and_frames_rejected(self):
        for key,val in [
            ("frames",173),("fps",60),("audio",True),
            ("captions",True),("watermark",""),("width",1080)
        ]:
            data=copy.deepcopy(self.contract)
            data["output_preview"][key]=val
            with self.subTest(key=key),self.assertRaises(m.S02StockGateError):
                m.validate(data=data)
        data=copy.deepcopy(self.contract)
        data["cut_frame_plan_30fps"]["s02_frames"]=146
        with self.assertRaises(m.S02StockGateError):
            m.validate(data=data)

    def test_s01_approval_cannot_transfer_to_s02(self):
        for key,val in [
            ("approved_preview_sha256","f"*64),
            ("s01_visual_approved",False)
        ]:
            data=copy.deepcopy(self.contract)
            data["previous_scene"][key]=val
            with self.assertRaises(m.S02StockGateError):
                m.validate(data=data)

    def test_no_source_is_fail_closed_and_does_not_fabricate_media(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td)
            with patch.object(m,"download_source",side_effect=ValueError("no-source")):
                status=m.run(d)
            self.assertEqual(status,2)
            report=json.loads((d/"S02_CLOCK_PHYSICAL_QA_REPORT.json").read_text())
            self.assertEqual(report["status"],"BLOCKED_NO_S02_PREVIEW")
            self.assertFalse(report["s02_visual_approved"])
            self.assertFalse(report["master_allowed"])
            self.assertFalse(report["publication_authorized"])
            self.assertFalse((d/"S02_WAITING_CLOCK_QA_NOT_MASTER.mp4").exists())


if __name__=="__main__":
    unittest.main()
