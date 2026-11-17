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


def validate_rights_record(payload: Any, *, allow_fixture: bool = False) -> list[str]:
    if not isinstance(payload, dict):
        return ["rights:not_object"]
    errors = []
    for key in REQUIRED_RIGHTS:
        value = payload.get(key)
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(f"rights:{key}")

    status = payload.get("status")
    if status == "FIXTURE_ONLY":
        if not allow_fixture:
            errors.append("rights:status")
        if payload.get("evidence_ref") != "FIXTURE_ONLY":
            errors.append("rights:fixture_evidence")
        return sorted(set(errors))

    if payload.get("commercial_use") is not True:
        errors.append("rights:commercial_use")
    if status != "CLEARED":
        errors.append("rights:status")
    return sorted(set(errors))
