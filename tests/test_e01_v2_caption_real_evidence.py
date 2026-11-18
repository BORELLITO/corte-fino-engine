"""Pin actual cloud subtitle-render bytes and protect media release boundary."""
import json
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/"contracts/e01_v2_caption_qa_real_evidence_v1.json"


class E01V2RealCaptionEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e=json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_exact_successful_cloud_provenance_pinned(self):
        self.assertEqual(self.e["source_workflow_run_id"],44208934506)
        self.assertEqual(self.e["source_workflow_sha"],
                         "5d64b3261ace02ab7108647c73a0d01a533a8442")
        self.assertEqual(self.e["source_artifact_id"],14385236602)

    def test_all_real_files_have_sizes_and_sha256(self):
        files=self.e["outputs"]
        self.assertEqual(len(files),7)
        self.assertEqual(len({x["filename"] for x in files}),7)
        self.assertTrue(all(x["bytes"]>100 and re.fullmatch("[0-9a-f]{64}",x["sha256"])
                            for x in files))

    def test_real_subtitles_are_28_two_line_cues_with_all_182_tokens(self):
        e=self.e
        self.assertEqual(e["caption_cues"],28)
        self.assertEqual(e["canonical_words"],182)
        self.assertEqual(e["confirmed_timing_from_primary_asr"],179)
        self.assertEqual(e["timing_from_secondary_asr"],1)
        self.assertEqual(e["phonetic_or_numeric_timing_aliases"],2)
        self.assertEqual(e["interpolated_timestamps"],0)
        self.assertEqual(e["max_lines"],2)
        self.assertEqual(e["max_chars_per_line"],28)

    def test_wav_and_script_hashes_still_exact(self):
        self.assertEqual(self.e["canonical_script_sha256"],
                         "c64b57cb9d6529b60b9e80ab7607e5887f909dd00e14cd80ed9ec2b7474a5dc6")
        self.assertEqual(self.e["physical_wav_sha256"],
                         "4f2ee1ff0171ddedb7c64e0dce2300c53a0ef105ef12d643a7af6b0a4621942e")
        self.assertEqual(self.e["asr_report_sha256"],
                         "377063ff846ddef641b9288656ea867ede965a73991abe6b4c203dec3a919a8b")

    def test_qa_video_physically_decoded_but_not_final(self):
        v=self.e["actual_diagnostic_video"]
        self.assertEqual((v["width"],v["height"]),(540,960))
        self.assertTrue(v["physically_decoded_in_github_ci"])
        self.assertGreater(v["duration_seconds"],70)
        self.assertEqual(v["status"],"QA_DIAGNOSTIC_ONLY_NOT_FINAL")
        self.assertIn("NÃO PUBLICAR",v["embedded_warning"])

    def test_all_real_rights_and_release_states_blocked(self):
        e=self.e
        self.assertFalse(e["visual_assets_physically_generated"])
        self.assertFalse(e["visual_assets_license_verified"])
        self.assertFalse(e["final_video_1080x1920_rendered"])
        self.assertFalse(e["final_video_master_approved"])
        self.assertFalse(e["commercial_voice_rights_cleared"])
        self.assertFalse(e["music_rights_cleared"])
        self.assertFalse(e["full_caption_sync_frame_verified"])
        self.assertFalse(e["publication_authorized"])

    def test_visual_storyboard_exists_without_fabricated_assets(self):
        p=ROOT/self.e["creative_storyboard_ref"]
        doc=json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(len(doc["scenes"]),12)
        self.assertTrue(all(not sc["generated"] for sc in doc["scenes"]))
        self.assertTrue(all(sc["rights"]=="PENDING" for sc in doc["scenes"]))
        self.assertFalse(doc["publication_authorized"])


if __name__=="__main__":
    unittest.main()
