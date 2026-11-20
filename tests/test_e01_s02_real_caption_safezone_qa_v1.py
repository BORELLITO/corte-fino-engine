"""E01 canonical karaoke: protect source hashes, releases, frames and voice/caption integrity."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agents import e01_s02_real_caption_safezone_qa_v1 as c

class S02RealCaptionSafezoneTests(unittest.TestCase):
    def setUp(self):
        self.contract=c.validated_contract()

    def test_approved_s01_is_scene_scoped_while_s02_remains_candidate(self):
        v=self.contract
        self.assertEqual(v["project_id"],"VERBO_NO_CHAO_EXCLUSIVO")
        self.assertEqual(v["scene_id"],"VNC-E01V2-S02")
        self.assertEqual(v["approval_state"],"S01_VISUAL_APPROVED_S02_UNAPPROVED")
        self.assertTrue(v["s01"]["owner_approved_visual"])
        self.assertFalse(v["s02"]["visual_owner_approved"])
        self.assertEqual(v["s01"]["frames_used"],172)
        self.assertEqual(v["s02"]["frames_used"],147)
        self.assertEqual(c.EXPECTED_FRAMES,319)
        self.assertEqual((c.W,c.H,c.FPS),(720,1280,30))

    def test_current_original_ass_is_fixed_and_proven(self):
        a=self.contract["canonical_caption_artifact"]
        self.assertEqual(a["ass_sha256"],"0b8171a473cbc247eb48ed822bb006a04c74510b8c4cd1b30e409c226f1bb98a")
        self.assertEqual(a["caption_cue_total"],28)
        self.assertTrue(a["caption_text_and_times_unchanged"])
        self.assertTrue(a["voice_wav_not_present_in_preview"])
        self.assertEqual(self.contract["output_requirements"]["contains_audio"],False)

    def test_disallow_project_identity_rights_approval_and_publication_forgery(self):
        for key,val in [
            ("project_id","CORTE_FINO"),
            ("episode_id","VNC-W01-E2"),
            ("scene_id","VNC-E01V2-S01"),
            ("approval_state","S02_APPROVED"),
            ("rights_cleared",True),
            ("master_allowed",True),
            ("publication_authorized",True),
            ("merge_authorized",True),
            ("spend_authorized",True),
            ("s02_editorial_approved",True),
        ]:
            bad=copy.deepcopy(self.contract)
            bad[key]=val
            with self.subTest(field=key),self.assertRaises(c.CaptionSafezoneQAError):
                c.validated_contract(obj=bad)

    def test_no_caption_or_scene_retiming_is_possible_silently(self):
        for sub,key,value in [
          ("s01","source_preview_sha256","f"*64),
          ("s01","frames_used",173),
          ("s01","owner_approved_visual",False),
          ("s02","graded_a_preview_sha256","f"*64),
          ("s02","frames_used",146),
          ("s02","selected_qa_gradient_strength",0.90),
          ("s02","visual_owner_approved",True),
          ("canonical_caption_artifact","ass_sha256","f"*64),
          ("canonical_caption_artifact","caption_cue_total",27),
          ("canonical_caption_artifact","caption_text_and_times_unchanged",False),
          ("output_requirements","frames",320),
          ("output_requirements","fps",60),
          ("output_requirements","contains_audio",True),
          ("output_requirements","master_allowed",True),
          ("output_requirements","publication_authorized",True),
        ]:
            bad=copy.deepcopy(self.contract)
            bad[sub][key]=value
            with self.subTest(key=sub+"."+key),self.assertRaises(c.CaptionSafezoneQAError):
                c.validated_contract(obj=bad)

    def test_no_media_never_generates_fake_preview_or_unlocks_release(self):
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td)
            with patch.object(c,"command",side_effect=AssertionError("ffmpeg should not be attempted")):
                code=c.render(folder/"missing_s01.mp4",
                                     folder/"missing_s02.mp4",
                                     folder/"missing_ass.ass",
                                     folder/"out")
            result=json.loads((folder/"out"/"S02_REAL_KARAOKE_QA_RESULT.json").read_text(encoding="utf8"))
            self.assertEqual(code,2)
            self.assertEqual(result["status"],"BLOCKED_KARAOKE_QA_NOT_REPRODUCED")
            self.assertFalse(result["master_allowed"])
            self.assertFalse(result["publication_authorized"])
            self.assertFalse((folder/"out"/"S01_S02_REAL_KARAOKE_GRADIENT55_QA_NOT_MASTER.mp4").exists())

    def test_source_hash_check_prevents_accidental_unapproved_surrogate(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            files=[root/"S01.mp4",root/"S02.mp4",root/"caption.ass"]
            for f in files:
                f.write_bytes(b"fake")
            with patch.object(c,"command",side_effect=AssertionError("decoder must not run")):
                code=c.render(*files,root/"out")
            self.assertEqual(code,2)
            result=json.loads((root/"out"/"S02_REAL_KARAOKE_QA_RESULT.json").read_text(encoding="utf8"))
            self.assertEqual(result["status"],"BLOCKED_KARAOKE_QA_NOT_REPRODUCED")

    def test_physical_evidence_is_explicitly_not_editorial_approval(self):
        e=self.contract["measured_local_physical_evidence"]
        self.assertEqual(e["selected_gradient55_composite_ass_sha256"],
                         "f30b1e1461412185f429bfa28c1b42a2def53b6ce8704fcc84a7ee99348f774c")
        self.assertEqual(e["threeway_frame_contact_sha256"],
                         "89fe5ad902652167178dae58260841d0c5782747be54ea75c9072b3c095de87e")
        self.assertEqual(e["luma_mean_caption_area_at_8_6_seconds"]["gradient_55_percent"],47.5)
        self.assertTrue(self.contract["s02_editorial_approved"] is False)
        self.assertFalse(self.contract["rights_cleared"])


if __name__=="__main__":
    unittest.main()
