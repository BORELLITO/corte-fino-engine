"""Isolated E01 script v2: exactly one-sentence pronunciation remediation.

Reads the immutable v1 from seed and its original AI-reviewed SHA. Rewrites
only one sentence into a new candidate, then requires a NEW AI semantic review
against its own hash. V1/Salmo13/main/bootstrap are never modified.
"""
from __future__ import annotations
import copy
from pathlib import Path
from typing import Any

from agents.content_production import check
from agents.e01_voice_preview import read_json, approved_source
from agents.autonomous_editorial_gate import canonical_sha, verify_ai_editorial_review

OLD = "Às vezes, dói esperar."
NEW = "Às vezes, esperar machuca."
PARENT_SHA = "67052ec614f3beaca25cbac40414eecb7f197be0b73b7c1af4fd6579c0cf6990"
V2_SHA = "c64b57cb9d6529b60b9e80ab7607e5887f909dd00e14cd80ed9ec2b7474a5dc6"
V2_ID = "vnc-vnc-w01-e1-script-v2"
SCRIPT_PATH = "contracts/e01_script_v2_candidate.json"
REVIEW_PATH = "contracts/e01_ai_editorial_review_v2.json"


def approved_v2(root: Path) -> tuple[str, dict[str, Any]]:
    # Strictly validate unchanged historic v1 and conditional service rights.
    _, v1_approval = approved_source(root)
    check(v1_approval["script_sha256"] == PARENT_SHA,
          "e01v2:parent_script_not_pinned")
    seed = read_json(root, "agents/first_batch_seed.json")
    parent = seed["episodes"][0]
    check(parent["blocks"][1]["text"].startswith(OLD)
          and parent["script_id"] == "vnc-vnc-w01-e1-script-v1",
          "e01v2:legacy_parent_unexpected")
    policy = read_json(root, "contracts/autonomous_editorial_policy_v1.json")
    payload = read_json(root, SCRIPT_PATH)
    review = read_json(root, REVIEW_PATH)
    check(isinstance(payload, dict)
          and payload.get("project") == "verbo-no-chao"
          and payload.get("candidate_status") == "SCRIPT_V2_PENDING_NEW_AUDIO_QA"
          and payload.get("voice_rights_cleared") is False
          and payload.get("production_wav_master_approved") is False
          and payload.get("publication_authorized") is False,
          "e01v2:candidate_release_flags")
    draft = payload.get("episode")
    check(isinstance(draft, dict), "e01v2:episode_missing")
    meta = draft.get("pronunciation_rewrite")
    check(isinstance(meta, dict)
          and meta.get("version") == 2
          and meta.get("parent_script_id") == parent["script_id"]
          and meta.get("parent_narration_sha256") == PARENT_SHA
          and meta.get("canonical_narration_sha256") == V2_SHA
          and meta.get("old_phrase") == OLD
          and meta.get("replacement_phrase") == NEW
          and meta.get("scope") ==
               "EXACTLY_ONE_SENTENCE_REPLACED_ALL_OTHER_BLOCKS_UNCHANGED"
          and meta.get("prior_asr_evidence_ref") ==
               "contracts/e01_asr_second_opinion_evidence_v1.json"
          and meta.get("old_audio_retained") is True
          and meta.get("master_approved") is False
          and meta.get("publication_authorized") is False,
          "e01v2:rewrite_lineage_or_approval")
    expected = copy.deepcopy(parent)
    expected["script_id"] = V2_ID
    expected["blocks"][1]["text"] = expected["blocks"][1]["text"].replace(
        OLD, NEW, 1)
    # Explicit lineage can include human-readable notes, but nothing else
    # about the six text blocks, Bible context, source URLs or status may differ.
    check({k: v for k, v in draft.items() if k != "pronunciation_rewrite"} ==
          expected, "e01v2:unreviewed_changes_outside_approved_phrase")
    check(canonical_sha(draft) == V2_SHA,
          "e01v2:exact_v2_hash_invalid")
    result = verify_ai_editorial_review(policy, review, draft)
    check(result["script_sha256"] == V2_SHA
          and result["review_file_ref"] == REVIEW_PATH
          and result["status"] == "AUTO_APPROVED_FOR_INTERNAL_PRODUCTION"
          and result["publication_authorized"] is False,
          "e01v2:review_evidence_not_approved")
    return "\n".join(b["text"].strip() for b in draft["blocks"]), result
