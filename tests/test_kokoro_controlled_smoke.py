import copy
import hashlib
import unittest

from agents.content_production import ProductionError
from agents.kokoro_controlled_smoke import (
    PHRASE, PHRASE_SHA, MAX_WALL_SECONDS, REQUIRED_BLOCKERS,
    base_report, choose_options, canonical_audio_nodes,
    assess, validate_report
)


class ControlledSmokeTests(unittest.TestCase):
    def test_test_phrase_is_original_non_project_short(self):
        self.assertLess(len(PHRASE), 120)
        self.assertEqual(PHRASE_SHA, hashlib.sha256(PHRASE.encode("utf-8")).hexdigest())
        self.assertNotIn("Habacuque", PHRASE)
        self.assertNotIn("Salmo", PHRASE)
        self.assertIn("teste", PHRASE.casefold() if "teste" in PHRASE.lower() else PHRASE.replace("prova", "teste").casefold())

    def test_language_and_voice_options_are_derived(self):
        selects = [
            {"index": 0, "options": [
                {"label": "English (US)", "value": "en-us"},
                {"label": "Português (Brasil)", "value": "pt-BR"}
            ]},
            {"index": 1, "options": [
                {"label": "Dora", "value": "pf_dora"},
                {"label": "Alex", "value": "pm_alex"}
            ]},
        ]
        lang, voice = choose_options(selects)
        self.assertEqual(lang, {"index": 0, "value": "pt-BR"})
        self.assertEqual(voice, {"index": 1, "value": "pm_alex"})

    def test_unknown_dropdown_never_selects_voice(self):
        self.assertEqual(choose_options([{"index": 0, "options":
                             [{"label": "English", "value": "en"}]}]), (None, None))

    def test_real_audio_requires_metadata_and_blob(self):
        self.assertEqual(canonical_audio_nodes([{
            "ready_state": 1, "duration": 3.5, "source_kind": "blob"
        }]), (True, 3.5))
        self.assertEqual(canonical_audio_nodes([{
            "ready_state": 0, "duration": 3.5, "source_kind": "blob"
        }]), (False, None))
        self.assertEqual(canonical_audio_nodes([{
            "ready_state": 2, "duration": None, "source_kind": "blob"
        }]), (False, None))
        self.assertEqual(canonical_audio_nodes([{
            "ready_state": 2, "duration": 3.5, "source_kind": "other"
        }]), (False, None))

    def test_audio_result_never_authorizes_publication(self):
        report = base_report()
        report["test_audio_observed"] = True
        report["test_audio_duration_seconds"] = 3.1
        report["generate_clicked"] = True
        report = assess(report)
        validate_report(report)
        self.assertEqual(report["status"],
                         "TEST_AUDIO_OBSERVED_PUBLICATION_RIGHTS_BLOCKED")
        self.assertFalse(report["production_audio_generated"])
        self.assertFalse(report["publication_authorized"])
        self.assertFalse(report["hosted_runtime_effective_voice_asset_proven"])
        self.assertTrue(set(REQUIRED_BLOCKERS).issubset(report["blockers"]))

    def test_no_test_audio_preserves_fail_closed(self):
        report = assess(base_report())
        validate_report(report)
        self.assertEqual(report["status"], "BLOCKED_NO_TEST_AUDIO_OBSERVED")
        self.assertIn("smoke_test_audio_not_confirmed", report["blockers"])
        self.assertIn("hosted_voice_bytes_not_observed_or_hashed", report["blockers"])

    def test_fake_rights_production_and_publish_rejected(self):
        for key in ("rights_approved", "license_cleared",
                    "owner_script_approved", "publication_authorized",
                    "production_audio_generated", "output_audio_saved",
                    "model_files_saved", "script_read_or_uploaded",
                    "hosted_runtime_effective_voice_asset_proven"):
            with self.subTest(key=key):
                bad = assess(base_report())
                bad[key] = True
                with self.assertRaisesRegex(ProductionError, "forged_or_unsafe"):
                    validate_report(bad)

    def test_false_test_audio_success_rejected(self):
        bad = assess(base_report())
        bad["status"] = "TEST_AUDIO_OBSERVED_PUBLICATION_RIGHTS_BLOCKED"
        with self.assertRaisesRegex(ProductionError, "audio_status_inconsistent"):
            validate_report(bad)

    def test_upstream_voice_network_match_cannot_clear_runtime(self):
        good = assess(base_report())
        good["voice_network_sha_matches"] = [{
            "voice_filename": "pm_alex.bin",
            "sha256": "0175c753f59c54e7fd5a995bedef0c5ff2fb67e0043dd3dcb2ae74ec2acbeb2a",
            "bytes": 500000,
            "matches_known_upstream_sha256": True,
        }]
        validate_report(good)
        self.assertFalse(good["hosted_runtime_effective_voice_asset_proven"])
        self.assertFalse(good["license_cleared"])

    def test_forged_network_sha_rejected(self):
        bad = assess(base_report())
        bad["voice_network_sha_matches"] = [{
            "sha256": "0" * 64,
            "matches_known_upstream_sha256": True,
        }]
        with self.assertRaisesRegex(ProductionError, "unverified_voice_sha_record"):
            validate_report(bad)

    def test_required_blockers_and_phrase_pinning(self):
        bad = assess(base_report())
        bad["blockers"] = []
        with self.assertRaisesRegex(ProductionError, "required_blocker_missing"):
            validate_report(bad)
        bad = assess(base_report())
        bad["phrase_sha256"] = "0" * 64
        with self.assertRaisesRegex(ProductionError, "report_identity_or_text_changed"):
            validate_report(bad)

    def test_time_and_resource_limits_are_defined(self):
        self.assertLessEqual(MAX_WALL_SECONDS, 190)
        self.assertEqual(len(assess(base_report())["model_resource_host_counts"]), 0)


if __name__ == "__main__":
    unittest.main()
