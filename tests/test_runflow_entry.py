import json
import shutil
import tempfile
import unittest
from pathlib import Path

from orchestrator.pipeline import evaluate
from orchestrator.runflow_entry import audit_workflows, resolve_spec, run_entry

ROOT = Path(__file__).resolve().parents[1]


class RunflowEntryTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _copy_root(self):
        root = self.tmp / "root"
        shutil.copytree(ROOT / "contracts", root / "contracts")
        (root / ".github" / "workflows").mkdir(parents=True)
        return root

    def test_real_repo_preflight_is_blocked_and_never_published(self):
        rep = run_entry(ROOT, "E01", "preflight", self.tmp / "r", env={})
        self.assertIs(rep["published"], False)
        self.assertIs(rep["publication_authorized"], False)
        self.assertEqual(rep["budget_new_spend_brl"], 0)
        self.assertNotEqual(rep["stages"]["publication"]["status"], "DONE")
        self.assertEqual(rep["stages"]["voice_rights"]["status"], "DONE")
        self.assertEqual(rep["stages"]["clips_rights"]["status"], "DONE")
        self.assertEqual(rep["stages"]["master"]["status"], "READY")
        self.assertEqual(rep["next_action"], "blocked:NO_AUTOMATED_EXECUTOR")
        self.assertNotEqual(rep["stages"]["master"]["status"], "DONE")

    def test_preview_without_package_is_blocked(self):
        rep = run_entry(ROOT, "E01", "preview", self.tmp / "r", env={})
        self.assertIn("BLOCKED_NO_PHYSICAL_PACKAGE", rep["blockers"])
        self.assertEqual(rep["state"], "BLOCKED")

    def test_episode_id_rejects_traversal_and_junk(self):
        for bad in ["../E01", "E1", "e01", "E01; rm", "", "E001", "E01/.."]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                resolve_spec(ROOT, bad)

    def test_unknown_episode_has_no_spec(self):
        with self.assertRaises(ValueError):
            resolve_spec(ROOT, "E99")

    def test_invalid_mode(self):
        with self.assertRaises(ValueError):
            run_entry(ROOT, "E01", "publish", self.tmp / "r", env={})

    def test_spend_and_publication_flags_block(self):
        rep = run_entry(ROOT, "E01", "preflight", self.tmp / "r",
                        env={"VNC_BUDGET_NEW_SPEND": "5", "VNC_PUBLICATION_AUTHORIZED": "true"})
        self.assertIn("budget_new_spend_must_be_zero", rep["blockers"])
        self.assertIn("publication_must_not_be_enabled_in_runflow", rep["blockers"])

    def test_idempotency_key_stable_and_stage_specific(self):
        a = run_entry(ROOT, "E01", "preflight", self.tmp / "a", env={})
        b = run_entry(ROOT, "E01", "preflight", self.tmp / "b", env={})
        self.assertEqual(a["stages"]["script"]["idempotency_key"], b["stages"]["script"]["idempotency_key"])
        self.assertNotEqual(a["stages"]["script"]["idempotency_key"], a["stages"]["voice_measured"]["idempotency_key"])

    def test_workflow_audit_flags_hazards(self):
        root = self._copy_root()
        wf = root / ".github" / "workflows"
        (wf / "a.yml").write_text("on:\n  schedule:\n    - cron: '0 * * * *'\njobs:\n  x:\n    steps: []\n")
        (wf / "b.yml").write_text("on:\n  workflow_dispatch:\njobs:\n  x:\n    env:\n      K: ${{ secrets.ELEVENLABS_API_KEY }}\n")
        (wf / "c.yml").write_text("on:\n  workflow_dispatch:\njobs:\n  x:\n    run: curl https://api.elevenlabs.io/v1\n")
        (wf / "d.yml").write_text("on:\n  push:\n    paths: ['x']\njobs:\n  x:\n    steps: []\n")
        (wf / "e.yml").write_text("on:\n  push:\n    branches: ['a']\njobs:\n  x:\n    env:\n      T: ${{ secrets.GITHUB_TOKEN }}\n")
        rules = {(f["file"], f["rule"].split(":")[0]) for f in audit_workflows(root)}
        self.assertIn(("a.yml", "schedule_trigger"), rules)
        self.assertIn(("b.yml", "non_github_secret"), rules)
        self.assertIn(("c.yml", "paid_provider_host"), rules)
        self.assertIn(("d.yml", "push_without_branch_filter"), rules)
        self.assertNotIn("e.yml", {f for f, _ in rules})

    def test_guard_blocks_when_workflow_hazard_present(self):
        root = self._copy_root()
        (root / ".github" / "workflows" / "bad.yml").write_text("on:\n  schedule:\n    - cron: '0 * * * *'\njobs: {}\n")
        rep = run_entry(root, "E01", "preflight", self.tmp / "rep", env={})
        self.assertTrue(any(b.startswith("workflow_guard:bad.yml") for b in rep["blockers"]))

    def test_report_dir_contains_only_json_and_md(self):
        run_entry(ROOT, "E01", "preflight", self.tmp / "r", env={})
        self.assertTrue({p.suffix for p in (self.tmp / "r").iterdir()} <= {".json", ".md"})

    def test_pipeline_never_names_missing_workflow(self):
        spec = json.loads((ROOT / "contracts" / "e01_pipeline_v3.json").read_text())
        out = evaluate(spec, ROOT)
        self.assertEqual(out["stages"]["clips_approved"]["status"], "DONE")
        self.assertEqual(out["stages"]["clips_rights"]["status"], "DONE")
        self.assertEqual(out["next_action"], "no_automated_executor")
        self.assertNotEqual(out["next_action"], "run_workflow:None")

    def test_voice_policy_is_owner_declaration_and_never_authorizes_publication(self):
        v = json.loads((ROOT / "contracts" / "vnc_voice_policy_v1.json").read_text())
        self.assertIs(v["voice_rights_cleared"], True)
        self.assertIs(v["publication_authorized"], False)
        self.assertIn("NAO_VERIFICADA", v["rights_basis"])
        self.assertEqual(v["applies_to"], "TODOS_OS_EPISODIOS")

    def test_standing_autonomy_never_covers_publication_or_spend(self):
        a = json.loads((ROOT / "contracts" / "vnc_owner_standing_autonomy_v1.json").read_text())
        self.assertIn("publicar ou agendar publicação", a["claude_must_not"])
        self.assertIn("gastar dinheiro ou créditos novos", a["claude_must_not"])
        self.assertEqual(a["owner_only"], ["publicação final"])

    def test_rights_evidence_is_scoped_and_not_publication(self):
        r = json.loads((ROOT / "contracts" / "e01_v3_clip_rights_verification_v1.json").read_text())
        self.assertEqual({c["scene"] for c in r["clips"]}, {"S01", "S04", "S05", "S10"})
        self.assertIs(r["publication_authorized"], False)

    def test_master_requires_voice_and_clip_rights_and_publication_is_human(self):
        spec = json.loads((ROOT / "contracts" / "e01_pipeline_v3.json").read_text())
        master = next(s for s in spec["stages"] if s["id"] == "master")
        self.assertLessEqual({"clips_rights", "voice_rights"}, set(master["requires"]))
        pub = next(s for s in spec["stages"] if s["id"] == "publication")
        self.assertEqual(pub["executor"], "human_only")


if __name__ == "__main__":
    unittest.main()
