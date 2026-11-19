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
        self.assertEqual([x["video_id"] for x in cs], [4510748, 28174743])
        self.assertNotIn(4458845, [x["video_id"] for x in cs])
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
        for field,val in (("video_id", 4458845),
                          ("video_id", True),
                          ("page_url", "https://evil.example/video/4510748/"),
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

    def test_partial_physical_qa_is_preserved_but_still_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)
            fake = path / "mock_source.mp4"
            fake.write_bytes(b"only a mock, not a real movie")
            attempts = [0]

            def fake_download(_source, _work):
                attempts[0] += 1
                if attempts[0] == 2:
                    from agents.e01_s01_multi_stock_pilot_v1 import PilotError
                    raise PilotError("source_not_compatible")
                return fake, {
                    "video_id": 4510748, "page_url": "https://www.pexels.com/video/woman-sitting-by-the-window-4510748/",
                    "bytes": 999999, "source_sha256": "a" * 64,
                    "source_rights_cleared": False
                }

            fake_probe = {"width": 2160, "height": 3840, "duration_seconds": 9.958,
                          "source_codec": "h264"}
            contact = {"sha256": "b" * 64, "path": "mock.jpg"}
            with patch.object(m, "download_source", side_effect=fake_download), \
                 patch.object(m, "probe", return_value=fake_probe), \
                 patch.object(m, "run_cmd", return_value=None), \
                 patch.object(m, "frame_at", return_value=object()), \
                 patch.object(m, "build_contact", return_value=contact):
                code, result = m.run(m.ROOT, path)
            self.assertEqual(code, 2)
            self.assertEqual(result["status"], "BLOCKED_PARTIAL_PHYSICAL_QA_EDITORIAL_RIGHTS_PENDING")
            self.assertEqual(result["error_code"], "source_not_compatible")
            self.assertEqual(result["failed_source_video_id"], 28174743)
            self.assertEqual(len(result["clips"]), 1)
            self.assertEqual(result["contact_sheet"], contact)
            self.assertFalse(result["master_allowed"])
            self.assertFalse(result["publication_authorized"])

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
            self.assertTrue((Path(td)/"S01_SINGLE_TAKE_REPORT.json").is_file())
            self.assertFalse((Path(td)/"S01_SINGLE_TAKE_CANDIDATES_QA.jpg").exists())


if __name__=="__main__":
    unittest.main()
