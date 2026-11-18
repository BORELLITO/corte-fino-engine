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
from orchestrator.render import RenderError, render_package


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
    # Defaults are allowed, but NEVER overwrite explicit adverse flags.
    # Earlier code silently changed legacy_projects_used=True to False.
    manifest.setdefault("execution", {
        "mode": "cloud_only",
        "device_role": "control_only",
        "legacy_projects_used": False,
    })
    manifest.setdefault("owner_approval", False)
    manifest.setdefault("publication_authorized", False)

    # The provider's claimed digests are untrusted evidence. Keep them as-is
    # so validate_manifest can compare them against actual physical bytes.
    # Rehashing into the same declaration would hide tampering.
    manifest.setdefault("artifacts", {})
    return manifest


def _preflight_untrusted_media(package_dir: Path, package: dict[str, Any]) -> list[str]:
    """Check source bytes before invoking FFmpeg; never trust self-certified hashes."""
    errors: list[str] = []
    root = package_dir.resolve()

    def check(path: Any, expected: Any, label: str) -> None:
        if not isinstance(path, str) or not path.strip():
            errors.append(f"{label}:missing_path")
            return
        if not isinstance(expected, str) or len(expected) != 64 or any(
            c not in "0123456789abcdef" for c in expected
        ):
            errors.append(f"{label}:missing_sha256")
            return
        target = (root / path).resolve()
        try:
            target.relative_to(root)
        except ValueError:
            errors.append(f"{label}:path_escape")
            return
        if not target.is_file():
            errors.append(f"{label}:missing_file")
            return
        if _artifact_hash(target) != expected:
            errors.append(f"{label}:sha256_mismatch")

    assets = package.get("assets")
    if not isinstance(assets, list) or not assets:
        return []  # Preserve render:assets_missing diagnostic.
    for i, asset in enumerate(assets, 1):
        if not isinstance(asset, dict):
            errors.append(f"asset:{i}:not_object")
            continue
        check(asset.get("path"), asset.get("source_hash"), f"asset:{i}")

    artifacts = package.get("artifacts")
    for label, hash_field in (("audio", "sha256"), ("music", "hash")):
        media = package.get(label)
        if not isinstance(media, dict):
            errors.append(f"{label}:not_object")
            continue
        media_item = artifacts.get(label) if isinstance(artifacts, dict) else None
        if not isinstance(media_item, dict) or media_item.get("path") != media.get("path"):
            errors.append(f"{label}:artifact_binding_missing")
        check(media.get("path"), media.get(hash_field), label)
    captions = package.get("captions")
    subtitle = artifacts.get("captions") if isinstance(artifacts, dict) else None
    if not isinstance(captions, dict) or not isinstance(subtitle, dict) or (
        subtitle.get("path") != captions.get("path")
    ):
        errors.append("captions:artifact_binding_missing")
    else:
        check(subtitle.get("path"), subtitle.get("sha256"), "captions")
    return sorted(set(errors))


def _write_blocked(
    result: RunResult,
    report_path: Path,
) -> RunResult:
    report_path.write_text(
        json.dumps(result.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def run_flow(
    brief: dict[str, Any],
    package_dir: Path,
    report_dir: Path,
    *,
    render: bool = False,
) -> RunResult:
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
        result = RunResult(
            run_id,
            "BLOCKED",
            "BLOCKED",
            str(manifest_path),
            tuple(sorted(set(errors))),
            provider_status,
        )
        return _write_blocked(result, report_path)

    provider_status = "MATERIALIZED"
    # This runflow has NO publisher integration. The provider cannot certify a
    # PUBLISHED state merely by writing JSON or setting owner_approval=True.
    if package.get("state") == "PUBLISHED":
        errors.append("runflow:publication_requires_separate_authorized_publisher")
    for key in ("execution", "artifacts", "output"):
        if key in package and not isinstance(package[key], dict):
            errors.append(f"provider_package:{key}:not_object")
    if errors:
        result = RunResult(
            run_id, "BLOCKED", "BLOCKED", str(manifest_path),
            tuple(sorted(set(errors))), provider_status,
        )
        return _write_blocked(result, report_path)

    should_render = render or (
        isinstance(package.get("render"), dict) and package["render"].get("enabled") is True
    )
    if should_render:
        errors.extend(_preflight_untrusted_media(package_dir, package))
        if errors:
            result = RunResult(
                run_id, "BLOCKED", "BLOCKED", str(manifest_path),
                tuple(sorted(set(errors))), provider_status,
            )
            return _write_blocked(result, report_path)
    if should_render:
        try:
            rendered = render_package(package_dir, package)
        except RenderError as exc:
            errors.append(str(exc))
            result = RunResult(
                run_id,
                "BLOCKED",
                "BLOCKED",
                str(manifest_path),
                tuple(sorted(set(errors))),
                provider_status,
            )
            return _write_blocked(result, report_path)
        package.setdefault("output", {}).update(
            {
                "file": rendered["file"],
                "duration_sec": rendered["duration_sec"],
                "width": rendered["width"],
                "height": rendered["height"],
                "sha256": rendered["sha256"],
            }
        )
        package.setdefault("artifacts", {})["output"] = {
            "path": rendered["file"],
            "sha256": rendered["sha256"],
            "physical_validation": rendered["physical_validation"],
        }

    manifest = _materialize_manifest(package_dir, package, run_id)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    errors.extend(validate_manifest(manifest, artifact_root=package_dir))
    if errors:
        state = "BLOCKED"
        status = "BLOCKED"
    else:
        state = manifest.get("state", "PREVIEW_READY")
        status = "PASS"
    result = RunResult(
        run_id,
        status,
        state,
        str(manifest_path),
        tuple(sorted(set(errors))),
        provider_status,
    )
    report_path.write_text(
        json.dumps(result.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Verbo no Chão cloud production gate")
    parser.add_argument("--brief", required=True, type=Path, help="JSON brief for this run")
    parser.add_argument("--package-dir", required=True, type=Path, help="provider materialization directory")
    parser.add_argument("--report-dir", default=Path("run-reports"), type=Path)
    parser.add_argument("--render", action="store_true", help="assemble and physically validate the vertical MP4")
    args = parser.parse_args()

    brief, errors = _read_json(args.brief, "brief")
    if brief is None:
        print("BLOCKED")
        for error in errors:
            print(f"- {error}")
        return 1

    result = run_flow(
        brief,
        args.package_dir,
        args.report_dir,
        render=args.render,
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
