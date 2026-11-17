"""Non-publishing orchestration of the validated Verbo no Chão contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from editorial.validators import validate_editorial_package
from media.validators import validate_audiovisual_package
from orchestrator.state_machine import StateMachine
from rights.validators import validate_rights_record

ROOT = Path(__file__).resolve().parents[1]
STATE_CONTRACT = ROOT / "contracts" / "state_machine.json"


@dataclass(frozen=True)
class DryRunResult:
    status: str
    state: str
    gates: dict[str, str]
    errors: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_dry_run(payload: Any) -> DryRunResult:
    errors: list[str] = []
    gates = {
        "editorial": "NOT_RUN",
        "rights": "NOT_RUN",
        "audiovisual": "NOT_RUN",
        "publication": "NOT_RUN",
    }

    if not isinstance(payload, dict):
        return DryRunResult("BLOCKED", "BLOCKED", gates, ("run:not_object",))

    editorial_errors = validate_editorial_package(payload.get("editorial"))
    if editorial_errors:
        errors.extend(editorial_errors)
        gates["editorial"] = "BLOCKED"
    else:
        gates["editorial"] = "PASS"

    rights_records = payload.get("rights")
    rights_errors: list[str] = []
    if not isinstance(rights_records, list) or not rights_records:
        rights_errors.append("rights:records")
    else:
        index = {}
        for record in rights_records:
            rights_errors.extend(validate_rights_record(record))
            if isinstance(record, dict) and record.get("asset_id"):
                index[record["asset_id"]] = record

        audiovisual = payload.get("audiovisual")
        scenes = audiovisual.get("scenes", []) if isinstance(audiovisual, dict) else []
        for scene in scenes if isinstance(scenes, list) else []:
            if not isinstance(scene, dict):
                rights_errors.append("rights:scene_not_object")
                continue
            asset_id = scene.get("rights_ref")
            if asset_id not in index:
                rights_errors.append(f"rights:missing_reference:{asset_id}")

    if rights_errors:
        errors.extend(rights_errors)
        gates["rights"] = "BLOCKED"
    else:
        gates["rights"] = "PASS"

    audiovisual_errors = validate_audiovisual_package(payload.get("audiovisual"))
    if audiovisual_errors:
        errors.extend(audiovisual_errors)
        gates["audiovisual"] = "BLOCKED"
    else:
        gates["audiovisual"] = "PASS"

    if payload.get("publication_requested") is True:
        errors.append("publication:not_allowed_in_dry_run")
        gates["publication"] = "BLOCKED"
    else:
        gates["publication"] = "PASS"

    if errors:
        return DryRunResult("BLOCKED", "BLOCKED", gates, tuple(sorted(set(errors))))

    machine = StateMachine.from_contract(STATE_CONTRACT)
    machine = machine.transition("INTERNAL_VALIDATED")
    return DryRunResult("PASS", machine.current, gates, ())
