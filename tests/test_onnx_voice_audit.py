import copy
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from agents.content_production import ProductionError, produce as produce_plan
from agents.first_batch_production import produce as produce_scripts
from agents.audio_preflight import produce as produce_audio
from agents.onnx_byte_audit import (
    EXPECTED_SHA256, MIN_BYTES, MAX_BYTES, EXPECTED_URL,
    check_manifest, digest_stream, validate_report, verify_upstream,
)

ROOT = Path(__file__).resolve().parents[1]


class OnnxVoiceAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (ROOT / "contracts/onnx_voice_asset_v1.json").read_text(encoding="utf-8")
        )

    def test_manifest_exactly_pins_onxx_not_pt(self):
        check_manifest(self.manifest)
        self.assertTrue(self.manifest["source_url"].endswith("/voices/pm_alex.bin"))
        self.assertNotEqual(EXPECTED_SHA256,
                            "cf0ba8c573c2480fc54123683a35cf1e2ae130428e441eb91f9149bdb188a526")
        self.assertFalse(self.manifest["rights_approved"])
        self.assertIsNone(self.manifest["hosted_site_asset_sha256"])

    def test_bounded_stream_hashes_bytes_in_memory(self):
        blob = b"\x80Kokoro" * 65000
        expected = hashlib.sha256(blob).hexdigest()
        actual, length = digest_stream(
            io.BytesIO(blob), expected=expected,
            min_bytes=MIN_BYTES, max_bytes=MAX_BYTES,
        )
        self.assertEqual(actual, expected)
        self.assertEqual(length, len(blob))

    def test_corrupt_stream_is_rejected(self):
        blob = b"A" * 500000
        with self.assertRaisesRegex(ProductionError, "sha256_mismatch"):
            digest_stream(io.BytesIO(blob), expected="0" * 64,
                          min_bytes=MIN_BYTES, max_bytes=MAX_BYTES)

    def test_truncated_stream_is_rejected(self):
        with self.assertRaisesRegex(ProductionError, "truncated_or_empty"):
            digest_stream(io.BytesIO(b"\x00" * 3000), expected="0" * 64,
                          min_bytes=MIN_BYTES, max_bytes=MAX_BYTES)

    def test_oversized_stream_is_rejected(self):
        with self.assertRaisesRegex(ProductionError, "size_limit_exceeded"):
            digest_stream(io.BytesIO(b"A" * (MAX_BYTES + 1)),
                          expected="0" * 64, min_bytes=MIN_BYTES, max_bytes=MAX_BYTES)

    def test_manifest_cannot_claim_host_verified(self):
        bad = copy.deepcopy(self.manifest)
        bad["hosted_site_asset_identity"] = "VERIFIED"
        with self.assertRaisesRegex(ProductionError, "forged_verification_or_rights"):
            check_manifest(bad)
        bad = copy.deepcopy(self.manifest)
        bad["rights_approved"] = True
        with self.assertRaisesRegex(ProductionError, "forged_verification_or_rights"):
            check_manifest(bad)

    def test_manifest_cannot_change_digest_or_target(self):
        bad = copy.deepcopy(self.manifest)
        bad["expected_sha256"] = "0" * 64
        with self.assertRaisesRegex(ProductionError, "source_or_digest_modified"):
            check_manifest(bad)
        bad = copy.deepcopy(self.manifest)
        bad["source_url"] = "http://example.invalid/pm_alex.bin"
        with self.assertRaisesRegex(ProductionError, "source_or_digest_modified"):
            check_manifest(bad)

    def test_offline_fake_blob_does_not_claim_verification(self):
        result = verify_upstream(ROOT, stream=io.BytesIO(b"wrong"))
        validate_report(result)
        self.assertEqual(result["status"], "BLOCKED_UPSTREAM_BYTES_NOT_VERIFIED")
        self.assertFalse(result["upstream_bytes_verified"])
        self.assertFalse(result["hosted_voice_bytes_verified"])
        self.assertIsNone(result["actual_sha256"])

    def test_report_rejects_forged_hosted_clearance(self):
        item = verify_upstream(ROOT, stream=io.BytesIO(b"wrong"))
        item["hosted_voice_bytes_verified"] = True
        with self.assertRaisesRegex(ProductionError, "forged_clearance"):
            validate_report(item)

    def test_report_rejects_unverified_sha_claim(self):
        item = verify_upstream(ROOT, stream=io.BytesIO(b"wrong"))
        item["upstream_bytes_verified"] = True
        with self.assertRaisesRegex(ProductionError, "inconsistent_verified_claim"):
            validate_report(item)

    def test_preflight_accepts_blocked_network_report_without_releasing_audio(self):
        with tempfile.TemporaryDirectory() as folder:
            tmp = Path(folder)
            produce_plan(ROOT, tmp)
            produce_scripts(ROOT, tmp, upstream_root=tmp)
            report_path = tmp / "voice-asset-audit/report.json"
            report_path.parent.mkdir()
            blocked = verify_upstream(ROOT, stream=io.BytesIO(b"wrong"))
            report_path.write_text(json.dumps(blocked), encoding="utf-8")
            result = produce_audio(ROOT, tmp, tmp, onnx_audit=report_path)
            rendered = json.loads((tmp / "audio-preflight/preflight.json").read_text(encoding="utf-8"))
        self.assertFalse(result["upstream_onnx_bytes_verified"])
        self.assertFalse(result["hosted_voice_pack_bytes_verified"])
        self.assertEqual(rendered["voice"]["upstream_onnx_audit_status"],
                         "BLOCKED_UPSTREAM_BYTES_NOT_VERIFIED")
        self.assertFalse(rendered["voice"]["hosted_voice_pack_bytes_verified"])
        self.assertEqual(result["status"], "BLOCKED")
        self.assertFalse(result["audio_generated"])

    def test_preflight_rejects_forged_upstream_report(self):
        with tempfile.TemporaryDirectory() as folder:
            tmp = Path(folder)
            produce_plan(ROOT, tmp)
            produce_scripts(ROOT, tmp, upstream_root=tmp)
            report_path = tmp / "voice-asset-audit/report.json"
            report_path.parent.mkdir()
            forged = verify_upstream(ROOT, stream=io.BytesIO(b"wrong"))
            forged["status"] = "VERIFIED_UPSTREAM_ONNX_BYTES_HOSTED_UNPROVEN"
            report_path.write_text(json.dumps(forged), encoding="utf-8")
            with self.assertRaisesRegex(ProductionError, "inconsistent_blocked_claim"):
                produce_audio(ROOT, tmp, tmp, onnx_audit=report_path)


if __name__ == "__main__":
    unittest.main()
