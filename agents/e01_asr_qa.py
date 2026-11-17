"""Independent ASR on a physically verified E01 WAV; no rights or release promotion.

Only transcribes the pinned 70.075-second private preview downloaded from an
earlier GitHub Actions artifact. An ASR comparison is evidence of likely
fidelity, NOT a perfect listener, a final caption track, or an audio master.
The model is downloaded at one immutable Hugging Face commit per run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import unicodedata
import wave
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from agents.content_production import ProductionError, check
from agents.e01_voice_preview import approved_source

REPO = "Systran/faster-whisper-small"
ASR_BACKEND = "faster-whisper==1.2.1"
SCRIPT_HASH = "67052ec614f3beaca25cbac40414eecb7f197be0b73b7c1af4fd6579c0cf6990"
WAV_SHA = "f7c18eac3b8ebc59069665d5e633d8ace1c342efd34546e0591cb7dd713a05d4"
REPORT_SHA = "a11f144722de64a1cd096deb460a21522104ba09cd4572bf13cc61a64c570686"
WAV_BYTES = 3363644
REPORT_BYTES = 2262
DURATION = 70.075
MAX_WORDS = 900
MAX_SEGMENTS = 140
MAX_WORD_ERROR_RATE = 0.13
MAX_CHAR_ERROR_RATE = 0.08
MAX_POTENTIAL_OMITTED_WORDS = 6


def sha256_file(path: Path) -> str:
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def tokenize(text: str) -> list[str]:
    check(isinstance(text, str) and len(text) <= 6000, "asr:invalid_text")
    clean = "".join(
        c for c in unicodedata.normalize("NFKD", text.casefold())
        if not unicodedata.combining(c)
    )
    clean = re.sub(r"[^a-z0-9]+", " ", clean)
    return clean.split()


def edit_distance(a: list[str] | str, b: list[str] | str) -> int:
    """True Levenshtein distance (WER/CER), not a loose token similarity."""
    if len(a) > len(b):
        a, b = b, a
    previous = list(range(len(a) + 1))
    for y, char_b in enumerate(b, start=1):
        current = [y]
        for x, char_a in enumerate(a, start=1):
            current.append(min(
                current[x-1] + 1,
                previous[x] + 1,
                previous[x-1] + (char_a != char_b),
            ))
        previous = current
    return previous[-1]


def compare_text(expected: str, recognized: str) -> dict[str, Any]:
    ref, hyp = tokenize(expected), tokenize(recognized)
    check(30 <= len(ref) <= MAX_WORDS, "asr:reference_length_invalid")
    check(1 <= len(hyp) <= MAX_WORDS, "asr:hypothesis_empty_or_oversize")
    wer_edits = edit_distance(ref, hyp)
    ref_chars = " ".join(ref)
    hyp_chars = " ".join(hyp)
    char_edits = edit_distance(ref_chars, hyp_chars)
    potential_omissions = []
    for op, ai, aj, bi, bj in SequenceMatcher(
        a=ref, b=hyp, autojunk=False
    ).get_opcodes():
        if op not in ("replace", "delete"):
            continue
        count = aj - ai
        if count >= 2:
            potential_omissions.append({
                "reference_word_start": ai,
                "reference_word_end_exclusive": aj,
                "potential_missing_words": count,
                "reference_excerpt": " ".join(ref[ai:aj])[:240],
                "asr_corresponding_excerpt": " ".join(hyp[bi:bj])[:240],
                "difference_kind": op,
            })
    worst = max((x["potential_missing_words"] for x in potential_omissions),
                default=0)
    wer = round(wer_edits / len(ref), 5)
    cer = round(char_edits / len(ref_chars), 5)
    return {
        "expected_words": len(ref),
        "recognized_words": len(hyp),
        "word_edits": wer_edits,
        "character_edits": char_edits,
        "word_error_rate": wer,
        "character_error_rate": cer,
        "word_error_limit": MAX_WORD_ERROR_RATE,
        "character_error_limit": MAX_CHAR_ERROR_RATE,
        "worst_potential_omission_words": worst,
        "potential_discrepancies": potential_omissions[:25],
        "thresholds_passed": (
            wer <= MAX_WORD_ERROR_RATE
            and cer <= MAX_CHAR_ERROR_RATE
            and worst <= MAX_POTENTIAL_OMITTED_WORDS
        ),
    }


def validate_timecodes(segments: list[dict[str, Any]],
                       duration: float) -> dict[str, Any]:
    check(isinstance(segments, list)
          and 1 <= len(segments) <= MAX_SEGMENTS, "asr:segments_missing")
    check(math.isfinite(duration) and duration == DURATION,
          "asr:source_duration_not_pinned")
    previous_start = -1.0
    words_count = 0
    low_prob_words = 0
    for seg in segments:
        check(isinstance(seg, dict)
              and isinstance(seg.get("text"), str)
              and seg["text"].strip()
              and isinstance(seg.get("start"), (int, float))
              and isinstance(seg.get("end"), (int, float)),
              "asr:malformed_segment")
        a, b = float(seg["start"]), float(seg["end"])
        check(math.isfinite(a) and math.isfinite(b)
              and -0.02 <= a <= b <= duration + 0.5
              and a + 0.1 >= previous_start,
              "asr:invalid_segment_time")
        previous_start = a
        for w in seg.get("words", []):
            check(isinstance(w, dict) and isinstance(w.get("word"), str)
                  and w["word"].strip()
                  and isinstance(w.get("start"), (int, float))
                  and isinstance(w.get("end"), (int, float))
                  and isinstance(w.get("probability"), (int, float)),
                  "asr:invalid_word")
            wstart, wend = float(w["start"]), float(w["end"])
            prob = float(w["probability"])
            check(math.isfinite(wstart) and math.isfinite(wend)
                  and -0.02 <= wstart <= wend <= duration + 0.5
                  and math.isfinite(prob) and 0 <= prob <= 1,
                  "asr:invalid_word_timing_or_probability")
            words_count += 1
            low_prob_words += int(prob < 0.45)
    check(15 <= words_count <= MAX_WORDS,
          "asr:word_level_timecodes_missing")
    return {
        "segments_with_timecodes": len(segments),
        "words_with_timecodes": words_count,
        "low_probability_words": low_prob_words,
        "word_timecodes_structurally_valid": True,
        "synced_final_caption_track": False,
    }


def check_source(root: Path, folder: Path) -> tuple[Path, str]:
    wav = (folder / "e01-preview-only.wav").resolve()
    source = (folder / "report.json").resolve()
    check(wav.is_relative_to(folder.resolve())
          and source.is_relative_to(folder.resolve())
          and wav.is_file() and source.is_file(),
          "asr:source_artifact_missing")
    check(wav.stat().st_size == WAV_BYTES
          and source.stat().st_size == REPORT_BYTES
          and sha256_file(wav) == WAV_SHA
          and sha256_file(source) == REPORT_SHA,
          "asr:source_artifact_sha256_or_size_mismatch")
    evidence = json.loads(
        (root / "contracts/e01_real_voice_preview_evidence_v1.json").read_text(
            encoding="utf-8"))
    check(evidence["normalized_preview_sha256"] == WAV_SHA
          and evidence["canonical_script_sha256"] == SCRIPT_HASH
          and evidence["source_report_sha256"] == REPORT_SHA
          and evidence["source_workflow_run_id"] == 44192226678
          and evidence["full_voice_license_clearance"] is False
          and evidence["publication_authorized"] is False,
          "asr:source_manifest_inconsistent")
    report = json.loads(source.read_text(encoding="utf-8"))
    check(report["status"] ==
          "QUARANTINED_WAV_PREVIEW_GENERATED_NOT_RELEASE_CLEARED"
          and report["source_script_sha256"] == SCRIPT_HASH
          and report["physical_wav_metrics"]["sha256"] == WAV_SHA
          and report["rights_cleared"] is False
          and report["publication_authorized"] is False,
          "asr:untrusted_audio_report")
    with wave.open(str(wav), "rb") as reader:
        check(reader.getnchannels() == 1
              and reader.getsampwidth() == 2
              and reader.getframerate() == 24000
              and abs(reader.getnframes()/reader.getframerate() - DURATION) < 0.001,
              "asr:source_pcm_shape_mismatch")
    text, editorial = approved_source(root)
    check(editorial["script_sha256"] == SCRIPT_HASH,
          "asr:reviewed_text_changed")
    return wav, text


def safe_stage_error(stage: str, exc: Exception) -> ProductionError:
    """Reveal only coarse public backend failure signatures; never tokens/URLs."""
    message = str(exc).casefold()
    if "unable to open file" in message or "no such file" in message:
        category = "MODEL_FILE_UNAVAILABLE"
    elif "invalid model" in message or "unsupported model" in message:
        category = "MODEL_FORMAT_UNSUPPORTED"
    elif "int8" in message or "compute type" in message:
        category = "COMPUTE_BACKEND_UNSUPPORTED"
    elif "memory" in message:
        category = "MEMORY_RESOURCE"
    elif "connection" in message or "timeout" in message:
        category = "REMOTE_ACCESS"
    elif "not implemented" in message or "missing feature" in message:
        category = "BACKEND_FEATURE"
    else:
        category = "OTHER"
    return ProductionError(f"asr:{stage}:{category}:{type(exc).__name__}")


def run_independent_asr(wav: Path, model_root: Path) -> tuple[
        list[dict[str, Any]], dict[str, Any]]:
    # Download only public licensed ASR weights. Resolve their exact commit first
    # so a changing "main" cannot silently change the evaluated model mid-job.
    from huggingface_hub import HfApi, snapshot_download
    from faster_whisper import WhisperModel
    try:
        info = HfApi().model_info(REPO)
    except Exception as exc:
        raise safe_stage_error("hub_metadata", exc) from exc
    revision = info.sha
    check(isinstance(revision, str)
          and bool(re.fullmatch(r"[a-f0-9]{40}", revision)),
          "asr:model_revision_unpinned")
    try:
        model_dir = snapshot_download(
            repo_id=REPO, revision=revision,
            allow_patterns=["*.bin", "*.json"],
            local_dir=str(model_root),
        )
    except Exception as exc:
        raise safe_stage_error("snapshot_download", exc) from exc
    binary = Path(model_dir)/"model.bin"
    check(binary.is_file()
          and 100_000_000 < binary.stat().st_size < 800_000_000,
          "asr:model_binary_missing_or_wrong_size")
    model_sha = sha256_file(binary)
    try:
        model = WhisperModel(
            str(model_dir), device="cpu", compute_type="int8",
            cpu_threads=4, num_workers=1,
        )
    except Exception as exc:
        raise safe_stage_error("model_load", exc) from exc
    try:
        segments_iter, info = model.transcribe(
            str(wav), language="pt", task="transcribe",
            beam_size=5, temperature=0.0, word_timestamps=True,
            vad_filter=False, condition_on_previous_text=False,
        )
    except Exception as exc:
        raise safe_stage_error("transcribe_call", exc) from exc
    segments: list[dict[str, Any]] = []
    try:
        for seg in segments_iter:
            check(len(segments) < MAX_SEGMENTS, "asr:too_many_segments")
            words = [
                {"start": round(float(w.start), 3),
                 "end": round(float(w.end), 3),
                 "word": w.word,
                 "probability": round(float(w.probability), 5)}
                for w in (seg.words or [])
            ]
            segments.append({
                "start": round(float(seg.start), 3),
                "end": round(float(seg.end), 3),
                "text": str(seg.text),
                "avg_logprob": round(float(seg.avg_logprob), 5),
                "words": words,
            })
    except ProductionError:
        raise
    except Exception as exc:
        raise safe_stage_error("transcribe_stream", exc) from exc
    return segments, {
        "backend": ASR_BACKEND, "repository": REPO,
        "repository_revision": revision,
        "model_bin_sha256": model_sha,
        "model_bin_bytes": binary.stat().st_size,
        "license_declared": "MIT",
        "cpu_compute_type": "int8",
        "model_language_parameter": "pt",
        "language_detected_independently": False,
        "vad_filter": False, "beam_size": 5,
        "condition_on_previous_text": False,
        "initial_prompt_used": False,
    }


def audit(root: Path, input_dir: Path, model_dir: Path) -> dict[str, Any]:
    wav, original = check_source(root, input_dir)
    segments, model = run_independent_asr(wav, model_dir)
    timecodes = validate_timecodes(segments, DURATION)
    transcript = " ".join(s["text"].strip() for s in segments)
    quality = compare_text(original, transcript)
    passed = quality["thresholds_passed"]
    return {
        "schema_version": "1.0.0",
        "project": "verbo-no-chao",
        "episode_id": "VNC-W01-E1",
        "status": ("ASR_PROVISIONAL_SCRIPT_MATCH_QUARANTINED"
                   if passed else "BLOCKED_ASR_DISCREPANCIES"),
        "qa_scope": "INDEPENDENT_ASR_ESTIMATE_NOT_HUMAN_LISTENING",
        "source_wav_sha256": WAV_SHA,
        "source_script_sha256": SCRIPT_HASH,
        "source_report_sha256": REPORT_SHA,
        "duration_seconds": DURATION,
        "model": model,
        "recognition": {
            "transcript": transcript, "timed_segments": segments,
            "reference_transcription_supplied_as_prompt": False,
            "asr_is_not_ground_truth": True,
        },
        "text_fidelity_estimates": quality,
        "timing_structure": timecodes,
        "asr_fidelity_provisionally_passed": bool(passed),
        "human_listening_completed": False,
        "pronunciation_quality_fully_cleared": False,
        "final_caption_sync_approved": False,
        "voice_rights_cleared": False,
        "production_audio_master_approved": False,
        "rendered_final_video_exists": False,
        "publication_authorized": False,
        "blockers": [
            *([] if passed else ["potential_omissions_or_asr_errors_require_correction"]),
            "human_equivalent_pronunciation_and_prosody_QA_not_proven",
            "exact_voice_runtime_and_commercial_rights_not_fully_cleared",
            "visual_music_caption_and_decoded_master_not_produced",
            "explicit_publication_authorization_not_given",
        ],
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Verify and ASR-check an existing E01 WAV")
    p.add_argument("--root", type=Path, default=Path("."))
    p.add_argument("--input-dir", type=Path, required=True)
    p.add_argument("--model-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--verify-input-only", action="store_true")
    args = p.parse_args()
    root = args.root.resolve()
    folder = args.input_dir.resolve()
    out = args.output_dir.resolve()
    if args.verify_input_only:
        wav, txt = check_source(root, folder)
        print(json.dumps({"input_sha256_verified": True,
                          "script_sha256": SCRIPT_HASH,
                          "wav_size": wav.stat().st_size,
                          "script_characters": len(txt)}))
        return 0
    out.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any]
    try:
        report = audit(root, folder, args.model_dir.resolve())
    except Exception as exc:
        # A failed ASR load, corrupted file, missing model or broken timing
        # must NEVER become a positive audio QA receipt.
        report = {
            "project": "verbo-no-chao",
            "episode_id": "VNC-W01-E1",
            "status": "BLOCKED_ASR_AUDIT_NOT_COMPLETED",
            "source_wav_sha256": WAV_SHA,
            "source_script_sha256": SCRIPT_HASH,
            "error_code": str(exc) if isinstance(exc, ProductionError)
                          else type(exc).__name__,
            "asr_fidelity_provisionally_passed": False,
            "human_listening_completed": False,
            "voice_rights_cleared": False,
            "production_audio_master_approved": False,
            "publication_authorized": False,
        }
    (out / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": report["status"],
        "wer": report.get("text_fidelity_estimates", {}).get("word_error_rate"),
        "cer": report.get("text_fidelity_estimates", {}).get("character_error_rate"),
        "segments": report.get("timing_structure", {}).get("segments_with_timecodes"),
        "asr_provisionally_passed": report["asr_fidelity_provisionally_passed"],
        "production_audio_master_approved": False,
        "publication_authorized": False,
        "error_code": report.get("error_code"),
    }, ensure_ascii=False))
    return 0 if report["status"] == "ASR_PROVISIONAL_SCRIPT_MATCH_QUARANTINED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
