"""Cloud runflow coordinator.

This module is intentionally fail-closed. It never invents media. A provider adapter
must materialize a package directory containing the declared files before the run can
be promoted to PREVIEW_READY or READY_FOR_OWNER_APPROVAL.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from engine.quality_gates import validate_manifest


@dataclass(frozen=True)
class RunResult:
    run_id: str
    status: str
    state: str
    manifest_path: str
    errors: tuple[str, ...]
    provider_status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _run_id(brief: dict[str, Any]) -> str:
    payload = json.dumps(brief, ensure_ascii=False, sort_keys=True).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()[:12]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"vnc-{stamp}-{digest}-{uuid.uuid4().hex[:6]}"


def _read_json(path: Path, label: str) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, [f"{label}:missing:{path}"]
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"{label}:invalid:{exc}"]
    if not isinstance(value, dict):
        return None, [f"{label}:not_object"]
    return value, []


def _artifact_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _materialize_manifest(package_dir: Path, package: dict[str, Any], run_id: str) -> dict[str, Any]:
    manifest = json.loads(json.dumps(package))
    manifest["run_id"] = run_id
    manifest["execution"] = {
        **(manifest.get("execution") or {}),
        "mode": "cloud_only",
        "device_role": "control_only",
        "legacy_projects_used": False,
    }
    manifest.setdefault("owner_approval", False)
    manifest.setdefault("publication_authorized", False)

    artifacts = manifest.get("artifacts") or {}
    if not isinstance(artifacts, dict):
        artifacts = {}
    for key in ("audio", "music", "captions", "output"):
        item = artifacts.get(key)
        if not isinstance(item, dict):
            continue
        relative = item.get("path")
        if isinstance(relative, str):
            target = (package_dir / relative).resolve()
            if target.is_file():
                item["sha256"] = _artifact_hash(target)
    manifest["artifacts"] = artifacts
    return manifest


def run_flow(brief: dict[str, Any], package_dir: Path, report_dir: Path) -> RunResult:
    run_id = _run_id(brief)
    report_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = report_dir / f"{run_id}.manifest.json"
    report_path = report_dir / f"{run_id}.report.json"
    errors: list[str] = []

    package_path = package_dir / "package.json"
    package, package_errors = _read_json(package_path, "provider_package")
    errors.extend(package_errors)
    provider_status = "NOT_CONFIGURED"

    if package is None:
        errors.append(
            "provider_package:required:an approved cloud provider must materialize "
            "package.json and media artifacts before validation"
        )
        result = RunResult(run_id, "BLOCKED", "BLOCKED", str(manifest_path), tuple(sorted(set(errors))), provider_status)
        report_path.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return result

    provider_status = "MATERIALIZED"
    manifest = _materialize_manifest(package_dir, package, run_id)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    errors.extend(validate_manifest(manifest, artifact_root=package_dir))
    if errors:
        state = "BLOCKED"
        status = "BLOCKED"
    else:
        state = manifest.get("state", "PREVIEW_READY")
        status = "PASS"
    result = RunResult(run_id, status, state, str(manifest_path), tuple(sorted(set(errors))), provider_status)
    report_path.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Verbo no Chão cloud production gate")
    parser.add_argument("--brief", required=True, type=Path, help="JSON brief for this run")
    parser.add_argument("--package-dir", required=True, type=Path, help="provider materialization directory")
    parser.add_argument("--report-dir", default=Path("run-reports"), type=Path)
    args = parser.parse_args()

    brief, errors = _read_json(args.brief, "brief")
    if brief is None:
        print("BLOCKED")
        for error in errors:
            print(f"- {error}")
        return 1

    result = run_flow(brief, args.package_dir, args.report_dir)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
