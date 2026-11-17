"""Release-candidate gate for non-fixture packages."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from orchestrator.dry_run import run_dry_run
from rights.validators import validate_rights_record


@dataclass(frozen=True)
class ReleaseGateResult:
    status: str
    errors: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status, "errors": list(self.errors)}


def _pending(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return True
    lowered = value.casefold()
    return any(marker in lowered for marker in ("confirmar", "pendente", "a definir", "fixture_only"))


def validate_release_candidate(payload: Any) -> ReleaseGateResult:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ReleaseGateResult("NO_GO", ("release:not_object",))

    if payload.get("fixture_mode") is True:
        errors.append("release:fixture_mode")
    if payload.get("publication_requested") is True:
        errors.append("release:publication_requested")

    editorial = payload.get("editorial")
    if not isinstance(editorial, dict):
        errors.append("release:editorial")
    else:
        if editorial.get("originality") != "ORIGINAL":
            errors.append("release:originality")
        basis = editorial.get("biblical_basis")
        if not isinstance(basis, dict):
            errors.append("release:biblical_basis")
        else:
            if _pending(basis.get("translation")):
                errors.append("release:translation")
            if _pending(basis.get("source_ref")):
                errors.append("release:biblical_source_ref")

    rights = payload.get("rights")
    if not isinstance(rights, list) or not rights:
        errors.append("release:rights")
    else:
        for record in rights:
            errors.extend(
                f"release:{item}"
                for item in validate_rights_record(record, allow_fixture=False)
            )

    audiovisual = payload.get("audiovisual")
    if not isinstance(audiovisual, dict):
        errors.append("release:audiovisual")
    else:
        audio = audiovisual.get("audio")
        if not isinstance(audio, dict):
            errors.append("release:audio")
        else:
            for label in ("voice", "music"):
                item = audio.get(label)
                if not isinstance(item, dict):
                    errors.append(f"release:{label}")
                    continue
                if item.get("commercial_use") is not True:
                    errors.append(f"release:{label}:commercial_use")
                if _pending(item.get("evidence_ref")):
                    errors.append(f"release:{label}:evidence_ref")

    dry_run = run_dry_run(payload)
    if dry_run.status != "PASS":
        errors.extend(f"release:dry_run:{item}" for item in dry_run.errors)

    unique = tuple(sorted(set(errors)))
    return ReleaseGateResult("PASS" if not unique else "NO_GO", unique)
