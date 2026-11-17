"""Pure schema, provenance and safety tests; no live browser required here."""
import copy
import hashlib
import unittest

from agents.content_production import ProductionError
from agents.hosted_browser_probe import (
    SITE, VOICE_ONNX_SHA, VOICE_PT_SHA, MAX_VOICE_BYTES, safe_resource,
    is_exact_voice_response, verify_voice_payload, evaluate_probe, validate_report,
)


def minimal():
    return {
        "schema_version": "1.0.0",
        "project": "verbo-no-chao",
        "audit_id": "VNC-HOSTED-KOKORO-RUNTIME-001",
        "requested_url": SITE,
        "mode": "REAL_BROWSER_PASSIVE_PUBLIC_SITE_READ_ONLY",
        "generate_clicked": False,
        "model_download_started_intentionally": False,
        "tts_run": False,
        "voice_payload_observations": [],
        "resource_observations": [],
    }


class HostedBrowserProbeTests(unittest.TestCase):
    def test_url_sanitization_strips_query_fragments_tokens(self):
        x = safe_resource(
            "https://huggingface.co/onnx/voices/pm_alex.bin?token=secret#fragment",
            "fetch",
        )
        self.assertEqual(x["host"], "huggingface.co")
        self.assertEqual(x["path"], "/onnx/voices/pm_alex.bin")
        self.assertNotIn("secret", str(x))

    def test_url_rejects_insecure_protocols(self):
        self.assertIsNone(safe_resource("http://kokoroweb.app/voice", "fetch"))
        self.assertIsNone(safe_resource("file:///etc/passwd", "document"))
        self.assertIsNone(safe_resource("data:text/html,abc", "document"))

    def test_voice_response_requires_exact_filenames_and_allowlisted_hosts(self):
        self.assertTrue(is_exact_voice_response(
            "https://huggingface.co/onnx-community/voices/pm_alex.bin?download=1"))
        self.assertTrue(is_exact_voice_response(
            "https://kokoroweb.app/models/pm_alex.pt"))
        self.assertFalse(is_exact_voice_response(
            "https://evil.example/voice/pm_alex.bin"))
        self.assertFalse(is_exact_voice_response(
            "http://huggingface.co/voice/pm_alex.bin"))
        self.assertFalse(is_exact_voice_response(
            "https://huggingface.co/voice/pm_alex.bin.exe"))

    def test_pinned_formats_have_different_sha(self):
        self.assertNotEqual(VOICE_ONNX_SHA, VOICE_PT_SHA)
        self.assertEqual(len(VOICE_ONNX_SHA), 64)
        self.assertEqual(len(VOICE_PT_SHA), 64)

    def test_binary_response_is_hashed_but_not_run(self):
        data = b"x" * 500000
        x = verify_voice_payload(
            "https://huggingface.co/voices/pm_alex.bin", data)
        self.assertEqual(x["bytes"], len(data))
        self.assertEqual(x["sha256"], hashlib.sha256(data).hexdigest())
        self.assertFalse(x["matches_known_upstream_sha256"])
        self.assertEqual(x["upstream_sha256_expected"], VOICE_ONNX_SHA)
        self.assertNotIn("body", x)

    def test_oversize_voice_binary_rejected_before_claim(self):
        with self.assertRaisesRegex(ProductionError, "size_invalid"):
            verify_voice_payload("https://huggingface.co/voices/pm_alex.bin",
                                 b"x" * (MAX_VOICE_BYTES + 1))
        with self.assertRaisesRegex(ProductionError, "size_invalid"):
            verify_voice_payload("https://huggingface.co/voices/pm_alex.bin",
                                 b"tiny")

    def test_unknown_network_cannot_be_claimed_verified(self):
        record = evaluate_probe(minimal())
        validate_report(record)
        self.assertEqual(record["status"], "BLOCKED_NO_MATCHED_HOSTED_VOICE_RESPONSE")
        self.assertFalse(record["hosted_voice_pack_bytes_verified"])
        self.assertFalse(record["rights_approved"])
        self.assertFalse(record["audio_generated"])
        self.assertIn("no_verified_pm_alex_voice_bytes_in_observed_network",
                      record["blockers"])

    def test_binary_from_unpinned_host_rejected(self):
        with self.assertRaisesRegex(ProductionError, "not_pinned"):
            verify_voice_payload("https://attack.example/pm_alex.bin",
                                 b"x" * 500000)

    def test_matching_sha_still_never_clears_site_identity(self):
        example = minimal()
        example["voice_payload_observations"] = [{
            "voice_filename": "pm_alex.bin",
            "sha256": VOICE_ONNX_SHA,
            "bytes": 500000,
            "matches_known_upstream_sha256": True,
            "source": {"host":"huggingface.co","path":"/voice/pm_alex.bin","resource_type":"voice_bin"},
        }]
        result = evaluate_probe(example)
        validate_report(result)
        self.assertTrue(result["hosted_voice_response_sha256_matched"])
        self.assertEqual(result["status"],
                         "OBSERVED_VOICE_NETWORK_BYTES_MATCH_UPSTREAM_HOSTED_IDENTITY_UNCONFIRMED")
        self.assertFalse(result["hosted_site_runtime_confirmed"])
        self.assertFalse(result["hosted_voice_pack_bytes_verified"])
        self.assertFalse(result["publication_authorized"])

    def test_forged_rights_or_voice_clearance_rejected(self):
        payload = evaluate_probe(minimal())
        for field in ("rights_approved", "license_cleared",
                      "script_approved", "hosted_voice_pack_bytes_verified",
                      "hosted_site_runtime_confirmed",
                      "tts_run", "generate_clicked", "publication_authorized",
                      "audio_generated"):
            forged = copy.deepcopy(payload)
            forged[field] = True
            with self.subTest(field=field):
                with self.assertRaisesRegex(ProductionError, "unsafe_or_unproven_claim"):
                    validate_report(forged)

    def test_token_leak_path_is_rejected(self):
        result = evaluate_probe(minimal())
        result["resource_observations"].append({
            "host":"huggingface.co","path":"/voice?token=secret","resource_type":"fetch"
        })
        with self.assertRaisesRegex(ProductionError, "unsafe_resource_path"):
            validate_report(result)

    def test_required_hosted_blockers_mandatory(self):
        result = evaluate_probe(minimal())
        result["blockers"] = []
        with self.assertRaisesRegex(ProductionError, "required_blocker_missing"):
            validate_report(result)


if __name__ == "__main__":
    unittest.main()
