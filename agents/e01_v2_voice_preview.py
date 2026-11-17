"""Generate a single quarantined REAL v2 E01 narration with isolated script.

This is an independent candidate: no mutation of v1 WAV, original editorial
approval, main, bootstrap, pilot Salmo 13, publisher or media contracts.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from agents.content_production import ProductionError, check
from agents.e01_v2_candidate import approved_v2, V2_SHA, PARENT_SHA, OLD, NEW
from agents.e01_voice_preview import (
    synthesize_browser, inspect_pcm_wav, MAX_WAIT_SECONDS,
)
from agents.wav_normalization import normalize_riff_wav

OUTPUT_NAME = "e01-v2-preview-only.wav"


def generate(root: Path, output_dir: Path, max_seconds: int = 475) -> dict[str, Any]:
    check(60 <= max_seconds <= MAX_WAIT_SECONDS,
          "e01v2:execution_budget")
    root, output_dir = root.resolve(), output_dir.resolve()
    check(not output_dir.is_relative_to(root / "agents")
          and not output_dir.is_relative_to(root / "contracts")
          and not output_dir.is_relative_to(root / "docs"),
          "e01v2:protected_output_path")
    output_dir.mkdir(parents=True, exist_ok=True)
    wav_path = output_dir / OUTPUT_NAME
    wav_path.unlink(missing_ok=True)
    report: dict[str, Any] = {
        "schema_version": "1.0.0",
        "project": "verbo-no-chao",
        "episode_id": "VNC-W01-E1",
        "candidate_version": 2,
        "candidate_script_sha256": V2_SHA,
        "original_script_sha256": PARENT_SHA,
        "old_phrase": OLD,
        "replacement_phrase": NEW,
        "voice_id": "pm_alex",
        "language": "pt-BR",
        "status": "BLOCKED_E01_V2_WAV_NOT_PROVEN",
        "audio_preview_saved": False,
        "production_audio_master_approved": False,
        "voice_runtime_rights_cleared": False,
        "listening_qa_completed": False,
        "independent_asr_completed_for_v2": False,
        "video_rendered": False,
        "publication_authorized": False,
        "blockers": [
            "asr_and_pronunciation_validation_required_for_new_wav",
            "full_voice_runtime_rights_pending",
            "visual_music_captions_and_master_pending",
            "separate_publication_permission_required",
        ],
    }
    try:
        script_text, editorial = approved_v2(root)
        check(editorial["script_sha256"] == V2_SHA
              and editorial["review_file_ref"] ==
                  "contracts/e01_ai_editorial_review_v2.json"
              and editorial["publication_authorized"] is False,
              "e01v2:editorial_receipt_not_confirmed")
        raw, cache = synthesize_browser(script_text, max_seconds=max_seconds)
        pcm, conversion = normalize_riff_wav(raw)
        metrics = inspect_pcm_wav(pcm)
        check(cache["observed_in_same_browser_session"] is True
              and cache["effective_inference_consumption_proven"] is False,
              "e01v2:cache_unsupported_claim")
        wav_path.write_bytes(pcm)
        report.update({
            "status": "QUARANTINED_E01_V2_WAV_PHYSICALLY_VERIFIED",
            "audio_preview_saved": True,
            "audio_preview_file": OUTPUT_NAME,
            "physical_wav_metrics": metrics,
            "input_wav_format": conversion,
            "browser_voice_cache": cache,
            "github_sha": os.environ.get("GITHUB_SHA"),
            "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        })
    except Exception as exc:
        wav_path.unlink(missing_ok=True)
        report["status"] = "BLOCKED_E01_V2_WAV_NOT_PROVEN"
        report["error_code"] = (
            str(exc) if isinstance(exc, ProductionError)
            else type(exc).__name__
        )
    (output_dir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2)+"\n",
        encoding="utf-8",
    )
    return report


def main() -> int:
    p = argparse.ArgumentParser(description="Quarantined E01 v2 audio only")
    p.add_argument("--root", type=Path, default=Path("."))
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--max-seconds", type=int, default=475)
    args = p.parse_args()
    report = generate(args.root, args.output_dir, args.max_seconds)
    print(json.dumps({
        "status": report["status"],
        "candidate_script_sha256": report["candidate_script_sha256"],
        "source_parent_sha256": report["original_script_sha256"],
        "preview_generated": report["audio_preview_saved"],
        "duration_seconds": report.get("physical_wav_metrics", {}).get("duration_seconds"),
        "bytes": report.get("physical_wav_metrics", {}).get("bytes"),
        "voice_rights_cleared": False,
        "production_audio_master_approved": False,
        "publication_authorized": False,
        "error_code": report.get("error_code"),
    }, ensure_ascii=False))
    return 0 if report["audio_preview_saved"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
