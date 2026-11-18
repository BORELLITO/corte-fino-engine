"""No fake identity, no still-image-as-real-motion, and no premature i2v handoff."""
from __future__ import annotations
import copy
import json
import unittest

from agents.e01_s01_video_anchor import (
    ROOT,BLUEPRINT,SAMPLE_FPS,TIMES,SCENE_SECONDS,
    validate_blueprint,validate_source_report,byte_motion_stats
)
from agents.e01_stock_candidates import StockIntakeError

class TestE01S01VideoAnchor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=json.loads((ROOT/BLUEPRINT).read_text(encoding="utf-8"))

    def broken(self,mutate):
        plan=copy.deepcopy(self.plan)
        mutate(plan)
        with self.assertRaises(StockIntakeError):
            validate_blueprint(ROOT,plan)

    def test_blueprint_exactly_eight_same_world_scenes(self):
        info=validate_blueprint(ROOT)
        self.assertEqual(info["scene_count"],8)
        self.assertFalse(info["publication_authorized"])
        self.assertFalse(info["reference_images_editorially_approved"])
        self.assertEqual(TIMES[0],0.0)
        self.assertLess(TIMES[-1],SCENE_SECONDS)
        self.assertEqual(SAMPLE_FPS,6)

    def test_no_fake_actor_approval(self):
        self.broken(lambda d:d.update(approved_first_frame_sha256="a"*64))
        self.broken(lambda d:d.update(same_person_across_scenes_verified=True))
        self.broken(lambda d:d.update(multiscene_generation_authorized=True))
        self.broken(lambda d:d.update(publication_authorized=True))
        self.broken(lambda d:d.update(first_frame_conditioning_cannot_guarantee_identity=False))

    def test_no_wrong_shots_or_cross_scene_blind_reuse(self):
        self.broken(lambda d:d["room_a_scene_plan"][0].update(id="VNC-E01V2-S03"))
        self.broken(lambda d:d["room_a_scene_plan"][1].update(start_seconds=11))
        self.broken(lambda d:d["room_a_scene_plan"][2].update(can_enter_master=True))
        self.broken(lambda d:d["room_a_scene_plan"][3].update(
            initial_reference_scene="VNC-E01V2-S05"))
        self.broken(lambda d:d["room_a_scene_plan"].pop())

    def test_unchanged_frames_are_not_genuine_motion_evidence(self):
        raw=bytes([34,34,34,34])*8
        info=byte_motion_stats(raw,4)
        self.assertFalse(info["motion_signal_detected"])
        self.assertEqual(info["mean_absolute_luma_change"],0)

    def test_temporal_delta_can_indicate_motion_but_not_semantics(self):
        raw=b"".join(bytes([n])*4 for n in (0,30,0,30,0,30,0,30))
        info=byte_motion_stats(raw,4)
        self.assertTrue(info["motion_signal_detected"])
        self.assertTrue(info["not_a_semantic_quality_or_actor_consistency_test"])
        with self.assertRaises(StockIntakeError):
            byte_motion_stats(b"\x00\x01\x02",4)
        with self.assertRaises(StockIntakeError):
            byte_motion_stats(bytes([10])*20,4)

    def test_false_provenance_and_approval_are_rejected(self):
        media={
         "sha256":"a"*64,"bytes":1000000,"duration_seconds":6.041667,
         "width":480,"height":848,"codec":"h264","frame_rate":"24/1",
         "reported_frames":"145","full_stream_decoded":True,
         "covers_requested_scene":True,"portrait_within_2pct":True,
        }
        report={
         "episode_id":"VNC-W01-E1","scene_id":"VNC-E01V2-S01",
         "media_origin":"AI_GENERATED_FICTIONAL_VIDEO",
         "status":"PHYSICAL_AI_PREVIEW_ELIGIBLE_FOR_EDITORIAL_REVIEW_ONLY",
         "video_file":"scene.mp4","media":media.copy(),
         "technically_eligible_for_editorial":True,
         "rights_cleared":False,"approved_for_master":False,
         "publication_authorized":False,
         "origin_and_usage_license_review_complete":False,
         "visual_continuity_verified":False,
         "closed_notebook_and_rain_visually_verified":False,
        }
        validate_source_report(report,media,"scene.mp4")
        for field,val in (
           ("status","BLOCKED_ZEROGPU_QUOTA_INSUFFICIENT"),
           ("scene_id","VNC-E01V2-S05"),
           ("approved_for_master",True),
           ("rights_cleared",True),
           ("closed_notebook_and_rain_visually_verified",True)
        ):
            modified=dict(report)
            modified[field]=val
            with self.subTest(field=field),self.assertRaises(StockIntakeError):
                validate_source_report(modified,media,"scene.mp4")
        altered=media.copy();altered["sha256"]="f"*64
        with self.assertRaises(StockIntakeError):
            validate_source_report(report,altered,"scene.mp4")

if __name__=="__main__":
    unittest.main()
