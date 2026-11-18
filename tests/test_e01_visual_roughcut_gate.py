"""Proof-oriented tests for real but private Library-sourced storyboard media."""
import json
import re
import tempfile
import unittest
import zipfile
from pathlib import Path

from agents.content_production import ProductionError
from agents.e01_visual_roughcut_gate import (
    PATH,EXACT_WAV_SHA,EXACT_ASR_ASS_SHA,EXACT_SCRIPT_SHA,
    EXACT_ZIP_SHA,EXACT_VIDEO_SHA,manifest,package,video,
)

ROOT=Path(__file__).resolve().parents[1]


def altered(temp:Path,fn):
    source=json.loads((ROOT/PATH).read_text(encoding="utf-8"))
    fn(source)
    target=temp/PATH
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(source,ensure_ascii=False),encoding="utf-8")


class VisualRoughcutProofTests(unittest.TestCase):
    def test_12_scene_manifest_contains_original_ai_assets(self):
        e=manifest(ROOT)
        self.assertEqual(e["shot_count"],12)
        self.assertEqual(e["shots"][0]["id"],"E01V2-S01")
        self.assertEqual(e["shots"][-1]["id"],"E01V2-S12")
        self.assertTrue(all(z["image_is_ai_generated"] for z in e["shots"]))
        self.assertTrue(all(z["source"]=="CHATGPT_IMAGEGEN_ORIGINAL" for z in e["shots"]))

    def test_protected_older_script_wav_and_caption_shas(self):
        e=manifest(ROOT)
        self.assertEqual(e["source_script_sha256"],EXACT_SCRIPT_SHA)
        self.assertEqual(e["source_voice_wav_sha256"],EXACT_WAV_SHA)
        self.assertEqual(e["source_caption_ass_sha256"],EXACT_ASR_ASS_SHA)
        self.assertEqual(e["source_package_sha256"],EXACT_ZIP_SHA)
        self.assertEqual(e["real_local_preview"]["sha256"],EXACT_VIDEO_SHA)

    def test_scene_timeline_is_continuous_exactly_70_425_seconds(self):
        s=manifest(ROOT)["shots"]
        self.assertEqual(s[0]["start_seconds"],0)
        self.assertEqual(s[-1]["end_seconds"],70.425)
        self.assertTrue(all(abs(s[i]["end_seconds"]-s[i+1]["start_seconds"])<.001
                            for i in range(len(s)-1)))

    def test_full_render_remains_roughcut_not_1080p_master(self):
        e=manifest(ROOT)
        p=e["real_local_preview"]
        self.assertEqual((p["width"],p["height"],p["fps"]),(720,1280,30))
        self.assertEqual(p["frames"],2113)
        self.assertTrue(p["pan_zoom_motion_simulated"])
        self.assertFalse(p["assets_are_actual_motion_video_clips"])
        self.assertFalse(e["full_1080x1920_master_exists"])
        self.assertFalse(e["publication_authorized"])

    def test_all_scene_originals_remain_below_native_master_quality(self):
        e=manifest(ROOT)
        self.assertTrue(all(z["source_resolution_adequate_for_master"] is False
                            and z["verified_final_visual_quality"] is False for z in e["shots"]))
        self.assertTrue(e["storyboard_tile_native_resolutions_low"])

    def test_release_rights_can_never_be_promoted_by_images(self):
        e=manifest(ROOT)
        self.assertFalse(e["music_included"])
        self.assertFalse(e["music_license_verified"])
        self.assertFalse(e["commercial_voice_rights_cleared"])
        self.assertFalse(e["publication_authorized"])
        self.assertFalse(e["reproducible_in_github_actions_now"])

    def test_unknown_image_replacement_cannot_pass_metadata_gate(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            altered(root,lambda e:e["shots"][2].update(sha256="x"*64))
            with self.assertRaisesRegex(ProductionError,"asset_metadata_invalid"):
                manifest(root)

    def test_fake_commercial_approval_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            altered(root,lambda e:e.update(music_license_verified=True))
            with self.assertRaisesRegex(ProductionError,"fake_commercial_or_release_approval"):
                manifest(root)

    def test_bad_scene_timing_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            altered(root,lambda e:e["shots"][4].update(start_seconds=33))
            with self.assertRaisesRegex(ProductionError,"scene_timeline_gap_or_overlap"):
                manifest(root)

    def test_relabeling_pan_zoom_as_generated_motion_clips_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            altered(root,lambda e:e["real_local_preview"].update(assets_are_actual_motion_video_clips=True))
            with self.assertRaisesRegex(ProductionError,"fake_clip_or_invalid_video_metrics"):
                manifest(root)

    def test_no_physical_asset_files_inside_repo_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            empty=root/"missing.zip"
            with self.assertRaisesRegex(ProductionError,"zip_sha_or_size_not_exact"):
                package(ROOT,empty)

    def test_zip_forgery_or_stale_source_also_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            wrong=Path(d)/"originals.zip"
            with zipfile.ZipFile(wrong,"w") as z:
                z.writestr("stills/E01V2_SCENE_01.jpg","not the real photo")
            with self.assertRaisesRegex(ProductionError,"zip_sha_or_size_not_exact"):
                package(ROOT,wrong)

    def test_fake_mp4_is_rejected_by_real_byte_hash(self):
        with tempfile.TemporaryDirectory() as d:
            wrong=Path(d)/"rough.mp4"
            wrong.write_bytes(b"not a real MP4")
            with self.assertRaisesRegex(ProductionError,"video_bytes_or_sha_changed"):
                video(ROOT,wrong)

    def test_hashes_and_sha_lengths_are_not_inferred_from_name(self):
        e=manifest(ROOT)
        self.assertTrue(all(re.fullmatch("[0-9a-f]{64}",z["sha256"])
                            and z["size_bytes"]>20000 for z in e["shots"]))
        self.assertEqual(len({z["sha256"] for z in e["shots"]}),12)

    def test_no_cloud_render_claim_until_secure_source_connected(self):
        e=manifest(ROOT)
        self.assertFalse(e["reproducible_in_github_actions_now"])
        self.assertIn("ChatGPT personal Library",e["asset_package_location"])
        self.assertEqual(e["status"],
                         "REAL_LOCAL_ROUGHCUT_MEDIA_BYTES_VERIFIED_NOT_CLOUD_EXECUTABLE")


if __name__=="__main__":
    unittest.main()
