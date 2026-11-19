"""Fail-closed semantic release lock for E01 S01 stock previews.

Does NOT declare rights, editorial acceptance, a master, or publication.
Uses explicit historical editorial rejections; online providers are NOT queried.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "contracts" / "e01_s01_stock_rejection_lock_20261119_v1.json"

# These are locked historical facts, independent of editable JSON.
LOCKED_REJECTIONS = {
    "3653dd73575446533b1f47512b3c236b9184bba150fec5116c5526ba0ee1013e":
        frozenset((32788087, 4458845, 6376122)),
    "2c099db52b219cb901977d98fac29f91579a4be1d9a2126f4ff6ba0cbcc7c1e5":
        frozenset((8860242, 4458845)),
}


class S01EditorialGateError(ValueError):
    """Never convert missing, contradictory or forged evidence into approval."""


def load_registry(path: Path = REGISTRY) -> dict[str, Any]:
    try:
        registry = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise S01EditorialGateError("rejection_registry_unavailable") from exc
    if not isinstance(registry, dict):
        raise S01EditorialGateError("rejection_registry_invalid")
    if (
        registry.get("schema_version") != "1.0.0"
        or registry.get("project_id") != "VERBO_NO_CHAO_EXCLUSIVO"
        or registry.get("scene_id") != "VNC-E01V2-S01"
        or registry.get("episode_id") != "VNC-W01-E1"
        or registry.get("publication_authorized") is not False
        or registry.get("master_allowed") is not False
        or registry.get("accepted_for_master") is not False
    ):
        raise S01EditorialGateError("rejection_registry_invariant_failed")
    rows = registry.get("rejections")
    if not isinstance(rows, list) or len(rows) != len(LOCKED_REJECTIONS):
        raise S01EditorialGateError("rejection_registry_missing_entries")
    observed = {}
    for row in rows:
        if not isinstance(row, dict):
            raise S01EditorialGateError("rejection_registry_bad_entry")
        digest = row.get("output_sha256")
        source_ids = row.get("source_video_ids")
        if (not isinstance(digest, str)
                or not isinstance(source_ids, list)
                or any(type(x) is not int for x in source_ids)
                or len(set(source_ids)) != len(source_ids)
                or digest in observed
                or row.get("decision") != "REJECTED_EDITORIAL"
                or row.get("rights_cleared") is not False
                or not isinstance(row.get("reason"), str)
                or not row["reason"].strip()
                or not isinstance(row.get("proof_run"), str)
                or not row["proof_run"].startswith(
                    "https://github.com/BORELLITO/verbo-no-chao-engine/actions/runs/"
                )):
            raise S01EditorialGateError("rejection_registry_bad_entry")
        observed[digest] = frozenset(source_ids)
    if observed != LOCKED_REJECTIONS:
        raise S01EditorialGateError("rejection_registry_historical_tampering")
    return registry


def _valid_sha(value: Any) -> bool:
    return (isinstance(value, str) and len(value) == 64
            and all(c in "0123456789abcdef" for c in value))


def classify_s01_stock_preview(
    report: dict[str, Any],
    movie_path: Path | None = None,
    registry_path: Path = REGISTRY,
) -> dict[str, Any]:
    """Classify a *technical preview*. No path through this function approves a master."""
    load_registry(registry_path)
    if not isinstance(report, dict) or report.get("project") != "VERBO_NO_CHAO_EXCLUSIVO":
        raise S01EditorialGateError("wrong_project")
    if report.get("scene_id") != "VNC-E01V2-S01":
        raise S01EditorialGateError("wrong_scene")
    for flag in ("editorial_reviewed", "rights_cleared", "master_allowed",
                 "publication_authorized", "source_audio_added", "captions_added"):
        if report.get(flag) is not False:
            raise S01EditorialGateError("false_approval_or_media_claim_" + flag)
    status = report.get("status")
    if status != "REAL_STOCK_MONTAGE_PHYSICALLY_VERIFIED_EDITORIAL_AND_RIGHTS_PENDING":
        raise S01EditorialGateError("technical_preview_not_verified")
    digest = report.get("output_sha256")
    if not _valid_sha(digest) or report.get("full_video_decode_ok") is not True:
        raise S01EditorialGateError("physical_evidence_missing")
    if movie_path is not None:
        p = Path(movie_path)
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != digest:
            raise S01EditorialGateError("physical_sha_mismatch")
    sources = report.get("source_clips")
    if not isinstance(sources, list) or not sources:
        raise S01EditorialGateError("source_provenance_missing")
    ids = []
    for src in sources:
        if (not isinstance(src, dict)
                or type(src.get("video_id")) is not int
                or not _valid_sha(src.get("source_sha256"))
                or src.get("source_rights_cleared") is not False
                or not isinstance(src.get("page_url"), str)
                or not src["page_url"].startswith("https://www.pexels.com/video/")):
            raise S01EditorialGateError("source_provenance_invalid")
        ids.append(src["video_id"])
    if len(set(ids)) != len(ids):
        raise S01EditorialGateError("duplicated_stock_source")
    known_hash = digest in LOCKED_REJECTIONS
    known_source_set = frozenset(ids) in LOCKED_REJECTIONS.values()
    previously_rejected = known_hash or known_source_set
    return {
        "editorial_decision": (
            "REJECTED_EDITORIAL_PREVIOUS_QA"
            if previously_rejected else "PENDING_HUMAN_FRAME_AND_RIGHTS_REVIEW"
        ),
        "release_gate": "BLOCKED_NOT_MASTER",
        "publication_authorized": False,
        "master_allowed": False,
        "reason": (
            "known_rejected_output_or_identical_stock_source_set"
            if previously_rejected else "new_preview_not_approved"
        ),
        "semantic_review_completed": False,
        "license_review_completed": False,
        "physical_sha_checked": movie_path is not None,
    }
