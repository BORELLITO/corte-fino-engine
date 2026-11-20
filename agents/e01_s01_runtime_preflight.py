"""S01 no-GPU runtime preflight: physical binaries and synthetic test footage only.

This script cannot call LTX, Gradio, any publishing platform, or account APIs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path

PROJECT = "VERBO_NO_CHAO_EXCLUSIVO"
PACKAGE = "portable-ffmpeg==0.5.0"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def command(*args: str, timeout: int = 25) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True,
                          timeout=timeout, check=False)


def inspect_real_binaries(ffmpeg: Path, ffprobe: Path) -> dict:
    binaries = {}
    for label, path in (("ffmpeg", ffmpeg), ("ffprobe", ffprobe)):
        if not path.is_file() or not os.access(path, os.X_OK):
            raise RuntimeError(f"{label}_unavailable")
        version = command(str(path), "-version")
        if version.returncode or not version.stdout.lower().startswith(label + " version "):
            raise RuntimeError(f"{label}_version_unverified")
        binaries[label] = {
            "sha256": sha256(path),
            "version": version.stdout.splitlines()[0][:160],
        }
    return binaries


def synthetic_decode_proof(ffmpeg: Path, ffprobe: Path, output_dir: Path) -> dict:
    """Moving synthetic pattern, never an E01 scene or asset."""
    video = output_dir / "SYNTHETIC_NOT_E01.mp4"
    created = command(str(ffmpeg), "-nostdin", "-hide_banner", "-v", "error",
                      "-f", "lavfi", "-i", "testsrc2=size=180x320:rate=24",
                      "-t", "0.85", "-an", "-threads", "2", "-c:v", "libx264",
                      "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                      "-y", str(video), timeout=70)
    if created.returncode or not video.is_file():
        raise RuntimeError("synthetic_encode_failed")
    probe = command(str(ffprobe), "-v", "error", "-select_streams", "v:0",
                    "-show_entries", "stream=width,height,codec_name:format=duration",
                    "-of", "json", str(video), timeout=30)
    if probe.returncode:
        raise RuntimeError("synthetic_probe_failed")
    meta = json.loads(probe.stdout)
    streams = meta.get("streams", [])
    if len(streams) != 1 or streams[0].get("width") != 180 or streams[0].get("height") != 320:
        raise RuntimeError("synthetic_metadata_invalid")
    decoded = command(str(ffmpeg), "-nostdin", "-v", "error", "-xerror",
                      "-i", str(video), "-map", "0:v:0",
                      "-f", "null", "-", timeout=35)
    if decoded.returncode:
        raise RuntimeError("synthetic_full_decode_failed")
    result = {
        "synthetic_file_sha256": sha256(video),
        "duration_seconds": float(meta["format"]["duration"]),
        "full_decode": True,
        "is_real_scene": False,
        "allowed_in_master": False,
    }
    video.unlink(missing_ok=True)
    return result


def run(out: Path, *, synthetic_smoke: bool = False) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    result = {
        "project_id": PROJECT,
        "runtime_package_pin": PACKAGE,
        "status": "BLOCKED_OR_NOT_YET_PROVEN",
        "provider_requests": 0,
        "paid_service_used": False,
        "rights_cleared": False,
        "editorial_approved": False,
        "master_created": False,
        "publication_authorized": False,
    }
    try:
        from portable_ffmpeg import get_ffmpeg
        ffmpeg, ffprobe = (Path(p) for p in get_ffmpeg())
        result["binaries"] = inspect_real_binaries(ffmpeg, ffprobe)
        if synthetic_smoke:
            result["synthetic_fixture"] = synthetic_decode_proof(ffmpeg, ffprobe, out)
        result["status"] = "PASS_NO_GPU_FFMPEG_FFPROBE_PHYSICAL_PREFLIGHT"
    except (ImportError, RuntimeError, OSError, ValueError,
            KeyError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
        result["status"] = "BLOCKED_RUNTIME_PREPARATION"
        result["error_type"] = type(exc).__name__
        result["error_detail"] = str(exc)[:160]
    (out / "S01_RUNTIME_PREFLIGHT.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path,
                        default=Path("artifacts/vnc_s01_no_gpu"))
    parser.add_argument("--synthetic-smoke", action="store_true")
    args = parser.parse_args()
    data = run(args.out, synthetic_smoke=args.synthetic_smoke)
    print(json.dumps({"status": data["status"], "provider_requests": 0,
                      "publication_authorized": False}), flush=True)
    return 0 if data["status"].startswith("PASS_NO_GPU") else 2


if __name__ == "__main__":
    raise SystemExit(main())
