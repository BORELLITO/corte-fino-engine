import copy
import json
import tempfile
import unittest
from pathlib import Path

from agents.content_production import ProductionError, produce as produce_plan
from agents.first_batch_production import produce as produce_scripts
from agents.audio_preflight import produce as preflight
from agents.autonomous_editorial_gate import verify_ai_editorial_review, canonical_sha

ROOT = Path(__file__).resolve().parents[1]


class AutonomousEditorialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = json.loads((ROOT / "contracts/autonomous_editorial_policy_v1.json").read_text(encoding="utf-8"))
        cls.review = json.loads((ROOT / "contracts/e01_ai_editorial_review_v1.json").read_text(encoding="utf-8"))
        cls.seed = json.loads((ROOT / "agents/first_batch_seed.json").read_text(encoding="utf-8"))
        cls.draft = cls.seed["episodes"][0]

    def test_real_e01_ai_review_approves_internal_script_only(self):
        r = verify_ai_editorial_review(self.policy, self.review, self.draft)
        self.assertEqual(r["status"], "AUTO_APPROVED_FOR_INTERNAL_PRODUCTION")
        self.assertEqual(r["mandatory_pillars_passed"], 8)
        self.assertEqual(r["script_sha256"], canonical_sha(self.draft))
        self.assertFalse(r["owner_script_review_required"])
        self.assertFalse(r["final_video_owner_approval_required"])
        self.assertTrue(r["internal_final_video_qa_required"])
        self.assertTrue(r["owner_final_video_review_optional"])
        self.assertFalse(r["voice_audio_generation_authorized"])
        self.assertFalse(r["publication_authorized"])

    def test_eight_script_and_four_video_pillars_are_preserved(self):
        self.assertEqual(len(self.policy["pillars"]), 12)
        self.assertEqual(sum(x["required_for_script"] for x in self.policy["pillars"]), 8)
        self.assertEqual(sum(not x["required_for_script"] for x in self.policy["pillars"]), 4)

    def test_reviewer_is_neither_human_nor_independent_second_model(self):
        out = verify_ai_editorial_review(self.policy, self.review, self.draft)
        self.assertEqual(out["reviewer_kind"], "AI_ASSISTANT_NOT_HUMAN_NOT_REEXECUTED_BY_CI")
        self.assertFalse(out["human_theological_endorsement"])
        self.assertFalse(self.review["review_externally_reexecuted_in_ci"])

    def test_script_revision_invalidates_pinned_ai_review(self):
        edited = copy.deepcopy(self.draft)
        edited["blocks"][3]["text"] += " Deus vai resolver amanhã."
        with self.assertRaisesRegex(ProductionError, "untrusted_semantic_review_or_digest"):
            verify_ai_editorial_review(self.policy, self.review, edited)

    def test_biblical_reference_forgery_rejected(self):
        fake = copy.deepcopy(self.review)
        fake["reference"] = "João 3:16"
        with self.assertRaisesRegex(ProductionError, "untrusted_semantic_review_or_digest"):
            verify_ai_editorial_review(self.policy, fake, self.draft)

    def test_fake_human_theologian_claim_denied(self):
        fake = copy.deepcopy(self.review)
        fake["review_independent_human"] = True
        with self.assertRaisesRegex(ProductionError, "untrusted_semantic_review_or_digest"):
            verify_ai_editorial_review(self.policy, fake, self.draft)

    def test_fake_publication_rights_or_audio_release_denied(self):
        for key in ("production_wav_rights_cleared", "visual_assets_cleared",
                    "music_license_cleared", "captions_synced", "physical_master_verified",
                    "monetization_cleared", "final_video_owner_approval",
                    "publication_authorized"):
            with self.subTest(key=key):
                f = copy.deepcopy(self.review)
                f[key] = True
                with self.assertRaisesRegex(ProductionError, "forged_media_or_release_clearance"):
                    verify_ai_editorial_review(self.policy, f, self.draft)

    def test_no_semantic_report_never_generates_approval(self):
        with self.assertRaises(ProductionError):
            verify_ai_editorial_review(self.policy, None, self.draft)

    def test_missing_required_pillar_denies(self):
        bad = copy.deepcopy(self.review)
        bad["pillars"].pop()
        with self.assertRaisesRegex(ProductionError, "missing_ai_review_pillars"):
            verify_ai_editorial_review(self.policy, bad, self.draft)

    def test_unanchored_reviewer_claim_denied(self):
        bad = copy.deepcopy(self.review)
        bad["pillars"][0]["script_anchor"] = "Essa frase não existe no roteiro"
        with self.assertRaisesRegex(ProductionError, "unanchored_or_failed_pillar"):
            verify_ai_editorial_review(self.policy, bad, self.draft)

    def test_fake_source_or_single_source_denied(self):
        bad = copy.deepcopy(self.review)
        bad["script_reviewed_sources"] = ["https://untrusted.example/bible"]
        with self.assertRaisesRegex(ProductionError, "source_evidence_missing"):
            verify_ai_editorial_review(self.policy, bad, self.draft)

    def test_critical_finding_denies_automatic_approval(self):
        bad = copy.deepcopy(self.review)
        bad["critical_findings"] = ["Unverified miracle promise"]
        with self.assertRaisesRegex(ProductionError, "unsafe_or_unsupported_approval"):
            verify_ai_editorial_review(self.policy, bad, self.draft)

    def test_policy_cannot_auto_publish_or_retroactively_approve_pilot(self):
        for key, value in (("publication_authorized", True),
                           ("owner_final_video_approval_required", True),
                           ("internal_final_video_qa_required", False),
                           ("protected_pilot_can_be_retroactively_auto_approved", True)):
            bad = copy.deepcopy(self.policy)
            bad[key] = value
            with self.assertRaisesRegex(ProductionError, "policy_contract_changed"):
                verify_ai_editorial_review(bad, self.review, self.draft)

    def test_preflight_reports_script_approved_rights_and_media_blocked(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)
            produce_plan(ROOT, p)
            produce_scripts(ROOT, p, upstream_root=p)
            result = preflight(ROOT, p, p)
            primary = json.loads((p / "audio-preflight/preflight.json").read_text(encoding="utf-8"))
            verified = json.loads((p / "audio-preflight/ai_editorial_approval.json").read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(result["ai_editorial_script_approved"])
        self.assertFalse(result["owner_script_review_required"])
        self.assertNotIn("script_owner_approval_pending", result["blockers"])
        self.assertNotIn("independent_biblical_review_pending", result["blockers"])
        self.assertIn("exact_voice_pack_commercial_rights_pending", result["blockers"])
        self.assertEqual(primary["script_review_status"], "AUTO_APPROVED_FOR_INTERNAL_PRODUCTION")
        self.assertEqual(verified["mandatory_pillars_passed"], 8)
        self.assertFalse(result["audio_generated"])

    def test_pilot_is_not_part_of_e01_approval(self):
        wrong = copy.deepcopy(self.draft)
        wrong["episode_id"] = "SALMO13"
        with self.assertRaisesRegex(ProductionError, "wrong_or_unapproved_script"):
            verify_ai_editorial_review(self.policy, self.review, wrong)


if __name__ == "__main__":
    unittest.main()
