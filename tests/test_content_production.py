import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from agents.content_production import ProductionError, produce, validate_seed

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "agents" / "editorial_seed.json"


class EditorialProductionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seed = json.loads(SEED.read_text(encoding="utf-8"))

    def test_seed_has_original_39_ideas_and_approved_positioning(self):
        validate_seed(self.seed)
        self.assertEqual(self.seed["approval_scope"]["name"]["value"], "VERBO NO CHÃO")
        self.assertEqual(len(self.seed["proposal"]["weeks"]), 13)
        self.assertEqual(sum(len(w["ideas"]) for w in self.seed["proposal"]["weeks"]), 39)

    def test_producer_generates_four_real_outputs_plus_report(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            result = produce(ROOT, out)
            self.assertEqual(result["status"], "DELIVERABLES_GENERATED_REVIEW_REQUIRED")
            self.assertEqual(result["ideas_count"], 39)
            self.assertEqual(len(result["files"]), 4)
            for item in result["files"]:
                path = out / item["path"]
                self.assertTrue(path.is_file())
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), item["sha256"])
            self.assertTrue((out / "editorial-deliveries" / "production_report.json").exists())

    def test_produced_files_are_deterministic(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            a, b = produce(ROOT, Path(first)), produce(ROOT, Path(second))
        self.assertEqual(a["files"], b["files"])
        self.assertEqual(a["source_evidence_sha256"], b["source_evidence_sha256"])

    def test_real_plan_covers_90_days_with_39_unique_references(self):
        with tempfile.TemporaryDirectory() as folder:
            produce(ROOT, Path(folder))
            plan = json.loads((Path(folder) / "operations/growth_90d.json").read_text(encoding="utf-8"))
        days = [x["relative_day"] for x in plan["episodes"]]
        refs = [x["scripture_reference"] for x in plan["episodes"]]
        self.assertEqual(len(days), 39)
        self.assertEqual(len(set(days)), 39)
        self.assertEqual(len(set(refs)), 39)
        self.assertEqual(min(days), 1)
        self.assertEqual(max(days), 90)
        self.assertNotIn("Salmo 13", refs)
        self.assertEqual(plan["start_date"], "NOT_SCHEDULED")
        self.assertEqual(plan["window_days"], 90)
        self.assertEqual([x["day"] for x in plan["milestones"]], [30, 60, 90])

    def test_plan_never_claims_approval_or_publication(self):
        with tempfile.TemporaryDirectory() as folder:
            produce(ROOT, Path(folder))
            strategy = json.loads((Path(folder) / "operations/niche_strategy.json").read_text(encoding="utf-8"))
            plan = json.loads((Path(folder) / "operations/growth_90d.json").read_text(encoding="utf-8"))
        for item in (strategy, plan):
            self.assertEqual(item["approval_status"], "DRAFT_REVIEW_REQUIRED")
            self.assertFalse(item["publication_authorized"])
            self.assertFalse(item["owner_approval"])
        self.assertEqual(plan["cadence"]["status"], "HYPOTHESIS_NOT_APPROVED")
        self.assertFalse(plan["cadence"]["publish_automatically"])
        self.assertTrue(all(x["script_status"] == "IDEA_ONLY_REQUIRES_CONTEXT_AND_SCRIPT_REVIEW"
                            and x["rights_status"] == "NOT_REVIEWED"
                            and x["publication_authorized"] is False for x in plan["episodes"]))

    def test_produced_markdown_contains_full_useful_content(self):
        with tempfile.TemporaryDirectory() as folder:
            produce(ROOT, Path(folder))
            strategy = (Path(folder) / "editorial-deliveries/editorial_strategy.md").read_text(encoding="utf-8")
            plan = (Path(folder) / "editorial-deliveries/90_day_plan.md").read_text(encoding="utf-8")
        self.assertIn("Bíblia", strategy)
        self.assertIn("Promessa", strategy)
        self.assertEqual(plan.count("Gancho:"), 39)
        self.assertIn("Semana 13", plan)
        self.assertIn("Dia 90:", plan)
        self.assertIn("sem datas reais", plan)

    def test_detects_duplicate_source_reference(self):
        invalid = copy.deepcopy(self.seed)
        invalid["proposal"]["weeks"][1]["ideas"][0]["reference"] = invalid["proposal"]["weeks"][0]["ideas"][0]["reference"]
        with self.assertRaisesRegex(ProductionError, "duplicate:reference"):
            validate_seed(invalid)

    def test_detects_duplicate_hook(self):
        invalid = copy.deepcopy(self.seed)
        invalid["proposal"]["weeks"][1]["ideas"][0]["hook_proposal"] = invalid["proposal"]["weeks"][0]["ideas"][0]["hook_proposal"]
        with self.assertRaisesRegex(ProductionError, "duplicate:hook_proposal"):
            validate_seed(invalid)

    def test_blocks_pilot_salmo_13_from_new_queue(self):
        invalid = copy.deepcopy(self.seed)
        invalid["proposal"]["weeks"][0]["ideas"][0]["reference"] = "Salmo 13"
        with self.assertRaisesRegex(ProductionError, "pilot_in_plan"):
            validate_seed(invalid)

    def test_blocks_claimed_preapproved_cadence(self):
        invalid = copy.deepcopy(self.seed)
        invalid["proposal"]["cadence"]["status"] = "OWNER_APPROVED"
        with self.assertRaisesRegex(ProductionError, "seed:cadence"):
            validate_seed(invalid)

    def test_blocks_unsafe_promise_in_hook(self):
        invalid = copy.deepcopy(self.seed)
        invalid["proposal"]["weeks"][0]["ideas"][0]["hook_proposal"] = "Milagre garantido amanhã"
        with self.assertRaisesRegex(ProductionError, "unsafe_promise"):
            validate_seed(invalid)

    def test_blocks_changed_approved_editorial_promise(self):
        invalid = copy.deepcopy(self.seed)
        invalid["approval_scope"]["editorial_promise"]["value"] = "Fique rico com a nossa mensagem"
        with self.assertRaisesRegex(ProductionError, "promise_changed"):
            validate_seed(invalid)

    def test_blocks_publication_claim_and_approved_tagline(self):
        invalid = copy.deepcopy(self.seed)
        invalid["publication_authorized"] = True
        with self.assertRaisesRegex(ProductionError, "publication_lock"):
            validate_seed(invalid)
        invalid = copy.deepcopy(self.seed)
        invalid["approval_scope"]["tagline"]["status"] = "OWNER_APPROVED"
        with self.assertRaisesRegex(ProductionError, "tagline_promoted"):
            validate_seed(invalid)

    def test_missing_provenance_is_blocking(self):
        invalid = copy.deepcopy(self.seed)
        invalid["provenance"] = []
        with tempfile.TemporaryDirectory() as folder:
            dummy = Path(folder)
            (dummy / "agents").mkdir()
            (dummy / "agents/editorial_seed.json").write_text(json.dumps(invalid), encoding="utf-8")
            with self.assertRaisesRegex(ProductionError, "provenance"):
                produce(dummy, dummy)

    def test_rejects_writes_to_protected_sources(self):
        with self.assertRaisesRegex(ProductionError, "protected_directory"):
            produce(ROOT, ROOT / "contracts")


if __name__ == "__main__":
    unittest.main()
