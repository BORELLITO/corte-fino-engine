"""Fail-closed tests for physically reproducing E01 S01/S02 QA with the original WAV."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agents import e01_s01_s02_real_voice_sync_qa_v1 as qa


class RealVoiceSceneQATests(unittest.TestCase):
    def setUp(self):
        self.c = qa.contract_checked()

    def altered(self, obj):
        tmp = tempfile.TemporaryDirectory()
        p = Path(tmp.name) / "altered.json"
        p.write_text(json.dumps(obj), encoding="utf-8")
        return tmp, p

    def test_canonical_input_hashes_and_geometry_locked(self):
        c = self.c
        self.assertEqual(c["project_id"], "VERBO_NO_CHAO_EXCLUSIVO")
        self.assertEqual(c["approval_state"], "S01_VISUAL_APPROVED_S02_CANDIDATE_NOT_APPROVED")
        self.assertEqual(c["input"]["wav"]["sha256"],
                         "4f2ee1ff0171ddedb7c64e0dce2300c53a0ef105ef12d643a7af6b0a4621942e")
        self.assertEqual(c["input"]["video"]["sha256"],
                         "f30b1e1461412185f429bfa28c1b42a2def53b6ce8704fcc84a7ee99348f774c")
        self.assertEqual(c["input"]["ass"]["caption_dialogue_cues"], 28)
        self.assertEqual(c["output_requirements"]["video_frames"], 319)
        self.assertTrue(c["input"]["video"]["with_original_karaoke_burned"])
        self.assertEqual(c["output_requirements"]["voice_start_offset_seconds"], 0)
        self.assertFalse(c["output_requirements"]["must_not_add_music"] is False)

    def test_release_or_approval_forgery_invalidates_contract(self):
        bad_fields = [
            ("project_id", "CAPTAPRONTO"),
            ("scope", "COMPLETE_MASTER"),
            ("approval_state", "S02_APPROVED"),
            ("s02_approved", True),
            ("rights_cleared", True),
            ("master_allowed", True),
            ("publication_authorized", True),
        ]
        for key, value in bad_fields:
            with self.subTest(key=key):
                bad = copy.deepcopy(self.c)
                bad[key] = value
                tmp, p = self.altered(bad)
                with tmp, self.assertRaises(qa.VoiceSyncQAError):
                    qa.contract_checked(p)

    def test_inputs_and_audio_processing_cannot_change_silently(self):
        nested = [
            ("video","sha256","f"*64),
            ("video","frames",320),
            ("video","audio_streams",1),
            ("video","with_original_karaoke_burned",False),
            ("wav","sha256","0"*64),
            ("wav","sample_rate_hz",44100),
            ("wav","duration_seconds",69.0),
            ("ass","sha256","f"*64),
            ("ass","caption_dialogue_cues",27)
        ]
        for section,key,value in nested:
            with self.subTest(key=section+"."+key):
                bad = copy.deepcopy(self.c)
                bad["input"][section][key] = value
                tmp, p = self.altered(bad)
                with tmp, self.assertRaises(qa.VoiceSyncQAError):
                    qa.contract_checked(p)
        for key,value in [
            ("mp4_audio_codec","mp3"),("audio_sample_rate_hz",44100),
            ("aac_bitrate","320k"),("voice_start_offset_seconds",0.25),
            ("video_bitstream_copy",False),("must_not_add_music",False),
            ("must_not_timestretch_or_rerender_voice",False),
            ("output_must_not_overwrite_existing",False),
            ("full_decode_required",False),("master_allowed",True),
            ("publication_authorized",True),("merge_authorized",True),
            ("rights_cleared",True),
        ]:
            with self.subTest(key=key):
                bad=copy.deepcopy(self.c)
                bad["output_requirements"][key]=value
                tmp,p=self.altered(bad)
                with tmp,self.assertRaises(qa.VoiceSyncQAError):
                    qa.contract_checked(p)

    def test_missing_source_creates_blocked_report_without_video(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            with patch.object(qa, "run_cmd", side_effect=AssertionError("no ffmpeg before sha")):
                status=qa.mux(root/"missing.mp4",root/"missing.wav",
                              root/"missing.ass",root/"out")
            self.assertEqual(status,2)
            report=json.loads((root/"out"/qa.REPORT_NAME).read_text(encoding="utf-8"))
            self.assertEqual(report["status"],"BLOCKED_REAL_VOICE_QA_NOT_REPRODUCED")
            self.assertFalse(report["master_allowed"])
            self.assertFalse(report["publication_authorized"])
            self.assertFalse((root/"out"/qa.DEST_NAME).exists())

    def test_fake_bytes_are_not_accepted_as_original_media(self):
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td)
            files=[folder/"fake_video.mp4",folder/"fake_voice.wav",folder/"fake.ass"]
            for f in files:
                f.write_bytes(b"FAKE" * 100)
            with patch.object(qa,"run_cmd",side_effect=AssertionError("must reject fake hash")):
                result=qa.mux(*files,folder/"out")
            self.assertEqual(result,2)
            report=json.loads((folder/"out"/qa.REPORT_NAME).read_text(encoding="utf8"))
            self.assertEqual(report["error_code"],"input_sha256_mismatch_video")
            self.assertFalse((folder/"out"/qa.DEST_NAME).exists())

    def test_previous_local_proof_is_not_claimed_ci_rerender(self):
        p=self.c["local_physical_evidence"]
        self.assertEqual(p["preview_sha256"],
                         "979fcb7d630177efc99e76baa98adc0d34cf0d3a89beaf06484060c7bdd6e5f6")
        self.assertEqual(p["preview_bytes"],2264744)
        self.assertTrue(p["full_video_and_audio_decode_passed"])
        self.assertEqual(p["approx_audio_lag_ms"],0)
        self.assertFalse(self.c["master_allowed"])
        self.assertFalse(self.c["publication_authorized"])


if __name__ == "__main__":
    unittest.main()
