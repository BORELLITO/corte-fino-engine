import copy
import json
import tempfile
import unittest
from pathlib import Path

from agents.content_production import ProductionError, produce as produce_plan
from agents.first_batch_production import produce as produce_scripts
from agents.audio_preflight import produce as produce_preflight
from agents.autonomous_editorial_gate import verify_ai_editorial_review
from agents.video_pillar_readiness import (
    video_pillar_readiness, validate_video_pillar_report, BLOCKERS,
)

ROOT = Path(__file__).resolve().parents[1]


class VideoPillarReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load = lambda f: json.loads((ROOT / f).read_text(encoding="utf-8"))
        cls.policy = load("contracts/autonomous_editorial_policy_v1.json")
        cls.workflow = load("contracts/video_workflow_policy.json")
        cls.review = load("contracts/e01_ai_editorial_review_v1.json")
        cls.draft = load("agents/first_batch_seed.json")["episodes"][0]
        cls.approval = verify_ai_editorial_review(cls.policy, cls.review, cls.draft)

    def make(self, policy=None, workflow=None, approval=None):
        return video_pillar_readiness(
            policy if policy is not None else self.policy,
            workflow if workflow is not None else self.workflow,
            approval if approval is not None else self.approval,
        )

    def test_eight_script_pillars_pass_four_media_pending(self):
        r = self.make()
        validate_video_pillar_report(r)
        self.assertEqual(len(r["pillars"]), 12)
        self.assertEqual(r["script_pillars_with_versioned_ai_review"], 8)
        self.assertEqual(r["media_pillars_with_actual_proof"], 0)
        self.assertTrue(all(x["status"] == "PASS_VERSIONED_AI_SCRIPT_REVIEW_ONLY" for x in r["pillars"][:8]))
        self.assertTrue(all(x["status"] == "BLOCKED_PHYSICAL_QA_PENDING" for x in r["pillars"][8:]))

    def test_no_owner_script_or_finished_video_review_required(self):
        r = self.make()
        self.assertFalse(r["owner_script_review_required"])
        self.assertFalse(r["owner_finished_video_review_required"])
        self.assertTrue(r["separate_explicit_publication_authorization_required"])
        self.assertFalse(r["publication_authorized"])

    def test_unapproved_script_never_passes_video_scoreboard(self):
        bad = copy.deepcopy(self.approval)
        bad["status"] = "DRAFT"
        with self.assertRaisesRegex(ProductionError, "script_not_genuinely_reviewed"):
            self.make(approval=bad)

    def test_missing_video_pillar_never_passes(self):
        bad = copy.deepcopy(self.policy)
        bad["pillars"].pop()
        with self.assertRaisesRegex(ProductionError, "missing_12_pillars"):
            self.make(policy=bad)

    def test_auto_publication_without_permission_denied(self):
        bad = copy.deepcopy(self.workflow)
        bad["publication_authorized_by_default"] = True
        with self.assertRaisesRegex(ProductionError, "publication_boundary_missing"):
            self.make(workflow=bad)

    def test_removing_manual_publication_action_denied(self):
        bad = copy.deepcopy(self.workflow)
        bad["workflow"] = [x for x in bad["workflow"] if
                           x["state"] != "AWAIT_SEPARATE_PUBLICATION_PERMISSION"]
        with self.assertRaisesRegex(ProductionError, "publication_boundary_missing"):
            self.make(workflow=bad)

    def test_forged_media_rights_caption_and_master_denied(self):
        for key in ("media_pillars_with_actual_proof", "ready_for_publication_authorization",
                    "all_rights_cleared", "decoded_final_master_verified",
                    "full_video_production_completed", "publication_authorized"):
            with self.subTest(key=key):
                bad = self.make()
                bad[key] = True if key != "media_pillars_with_actual_proof" else 4
                with self.assertRaisesRegex(ProductionError, "false_video_approval"):
                    validate_video_pillar_report(bad)

    def test_forged_visuals_music_captions_or_metadata_denied(self):
        for i in range(8, 12):
            bad = self.make()
            bad["pillars"][i]["status"] = "PASS"
            with self.subTest(i=i):
                with self.assertRaisesRegex(ProductionError, "media_claims_inflated"):
                    validate_video_pillar_report(bad)

    def test_breakdown_blockers_are_explicit_non_decorative(self):
        r = self.make()
        self.assertEqual(tuple(r["blocking_reasons"]), BLOCKERS)
        self.assertTrue(all(x["blocker"] in BLOCKERS for x in r["pillars"][8:]))

    def test_production_preflight_emits_video_readiness_real_json(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            produce_plan(ROOT, path)
            produce_scripts(ROOT, path, upstream_root=path)
            result = produce_preflight(ROOT, path, path)
            data = json.loads((path / "audio-preflight/video_pillar_readiness.json").read_text(encoding="utf-8"))
            validate_video_pillar_report(data)
            self.assertTrue((path / "audio-preflight/ai_editorial_approval.json").is_file())
            self.assertTrue(any(x["path"] == "audio-preflight/video_pillar_readiness.json" for x in result["files"]))
        self.assertFalse(data["full_video_production_completed"])
        self.assertFalse(result["publication_authorized"])


if __name__ == "__main__":
    unittest.main()
