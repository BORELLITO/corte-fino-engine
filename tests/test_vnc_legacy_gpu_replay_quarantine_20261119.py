"""Regression safety: retired external-GPU jobs must remain fail-closed.

These tests inspect workflow source only: they do not call external providers,
consume quotas, validate licenses, or imply that any E01 video exists.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FROZEN = {
    ".github/workflows/verbo-no-chao-e01-free-motion-probe.yml":
        "anonymous-zerogpu-motion-proof",
    ".github/workflows/verbo-no-chao-e01-ltx23-motion.yml":
        "ltx23-anonymous-motion",
}


class TestLegacyGpuReplayQuarantine(unittest.TestCase):
    def test_workflows_have_only_the_expected_job(self):
        for relative, expected_job in FROZEN.items():
            with self.subTest(workflow=relative):
                source = (ROOT / relative).read_text(encoding="utf-8")
                self.assertIn("\njobs:\n", source)
                job_text = source.split("\njobs:\n", 1)[1]
                jobs = re.findall(r"(?m)^  ([a-zA-Z0-9_-]+):\s*$", job_text)
                self.assertEqual(jobs, [expected_job])

    def test_each_job_is_unconditionally_skipped_before_any_steps(self):
        for relative, job in FROZEN.items():
            with self.subTest(workflow=relative):
                source = (ROOT / relative).read_text(encoding="utf-8")
                anchor = f"  {job}:\n"
                self.assertEqual(source.count(anchor), 1)
                remainder = source.split(anchor, 1)[1].split("\n    steps:", 1)[0]
                active = [line.strip() for line in remainder.splitlines()
                          if line.strip() and not line.lstrip().startswith("#")]
                self.assertTrue(active, "missing job-level gate")
                self.assertEqual(active[0], "if: ${{ false }}")

    def test_experiment_sources_are_preserved_without_running_them(self):
        expected = {
            ".github/workflows/verbo-no-chao-e01-free-motion-probe.yml":
                "agents/e01_public_zerogpu_motion_probe.py",
            ".github/workflows/verbo-no-chao-e01-ltx23-motion.yml":
                "agents/e01_ltx23_public_probe.py",
        }
        for workflow, script in expected.items():
            with self.subTest(workflow=workflow):
                source = (ROOT / workflow).read_text(encoding="utf-8")
                self.assertIn(script, source)
                self.assertIn("workflow_dispatch:", source)
                # Manual dispatch may create a skipped run; it cannot execute
                # these external provider jobs while their job-level 'if' is false.


if __name__ == "__main__":
    unittest.main()
