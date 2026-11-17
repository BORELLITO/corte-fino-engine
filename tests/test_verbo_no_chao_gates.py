import copy
import hashlib
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

    def test_materialized_asset_hash_must_match_bytes(self):
        broken = copy.deepcopy(self.manifest)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            asset = root / "asset.mp4"
            asset.write_bytes(b"real asset")
            broken["assets"][0]["path"] = "asset.mp4"
            broken["assets"][0]["source_hash"] = "0" * 64
            errors = validate_manifest(broken, artifact_root=root)
        self.assertTrue(any("asset 1 sha256 does not match" in item for item in errors))

    def test_materialized_asset_hash_passes_for_matching_bytes(self):
        broken = copy.deepcopy(self.manifest)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            asset = root / "asset.mp4"
            asset.write_bytes(b"real asset")
            broken["assets"][0]["path"] = "asset.mp4"
            broken["assets"][0]["source_hash"] = hashlib.sha256(asset.read_bytes()).hexdigest()
            errors = validate_manifest(broken, artifact_root=root)
        self.assertFalse(any(item.startswith("asset 1 ") for item in errors))

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
        self.assertTrue(any("render:assets_missing" in item for item in result.errors))


    def test_materialized_run_requires_all_four_artifact_records(self):
        broken = copy.deepcopy(self.manifest)
        broken["artifacts"] = {}
        with tempfile.TemporaryDirectory() as directory:
            errors = validate_manifest(broken, artifact_root=Path(directory))
        for key in ("audio", "music", "captions", "output"):
            self.assertIn(f"artifact.{key} record is missing", errors)

    def test_artifact_summary_hash_cannot_disagree_with_provided_file(self):
        broken = copy.deepcopy(self.manifest)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "voice.wav").write_bytes(b"voice bytes")
            true_sha = hashlib.sha256(b"voice bytes").hexdigest()
            broken["artifacts"] = {"audio": {"path": "voice.wav", "sha256": true_sha}}
            errors = validate_manifest(broken, artifact_root=root)
        self.assertIn("artifact.audio sha256 conflicts with canonical summary", errors)
        self.assertFalse(any("artifact.audio sha256 does not match the file" in e for e in errors))

    def test_output_artifact_path_must_match_declared_master(self):
        broken = copy.deepcopy(self.manifest)
        broken["artifacts"] = {"output": {"path": "wrong-master.mp4", "sha256": broken["output"]["sha256"]}}
        with tempfile.TemporaryDirectory() as directory:
            errors = validate_manifest(broken, artifact_root=Path(directory))
        self.assertIn("artifact.output path conflicts with canonical output.file", errors)

    def test_runflow_does_not_rewrite_provider_sha_to_hide_mismatch(self):
        package = copy.deepcopy(self.manifest)
        package["artifacts"] = {"audio": {"path": "voice.wav", "sha256": "0" * 64}}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pack_dir = root / "package"
            pack_dir.mkdir()
            (pack_dir / "voice.wav").write_bytes(b"actual voice")
            (pack_dir / "package.json").write_text(json.dumps(package), encoding="utf-8")
            result = run_flow({"topic": "Salmo 13"}, pack_dir, root / "reports")
            written = json.loads(Path(result.manifest_path).read_text(encoding="utf-8"))
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(written["artifacts"]["audio"]["sha256"], "0" * 64)
        self.assertTrue(any("artifact.audio sha256 does not match the file" in e for e in result.errors))

    def test_runflow_preserves_and_rejects_legacy_execution_claim(self):
        package = copy.deepcopy(self.manifest)
        package["execution"]["legacy_projects_used"] = True
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pack_dir = root / "package"
            pack_dir.mkdir()
            (pack_dir / "package.json").write_text(json.dumps(package), encoding="utf-8")
            result = run_flow({"topic": "Salmo 13"}, pack_dir, root / "reports")
            written = json.loads(Path(result.manifest_path).read_text(encoding="utf-8"))
        self.assertTrue(written["execution"]["legacy_projects_used"])
        self.assertIn("legacy project usage is forbidden", result.errors)
        self.assertEqual(result.status, "BLOCKED")

    def test_runflow_refuses_provider_claimed_publication_or_owner_approval(self):
        invalid_claims = (
            {"state": "PUBLISHED"},
            {"publication_authorized": True},
            {"owner_approval": True},
        )
        for claim in invalid_claims:
            with self.subTest(claim=claim), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                pack_dir = root / "package"
                pack_dir.mkdir()
                package = {**copy.deepcopy(self.manifest), **claim}
                (pack_dir / "package.json").write_text(json.dumps(package), encoding="utf-8")
                result = run_flow({"topic": "Salmo 13"}, pack_dir, root / "reports")
                self.assertEqual(result.status, "BLOCKED")
                self.assertIn("provider_package:publication_or_owner_approval_claim_forbidden", result.errors)


if __name__ == "__main__":
    unittest.main()
