"""Second independent multilingual Whisper weight-set on exact pinned E01 audio.

This uses Systran/faster-whisper-base in addition to the original small model,
with no script prompt and no new WAV. Disagreements cannot be treated as proof
of TTS correctness or fault. Never authorizes video/audio/publication.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from agents.content_production import ProductionError, check
from agents.e01_asr_qa import (
    SECOND_OPINION_REPO, DURATION, WAV_SHA,
    check_source, run_independent_asr, validate_timecodes, compare_text,
)
from agents.e01_asr_semantic_sentry import (
    evaluate_wording, validate_original_asr, EXPECTED_REPORT_SHA,
)

FIRST_SENTRY_SHA = "f8ba94bc0abc4df04ca2a7ef385a455378e59504342eea1fde1fc774069bd20a"
FIRST_SENTRY_BYTES = 1395


def load_first_sentry(path: Path) -> dict[str, Any]:
    check(path.is_file() and path.stat().st_size == FIRST_SENTRY_BYTES,
          "asr_opinion:original_sentry_size")
    with path.open("rb") as f:
        check(hashlib.file_digest(f, "sha256").hexdigest() == FIRST_SENTRY_SHA,
              "asr_opinion:original_sentry_sha")
    val = json.loads(path.read_text(encoding="utf-8"))
    check(val["status"] == "BLOCKED_CRITICAL_WORDING_NEEDS_AUDIO_RECHECK"
          and val["number_of_critical_word_alerts"] == 1
          and val["number_of_sentence_boundary_alerts"] == 1
          and val["source_provenance_sha256_verified"] is True
          and val["publication_authorized"] is False,
          "asr_opinion:original_warning_not_grounded")
    return val


def adjudicate(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    first_words = {x["word"] for x in first.get("critical_word_alerts", [])}
    second_words = {x["word"] for x in second.get("critical_word_alerts", [])}
    shared = sorted(first_words & second_words)
    first_boundaries = len(first.get("sentence_boundary_alerts", []))
    second_boundaries = len(second.get("sentence_boundary_alerts", []))
    if shared or (first_boundaries and second_boundaries):
        category = "POSSIBLE_VOICE_ISSUE_CORROBORATED_BY_SECOND_ASR"
    elif second_words or second_boundaries:
        category = "DIFFERENT_ASR_ERRORS_NO_CONFIDENT_RESOLUTION"
    elif first_words or first_boundaries:
        category = "SECOND_ASR_HEARD_CRITICAL_WORDS_SMALL_MODEL_DISAGREES"
    else:
        category = "NO_CRITICAL_WORDING_ALERTS_BOTH_MODELS"
    return {
        "status": category,
        "shared_critical_word_alerts": shared,
        "small_model_boundary_alerts": first_boundaries,
        "base_model_boundary_alerts": second_boundaries,
        "small_model_critical_word_alerts": len(first_words),
        "base_model_critical_word_alerts": len(second_words),
        "small_model_confidence_is_not_ground_truth": True,
        "base_model_confidence_is_not_ground_truth": True,
        "corroboration_does_not_prove_tts_defect": True,
        "disagreement_does_not_prove_tts_is_correct": True,
        "extra_video_or_audio_rights_granted": False,
        "master_approved": False,
        "publication_authorized": False,
    }


def audit_second_opinion(root: Path, input_dir: Path,
                         initial_report: Path, first_sentry: Path,
                         model_dir: Path) -> dict[str, Any]:
    wav, expected = check_source(root, input_dir)
    first, same_expected = validate_original_asr(root, initial_report)
    check(expected == same_expected, "asr_opinion:source_script_drift")
    first_flags = load_first_sentry(first_sentry)
    second_segments, second_model = run_independent_asr(
        wav, model_dir, repository=SECOND_OPINION_REPO,
    )
    timings = validate_timecodes(second_segments, DURATION)
    recognized = " ".join(x["text"].strip() for x in second_segments)
    text_accuracy = compare_text(expected, recognized)
    wording = evaluate_wording(expected, recognized)
    adjudication = adjudicate(first_flags, wording)
    return {
        "schema_version": "1.0.0",
        "project": "verbo-no-chao",
        "episode_id": "VNC-W01-E1",
        "status": "SECOND_ASR_OPINION_GENERATED_STILL_QUARANTINED",
        "source_wav_sha256": WAV_SHA,
        "first_small_asr_report_sha256": EXPECTED_REPORT_SHA,
        "first_wording_alert_report_sha256": FIRST_SENTRY_SHA,
        "second_model": second_model,
        "second_recognized_transcript": recognized,
        "second_timed_segments": second_segments,
        "second_text_fidelity_estimates": text_accuracy,
        "second_timing_structure": timings,
        "second_semantic_alerts": wording,
        "cross_model_adjudication": adjudication,
        "first_asr_model": first["model"]["repository"],
        "second_asr_model": SECOND_OPINION_REPO,
        "no_script_prompt_used": True,
        "tts_defect_proven": False,
        "production_audio_master_approved": False,
        "human_listening_completed": False,
        "voice_rights_cleared": False,
        "final_video_rendered": False,
        "publication_authorized": False,
    }


def main() -> int:
    p = argparse.ArgumentParser(description="E01 base model second ASR opinion")
    p.add_argument("--root", type=Path, default=Path("."))
    p.add_argument("--wav-dir", type=Path, required=True)
    p.add_argument("--first-asr", type=Path, required=True)
    p.add_argument("--first-alerts", type=Path, required=True)
    p.add_argument("--model-dir", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    try:
        result = audit_second_opinion(
            args.root.resolve(), args.wav_dir.resolve(),
            args.first_asr.resolve(), args.first_alerts.resolve(),
            args.model_dir.resolve(),
        )
    except Exception as exc:
        result = {
            "project": "verbo-no-chao",
            "episode_id": "VNC-W01-E1",
            "status": "BLOCKED_SECOND_ASR_NOT_COMPLETED",
            "error_code": str(exc) if isinstance(exc, ProductionError)
                          else type(exc).__name__,
            "production_audio_master_approved": False,
            "publication_authorized": False,
        }
    out = args.output.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n",
                   encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "base_wer": result.get("second_text_fidelity_estimates", {}).get("word_error_rate"),
        "base_cer": result.get("second_text_fidelity_estimates", {}).get("character_error_rate"),
        "critical_decision": result.get("cross_model_adjudication", {}).get("status"),
        "tts_defect_proven": False,
        "master_approved": False,
        "publication_authorized": False,
        "error_code": result.get("error_code"),
    }, ensure_ascii=False))
    return 0 if result["status"] == "SECOND_ASR_OPINION_GENERATED_STILL_QUARANTINED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
