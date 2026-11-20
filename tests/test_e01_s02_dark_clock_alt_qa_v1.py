"""S02 native 4K-cropped real stock must never inherit S01 approval."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from agents import e01_s02_dark_clock_alt_qa_v1 as qa
from agents.e01_s01_single_take_stock_qa import crop_native


class DarkClockResearchTests(unittest.TestCase):
    def setUp(self):
        self.c=json.loads((qa.ROOT/qa.CONTRACT).read_text(encoding="utf8"))

    def test_immutable_scene_and_native_portrait_crop(self):
        data=qa.validate_contract()
        self.assertEqual(data["source_id"],29862379)
        self.assertEqual(crop_native(3840,2160),(1214,2160))
        self.assertEqual(self.c["scene_id"],"VNC-E01V2-S02")
        self.assertEqual(qa.FRAMES,147)
        self.assertFalse(self.c["s02_user_approved"])

    def test_forged_rights_master_source_and_approval_are_denied(self):
        tests=[
          ("project_id","CORTE_FINO"),("scene_id","VNC-E01V2-S01"),
          ("artistic_state","S02_APPROVED"),("s01_preview_immutable",False),
          ("current_s02_not_rejected_or_approved",False),
          ("rights_cleared",True),("master_allowed",True),
          ("publication_authorized",True),("paid_services_authorized",True),
          ("source_media_persisted",True),("s02_user_approved",True),
          ("current_s02_reference_source_id",4458845),
          ("current_s02_grade_a_preview_sha256","x"*64),
        ]
        for k,value in tests:
            bad=copy.deepcopy(self.c)
            bad[k]=value
            with self.subTest(field=k),self.assertRaises(qa.DarkClockQAError):
                qa.validate_contract(obj=bad)

    def test_wrong_page_origin_license_or_crop_is_denied(self):
        checks=[
            ("source_id",7034348),("source_id",True),
            ("page_url","https://evil.example/video"),
            ("source_page_license","Commercial license cleared"),
            ("listing_width",1920),("listing_height",1080),
            ("listing_fps",25),("mp4_verified",True),
            ("rights_cleared",True),("editorial_approved",True),
            ("expected_exact_center_native_crop",[1080,1920])
        ]
        for k,v in checks:
            bad=copy.deepcopy(self.c)
            bad["candidate"][k]=v
            with self.subTest(field=k),self.assertRaises(qa.DarkClockQAError):
                qa.validate_contract(obj=bad)

    def test_preview_cannot_contain_audio_captions_or_publish_flags(self):
        checks=[("portrait_width",1080),("portrait_height",1920),
                ("fps",60),("frames",173),("audio",True),
                ("captions",True),("watermark","")]
        for k,v in checks:
            bad=copy.deepcopy(self.c)
            bad["required_output"][k]=v
            with self.subTest(field=k),self.assertRaises(qa.DarkClockQAError):
                qa.validate_contract(obj=bad)

    def test_failed_download_produces_only_block_report(self):
        with tempfile.TemporaryDirectory() as td:
            with patch.object(qa,"download_source",side_effect=OSError("blocked")):
                result=qa.run(Path(td))
            self.assertEqual(result,2)
            d=Path(td)
            obj=json.loads((d/"S02_DARK_CLOCK_29862379_REPORT.json").read_text())
            self.assertEqual(obj["status"],"BLOCKED_NO_PHYSICAL_VIDEO")
            self.assertFalse(obj["master_allowed"])
            self.assertFalse(obj["publication_authorized"])
            self.assertFalse((d/"S02_DARK_CLOCK_29862379_REVIEW_ONLY.mp4").exists())


if __name__=="__main__":
    unittest.main()
