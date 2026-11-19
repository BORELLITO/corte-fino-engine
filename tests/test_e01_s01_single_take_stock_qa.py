"""Offline fail-closed contract and geometry tests for camera stock S01."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agents import e01_s01_single_take_stock_qa as m


class SingleTakeContractTests(unittest.TestCase):
    def test_contract_is_candidate_only_and_distinct_from_rejected_sets(self):
        cs = m.validate_plan()
        self.assertEqual([x["video_id"] for x in cs], [7026683])
        self.assertNotIn(4510748, [x["video_id"] for x in cs])
        self.assertNotIn(28174743, [x["video_id"] for x in cs])
        self.assertEqual(m.SAMPLE_TIMES, (0.5, 2.8, 5.4))
        self.assertLess(max(m.SAMPLE_TIMES), m.WINDOW)

    def test_block_forged_publish_or_rights(self):
        base = json.loads((m.ROOT/m.CONTRACT).read_text())
        for field, val in (("publication_authorized", True),
                           ("editorial_approval", True),
                           ("full_master_authorized", True),
                           ("commercial_rights", "CLEARED"),
                           ("no_cost_trial_only", False),
                           ("scene_id", "VNC-E01V2-S02"),
                           ("project_id", "CORTE_FINO")):
            forged = copy.deepcopy(base)
            forged[field]=val
            with self.subTest(field=field), self.assertRaises(m.SingleTakeProbeError):
                m.validate_plan(obj=forged)

    def test_candidate_ids_urls_and_state_are_locked(self):
        base=json.loads((m.ROOT/m.CONTRACT).read_text())
        for field,val in (("video_id", 4510748),
                          ("video_id", True),
                          ("page_url", "https://evil.example/video/7026683/"),
                          ("downloaded", True),
                          ("editorial_status", "APPROVED"),
                          ("rights_cleared", True),
                          ("known_conflict", "")):
            forged=copy.deepcopy(base)
            forged["candidates"][0][field]=val
            with self.subTest(field=field,val=val), self.assertRaises(m.SingleTakeProbeError):
                m.validate_plan(obj=forged)

    def test_geometry_native_portrait_crop_is_measurable(self):
        self.assertEqual(m.crop_native(2160,3840),(2160,3840))
        self.assertEqual(m.crop_native(3840,2160),(1214,2160))
        self.assertEqual(m.crop_native(1080,1920),(1080,1920))
        for wh in ((1920,1080),(720,1280),(True,3840),(0,5000),(5000,1200)):
            with self.subTest(wh=wh), self.assertRaises(m.SingleTakeProbeError):
                m.crop_native(*wh)

    def test_single_source_technical_success_remains_unapproved(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)
            fake=path/"mock_source.mp4"
            fake.write_bytes(b"mock only, not a real movie")
            meta={"video_id":7026683,
                  "page_url":"https://www.pexels.com/video/a-woman-writing-on-the-notebook-7026683/",
                  "bytes":999999,"source_sha256":"a"*64,"source_rights_cleared":False}
            p={"width":2160,"height":3840,"duration_seconds":10.0,"source_codec":"h264"}
            with patch.object(m,"download_source",return_value=(fake,meta)), \
                 patch.object(m,"probe",return_value=p), \
                 patch.object(m,"run_cmd",return_value=None), \
                 patch.object(m,"frame_at",return_value=object()), \
                 patch.object(m,"build_contact",return_value={"path":"mock.jpg","sha256":"b"*64}):
                code,result=m.run(m.ROOT,path)
            self.assertEqual(code,0)
            self.assertEqual(result["status"],
                "PHYSICAL_SINGLE_TAKE_CANDIDATES_READY_FOR_HUMAN_FRAME_REVIEW_ONLY")
            self.assertFalse(result["editorial_approved"])
            self.assertFalse(result["master_allowed"])
            self.assertFalse(result["rights_cleared"])
            self.assertFalse(result["publication_authorized"])
            self.assertEqual(len(result["clips"]),1)

    def test_failed_acquisition_is_not_a_success_or_master(self):
        with tempfile.TemporaryDirectory() as td:
            with patch.object(m,"download_source",side_effect=ValueError("no media")):
                code,report=m.run(m.ROOT,Path(td))
            self.assertEqual(code,2)
            self.assertEqual(report["status"],"BLOCKED_NO_NEW_MEDIA_QA")
            self.assertFalse(report["rights_cleared"])
            self.assertFalse(report["publication_authorized"])
            self.assertFalse(report["master_allowed"])
            self.assertFalse(report["new_master_created"])
            self.assertTrue((Path(td)/"S01_SINGLE_TAKE_V2_REPORT.json").is_file())
            self.assertFalse((Path(td)/"S01_SINGLE_TAKE_V2_QA.jpg").exists())


if __name__=="__main__":
    unittest.main()
