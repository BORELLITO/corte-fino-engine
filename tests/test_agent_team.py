import json
import tempfile
import unittest
from pathlib import Path

from agents.team import CANONICAL_IDS, aggregate, run_agent

ROOT = Path(__file__).resolve().parents[1]


class AgentTeamTests(unittest.TestCase):
    def test_canonical_eight_roles_and_publish_lock(self):
        registry = json.loads((ROOT / "agents/registry.json").read_text(encoding="utf-8"))
        self.assertEqual([role["id"] for role in registry["agents"]], list(CANONICAL_IDS))
        self.assertFalse(registry["default_publication_authorized"])

    def test_all_specialists_generate_read_only_evidence(self):
        for agent in CANONICAL_IDS:
            with self.subTest(agent=agent):
                result = run_agent(agent, ROOT)
                self.assertEqual(result["agent"], agent)
                self.assertIn(result["status"], ("BLOCKED", "PASS_CHECKED_SCOPE"))
                self.assertFalse(result["publication_authorized"])
                self.assertIn("agents/registry.json", result["evidence_sha256"])

    def test_strategy_does_not_claim_missing_evidence(self):
        result = run_agent("niche_strategy", ROOT)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("niche_strategy_not_documented:operations/niche_strategy.json", result["blockers"])

    def test_growth_does_not_invent_plan(self):
        result = run_agent("growth_90d", ROOT)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(any("growth_plan_not_documented" in item for item in result["blockers"]))

    def test_metrics_are_never_invented(self):
        result = run_agent("performance", ROOT)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(any("real_metrics_not_available" in item for item in result["blockers"]))

    def test_short_video_needs_actual_bytes(self):
        result = run_agent("shorts_production", ROOT)
        self.assertIn("physical_master_and_audio_not_available_to_ci", result["blockers"])

    def test_uncleared_rights_block_monetization(self):
        result = run_agent("monetization", ROOT)
        self.assertIn("rights_not_cleared:voice_review", result["blockers"])

    def test_aggregation_requires_every_agent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "growth.json").write_text(json.dumps(run_agent("growth_90d", ROOT)), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing_agent_reports"):
                aggregate(root)

    def test_aggregation_refuses_fake_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for agent in CANONICAL_IDS:
                report = run_agent(agent, ROOT)
                if agent == "monetization":
                    report["publication_authorized"] = True
                (root / f"{agent}.json").write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unsafe_agent_report"):
                aggregate(root)

    def test_aggregation_preserves_blocked_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for agent in CANONICAL_IDS:
                (root / f"{agent}.json").write_text(
                    json.dumps(run_agent(agent, ROOT)), encoding="utf-8"
                )
            report = aggregate(root)
        self.assertEqual(report["agents_executed"], 8)
        self.assertGreater(report["agents_blocked"], 0)
        self.assertEqual(report["status"], "BLOCKED")
        self.assertFalse(report["publication_authorized"])

    def test_duplicate_agent_report_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            item = json.dumps(run_agent("growth_90d", ROOT))
            (root / "one.json").write_text(item, encoding="utf-8")
            (root / "two.json").write_text(item, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unexpected_or_duplicate_agent_report"):
                aggregate(root)


if __name__ == "__main__":
    unittest.main()
