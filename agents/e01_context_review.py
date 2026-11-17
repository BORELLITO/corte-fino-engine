"""Check a human-readable, source-grounded editorial cross-check against exact script bytes.

This is a deterministic *evidence integrity* gate, not AI exegesis or a human
theological endorsement. Reference URLs were reviewed outside CI.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any

from agents.content_production import check

SCRIPT_ID = "vnc-vnc-w01-e1-script-v1"
EPISODE_ID = "VNC-W01-E1"
EXPECTED_REFERENCE = "Habacuque 1:2-4"
SOURCE_URLS = frozenset({
    "https://classic.net.bible.org/passage.php?passage=hab+1%3A2-4",
    "https://bibleproject.com/guides/book-of-habakkuk/",
    "https://new.bible.org/seriespage/2-habakkuk",
})
EXPECTED_CLAIMS = ("C1", "C2", "C3")
REQUIRED_BLOCKS = (
    "opening", "connection", "biblical_reference",
    "reflection", "application", "conclusion",
)


def validate_context_crosscheck(review: Any, draft: Any, expected_fingerprint: str) -> dict[str, Any]:
    check(isinstance(review, dict), "context_review:not_object")
    check(review.get("project") == "verbo-no-chao"
          and review.get("episode_id") == EPISODE_ID
          and review.get("script_id") == SCRIPT_ID
          and review.get("reference") == EXPECTED_REFERENCE
          and review.get("review_type") == "SOURCE_BASED_INTERNAL_EDITORIAL_CROSSCHECK",
          "context_review:wrong_target_or_review_type")
    check(review.get("result") == "INTERNAL_CONTEXT_CROSSCHECK_PASS_WITH_CAVEATS"
          and review.get("independent_human_theological_review") == "PENDING"
          and review.get("owner_approval") is False
          and review.get("approved_for_audio") is False
          and review.get("publication_authorized") is False,
          "context_review:false_approval_or_bad_scope")
    check(isinstance(draft, dict) and draft.get("episode_id") == EPISODE_ID
          and draft.get("script_id") == SCRIPT_ID
          and draft.get("reference") == EXPECTED_REFERENCE
          and draft.get("status") == "DRAFT_REVIEW_REQUIRED"
          and draft.get("biblical_review_status") == "PENDING_INDEPENDENT_REVIEW"
          and draft.get("owner_approval") is False
          and draft.get("publication_authorized") is False,
          "context_review:unapproved_draft_required")
    blocks = draft.get("blocks")
    check(isinstance(blocks, list) and len(blocks) == len(REQUIRED_BLOCKS)
          and all(isinstance(b, dict) and isinstance(b.get("text"), str)
                  for b in blocks) and
          tuple(b.get("type") for b in blocks) == REQUIRED_BLOCKS,
          "context_review:script_blocks_invalid")
    block_hashes = [hashlib.sha256(b["text"].encode("utf-8")).hexdigest() for b in blocks]
    check(review.get("script_blocks_sha256") == block_hashes,
          "context_review:review_does_not_match_exact_block_bytes")
    actual_fingerprint = hashlib.sha256(
        re.sub(r"\s+", " ", " ".join(b["text"] for b in blocks).casefold()).encode("utf-8")
    ).hexdigest()
    check(actual_fingerprint == expected_fingerprint
          and review.get("reviewed_canonical_narration_sha256") == actual_fingerprint,
          "context_review:canonical_script_fingerprint_changed")

    sources = review.get("reviewed_sources")
    check(isinstance(sources, list) and len(sources) == 3
          and all(isinstance(s, dict) and s.get("verified") == "2026-11-17"
                  and s.get("publication_license") == "NOT_CLEARED_FOR_QUOTING"
                  and isinstance(s.get("finding"), str) and len(s["finding"]) >= 40
                  for s in sources),
          "context_review:sources_incomplete_or_unlicensed")
    cited_urls = [item.get("url") for item in sources]
    check(len(set(cited_urls)) == 3 and set(cited_urls) == SOURCE_URLS,
          "context_review:source_urls_changed")
    claims = review.get("claims_checked")
    check(isinstance(claims, list) and
          tuple(c.get("claim_id") for c in claims if isinstance(c, dict)) == EXPECTED_CLAIMS,
          "context_review:required_claims_missing")
    block_map = {b["type"]: b["text"] for b in blocks}
    for claim in claims:
        check(isinstance(claim, dict)
              and claim.get("status") in {"SUPPORTED_IN_CONTEXT", "SUPPORTED_IN_BOOK_CONTEXT",
                                         "EDITORIAL_SCOPE_REVIEW_ONLY"},
              "context_review:claim_incomplete")
        check(isinstance(claim.get("source_urls"), list)
              and bool(claim["source_urls"])
              and set(claim["source_urls"]).issubset(SOURCE_URLS),
              "context_review:unsupported_citation")
        section = claim.get("required_in_script_block")
        anchors = claim.get("anchor_words")
        check(section in block_map and isinstance(anchors, list)
              and len(anchors) >= 2 and
              all(isinstance(a, str) and len(a) >= 6 and
                  a.casefold() in block_map[section].casefold() for a in anchors),
              f"context_review:claim_anchor_mismatch:{claim.get('claim_id')}")
    caveats = review.get("caveats")
    check(isinstance(caveats, list) and len(caveats) >= 4
          and all(isinstance(x, str) and len(x) > 45 for x in caveats),
          "context_review:caveats_missing")
    return {
        "episode_id": EPISODE_ID,
        "status": "INTERNAL_CONTEXT_CROSSCHECK_PASS_WITH_CAVEATS",
        "review_date": review.get("review_date"),
        "source_urls": sorted(SOURCE_URLS),
        "claims_checked": [x["claim_id"] for x in claims],
        "canonical_narration_sha256": actual_fingerprint,
        "independent_human_theological_review": "PENDING",
        "approved_for_audio": False,
        "owner_approval": False,
        "publication_authorized": False,
        "limitations": [
            "Evidence record was assembled from publicly reviewed sources; CI verifies links and hashes, not live theological truth.",
            "Manual human theological review, originality scrutiny and owner script approval are still required.",
            "Reference text and commentary are not automatically licensed for narration or quotation.",
        ],
    }
