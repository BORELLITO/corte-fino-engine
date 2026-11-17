"""Deterministic validation for editorial and biblical packages."""

from __future__ import annotations

from typing import Any

REQUIRED_EDITORIAL = (
    "video_id",
    "audience",
    "theme",
    "opening",
    "biblical_basis",
    "reflection",
    "application",
    "conclusion",
    "language",
    "format",
    "duration_seconds",
    "originality",
    "safety",
)

REQUIRED_BIBLICAL = (
    "reference",
    "translation",
    "context",
    "textual_basis",
    "interpretation",
    "application",
    "certainty",
)

FORBIDDEN_SAFETY_FLAGS = (
    "invented_revelation",
    "guaranteed_miracle",
    "prosperity_guarantee",
    "fear_manipulation",
    "medical_substitute",
)


def _missing_text(payload: dict[str, Any], keys: tuple[str, ...]) -> list[str]:
    return [
        key for key in keys
        if not isinstance(payload.get(key), str) or not payload[key].strip()
    ]


def validate_biblical_basis(basis: Any) -> list[str]:
    if not isinstance(basis, dict):
        return ["biblical_basis:not_object"]
    errors = [f"biblical_basis:{key}" for key in _missing_text(basis, REQUIRED_BIBLICAL)]
    safety = basis.get("safety", {})
    if not isinstance(safety, dict):
        errors.append("biblical_basis:safety_not_object")
    else:
        errors.extend(
            f"biblical_basis:forbidden_safety:{flag}"
            for flag in FORBIDDEN_SAFETY_FLAGS
            if safety.get(flag) is True
        )
    return errors


def validate_editorial_package(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return ["editorial:not_object"]
    errors = [f"editorial:{key}" for key in _missing_text(payload, REQUIRED_EDITORIAL)]
    errors.extend(validate_biblical_basis(payload.get("biblical_basis")))
    if payload.get("language") != "pt-BR":
        errors.append("editorial:language")
    if payload.get("format") not in {"short", "long"}:
        errors.append("editorial:format")
    duration = payload.get("duration_seconds")
    if not isinstance(duration, int) or not 15 <= duration <= 900:
        errors.append("editorial:duration_seconds")
    if payload.get("originality") != "ORIGINAL":
        errors.append("editorial:originality")
    safety = payload.get("safety")
    if not isinstance(safety, dict):
        errors.append("editorial:safety_not_object")
    else:
        errors.extend(
            f"editorial:forbidden_safety:{flag}"
            for flag in FORBIDDEN_SAFETY_FLAGS
            if safety.get(flag) is True
        )
    return sorted(set(errors))
