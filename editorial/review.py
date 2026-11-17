"""Automated editorial review for a draft script."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

REQUIRED_ORDER = (
    "opening",
    "connection",
    "biblical_reference",
    "reflection",
    "application",
    "conclusion",
)

FORBIDDEN_PHRASES = (
    "milagre garantido",
    "vai curar",
    "prosperidade garantida",
    "deus me revelou",
    "se você tiver fé, isso acontecerá",
)


@dataclass(frozen=True)
class ScriptReview:
    status: str
    word_count: int
    estimated_seconds: float
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "word_count": self.word_count,
            "estimated_seconds": self.estimated_seconds,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


def _words(text: str) -> list[str]:
    return re.findall(r"\b[\wÀ-ÿ'-]+\b", text)


def review_script(payload: Any) -> ScriptReview:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(payload, dict):
        return ScriptReview("NO_GO", 0, 0.0, ("review:not_object",), ())

    blocks = payload.get("blocks")
    if not isinstance(blocks, list):
        return ScriptReview("NO_GO", 0, 0.0, ("review:blocks",), ())

    block_map = {item.get("type"): item.get("text", "") for item in blocks if isinstance(item, dict)}
    if tuple(block_map) != REQUIRED_ORDER:
        errors.append("review:block_order")
    if any(not isinstance(block_map.get(name), str) or not block_map[name].strip() for name in REQUIRED_ORDER):
        errors.append("review:empty_block")

    full_text = " ".join(block_map.get(name, "") for name in REQUIRED_ORDER)
    word_count = len(_words(full_text))
    estimated_seconds = round(word_count / 2.25, 1)

    target = payload.get("duration_target_seconds")
    if target not in {70, 75, 78}:
        errors.append("review:duration_target")
    else:
        lower = target * 0.85
        upper = target * 1.15
        if not lower <= estimated_seconds <= upper:
            errors.append("review:estimated_duration")

    lowered = full_text.casefold()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lowered:
            errors.append(f"review:forbidden_phrase:{phrase}")

    if payload.get("contains_verbatim_quote") is not False:
        errors.append("review:verbatim_quote")
    if payload.get("source_mode") != "reference_and_paraphrase":
        errors.append("review:source_mode")
    if payload.get("status") not in {"DRAFT_REVIEW_REQUIRED", "APPROVED_FOR_AUDIO"}:
        warnings.append("review:status_not_ready")

    return ScriptReview(
        "PASS_AUTOMATED_REVIEW" if not errors else "NO_GO",
        word_count,
        estimated_seconds,
        tuple(sorted(set(errors))),
        tuple(sorted(set(warnings))),
    )
