"""Validate immutable real-browser smoke evidence without approving voice or publishing.

This file records a historical, observed result from GitHub Actions. It is
not a fresh live probe and cannot attest the voice actually used for inference.
"""
from __future__ import annotations
from typing import Any
from agents.content_production import check
from agents.kokoro_controlled_smoke import PHRASE_SHA
from agents.onnx_byte_audit import EXPECTED_SHA256 as ONNX_SHA

RUN_ID = 44179520750
RUN_SHA = "781817eee77369739174fe24751a3111eb0af682"
REPORT_SHA = "1b83c7dcdcf11c18241d20c572b72db286b3c4a1a38cdae45dc8ffa5acf9af37"
ARTIFACT_ID = 14371033576


def validate_smoke_attestation(value: Any) -> dict[str, Any]:
    check(isinstance(value, dict) and value.get("project") == "verbo-no-chao"
          and value.get("evidence_id") == "VNC-CONTROLLED-SMOKE-2026-11-17-01"
          and value.get("historical_observation_only") is True,
          "controlled_smoke:identity")
    source = value.get("source")
    check(isinstance(source, dict)
          and source.get("run_id") == RUN_ID
          and source.get("head_sha") == RUN_SHA
          and source.get("artifact_id") == ARTIFACT_ID
          and source.get("original_report_sha256") == REPORT_SHA
          and source.get("report_bytes") == 1723
          and source.get("report_name") == "report.json"
          and source.get("observed_date") == "2026-11-17"
          and source.get("workflow_url") ==
             "https://github.com/BORELLITO/corte-fino-engine/actions/runs/44179520750",
          "controlled_smoke:source_provenance")
    check(value.get("site") == "https://kokoroweb.app/"
          and value.get("fixture_sha256") == PHRASE_SHA
          and value.get("test_character_count") == 74
          and value.get("pt_br_selected") is True
          and value.get("pm_alex_selected") is True
          and value.get("generate_clicked") is True
          and value.get("test_audio_element_observed") is True
          and value.get("test_audio_duration_seconds") == 5.875
          and value.get("model_resources_observed") == 12,
          "controlled_smoke:browser_observations")
    cached = value.get("cached_voice_observation")
    check(isinstance(cached, dict)
          and cached.get("name") == "pm_alex.bin"
          and cached.get("format") == "onnx_voice_bin"
          and cached.get("bytes") == 522240
          and cached.get("cached_file_sha256") == ONNX_SHA
          and cached.get("upstream_onnx_file_sha256") == ONNX_SHA
          and cached.get("hash_matches_upstream") is True
          and cached.get("source_observation") ==
              "READ_ONLY_CACHE_API_IN_ORIGINAL_BROWSER_SESSION"
          and cached.get("proves_effective_inference_use") is False,
          "controlled_smoke:cache_sha_or_unsupported_claim")
    check(value.get("network_voice_hash_matches") == 0
          and value.get("test_audio_saved") is False
          and value.get("binary_pack_saved") is False
          and value.get("production_audio_generated") is False
          and value.get("human_listening_review") == "PENDING"
          and value.get("effective_runtime_asset_usage_proven") is False
          and value.get("exact_dependencies_and_rights_cleared") is False
          and value.get("owner_script_approval") is False
          and value.get("publication_authorized") is False
          and value.get("status") ==
             "TECHNICAL_SMOKE_AND_CACHE_MATCH_OBSERVED_RIGHTS_BLOCKED",
          "controlled_smoke:forged_production_or_rights")
    limits = value.get("limitations")
    check(isinstance(limits, list) and len(limits) >= 4,
          "controlled_smoke:missing_limitations")
    return {
        "result": "HISTORICAL_TEST_AUDIO_AND_CACHE_SHA_OBSERVED",
        "source_workflow_run_id": RUN_ID,
        "source_report_sha256": REPORT_SHA,
        "observed_date": "2026-11-17",
        "test_audio_duration_seconds": 5.875,
        "cached_voice_filename": "pm_alex.bin",
        "cached_voice_bytes": 522240,
        "cached_voice_sha256": ONNX_SHA,
        "cache_matches_upstream": True,
        "effective_runtime_asset_usage_proven": False,
        "human_listening_review": "PENDING",
        "voice_rights_cleared": False,
        "owner_script_approval": False,
        "production_audio_generated": False,
        "publication_authorized": False,
    }
