"""FFprobe-backed physical validation for rendered media."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


class ProbeError(RuntimeError):
    pass


def _binary(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise ProbeError(f"{name}:not_available")
    return path


def probe_media(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ProbeError(f"media:missing:{path}")
    command = [
        _binary("ffprobe"),
        "-v", "error",
        "-show_entries", "format=duration:stream=index,codec_type,codec_name,width,height,r_frame_rate",
        "-of", "json",
        str(path),
    ]
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise ProbeError(f"media:decode:{completed.stderr.strip() or 'ffprobe_failed'}")
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ProbeError(f"media:probe_json:{exc}") from exc
    if not isinstance(payload, dict):
        raise ProbeError("media:probe_not_object")
    return payload


def validate_rendered_video(path: Path, *, width: int = 1080, height: int = 1920) -> list[str]:
    try:
        payload = probe_media(path)
    except ProbeError as exc:
        return [str(exc)]

    errors: list[str] = []
    streams = payload.get("streams") or []
    video = next((item for item in streams if item.get("codec_type") == "video"), None)
    audio = next((item for item in streams if item.get("codec_type") == "audio"), None)
    if not isinstance(video, dict):
        errors.append("media:video_stream_missing")
    else:
        if video.get("width") != width or video.get("height") != height:
            errors.append(f"media:resolution:{video.get('width')}x{video.get('height')}")
    if not isinstance(audio, dict):
        errors.append("media:audio_stream_missing")
    try:
        duration = float((payload.get("format") or {}).get("duration"))
    except (TypeError, ValueError):
        duration = 0.0
    if duration <= 0:
        errors.append("media:duration_invalid")
    return errors
