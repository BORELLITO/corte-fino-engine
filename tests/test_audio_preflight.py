import copy
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from agents.content_production import ProductionError, produce as editorial
from agents.first_batch_production import produce as scripts
from agents.audio_preflight import produce, validate_voice_evidence, validate_input
from agents.team import aggregate, CANONICAL_IDS
from agents.e01_context_review import validate_context_crosscheck

ROOT = Path(__file__).resolve().parents[1]


class AudioPreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.upstream = Path(cls.tmp.name)
        editorial(ROOT, cls.upstream)
        scripts(ROOT, cls.upstream, upstream_root=cls.upstream)
        cls.voice = json.loads((ROOT / "contracts/kokoro_voice_research_v1.json").read_text(encoding="utf-8"))
        cls.package = json.loads((cls.upstream / "operations/first_batch_scripts.json").read_text(encoding="utf-8"))
        cls.report = json.loads((cls.upstream / "editorial-deliveries/first_batch_report.json").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_canonical_voice_provenance_verifies_without_rights_promotion(self):
        validate_voice_evidence(self.voice)
        self.assertEqual(self.voice["model_license"], "Apache-2.0")
        self.assertEqual(self.voice["upstream_voice_name"], "pm_alex")
        self.assertFalse(self.voice["voice_pack_bytes_verified"])
        self.assertEqual(self.voice["upstream_voice_pack_full_sha256"], "cf0ba8c573c2480fc54123683a35cf1e2ae130428e441eb91f9149bdb188a526")
        self.assertTrue(self.voice["runtime_terms_checked"])
        self.assertFalse(self.voice["hosted_voice_pack_bytes_verified"])

    def test_preflight_generates_real_hashed_report_but_no_audio(self):
        with tempfile.TemporaryDirectory() as folder:
            result = produce(ROOT, self.upstream, Path(folder))
            self.assertEqual(result["status"], "BLOCKED")
            self.assertFalse(result["audio_generated"])
            self.assertFalse(result["publication_authorized"])
            for file in result["files"]:
                bytes_ = (Path(folder) / file["path"]).read_bytes()
                self.assertEqual(hashlib.sha256(bytes_).hexdigest(), file["sha256"])
            payload = json.loads((Path(folder) / "audio-preflight/preflight.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["stage"], "AUDIO_PREFLIGHT_ONLY")
        self.assertIsNone(payload["narration"]["audio_file"])
        self.assertEqual(len(payload["narration"]["segments"]), 6)
        self.assertEqual(payload["internal_editorial_source_crosscheck"]["status"], "INTERNAL_CONTEXT_CROSSCHECK_PASS_WITH_CAVEATS")
        self.assertTrue(result["internal_context_crosscheck_completed"])
        self.assertTrue(result["human_theological_review_pending"])

    def test_reproduction_deterministic(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            first = produce(ROOT, self.upstream, Path(a))
            second = produce(ROOT, self.upstream, Path(b))
        self.assertEqual(first["files"], second["files"])

    def test_narration_safely_pins_exact_text_hash(self):
        payload = validate_input(self.package, self.report, self.voice)
        self.assertEqual(len(payload["narration_sha256"]), 64)
        bad = copy.deepcopy(self.package)
        bad["scripts"][0]["blocks"][0]["text"] += " Exemplo adicional."
        with self.assertRaisesRegex(ProductionError, "canonical_narration_hash_mismatch"):
            validate_input(bad, self.report, self.voice)

    def test_approval_claim_rejected(self):
        for claim in ("owner_approval", "publication_authorized"):
            with self.subTest(claim=claim):
                bad = copy.deepcopy(self.package)
                bad["scripts"][0][claim] = True
                with self.assertRaisesRegex(ProductionError, "approval_or_source_changed"):
                    validate_input(bad, self.report, self.voice)

    def test_voice_license_claim_cannot_upgrade_itself(self):
        bad = copy.deepcopy(self.voice)
        bad["voice_pack_commercial_rights_status"] = "CLEARED"
        with self.assertRaisesRegex(ProductionError, "unsupported_license_or_hash_claim"):
            validate_voice_evidence(bad)
        bad = copy.deepcopy(self.voice)
        bad["upstream_voice_pack_full_sha256"] = "f" * 64
        with self.assertRaisesRegex(ProductionError, "unsupported_license_or_hash_claim"):
            validate_voice_evidence(bad)
        bad = copy.deepcopy(self.voice)
        bad["runtime_terms_checked"] = False
        with self.assertRaisesRegex(ProductionError, "runtime_license_not_verified"):
            validate_voice_evidence(bad)

    def test_upstream_package_tampering_detected(self):
        with tempfile.TemporaryDirectory() as folder:
            up = Path(folder)
            (up / "operations").mkdir()
            (up / "editorial-deliveries").mkdir()
            for rel in ("operations/first_batch_scripts.json",
                        "editorial-deliveries/first_batch_report.json"):
                shutil.copy2(self.upstream / rel, up / rel)
            bad = json.loads((up / "operations/first_batch_scripts.json").read_text(encoding="utf-8"))
            bad["scripts"][0]["title_proposal"] = "FRAUDE NO ROTEIRO"
            (up / "operations/first_batch_scripts.json").write_text(json.dumps(bad), encoding="utf-8")
            with self.assertRaisesRegex(ProductionError, "script_package_sha256_mismatch"):
                produce(ROOT, up, up)

    def test_missing_upstream_denied(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ProductionError, "evidence_missing"):
                produce(ROOT, Path(folder), Path(folder))

    def test_protected_repository_paths_denied(self):
        with self.assertRaisesRegex(ProductionError, "protected_output_directory"):
            produce(ROOT, self.upstream, ROOT / "contracts")

    def test_research_url_cannot_silently_switch_to_other_host(self):
        bad = copy.deepcopy(self.voice)
        bad["official_voice_registry"] = "https://random-site.invalid/voice-license"
        with self.assertRaisesRegex(ProductionError, "untrusted_url"):
            validate_voice_evidence(bad)


    def test_team_coordinator_explicitly_includes_audio_blockers(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            reports = root / "reports"
            reports.mkdir()
            for name in CANONICAL_IDS:
                (reports / f"{name}.json").write_text(json.dumps({
                    "agent": name, "project": "verbo-no-chao", "publication_authorized": False,
                    "status": "BLOCKED", "blockers": ["test_fixture"],
                }), encoding="utf-8")
            produce(ROOT, self.upstream, root)
            combined = aggregate(reports, root / "audio-preflight/report.json")
        self.assertEqual(combined["agents_executed"], 8)
        self.assertEqual(combined["audio_preflight"]["status"], "BLOCKED")
        self.assertFalse(combined["audio_preflight"]["voice_license_approved"])
        self.assertIn("hosted_inference_voice_asset_consumption_unverified",
                      combined["audio_preflight"]["blockers"])
        self.assertEqual(combined["status"], "BLOCKED")

    def test_team_rejects_forged_audio_license_clearance(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            reports = root / "reports"
            reports.mkdir()
            for name in CANONICAL_IDS:
                (reports / f"{name}.json").write_text(json.dumps({
                    "agent": name, "project": "verbo-no-chao", "publication_authorized": False,
                    "status": "BLOCKED", "blockers": ["test_fixture"],
                }), encoding="utf-8")
            produce(ROOT, self.upstream, root)
            audio_path = root / "audio-preflight/report.json"
            forged = json.loads(audio_path.read_text(encoding="utf-8"))
            forged["voice_license_approved"] = True
            audio_path.write_text(json.dumps(forged), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "audio_preflight_failed_closed_contract"):
                aggregate(reports, audio_path)


    def test_editorial_crosscheck_binds_all_original_blocks(self):
        review = json.loads((ROOT / "contracts/e01_editorial_crosscheck_v1.json").read_text(encoding="utf-8"))
        fingerprint = self.package["automated_checks"][0]["original_script_sha256"]
        result = validate_context_crosscheck(review, self.package["scripts"][0], fingerprint)
        self.assertEqual(result["status"], "INTERNAL_CONTEXT_CROSSCHECK_PASS_WITH_CAVEATS")
        self.assertEqual(len(result["claims_checked"]), 3)
        self.assertEqual(result["independent_human_theological_review"], "PENDING")
        self.assertFalse(result["approved_for_audio"])

    def test_crosscheck_rejects_changed_script(self):
        review = json.loads((ROOT / "contracts/e01_editorial_crosscheck_v1.json").read_text(encoding="utf-8"))
        fingerprint = self.package["automated_checks"][0]["original_script_sha256"]
        tampered = copy.deepcopy(self.package["scripts"][0])
        tampered["blocks"][2]["text"] += " Acrescentei algo."
        with self.assertRaisesRegex(ProductionError, "review_does_not_match_exact_block_bytes"):
            validate_context_crosscheck(review, tampered, fingerprint)

    def test_crosscheck_rejects_forged_human_approval(self):
        review = json.loads((ROOT / "contracts/e01_editorial_crosscheck_v1.json").read_text(encoding="utf-8"))
        fingerprint = self.package["automated_checks"][0]["original_script_sha256"]
        review["independent_human_theological_review"] = "APPROVED"
        with self.assertRaisesRegex(ProductionError, "false_approval_or_bad_scope"):
            validate_context_crosscheck(review, self.package["scripts"][0], fingerprint)

    def test_crosscheck_rejects_fake_sources(self):
        review = json.loads((ROOT / "contracts/e01_editorial_crosscheck_v1.json").read_text(encoding="utf-8"))
        fingerprint = self.package["automated_checks"][0]["original_script_sha256"]
        review["reviewed_sources"][1]["url"] = "https://fake.test/reference"
        with self.assertRaisesRegex(ProductionError, "source_urls_changed"):
            validate_context_crosscheck(review, self.package["scripts"][0], fingerprint)

    def test_host_sha_metadata_does_not_count_as_downloaded_bytes(self):
        bad = copy.deepcopy(self.voice)
        bad["hosted_voice_pack_bytes_verified"] = True
        with self.assertRaisesRegex(ProductionError, "unsupported_license_or_hash_claim"):
            validate_voice_evidence(bad)
        bad = copy.deepcopy(self.voice)
        bad["hosted_voice_pack_sha256"] = bad["upstream_voice_pack_full_sha256"]
        with self.assertRaisesRegex(ProductionError, "unsupported_license_or_hash_claim"):
            validate_voice_evidence(bad)

    def test_coordinator_rejects_human_review_inflation(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            reports = root / "reports"
            reports.mkdir()
            for name in CANONICAL_IDS:
                (reports / f"{name}.json").write_text(json.dumps({
                    "agent": name, "project": "verbo-no-chao", "publication_authorized": False,
                    "status": "BLOCKED", "blockers": ["test_fixture"],
                }), encoding="utf-8")
            produce(ROOT, self.upstream, root)
            path = root / "audio-preflight/report.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["human_theological_review_pending"] = False
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "audio_preflight_failed_closed_contract"):
                aggregate(reports, path)


if __name__ == "__main__":
    unittest.main()
