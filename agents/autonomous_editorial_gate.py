"""Versioned AI editorial judgment with strict source/script binding and narrow scope.

The ChatGPT assistant writes a semantic review *before* this gate is run.
CI verifies evidence consistency, not theology through a live model call.
No false 'independent human' label, no media or publication authorization.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any

from agents.content_production import check, ProductionError
from editorial.review import review_script
from editorial.script_validator import validate_script_package

SCRIPT_PILLARS = (
    "biblical_primary_context", "claims_and_interpretation",
    "christian_integrity", "emotional_safety",
    "originality_and_copyright", "narrative_and_retention",
    "language_and_tts", "research_evidence",
)
SOURCE_URLS = frozenset({
    "https://bible.usccb.org/bible/habakkuk/1",
    "https://bibleproject.com/guides/book-of-habakkuk/",
    "https://classic.net.bible.org/passage.php?passage=hab+1%3A2-4",
})


def canonical_sha(draft: Any) -> str:
    check(isinstance(draft, dict) and isinstance(draft.get("blocks"), list),
          "ai_editorial:invalid_script")
    blocks = draft["blocks"]
    check(len(blocks) == 6 and all(isinstance(b, dict) and isinstance(b.get("text"), str)
                                  for b in blocks), "ai_editorial:invalid_blocks")
    text = " ".join(b["text"] for b in blocks)
    return hashlib.sha256(re.sub(r"\s+", " ", text.casefold()).encode("utf-8")).hexdigest()


def verify_ai_editorial_review(policy: Any, review: Any, draft: Any) -> dict[str, Any]:
    check(isinstance(policy, dict) and policy.get("project") == "verbo-no-chao"
          and policy.get("policy_id") == "VNC-AUTONOMOUS_EDITORIAL_QA_V1"
          and policy.get("effective_for") == "NEW_NON_PILOT_EPISODES_ONLY"
          and policy.get("supersedes_only") == "SCRIPT_REVIEW_AND_SCRIPT_OWNER_APPROVAL_REQUIREMENT"
          and policy.get("owner_reviews_intermediate_scripts") is False
          and policy.get("owner_approves_internal_script") is False
          and policy.get("automated_internal_script_approval_permitted") is True
          and policy.get("approver_kind") == "AI_ASSISTANT_INTERNAL_EDITORIAL_NOT_INDEPENDENT_HUMAN"
          and policy.get("publication_authorized") is False
          and policy.get("owner_final_video_approval_required") is False
          and policy.get("internal_final_video_qa_required") is True
          and policy.get("final_video_owner_review_optional") is True
          and policy.get("separate_explicit_publication_authorization_required") is True
          and policy.get("protected_pilot_can_be_retroactively_auto_approved") is False,
          "ai_editorial:policy_contract_changed")
    configured = policy.get("pillars")
    check(isinstance(configured, list) and len(configured) == 12
          and tuple(x.get("id") for x in configured[:8] if isinstance(x, dict)) ==
          SCRIPT_PILLARS
          and all(x.get("required_for_script") is True for x in configured[:8])
          and all(x.get("required_for_script") is False for x in configured[8:]),
          "ai_editorial:required_pillars_invalid")
    rules = policy.get("script_approval_rules")
    check(isinstance(rules, dict) and rules.get("mandatory_script_pillars") == 8
          and rules.get("critical_findings_allowed") == 0
          and rules.get("source_count_at_least") == 2
          and rules.get("must_pin_canonical_script_sha256") is True
          and rules.get("fail_closed_if_semantic_review_missing") is True,
          "ai_editorial:policy_gate_weak")
    check(isinstance(draft, dict)
          and draft.get("episode_id") == "VNC-W01-E1"
          and draft.get("reference") == "Habacuque 1:2-4"
          and draft.get("status") == "DRAFT_REVIEW_REQUIRED"
          and draft.get("owner_approval") is False
          and draft.get("publication_authorized") is False
          and draft.get("source_mode") == "reference_and_paraphrase"
          and draft.get("contains_verbatim_quote") is False,
          "ai_editorial:wrong_or_unapproved_script")
    check(not validate_script_package(draft), "ai_editorial:invalid_script_package")
    deterministic = review_script(draft)
    check(deterministic.status == "PASS_AUTOMATED_REVIEW" and not deterministic.errors
          and 63.75 <= deterministic.estimated_seconds <= 86.25,
          "ai_editorial:deterministic_script_gate_failed")

    digest = canonical_sha(draft)
    check(isinstance(review, dict) and review.get("project") == "verbo-no-chao"
          and review.get("episode_id") == draft["episode_id"]
          and review.get("reference") == draft["reference"]
          and review.get("review_id") == "VNC-E01-INTERNAL-AI-REVIEW-2026-11-17"
          and review.get("review_date") == "2026-11-17"
          and review.get("review_model_context") == "CHATGPT_GPT6_IN_CONVERSATION_NOT_CI_MODEL"
          and review.get("review_method") ==
          "AI_SEMANTIC_SOURCE_CROSSCHECK_ONE_MODEL_WITH_DETERMINISTIC_VALIDATION"
          and review.get("review_independent_human") is False
          and review.get("review_externally_reexecuted_in_ci") is False
          and review.get("reviewed_canonical_script_sha256") == digest,
          "ai_editorial:untrusted_semantic_review_or_digest")
    sources = review.get("script_reviewed_sources")
    check(isinstance(sources, list)
          and len(set(sources)) >= 2
          and set(sources) == SOURCE_URLS,
          "ai_editorial:source_evidence_missing")
    check(review.get("result") == "PASS_WITH_DOCUMENTED_CAVEATS"
          and review.get("decision_status") == "AUTO_APPROVED_FOR_INTERNAL_PRODUCTION"
          and review.get("approval_scope") == "SCRIPT_TEXT_ONLY"
          and review.get("owner_script_review_required") is False
          and review.get("owner_script_approval") is False
          and review.get("human_theological_endorsement") is False
          and review.get("critical_findings") == []
          and review.get("fix_required_before_script_approval") == [],
          "ai_editorial:unsafe_or_unsupported_approval")
    observed = review.get("pillars")
    check(isinstance(observed, list) and len(observed) == 8
          and tuple(p.get("id") for p in observed if isinstance(p, dict)) ==
          SCRIPT_PILLARS, "ai_editorial:missing_ai_review_pillars")
    texts = {b["type"]: b["text"] for b in draft["blocks"]}
    for p in observed:
        check(p.get("status") == "PASS_WITH_CAVEATS"
              and p.get("block") in texts
              and isinstance(p.get("script_anchor"), str)
              and len(p["script_anchor"]) >= 18
              and p["script_anchor"] in texts[p["block"]]
              and p.get("source_url") in SOURCE_URLS
              and isinstance(p.get("analysis"), str)
              and len(p["analysis"]) >= 55,
              "ai_editorial:unanchored_or_failed_pillar:" + str(p.get("id")))
    check(isinstance(review.get("caveats"), list)
          and len(review["caveats"]) >= 4
          and all(isinstance(x, str) and len(x) >= 45 for x in review["caveats"]),
          "ai_editorial:missing_caveats")
    for k in ("production_wav_rights_cleared", "visual_assets_cleared",
              "music_license_cleared", "captions_synced", "physical_master_verified",
              "monetization_cleared", "final_video_owner_approval",
              "publication_authorized"):
        check(review.get(k) is False, "ai_editorial:forged_media_or_release_clearance:" + k)
    return {
        "episode_id": draft["episode_id"],
        "script_sha256": digest,
        "status": "AUTO_APPROVED_FOR_INTERNAL_PRODUCTION",
        "reviewer_kind": "AI_ASSISTANT_NOT_HUMAN_NOT_REEXECUTED_BY_CI",
        "source_count": len(sources),
        "mandatory_pillars_passed": len(observed),
        "semantic_report_verified_against_script": True,
        "owner_script_review_required": False,
        "human_theological_endorsement": False,
        "voice_audio_generation_authorized": False,
        "full_video_ready": False,
        "final_video_owner_approval_required": False,
        "internal_final_video_qa_required": True,
        "owner_final_video_review_optional": True,
        "publication_authorized": False,
        "remaining_gates": [
            "VOICE_RIGHTS_AND_RUNTIME_NOTICES",
            "AUDIO_PRODUCTION_AND_LISTENING_QA",
            "VISUAL_ASSET_RIGHTS_AND_NON_REPETITION",
            "MUSIC_AND_CAPTIONS_AND_PHYSICAL_MASTER_QA",
            "FINAL_VIDEO_OWNER_APPROVAL",
            "SEPARATE_PUBLICATION_AUTHORIZATION",
        ],
    }
