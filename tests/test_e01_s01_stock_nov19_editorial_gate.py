"""Regression: a visually rejected scene cannot be promoted from free stock."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from agents import e01_s01_stock_nov19_editorial_gate as gate


class TestNov19EditorialGate(unittest.TestCase):
    def test_current_real_video_review_not_a_master(self):
        res = gate.verify()
        self.assertEqual(res["verified_original_source_files"], 3)
        self.assertEqual(res["style_reference_only_video_id"], 32788087)
        self.assertFalse(res["scene_media_ready"])
        self.assertFalse(res["publication_authorized"])

    def test_forged_scene_asset_or_publication_fails(self):
        original = json.loads((gate.ROOT / gate.CONTRACT).read_text(encoding="utf8"))
        altered = []
        def change(field,value):
            obj=copy.deepcopy(original);obj[field]=value;return obj
        altered.extend([change("footage_approved_for_s01", 1),
                        change("source_rights_cleared", True),
                        change("full_video_playback_reviewed", True),
                        change("publication_authorized", True)])
        a=copy.deepcopy(original);a["decisions"][1]["scene_approved"]=True;altered.append(a)
        a=copy.deepcopy(original);a["decisions"][1]["editorial_decision"]="APPROVED";altered.append(a)
        a=copy.deepcopy(original);a["decisions"][2]["can_publish"]=True;altered.append(a)
        for ix,doc in enumerate(altered):
            with self.subTest(ix=ix), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                contract = root / gate.CONTRACT
                contract.parent.mkdir(parents=True)
                contract.write_text(json.dumps(doc),encoding="utf8")
                real_story = gate.ROOT / "contracts/e01_v2_12_scene_visual_plan_v1.json"
                (root/"contracts/e01_v2_12_scene_visual_plan_v1.json").write_bytes(real_story.read_bytes())
                with self.assertRaises(ValueError):
                    gate.verify(root)


if __name__ == "__main__":
    unittest.main()
