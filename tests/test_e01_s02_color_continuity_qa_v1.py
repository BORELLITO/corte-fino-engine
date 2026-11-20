"""VNC E01 S02 cinematic color grade: fail-closed offline release and hash tests."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agents import e01_s02_color_continuity_qa_v1 as g


class S02ColorContinuityTests(unittest.TestCase):
    def setUp(self):
        self.c = g.load_contract()

    def test_contract_is_s02_only_and_still_pending(self):
        self.assertEqual(self.c["project_id"], "VERBO_NO_CHAO_EXCLUSIVO")
        self.assertEqual(self.c["scene_id"], "VNC-E01V2-S02")
        self.assertEqual(self.c["approval_state"],
                         "S01_APPROVED_S02_CANDIDATE_NOT_APPROVED")
        self.assertEqual(self.c["filter_for_s02_only"], g.GRADE)
        self.assertEqual((g.FPS, g.TOTAL_FRAMES), (30, 319))
        self.assertEqual(self.c["input_preview_source"]["s01_trim_frames"], 172)
        self.assertEqual(self.c["input_preview_source"]["s02_trim_frames"], 147)
        self.assertEqual(self.c["render_requirements"]["master_allowed"], False)
        self.assertEqual(self.c["render_requirements"]["publication_authorized"], False)

    def test_injected_release_flags_and_wrong_source_refs_fail(self):
        for field, bad in (
            ("project_id", "CORTE_FINO"),
            ("episode_id", "VNC-W01-E2"),
            ("scene_id", "VNC-E01V2-S01"),
            ("approval_state", "S02_APPROVED"),
            ("filter_for_s02_only", "unverified_filter"),
        ):
            altered = copy.deepcopy(self.c)
            altered[field] = bad
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "manifest.json"
                path.write_text(json.dumps(altered), encoding="utf-8")
                with self.assertRaises(g.S02ColorContinuityError):
                    g.load_contract(path)
        for flag in ("master_allowed", "publication_authorized",
                     "source_rights_cleared", "audio_included", "captions_included"):
            altered = copy.deepcopy(self.c)
            altered["render_requirements"][flag] = True
            with self.subTest(flag=flag), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "manifest.json"
                path.write_text(json.dumps(altered), encoding="utf-8")
                with self.assertRaises(g.S02ColorContinuityError):
                    g.load_contract(path)

    def test_attempts_to_reuse_rejected_s01_and_forge_s02_approval_fail(self):
        for field, bad in (
            ("s01_expected_sha256", "f"*64),
            ("s02_expected_sha256", "f"*64),
            ("s01_trim_frames", 173),
            ("s02_trim_frames", 146),
            ("s01_art_approved", False),
            ("s02_art_approved", True),
        ):
            altered = copy.deepcopy(self.c)
            altered["input_preview_source"][field] = bad
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "manifest.json"
                path.write_text(json.dumps(altered), encoding="utf-8")
                with self.assertRaises(g.S02ColorContinuityError):
                    g.load_contract(path)

    def test_no_media_fails_closed_without_fake_video_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            rc, report = g.render(folder/"missing_s01.mp4",
                                  folder/"missing_s02.mp4",
                                  folder/"out")
            self.assertEqual(rc, 2)
            self.assertEqual(report["status"], "BLOCKED_COLOR_QA_INCOMPLETE")
            self.assertFalse(report["s02_visual_approved"])
            self.assertFalse(report["master_allowed"])
            self.assertFalse(report["publication_authorized"])
            self.assertFalse((folder/"out"/"S01_APPROVED_S02_GRADED_A_TRANSITION_QA.mp4").exists())
            self.assertTrue((folder/"out"/"S02_COLOR_MATCH_RENDER_REPORT.json").exists())

    def test_fake_movie_bytes_fail_before_ffmpeg_render(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            a, b = folder/"s01.mp4", folder/"s02.mp4"
            a.write_bytes(b"not an mp4")
            b.write_bytes(b"also not an mp4")
            with patch.object(g, "run_command", side_effect=AssertionError("should not call decoder")):
                rc, report = g.render(a, b, folder/"out")
            self.assertEqual(rc, 2)
            self.assertEqual(report["status"], "BLOCKED_COLOR_QA_INCOMPLETE")

    def test_local_physical_evidence_is_qa_only_not_master(self):
        data = self.c["observed_physical_results"]
        self.assertEqual(data["s02_graded_sha256"],
                         "0392829780be80a3228c5c03ee9f06aa9a6332ea1222b95e2687279596b022c3")
        self.assertEqual(data["s01_s02_composite_sha256"],
                         "598675e1e00b2a27880080bdd0052f6bc8ab8ae408d80be2272aeabd1eeae4ae")
        self.assertEqual(data["contact_sheet_sha256"],
                         "0f2f24d81927fb5fbe16b1c216d3b89c5218967b0c9c7012ebabf95aeb8fe146")
        self.assertGreater(data["mean_luma_samples_2_3s"]["s02_original"],
                           data["mean_luma_samples_2_3s"]["s02_color_grade_a"])
        self.assertTrue(self.c["tests_and_limits"]["not_approved_for_s02"])
        self.assertTrue(self.c["tests_and_limits"]["no_publication"])
        self.assertTrue(self.c["tests_and_limits"]["lossy_reencoding_of_s01_in_combined_QA_is_not_pixel_identity"])


if __name__ == "__main__":
    unittest.main()
