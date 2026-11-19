"""Offline, zero-network security tests for the VNC Agnes transport."""
import copy
import hashlib
import unittest
from unittest.mock import patch

from agents import e01_agnes_flash_transport_v1 as t


class TestAgnesFlashTransport(unittest.TestCase):
    def test_plan_is_offline_and_reuses_canonical_e01(self):
        with patch.object(t, "_http_json") as http:
            p = t.plan()
        http.assert_not_called()
        self.assertEqual(p["status"], "PLAN_ONLY_NO_PROVIDER_REQUEST")
        self.assertEqual(p["request"]["seconds"], "6")
        self.assertEqual(p["request"]["aspect_ratio"], "9:16")
        self.assertEqual(p["request"]["model"], t.MODEL)
        self.assertFalse(p["generation_started"])
        self.assertFalse(p["submit_enabled"])

    def test_no_key_never_contacts_provider(self):
        with patch.object(t, "_http_json") as http:
            report = t.model_preflight("")
        self.assertEqual(report["status"], "BLOCKED_NO_AGNES_API_KEY")
        http.assert_not_called()

    def test_catalog_check_is_get_only_and_not_price_attestation(self):
        with patch.object(t, "_http_json", return_value={
            "data": [{"id": "agnes-video-2.5"}, {"id": t.MODEL}]
        }) as http:
            result = t.model_preflight("placeholder-secret")
        http.assert_called_once_with("GET", t.MODELS_URL, "placeholder-secret")
        self.assertEqual(result["status"], "MODEL_LISTED_PRICE_UNVERIFIED")
        self.assertFalse(result["account_specific_zero_price_verified"])

    def test_catalog_missing_or_malformed_never_becomes_enabled(self):
        for response in ({"data": []}, {"data": None}, {"data": ["wrong"]},
                         {"data": [{"id": "agnes-video-2.5"}]}):
            with self.subTest(response=response), patch.object(t, "_http_json", return_value=response):
                self.assertEqual(t.model_preflight("placeholder-secret")["status"],
                                 "MODEL_NOT_LISTED")

    def test_checked_in_gate_denies_submission_even_with_key_and_authorization(self):
        with patch.object(t, "_http_json") as http:
            with self.assertRaisesRegex(t.AgnesTransportError, "submit_blocked"):
                t.submit_once("placeholder-secret", t.SCENE)
        http.assert_not_called()

    def test_all_guard_conditions_must_be_true(self):
        good = t.gate_config()
        required = ("api_access_verified", "account_default_plan_verified",
                    "account_specific_zero_price_verified",
                    "zero_price_reverified_before_generation",
                    "scene_generation_authorized", "enable_submission")
        for field in required:
            attempt = copy.deepcopy(good)
            for f in required:
                attempt[f] = True
            attempt[field] = False
            with self.subTest(field=field), patch.object(t, "gate_config", return_value=attempt):
                with patch.object(t, "_http_json") as http:
                    with self.assertRaises(t.AgnesTransportError):
                        t.submit_once("placeholder-secret", t.SCENE)
                    http.assert_not_called()

    def test_wrong_scene_authorization_denied_even_when_flags_true(self):
        gate = t.gate_config()
        for key in ("api_access_verified", "account_default_plan_verified",
                    "account_specific_zero_price_verified",
                    "zero_price_reverified_before_generation",
                    "scene_generation_authorized", "enable_submission"):
            gate[key] = True
        with patch.object(t, "gate_config", return_value=gate):
            with patch.object(t, "_http_json") as http:
                with self.assertRaisesRegex(t.AgnesTransportError, "scene_specific"):
                    t.submit_once("placeholder-secret", "another-scene")
                http.assert_not_called()

    def test_never_upgrades_to_paid_model_even_if_payload_changes(self):
        gate = t.gate_config()
        for key in ("api_access_verified", "account_default_plan_verified",
                    "account_specific_zero_price_verified",
                    "zero_price_reverified_before_generation",
                    "scene_generation_authorized", "enable_submission"):
            gate[key] = True
        forged = t.payload()
        forged["model"] = "agnes-video-2.5"
        with patch.object(t, "gate_config", return_value=gate), patch.object(t, "payload", return_value=forged):
            with patch.object(t, "_http_json") as http:
                with self.assertRaisesRegex(t.AgnesTransportError, "unexpected_paid"):
                    t.submit_once("placeholder-secret", t.SCENE)
                http.assert_not_called()

    def test_successful_submit_still_not_approved_and_one_post_only(self):
        gate = t.gate_config()
        for key in ("api_access_verified", "account_default_plan_verified",
                    "account_specific_zero_price_verified",
                    "zero_price_reverified_before_generation",
                    "scene_generation_authorized", "enable_submission"):
            gate[key] = True
        with patch.object(t, "gate_config", return_value=gate), patch.object(t, "_http_json", return_value={
            "video_id": "verified-123456"
        }) as http:
            result = t.submit_once("placeholder-secret", t.SCENE)
        self.assertEqual(result["status"], "JOB_SUBMITTED_NOT_APPROVED")
        self.assertFalse(result["publication_authorized"])
        http.assert_called_once()
        self.assertEqual(http.call_args.args[0], "POST")
        self.assertEqual(http.call_args.args[1], t.CREATE_URL)

    def test_ambiguous_submission_does_not_retry(self):
        gate = t.gate_config()
        for key in ("api_access_verified", "account_default_plan_verified",
                    "account_specific_zero_price_verified",
                    "zero_price_reverified_before_generation",
                    "scene_generation_authorized", "enable_submission"):
            gate[key] = True
        with patch.object(t, "gate_config", return_value=gate), patch.object(t, "_http_json", return_value={}) as http:
            with self.assertRaisesRegex(t.AgnesTransportError, "ambiguous"):
                t.submit_once("placeholder-secret", t.SCENE)
        http.assert_called_once()

    def test_poll_rejects_id_injection_without_network(self):
        with patch.object(t, "_http_json") as http:
            for ident in ("../../bad", "https://attacker.test", "x&model_name=paid", "a"):
                with self.subTest(ident=ident), self.assertRaises(t.AgnesTransportError):
                    t.poll_once("placeholder-secret", ident)
        http.assert_not_called()

    def test_poll_completed_hides_private_url_and_never_approves_master(self):
        url = "https://provider.example/private-video.mp4?access_token=secret"
        with patch.object(t, "_http_json", return_value={
            "status": "completed", "url": url}) as http:
            result = t.poll_once("placeholder-secret", "video_123456")
        self.assertEqual(result["media_url_sha256"], hashlib.sha256(url.encode()).hexdigest())
        self.assertNotIn(url, str(result))
        self.assertFalse(result["master_allowed"])
        self.assertFalse(result["publication_authorized"])
        self.assertEqual(http.call_args.args[0], "GET")
        self.assertIn("model_name=agnes-video-2.5-flash", http.call_args.args[1])

    def test_poll_without_https_media_is_blocked(self):
        with patch.object(t, "_http_json", return_value={
            "status": "completed", "url": "http://provider.example/file.mp4"}):
            with self.assertRaisesRegex(t.AgnesTransportError, "without_https_media"):
                t.poll_once("placeholder-secret", "video_123456")

    def test_runtime_gate_tampering_fails_closed(self):
        with patch("json.loads", return_value={
            "project": "other-project", "scene_id": t.SCENE,
            "model": t.MODEL, "endpoint": t.CREATE_URL,
            "price_ceiling_usd": 0, "max_post_attempts": 1,
            "publication_authorized": False
        }):
            with self.assertRaisesRegex(t.AgnesTransportError, "invalid_or_untrusted"):
                t.gate_config()


if __name__ == "__main__":
    unittest.main()
