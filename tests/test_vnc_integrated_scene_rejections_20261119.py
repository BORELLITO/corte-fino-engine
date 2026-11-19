"""Cross-branch editorial rejects and spent-S01 nonce; no external calls."""
import json
import unittest
from pathlib import Path
from unittest.mock import patch
from agents import e01_source_precision_gate as gate
from agents.e01_stock_candidates import StockIntakeError

class CombinedRejectionGates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=gate.ROOT
        cls.plan=json.loads((cls.root/gate.POLICY).read_text(encoding="utf8"))

    def test_five_rejected_ids_do_not_reenter_their_scene(self):
        cases=[
            (2,40316686,"quiet-residential-street-at-dusk"),
            (2,19381590,"carousel"),
            (3,7977614,"person-using-a-quill"),
            (3,11137423,"close-up-on-writing-with-ink-pen"),
            (9,9490306,"a-woman-talking-to-her-friend-while-sitting-at-a-table")
        ]
        for index,id_,slug in cases:
            s=self.plan["scenes"][index]
            with self.subTest(scene=s["scene_id"],id=id_):
                with self.assertRaisesRegex(StockIntakeError,"editorially_rejected"):
                    gate.preflight_stock(s["scene_id"],id_,
                        "https://www.pexels.com/video/%s-%s/"%(slug,id_),
                        s["locked_search_queries_en"][0])
        self.assertEqual(gate.verify(self.root)["scene_briefs"],12)

    def test_per_scene_scoping_and_no_global_blacklist_pollution(self):
        self.assertTrue(gate.s03_rejected_for_scene(self.root,"VNC-E01V2-S03",19381590))
        self.assertFalse(gate.s03_rejected_for_scene(self.root,"VNC-E01V2-S04",19381590))
        self.assertTrue(gate.s04_rejected_for_scene(self.root,"VNC-E01V2-S04",11137423))
        self.assertFalse(gate.s04_rejected_for_scene(self.root,"VNC-E01V2-S10",11137423))
        self.assertTrue(gate.s10_rejected_for_scene(self.root,"VNC-E01V2-S10",9490306))
        self.assertFalse(gate.s10_rejected_for_scene(self.root,"VNC-E01V2-S03",9490306))
        self.assertEqual(len(gate.EXCLUDED_PEXELS),12)

    def test_mutated_sha_evidence_blocks_instead_of_silent_acceptance(self):
        original=gate.read_json
        for path in (gate.S03_LOCAL_REJECTS,gate.S04_REJECTIONS):
            def bad_read(root,requested,ledger=path):
                obj=original(root,requested)
                if requested==ledger:
                    obj=json.loads(json.dumps(obj))
                    if ledger==gate.S03_LOCAL_REJECTS:
                        obj["decisions"][1]["source_sha256"]="f"*64
                    else:
                        obj["evidence"][0]["source_sha256"]="f"*64
                return obj
            with self.subTest(path=str(path)):
                with patch.object(gate,"read_json",side_effect=bad_read):
                    with self.assertRaisesRegex(StockIntakeError,"source_hash_changed"):
                        if path==gate.S03_LOCAL_REJECTS:
                            gate.s03_rejected_for_scene(self.root,"VNC-E01V2-S03",19381590)
                        else:
                            gate.s04_rejected_for_scene(self.root,"VNC-E01V2-S04",7977614)

    def test_all_ledgers_deny_publication_and_scene_release(self):
        for path in (gate.S03_LOCAL_REJECTS,gate.S04_REJECTIONS,gate.S10_REJECTIONS):
            d=gate.read_json(self.root,path)
            self.assertFalse(d["publication_authorized"])
            self.assertEqual(d["episode_id"],"VNC-W01-E1")
        for path in (gate.S04_REJECTIONS,gate.S10_REJECTIONS):
            self.assertFalse(gate.read_json(self.root,path)["allowed_in_master"])

    def test_new_unrejected_sources_remain_research_only(self):
        for index,video in ((2,99999931),(3,99999941),(9,99999951)):
            s=self.plan["scenes"][index]
            r=gate.preflight_stock(s["scene_id"],video,
                "https://www.pexels.com/video/other-source-%d/"%video,
                s["locked_search_queries_en"][0])
            self.assertEqual(r["status"],"ELIGIBLE_FOR_PHYSICAL_MEDIA_REVIEW_ONLY")
            self.assertFalse(r["actual_video_frames_reviewed"])
            self.assertFalse(r["publication_authorized"])

    def test_consumed_s01_cannot_be_manually_replayed(self):
        w=(self.root/".github/workflows/verbo-no-chao-e01-s01-v2-probe.yml").read_text(encoding="utf8")
        for required in ("git diff-tree","git rev-list --count","github.event_name == 'push'","persist-credentials: false"):
            self.assertIn(required,w)
        self.assertNotIn("workflow_dispatch:",w)
        nonce=gate.read_json(self.root,Path("contracts/e01_ltx23_s01_one_shot_trigger_20261118.json"))
        self.assertIs(nonce["publication_authorized"],False)

if __name__=="__main__":
    unittest.main()
