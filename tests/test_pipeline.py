import json
import tempfile
import unittest
from pathlib import Path

from orchestrator.pipeline import evaluate

ROOT = Path(__file__).resolve().parents[1]
PIPE = json.loads((ROOT / "contracts/e01_pipeline_v1.json").read_text(encoding="utf-8"))


def mini(tmp: Path, evid: dict[str, dict]):
    for name, body in evid.items():
        (tmp / name).write_text(json.dumps(body), encoding="utf-8")
    return {"pipeline_id": "t", "episode_id": "T", "stages": [
        {"id": "a", "requires": [], "executor": "auto", "workflow": "a.yml", "evidence": "a.json",
         "done_when": [{"field": "ok", "equals": True}]},
        {"id": "b", "requires": ["a"], "executor": "auto", "workflow": "b.yml", "evidence": "b.json",
         "done_when": [{"field": "ok", "equals": True}]},
        {"id": "pub", "requires": ["b"], "executor": "human_only", "workflow": None, "evidence": "p.json",
         "done_when": [{"field": "publication_authorized", "equals": True}]},
    ]}


class PipelineTests(unittest.TestCase):
    def test_real_e01_is_blocked_and_never_published(self):
        r = evaluate(PIPE, ROOT)
        self.assertEqual(r["state"], "BLOCKED")
        self.assertNotEqual(r["stages"]["publication"]["status"], "DONE")
        self.assertEqual(r["stages"]["script"]["status"], "DONE")
        self.assertEqual(r["next_stage"], "voice")
        self.assertEqual(r["next_action"], "run_workflow:verbo-no-chao-e01-v2-voice.yml")

    def test_downstream_waits_on_upstream(self):
        with tempfile.TemporaryDirectory() as d:
            p = mini(Path(d), {"a.json": {"ok": False}, "b.json": {"ok": True}, "p.json": {}})
            r = evaluate(p, Path(d))
            self.assertEqual(r["stages"]["b"]["status"], "WAITING")

    def test_truthy_non_bool_does_not_pass(self):
        with tempfile.TemporaryDirectory() as d:
            p = mini(Path(d), {"a.json": {"ok": 1}, "b.json": {}, "p.json": {}})
            self.assertEqual(evaluate(p, Path(d))["stages"]["a"]["status"], "READY")

    def test_missing_or_corrupt_evidence_is_not_done(self):
        with tempfile.TemporaryDirectory() as d:
            p = mini(Path(d), {"a.json": {"ok": True}, "p.json": {}})
            (Path(d) / "b.json").write_text("{broken", encoding="utf-8")
            self.assertEqual(evaluate(p, Path(d))["stages"]["b"]["status"], "READY")
            (Path(d) / "a.json").unlink()
            self.assertEqual(evaluate(p, Path(d))["stages"]["a"]["status"], "READY")

    def test_publication_needs_human_even_when_all_else_done(self):
        with tempfile.TemporaryDirectory() as d:
            p = mini(Path(d), {"a.json": {"ok": True}, "b.json": {"ok": True}, "p.json": {}})
            r = evaluate(p, Path(d))
            self.assertEqual(r["next_stage"], "pub")
            self.assertEqual(r["next_action"], "owner_authorization_required")
            self.assertEqual(r["state"], "BLOCKED")

    def test_evidence_path_cannot_escape_root(self):
        with tempfile.TemporaryDirectory() as d:
            p = mini(Path(d), {"a.json": {"ok": True}, "b.json": {}, "p.json": {}})
            p["stages"][0]["evidence"] = "../../etc/passwd"
            self.assertEqual(evaluate(p, Path(d))["stages"]["a"]["status"], "READY")

    def test_bad_order_rejected(self):
        p = {"stages": [{"id": "x", "requires": ["y"], "evidence": "x.json", "done_when": []},
                        {"id": "y", "requires": [], "evidence": "y.json", "done_when": []}]}
        with self.assertRaises(ValueError):
            evaluate(p, ROOT)

    def test_all_workflows_in_contract_exist(self):
        for s in PIPE["stages"]:
            if s["workflow"]:
                self.assertTrue((ROOT / ".github/workflows" / s["workflow"]).is_file(), s["workflow"])


if __name__ == "__main__":
    unittest.main()
