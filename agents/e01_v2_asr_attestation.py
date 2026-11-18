"""Reconcile a real, exactly hashed two-ASR E01 v2 report without fake release.

One stronger model heard "esperar machuca"; the smaller base model segmented
the phrase as "esperar uma chuca". Text fidelity is good in both, but that
does not prove prosody, full pronunciation, licensing or a complete video.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from typing import Any

from agents.content_production import ProductionError, check
from agents.e01_v2_candidate import V2_SHA
from agents.e01_v2_dual_asr import contains_phrase

EVIDENCE = "contracts/e01_v2_dual_asr_real_evidence_v1.json"
REPORT_SHA = "377063ff846ddef641b9288656ea867ede965a73991abe6b4c203dec3a919a8b"
REPORT_BYTES = 72475


def verify_report(root: Path, report_file: Path) -> dict[str, Any]:
    check(report_file.is_file() and report_file.stat().st_size == REPORT_BYTES,
          "v2asr_evidence:source_report_size_mismatch")
    with report_file.open("rb") as f:
        check(hashlib.file_digest(f, "sha256").hexdigest() == REPORT_SHA,
              "v2asr_evidence:source_report_sha_mismatch")
    evidence = json.loads((root/EVIDENCE).read_text(encoding="utf-8"))
    check(evidence.get("project") == "verbo-no-chao"
          and evidence.get("episode_id") == "VNC-W01-E1"
          and evidence.get("source_workflow_run_id") == 44204868327
          and evidence.get("source_report_sha256") == REPORT_SHA
          and evidence.get("report_bytes") == REPORT_BYTES
          and evidence.get("source_script_sha256") == V2_SHA
          and evidence.get("both_models_pass_aggregate_wer_cer") is True
          and evidence.get("both_models_exact_phrase_agreement") is False
          and evidence.get("voice_rights_cleared") is False
          and evidence.get("audio_master_approved") is False
          and evidence.get("publication_authorized") is False,
          "v2asr_evidence:contract_forged")
    r = json.loads(report_file.read_text(encoding="utf-8"))
    models = r.get("model_results")
    decision = r.get("two_model_adjudication")
    check(r.get("status") == "BLOCKED_V2_TEXT_OR_CRITICAL_WORD_DISCREPANCY"
          and r.get("episode_id") == "VNC-W01-E1"
          and r.get("source_script_sha256") == V2_SHA
          and r.get("source_wav_sha256") == evidence["source_wav_sha256"]
          and r.get("duration_seconds") == 70.425
          and r.get("commercial_rights_cleared") is False
          and r.get("final_audio_master_approved") is False
          and r.get("publication_authorized") is False
          and isinstance(models, list) and len(models) == 2
          and isinstance(decision, dict)
          and decision.get("both_models_recognized_exact_replacement") is False
          and decision.get("both_models_passed_aggregate_thresholds") is True
          and decision.get("shared_critical_word_warnings") == [],
          "v2asr_evidence:record_claims_forged")
    for observed, expected in zip(models, evidence["models"]):
        details, q = observed["model"], observed["fidelity_estimates"]
        check(details["repository"] == expected["repository"]
              and details["repository_revision"] == expected["revision"]
              and details["model_bin_sha256"] == expected["model_sha256"]
              and details["initial_prompt_used"] is False
              and q["word_error_rate"] == expected["wer"]
              and q["character_error_rate"] == expected["cer"]
              and q["thresholds_passed"] is True
              and observed["new_pronunciation_safe_phrase_recognized"] is
              expected["replacement_phrase_exact_match"]
              and observed["timecodes"]["word_timecodes_structurally_valid"] is True,
              "v2asr_evidence:model_or_qa_mismatch")
    first, second = models
    # Preserve the exact first-phrase difference, not a blanket "approval".
    check(contains_phrase(first["recognized_text"]) is True
          and contains_phrase(second["recognized_text"]) is False
          and "esperar uma chuca" in second["recognized_text"].casefold(),
          "v2asr_evidence:word_boundary_observation_changed")
    return {
        "project": "verbo-no-chao",
        "episode_id": "VNC-W01-E1",
        "candidate_version": 2,
        "source_report_sha256_verified": True,
        "source_report_sha256": REPORT_SHA,
        "status": "ASR_TWO_MODELS_LOW_GLOBAL_ERROR_ONE_WORD_BOUNDARY_DISAGREEMENT",
        "small_model_exact_new_phrase": True,
        "base_model_word_boundary_warning": "esperar uma chuca",
        "both_models_word_error_thresholds_passed": True,
        "proven_tts_defect": False,
        "proven_pronunciation_correctness": False,
        "possible_lexical_segmentation_false_positive": True,
        "safe_to_prepare_nonrelease_storyboard": True,
        "audio_master_approved": False,
        "voice_rights_cleared": False,
        "final_video_rendered": False,
        "publication_authorized": False,
        "next_production_gate": "REAL_AUDIO_CAPTION_ALIGNMENT_AND_RIGHTS_NO_RELEASE",
    }
