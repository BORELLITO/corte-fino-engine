import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from agents.content_production import ProductionError, produce as produce_plan
from agents.first_batch_production import produce as produce_scripts
from agents.audio_preflight import produce as produce_preflight
from agents.e01_rights_handoff import (
    verify_dossier, render_human_review_packet, VOICE_SHA,
)
from agents.team import aggregate, CANONICAL_IDS

ROOT = Path(__file__).resolve().parents[1]


class E01RightsReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rights = json.loads((ROOT / "contracts/e01_rights_review_dossier_v1.json").read_text(encoding="utf-8"))
        cls.context = json.loads((ROOT / "contracts/e01_editorial_crosscheck_v1.json").read_text(encoding="utf-8"))
        cls.smoke = json.loads((ROOT / "contracts/kokoro_controlled_smoke_evidence_v1.json").read_text(encoding="utf-8"))
        cls.voice = json.loads((ROOT / "contracts/kokoro_voice_research_v1.json").read_text(encoding="utf-8"))
        cls.seed = json.loads((ROOT / "agents/first_batch_seed.json").read_text(encoding="utf-8"))
        cls.script = cls.seed["episodes"][0]
        cls.digest = cls.context["reviewed_canonical_narration_sha256"]

    def assess(self, dossier=None, review=None, smoke=None, voice=None, script=None, digest=None):
        return verify_dossier(
            dossier if dossier is not None else self.rights,
            review if review is not None else self.context,
            smoke if smoke is not None else self.smoke,
            voice if voice is not None else self.voice,
            script if script is not None else self.script,
            digest if digest is not None else self.digest,
        )

    def test_source_backed_conditional_licensing_not_legal_clearance(self):
        result = self.assess()
        self.assertEqual(result["status"], "REVIEW_PACKET_READY_NOT_APPROVED")
        self.assertEqual(result["source_record_count"], 6)
        self.assertEqual(result["model_upstream_license"], "Apache-2.0")
        self.assertEqual(result["onnx_upstream_license"], "Apache-2.0")
        self.assertEqual(result["site_output_permission"],
                         "COMMERCIAL_USE_CONDITIONAL_ON_ALL_RIGHTS")
        self.assertFalse(result["approved_for_audio"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["runtime_notices_reviewed"])

    def test_cache_voice_matches_real_smoke_and_upstream(self):
        result = self.assess()
        self.assertEqual(result["observed_cached_voice_sha256"], VOICE_SHA)
        self.assertEqual(result["historical_audio_test_duration_seconds"], 5.875)
        self.assertFalse(result["hosted_effective_voice_use_proven"])

    def test_rights_dossier_rejects_forged_owner_or_release_approval(self):
        for key, value in (
            ("owner_script_approval", True),
            ("approved_for_audio", True),
            ("license_cleared", True),
            ("publication_authorized", True),
            ("independent_human_biblical_review", "APPROVED"),
            ("right_to_use_all_actual_runtime_assets", "FULLY_CONFIRMED"),
        ):
            with self.subTest(key=key):
                fake = copy.deepcopy(self.rights)
                fake[key] = value
                with self.assertRaisesRegex(ProductionError, "false_clearance"):
                    self.assess(dossier=fake)

    def test_rights_dossier_rejects_model_license_forgery(self):
        fake = copy.deepcopy(self.rights)
        fake["evidence"][0]["declared_license"] = "proprietary"
        with self.assertRaisesRegex(ProductionError, "model_license"):
            self.assess(dossier=fake)

    def test_rights_dossier_rejects_untrusted_or_replaced_source(self):
        fake = copy.deepcopy(self.rights)
        fake["evidence"][3]["url"] = "https://example.invalid/terms"
        with self.assertRaisesRegex(ProductionError, "source_claim_changed:HOST"):
            self.assess(dossier=fake)

    def test_dossier_rejects_renamed_model_or_voice(self):
        fake = copy.deepcopy(self.rights)
        fake["evidence"][2]["status"] = "FULLY_CLEARED"
        with self.assertRaisesRegex(ProductionError, "source_claim_changed:VOICE"):
            self.assess(dossier=fake)

    def test_dossier_rejects_fake_voice_size_and_hash(self):
        fake = copy.deepcopy(self.rights)
        fake["cache_voice_bytes"] = 12345
        with self.assertRaisesRegex(ProductionError, "cached_voice_evidence_mismatch"):
            self.assess(dossier=fake)
        fake = copy.deepcopy(self.rights)
        fake["onnx_voice_sha256"] = "0" * 64
        with self.assertRaisesRegex(ProductionError, "cached_voice_evidence_mismatch"):
            self.assess(dossier=fake)

    def test_dossier_rejects_shrunk_manual_review_requirements(self):
        fake = copy.deepcopy(self.rights)
        fake["unresolved"] = []
        with self.assertRaisesRegex(ProductionError, "unresolved_controls_missing"):
            self.assess(dossier=fake)

    def test_human_packet_contains_exact_all_six_blocks_not_placeholder(self):
        result = self.assess()
        md = render_human_review_packet(self.script, result, self.rights, self.context)
        self.assertIn(result["script_canonical_sha256"], md)
        for block in self.script["blocks"]:
            self.assertIn(block["text"], md)
        self.assertIn("PENDENTE", md)
        self.assertIn("Apache-2.0", md)
        self.assertIn("Habacuque", md)
        self.assertNotIn("APROVADO PARA PUBLICAÇÃO", md)

    def test_human_packet_rejects_fake_owner_approval(self):
        outcome = self.assess()
        outcome["owner_script_approval"] = True
        with self.assertRaisesRegex(ProductionError, "requires_unapproved_draft"):
            render_human_review_packet(self.script, outcome, self.rights, self.context)

    def test_preflight_produces_real_hashed_review_documents_no_wav(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            produce_plan(ROOT, p)
            produce_scripts(ROOT, p, upstream_root=p)
            report = produce_preflight(ROOT, p, p)
            preflight = json.loads((p / "audio-preflight/preflight.json").read_text(encoding="utf-8"))
            rights = json.loads((p / "audio-preflight/rights_review_handoff.json").read_text(encoding="utf-8"))
            review = (p / "audio-preflight/e01_human_review_packet.md").read_text(encoding="utf-8")
            for item in report["files"]:
                raw = (p / item["path"]).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), item["sha256"])
        self.assertEqual(report["status"], "BLOCKED")
        self.assertTrue(report["rights_review_handoff_generated"])
        self.assertEqual(report["rights_review_handoff_status"],
                         "REVIEW_PACKET_READY_NOT_APPROVED")
        self.assertEqual(preflight["rights_and_editorial_handoff"]["status"],
                         "REVIEW_PACKET_READY_NOT_APPROVED")
        self.assertFalse(rights["publication_authorized"])
        self.assertIn("O diálogo continua ao longo do livro", review)
        self.assertFalse(report["audio_generated"])

    def test_wrong_draft_hash_is_rejected(self):
        bad = "0" * 64
        with self.assertRaisesRegex(ProductionError, "canonical_script_fingerprint_changed"):
            self.assess(digest=bad)


    def _prepare_coordinator_fixture(self, root):
        produce_plan(ROOT, root)
        produce_scripts(ROOT, root, upstream_root=root)
        produce_preflight(ROOT, root, root)
        out = root / "reports"
        out.mkdir(exist_ok=True)
        for name in CANONICAL_IDS:
            (out / (name + ".json")).write_text(json.dumps({
                "project": "verbo-no-chao", "agent": name,
                "publication_authorized": False, "status": "BLOCKED",
                "blockers": ["test_fixture"],
            }), encoding="utf-8")
        return out, root / "audio-preflight/report.json"

    def test_coordinator_checks_real_supporting_files_and_review_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            reports, preflight_path = self._prepare_coordinator_fixture(Path(tmp))
            result = aggregate(reports, preflight_path)
        self.assertTrue(result["audio_preflight"]["supporting_file_hashes_verified"])
        self.assertEqual(result["audio_preflight"]["supporting_file_count"], 8)
        self.assertEqual(result["audio_preflight"]["twelve_pillar_video_readiness"],
                         "BLOCKED_PHYSICAL_MEDIA_AND_RIGHTS_NOT_PROVEN")
        self.assertTrue(result["audio_preflight"]["ai_editorial_script_approved"])
        self.assertFalse(result["audio_preflight"]["owner_script_review_required"])
        self.assertEqual(len(result["audio_preflight"]["human_review_packet_sha256"]), 64)
        self.assertEqual(result["status"], "BLOCKED")

    def test_coordinator_rejects_tampered_human_review_packet(self):
        with tempfile.TemporaryDirectory() as tmp:
            reports, preflight_path = self._prepare_coordinator_fixture(Path(tmp))
            human = Path(tmp) / "audio-preflight/e01_human_review_packet.md"
            human.write_text(human.read_text(encoding="utf-8") + "\nAprovado sem revisão!\n",
                             encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "audio_preflight_artifact_hash_mismatch"):
                aggregate(reports, preflight_path)

    def test_coordinator_rejects_missing_source_handoff_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            reports, preflight_path = self._prepare_coordinator_fixture(Path(tmp))
            (Path(tmp) / "audio-preflight/rights_review_handoff.json").unlink()
            with self.assertRaisesRegex(ValueError, "audio_preflight_artifact_missing"):
                aggregate(reports, preflight_path)


if __name__ == "__main__":
    unittest.main()
