"""Fail-closed preparation for a *possible* audio build. Never invokes TTS.

This report deliberately remains BLOCKED until editorial approval and exact
voice-pack/runtime license evidence are available. Files are proposals only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from agents.content_production import ProductionError, check, read

TARGET_ID = "VNC-W01-E1"
TARGET_REFERENCE = "Habacuque 1:2-4"
EXPECTED_BLOCKS = (
    "opening", "connection", "biblical_reference",
    "reflection", "application", "conclusion",
)
REQUIRED_BLOCKERS = (
    "script_owner_approval_pending",
    "independent_biblical_review_pending",
    "exact_voice_pack_sha256_missing",
    "exact_voice_pack_commercial_rights_pending",
    "runtime_service_terms_unverified",
    "voice_audio_not_generated",
)


def validate_voice_evidence(value: Any) -> None:
    check(isinstance(value, dict) and value.get("project") == "verbo-no-chao",
          "voice_evidence:project")
    check(value.get("model_upstream") == "hexgrad/Kokoro-82M"
          and value.get("engine") == "Kokoro-82M"
          and value.get("model_license") == "Apache-2.0"
          and value.get("model_license_status") == "UPSTREAM_DECLARATION_VERIFIED",
          "voice_evidence:model_provenance")
    check(value.get("upstream_voice_name") == "pm_alex"
          and value.get("language") == "pt-BR"
          and value.get("upstream_voice_registry_hash_prefix") == "cf0ba8c5",
          "voice_evidence:voice_identity")
    check(value.get("upstream_voice_pack_full_sha256") is None
          and value.get("voice_pack_bytes_verified") is False
          and value.get("voice_pack_commercial_rights_status") ==
          "PENDING_EXACT_PACK_LICENSE_AND_ATTRIBUTION_AUDIT",
          "voice_evidence:unsupported_license_or_hash_claim")
    check(value.get("runtime_terms_checked") is False
          and value.get("runtime_license_status") == "PENDING_SERVICE_TERMS_AND_DEPENDENCY_REVIEW"
          and value.get("commercial_audio_status") == "BLOCKED",
          "voice_evidence:runtime_license_not_verified")
    check(value.get("publication_authorized") is False
          and value.get("final_approval") is False,
          "voice_evidence:publication_lock")
    for k in ("model_license_evidence", "official_voice_registry", "official_voice_file_listing"):
        url = value.get(k)
        check(isinstance(url, str) and url.startswith("https://huggingface.co/hexgrad/Kokoro-82M"),
              f"voice_evidence:untrusted_url:{k}")


def validate_input(package: Any, report: Any, voice: Any) -> dict[str, Any]:
    validate_voice_evidence(voice)
    check(isinstance(package, dict)
          and package.get("project") == "verbo-no-chao"
          and package.get("status") == "DRAFT_REVIEW_REQUIRED"
          and package.get("publication_authorized") is False
          and package.get("owner_approval") is False
          and package.get("contextual_review_status") == "PENDING_INDEPENDENT_REVIEW",
          "audio_preflight:first_batch_not_draft")
    check(isinstance(report, dict)
          and report.get("project") == "verbo-no-chao"
          and report.get("status") == "FIRST_THREE_DRAFTS_GENERATED_REVIEW_REQUIRED"
          and report.get("publication_authorized") is False,
          "audio_preflight:upstream_report_invalid")
    scripts = package.get("scripts")
    checks = package.get("automated_checks")
    check(isinstance(scripts, list) and len(scripts) == 3
          and isinstance(checks, list) and len(checks) == 3,
          "audio_preflight:three_drafts_missing")
    script = scripts[0]
    audit = checks[0]
    check(isinstance(script, dict) and isinstance(audit, dict)
          and script.get("episode_id") == TARGET_ID and audit.get("episode_id") == TARGET_ID
          and script.get("reference") == TARGET_REFERENCE,
          "audio_preflight:target_script_changed")
    check(script.get("status") == "DRAFT_REVIEW_REQUIRED"
          and script.get("biblical_review_status") == "PENDING_INDEPENDENT_REVIEW"
          and script.get("owner_approval") is False
          and script.get("publication_authorized") is False
          and script.get("contains_verbatim_quote") is False
          and script.get("source_mode") == "reference_and_paraphrase",
          "audio_preflight:script_approval_or_source_changed")
    check(audit.get("automated_review") == "PASS_AUTOMATED_REVIEW"
          and audit.get("status") == "DRAFT_REVIEW_REQUIRED"
          and audit.get("publication_authorized") is False,
          "audio_preflight:automated_review_missing")
    blocks = script.get("blocks")
    check(isinstance(blocks, list) and len(blocks) == 6
          and tuple(b.get("type") for b in blocks if isinstance(b, dict)) == EXPECTED_BLOCKS,
          "audio_preflight:script_blocks_changed")
    check(all(isinstance(b.get("text"), str) and b["text"].strip() for b in blocks),
          "audio_preflight:empty_block")
    narration = " ".join(b["text"] for b in blocks)
    fingerprint = hashlib.sha256(re.sub(r"\s+", " ", narration.casefold()).encode("utf-8")).hexdigest()
    check(audit.get("original_script_sha256") == fingerprint,
          "audio_preflight:canonical_narration_hash_mismatch")
    check(isinstance(audit.get("estimated_seconds"), (int, float))
          and 63.75 <= audit["estimated_seconds"] <= 86.25,
          "audio_preflight:estimated_duration_invalid")
    return {"script": script, "audit": audit, "narration_sha256": fingerprint}


def produce(root: Path, upstream_dir: Path, out_dir: Path) -> dict[str, Any]:
    root, upstream_dir, out_dir = root.resolve(), upstream_dir.resolve(), out_dir.resolve()
    check(not any(out_dir.is_relative_to(root / x) for x in ("agents", "contracts", "docs", "tests")),
          "audio_preflight:protected_output_directory")
    evidence: dict[str, str] = {}
    voice = read(root, "contracts/kokoro_voice_research_v1.json", evidence)
    package = read(upstream_dir, "operations/first_batch_scripts.json", evidence)
    report = read(upstream_dir, "editorial-deliveries/first_batch_report.json", evidence)
    check(isinstance(report, dict) and isinstance(report.get("files"), list),
          "audio_preflight:upstream_hash_report_missing")
    upstream = next((x for x in report["files"] if isinstance(x, dict) and
                     x.get("path") == "operations/first_batch_scripts.json"), None)
    check(isinstance(upstream, dict) and
          upstream.get("sha256") == evidence["operations/first_batch_scripts.json"],
          "audio_preflight:script_package_sha256_mismatch")
    proof = validate_input(package, report, voice)
    script = proof["script"]
    audit = proof["audit"]
    result = {
        "schema_version": "1.0.0",
        "project": "verbo-no-chao",
        "episode_id": TARGET_ID,
        "script_id": script["script_id"],
        "reference": TARGET_REFERENCE,
        "status": "BLOCKED",
        "stage": "AUDIO_PREFLIGHT_ONLY",
        "script_review_status": "DRAFT_REVIEW_REQUIRED",
        "biblical_context_status": "PENDING_INDEPENDENT_REVIEW",
        "voice_selection_scope": "PREVIEW_BASELINE_NOT_COMMERCIAL_RELEASE",
        "voice": {
            "engine": "Kokoro-82M",
            "voice_id": "pm_alex", "language": "pt-BR",
            "sample_rate_hz_planned": 24000,
            "engine_license_evidence": voice["model_license_evidence"],
            "upstream_voice_catalog": voice["official_voice_registry"],
            "voice_pack_sha256": None,
            "commercial_rights": "PENDING_EXACT_PACK_LICENSE_AND_ATTRIBUTION_AUDIT",
            "runtime_license": "PENDING_SERVICE_TERMS_AND_DEPENDENCY_REVIEW",
        },
        "narration": {
            "source": "operations/first_batch_scripts.json",
            "canonical_sha256": proof["narration_sha256"],
            "word_count": audit["word_count"],
            "estimated_seconds": audit["estimated_seconds"],
            "segments": [{"index": i, "block_type": b["type"], "text": b["text"],
                          "sha256": hashlib.sha256(b["text"].encode("utf-8")).hexdigest()}
                         for i, b in enumerate(script["blocks"], 1)],
            "audio_file": None,
            "audio_generated": False,
        },
        "blockers": list(REQUIRED_BLOCKERS),
        "rights_cleared": False,
        "owner_approval": False,
        "publication_authorized": False,
        "evidence_sha256": evidence,
        "next_required_gate": "independent_biblical_editorial_and_exact_voice_runtime_license_review",
    }
    md = [
        "# VERBO NO CHÃO — Pré-voo do áudio 01",
        "", "**BLOQUEADO: pacote de preparação, NÃO áudio produzido nem autorizado.**",
        "", "Referência: **Habacuque 1:2-4**.",
        f"Voz candidata preservada: **pm_alex** / Kokoro-82M / pt-BR.",
        f"Estimativa automatizada: **{audit['estimated_seconds']} s**, não medição de áudio.",
        "", "## O que já está demonstrado", "",
        "- A voz pm_alex aparece no catálogo oficial da upstream do modelo.",
        "- A upstream do modelo declara licença Apache-2.0.",
        "- Os seis blocos do rascunho foram preservados literalmente em ordem e hasheados.",
        "- O hash do pacote gerado é conferido com o relatório de produção anterior.",
        "", "## O que permanece bloqueado", "",
        "- O roteiro não passou por revisão bíblica independente nem aprovação do proprietário.",
        "- Falta o hash integral de um pack de voz realmente recebido e sua cadeia de licença/avisos.",
        "- Faltam os termos do runtime hospedado usado para sintetizar áudio, inclusive uso comercial.",
        "- Não houve geração de WAV, renderização, agendamento ou publicação.",
        "", "## Segmentos prontos para futura revisão", "",
    ]
    for seg in result["narration"]["segments"]:
        md.extend([f"### {seg['index']} — {seg['block_type']}", seg["text"], ""])
    md.extend(["## Próxima decisão", "",
               "Revisão contextual humana do roteiro e evidências específicas da voz/serviço, antes de iniciar o TTS.",
               "Um selo 'Apache-2.0' do modelo não substitui auditoria do serviço, de dependências e de reprodução comercial.",
               ""])
    def dump(data: Any) -> str:
        return json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    def write(rel: str, content: str) -> dict[str, str]:
        path = (out_dir / rel).resolve()
        check(path.is_relative_to(out_dir), "audio_preflight:output_path_escape")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return {"path": rel, "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest()}
    files = [
        write("audio-preflight/preflight.json", dump(result)),
        write("audio-preflight/preflight.md", "\n".join(md)),
    ]
    summary = {
        "schema_version": "1.0.0", "project": "verbo-no-chao",
        "episode_id": TARGET_ID, "status": "BLOCKED",
        "stage": "AUDIO_PREFLIGHT_ONLY",
        "files": files, "blockers": list(REQUIRED_BLOCKERS),
        "voice_license_approved": False,
        "audio_generated": False,
        "publication_authorized": False,
    }
    write("audio-preflight/report.json", dump(summary))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail-closed audio preflight for first script")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--upstream-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        outcome = produce(args.root, args.upstream_dir, args.output_dir)
    except (ProductionError, TypeError, KeyError, ValueError, OSError) as exc:
        parser.exit(1, f"BLOCKED: invalid preflight inputs: {exc}\n")
    print(json.dumps({k: outcome[k] for k in ("episode_id", "status", "audio_generated", "blockers")}))
    return 0  # Preparation ran successfully; audio remains blocked by design.


if __name__ == "__main__":
    raise SystemExit(main())
