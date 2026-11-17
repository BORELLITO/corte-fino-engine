"""Blocking quality gates for the Verbo no Chão production engine."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ALLOWED_STATES = {
    "PLANNED", "IN_PROGRESS", "BLOCKED", "PREVIEW_READY",
    "READY_FOR_OWNER_APPROVAL", "PUBLISHED", "REJECTED",
}
PUBLISHABLE_STATES = {"READY_FOR_OWNER_APPROVAL", "PUBLISHED"}
PASS_RIGHTS = {"CLEARED", "PASS"}
HEX64 = set("0123456789abcdef")


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and set(value) <= HEX64


def _add(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    _add(errors, manifest.get("engine_id") == "verbo-no-chao", "engine_id must be verbo-no-chao")
    _add(errors, manifest.get("state") in ALLOWED_STATES, "state is not an allowed engine state")
    _add(errors, manifest.get("owner_approval") is False or manifest.get("state") == "PUBLISHED", "owner_approval cannot be true before PUBLISHED")

    execution = manifest.get("execution") or {}
    _add(errors, execution.get("mode") == "cloud_only", "execution.mode must be cloud_only")
    _add(errors, execution.get("device_role") == "control_only", "execution.device_role must be control_only")
    _add(errors, execution.get("legacy_projects_used") is False, "legacy project usage is forbidden")

    assets = manifest.get("assets")
    _add(errors, isinstance(assets, list) and bool(assets), "assets must be a non-empty list")
    if isinstance(assets, list):
        asset_ids = [a.get("asset_id") for a in assets if isinstance(a, dict)]
        source_hashes = [a.get("source_hash") for a in assets if isinstance(a, dict)]
        _add(errors, len(asset_ids) == len(set(asset_ids)), "duplicate asset_id detected; clip repetition gate failed")
        _add(errors, len(source_hashes) == len(set(source_hashes)), "duplicate source_hash detected; source repetition gate failed")
        for index, asset in enumerate(assets, start=1):
            if not isinstance(asset, dict):
                errors.append(f"asset {index} is not an object")
                continue
            for key in ("asset_id", "source_url", "source_hash", "in", "out", "rights_status"):
                _add(errors, key in asset, f"asset {index} missing {key}")
            _add(errors, _is_sha256(asset.get("source_hash")), f"asset {index} source_hash must be SHA-256")
            if "in" in asset and "out" in asset:
                _add(errors, float(asset["out"]) > float(asset["in"]), f"asset {index} interval must have out > in")

    audio = manifest.get("audio") or {}
    _add(errors, audio.get("engine") == "Kokoro-82M", "audio engine must remain Kokoro-82M")
    _add(errors, audio.get("language") == "pt-BR", "audio language must remain pt-BR")
    _add(errors, audio.get("format") == "WAV 24 kHz mono float", "audio format contract failed")
    _add(errors, audio.get("persisted") is True, "audio persistence is not proven")
    _add(errors, isinstance(audio.get("segments"), int) and audio["segments"] > 0, "audio segment count is invalid")
    _add(errors, isinstance(audio.get("duration_sec"), (int, float)) and audio["duration_sec"] > 0, "audio duration is invalid")
    _add(errors, _is_sha256(audio.get("sha256")), "audio sha256 is missing or invalid")

    music = manifest.get("music") or {}
    _add(errors, music.get("present") is True, "music gate failed: music is absent")
    _add(errors, music.get("ducking") is True, "music gate failed: voice ducking is not proven")
    _add(errors, _is_sha256(music.get("hash")), "music hash is missing or invalid")
    if music.get("origin") == "original_procedural":
        _add(errors, music.get("external_samples") is False, "original procedural music cannot declare external samples")
    elif music.get("origin") == "licensed":
        _add(errors, bool(music.get("license_url")), "licensed music requires a license_url")
    else:
        errors.append("music origin is not supported")

    captions = manifest.get("captions") or {}
    _add(errors, captions.get("present") is True, "caption gate failed: captions are absent")
    _add(errors, captions.get("safe_area_pass") is True, "caption safe-area gate failed")
    _add(errors, captions.get("synchronized") is True, "caption synchronization gate failed")

    output = manifest.get("output") or {}
    _add(errors, output.get("width") == 1080 and output.get("height") == 1920, "output must be 1080x1920")
    _add(errors, _is_sha256(output.get("sha256")), "output sha256 is missing or invalid")

    gates = manifest.get("gates") or {}
    for key in ("clip_repetition", "audio_integrity", "video_decode", "subtitle_safe_area"):
        _add(errors, gates.get(key) == "PASS", f"{key} gate did not pass")

    rights = manifest.get("rights") or {}
    rights_clear = all(rights.get(k) in PASS_RIGHTS for k in ("visual_review", "voice_review", "music_review", "monetization"))
    if manifest.get("state") in PUBLISHABLE_STATES:
        _add(errors, rights_clear, "publishable state requires all rights gates cleared")
        _add(errors, manifest.get("publication_authorized") is False or manifest.get("state") == "PUBLISHED", "publication_authorized can only be true in PUBLISHED state")
    else:
        _add(errors, manifest.get("publication_authorized") is False, "publication must remain false before publication")

    if manifest.get("state") == "PUBLISHED":
        _add(errors, manifest.get("owner_approval") is True, "PUBLISHED requires owner approval")
        _add(errors, manifest.get("publication_authorized") is True, "PUBLISHED requires publication authorization")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Verbo no Chão engine gates")
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"BLOCKED: cannot read manifest: {exc}", file=sys.stderr)
        return 2
    errors = validate_manifest(data)
    if errors:
        print("BLOCKED")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"PASS: {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
