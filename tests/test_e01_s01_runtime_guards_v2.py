"""Master V2 fail-closed tests: NO provider/GPU is called."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agents import e01_s01_runtime_preflight as runtime

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/verbo-no-chao-e01-s01-v2-probe.yml"
NONCE = ROOT / "contracts/e01_ltx23_s01_one_shot_trigger_20261118.json"


class S01RuntimeGuards(unittest.TestCase):
    def test_project_isolation_and_zero_default_external_effects(self):
        self.assertEqual(runtime.PROJECT, "VERBO_NO_CHAO_EXCLUSIVO")
        self.assertEqual(runtime.PACKAGE, "portable-ffmpeg==0.5.0")
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict("sys.modules", {"portable_ffmpeg": None}):
                evidence = runtime.run(Path(tmp), synthetic_smoke=True)
            self.assertEqual(evidence["status"], "BLOCKED_RUNTIME_PREPARATION")
            for key in ("paid_service_used", "rights_cleared",
                        "editorial_approved", "master_created",
                        "publication_authorized"):
                self.assertIs(evidence[key], False)
            self.assertEqual(evidence["provider_requests"], 0)
            self.assertTrue((Path(tmp) / "S01_RUNTIME_PREFLIGHT.json").is_file())

    def test_spent_nonce_blocks_manual_rerun(self):
        yaml = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("e01_ltx23_s01_one_shot_trigger_20261118.json", yaml)
        self.assertIn("git diff-tree", yaml)
        self.assertIn("git rev-list --count", yaml)
        self.assertIn("github.event_name == 'push'", yaml)
        self.assertNotIn("workflow_dispatch:", yaml)
        self.assertNotIn("schedule:", yaml)
        self.assertNotIn("pull_request:", yaml)
        self.assertNotIn("apt-get", yaml)
        self.assertIn("persist-credentials: false", yaml)
        self.assertIn("publication_authorized", yaml)
        self.assertIn("timeout-minutes: 9", yaml)

    def test_exact_consumed_nonce_does_not_authorize_publication(self):
        data = json.loads(NONCE.read_text(encoding="utf-8"))
        self.assertEqual(data, {
            "episode_id": "VNC-W01-E1",
            "scene_id": "VNC-E01V2-S01",
            "reason": "one-time post-quota free LTX23 retest",
            "publication_authorized": False,
        })

    def test_bad_binary_file_cannot_pass_as_real_ffmpeg(self):
        with tempfile.TemporaryDirectory() as tmp:
            f1 = Path(tmp) / "ffmpeg"
            f2 = Path(tmp) / "ffprobe"
            f1.write_text("not a binary", encoding="utf-8")
            f2.write_text("not a binary", encoding="utf-8")
            os.chmod(f1, 0o755)
            os.chmod(f2, 0o755)
            with self.assertRaises(OSError):
                runtime.inspect_real_binaries(f1, f2)

    def test_runtime_report_has_no_provider_method(self):
        import inspect
        source = inspect.getsource(runtime)
        self.assertNotIn("Client(", source)
        self.assertNotIn("predict(", source)
        self.assertNotIn("generate_video(", source)
        self.assertNotIn("gh api", source)


if __name__ == "__main__":
    unittest.main()
