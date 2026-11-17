"""Validation of original narrative packages before audio generation."""

from __future__ import annotations

from typing import Any

REQUIRED_BLOCKS = (
    "opening",
    "connection",
    "biblical_reference",
    "reflection",
    "application",
    "conclusion",
)


def validate_script_package(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return ["script:not_object"]

    errors = []
    for key in (
        "script_id",
        "status",
        "source_decision_ref",
        "source_mode",
        "contains_verbatim_quote",
        "duration_target_seconds",
        "blocks",
    ):
        value = payload.get(key)
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(f"script:{key}")

    if payload.get("status") != "DRAFT_REVIEW_REQUIRED":
        errors.append("script:status")
    if payload.get("source_mode") != "reference_and_paraphrase":
        errors.append("script:source_mode")
    if payload.get("contains_verbatim_quote") is not False:
        errors.append("script:contains_verbatim_quote")
    if payload.get("duration_target_seconds") not in {70, 75, 78}:
        errors.append("script:duration_target_seconds")

    blocks = payload.get("blocks")
    if not isinstance(blocks, list):
        errors.append("script:blocks")
        return sorted(set(errors))

    found = set()
    for index, block in enumerate(blocks):
        if not isinstance(block, dict):
            errors.append(f"script:block:{index}:not_object")
            continue
        block_type = block.get("type")
        text = block.get("text")
        if block_type in found:
            errors.append(f"script:block_duplicate:{block_type}")
        if block_type:
            found.add(block_type)
        else:
            errors.append(f"script:block:{index}:type")
        if not isinstance(text, str) or not text.strip():
            errors.append(f"script:block:{index}:text")

    for block_type in REQUIRED_BLOCKS:
        if block_type not in found:
            errors.append(f"script:block_missing:{block_type}")

    return sorted(set(errors))
