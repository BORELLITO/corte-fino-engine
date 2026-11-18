"""Independent two-model ASR of immutable E01 v2 WAV, no publisher action.

A clean aggregate WER is insufficient: the exact replacement phrase
'esperar machuca' must appear in BOTH independent ASR model outputs, and
critical words/potential omissions must be checked. Each model is run without
feeding the reference text as a prompt. Release always remains BLOCKED.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import wave
from pathlib import Path
from typing import Any

from agents.content_production import ProductionError, check
from agents.e01_v2_candidate import approved_v2, V2_SHA, PARENT_SHA
from agents.e01_asr_qa import (
    REPO, SECOND_OPINION_REPO, run_independent_asr, validate_timecodes,
    compare_text, tokenize,
)
from agents.e01_asr_semantic_sentry import evaluate_wording

SOURCE_CONTRACT = "contracts/e01_v2_voice_preview_evidence_v1.json"
REQUIRED_CORRECTION = ["esperar", "machuca"]
ORIGINAL_PRODUCER_RUN_ID = 44204100486
SOURCE_FILE = "e01-v2-preview-only.wav"


def file_sha256(path: Path) -> str:
    with path.open("rb") as h:
        return hashlib.file_digest(h, "sha256").hexdigest()


def source_check(root: Path, source_dir: Path) -> tuple[Path, str, float, dict[str, Any]]:
    candidate = source_dir / SOURCE_FILE
    report_file = source_dir / "report.json"
    check(candidate.is_file() and report_file.is_file(),
          "v2asr:missing_physical_voice_artifact")
    evidence_file = root / SOURCE_CONTRACT
    check(evidence_file.is_file(), "v2asr:missing_pinned_voice_contract")
    evidence = json.loads(evidence_file.read_text(encoding="utf-8"))
    check(evidence.get("project") == "verbo-no-chao"
          and evidence.get("episode_id") == "VNC-W01-E1"
          and evidence.get("candidate_version") == 2
          and evidence.get("source_workflow_run_id") == ORIGINAL_PRODUCER_RUN_ID
          and evidence.get("candidate_script_sha256") == V2_SHA
          and evidence.get("parent_script_sha256") == PARENT_SHA
          and evidence.get("status") == "QUARANTINED_E01_V2_WAV_PHYSICALLY_VERIFIED"
          and evidence.get("production_audio_master_approved") is False
          and evidence.get("voice_rights_cleared") is False
          and evidence.get("publication_authorized") is False,
          "v2asr:untrusted_candidate_evidence")
    check(candidate.stat().st_size == evidence["wav_bytes"]
          and report_file.stat().st_size == evidence["report_bytes"]
          and file_sha256(candidate) == evidence["wav_sha256"]
          and file_sha256(report_file) == evidence["report_sha256"],
          "v2asr:physical_sha_or_size_mismatch")
    report = json.loads(report_file.read_text(encoding="utf-8"))
    metrics = report.get("physical_wav_metrics", {})
    check(report.get("candidate_script_sha256") == V2_SHA
          and report.get("original_script_sha256") == PARENT_SHA
          and report.get("candidate_version") == 2
          and report.get("status") == evidence["status"]
          and report.get("audio_preview_saved") is True
          and report.get("voice_runtime_rights_cleared") is False
          and report.get("production_audio_master_approved") is False
          and report.get("publication_authorized") is False
          and metrics.get("sha256") == evidence["wav_sha256"]
          and metrics.get("bytes") == evidence["wav_bytes"],
          "v2asr:actual_producer_receipt_inconsistent")
    with wave.open(str(candidate), "rb") as wav:
        check(wav.getframerate() == 24000
              and wav.getnchannels() == 1
              and wav.getsampwidth() == 2,
              "v2asr:unexpected_pcm_format")
        duration = wav.getnframes() / wav.getframerate()
    check(math.isfinite(duration)
          and 25.0 <= duration <= 150.0
          and abs(duration - evidence["duration_seconds"]) < 0.001,
          "v2asr:duration_does_not_match_wav")
    expected, decision = approved_v2(root)
    check(decision["script_sha256"] == V2_SHA
          and decision["publication_authorized"] is False,
          "v2asr:editorial_receipt_changed")
    return candidate, expected, duration, evidence


def contains_phrase(recognized: str, words: list[str] = REQUIRED_CORRECTION) -> bool:
    tokens = tokenize(recognized)
    return any(tokens[i:i+len(words)] == words
               for i in range(max(0, len(tokens)-len(words)+1)))


def run_model(wav: Path, model_root: Path, repository: str,
              expected: str, duration: float) -> dict[str, Any]:
    segments, model = run_independent_asr(wav, model_root, repository=repository)
    timing = validate_timecodes(segments, duration, expected_duration=None)
    transcript = " ".join(s["text"].strip() for s in segments)
    differences = compare_text(expected, transcript)
    alerts = evaluate_wording(expected, transcript)
    exact = contains_phrase(transcript)
    return {
        "model": model,
        "recognized_text": transcript,
        "segments": segments,
        "timecodes": timing,
        "fidelity_estimates": differences,
        "critical_word_alerts": alerts,
        "new_pronunciation_safe_phrase_recognized": exact,
        "word_level_timestamps_not_final_captions": True,
    }


def adjudicate(models: list[dict[str, Any]]) -> dict[str, Any]:
    check(len(models) == 2
          and models[0]["model"]["repository"] == REPO
          and models[1]["model"]["repository"] == SECOND_OPINION_REPO,
          "v2asr:not_two_distinct_model_weights")
    for output in models:
        check(output["timecodes"]["word_timecodes_structurally_valid"] is True,
              "v2asr:invalid_timecodes")
    two_phrase = all(x["new_pronunciation_safe_phrase_recognized"] for x in models)
    two_text = all(x["fidelity_estimates"]["thresholds_passed"] for x in models)
    critical = [
        { "repository": x["model"]["repository"],
          "alerts": x["critical_word_alerts"]["critical_word_alerts"],
          "boundaries": x["critical_word_alerts"]["sentence_boundary_alerts"],
        } for x in models
    ]
    shared_critical = set(
        w["word"] for w in models[0]["critical_word_alerts"]["critical_word_alerts"]
    ) & set(
        w["word"] for w in models[1]["critical_word_alerts"]["critical_word_alerts"]
    )
    pass_triage = bool(two_phrase and two_text and not shared_critical)
    return {
        "status": ("ASR_V2_TWO_MODEL_TEXT_TRIAGE_PASS_STILL_QUARANTINED"
                   if pass_triage else
                   "BLOCKED_V2_TEXT_OR_CRITICAL_WORD_DISCREPANCY"),
        "both_models_recognized_exact_replacement": two_phrase,
        "both_models_passed_aggregate_thresholds": two_text,
        "shared_critical_word_warnings": sorted(shared_critical),
        "per_model_wording_warnings": critical,
        "provisional_text_gate_passed": pass_triage,
        "practical_pronunciation_or_prosody_quality_guaranteed": False,
        "human_listening_completed": False,
        "voice_rights_cleared": False,
        "production_audio_master_approved": False,
        "full_video_rendered": False,
        "publication_authorized": False,
    }


def audit(root: Path, audio_dir: Path, model_dir: Path) -> dict[str, Any]:
    wav, text, duration, evidence = source_check(root, audio_dir)
    models = []
    for repo, subdir in ((REPO, "small"), (SECOND_OPINION_REPO, "base")):
        models.append(run_model(wav, model_dir/subdir, repo, text, duration))
    adjudication = adjudicate(models)
    return {
        "schema_version": "1.0.0", "project": "verbo-no-chao",
        "episode_id": "VNC-W01-E1", "candidate_version": 2,
        "source_run_id": ORIGINAL_PRODUCER_RUN_ID,
        "source_wav_sha256": evidence["wav_sha256"],
        "source_script_sha256": V2_SHA,
        "duration_seconds": round(duration, 3),
        "status": adjudication["status"],
        "model_results": models,
        "two_model_adjudication": adjudication,
        "only_preliminary_asr_quality": True,
        "commercial_rights_cleared": False,
        "final_audio_master_approved": False,
        "captions_synced_to_master": False,
        "video_rendered": False,
        "publication_authorized": False,
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Two ASR checks of new E01 v2 WAV")
    p.add_argument("--root", type=Path, default=Path("."))
    p.add_argument("--audio-dir", type=Path, required=True)
    p.add_argument("--model-dir", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    try:
        result = audit(args.root.resolve(),
                       args.audio_dir.resolve(), args.model_dir.resolve())
    except Exception as exc:
        result = {
            "project": "verbo-no-chao", "episode_id": "VNC-W01-E1",
            "candidate_version": 2,
            "status": "BLOCKED_V2_ASR_JOB_NOT_COMPLETED",
            "error_code": str(exc) if isinstance(exc, ProductionError)
                          else type(exc).__name__,
            "commercial_rights_cleared": False,
            "final_audio_master_approved": False,
            "publication_authorized": False,
        }
    out = args.output.resolve(); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n",
                   encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "both_models_recognized_replacement":
            result.get("two_model_adjudication", {}).get(
                "both_models_recognized_exact_replacement"),
        "small_wer": (result.get("model_results") or [{}])[0].get(
            "fidelity_estimates", {}).get("word_error_rate"),
        "master_approved": False,
        "publication_authorized": False,
        "error_code": result.get("error_code"),
    }, ensure_ascii=False))
    return 0 if result["status"] == "ASR_V2_TWO_MODEL_TEXT_TRIAGE_PASS_STILL_QUARANTINED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
