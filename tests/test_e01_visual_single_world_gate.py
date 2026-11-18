"""E01 world-continuity plan never confuses a shot list with actual film."""
import copy
import json
import unittest
from agents.e01_visual_single_world_gate import ROOT,CONTRACT,validate
from agents.e01_stock_candidates import StockIntakeError

class TestE01VisualSingleWorld(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=json.loads((ROOT/CONTRACT).read_text(encoding="utf-8"))
    def changed(self,mutate):
        copy_plan=copy.deepcopy(self.original);mutate(copy_plan);return copy_plan
    def fail(self,modify):
        with self.assertRaises(StockIntakeError):
            validate(ROOT,self.changed(modify))
    def test_one_world_shoot_plan_matches_all_28_cues(self):
        outcome=validate(ROOT)
        self.assertEqual(outcome["scene_count"],12)
        self.assertEqual(outcome["same_world_scene_count"],8)
        self.assertEqual(outcome["caption_cues"],28)
        self.assertEqual(outcome["physically_verified_assets"],0)
        self.assertFalse(outcome["publication_authorized"])
    def test_no_fake_publish_rights_or_master(self):
        for key,value in (("source_assets_verified_for_this_plan",1),
                          ("license_all_cleared",True),
                          ("master_1080x1920_rendered",True),
                          ("publication_authorized",True),
                          ("status","READY_FOR_PUBLICATION_AUTHORIZATION")):
            with self.subTest(key=key):
                self.fail(lambda d:d.update({key:value}))
    def test_unverified_footage_cannot_be_declared_real(self):
        changes=[("source_asset_id","fake_id"),("source_file_sha256","a"*64),
                 ("asset_state","READY"),("license_status","CLEARED"),
                 ("actual_frame_review",True),("same_person_verified",True),
                 ("real_motion_verified",True),("safe_zone_verified",True),
                 ("allowed_in_master",True)]
        for key,value in changes:
            with self.subTest(key=key):
                self.fail(lambda d:d["scenes"][0].update({key:value}))
    def test_script_audio_timeline_cannot_drift(self):
        for k,v in (("script_sha256","f"*64),("audio_sha256","0"*64)):
            self.fail(lambda d:d.update({k:v}))
        self.fail(lambda d:d["scenes"][3].update(start_seconds=19))
        self.fail(lambda d:d["scenes"][9].update(caption_cues=[23]))
        self.fail(lambda d:d["scenes"].pop())
        self.fail(lambda d:d["scenes"][1].update(shot_id="VNC-E01V2-S01"))
    def test_continuity_anchors_and_stock_history_are_locked(self):
        self.fail(lambda d:d["scenes"][8].update(continuity_group="BIBLICAL_SYMBOL_C"))
        self.fail(lambda d:d["scenes"][8].update(preferred_acquisition="SYMBOLIC_REAL_FOOTAGE"))
        self.fail(lambda d:d["global_continuity"].update(safe_zone_bottom_px=0))
        self.fail(lambda d:d["prior_rejections"].clear())
    def test_visual_research_cannot_drop_hard_negative_filters(self):
        self.fail(lambda d:d["scenes"][2].update(hard_reject_if=[]))
        self.fail(lambda d:d["scenes"][2].update(verified_real_footage_search_en=[]))
        self.fail(lambda d:d["scenes"][8].update(visual_action_pt=""))
if __name__=="__main__":
    unittest.main()
