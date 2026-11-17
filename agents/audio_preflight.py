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
from agents.e01_context_review import validate_context_crosscheck
from agents.controlled_smoke_evidence import validate_smoke_attestation
from agents.e01_rights_handoff import verify_dossier, render_human_review_packet
from agents.onnx_byte_audit import validate_report as validate_onnx_report, EXPECTED_SHA256 as ONNX_EXPECTED_SHA256

TARGET_ID = "VNC-W01-E1"
TARGET_REFERENCE = "Habacuque 1:2-4"
EXPECTED_BLOCKS = (
    "opening", "connection", "biblical_reference",
    "reflection", "application", "conclusion",
)
REQUIRED_BLOCKERS = (
    "script_owner_approval_pending",
    "independent_biblical_review_pending",
    "hosted_inference_voice_asset_consumption_unverified",
    "exact_voice_pack_commercial_rights_pending",
    "runtime_dependency_notices_unverified",
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
    check(
        value.get("upstream_voice_pack_full_sha256") ==
        "cf0ba8c573c2480fc54123683a35cf1e2ae130428e441eb91f9149bdb188a526"
        and value.get("upstream_voice_pack_sha256_provenance") ==
        "UPSTREAM_HF_FILE_PAGE_METADATA_NOT_INDEPENDENT_BYTE_HASH"
        and value.get("voice_pack_bytes_verified") is False
        and value.get("hosted_voice_pack_bytes_verified") is False
        and value.get("hosted_voice_pack_sha256") is None
        and value.get("voice_pack_commercial_rights_status") ==
        "PENDING_EXACT_PACK_LICENSE_AND_ATTRIBUTION_AUDIT",
        "voice_evidence:unsupported_license_or_hash_claim",
    )
    check(
        value.get("runtime_terms_checked") is True
        and value.get("runtime_terms_url") == "https://kokoroweb.app/terms"
        and value.get("runtime_terms_last_updated") == "2026-10-30"
        and value.get("runtime_terms_reviewed_on") == "2026-11-17"
        and value.get("runtime_license_status") ==
        "HOST_COMMERCIAL_NARRATION_CONDITIONALLY_ALLOWED"
        and value.get("commercial_audio_status") ==
        "BLOCKED_PENDING_EXACT_HOST_ASSET_IDENTITY_AND_SCRIPT_APPROVAL"
        and value.get("service_resale_or_commercial_rendering_permission") ==
        "TERMS_PERMIT_NARRATION_IN_PERSONAL_OR_COMMERCIAL_PROJECTS_CONDITIONAL_ON_RIGHTS"
        and value.get("runtime_execution_type") ==
        "IN_BROWSER_CLIENT_SIDE_BROWSER_COMPUTE_NOT_REMOTE_API",
        "voice_evidence:runtime_license_not_verified",
    )
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


def produce(root: Path, upstream_dir: Path, out_dir: Path, *, onnx_audit: Path | None = None) -> dict[str, Any]:
    root, upstream_dir, out_dir = root.resolve(), upstream_dir.resolve(), out_dir.resolve()
    check(not any(out_dir.is_relative_to(root / x) for x in ("agents", "contracts", "docs", "tests")),
          "audio_preflight:protected_output_directory")
    evidence: dict[str, str] = {}
    voice = read(root, "contracts/kokoro_voice_research_v1.json", evidence)
    editorial_crosscheck = read(root, "contracts/e01_editorial_crosscheck_v1.json", evidence)
    historical_smoke = read(root, "contracts/kokoro_controlled_smoke_evidence_v1.json", evidence)
    rights_dossier = read(root, "contracts/e01_rights_review_dossier_v1.json", evidence)
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
    crosscheck_result = validate_context_crosscheck(
        editorial_crosscheck, script, proof["narration_sha256"]
    )
    historical_smoke_verified = validate_smoke_attestation(historical_smoke)
    rights_handoff = verify_dossier(
        rights_dossier, editorial_crosscheck, historical_smoke,
        voice, script, proof["narration_sha256"]
    )
    human_review_md = render_human_review_packet(
        script, rights_handoff, rights_dossier, editorial_crosscheck
    )
    onnx_result = None
    if onnx_audit is not None:
        report_path = onnx_audit.resolve()
        check(report_path.is_file(), "audio_preflight:onnx_report_missing")
        raw_onnx = report_path.read_bytes()
        check(len(raw_onnx) <= 100000, "audio_preflight:onnx_report_oversize")
        try:
            onnx_result = json.loads(raw_onnx)
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ProductionError("audio_preflight:onnx_report_invalid") from exc
        validate_onnx_report(onnx_result)
        evidence["voice-asset-audit/report.json"] = hashlib.sha256(raw_onnx).hexdigest()
    onnx_upstream_verified = onnx_result is not None and onnx_result["upstream_bytes_verified"] is True
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
        "internal_editorial_source_crosscheck": crosscheck_result,
        "historical_short_technical_smoke": historical_smoke_verified,
        "rights_and_editorial_handoff": rights_handoff,
        "voice_selection_scope": "PREVIEW_BASELINE_NOT_COMMERCIAL_RELEASE",
        "voice": {
            "engine": "Kokoro-82M",
            "voice_id": "pm_alex", "language": "pt-BR",
            "sample_rate_hz_planned": 24000,
            "engine_license_evidence": voice["model_license_evidence"],
            "upstream_voice_catalog": voice["official_voice_registry"],
            "upstream_voice_pack_sha256_from_repo_metadata": voice["upstream_voice_pack_full_sha256"],
            "upstream_pack_bytes_independently_verified": False,
            "upstream_onnx_voice_format": "pm_alex.bin",
            "upstream_onnx_sha256_expected": ONNX_EXPECTED_SHA256,
            "upstream_onnx_bytes_verified": onnx_upstream_verified,
            "upstream_onnx_bytes_sha256": (onnx_result["actual_sha256"] if onnx_upstream_verified else None),
            "upstream_onnx_audit_status": (onnx_result["status"] if onnx_result is not None else "NOT_AUDITED_THIS_INVOCATION"),
            "actual_hosted_voice_pack_sha256": None,
            "hosted_voice_pack_bytes_verified": False,
            "historical_browser_cache_pm_alex_bin_sha256_matched": True,
            "effective_inference_voice_asset_consumption_proven": False,
            "commercial_rights": "PENDING_EXACT_PACK_LICENSE_AND_ATTRIBUTION_AUDIT",
            "runtime_terms_url": voice["runtime_terms_url"],
            "runtime_terms_reviewed": True,
            "runtime_permission": "COMMERCIAL_USE_CONDITIONAL_ON_ALL_RIGHTS",
            "runtime_dependency_notices_verified": False,
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
        "- Habacuque 1:2–4 foi cruzado com três referências documentadas; revisão teológica humana continua pendente.",
        "- A voz pm_alex aparece no catálogo oficial da upstream do modelo.",
        "- A upstream do modelo declara licença Apache-2.0.",
        "- Os seis blocos do rascunho foram preservados literalmente em ordem e hasheados.",
        "- O hash do pacote gerado é conferido com o relatório de produção anterior.",
        "", "## O que permanece bloqueado", "",
        "- O roteiro não passou por revisão bíblica independente nem aprovação do proprietário.",
        "- O upstream original publica pm_alex.pt e o upstream ONNX publica pm_alex.bin com SHA-256 diferente: um não comprova o outro.",
        "- Status da checagem ONNX: " + result["voice"]["upstream_onnx_audit_status"] + ". O hash do cache foi confirmado no teste histórico, mas não há prova independente de que a inferência consumiu aquele objeto.",
        "- O Kokoro Web permite narração comercial condicionalmente; ainda falta provar a identidade do pack realmente carregado e conferir licenças/avisos das dependências.",
        "- Em uma sessão isolada de Chrome, uma frase técnica não bíblica gerou um áudio temporário de 5,875 s e o cache continha pm_alex.bin com SHA correspondente ao ONNX upstream.",
        "- Esse teste histórico NÃO prova a identidade do arquivo consumido pela inferência, a licença completa nem a inteligibilidade de áudio de produção.",
        "- Foi preparado um pacote humano com seis blocos do texto exato, fontes, checklist e estado jurídico condicional, mas não existe aprovação humana.",
        "- Nenhuma voz nova nem WAV do roteiro E01 é produzido por este pré-voo.",
        "- Não houve geração de WAV, renderização, agendamento ou publicação.",
        "", "## Segmentos prontos para futura revisão", "",
    ]
    for seg in result["narration"]["segments"]:
        md.extend([f"### {seg['index']} — {seg['block_type']}", seg["text"], ""])
    md.extend(["## Próxima decisão", "",
               "Revisão contextual humana do roteiro e evidências específicas da voz/serviço, antes de iniciar o TTS.",
               "A licença Apache-2.0 da upstream e as permissões condicionais do site não comprovam, sozinhas, os direitos e a identidade dos assets efetivamente utilizados.",
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
        write("audio-preflight/context_crosscheck.json", dump(crosscheck_result)),
        write("audio-preflight/historical_smoke.json", dump(historical_smoke_verified)),
        write("audio-preflight/rights_review_handoff.json", dump(rights_handoff)),
        write("audio-preflight/e01_human_review_packet.md", human_review_md),
    ]
    summary = {
        "schema_version": "1.0.0", "project": "verbo-no-chao",
        "episode_id": TARGET_ID, "status": "BLOCKED",
        "stage": "AUDIO_PREFLIGHT_ONLY",
        "files": files, "blockers": list(REQUIRED_BLOCKERS),
        "voice_license_approved": False,
        "historical_smoke_evidence_verified": True,
        "rights_review_handoff_generated": True,
        "rights_review_handoff_status": "REVIEW_PACKET_READY_NOT_APPROVED",
        "historical_smoke_source_report_sha256": historical_smoke_verified["source_report_sha256"],
        "upstream_onnx_bytes_verified": onnx_upstream_verified,
        "hosted_voice_pack_bytes_verified": False,
        "internal_context_crosscheck_completed": True,
        "human_theological_review_pending": True,
        "audio_generated": False,
        "publication_authorized": False,
    }
    write("audio-preflight/report.json", dump(summary))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail-closed audio preflight for first script")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--upstream-dir", type=Path, required=True)
    parser.add_argument("--onnx-voice-audit", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        outcome = produce(args.root, args.upstream_dir, args.output_dir, onnx_audit=args.onnx_voice_audit)
    except (ProductionError, TypeError, KeyError, ValueError, OSError) as exc:
        parser.exit(1, f"BLOCKED: invalid preflight inputs: {exc}\n")
    print(json.dumps({k: outcome[k] for k in ("episode_id", "status", "audio_generated", "blockers")}))
    return 0  # Preparation ran successfully; audio remains blocked by design.


if __name__ == "__main__":
    raise SystemExit(main())
