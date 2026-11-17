import json
import unittest
from pathlib import Path

from orchestrator.dry_run import run_dry_run


FIXTURE = Path(__file__).parent / "fixtures" / "salmo_13_dry_run.json"


class Salmo13FixtureTests(unittest.TestCase):
    def test_official_fixture_passes_only_in_fixture_mode(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        result = run_dry_run(payload)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.state, "INTERNAL_VALIDATED")
        self.assertEqual(result.gates["publication"], "PASS")

    def test_fixture_is_not_release_ready(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["fixture_mode"] = False
        result = run_dry_run(payload)
        self.assertEqual(result.status, "BLOCKED")
        self.assertIn("rights:status", result.errors)


if __name__ == "__main__":
    unittest.main()
