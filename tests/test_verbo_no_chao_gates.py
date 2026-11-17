import copy
import json
import tempfile
import unittest
from pathlib import Path

from engine.quality_gates import validate_manifest
from orchestrator.runflow import run_flow

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "contracts" / "pilot_salmo_13_master.json"


class VerboNoChaoGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_canonical_preview_passes_non_public_gates(self):
        self.assertEqual(validate_manifest(self.manifest), [])

    def test_duplicate_asset_id_is_blocking(self):
        broken = copy.deepcopy(self.manifest)
        broken["assets"].append(copy.deepcopy(broken["assets"][0]))
        errors = validate_manifest(broken)
        self.assertTrue(any("duplicate asset_id" in item for item in errors))

    def test_duplicate_source_url_is_blocking(self):
        broken = copy.deepcopy(self.manifest)
        broken["assets"][1]["source_url"] = broken["assets"][0]["source_url"]
        errors = validate_manifest(broken)
        self.assertTrue(any("duplicate source_url" in item for item in errors))

    def test_missing_music_is_blocking(self):
        broken = copy.deepcopy(self.manifest)
        broken["music"]["present"] = False
        errors = validate_manifest(broken)
        self.assertTrue(any("music gate failed" in item for item in errors))

    def test_uncleared_asset_blocks_publishable_state(self):
        broken = copy.deepcopy(self.manifest)
        broken["state"] = "READY_FOR_OWNER_APPROVAL"
        broken["rights"] = {
            "visual_review": "CLEARED",
            "voice_review": "CLEARED",
            "music_review": "CLEARED",
            "monetization": "CLEARED",
        }
        errors = validate_manifest(broken)
        self.assertTrue(any("asset 1 rights cleared" in item for item in errors))

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

    def test_invalid_interval_is_reported_not_crashed(self):
        broken = copy.deepcopy(self.manifest)
        broken["assets"][0]["out"] = "not-a-number"
        errors = validate_manifest(broken)
        self.assertTrue(any("asset 1 out must be numeric" in item for item in errors))

    def test_artifact_hash_must_match_bytes(self):
        broken = copy.deepcopy(self.manifest)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "out.mp4"
            output.write_bytes(b"real output")
            broken["artifacts"] = {
                "output": {"path": "out.mp4", "sha256": "0" * 64}
            }
            errors = validate_manifest(broken, artifact_root=root)
        self.assertTrue(any("artifact.output sha256 does not match" in item for item in errors))

    def test_runflow_blocks_without_provider_package(self):
        with tempfile.TemporaryDirectory() as directory:
            package_dir = Path(directory) / "package"
            report_dir = Path(directory) / "reports"
            result = run_flow({"topic": "Salmo 13"}, package_dir, report_dir)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.state, "BLOCKED")
        self.assertTrue(any("provider_package:required" in item for item in result.errors))

    def test_runflow_render_blocks_without_media_package(self):
        with tempfile.TemporaryDirectory() as directory:
            package_dir = Path(directory) / "package"
            package_dir.mkdir()
            (package_dir / "package.json").write_text("{}\n", encoding="utf-8")
            report_dir = Path(directory) / "reports"
            result = run_flow(
                {"topic": "Salmo 13"},
                package_dir,
                report_dir,
                render=True,
            )
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.state, "BLOCKED")
        self.assertTrue(any("assets:required" in item for item in result.errors))


if __name__ == "__main__":
    unittest.main()
