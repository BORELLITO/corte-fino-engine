"""MASTER V2 fail-closed regression tests for formerly repeatable free GPU probes.

These tests audit GitHub workflow text; they do NOT contact any provider,
execute video generation, authenticate, download footage, or claim approval.
The old provider modules remain versioned for forensic continuity.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = (
    ".github/workflows/verbo-no-chao-e01-ltx23-motion.yml",
    ".github/workflows/verbo-no-chao-e01-free-motion-probe.yml",
    ".github/workflows/verbo-no-chao-e01-v2-voice.yml",
    ".github/workflows/verbo-no-chao-e01-voice-preview.yml",
)
OPERATIONAL = "verbo-no-chao/e01-stock-curation-gate-v1"
FORBIDDEN_NETWORK_STEPS = (
    "gradio_client", "client.predict(", "Client(", "huggingface_hub",
    "pip install", "apt-get", "curl ", "wget ", "generate_video",
    "anonymous public gpu", "short anonymous", "remote gpu generation step",
)


def workflow_text(path: str) -> str:
    p = (ROOT / path).resolve()
    if not p.is_relative_to(ROOT.resolve()) or not p.is_file():
        raise ValueError("workflow_missing_or_outside_project")
    return p.read_text(encoding="utf-8")


def on_block(source: str) -> str:
    m = re.search(r"(?ms)^on:\s*\n(.*?)(?=^(?:permissions|concurrency|jobs):)", source)
    if m is None:
        raise ValueError("workflow_trigger_not_readable")
    return m.group(1)


class VNCProviderReplayContainmentTests(unittest.TestCase):
    def test_workflows_are_scoped_to_vnc_and_cannot_be_manual_replayed(self):
        for name in TARGETS:
            with self.subTest(workflow=name):
                text = workflow_text(name)
                block = on_block(text)
                self.assertIn('"' + OPERATIONAL + '"', block)
                self.assertNotIn("workflow_dispatch", block)
                self.assertNotIn("schedule:", block)
                self.assertNotIn("pull_request_target", block)
                self.assertNotIn("main", block)
                self.assertIn("push:", block)

    def test_retired_workflows_are_no_network_zero_gpu_only(self):
        for name in TARGETS:
            with self.subTest(workflow=name):
                text = workflow_text(name)
                self.assertIn("offline-only:", text)
                self.assertIn("tests.test_vnc_provider_replay_containment_v2", text)
                self.assertIn("permissions:\n  contents: read", text)
                self.assertIn("persist-credentials: false", text)
                self.assertNotIn("contents: write", text)
                self.assertNotIn("actions/upload-artifact", text)
                self.assertNotIn("secrets.", text)
                self.assertNotIn("sudo", text)
                self.assertNotIn("workflow_dispatch:", text)
                self.assertNotIn("on:\n  schedule:", text)
                self.assertNotIn("github.event_name == 'workflow_dispatch'", text)
                commands = [
                    line.strip().lower()
                    for line in text.splitlines()
                    if line.strip().startswith(("run:", "python ", "timeout ", "sudo ", "pip "))
                ]
                body = "\n".join(commands)
                for token in FORBIDDEN_NETWORK_STEPS:
                    self.assertNotIn(token, body, (name, token))

    def test_no_alternate_project_identity_or_release_side_effects(self):
        for name in TARGETS:
            source = workflow_text(name)
            self.assertTrue(Path(name).name.startswith("verbo-no-chao-"))
            self.assertNotIn("publisher/", source)
            self.assertNotIn("corte-fino/", source)
            self.assertNotIn("captapronto", source.casefold())
            self.assertNotIn("because-of-this", source.casefold())
            self.assertNotIn("upload-pages-artifact", source)
            self.assertNotIn("gh release create", source)

    def test_workflow_is_self_limited_without_legacy_provider_trigger(self):
        for name in TARGETS:
            source = workflow_text(name)
            triggers = on_block(source)
            self.assertIn('"' + name + '"', triggers)
            self.assertIn('"tests/test_vnc_provider_replay_containment_v2.py"', triggers)
            self.assertNotIn("agents/e01_public_zerogpu_motion_probe.py", triggers)
            self.assertNotIn("agents/e01_ltx23_public_probe.py", triggers)

    def test_voice_scripts_never_run_browser_synthesis_in_retired_workflows(self):
        for name in (
            ".github/workflows/verbo-no-chao-e01-v2-voice.yml",
            ".github/workflows/verbo-no-chao-e01-voice-preview.yml",
        ):
            with self.subTest(workflow=name):
                content = workflow_text(name)
                run_lines = "\\n".join(
                    line.strip() for line in content.splitlines()
                    if line.strip().startswith(("run:", "python ", "pip ", "sudo ", "timeout "))
                )
                self.assertNotIn("python -m agents.e01_voice_preview", run_lines)
                self.assertNotIn("python -m agents.e01_v2_voice_preview", run_lines)
                self.assertNotIn("playwright install", run_lines)
                self.assertNotIn("google-chrome", run_lines)
                self.assertIn("tests.test_vnc_provider_replay_containment_v2", content)

    def test_historical_provider_modules_remain_for_auditable_recovery(self):
        for name in (
            "agents/e01_public_zerogpu_motion_probe.py",
            "agents/e01_ltx23_public_probe.py",
            "agents/e01_v2_voice_preview.py",
            "agents/e01_voice_preview.py",
        ):
            self.assertTrue((ROOT / name).is_file())

    def test_current_one_shot_nonce_workflow_is_not_changed_or_reopened(self):
        # This workflow has a separate spent-nonce trigger and was not edited.
        p = ROOT / ".github/workflows/verbo-no-chao-e01-s01-v2-probe.yml"
        src = p.read_text(encoding="utf-8")
        self.assertIn("nonce", src)
        block = on_block(src)
        self.assertNotIn("workflow_dispatch", block)
        self.assertNotIn("schedule:", block)


if __name__ == "__main__":
    unittest.main()
