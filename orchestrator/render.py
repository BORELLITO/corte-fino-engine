"""Deterministic cloud render stage for a validated provider package."""
from __future__ import annotations

import hashlib
import json
import math
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any

from media.probe import ProbeError, probe_media, validate_rendered_video


class RenderError(RuntimeError):
    pass


def _binary(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RenderError(f"{name}:not_available")
    return path


def _safe_path(root: Path, relative: Any, label: str) -> Path:
    if not isinstance(relative, str) or not relative.strip():
        raise RenderError(f"{label}:path_missing")
    target = (root / relative).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError as exc:
        raise RenderError(f"{label}:path_escape") from exc
    if not target.is_file():
        raise RenderError(f"{label}:missing:{relative}")
    return target


def _escape_subtitle_path(path: Path) -> str:
    # ffmpeg's subtitles filter uses single-quoted filter arguments.
    return str(path).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render_package(package_dir: Path, package: dict[str, Any]) -> dict[str, Any]:
    assets = package.get("assets")
    if not isinstance(assets, list) or not assets:
        raise RenderError("render:assets_missing")

    output_spec = package.get("output") or {}
    if not isinstance(output_spec, dict):
        raise RenderError("render:output_spec_not_object")
    output_file = output_spec.get("file", "output.mp4")
    if not isinstance(output_file, str) or not output_file.strip():
        raise RenderError("render:output_path_invalid")
    try:
        output = (package_dir / output_file).resolve()
    except (OSError, ValueError) as exc:
        raise RenderError("render:output_path_invalid") from exc
    try:
        output.relative_to(package_dir.resolve())
    except ValueError as exc:
        raise RenderError("render:output_path_escape") from exc
    if output.exists():
        raise RenderError("render:refuse_overwrite_existing_output")
    output.parent.mkdir(parents=True, exist_ok=True)

    inputs: list[str] = []
    filters: list[str] = []
    for index, asset in enumerate(assets):
        if not isinstance(asset, dict):
            raise RenderError(f"render:asset:{index}:not_object")
        path = _safe_path(package_dir, asset.get("path"), f"asset:{index}")
        if path == output:
            raise RenderError("render:output_collides_with_visual_source")
        try:
            start = float(asset.get("in", 0))
            end = float(asset["out"])
        except (KeyError, TypeError, ValueError) as exc:
            raise RenderError(f"render:asset:{index}:interval_invalid") from exc
        duration = end - start
        if not math.isfinite(start) or not math.isfinite(end) or start < 0 or duration <= 0:
            raise RenderError(f"render:asset:{index}:interval_invalid")
        inputs.extend(["-stream_loop", "-1", "-i", str(path)])
        filters.append(
            f"[{index}:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,setsar=1,fps=30,trim=start={start}:duration={duration},"
            f"setpts=PTS-STARTPTS[v{index}]"
        )

    audio = package.get("audio") or {}
    music = package.get("music") or {}
    captions = package.get("captions") or {}
    voice_path = _safe_path(package_dir, audio.get("path"), "audio")
    music_path = _safe_path(package_dir, music.get("path"), "music")
    caption_path = _safe_path(package_dir, captions.get("path"), "captions")
    if output in (voice_path, music_path, caption_path):
        raise RenderError("render:output_collides_with_audio_or_caption")

    concat_inputs = "".join(f"[v{i}]" for i in range(len(assets)))
    filters.append(f"{concat_inputs}concat=n={len(assets)}:v=1:a=0[vbase]")
    filters.append(f"[vbase]subtitles='{_escape_subtitle_path(caption_path)}':force_style='Alignment=2,MarginV=220,FontSize=42,Outline=2,Shadow=1'[vout]")
    voice_index = len(assets)
    music_index = len(assets) + 1
    # Sidechain compression is genuine, voice-driven music ducking; a fixed
    # music volume alone cannot truthfully satisfy the ducking requirement.
    filters.append(f"[{voice_index}:a]aresample=24000,volume=1.0,asplit=2[voice][duckkey]")
    filters.append(f"[{music_index}:a]aresample=24000,volume=0.12[music]")
    filters.append("[music][duckkey]sidechaincompress=threshold=0.035:ratio=8:attack=20:release=250[ducked]")
    filters.append("[voice][ducked]amix=inputs=2:duration=first:dropout_transition=2,alimiter=limit=0.96[aout]")

    command = [
        _binary("ffmpeg"), "-y",
        *inputs,
        "-i", str(voice_path),
        "-i", str(music_path),
        "-filter_complex", ";".join(filters),
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        str(output),
    ]
    completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=900)
    if completed.returncode != 0:
        tail = completed.stderr[-2000:].strip()
        raise RenderError(f"render:ffmpeg_failed:{tail}")
    physical_errors = validate_rendered_video(output)
    if physical_errors:
        raise RenderError("render:physical_validation:" + "|".join(physical_errors))
    probe = probe_media(output)
    duration = float((probe.get("format") or {}).get("duration") or 0)
    return {
        "file": str(output.relative_to(package_dir)),
        "sha256": _hash(output),
        "duration_sec": round(duration, 3),
        "width": 1080,
        "height": 1920,
        "physical_validation": "PASS",
        "command": " ".join(shlex.quote(item) for item in command),
    }
