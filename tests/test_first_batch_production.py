import copy
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from agents.content_production import ProductionError, produce as produce_plan
from agents.first_batch_production import produce, validate_batch
from editorial.review import review_script
from editorial.script_validator import validate_script_package

ROOT = Path(__file__).resolve().parents[1]


class FirstThreeScriptsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.upstream = Path(cls.temp.name)
        produce_plan(ROOT, cls.upstream)
        cls.seed = json.loads((ROOT / "agents/first_batch_seed.json").read_text(encoding="utf-8"))
        cls.plan = json.loads((cls.upstream / "operations/growth_90d.json").read_text(encoding="utf-8"))
        cls.policy = json.loads((ROOT / "contracts/new_script_source_policy.json").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_first_three_scripts_original_structure(self):
        checks = validate_batch(self.seed, self.plan, self.policy)
        self.assertEqual([x["episode_id"] for x in checks],
                         ["VNC-W01-E1", "VNC-W01-E2", "VNC-W01-E3"])
        self.assertEqual(len(set(x["original_script_sha256"] for x in checks)), 3)
        self.assertTrue(all(x["automated_review"] == "PASS_AUTOMATED_REVIEW" for x in checks))

    def test_first_three_scripts_fit_75_second_review_window(self):
        for draft in self.seed["episodes"]:
            with self.subTest(draft=draft["episode_id"]):
                self.assertEqual(validate_script_package(draft), [])
                result = review_script(draft)
                self.assertEqual(result.status, "PASS_AUTOMATED_REVIEW")
                self.assertGreaterEqual(result.estimated_seconds, 63.75)
                self.assertLessEqual(result.estimated_seconds, 86.25)

    def test_production_writes_real_hashed_markdown_and_json(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            report = produce(ROOT, out, upstream_root=self.upstream)
            self.assertEqual(report["status"], "FIRST_THREE_DRAFTS_GENERATED_REVIEW_REQUIRED")
            self.assertEqual(report["scripts_count"], 3)
            for item in report["files"]:
                blob = (out / item["path"]).read_bytes()
                self.assertEqual(hashlib.sha256(blob).hexdigest(), item["sha256"])
            self.assertTrue((out / "editorial-deliveries/first_batch_report.json").exists())

    def test_outputs_are_deterministic_and_not_approved(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            a = produce(ROOT, Path(first), upstream_root=self.upstream)
            b = produce(ROOT, Path(second), upstream_root=self.upstream)
            obj = json.loads((Path(first) / "operations/first_batch_scripts.json").read_text(encoding="utf-8"))
        self.assertEqual(a["files"], b["files"])
        self.assertEqual(obj["status"], "DRAFT_REVIEW_REQUIRED")
        self.assertEqual(obj["contextual_review_status"], "PENDING_INDEPENDENT_REVIEW")
        self.assertFalse(obj["owner_approval"])
        self.assertFalse(obj["publication_authorized"])
        self.assertTrue(all(x["status"] == "DRAFT_REVIEW_REQUIRED" for x in obj["scripts"]))

    def test_markdown_includes_all_six_blocks_and_context(self):
        with tempfile.TemporaryDirectory() as folder:
            produce(ROOT, Path(folder), upstream_root=self.upstream)
            body = (Path(folder) / "editorial-deliveries/first_batch_scripts.md").read_text(encoding="utf-8")
        for episode_id, reference in [
            ("VNC-W01-E1", "Habacuque 1:2-4"),
            ("VNC-W01-E2", "Lamentações 3:19-26"),
            ("VNC-W01-E3", "Lucas 18:1-8"),
        ]:
            self.assertIn(episode_id, body)
            self.assertIn(reference, body)
        self.assertEqual(body.count("### Narração proposta"), 3)
        self.assertEqual(body.count("### Contexto e riscos interpretativos"), 3)
        self.assertEqual(body.count("**opening**"), 3)
        self.assertIn("PENDING_INDEPENDENT_REVIEW", body)

    def test_blocks_pilot_reference_and_unmatched_plan(self):
        bad = copy.deepcopy(self.seed)
        bad["episodes"][0]["reference"] = "Salmo 13"
        with self.assertRaisesRegex(ProductionError, "plan_reference_or_title_mismatch"):
            validate_batch(bad, self.plan, self.policy)

    def test_blocks_claimed_owner_approval(self):
        bad = copy.deepcopy(self.seed)
        bad["episodes"][0]["owner_approval"] = True
        with self.assertRaisesRegex(ProductionError, "forged_approval"):
            validate_batch(bad, self.plan, self.policy)

    def test_blocks_wrong_script_source_policy(self):
        bad = copy.deepcopy(self.seed)
        bad["episodes"][1]["source_decision_ref"] = "contracts/pilot_source_decision.json"
        with self.assertRaisesRegex(ProductionError, "wrong_source_policy"):
            validate_batch(bad, self.plan, self.policy)

    def test_blocks_false_verbatim_text_approval(self):
        bad = copy.deepcopy(self.seed)
        bad["episodes"][0]["contains_verbatim_quote"] = True
        with self.assertRaisesRegex(ProductionError, "script_contract"):
            validate_batch(bad, self.plan, self.policy)

    def test_blocks_unsafe_claim_in_narration(self):
        bad = copy.deepcopy(self.seed)
        bad["episodes"][0]["blocks"][0]["text"] = "Você receberá um milagre garantido amanhã, basta assistir."
        with self.assertRaisesRegex(ProductionError, "automated_review"):
            validate_batch(bad, self.plan, self.policy)

    def test_blocks_short_incomplete_script(self):
        bad = copy.deepcopy(self.seed)
        bad["episodes"][1]["blocks"][4]["text"] = "Siga."
        with self.assertRaisesRegex(ProductionError, "automated_review|weak_block"):
            validate_batch(bad, self.plan, self.policy)

    def test_blocks_context_without_theological_review(self):
        bad = copy.deepcopy(self.seed)
        bad["episodes"][2]["biblical_context"]["theological_status"] = "APPROVED"
        with self.assertRaisesRegex(ProductionError, "weak_or_approved_theology"):
            validate_batch(bad, self.plan, self.policy)

    def test_blocks_untrusted_or_missing_source(self):
        bad = copy.deepcopy(self.seed)
        bad["episodes"][2]["research_sources"][0]["url"] = "https://random.example.org/fake-theology"
        with self.assertRaisesRegex(ProductionError, "untrusted_source_url"):
            validate_batch(bad, self.plan, self.policy)

    def test_blocks_duplicate_source_reference_link(self):
        bad = copy.deepcopy(self.seed)
        bad["episodes"][1]["research_sources"][0]["url"] = bad["episodes"][0]["research_sources"][0]["url"]
        with self.assertRaisesRegex(ProductionError, "reused_or_unexplained_source"):
            validate_batch(bad, self.plan, self.policy)

    def test_blocks_tampered_upstream_generated_plan(self):
        with tempfile.TemporaryDirectory() as folder:
            tmp = Path(folder)
            for rel in ("operations/growth_90d.json", "editorial-deliveries/production_report.json"):
                path = tmp / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(self.upstream / rel, path)
            data = json.loads((tmp / "operations/growth_90d.json").read_text(encoding="utf-8"))
            data["episodes"][0]["title_proposal"] = "TÍTULO INJETADO"
            (tmp / "operations/growth_90d.json").write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ProductionError, "upstream_plan_hash_mismatch"):
                produce(ROOT, tmp / "output", upstream_root=tmp)

    def test_missing_upstream_artifacts_fail_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ProductionError, "evidence_missing"):
                produce(ROOT, Path(folder) / "output", upstream_root=Path(folder))

    def test_output_cannot_overwrite_contracts(self):
        with self.assertRaisesRegex(ProductionError, "protected_output_directory"):
            produce(ROOT, ROOT / "contracts", upstream_root=self.upstream)


if __name__ == "__main__":
    unittest.main()
