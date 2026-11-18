"""Frozen policy invariants for VNC E01 and isolation; metadata checks only.
No external model, network, GPU or publisher is invoked.
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = "c64b57cb9d6529b60b9e80ab7607e5887f909dd00e14cd80ed9ec2b7474a5dc6"
WAV = "4f2ee1ff0171ddedb7c64e0dce2300c53a0ef105ef12d643a7af6b0a4621942e"
ASS = "0b8171a473cbc247eb48ed822bb006a04c74510b8c4cd1b30e409c226f1bb98a"
ROOM = {1, 2, 6, 7, 8, 9, 11, 12}


def doc(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class CanonicalGuardrailMatrix(unittest.TestCase):
    def test_cleanroom_and_autonomy_do_not_authorize_publication(self):
        policy = doc("contracts/autonomous_editorial_policy_v1.json")
        wf = doc("contracts/video_workflow_policy.json")
        self.assertFalse(policy["publication_authorized"])
        self.assertFalse(policy["owner_reviews_intermediate_scripts"])
        self.assertFalse(policy["owner_final_video_approval_required"])
        self.assertTrue(policy["separate_explicit_publication_authorization_required"])
        self.assertFalse(wf["publication_authorized_by_default"])
        self.assertFalse(wf["final_owner_approval_required"])
        self.assertEqual(wf["effective_scope"], "NEW_NON_PILOT_EPISODES_ONLY")
        text = (ROOT / "docs/CLEAN_ROOM_POLICY.md").read_text(encoding="utf-8")
        self.assertIn("Because Of This", text)
        self.assertIn("proibido", text)

    def test_exact_script_audio_anchor_across_independent_contracts(self):
        scene = doc("contracts/e01_v2_12_scene_visual_plan_v1.json")
        world = doc("contracts/e01_v2_visual_single_world_acquisition_v1.json")
        refs = doc("contracts/e01_room_a_reference_handoff_v1.json")
        rights = doc("contracts/e01_v2_media_intake_policy_v1.json")
        self.assertEqual(scene["script_sha256"], SCRIPT)
        self.assertEqual(scene["audio_sha256"], WAV)
        for document in (world, refs):
            self.assertEqual(document["script_sha256"], SCRIPT)
            self.assertEqual(document["audio_sha256"], WAV)
        self.assertFalse(rights["rights_review_completed"])
        self.assertFalse(rights["user_publication_approval"])

    def test_exact_12_scene_70s_timeline_and_28_caption_cues(self):
        scene = doc("contracts/e01_v2_12_scene_visual_plan_v1.json")
        world = doc("contracts/e01_v2_visual_single_world_acquisition_v1.json")
        self.assertEqual(len(scene["scenes"]), 12)
        self.assertEqual(len(world["scenes"]), 12)
        self.assertEqual(scene["duration_seconds"], 70.425)
        self.assertEqual(scene["canvas"]["fps"], 30)
        self.assertEqual((scene["canvas"]["width"], scene["canvas"]["height"]), (1080, 1920))
        self.assertEqual(scene["scenes"][0]["start_seconds"], 0)
        self.assertEqual(scene["scenes"][-1]["end_seconds"], 70.425)
        cues = []
        for i, (shot, production) in enumerate(zip(scene["scenes"], world["scenes"]), start=1):
            self.assertEqual(shot["id"], f"VNC-E01V2-S{i:02d}")
            self.assertEqual(shot["id"], production["shot_id"])
            self.assertEqual(shot["start_seconds"], production["start_seconds"])
            self.assertEqual(shot["end_seconds"], production["end_seconds"])
            cues.extend(shot["caption_cues"])
            if i < 12:
                self.assertEqual(shot["end_seconds"], scene["scenes"][i]["start_seconds"])
        self.assertEqual(cues, list(range(1, 29)))

    def test_room_a_unique_actor_eight_shots_and_remaining_four_groups(self):
        world = doc("contracts/e01_v2_visual_single_world_acquisition_v1.json")
        refs = doc("contracts/e01_room_a_reference_handoff_v1.json")
        indices = {x["scene_index"] for x in world["scenes"]
                   if x["continuity_group"] == "ROOM_A"}
        self.assertEqual(indices, ROOM)
        self.assertEqual({int(x["id"].rsplit("S", 1)[-1]) for x in refs["room_a_scene_plan"]}, ROOM)
        self.assertEqual(len(world["scenes"]) - len(ROOM), 4)
        self.assertFalse(refs["multiscene_generation_authorized"])
        self.assertFalse(refs["reference_qa_verified"])
        self.assertIsNone(refs["approved_first_frame_sha256"])

    def test_all_visual_sources_remain_quarantined_until_real_review(self):
        scene = doc("contracts/e01_v2_12_scene_visual_plan_v1.json")
        world = doc("contracts/e01_v2_visual_single_world_acquisition_v1.json")
        for shot, production in zip(scene["scenes"], world["scenes"]):
            self.assertFalse(shot["generated"])
            self.assertFalse(shot["approved_for_export"])
            self.assertEqual(shot["rights"], "PENDING")
            self.assertIsNone(shot["asset_sha256"])
            self.assertEqual(production["asset_state"], "UNSOURCED")
            self.assertFalse(production["allowed_in_master"])
            self.assertFalse(production["real_motion_verified"])
            self.assertFalse(production["actual_frame_review"])
        self.assertFalse(world["master_1080x1920_rendered"])
        self.assertFalse(world["publication_authorized"])

    def test_s01_closed_notebook_and_loop_intent_no_early_forged_approval(self):
        scene = doc("contracts/e01_v2_12_scene_visual_plan_v1.json")["scenes"]
        self.assertIn("notebook closed", scene[0]["visual_prompt"])
        self.assertIn("loop alignment", scene[-1]["visual_prompt"])
        self.assertIn("notebook", scene[-1]["visual_prompt"])
        self.assertIn("same", scene[-1]["visual_prompt"].lower())

    def test_conservative_caption_zone_is_documented_without_rewriting_story(self):
        world = doc("contracts/e01_v2_visual_single_world_acquisition_v1.json")
        scene = doc("contracts/e01_v2_12_scene_visual_plan_v1.json")
        self.assertEqual(world["global_continuity"]["safe_zone_bottom_px"], 380)
        self.assertTrue(all("420px" in shot["subtitle_safe_zone"] for shot in scene["scenes"]))
        protocol = (ROOT / "docs/VERBO_NO_CHAO_PROTOCOLO_OPERACIONAL_CANONICO_20261118.md").read_text(encoding="utf-8")
        self.assertIn("420 px", protocol)
        self.assertIn("S12", protocol)

    def test_rejected_sources_and_rights_stay_blocked(self):
        source = doc("contracts/e01_source_precision_policy_v1.json")
        self.assertEqual(source["selected_candidate_count"], 0)
        self.assertEqual(len(source["excluded_pexels_video_ids"]), 12)
        self.assertEqual(len(source["excluded_known_video_sha256"]), 13)
        self.assertTrue(source["previously_rejected_source_ids_are_never_auto_reconsidered"])
        self.assertFalse(source["publication_authorized"])
        refs = doc("contracts/e01_room_a_reference_handoff_v1.json")
        self.assertFalse(refs["source_rights_verified"])
        self.assertFalse(refs["automation_may_generate_followups_without_director_approval"])

    def test_legacy_pilot_is_still_not_publishable(self):
        pilot = doc("contracts/pilot_salmo_13_master.json")
        self.assertEqual(pilot["state"], "PREVIEW_READY")
        self.assertFalse(pilot["publication_authorized"])
        self.assertFalse(pilot["owner_approval"])

    def test_one_shot_qa_cannot_be_manually_approved(self):
        data=(ROOT / ".github/workflows/verbo-no-chao-e01-s01-v2-probe.yml").read_text(encoding="utf-8")
        self.assertIn("github.event_name == 'push'", data)
        self.assertIn("vnc-e01-s01-one-shot-free-retest-20261118", data)
        self.assertIn("git diff-tree", data)
        self.assertIn("git rev-list --count", data)
        self.assertIn("publication_authorized", data)
        self.assertNotIn("schedule:", data)

    def test_audio_and_captions_qa_are_different_from_release_approval(self):
        captions=doc("contracts/e01_v2_caption_qa_real_evidence_v1.json")
        self.assertEqual(captions["canonical_script_sha256"], SCRIPT)
        self.assertEqual(captions["physical_wav_sha256"], WAV)
        self.assertEqual(captions["caption_cues"], 28)
        self.assertFalse(captions["final_video_master_approved"])
        self.assertFalse(captions["publication_authorized"])
        self.assertEqual(next(x["sha256"] for x in captions["outputs"]
                         if x["filename"] == "e01-v2-karaoke-qa.ass"), ASS)


if __name__ == "__main__":
    unittest.main()
