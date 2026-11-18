import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "contracts/e01_v2_12_scene_visual_plan_v1.json"


class E01V2StoryboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=json.loads(PLAN.read_text(encoding="utf-8"))

    def test_all_12_scenes_cover_exactly_real_audio_no_gaps(self):
        scenes=self.doc["scenes"]
        self.assertEqual(len(scenes),12)
        self.assertEqual(scenes[0]["start_seconds"],0)
        self.assertEqual(scenes[-1]["end_seconds"],70.425)
        self.assertTrue(all(s["end_seconds"]>s["start_seconds"] for s in scenes))
        self.assertTrue(all(abs(scenes[i]["end_seconds"]-scenes[i+1]["start_seconds"])<0.001
                            for i in range(len(scenes)-1)))

    def test_script_and_real_wav_hash_are_immutable(self):
        self.assertEqual(self.doc["script_sha256"],
                         "c64b57cb9d6529b60b9e80ab7607e5887f909dd00e14cd80ed9ec2b7474a5dc6")
        self.assertEqual(self.doc["audio_sha256"],
                         "4f2ee1ff0171ddedb7c64e0dce2300c53a0ef105ef12d643a7af6b0a4621942e")

    def test_exact_cue_assignments_cover_28_captions_no_overlap(self):
        cues=[n for s in self.doc["scenes"] for n in s["caption_cues"]]
        self.assertEqual(sorted(cues),list(range(1,29)))
        self.assertEqual(len(set(cues)),28)

    def test_scene_assets_are_missing_not_fake_approved(self):
        for scene in self.doc["scenes"]:
            with self.subTest(scene=scene["id"]):
                self.assertIsNone(scene["asset_sha256"])
                self.assertIsNone(scene["asset_file"])
                self.assertFalse(scene["generated"])
                self.assertFalse(scene["approved_for_export"])
                self.assertEqual(scene["rights"],"PENDING")
        self.assertFalse(self.doc["visual_assets_generated"])
        self.assertFalse(self.doc["visual_license_audit_completed"])
        self.assertFalse(self.doc["master_rendered"])
        self.assertFalse(self.doc["publication_authorized"])

    def test_all_shots_have_physical_production_direction_and_religious_guard(self):
        scenes=self.doc["scenes"]
        self.assertEqual(self.doc["canvas"],{"width":1080,"height":1920,"fps":30,"aspect_ratio":"9:16"})
        self.assertTrue(self.doc["design"]["no_biblical_false_claims"])
        self.assertTrue(self.doc["design"]["no_graphics"])
        self.assertTrue(all(len(x["visual_prompt"])>220
                            and "no text" in x["visual_prompt"]
                            and x["camera_motion"]
                            and x["editorial_intent"] for x in scenes))
        self.assertTrue(all(x["media_source"]=="TO_BE_CREATED_OR_LICENSED" for x in scenes))


if __name__=="__main__":
    unittest.main()
