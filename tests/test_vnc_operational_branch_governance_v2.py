"""MASTER V2 governance: current VNC operational branch, not bootstrap mythology."""
import tempfile
import unittest
from pathlib import Path
from agents.team import _governance

ROOT = Path(__file__).resolve().parents[1]
CANON = "verbo-no-chao/e01-stock-curation-gate-v1"


class VNCCanonicalBranchGovernanceTests(unittest.TestCase):
    def test_current_engine_lock_points_to_verified_operational_branch(self):
        text = (ROOT / "docs/ENGINE_LOCK.md").read_text(encoding="utf-8")
        self.assertIn("A branch operacional atual verificada", text)
        self.assertIn("`" + CANON + "`", text)
        self.assertIn("BORELLITO/verbo-no-chao-engine", text)
        self.assertIn("histórico", text)

    def test_old_bootstrap_only_cannot_pass_specialist_governance(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/"docs").mkdir()
            (root/"docs/CLEAN_ROOM_POLICY.md").write_text(
                "Estado: `APPROVED`\n",encoding="utf-8")
            legacy=(root/"docs/ENGINE_LOCK.md")
            legacy.write_text(
                "A branch de operação do canal é verbo-no-chao/bootstrap.\n"
                "publication_authorized false\n",encoding="utf-8")
            evidence, blockers={},[]
            _governance(root,evidence,blockers)
            self.assertIn("canonical_branch_not_recorded",blockers)
            legacy.write_text(
                "A branch operacional atual verificada: `" + CANON + "`.\n"
                "publication_authorized false\n",encoding="utf-8")
            evidence, blockers={},[]
            _governance(root,evidence,blockers)
            self.assertEqual(blockers,[])
            self.assertIn("docs/ENGINE_LOCK.md",evidence)

    def test_team_description_does_not_claim_eight_independent_ai_models(self):
        content=(ROOT/"docs/SPECIALIST_TEAM.md").read_text(encoding="utf-8")
        self.assertIn("`" + CANON + "`",content)
        self.assertIn("não são",content.casefold())
        self.assertIn("Bíblia",content)
        self.assertIn("não",content.casefold())

    def test_current_project_does_not_retarget_main_or_legacy(self):
        lock=(ROOT/"docs/ENGINE_LOCK.md").read_text(encoding="utf-8")
        self.assertIn("main",lock)
        self.assertIn("Because Of This",lock)
        self.assertNotIn(
            "A branch de operação do canal é verbo-no-chao/bootstrap.",lock
        )


if __name__=="__main__":
    unittest.main()
