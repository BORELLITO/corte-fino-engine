"""Adversarial cloud runflow regression checks: no external providers or costs."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from engine.quality_gates import validate_manifest
from orchestrator.runflow import run_flow

ROOT = Path(__file__).resolve().parents[1]
BASE = json.loads((ROOT / "contracts/pilot_salmo_13_master.json").read_text(encoding="utf-8"))


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fixture_with_physical_bytes(root: Path) -> dict:
    """Deliberately fake media bytes; hash verifiable but NOT decodable."""
    package = copy.deepcopy(BASE)
    package["state"] = "PREVIEW_READY"
    for i, asset in enumerate(package["assets"]):
        name = f"scene-{i}.mp4"
        blob = f"fake bytes for scene {i}".encode()
        (root / name).write_bytes(blob)
        asset["path"] = name
        asset["source_hash"] = _sha(blob)
    package["artifacts"] = {}
    for label, name, own_field in (
        ("audio", "source.wav", "sha256"),
        ("music", "score.wav", "hash"),
        ("captions", "subs.ass", None),
        ("output", "draft.mp4", "sha256"),
    ):
        blob = ("not real " + label).encode()
        (root / name).write_bytes(blob)
        package["artifacts"][label] = {"path": name, "sha256": _sha(blob)}
        if label == "output":
            package["output"]["file"] = name
        else:
            package[label]["path"] = name
        if own_field:
            package["output" if label == "output" else label][own_field] = _sha(blob)
    return package


class TestCloudIntegrityHardening(unittest.TestCase):
    def test_canonical_pilot_remains_unchanged_and_valid_as_legacy_preview(self):
        self.assertEqual(validate_manifest(copy.deepcopy(BASE)), [])

    def test_real_e01_pcm16_contract_can_be_expressed_without_pilot_drift(self):
        data = copy.deepcopy(BASE)
        data["audio"]["format"] = "WAV 24 kHz mono PCM16"
        self.assertEqual(validate_manifest(data), [])

    def test_malformed_states_and_sections_cannot_crash_validator(self):
        for bad in ([], {}, True, 3):
            with self.subTest(bad=bad):
                document = copy.deepcopy(BASE)
                document["state"] = bad
                self.assertTrue(validate_manifest(document))
        for field in ("execution", "audio", "music", "captions", "rights", "output", "gates"):
            with self.subTest(field=field):
                doc = copy.deepcopy(BASE)
                doc[field] = ["unexpected list"]
                self.assertTrue(validate_manifest(doc))
        doc = copy.deepcopy(BASE)
        doc["assets"][0]["asset_id"] = {"unhashable": True}
        self.assertTrue(validate_manifest(doc))

    def test_invalid_numbers_and_boolean_segment_count_are_rejected(self):
        for value in ("Infinity", "-Infinity", "NaN", True):
            doc = copy.deepcopy(BASE)
            doc["assets"][0]["out"] = value
            self.assertTrue(validate_manifest(doc), value)
        for value in (float("inf"), float("nan"), -1.0, 0):
            doc = copy.deepcopy(BASE)
            doc["audio"]["duration_sec"] = value
            self.assertTrue(validate_manifest(doc), value)
        doc = copy.deepcopy(BASE)
        doc["audio"]["segments"] = True
        self.assertTrue(validate_manifest(doc))

    def test_cloud_provider_missing_artifacts_is_blocked_not_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = fixture_with_physical_bytes(root)
            del package["artifacts"]
            (root / "package.json").write_text(json.dumps(package), encoding="utf-8")
            result = run_flow({"topic": "hash audit"}, root, root / "reports")
            self.assertEqual(result.status, "BLOCKED")
            for label in ("audio", "music", "captions", "output"):
                self.assertTrue(any(f"artifact.{label} is required" in e for e in result.errors), label)

    def test_runflow_does_not_launder_provider_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = fixture_with_physical_bytes(root)
            package["artifacts"]["audio"]["sha256"] = "0" * 64
            (root / "package.json").write_text(json.dumps(package), encoding="utf-8")
            result = run_flow({"topic": "sha mismatch"}, root, root / "reports")
            self.assertEqual(result.status, "BLOCKED")
            self.assertTrue(any("artifact.audio sha256 does not match" in e for e in result.errors))
            manifest = json.loads(Path(result.manifest_path).read_text(encoding="utf-8"))
            self.assertEqual(manifest["artifacts"]["audio"]["sha256"], "0" * 64)

    def test_explicit_legacy_prohibition_cannot_be_erased(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = fixture_with_physical_bytes(root)
            package["execution"] = {
                "mode": "cloud_only", "device_role": "control_only",
                "legacy_projects_used": True,
            }
            (root / "package.json").write_text(json.dumps(package), encoding="utf-8")
            result = run_flow({"topic": "legacy flag"}, root, root / "reports")
            self.assertEqual(result.status, "BLOCKED")
            self.assertIn("legacy project usage is forbidden", result.errors)

    def test_fake_video_cannot_be_marked_preview_ready(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = fixture_with_physical_bytes(root)
            errors = validate_manifest(package, artifact_root=root)
            self.assertTrue(any("media:" in e or "release:full_media_decode_failed" in e for e in errors))

    def test_published_state_rejected_without_external_publisher(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = fixture_with_physical_bytes(root)
            package["state"] = "PUBLISHED"
            package["owner_approval"] = True
            package["publication_authorized"] = True
            (root / "package.json").write_text(json.dumps(package), encoding="utf-8")
            result = run_flow({"topic": "fake publication"}, root, root / "reports")
            self.assertEqual(result.status, "BLOCKED")
            self.assertIn("runflow:publication_requires_separate_authorized_publisher", result.errors)

    def test_wrong_source_hash_blocks_before_render_invocation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = fixture_with_physical_bytes(root)
            package["assets"][0]["source_hash"] = "a" * 64
            (root / "package.json").write_text(json.dumps(package), encoding="utf-8")
            result = run_flow({"topic": "wrong source"}, root, root / "reports", render=True)
            self.assertEqual(result.status, "BLOCKED")
            self.assertIn("asset:1:sha256_mismatch", result.errors)
            self.assertFalse((root / "rendered.mp4").exists())


if __name__ == "__main__":
    unittest.main()
