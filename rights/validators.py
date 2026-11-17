"""Deterministic rights validation for media assets."""

from __future__ import annotations

from typing import Any

REQUIRED_RIGHTS = (
    "asset_id",
    "source",
    "license",
    "commercial_use",
    "evidence_ref",
    "status",
)


def validate_rights_record(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return ["rights:not_object"]
    errors = []
    for key in REQUIRED_RIGHTS:
        value = payload.get(key)
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(f"rights:{key}")
    if payload.get("commercial_use") is not True:
        errors.append("rights:commercial_use")
    if payload.get("status") != "CLEARED":
        errors.append("rights:status")
    return sorted(set(errors))
