"""Fail-closed blocking gates for the Verbo no Chão production engine."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
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
CORE_GATES = ("clip_repetition", "audio_integrity", "video_decode", "subtitle_safe_area")


# Kokoro-82M is the locked default; ElevenLabs was owner-approved by ear (voice "Mark") on 2026-11-20.
ALLOWED_VOICE_ENGINES = {"Kokoro-82M", "ElevenLabs"}


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and set(value.casefold()) <= HEX64


def _add(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def _number(value: Any, label: str, errors: list[str]) -> float | None:
    if isinstance(value, bool):
        errors.append(f"{label} must be numeric")
        return None
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError):
        errors.append(f"{label} must be numeric")
        return None
    if not math.isfinite(result):
        errors.append(f"{label} must be finite")
        return None
    return result


def _object(value: Any, label: str, errors: list[str]) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    errors.append(f"{label} must be an object")
    return {}


def _unique(values: list[Any]) -> bool:
    try:
        return len(values) == len(set(values))
    except TypeError:
        return False


def _verify_artifact(path_value: Any, expected: Any, root: Path, label: str, errors: list[str]) -> None:
    _add(errors, isinstance(path_value, str) and bool(path_value.strip()), f"{label} path is missing")
    _add(errors, _is_sha256(expected), f"{label} sha256 is missing or invalid")
    if not isinstance(path_value, str) or not path_value.strip() or not _is_sha256(expected):
        return
    try:
        path = (root / path_value).resolve()
        path.relative_to(root.resolve())
        if not path.is_file():
            errors.append(f"{label} file does not exist: {path_value}")
            return
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1048576), b""):
                digest.update(chunk)
    except (ValueError, OSError):
        errors.append(f"{label} path is invalid, inaccessible or escapes artifact root")
        return
    _add(errors, digest.hexdigest() == expected, f"{label} sha256 does not match the file")


def validate_manifest(manifest: dict[str, Any], artifact_root: Path | None = None) -> list[str]:
    errors: list[str] = []
    if not isinstance(manifest, dict):
        return ["manifest must be an object"]

    _add(errors, manifest.get("engine_id") == "verbo-no-chao", "engine_id must be verbo-no-chao")
    state = manifest.get("state")
    _add(errors, isinstance(state, str) and state in ALLOWED_STATES, "state is not an allowed engine state")
    _add(
        errors,
        manifest.get("owner_approval") is False or manifest.get("state") == "PUBLISHED",
        "owner_approval cannot be true before PUBLISHED",
    )

    execution = _object(manifest.get("execution"), "execution", errors)
    _add(errors, execution.get("mode") == "cloud_only", "execution.mode must be cloud_only")
    _add(errors, execution.get("device_role") == "control_only", "execution.device_role must be control_only")
    _add(errors, execution.get("legacy_projects_used") is False, "legacy project usage is forbidden")

    assets = manifest.get("assets")
    _add(errors, isinstance(assets, list) and bool(assets), "assets must be a non-empty list")
    if isinstance(assets, list):
        asset_ids = [a.get("asset_id") for a in assets if isinstance(a, dict)]
        source_hashes = [a.get("source_hash") for a in assets if isinstance(a, dict)]
        source_urls = [a.get("source_url") for a in assets if isinstance(a, dict)]
        _add(errors, _unique(asset_ids), "duplicate asset_id or invalid asset_id detected; clip repetition gate failed")
        _add(errors, _unique(source_hashes), "duplicate source_hash or invalid source_hash detected; source repetition gate failed")
        _add(errors, _unique(source_urls), "duplicate source_url or invalid source_url detected; source repetition gate failed")
        for index, asset in enumerate(assets, start=1):
            if not isinstance(asset, dict):
                errors.append(f"asset {index} is not an object")
                continue
            for key in ("asset_id", "source_url", "source_hash", "in", "out", "rights_status"):
                _add(errors, key in asset, f"asset {index} missing {key}")
            _add(errors, _is_sha256(asset.get("source_hash")), f"asset {index} source_hash must be SHA-256")
            start = _number(asset.get("in"), f"asset {index} in", errors)
            end = _number(asset.get("out"), f"asset {index} out", errors)
            if start is not None:
                _add(errors, start >= 0, f"asset {index} in must be >= 0")
            if start is not None and end is not None:
                _add(errors, end > start, f"asset {index} interval must have out > in")

        # A provider-backed run must prove that each declared source hash matches
        # the actual materialized bytes. The historical pilot fixture deliberately
        # omits local paths and is validated without artifact_root.
        if artifact_root is not None:
            for index, asset in enumerate(assets, start=1):
                if not isinstance(asset, dict):
                    continue
                _add(errors, "path" in asset, f"asset {index} physical path is missing")
                if "path" in asset:
                    _verify_artifact(
                        asset.get("path"),
                        asset.get("source_hash"),
                        artifact_root,
                        f"asset {index}",
                        errors,
                    )

    audio = _object(manifest.get("audio"), "audio", errors)
    _add(errors, audio.get("engine") in ALLOWED_VOICE_ENGINES, "audio engine must remain Kokoro-82M")
    _add(errors, audio.get("language") == "pt-BR", "audio language must remain pt-BR")
    _add(errors, isinstance(audio.get("format"), str) and audio.get("format") in {"WAV 24 kHz mono float", "WAV 24 kHz mono PCM16"}, "audio format contract failed")
    _add(errors, audio.get("persisted") is True, "audio persistence is not proven")
    _add(errors, type(audio.get("segments")) is int and audio["segments"] > 0, "audio segment count is invalid")
    _add(errors, type(audio.get("duration_sec")) in (int, float) and math.isfinite(audio["duration_sec"]) and audio["duration_sec"] > 0, "audio duration is invalid")
    _add(errors, _is_sha256(audio.get("sha256")), "audio sha256 is missing or invalid")

    music = _object(manifest.get("music"), "music", errors)
    _add(errors, music.get("present") is True, "music gate failed: music is absent")
    _add(errors, music.get("ducking") is True, "music gate failed: voice ducking is not proven")
    _add(errors, _is_sha256(music.get("hash")), "music hash is missing or invalid")
    _add(errors, isinstance(music.get("license_status"), str) and music.get("license_status") in {"CLEARED", "PASS"}, "music license status is not cleared")
    if music.get("origin") == "original_procedural":
        _add(errors, music.get("external_samples") is False, "original procedural music cannot declare external samples")
    elif music.get("origin") == "licensed":
        _add(errors, bool(music.get("license_url")), "licensed music requires a license_url")
    else:
        errors.append("music origin is not supported")

    captions = _object(manifest.get("captions"), "captions", errors)
    _add(errors, captions.get("present") is True, "caption gate failed: captions are absent")
    _add(errors, captions.get("safe_area_pass") is True, "caption safe-area gate failed")
    _add(errors, captions.get("synchronized") is True, "caption synchronization gate failed")

    output = _object(manifest.get("output"), "output", errors)
    _add(errors, output.get("width") == 1080 and output.get("height") == 1920, "output must be 1080x1920")
    _add(errors, _is_sha256(output.get("sha256")), "output sha256 is missing or invalid")

    gates = _object(manifest.get("gates"), "gates", errors)
    for key in CORE_GATES:
        _add(errors, gates.get(key) == "PASS", f"{key} gate did not pass")

    rights = _object(manifest.get("rights"), "rights", errors)
    rights_clear = all(
        isinstance(rights.get(k), str) and rights.get(k) in PASS_RIGHTS
        for k in ("visual_review", "voice_review", "music_review", "monetization")
    )
    if isinstance(state, str) and state in PUBLISHABLE_STATES:
        _add(errors, rights_clear, "publishable state requires all summary rights gates cleared")
        if isinstance(assets, list):
            for index, asset in enumerate(assets, start=1):
                if isinstance(asset, dict):
                    _add(
                        errors,
                        isinstance(asset.get("rights_status"), str) and asset.get("rights_status") in PASS_RIGHTS,
                        f"publishable state requires asset {index} rights cleared",
                    )
        _add(
            errors,
            manifest.get("publication_authorized") is False or manifest.get("state") == "PUBLISHED",
            "publication_authorized can only be true in PUBLISHED state",
        )
    else:
        _add(errors, manifest.get("publication_authorized") is False, "publication must remain false before publication")

    if state == "PUBLISHED":
        _add(errors, manifest.get("owner_approval") is True, "PUBLISHED requires owner approval")
        _add(errors, manifest.get("publication_authorized") is True, "PUBLISHED requires publication authorization")

    # A cloud package is NOT physically validated just because its JSON says
    # "PASS". All four required media inputs must exist and match locked SHAs.
    if artifact_root is not None:
        artifacts = manifest.get("artifacts")
        expected_hashes = {
            "audio": audio.get("sha256"),
            "music": music.get("hash"),
            "output": output.get("sha256"),
        }
        source_paths = {
            "audio": audio.get("path"),
            "music": music.get("path"),
            "captions": captions.get("path"),
            "output": output.get("file"),
        }
        for key in ("audio", "music", "captions", "output"):
            item = artifacts.get(key) if isinstance(artifacts, dict) else None
            if not isinstance(item, dict):
                errors.append(f"artifact.{key} is required for physical cloud runs")
                continue
            _verify_artifact(item.get("path"), item.get("sha256"), artifact_root, f"artifact.{key}", errors)
            if key in expected_hashes and item.get("sha256") != expected_hashes[key]:
                errors.append(f"artifact.{key} SHA conflicts with declared source manifest")
            if not isinstance(source_paths[key], str) or source_paths[key] != item.get("path"):
                errors.append(f"artifact.{key} path conflicts with rendering source")

        # Upscaling a low-res preview to 1080x1920 does NOT create a
        # native high-quality master. Validate source media bytes directly.
        if isinstance(state, str) and state in PUBLISHABLE_STATES and isinstance(assets, list):
            from media.probe import ProbeError, probe_media
            for index, asset in enumerate(assets, 1):
                if not isinstance(asset, dict) or not isinstance(asset.get("path"), str):
                    continue
                try:
                    source_path = (artifact_root / asset["path"]).resolve()
                    source_path.relative_to(artifact_root.resolve())
                    media = probe_media(source_path)
                    video = next((x for x in media.get("streams", [])
                                  if x.get("codec_type") == "video"), None)
                    if not isinstance(video, dict):
                        errors.append(f"release:asset:{index}:no_video_stream")
                        continue
                    width, height = video.get("width"), video.get("height")
                    if type(width) is not int or type(height) is not int or width < 1080 or height < 1920:
                        errors.append(f"release:asset:{index}:source_below_native_master_resolution")
                    source_duration = float((media.get("format") or {}).get("duration") or 0)
                    source_end = _number(asset.get("out"), f"asset {index} out", errors)
                    if source_end is None or not math.isfinite(source_duration) or source_end > source_duration + 0.03:
                        errors.append(f"release:asset:{index}:insufficient_real_temporal_coverage")
                except (ProbeError, ValueError, TypeError, OSError):
                    errors.append(f"release:asset:{index}:source_probe_failed")

        # Any advertised preview or release must be an actual decodable
        # audiovisual file; self-declared video_decode PASS never suffices.
        if state in {"PREVIEW_READY", "READY_FOR_OWNER_APPROVAL", "PUBLISHED"}:
            output_item = artifacts.get("output") if isinstance(artifacts, dict) else None
            if isinstance(output_item, dict) and isinstance(output_item.get("path"), str):
                video_path = (artifact_root / output_item["path"]).resolve()
                try:
                    video_path.relative_to(artifact_root.resolve())
                    from media.probe import validate_rendered_video
                    errors.extend(x if x.startswith("media:") else "media:" + x for x in validate_rendered_video(video_path))
                    decoder = shutil.which("ffmpeg")
                    if decoder is None:
                        errors.append("release:ffmpeg_decoder_unavailable")
                    elif video_path.is_file():
                        decoded = subprocess.run(
                            [decoder, "-nostdin", "-v", "error", "-xerror",
                             "-i", str(video_path), "-map", "0", "-f", "null", "-"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                            timeout=240, check=False,
                        )
                        if decoded.returncode != 0:
                            errors.append("release:full_media_decode_failed")
                except (ValueError, OSError, subprocess.TimeoutExpired):
                    errors.append("release:full_media_decode_failed")
    elif isinstance(state, str) and state in PUBLISHABLE_STATES:
        errors.append("release:physical_media_root_required")

    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Verbo no Chão engine gates")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--artifact-root", type=Path, default=None)
    args = parser.parse_args()
    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"BLOCKED: cannot read manifest: {exc}", file=sys.stderr)
        return 2
    errors = validate_manifest(data, args.artifact_root)
    if errors:
        print("BLOCKED")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"PASS: {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
