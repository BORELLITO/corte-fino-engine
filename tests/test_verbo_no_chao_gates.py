import copy
import json
import unittest
from pathlib import Path

from engine.quality_gates import validate_manifest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "contracts" / "pilot_salmo_13_master.json"


class VerboNoChaoGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_canonical_preview_passes_non_public_gates(self):
        self.assertEqual(validate_manifest(self.manifest), [])

    def test_duplicate_asset_is_blocking(self):
        broken = copy.deepcopy(self.manifest)
        broken["assets"].append(copy.deepcopy(broken["assets"][0]))
        errors = validate_manifest(broken)
        self.assertTrue(any("duplicate asset_id" in item for item in errors))

    def test_missing_music_is_blocking(self):
        broken = copy.deepcopy(self.manifest)
        broken["music"]["present"] = False
        errors = validate_manifest(broken)
        self.assertTrue(any("music gate failed" in item for item in errors))

    def test_preview_cannot_publish(self):
        broken = copy.deepcopy(self.manifest)
        broken["publication_authorized"] = True
        errors = validate_manifest(broken)
        self.assertTrue(any("publication must remain false" in item for item in errors))

    def test_legacy_execution_is_blocking(self):
        broken = copy.deepcopy(self.manifest)
        broken["execution"]["legacy_projects_used"] = True
        errors = validate_manifest(broken)
        self.assertTrue(any("legacy project usage" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
