"""Fail-closed licensing and human-review handoff for the first original script.

Validation is about provenance and internal consistency of a *source-based
assessment*, not an automated legal opinion or an independent theologian.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any

from agents.content_production import check
from agents.e01_context_review import validate_context_crosscheck
from agents.controlled_smoke_evidence import validate_smoke_attestation
from agents.audio_preflight import validate_voice_evidence

EPISODE = "VNC-W01-E1"
EXPECTED_IDS = ("MODEL", "ONNX", "VOICE", "HOST", "HOST_NOTICE", "SCRIPT")
SOURCE_URLS = {
    "MODEL": "https://huggingface.co/hexgrad/Kokoro-82M",
    "ONNX": "https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX",
    "VOICE": "https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX/blob/main/voices/pm_alex.bin",
    "HOST": "https://kokoroweb.app/terms",
    "HOST_NOTICE": "https://kokoroweb.app/privacy",
    "SCRIPT": "https://bibleproject.com/guides/book-of-habakkuk/",
}
EXPECTED_STATUSES = {
    "MODEL": "UPSTREAM_DECLARATION_VERIFIED",
    "ONNX": "UPSTREAM_DECLARATION_AND_VOICE_BYTES_VERIFIED",
    "VOICE": "CACHE_SHA_MATCH_OBSERVED_NOT_RUNTIME_CONSUMPTION_PROVEN",
    "HOST": "COMMERCIAL_OUTPUT_CONDITIONALLY_PERMITTED_BY_HOST_TERMS",
    "HOST_NOTICE": "FRONTEND_DEPENDENCY_VERSIONS_UNVERIFIED",
    "SCRIPT": "NO_VERBATIM_INTENDED_REVIEW_PENDING",
}
VOICE_SHA = "0175c753f59c54e7fd5a995bedef0c5ff2fb67e0043dd3dcb2ae74ec2acbeb2a"
ALLOWED_BLOCKS = ("opening", "connection", "biblical_reference", "reflection", "application", "conclusion")


def verify_dossier(dossier: Any, crosscheck: Any, smoke: Any,
                   voice: Any, draft: Any, draft_hash: str) -> dict[str, Any]:
    check(isinstance(dossier, dict)
          and dossier.get("schema_version") == "1.0.0"
          and dossier.get("project") == "verbo-no-chao"
          and dossier.get("assessment_id") == "VNC-E01-RIGHTS-AND-REVIEW-HANDOFF-001"
          and dossier.get("episode_id") == EPISODE
          and dossier.get("reference") == "Habacuque 1:2-4"
          and dossier.get("assessment_date") == "2026-11-17"
          and dossier.get("source_kind") ==
              "VERIFIED_PUBLIC_SOURCE_DECLARATIONS_NOT_LEGAL_OPINION",
          "rights_review:identity")
    check(dossier.get("linked_review_contract") ==
          "contracts/e01_editorial_crosscheck_v1.json"
          and dossier.get("linked_smoke_contract") ==
          "contracts/kokoro_controlled_smoke_evidence_v1.json"
          and dossier.get("scope") ==
          "DRAFT_E01_AND_KOKORO_WEB_NARRATION_PREPARATION_ONLY",
          "rights_review:source_linkage")
    validate_voice_evidence(voice)
    ctx = validate_context_crosscheck(crosscheck, draft, draft_hash)
    historical = validate_smoke_attestation(smoke)
    items = dossier.get("evidence")
    check(isinstance(items, list) and len(items) == len(EXPECTED_IDS)
          and tuple(x.get("id") for x in items if isinstance(x, dict)) == EXPECTED_IDS,
          "rights_review:evidence_inventory")
    for item in items:
        ident = item["id"]
        check(item.get("url") == SOURCE_URLS[ident]
              and item.get("status") == EXPECTED_STATUSES[ident]
              and isinstance(item.get("declared_license"), str)
              and len(item["declared_license"]) >= 8
              and isinstance(item.get("finding"), str)
              and len(item["finding"]) > 70
              and isinstance(item.get("permission_inference"), str)
              and item["permission_inference"] != "FULLY_LICENSED",
              f"rights_review:source_claim_changed:{ident}")
    check(items[0]["declared_license"] == "Apache-2.0"
          and items[1]["declared_license"] == "Apache-2.0",
          "rights_review:model_license")
    check(dossier.get("audio_test_duration_seconds") == historical["test_audio_duration_seconds"]
          and dossier.get("onnx_voice_sha256") == historical["cached_voice_sha256"]
          and dossier.get("onnx_voice_sha256") == VOICE_SHA
          and dossier.get("cache_voice_bytes") == historical["cached_voice_bytes"],
          "rights_review:cached_voice_evidence_mismatch")
    check(dossier.get("host_commercial_narration_terms") ==
          "CONDITIONAL_PERMISSION_DOCUMENTED"
          and dossier.get("release_review_status") ==
          "NEEDS_INDEPENDENT_HUMAN_THEOLOGICAL_EDITORIAL_REVIEW_AND_OWNER_APPROVAL"
          and dossier.get("independent_human_biblical_review") == "PENDING"
          and dossier.get("owner_script_approval") is False
          and dossier.get("right_to_use_all_actual_runtime_assets") == "NOT_FULLY_CONFIRMED"
          and dossier.get("original_licensed_voice_runtime_notice_bundle") == "NOT_VERIFIED"
          and dossier.get("effective_voice_asset_consumption") == "NOT_INDEPENDENTLY_PROVEN"
          and dossier.get("production_wav_generated") is False
          and dossier.get("human_audio_listening_test") == "NOT_PERFORMED"
          and dossier.get("publication_authorized") is False
          and dossier.get("license_cleared") is False
          and dossier.get("approved_for_audio") is False,
          "rights_review:false_clearance")
    outstanding = dossier.get("unresolved")
    check(isinstance(outstanding, list) and len(outstanding) == 5
          and all(isinstance(x, str) and len(x) > 55 for x in outstanding),
          "rights_review:unresolved_controls_missing")
    check(draft.get("source_mode") == "reference_and_paraphrase"
          and draft.get("contains_verbatim_quote") is False
          and draft.get("biblical_review_status") == "PENDING_INDEPENDENT_REVIEW",
          "rights_review:unlicensed_script")
    return {
        "schema_version": "1.0.0",
        "project": "verbo-no-chao",
        "episode_id": EPISODE,
        "status": "REVIEW_PACKET_READY_NOT_APPROVED",
        "script_canonical_sha256": ctx["canonical_narration_sha256"],
        "source_record_count": len(items),
        "site_output_permission": "COMMERCIAL_USE_CONDITIONAL_ON_ALL_RIGHTS",
        "model_upstream_license": "Apache-2.0",
        "onnx_upstream_license": "Apache-2.0",
        "observed_cached_voice_sha256": historical["cached_voice_sha256"],
        "historical_audio_test_duration_seconds": historical["test_audio_duration_seconds"],
        "hosted_effective_voice_use_proven": False,
        "runtime_notices_reviewed": False,
        "independent_human_biblical_review": "PENDING",
        "owner_script_approval": False,
        "approved_for_audio": False,
        "publication_authorized": False,
        "limitations": list(outstanding),
    }


def render_human_review_packet(draft: dict[str, Any], assessment: dict[str, Any],
                               dossier: dict[str, Any], crosscheck: dict[str, Any]) -> str:
    check(assessment.get("status") == "REVIEW_PACKET_READY_NOT_APPROVED"
          and draft.get("episode_id") == EPISODE
          and assessment.get("owner_script_approval") is False,
          "rights_review:review_pack_requires_unapproved_draft")
    blocks = draft.get("blocks", [])
    check(isinstance(blocks, list) and
          tuple(b.get("type") for b in blocks if isinstance(b, dict)) == ALLOWED_BLOCKS,
          "rights_review:review_pack_blocks")
    lines = [
        "# VERBO NO CHÃO — E01 | Revisão editorial e direitos (NÃO aprovado)",
        "",
        "Este pacote prepara uma decisão humana. **Não certifica teologia, licença ou aprovação de áudio.**",
        "",
        f"**Título provisório:** {draft.get('title_proposal')}",
        f"**Texto:** {draft['reference']}",
        f"**Hash canônico da narração:** \`{assessment['script_canonical_sha256']}\`",
        "",
        "## 1. Roteiro integral, versão exata sob revisão",
        "",
    ]
    for i, b in enumerate(blocks, start=1):
        lines.extend([f"### {i}. {b['type']}", "", b["text"], ""])
    lines.extend([
        "## 2. Pontos para um revisor bíblico independente",
        "",
        "- [ ] Verificar Habacuque 1:2–4 em contexto (violência, justiça distorcida e lei sem força)",
        "- [ ] Confirmar que a aplicação individual não substitui a denúncia coletiva",
        "- [ ] Conferir o desenvolvimento posterior do livro (1:5 em diante) sem prometer soluções imediatas",
        "- [ ] Verificar que nenhuma frase é atribuída ao texto bíblico como citação inexistente",
        "- [ ] Avaliar a linguagem cristã ampla, esperança honesta e ausência de manipulação emocional",
        "- [ ] Registrar parecer humano identificável e mudanças necessárias fora deste pacote automático",
        "",
        "### Referências de pesquisa (não autorizam reprodução literal)",
        "",
    ])
    for source in crosscheck["reviewed_sources"]:
        lines.append(f"- {source['url']} — {source['finding']}")
    lines.extend([
        "",
        "## 3. Situação das licenças e do ambiente",
        "",
        "| Componente | Evidência verificada | Estado |",
        "|---|---|---|",
    ])
    for item in dossier["evidence"]:
        lines.append(f"| {item['class']} | {item['url']} | {item['status']} |")
    lines.extend([
        "",
        "Modelo e ONNX declaram Apache-2.0. O Kokoro Web admite uso comercial da narração",
        "**condicionado** a todos os direitos necessários. O SHA do cache da voz correspondeu",
        "ao ONNX upstream na sessão histórica, mas **não demonstra uso efetivo do objeto pela inferência**.",
        "Este pacote não contém avisos completos da versão hospedada, atestado jurídico ou WAV.",
        "",
        "## 4. Gates e decisões independentes",
        "",
        "- **Preparação documental:** concluída e verificável por hash.",
        "- **Revisão teológica humana independente:** PENDENTE.",
        "- **Aprovação do proprietário deste roteiro exato:** PENDENTE.",
        "- **Licenças/avisos do runtime realmente usado:** INCOMPLETOS.",
        "- **Geração de WAV de produção e escuta/QA:** NÃO EXECUTADOS.",
        "- **Publicação:** NÃO AUTORIZADA.",
        "",
        "Nenhum campo acima pode ser promovido automaticamente por testes de CI.",
        "",
    ])
    return "\n".join(lines)
