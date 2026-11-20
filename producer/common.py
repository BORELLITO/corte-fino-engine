"""Shared helpers: hashing, ffmpeg runs, probing and the audio sanity check."""
from __future__ import annotations

import hashlib
import math
import re
import shutil
import subprocess
from pathlib import Path

from media.probe import ProbeError, probe_media


class ProducerError(RuntimeError):
    """Raised when a stage cannot produce a provable artifact. Maps to BLOCKED."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1048576), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ffmpeg_bin() -> str:
    path = shutil.which("ffmpeg")
    if not path:
        raise ProducerError("producer:ffmpeg_not_available")
    return path


def run_ffmpeg(args: list[str], *, timeout: int = 600) -> subprocess.CompletedProcess:
    done = subprocess.run(
        [ffmpeg_bin(), "-nostdin", "-hide_banner", "-y", *args],
        capture_output=True, text=True, timeout=timeout, check=False,
    )
    if done.returncode != 0:
        raise ProducerError(f"producer:ffmpeg_failed:{done.stderr[-800:].strip()}")
    return done


def duration_sec(path: Path) -> float:
    try:
        value = float((probe_media(path).get("format") or {}).get("duration") or 0)
    except (ProbeError, TypeError, ValueError) as exc:
        raise ProducerError(f"producer:probe_failed:{path.name}:{exc}") from exc
    if not math.isfinite(value) or value <= 0:
        raise ProducerError(f"producer:duration_invalid:{path.name}")
    return value


def normalize_wav(src: Path, dst: Path) -> None:
    """Force the contract format: WAV, 24 kHz, mono, PCM16."""
    run_ffmpeg(["-i", str(src), "-ac", "1", "-ar", "24000", "-c:a", "pcm_s16le", str(dst)])


def audio_levels(path: Path) -> tuple[float, float]:
    """Return (mean_volume_db, max_volume_db) measured by ffmpeg volumedetect."""
    done = run_ffmpeg(["-i", str(path), "-af", "volumedetect", "-f", "null", "-"])
    mean = re.search(r"mean_volume:\s*(-?[\d.]+|-inf) dB", done.stderr)
    peak = re.search(r"max_volume:\s*(-?[\d.]+|-inf) dB", done.stderr)
    if not mean or not peak:
        raise ProducerError("producer:volumedetect_unreadable")
    return float(mean.group(1)), float(peak.group(1))


def audio_integrity_ok(path: Path) -> bool:
    """Real check: decodable, not silent, not clipped."""
    try:
        mean, peak = audio_levels(path)
    except (ProducerError, ValueError):
        return False
    return mean > -50.0 and peak < -0.1


def decodes_cleanly(path: Path) -> bool:
    done = subprocess.run(
        [ffmpeg_bin(), "-nostdin", "-v", "error", "-xerror", "-i", str(path),
         "-map", "0", "-f", "null", "-"],
        capture_output=True, text=True, timeout=300, check=False,
    )
    return done.returncode == 0
