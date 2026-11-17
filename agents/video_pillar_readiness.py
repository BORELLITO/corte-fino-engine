"""Consolidated 12-pillar stage scoreboard for non-pilot video automation.

Only an evidenced AI script decision can clear the first eight gates. The
physical video, rights and publication gates remain blocked until decoded
media, provenance and exact release contracts exist. No paper QA is a master.
"""
from __future__ import annotations

from typing import Any
from agents.content_production import check

SCRIPT_IDS = (
    "biblical_primary_context", "claims_and_interpretation",
    "christian_integrity", "emotional_safety",
    "originality_and_copyright", "narrative_and_retention",
    "language_and_tts", "research_evidence",
)
MEDIA_IDS = ("visual_storyboard", "music_and_voice",
             "captions_and_export", "metadata_and_monetization")
BLOCKERS = (
    "visual_storyboard_real_assets_and_no_repetition_not_verified",
    "music_voice_rights_real_waveform_and_listening_qa_not_verified",
    "captions_timing_and_decoded_video_master_not_verified",
    "metadata_platform_rights_monetization_not_verified",
)


def video_pillar_readiness(policy: Any, video_policy: Any,
                           ai_result: Any) -> dict[str, Any]:
    check(isinstance(policy, dict) and isinstance(video_policy, dict)
          and isinstance(ai_result, dict), "video_readiness:missing_inputs")
    configured = policy.get("pillars")
    check(isinstance(configured, list)
          and tuple(x.get("id") for x in configured[:8] if isinstance(x, dict)) == SCRIPT_IDS
          and tuple(x.get("id") for x in configured[8:] if isinstance(x, dict)) == MEDIA_IDS,
          "video_readiness:missing_12_pillars")
    check(ai_result.get("status") == "AUTO_APPROVED_FOR_INTERNAL_PRODUCTION"
          and ai_result.get("mandatory_pillars_passed") == 8
          and ai_result.get("semantic_report_verified_against_script") is True
          and ai_result.get("voice_audio_generation_authorized") is False
          and ai_result.get("publication_authorized") is False,
          "video_readiness:script_not_genuinely_reviewed")
    check(video_policy.get("project") == "verbo-no-chao"
          and video_policy.get("effective_scope") == "NEW_NON_PILOT_EPISODES_ONLY"
          and video_policy.get("owner_script_approval_required") is False
          and video_policy.get("final_owner_approval_required") is False
          and video_policy.get("internal_final_video_qa_required") is True
          and video_policy.get("publication_authorized_by_default") is False
          and isinstance(video_policy.get("workflow"), list)
          and any(x.get("state") == "AWAIT_SEPARATE_PUBLICATION_PERMISSION"
                  and x.get("automatic") is False
                  for x in video_policy["workflow"] if isinstance(x, dict)),
          "video_readiness:publication_boundary_missing")
    base = [
        {
            "id": pid, "status": "PASS_VERSIONED_AI_SCRIPT_REVIEW_ONLY",
            "script_sha256": ai_result["script_sha256"],
            "source": "contracts/e01_ai_editorial_review_v1.json",
            "scope": "SCRIPT_TEXT",
        }
        for pid in SCRIPT_IDS
    ]
    extra = [
        {
            "id": pid, "status": "BLOCKED_PHYSICAL_QA_PENDING",
            "blocker": reason, "evidence": None,
            "scope": "RENDERED_VIDEO_AND_RIGHTS",
        }
        for pid, reason in zip(MEDIA_IDS, BLOCKERS)
    ]
    return {
        "schema_version": "1.0.0",
        "project": "verbo-no-chao",
        "episode_id": ai_result["episode_id"],
        "status": "BLOCKED_PHYSICAL_MEDIA_AND_RIGHTS_NOT_PROVEN",
        "script_editorial_internal_approval": True,
        "script_approval_only": True,
        "pillars": base + extra,
        "script_pillars_with_versioned_ai_review": 8,
        "media_pillars_with_actual_proof": 0,
        "owner_script_review_required": False,
        "owner_finished_video_review_required": False,
        "full_video_production_completed": False,
        "decoded_final_master_verified": False,
        "all_rights_cleared": False,
        "ready_for_publication_authorization": False,
        "separate_explicit_publication_authorization_required": True,
        "publication_authorized": False,
        "blocking_reasons": list(BLOCKERS),
    }


def validate_video_pillar_report(v: Any) -> None:
    check(isinstance(v, dict) and v.get("project") == "verbo-no-chao"
          and v.get("episode_id") == "VNC-W01-E1"
          and v.get("status") == "BLOCKED_PHYSICAL_MEDIA_AND_RIGHTS_NOT_PROVEN"
          and v.get("script_editorial_internal_approval") is True
          and v.get("script_approval_only") is True
          and v.get("script_pillars_with_versioned_ai_review") == 8
          and v.get("media_pillars_with_actual_proof") == 0
          and v.get("owner_script_review_required") is False
          and v.get("owner_finished_video_review_required") is False
          and v.get("full_video_production_completed") is False
          and v.get("decoded_final_master_verified") is False
          and v.get("all_rights_cleared") is False
          and v.get("ready_for_publication_authorization") is False
          and v.get("separate_explicit_publication_authorization_required") is True
          and v.get("publication_authorized") is False
          and v.get("blocking_reasons") == list(BLOCKERS),
          "video_readiness:false_video_approval")
    entries = v.get("pillars")
    check(isinstance(entries, list) and len(entries) == 12
          and tuple(x.get("id") for x in entries if isinstance(x, dict)) ==
          SCRIPT_IDS + MEDIA_IDS,
          "video_readiness:invalid_pillars")
    check(all(x.get("status") == "PASS_VERSIONED_AI_SCRIPT_REVIEW_ONLY"
              and x.get("source") == "contracts/e01_ai_editorial_review_v1.json"
              and isinstance(x.get("script_sha256"), str)
              and len(x["script_sha256"]) == 64
              for x in entries[:8]),
          "video_readiness:script_claims_inflated")
    check(all(x.get("status") == "BLOCKED_PHYSICAL_QA_PENDING"
              and x.get("evidence") is None
              and x.get("blocker") == BLOCKERS[i]
              for i, x in enumerate(entries[8:])),
          "video_readiness:media_claims_inflated")
