"""Adversarial tests for the free daily Google Flow S01-12 acquisition contract."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from agents import e01_flow_free_daily_intake_gate as gate


class TestFlowFreeDaily(unittest.TestCase):
    def test_canonical_timecodes_and_free_daily_budget(self):
        manifest=gate.verified_manifest()
        self.assertEqual(len(manifest["scenes"]),12)
        self.assertEqual(sum(s["credits_estimate"] for s in manifest["scenes"]),120)
        by_day=[sum(s["credits_estimate"] for s in manifest["scenes"]
                    if s["suggested_day"]==d) for d in (1,2,3)]
        self.assertEqual(by_day,[50,50,20])
        self.assertEqual(manifest["scenes"][0]["source_duration_seconds"],5.74)
        self.assertEqual(manifest["scenes"][-1]["requested_video_seconds"],4)
        self.assertFalse(manifest["publication_authorized"])
        self.assertFalse(manifest["live_user_account_entitlement_verified"])

    def test_no_fake_paid_or_publication_entitlement(self):
        data=gate.verified_manifest()
        bad=[]
        for key, value in (
            ("publication_authorized",True),
            ("master_allowed",True),
            ("rights_cleared",True),
            ("live_user_account_entitlement_verified",True),
            ("automated_browser_credentials_or_unofficial_api_permitted",True),
            ("regular_user_free_daily_credits_officially_advertised",100)):
            x=copy.deepcopy(data);x[key]=value;bad.append(x)
        x=copy.deepcopy(data);x["scenes"][0]["final_use_allowed"]=True;bad.append(x)
        x=copy.deepcopy(data);x["scenes"][0]["requested_video_seconds"]=4;bad.append(x)
        x=copy.deepcopy(data);x["scenes"][2]["requested_video_seconds"]=6;bad.append(x)
        x=copy.deepcopy(data);x["scenes"][7]["suggested_day"]=2;bad.append(x)
        x=copy.deepcopy(data);x["scenes"][0]["output_filename"]="../x.mp4";bad.append(x)
        for i, trial in enumerate(bad):
            with self.subTest(case=i), tempfile.TemporaryDirectory() as tmp:
                base=Path(tmp)
                path=base/gate.CONTRACT
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_text(json.dumps(trial),encoding="utf8")
                story=base/gate.STORY
                story.write_bytes((gate.ROOT/gate.STORY).read_bytes())
                with self.assertRaises(gate.IntakeRejected):
                    gate.verified_manifest(base)

    def test_missing_media_is_not_fake_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            result=gate.audit_files(Path(tmp))
        self.assertEqual(result["physical_candidates_verified"],0)
        self.assertFalse(result["publication_authorized"])
        self.assertEqual(len(result["scenes"]),12)

    def test_small_fake_media_blocked_without_probe(self):
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/"fake.mp4"
            file.write_bytes(b"not real video")
            with self.assertRaises(gate.IntakeRejected):
                gate.inspect_file(file,5.74)

    def test_mock_real_physical_video_still_never_releases(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"scene.mp4"
            path.write_bytes(b"A"*120000)
            video_info={
                "streams":[{"codec_name":"h264","width":720,"height":1280,"avg_frame_rate":"30/1"}],
                "format":{"duration":6.0}}
            fake_probe=SimpleNamespace(returncode=0,stdout=json.dumps(video_info))
            decode=SimpleNamespace(returncode=0,stdout=b"",stderr=b"")
            step=48*84
            motion=SimpleNamespace(returncode=0,
               stdout=b"".join(bytes([10+i]) * step for i in range(18)),stderr=b"")
            with patch.object(gate,"_run",return_value=fake_probe), \
                 patch.object(gate.subprocess,"run",side_effect=[decode,motion]):
                observation=gate.inspect_file(path,5.74)
            self.assertEqual(observation["status"],"PHYSICAL_BYTES_VALID_PENDING_EDITORIAL_AND_RIGHTS")
            self.assertTrue(observation["full_mp4_decode"])
            self.assertFalse(observation["rights_cleared"])
            self.assertFalse(observation["master_allowed"])
            self.assertFalse(observation["publication_authorized"])
            self.assertFalse(observation["human_and_object_temporal_motion_verified"])

    def test_landscape_and_short_video_rejected_without_full_decode(self):
        for duration, width, height in ((5.3,720,1280),(6.0,1280,720)):
            with self.subTest(duration=duration,width=width), tempfile.TemporaryDirectory() as tmp:
                path=Path(tmp)/"scene.mp4";path.write_bytes(b"A"*120000)
                probe={"streams":[{"codec_name":"h264","width":width,"height":height,
                                   "avg_frame_rate":"30/1"}],"format":{"duration":duration}}
                with patch.object(gate,"_run",return_value=SimpleNamespace(
                      returncode=0,stdout=json.dumps(probe))), \
                     patch.object(gate.subprocess,"run") as decode, \
                     self.assertRaises(gate.IntakeRejected):
                    gate.inspect_file(path,5.74)
                decode.assert_not_called()


if __name__=="__main__":
    unittest.main()
