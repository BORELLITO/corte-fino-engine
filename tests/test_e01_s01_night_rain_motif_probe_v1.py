"""Offline adversarial guardrails for night-rain thematic S01 video preview."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agents import e01_s01_night_rain_motif_probe_v1 as m


class NightRainProbeTests(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads(m.CONTRACT.read_text(encoding="utf8"))

    def test_isolated_identity_and_unapproved_alternative(self):
        c=m.validate_contract()
        self.assertEqual(c["source_id"],31069867)
        self.assertEqual(c["scene_id"],"VNC-E01V2-S01")
        self.assertEqual(c["concept"],"NIGHT_RAIN_WINDOW_SINGLE_TAKE_SYMBOLIC_VISUAL_ALTERNATIVE")
        self.assertIn("Metro window is not ROOM_A",c["known_storyboard_deviation"])
        self.assertEqual(c["approval_status"],"CONCEPT_RESEARCH_ONLY_NOT_USER_APPROVED")

    def test_false_release_rights_music_or_upload_claims_block(self):
        modifications=[
            ("project_id","CORTE_FINO"),
            ("episode_id","VNC-W01-E2"),
            ("scene_id","VNC-E01V2-S05"),
            ("approval_status","APPROVED"),
            ("source_class","AI_GENERATED_VIDEO"),
            ("source_id",4458845),
            ("source_id",True),
            ("page_url","https://evil.example/video"),
            ("page_license","Unrestricted"),
            ("free_cost_only",False),
            ("raw_movie_to_repo",True),
            ("editorial_approved",True),
            ("third_party_rights_cleared",True),
            ("voice_license_cleared",True),
            ("master_allowed",True),
            ("publication_authorized",True),
            ("release_state","MASTER_READY"),
            ("scene_window_seconds",7.2)
        ]
        for key,value in modifications:
            with self.subTest(field=key):
                candidate=copy.deepcopy(self.contract)
                candidate[key]=value
                with self.assertRaises(m.NightRainProbeError):
                    m.validate_contract(obj=candidate)

    def test_preview_has_exact_frames_video_only_watermark(self):
        for key,value in [
            ("width",1080),("height",1920),("fps",60),
            ("frames",100),("source_audio_removed",False),
            ("voice_added",True),("subtitles_added",True),
            ("watermark","")
        ]:
            with self.subTest(key=key):
                candidate=copy.deepcopy(self.contract)
                candidate["experimental_preview"][key]=value
                with self.assertRaises(m.NightRainProbeError):
                    m.validate_contract(obj=candidate)

    def test_rejected_sources_not_reused(self):
        self.assertNotIn(31069867, self.contract["rejected_source_ids"])
        test=copy.deepcopy(self.contract)
        test["rejected_source_ids"].append(31069867)
        with self.assertRaises(m.NightRainProbeError):
            m.validate_contract(obj=test)

    def test_no_movie_is_fail_closed_and_report_is_real(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            with patch.object(m,"download_source",side_effect=ValueError("blocked-download")):
                exit_code=m.run(root)
            self.assertEqual(exit_code,2)
            rep=json.loads((root/"S01_NIGHT_RAIN_PHYSICAL_QA_REPORT.json").read_text())
            self.assertEqual(rep["status"],"BLOCKED_NO_PHYSICAL_PREVIEW")
            self.assertFalse(rep["publication_authorized"])
            self.assertFalse(rep["master_allowed"])
            self.assertFalse(rep["editorial_approved"])
            self.assertIsNone(rep["output"])
            self.assertFalse((root/"S01_NIGHT_RAIN_SYMBOLIC_PREVIEW_NOT_MASTER.mp4").exists())

    def test_native_portrait_crop_is_not_an_upscaled_720p_illusion(self):
        from agents.e01_s01_single_take_stock_qa import crop_native
        self.assertEqual(crop_native(2160,3840),(2160,3840))
        self.assertEqual(m.FPS,30)
        self.assertEqual(m.FRAMES,173)
        self.assertAlmostEqual(m.FRAMES/m.FPS,5.766666,places=4)


if __name__=="__main__":
    unittest.main()
