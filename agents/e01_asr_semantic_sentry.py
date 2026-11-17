"""Second, lexical-semantic gate over the REAL independently produced ASR JSON.

Do not confuse small aggregate WER with certainty about key expressions.
This gate evaluates one exactly hashed prior GitHub Actions artifact, requiring
no new ASR model, no audio regeneration, and no owner review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from agents.content_production import ProductionError, check
from agents.e01_asr_qa import tokenize
from agents.e01_voice_preview import approved_source

EXPECTED_REPORT_SHA = "917650006cd03b95ede779efe6b831fc520c9d2eb37d59c63e99c0c4efc2a406"
EXPECTED_REPORT_BYTES = 33248
SCRIPT_SHA = "67052ec614f3beaca25cbac40414eecb7f197be0b73b7c1af4fd6579c0cf6990"

# This is not a grammar judge: missing instances are review signals, not proof
# that the TTS mispronounced the term. ASR may be wrong itself.
CRITICAL_WORDS = (
    "doi", "nao", "ninguem", "deus", "fe", "violencia",
    "injustica", "injusticas", "orar", "oracao", "verdade", "esperanca",
)
INCOMPLETE_ENDING = re.compile(r"\b(de|para|com|sem|em)\s*[.!?](?=\s|$)", re.I)


def validate_original_asr(root: Path, source: Path) -> tuple[dict[str, Any], str]:
    check(source.is_file() and source.stat().st_size == EXPECTED_REPORT_BYTES,
          "asr_semantic:source_report_size")
    with source.open("rb") as f:
        digest = hashlib.file_digest(f, "sha256").hexdigest()
    check(digest == EXPECTED_REPORT_SHA, "asr_semantic:source_report_digest")
    evidence = json.loads(
        (root / "contracts/e01_asr_real_evidence_v1.json").read_text(encoding="utf-8"))
    check(evidence["project"] == "verbo-no-chao"
          and evidence["episode_id"] == "VNC-W01-E1"
          and evidence["source_report_sha256"] == EXPECTED_REPORT_SHA
          and evidence["source_report_bytes"] == EXPECTED_REPORT_BYTES
          and evidence["source_workflow_run_id"] == 44201071884
          and evidence["source_artifact_id"] == 14381047221
          and evidence["source_script_sha256"] == SCRIPT_SHA
          and evidence["critical_semantic_recheck_completed"] is False
          and evidence["voice_rights_cleared"] is False
          and evidence["production_audio_master_approved"] is False
          and evidence["publication_authorized"] is False,
          "asr_semantic:manifest_claims_untrusted")
    report = json.loads(source.read_text(encoding="utf-8"))
    model = report["model"]
    q = report["text_fidelity_estimates"]
    check(report["project"] == "verbo-no-chao"
          and report["episode_id"] == "VNC-W01-E1"
          and report["source_script_sha256"] == SCRIPT_SHA
          and report["status"] == "ASR_PROVISIONAL_SCRIPT_MATCH_QUARANTINED"
          and report["asr_fidelity_provisionally_passed"] is True
          and report["production_audio_master_approved"] is False
          and report["voice_rights_cleared"] is False
          and report["publication_authorized"] is False
          and q["word_edits"] == 5
          and q["expected_words"] == 182
          and q["recognized_words"] == 182
          and q["word_error_rate"] == 0.02747
          and q["character_error_rate"] == 0.0075
          and model["repository"] == evidence["asr_model_repository"]
          and model["repository_revision"] == evidence["asr_model_repo_revision"]
          and model["model_bin_sha256"] == evidence["asr_model_bin_sha256"],
          "asr_semantic:asr_summary_or_model_changed")
    reference, script = approved_source(root)
    check(script["script_sha256"] == SCRIPT_SHA,
          "asr_semantic:script_changed")
    return report, reference


def evaluate_wording(reference: str, recognized: str) -> dict[str, Any]:
    expected, heard = Counter(tokenize(reference)), Counter(tokenize(recognized))
    warnings = []
    for word in CRITICAL_WORDS:
        n_ref, n_asr = expected[word], heard[word]
        if n_ref > n_asr:
            warnings.append({
                "type": "POSSIBLE_CRITICAL_WORD_DISCREPANCY",
                "word": word,
                "script_occurrences": n_ref,
                "asr_occurrences": n_asr,
                "missing_instances": n_ref-n_asr,
                "may_be_recognizer_error": True,
            })
    boundaries = []
    for match in INCOMPLETE_ENDING.finditer(recognized):
        boundaries.append({
            "type": "POSSIBLE_BAD_SENTENCE_BOUNDARY",
            "asr_excerpt": recognized[max(match.start()-40, 0):min(match.end()+55, len(recognized))],
            "may_be_recognizer_punctuation_error": True,
        })
    return {
        "status": (
            "BLOCKED_CRITICAL_WORDING_NEEDS_AUDIO_RECHECK"
            if warnings or boundaries else "NO_CRITICAL_WORDING_ALERTS_IN_THIS_GATE"
        ),
        "critical_word_alerts": warnings,
        "sentence_boundary_alerts": boundaries,
        "number_of_critical_word_alerts": len(warnings),
        "number_of_sentence_boundary_alerts": len(boundaries),
        "tts_defect_proven": False,
        "requires_secondary_evidence_for_disambiguation": bool(warnings or boundaries),
        "automatic_script_review_required_from_owner": False,
        "human_listening_qa_completed": False,
        "voice_rights_cleared": False,
        "production_audio_master_approved": False,
        "publication_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify E01 ASR semantic edge cases")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--input-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        original, reference = validate_original_asr(args.root.resolve(),
                                                     args.input_file.resolve())
        recognized = original["recognition"]["transcript"]
        result = evaluate_wording(reference, recognized)
        result.update({
            "project": "verbo-no-chao",
            "episode_id": "VNC-W01-E1",
            "source_asr_report_sha256": EXPECTED_REPORT_SHA,
            "source_script_sha256": SCRIPT_SHA,
            "aggregate_asr_word_error_rate": 0.02747,
            "aggregate_asr_character_error_rate": 0.0075,
            "asr_aggregate_thresholds_passed": True,
            "source_provenance_sha256_verified": True,
        })
    except Exception as exc:
        result = {
            "project": "verbo-no-chao",
            "episode_id": "VNC-W01-E1",
            "status": "BLOCKED_SEMANTIC_ASR_EVIDENCE_INVALID",
            "source_provenance_sha256_verified": False,
            "error_code": str(exc) if isinstance(exc, ProductionError)
                          else type(exc).__name__,
            "publication_authorized": False,
            "production_audio_master_approved": False,
        }
    dest = args.output.resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n",
                    encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "source_verified": result["source_provenance_sha256_verified"],
        "critical_alerts": result.get("number_of_critical_word_alerts"),
        "boundary_alerts": result.get("number_of_sentence_boundary_alerts"),
        "production_master_approved": False,
        "publication_authorized": False,
        "error_code": result.get("error_code"),
    }, ensure_ascii=False))
    return 2 if result["status"] == "BLOCKED_SEMANTIC_ASR_EVIDENCE_INVALID" else 0


if __name__ == "__main__":
    raise SystemExit(main())
